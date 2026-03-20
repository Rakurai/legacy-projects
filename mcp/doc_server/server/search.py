"""
Hybrid Search - Semantic + Keyword + Exact Match.

Combines three search strategies:
1. Exact match (signature or name) - highest boost
2. Semantic search (pgvector cosine similarity)
3. Keyword search (PostgreSQL full-text via tsvector)

Scores are normalized and combined with weights:
- Exact: 10x boost
- Semantic: 0.6 weight
- Keyword: 0.4 weight

Degrades to keyword-only mode if embedding service unavailable.

All queries use SQLAlchemy ORM — no raw SQL.
"""

from typing import TYPE_CHECKING

from sqlalchemy import Select, func, literal, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

if TYPE_CHECKING:
    from server.embedding import EmbeddingProvider

from server.converters import entity_to_summary
from server.db_models import Entity, EntityUsage
from server.enums import SearchMode
from server.logging_config import log
from server.models import MatchingUsage, SearchResult

# Scoring weights (matching spec)
_EXACT_WEIGHT = 10.0
_SEMANTIC_WEIGHT = 0.6
_KEYWORD_WEIGHT = 0.4

# Minimum combined score for a result to be returned (FR-008)
_SCORE_THRESHOLD: float = 0.2


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
) -> set[str]:
    """Find entity IDs with exact signature or name match."""
    stmt = select(Entity.entity_id).where(or_(Entity.signature == query, Entity.name == query))
    stmt = _apply_filters(stmt, kind, capability)
    result = await session.execute(stmt)
    return {row[0] for row in result.all()}


async def _keyword_scores(
    session: AsyncSession,
    query: str,
    kind: str | None,
    capability: str | None,
    limit: int,
) -> dict[str, float]:
    """Get {entity_id: ts_rank score} for keyword matches."""
    tsq = func.plainto_tsquery("english", query)
    rank_expr = func.ts_rank(Entity.search_vector, tsq).label("score")

    stmt = select(Entity.entity_id, rank_expr).where(Entity.search_vector.op("@@")(tsq))
    stmt = _apply_filters(stmt, kind, capability)
    stmt = stmt.order_by(rank_expr.desc()).limit(limit)

    result = await session.execute(stmt)
    return {row.entity_id: float(row.score) for row in result.all()}


async def _semantic_scores(
    session: AsyncSession,
    query_embedding: list[float],
    kind: str | None,
    capability: str | None,
    limit: int,
) -> dict[str, float]:
    """Get {entity_id: cosine_similarity score} for semantic matches."""
    cosine_dist = Entity.embedding.cosine_distance(query_embedding)
    score_expr = (literal(1) - cosine_dist).label("score")

    stmt = select(Entity.entity_id, score_expr).where(Entity.embedding.isnot(None))
    stmt = _apply_filters(stmt, kind, capability)
    stmt = stmt.order_by(score_expr.desc()).limit(limit)

    result = await session.execute(stmt)
    return {row.entity_id: float(row.score) for row in result.all()}


def _merge_scores(
    exact_ids: set[str],
    keyword_scores: dict[str, float],
    semantic_scores: dict[str, float],
    limit: int,
) -> list[tuple[str, float]]:
    """Merge scores from all strategies, return sorted (entity_id, combined_score) pairs."""
    # Normalize keyword scores within this result set before applying weight,
    # so keyword contribution is bounded to [0, _KEYWORD_WEIGHT] regardless of ts_rank magnitude.
    if keyword_scores:
        max_kw = max(keyword_scores.values())
        if max_kw > 0:
            keyword_scores = {eid: s / max_kw for eid, s in keyword_scores.items()}

    all_ids = exact_ids | keyword_scores.keys() | semantic_scores.keys()
    scored: list[tuple[str, float]] = []

    for eid in all_ids:
        score = 0.0
        if eid in exact_ids:
            score += _EXACT_WEIGHT
        if eid in semantic_scores:
            score += semantic_scores[eid] * _SEMANTIC_WEIGHT
        if eid in keyword_scores:
            score += keyword_scores[eid] * _KEYWORD_WEIGHT
        scored.append((eid, score))

    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:limit]


async def hybrid_search(
    session: AsyncSession,
    query: str,
    embedding_provider: EmbeddingProvider | None = None,
    kind: str | None = None,
    capability: str | None = None,
    limit: int = 20,
) -> tuple[list[SearchResult], SearchMode]:
    """Perform hybrid search combining semantic + keyword + exact matching."""
    log.info("Hybrid search", query=query, kind=kind, capability=capability)

    query_embedding: list[float] | None = None
    search_mode: SearchMode = SearchMode.HYBRID

    if embedding_provider:
        query_embedding = await embedding_provider.embed_query(query)
    else:
        search_mode = SearchMode.KEYWORD_FALLBACK

    # Run sub-queries
    exact_ids = await _exact_match_ids(session, query, kind, capability)
    keyword_sc = await _keyword_scores(session, query, kind, capability, limit=100)

    semantic_sc: dict[str, float] = {}
    if search_mode == SearchMode.HYBRID and query_embedding:
        semantic_sc = await _semantic_scores(session, query_embedding, kind, capability, limit=100)

    # Merge scores
    ranked = _merge_scores(exact_ids, keyword_sc, semantic_sc, limit)

    if not ranked:
        log.info("Search complete", result_count=0, search_mode=search_mode)
        return [], search_mode

    # Fetch full entities for top results in one query
    top_ids = [eid for eid, _ in ranked]
    result = await session.execute(select(Entity).where(Entity.entity_id.in_(top_ids)))
    entity_map = {e.entity_id: e for e in result.scalars().all()}

    results: list[SearchResult] = []
    for eid, score in ranked:
        if score < _SCORE_THRESHOLD:
            continue
        entity = entity_map.get(eid)
        if not entity:
            continue
        results.append(
            SearchResult(
                result_type="entity",
                score=score,
                search_mode=search_mode,
                entity_summary=entity_to_summary(entity),
            )
        )

    log.info("Search complete", result_count=len(results), search_mode=search_mode)
    return results, search_mode


async def hybrid_search_usages(
    session: AsyncSession,
    query: str,
    embedding_provider: EmbeddingProvider | None = None,
    kind: str | None = None,
    capability: str | None = None,
    limit: int = 20,
) -> tuple[list[SearchResult], SearchMode]:
    """
    Hybrid search over entity_usages descriptions (FR-008).

    Combines semantic search over usage embeddings (0.6 weight) with keyword
    search over usage tsvectors (0.4 weight). No exact-match boost (usage
    descriptions have no name/signature to boost).

    Results are grouped by callee entity — one SearchResult per callee, with
    top-matching usage descriptions inlined as supporting evidence.

    kind and capability filters apply to the callee entity.
    """
    log.info("Hybrid usage search", query=query, kind=kind, capability=capability)

    query_embedding: list[float] | None = None
    search_mode: SearchMode = SearchMode.HYBRID

    if embedding_provider:
        query_embedding = await embedding_provider.embed_query(query)
    else:
        search_mode = SearchMode.KEYWORD_FALLBACK

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
        usage_scores[key] = s * _KEYWORD_WEIGHT

    # Semantic scores over usage embeddings
    if search_mode == SearchMode.HYBRID and query_embedding is not None:
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
            sem_contribution = float(row.score) * _SEMANTIC_WEIGHT
            usage_scores[key] = usage_scores.get(key, 0.0) + sem_contribution

    if not usage_scores:
        log.info("Usage search complete", result_count=0, search_mode=search_mode)
        return [], search_mode

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
        if score < _SCORE_THRESHOLD:
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
                search_mode=search_mode,
                entity_summary=entity_to_summary(entity),
                matching_usages=callee_usages.get(callee_id),
            )
        )

    log.info("Usage search complete", result_count=len(results), search_mode=search_mode)
    return results, search_mode
