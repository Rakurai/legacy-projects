"""
Entity Resolution Pipeline - Multi-stage entity name resolution.

Pipeline stages (fail-through):
1. Exact signature match
2. Exact name match (ranked by doc_quality, fan_in)
3. Prefix match (ranked by length, doc_quality)
4. Keyword search (full-text via tsvector)
5. Semantic search (pgvector cosine similarity)

Returns ResolutionEnvelope with match metadata and candidates.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from sqlalchemy import func, literal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from server.converters import entity_to_summary
from server.db_models import Entity
from server.enums import MatchType, ResolutionStatus
from server.logging_config import log
from server.models import EntitySummary, ResolutionEnvelope
from server.util import doc_quality_sort_key

if TYPE_CHECKING:
    from server.embedding import EmbeddingProvider

_ENTITY_ID_MIN_LEN = 20


@dataclass
class ResolutionResult:
    """Resolution result with metadata."""
    status: ResolutionStatus
    match_type: MatchType
    candidates: list[Entity]
    resolved_from: str

    def to_envelope(self) -> ResolutionEnvelope:
        """Convert to ResolutionEnvelope."""
        return ResolutionEnvelope(
            resolution_status=self.status,
            resolved_from=self.resolved_from,
            match_type=self.match_type,
            resolution_candidates=len(self.candidates),
        )

    def to_entity_summaries(self) -> list[EntitySummary]:
        """Convert candidates to EntitySummary list."""
        return [entity_to_summary(e) for e in self.candidates]


async def resolve_entity(
    session: AsyncSession,
    query: str,
    kind: str | None = None,
    embedding_provider: EmbeddingProvider | None = None,
    limit: int = 20,
) -> ResolutionResult:
    """Resolve entity name through multi-stage pipeline (fail-through stages 1-6)."""
    log.info("Resolving entity", query=query, kind=kind)

    # Stage 1: Exact entity_id match (if query looks like entity_id)
    if "_" in query and len(query) > _ENTITY_ID_MIN_LEN:
        result = await _resolve_by_entity_id(session, query)
        if result:
            log.info("Resolved by entity_id", entity_id=query, match_type="entity_id")
            return result

    # Stage 2: Exact signature match
    result = await _resolve_by_signature(session, query, kind)
    if result:
        log.info("Resolved by exact signature", signature=query, match_type="signature_exact")
        return result

    # Stage 3: Exact name match
    result = await _resolve_by_name(session, query, kind, limit)
    if result:
        log.info("Resolved by exact name", name=query, candidates=len(result.candidates))
        return result

    # Stage 4: Prefix match
    result = await _resolve_by_prefix(session, query, kind, limit)
    if result:
        log.info("Resolved by prefix", prefix=query, candidates=len(result.candidates))
        return result

    # Stage 5: Keyword search (full-text)
    result = await _resolve_by_keyword(session, query, kind, limit)
    if result:
        log.info("Resolved by keyword search", query=query, candidates=len(result.candidates))
        return result

    # Stage 6: Semantic search (if embedding provider available)
    if embedding_provider:
        result = await _resolve_by_semantic(session, query, kind, embedding_provider, limit)
        if result:
            log.info("Resolved by semantic search", query=query, candidates=len(result.candidates))
            return result

    # No matches found
    log.info("Entity not found", query=query)
    return ResolutionResult(
        status=ResolutionStatus.NOT_FOUND,
        match_type=MatchType.SEMANTIC,  # Last attempted stage
        candidates=[],
        resolved_from=query,
    )


async def _resolve_by_entity_id(session: AsyncSession, entity_id: str) -> ResolutionResult | None:
    """Stage 1: Exact entity_id match."""
    result = await session.execute(
        select(Entity).where(Entity.entity_id == entity_id)
    )
    entity = result.scalar_one_or_none()

    if entity:
        return ResolutionResult(
            status=ResolutionStatus.EXACT,
            match_type=MatchType.ENTITY_ID,
            candidates=[entity],
            resolved_from=entity_id,
        )

    return None


async def _resolve_by_signature(
    session: AsyncSession,
    signature: str,
    kind: str | None,
) -> ResolutionResult | None:
    """Stage 2: Exact signature match."""
    stmt = select(Entity).where(Entity.signature == signature)

    if kind:
        stmt = stmt.where(Entity.kind == kind)

    stmt = stmt.order_by(doc_quality_sort_key(), Entity.fan_in.desc()).limit(20)

    result = await session.execute(stmt)
    entities = list(result.scalars().all())

    if entities:
        status: ResolutionStatus = ResolutionStatus.EXACT if len(entities) == 1 else ResolutionStatus.AMBIGUOUS
        return ResolutionResult(
            status=status,
            match_type=MatchType.SIGNATURE_EXACT,
            candidates=entities,
            resolved_from=signature,
        )

    return None


async def _resolve_by_name(
    session: AsyncSession,
    name: str,
    kind: str | None,
    limit: int,
) -> ResolutionResult | None:
    """Stage 3: Exact name match (ranked by doc_quality, fan_in)."""
    stmt = select(Entity).where(Entity.name == name)

    if kind:
        stmt = stmt.where(Entity.kind == kind)

    stmt = stmt.order_by(
        doc_quality_sort_key(),
        Entity.fan_in.desc(),
    ).limit(limit)

    result = await session.execute(stmt)
    entities = list(result.scalars().all())

    if entities:
        status: ResolutionStatus = ResolutionStatus.EXACT if len(entities) == 1 else ResolutionStatus.AMBIGUOUS
        return ResolutionResult(
            status=status,
            match_type=MatchType.NAME_EXACT,
            candidates=entities,
            resolved_from=name,
        )

    return None


async def _resolve_by_prefix(
    session: AsyncSession,
    prefix: str,
    kind: str | None,
    limit: int,
) -> ResolutionResult | None:
    """Stage 4: Prefix match (ranked by length, doc_quality)."""
    stmt = select(Entity).where(Entity.name.startswith(prefix))

    if kind:
        stmt = stmt.where(Entity.kind == kind)

    stmt = stmt.order_by(
        func.length(Entity.name),
        doc_quality_sort_key(),
    ).limit(limit)

    result = await session.execute(stmt)
    entities = list(result.scalars().all())

    if entities:
        return ResolutionResult(
            status=ResolutionStatus.AMBIGUOUS,
            match_type=MatchType.NAME_PREFIX,
            candidates=entities,
            resolved_from=prefix,
        )

    return None


async def _resolve_by_keyword(
    session: AsyncSession,
    query: str,
    kind: str | None,
    limit: int,
) -> ResolutionResult | None:
    """Stage 5: Keyword search (PostgreSQL full-text via tsvector)."""
    tsq = func.plainto_tsquery("english", query)
    rank_expr = func.ts_rank(Entity.search_vector, tsq).label("score")

    stmt = (
        select(Entity)
        .where(Entity.search_vector.op("@@")(tsq))
    )
    if kind:
        stmt = stmt.where(Entity.kind == kind)
    stmt = stmt.order_by(rank_expr.desc()).limit(limit)

    result = await session.execute(stmt)
    entities = list(result.scalars().all())

    if entities:
        return ResolutionResult(
            status=ResolutionStatus.AMBIGUOUS,
            match_type=MatchType.KEYWORD,
            candidates=entities,
            resolved_from=query,
        )

    return None


async def _resolve_by_semantic(
    session: AsyncSession,
    query: str,
    kind: str | None,
    embedding_provider: EmbeddingProvider,
    limit: int,
) -> ResolutionResult | None:
    """Stage 6: Semantic search (pgvector cosine similarity)."""
    try:
        query_embedding = await embedding_provider.embed_query(query)

        cosine_dist = Entity.embedding.cosine_distance(query_embedding)
        score_expr = (literal(1) - cosine_dist).label("score")

        stmt = (
            select(Entity)
            .where(Entity.embedding.isnot(None))
        )
        if kind:
            stmt = stmt.where(Entity.kind == kind)
        stmt = stmt.order_by(score_expr.desc()).limit(limit)

        result = await session.execute(stmt)
        entities = list(result.scalars().all())

        if entities:
            return ResolutionResult(
                status=ResolutionStatus.AMBIGUOUS,
                match_type=MatchType.SEMANTIC,
                candidates=entities,
                resolved_from=query,
            )

    except Exception as e:
        log.warning("Semantic search failed", error=str(e), query=query[:50])

    return None
