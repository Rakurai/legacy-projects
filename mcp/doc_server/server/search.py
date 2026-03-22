"""
Multi-View Search Pipeline — 7-stage retrieval with cross-encoder reranking.

Stages:
1. Five parallel channel queries (doc semantic, symbol semantic, doc keyword, symbol keyword, trigram)
2. Union + deduplicate by entity_id
3. Compute intermediate signal vector (8 signals)
4. Per-signal floor filtering with name_exact bypass
5. Cross-encoder reranking (both views per candidate)
6. Assign winning_view / winning_score / losing_score
7. Return top-K

hybrid_search_usages is unchanged (entity_usages out of scope per FR-062).
"""

import math
import time
from dataclasses import dataclass

from sqlalchemy import Select, func, literal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from server.converters import entity_to_summary
from server.db_models import Entity, EntityUsage
from server.embedding import EmbeddingProvider
from server.logging_config import log
from server.models import MatchingUsage, SearchResult
from server.retrieval_view import RetrievalView

# Per-channel retrieval limit
_CHANNEL_LIMIT = 100

# Trigram similarity threshold (low bar for short C++ identifiers)
_TRIGRAM_THRESHOLD = 0.2

# Scoring weights for hybrid_search_usages (V1 compat, unchanged)
_USAGE_SEMANTIC_WEIGHT = 0.6
_USAGE_KEYWORD_WEIGHT = 0.4
_USAGE_SCORE_THRESHOLD: float = 0.2


# ---------------------------------------------------------------------------
# Candidate data structure
# ---------------------------------------------------------------------------


@dataclass
class Candidate:
    """Intermediate candidate accumulating signals from multiple channels."""

    entity_id: str
    # Raw channel scores (0.0 if channel didn't produce this candidate)
    doc_semantic: float = 0.0
    symbol_semantic: float = 0.0
    doc_keyword: float = 0.0
    symbol_keyword: float = 0.0
    trigram: float = 0.0
    name_exact: bool = False
    signature_exact: bool = False
    # Shaped scores (computed after channel merge)
    doc_keyword_shaped: float = 0.0
    symbol_keyword_shaped: float = 0.0
    # Token overlap signals (FR-032, FR-034, FR-035)
    token_jaccard: float = 0.0
    query_coverage: float = 0.0
    # Cross-encoder scores (set during reranking)
    ce_doc: float = 0.0
    ce_symbol: float = 0.0


# Stop words excluded from token overlap computations
_STOP_WORDS: frozenset[str] = frozenset(
    {
        "a",
        "an",
        "the",
        "and",
        "or",
        "but",
        "in",
        "on",
        "at",
        "to",
        "for",
        "of",
        "with",
        "by",
        "from",
        "is",
        "are",
        "was",
        "were",
        "be",
        "been",
        "that",
        "this",
        "it",
        "as",
        "if",
        "not",
        "no",
        "do",
        "does",
        "did",
        "has",
        "have",
        "had",
        "can",
        "could",
        "will",
        "would",
        "shall",
        "should",
        "may",
        "might",
        "must",
        "so",
        "than",
        "then",
        "all",
        "each",
        "every",
        "any",
        "some",
        "such",
        "what",
        "which",
        "who",
        "how",
        "when",
        "where",
    }
)


def _tokenize(text: str) -> set[str]:
    """Lowercase alpha-numeric tokenization, stripping stop words."""
    import re as _re

    return {t for t in _re.findall(r"[a-z0-9_]+", text.lower()) if t not in _STOP_WORDS}


def _compute_token_jaccard(query_tokens: set[str], entity_tokens: set[str]) -> float:
    """Jaccard similarity between query tokens and entity name/signature tokens."""
    if not query_tokens or not entity_tokens:
        return 0.0
    intersection = query_tokens & entity_tokens
    union = query_tokens | entity_tokens
    return len(intersection) / len(union)


def _compute_query_coverage(query_tokens: set[str], entity_tokens: set[str]) -> float:
    """Fraction of query tokens found in entity tokens."""
    if not query_tokens:
        return 0.0
    return len(query_tokens & entity_tokens) / len(query_tokens)


def _shape_tsrank(raw: float, ceiling: float) -> float:
    """Corpus-calibrated ts_rank shaping: log(1 + score) / log(1 + ceiling), clamped to [0, 1]."""
    if ceiling <= 0:
        return 0.0
    return min(math.log1p(raw) / math.log1p(ceiling), 1.0)


# ---------------------------------------------------------------------------
# Channel query helpers
# ---------------------------------------------------------------------------


def _apply_filters(
    stmt: Select[tuple[Entity]],
    kind: str | None,
    capability: str | None,
) -> Select[tuple[Entity]]:
    """Apply optional filters to a SELECT statement."""
    if kind:
        stmt = stmt.where(Entity.kind == kind)
    if capability:
        stmt = stmt.where(Entity.capability == capability)
    return stmt


async def _exact_match_ids(
    session: AsyncSession,
    query: str,
    kind: str | None,
    capability: str | None,
) -> tuple[set[str], set[str]]:
    """Find entity IDs with exact name or signature match.

    Returns (name_exact_ids, signature_exact_ids).
    """
    name_stmt = select(Entity.entity_id).where(Entity.name == query)
    name_stmt = _apply_filters(name_stmt, kind, capability)
    name_result = await session.execute(name_stmt)
    name_ids = {row[0] for row in name_result.all()}

    sig_stmt = select(Entity.entity_id).where(Entity.signature == query)
    sig_stmt = _apply_filters(sig_stmt, kind, capability)
    sig_result = await session.execute(sig_stmt)
    sig_ids = {row[0] for row in sig_result.all()}

    return name_ids, sig_ids


async def _doc_keyword_scores(
    session: AsyncSession,
    query: str,
    kind: str | None,
    capability: str | None,
    limit: int,
) -> dict[str, float]:
    """ts_rank scores against doc_search_vector (english dictionary)."""
    tsq = func.plainto_tsquery("english", query)
    rank_expr = func.ts_rank(Entity.doc_search_vector, tsq).label("score")
    stmt = select(Entity.entity_id, rank_expr).where(Entity.doc_search_vector.op("@@")(tsq))
    stmt = _apply_filters(stmt, kind, capability)
    stmt = stmt.order_by(rank_expr.desc()).limit(limit)
    result = await session.execute(stmt)
    return {row.entity_id: float(row.score) for row in result.all()}


async def _symbol_keyword_scores(
    session: AsyncSession,
    query: str,
    kind: str | None,
    capability: str | None,
    limit: int,
) -> dict[str, float]:
    """ts_rank scores against symbol_search_vector (simple dictionary, no stemming)."""
    tsq = func.plainto_tsquery("simple", query)
    rank_expr = func.ts_rank(Entity.symbol_search_vector, tsq).label("score")
    stmt = select(Entity.entity_id, rank_expr).where(Entity.symbol_search_vector.op("@@")(tsq))
    stmt = _apply_filters(stmt, kind, capability)
    stmt = stmt.order_by(rank_expr.desc()).limit(limit)
    result = await session.execute(stmt)
    return {row.entity_id: float(row.score) for row in result.all()}


async def _doc_semantic_scores(
    session: AsyncSession,
    query_embedding: list[float],
    kind: str | None,
    capability: str | None,
    limit: int,
) -> dict[str, float]:
    """Cosine similarity scores against doc_embedding."""
    cosine_dist = Entity.doc_embedding.cosine_distance(query_embedding)
    score_expr = (literal(1) - cosine_dist).label("score")
    stmt = select(Entity.entity_id, score_expr).where(Entity.doc_embedding.isnot(None))
    stmt = _apply_filters(stmt, kind, capability)
    stmt = stmt.order_by(score_expr.desc()).limit(limit)
    result = await session.execute(stmt)
    return {row.entity_id: float(row.score) for row in result.all()}


async def _symbol_semantic_scores(
    session: AsyncSession,
    query_embedding: list[float],
    kind: str | None,
    capability: str | None,
    limit: int,
) -> dict[str, float]:
    """Cosine similarity scores against symbol_embedding."""
    cosine_dist = Entity.symbol_embedding.cosine_distance(query_embedding)
    score_expr = (literal(1) - cosine_dist).label("score")
    stmt = select(Entity.entity_id, score_expr).where(Entity.symbol_embedding.isnot(None))
    stmt = _apply_filters(stmt, kind, capability)
    stmt = stmt.order_by(score_expr.desc()).limit(limit)
    result = await session.execute(stmt)
    return {row.entity_id: float(row.score) for row in result.all()}


async def _trigram_scores(
    session: AsyncSession,
    query: str,
    kind: str | None,
    capability: str | None,
    limit: int,
) -> dict[str, float]:
    """pg_trgm similarity scores against symbol_searchable."""
    sim_expr = func.similarity(Entity.symbol_searchable, query.lower()).label("score")
    stmt = (
        select(Entity.entity_id, sim_expr)
        .where(Entity.symbol_searchable.isnot(None))
        .where(sim_expr >= _TRIGRAM_THRESHOLD)
    )
    stmt = _apply_filters(stmt, kind, capability)
    stmt = stmt.order_by(sim_expr.desc()).limit(limit)
    result = await session.execute(stmt)
    return {row.entity_id: float(row.score) for row in result.all()}


# ---------------------------------------------------------------------------
# Core multi-view search pipeline
# ---------------------------------------------------------------------------


async def hybrid_search(
    session: AsyncSession,
    query: str,
    embedding_provider: EmbeddingProvider,
    doc_view: RetrievalView,
    symbol_view: RetrievalView,
    kind: str | None = None,
    capability: str | None = None,
    limit: int = 20,
) -> list[SearchResult]:
    """Multi-view search: 5 channels → merge → filter → cross-encoder rerank → top-K."""
    log.info("Multi-view search", query=query, kind=kind, capability=capability)

    if not query or not query.strip():
        return []

    # Detect scoped query (e.g. "Logging::stc", "Character::position")
    scope_prefix: str | None = None
    bare_name: str | None = None
    if "::" in query:
        parts = query.rsplit("::", 1)
        if len(parts) == 2 and parts[0].strip() and parts[1].strip():  # noqa: PLR2004
            scope_prefix = parts[0].strip()
            bare_name = parts[1].strip()

    # For scoped queries, also search the bare name through all channels
    search_query = bare_name if bare_name else query

    # Stage 1: Five parallel channel queries
    name_exact_ids, sig_exact_ids = await _exact_match_ids(session, search_query, kind, capability)

    # Also check for qualified_name exact match on the full scoped query
    if scope_prefix and bare_name:
        qn_stmt = select(Entity.entity_id).where(Entity.qualified_name.ilike(f"%{scope_prefix}::{bare_name}%"))
        qn_stmt = _apply_filters(qn_stmt, kind, capability)
        qn_result = await session.execute(qn_stmt)
        qn_ids = {row[0] for row in qn_result.all()}
        name_exact_ids = name_exact_ids | qn_ids

    query_embedding = await embedding_provider.aembed(search_query)

    doc_kw = await _doc_keyword_scores(session, search_query, kind, capability, _CHANNEL_LIMIT)
    sym_kw = await _symbol_keyword_scores(session, search_query, kind, capability, _CHANNEL_LIMIT)
    trgm = await _trigram_scores(session, search_query, kind, capability, _CHANNEL_LIMIT)

    doc_sem = await _doc_semantic_scores(session, query_embedding, kind, capability, _CHANNEL_LIMIT)
    sym_sem = await _symbol_semantic_scores(session, query_embedding, kind, capability, _CHANNEL_LIMIT)

    # Stage 2: Merge by entity_id
    all_ids = (
        name_exact_ids | sig_exact_ids | doc_kw.keys() | sym_kw.keys() | doc_sem.keys() | sym_sem.keys() | trgm.keys()
    )

    log.debug(
        "Channel counts",
        name_exact=len(name_exact_ids),
        sig_exact=len(sig_exact_ids),
        doc_kw=len(doc_kw),
        sym_kw=len(sym_kw),
        doc_sem=len(doc_sem),
        sym_sem=len(sym_sem),
        trigram=len(trgm),
        merged=len(all_ids),
    )

    if not all_ids:
        log.info("Search complete", result_count=0)
        return []

    # Get ceiling values from views
    doc_ceiling = doc_view.ts_rank_ceiling
    sym_ceiling = symbol_view.ts_rank_ceiling

    candidates: dict[str, Candidate] = {}
    for eid in all_ids:
        c = Candidate(entity_id=eid)
        c.name_exact = eid in name_exact_ids
        c.signature_exact = eid in sig_exact_ids
        c.doc_semantic = doc_sem.get(eid, 0.0)
        c.symbol_semantic = sym_sem.get(eid, 0.0)
        c.doc_keyword = doc_kw.get(eid, 0.0)
        c.symbol_keyword = sym_kw.get(eid, 0.0)
        c.trigram = trgm.get(eid, 0.0)
        # Stage 3: Shaped keyword scores
        c.doc_keyword_shaped = _shape_tsrank(c.doc_keyword, doc_ceiling)
        c.symbol_keyword_shaped = _shape_tsrank(c.symbol_keyword, sym_ceiling)
        candidates[eid] = c

    # Token overlap signals (FR-032, FR-034, FR-035)
    query_tokens = _tokenize(search_query)
    if query_tokens:
        name_result = await session.execute(
            select(Entity.entity_id, Entity.name, Entity.signature).where(Entity.entity_id.in_(list(all_ids)))
        )
        for row in name_result.all():
            c = candidates.get(row.entity_id)
            if c is None:
                continue
            entity_tokens = _tokenize(f"{row.name or ''} {row.signature or ''}")
            c.token_jaccard = _compute_token_jaccard(query_tokens, entity_tokens)
            c.query_coverage = _compute_query_coverage(query_tokens, entity_tokens)

    # Stage 4: Per-signal floor filtering with name_exact bypass
    # Candidates pass if: any signal exceeds its floor threshold, OR name/sig exact match
    doc_floors = doc_view.floor_thresholds
    sym_floors = symbol_view.floor_thresholds
    floor_thresholds = {
        "doc_semantic": doc_floors.get("semantic", 0.3),
        "symbol_semantic": sym_floors.get("semantic", 0.3),
        "doc_keyword_shaped": doc_floors.get("keyword_shaped", 0.05),
        "symbol_keyword_shaped": sym_floors.get("keyword_shaped", 0.05),
        "trigram": sym_floors.get("trigram", _TRIGRAM_THRESHOLD),
    }

    filtered: dict[str, Candidate] = {}
    for eid, c in candidates.items():
        if c.name_exact or c.signature_exact:
            filtered[eid] = c
            continue
        # Check if any signal exceeds its floor
        if (
            c.doc_semantic >= floor_thresholds["doc_semantic"]
            or c.symbol_semantic >= floor_thresholds["symbol_semantic"]
            or c.doc_keyword_shaped >= floor_thresholds["doc_keyword_shaped"]
            or c.symbol_keyword_shaped >= floor_thresholds["symbol_keyword_shaped"]
            or c.trigram >= floor_thresholds["trigram"]
        ):
            filtered[eid] = c

    if not filtered:
        log.info("Search complete (all filtered)", result_count=0, pre_filter=len(candidates))
        return []

    log.info("Floor filtering", pre_filter=len(candidates), post_filter=len(filtered))

    # Fetch full entities for surviving candidates
    result = await session.execute(select(Entity).where(Entity.entity_id.in_(list(filtered.keys()))))
    entity_map = {e.entity_id: e for e in result.scalars().all()}

    # Scope-aware boost: if query contained "::", boost candidates whose qualified_name matches the scope
    scope_matched_ids: set[str] = set()
    if scope_prefix:
        full_scope = f"{scope_prefix}::{bare_name}".lower()
        for eid, entity in entity_map.items():
            if entity.qualified_name and full_scope in entity.qualified_name.lower():
                scope_matched_ids.add(eid)

    # Stage 5: Cross-encoder reranking (both views per candidate)
    # Build document texts for cross-encoder
    doc_texts: list[str] = []
    sym_texts: list[str] = []
    candidate_list: list[Candidate] = []

    for eid, c in filtered.items():
        entity = entity_map.get(eid)
        if not entity:
            continue
        candidate_list.append(c)
        doc_texts.append(doc_view.assemble_embed_text(entity))
        sym_texts.append(symbol_view.assemble_embed_text(entity))

    rerank_start = time.monotonic()
    if candidate_list:
        doc_scores = await doc_view.cross_encoder.arerank(query, doc_texts)
        sym_scores = await symbol_view.cross_encoder.arerank(query, sym_texts)

        for i, c in enumerate(candidate_list):
            c.ce_doc = doc_scores[i]
            c.ce_symbol = sym_scores[i]
    rerank_elapsed_ms = (time.monotonic() - rerank_start) * 1000

    # Stage 6: Assign winning view and build results
    results: list[SearchResult] = []
    for eid, c in filtered.items():
        entity = entity_map.get(eid)
        if not entity:
            continue

        # Determine winning view
        if c.ce_doc >= c.ce_symbol:
            winning_view = "doc"
            winning_score = c.ce_doc
            losing_score = c.ce_symbol
        else:
            winning_view = "symbol"
            winning_score = c.ce_symbol
            losing_score = c.ce_doc

        # Tier-based sort: scope match > exact match > cross-encoder score
        if eid in scope_matched_ids:
            tier = 2
        elif c.name_exact or c.signature_exact:
            tier = 1
        else:
            tier = 0

        results.append(
            SearchResult(
                result_type="entity",
                score=winning_score,
                entity_summary=entity_to_summary(entity),
                winning_view=winning_view,
                winning_score=winning_score,
                losing_score=losing_score,
                sort_tier=tier,
            )
        )

    # Stage 7: Sort by tier desc then score desc, return top-K
    results.sort(key=lambda r: (r.sort_tier, r.score), reverse=True)
    results = results[:limit]

    log.info(
        "Search complete",
        result_count=len(results),
        pre_filter=len(candidates),
        post_filter=len(filtered),
        rerank_ms=round(rerank_elapsed_ms, 1),
    )
    return results


# ---------------------------------------------------------------------------
# Usage search (V1 compat — unchanged per FR-062)
# ---------------------------------------------------------------------------


async def hybrid_search_usages(
    session: AsyncSession,
    query: str,
    embedding_provider: EmbeddingProvider,
    kind: str | None = None,
    capability: str | None = None,
    limit: int = 20,
) -> list[SearchResult]:
    """
    Hybrid search over entity_usages descriptions.

    Unchanged from V1 (FR-062) — entity_usages pipeline is out of scope.
    Results are grouped by callee entity with top-matching usage descriptions inlined.
    """
    log.info("Hybrid usage search", query=query, kind=kind, capability=capability)

    query_embedding = await embedding_provider.aembed(query)

    # Keyword scores over usage descriptions: {(callee_id, caller_compound, caller_sig): score}
    usage_scores: dict[tuple[str, str, str], float] = {}

    tsq = func.plainto_tsquery("english", query)
    kw_rank = func.ts_rank(EntityUsage.search_vector, tsq).label("score")
    kw_stmt = (
        select(  # type: ignore[call-overload]
            EntityUsage.callee_id,
            EntityUsage.caller_compound,
            EntityUsage.caller_sig,
            EntityUsage.description,
            kw_rank,
        )
        .where(EntityUsage.search_vector.op("@@")(tsq))  # type: ignore[union-attr]
        .order_by(kw_rank.desc())
        .limit(limit * 5)
    )
    raw_kw_scores: dict[tuple[str, str, str], float] = {}
    kw_result = await session.execute(kw_stmt)
    for row in kw_result.all():
        key = (row.callee_id, row.caller_compound, row.caller_sig)
        raw_kw_scores[key] = float(row.score)

    # Normalize keyword scores within this result set before applying weight
    if raw_kw_scores:
        max_kw = max(raw_kw_scores.values())
        if max_kw > 0:
            raw_kw_scores = {k: s / max_kw for k, s in raw_kw_scores.items()}
    for key, s in raw_kw_scores.items():
        usage_scores[key] = s * _USAGE_KEYWORD_WEIGHT

    # Semantic scores over usage embeddings
    cosine_dist = EntityUsage.embedding.cosine_distance(query_embedding)  # type: ignore[union-attr]
    sem_score_expr = (literal(1) - cosine_dist).label("score")
    sem_stmt = (
        select(  # type: ignore[call-overload]
            EntityUsage.callee_id,
            EntityUsage.caller_compound,
            EntityUsage.caller_sig,
            EntityUsage.description,
            sem_score_expr,
        )
        .where(EntityUsage.embedding.isnot(None))  # type: ignore[union-attr]
        .order_by(sem_score_expr.desc())
        .limit(limit * 5)
    )
    sem_result = await session.execute(sem_stmt)
    for row in sem_result.all():
        key = (row.callee_id, row.caller_compound, row.caller_sig)
        sem_contribution = float(row.score) * _USAGE_SEMANTIC_WEIGHT
        usage_scores[key] = usage_scores.get(key, 0.0) + sem_contribution

    if not usage_scores:
        log.info("Usage search complete", result_count=0)
        return []

    # Fetch all descriptions for scored rows (needed for MatchingUsage)
    desc_map: dict[tuple[str, str, str], str] = {}
    keys_with_scores = list(usage_scores.keys())
    all_callee_ids = list({k[0] for k in keys_with_scores})

    desc_result = await session.execute(
        select(
            EntityUsage.callee_id, EntityUsage.caller_compound, EntityUsage.caller_sig, EntityUsage.description
        ).where(EntityUsage.callee_id.in_(all_callee_ids))  # type: ignore[attr-defined]
    )
    for row in desc_result.all():
        desc_map[(row.callee_id, row.caller_compound, row.caller_sig)] = row.description

    # Group by callee: best combined score, top matching usages
    callee_scores: dict[str, float] = {}
    callee_usages: dict[str, list[MatchingUsage]] = {}

    for (callee_id, compound, sig), score in usage_scores.items():
        if callee_id not in callee_scores or score > callee_scores[callee_id]:
            callee_scores[callee_id] = score
        description = desc_map.get((callee_id, compound, sig), "")
        if callee_id not in callee_usages:
            callee_usages[callee_id] = []
        callee_usages[callee_id].append(
            MatchingUsage(
                caller_compound=compound,
                caller_sig=sig,
                description=description,
                score=min(score, 1.0),
            )
        )

    # Sort callee_usages per callee by score desc, keep top 3 as evidence
    for callee_id, usages_list in callee_usages.items():
        usages_list.sort(key=lambda u: u.score, reverse=True)
        callee_usages[callee_id] = usages_list[:3]

    # Rank callees by best score
    ranked_callees = sorted(callee_scores.items(), key=lambda x: x[1], reverse=True)[:limit]

    # Fetch callee entities
    ranked_callee_ids = [cid for cid, _ in ranked_callees]
    entity_result = await session.execute(select(Entity).where(Entity.entity_id.in_(ranked_callee_ids)))  # type: ignore[attr-defined]
    entity_map = {e.entity_id: e for e in entity_result.scalars().all()}

    # Apply callee-level filters and threshold
    results: list[SearchResult] = []
    for callee_id, score in ranked_callees:
        if score < _USAGE_SCORE_THRESHOLD:
            continue
        entity = entity_map.get(callee_id)
        if not entity:
            continue
        if kind and entity.kind != kind:
            continue
        if capability and entity.capability != capability:
            continue
        results.append(
            SearchResult(
                result_type="entity",
                score=score,
                entity_summary=entity_to_summary(entity),
                matching_usages=callee_usages.get(callee_id),
                winning_view="doc",
                winning_score=score,
                losing_score=0.0,
            )
        )

    log.info("Usage search complete", result_count=len(results))
    return results
