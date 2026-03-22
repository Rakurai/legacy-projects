"""
Entity Resolution Pipeline - Multi-stage entity name resolution.

Internal pipeline used by search to resolve user queries to entities.

Pipeline stages (fail-through):
1. Exact entity_id match
2. Exact signature match
3. Exact name match (ranked by fan_in)
4. Prefix match (ranked by length, fan_in)
5. Keyword search (full-text via tsvector)
6. Semantic search (pgvector cosine similarity)

Returns ResolutionResult with match metadata and candidates.
"""

from pydantic import BaseModel, ConfigDict
from sqlalchemy import func, literal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from server.converters import entity_to_summary
from server.db_models import Entity
from server.embedding import EmbeddingProvider
from server.enums import MatchType, ResolutionStatus
from server.logging_config import log
from server.models import EntitySummary

# Maximum length of a deterministic entity ID (e.g. "file:a1b2c3d" = 12 chars)
_MAX_ENTITY_ID_LENGTH = 15


class ResolutionResult(BaseModel):
    """Resolution result with metadata."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    status: ResolutionStatus
    match_type: MatchType
    candidates: list[Entity]
    resolved_from: str

    def to_entity_summaries(self) -> list[EntitySummary]:
        """Convert candidates to EntitySummary list."""
        return [entity_to_summary(e) for e in self.candidates]


async def resolve_entity(
    session: AsyncSession,
    query: str,
    embedding_provider: EmbeddingProvider,
    kind: str | None = None,
    limit: int = 20,
) -> ResolutionResult:
    """Resolve entity name through multi-stage pipeline (fail-through stages 1-6)."""
    log.info("Resolving entity", query=query, kind=kind)

    # Stage 1: Exact entity_id match (if query looks like a deterministic ID)
    if ":" in query and len(query) <= _MAX_ENTITY_ID_LENGTH:
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

    # Stage 6: Semantic search
    result = await _resolve_by_semantic(session, query, kind, embedding_provider, limit)
    if result:
        log.info("Resolved by semantic search", query=query, candidates=len(result.candidates))
        return result

    # No matches found
    log.info("Entity not found", query=query)
    return ResolutionResult(
        status=ResolutionStatus.NOT_FOUND,
        match_type=MatchType.SEMANTIC,
        candidates=[],
        resolved_from=query,
    )


async def _resolve_by_entity_id(session: AsyncSession, entity_id: str) -> ResolutionResult | None:
    """Stage 1: Exact entity_id match."""
    result = await session.execute(select(Entity).where(Entity.entity_id == entity_id))
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

    stmt = stmt.order_by(Entity.fan_in.desc()).limit(20)

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
    """Stage 3: Exact name match (ranked by fan_in)."""
    stmt = select(Entity).where(Entity.name == name)

    if kind:
        stmt = stmt.where(Entity.kind == kind)

    stmt = stmt.order_by(
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
    """Stage 4: Prefix match (ranked by length, fan_in)."""
    stmt = select(Entity).where(Entity.name.startswith(prefix))

    if kind:
        stmt = stmt.where(Entity.kind == kind)

    stmt = stmt.order_by(
        func.length(Entity.name),
        Entity.fan_in.desc(),
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
    rank_expr = func.ts_rank(Entity.doc_search_vector, tsq).label("score")

    stmt = select(Entity).where(Entity.doc_search_vector.op("@@")(tsq))
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
    query_embedding = await embedding_provider.aembed(query)

    cosine_dist = Entity.doc_embedding.cosine_distance(query_embedding)
    score_expr = (literal(1) - cosine_dist).label("score")

    stmt = select(Entity).where(Entity.doc_embedding.isnot(None))
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

    return None
