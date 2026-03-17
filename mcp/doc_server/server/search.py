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

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Select, func, literal, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

if TYPE_CHECKING:
    from server.embedding import EmbeddingProvider

from server.converters import entity_to_summary
from server.db_models import Entity
from server.enums import Provenance, SearchMode
from server.logging_config import log
from server.models import SearchResult

# Scoring weights (matching spec)
_EXACT_WEIGHT = 10.0
_SEMANTIC_WEIGHT = 0.6
_KEYWORD_WEIGHT = 0.4


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
    stmt = (
        select(Entity.entity_id)
        .where(or_(Entity.signature == query, Entity.name == query))
    )
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

    stmt = (
        select(Entity.entity_id, rank_expr)
        .where(Entity.search_vector.op("@@")(tsq))
    )
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

    stmt = (
        select(Entity.entity_id, score_expr)
        .where(Entity.embedding.isnot(None))
    )
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
        try:
            query_embedding = await embedding_provider.embed_query(query)
        except Exception as e:
            log.warning("Embedding generation failed; falling back to keyword-only", error=str(e))
            search_mode = SearchMode.KEYWORD_FALLBACK
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
    result = await session.execute(
        select(Entity).where(Entity.entity_id.in_(top_ids))
    )
    entity_map = {e.entity_id: e for e in result.scalars().all()}

    # Normalize max score for 0-1 range
    max_score = ranked[0][1] if ranked else 1.0
    normalizer = max_score if max_score > 0 else 1.0

    results: list[SearchResult] = []
    for eid, score in ranked:
        entity = entity_map.get(eid)
        if not entity:
            continue
        results.append(SearchResult(
            result_type="entity",
            score=min(score / normalizer, 1.0),
            search_mode=search_mode,
            provenance=Provenance.PRECOMPUTED,
            entity_summary=entity_to_summary(entity),
        ))

    log.info("Search complete", result_count=len(results), search_mode=search_mode)
    return results, search_mode
