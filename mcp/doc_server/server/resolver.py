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

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, func
from sqlmodel import select
from typing import Literal

from server.db_models import Entity
from server.models import ResolutionEnvelope, EntitySummary
from server.logging_config import log


MatchType = Literal["entity_id", "signature_exact", "name_exact", "name_prefix", "keyword", "semantic"]
ResolutionStatus = Literal["exact", "ambiguous", "not_found"]


class ResolutionResult:
    """Resolution result with metadata."""

    def __init__(
        self,
        status: ResolutionStatus,
        match_type: MatchType,
        candidates: list[Entity],
        resolved_from: str,
    ):
        self.status = status
        self.match_type = match_type
        self.candidates = candidates
        self.resolved_from = resolved_from

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


def entity_to_summary(entity: Entity) -> EntitySummary:
    """Convert Entity to EntitySummary."""
    return EntitySummary(
        entity_id=entity.entity_id,
        signature=entity.signature,
        name=entity.name,
        kind=entity.kind,  # type: ignore
        file_path=entity.file_path,
        capability=entity.capability,
        brief=entity.brief,
        doc_state=entity.doc_state or "extracted_summary",
        doc_quality=entity.doc_quality or "low",  # type: ignore
        fan_in=entity.fan_in,
        fan_out=entity.fan_out,
        provenance="precomputed",
    )


async def resolve_entity(
    session: AsyncSession,
    query: str,
    kind: str | None = None,
    embedding_client=None,
    limit: int = 20,
) -> ResolutionResult:
    """
    Resolve entity name through multi-stage pipeline.

    Args:
        session: Database session
        query: Entity name or signature to resolve
        kind: Optional kind filter (function, class, etc.)
        embedding_client: Optional OpenAI embedding client for semantic search
        limit: Maximum candidates to return

    Returns:
        ResolutionResult with status, match_type, and candidates
    """
    log.info("Resolving entity", query=query, kind=kind)

    # Stage 1: Exact entity_id match (if query looks like entity_id)
    if "_" in query and len(query) > 20:
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

    # Stage 6: Semantic search (if embedding client available)
    if embedding_client:
        result = await _resolve_by_semantic(session, query, kind, embedding_client, limit)
        if result:
            log.info("Resolved by semantic search", query=query, candidates=len(result.candidates))
            return result

    # No matches found
    log.info("Entity not found", query=query)
    return ResolutionResult(
        status="not_found",
        match_type="semantic",  # Last attempted stage
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
            status="exact",
            match_type="entity_id",
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

    result = await session.execute(stmt)
    entity = result.scalar_one_or_none()

    if entity:
        return ResolutionResult(
            status="exact",
            match_type="signature_exact",
            candidates=[entity],
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
        Entity.doc_quality.desc(),
        Entity.fan_in.desc(),
    ).limit(limit)

    result = await session.execute(stmt)
    entities = list(result.scalars().all())

    if entities:
        status: ResolutionStatus = "exact" if len(entities) == 1 else "ambiguous"
        return ResolutionResult(
            status=status,
            match_type="name_exact",
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
        Entity.doc_quality.desc(),
    ).limit(limit)

    result = await session.execute(stmt)
    entities = list(result.scalars().all())

    if entities:
        return ResolutionResult(
            status="ambiguous",
            match_type="name_prefix",
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
    # Build query with optional kind filter
    kind_filter = f"AND kind = '{kind}'" if kind else ""

    keyword_sql = text(f"""
        SELECT *, ts_rank(search_vector, plainto_tsquery('english', :query)) AS score
        FROM entities
        WHERE search_vector @@ plainto_tsquery('english', :query)
        {kind_filter}
        ORDER BY score DESC
        LIMIT :limit
    """)

    result = await session.execute(
        keyword_sql,
        {"query": query, "limit": limit}
    )

    rows = result.fetchall()

    if rows:
        # Convert rows to Entity objects
        entities = []
        for row in rows:
            entity = Entity(**{k: v for k, v in row._mapping.items() if k != "score"})
            entities.append(entity)

        return ResolutionResult(
            status="ambiguous",
            match_type="keyword",
            candidates=entities,
            resolved_from=query,
        )

    return None


async def _resolve_by_semantic(
    session: AsyncSession,
    query: str,
    kind: str | None,
    embedding_client,
    limit: int,
) -> ResolutionResult | None:
    """Stage 6: Semantic search (pgvector cosine similarity)."""
    try:
        # Get query embedding
        response = await embedding_client.embeddings.create(
            model="text-embedding-3-large",  # or configured model
            input=query,
            encoding_format="float"
        )
        query_embedding = response.data[0].embedding

        # Build query with optional kind filter
        kind_filter = f"AND kind = '{kind}'" if kind else ""

        semantic_sql = text(f"""
            SELECT *, 1 - (embedding <=> :embedding::vector) AS score
            FROM entities
            WHERE embedding IS NOT NULL
            {kind_filter}
            ORDER BY score DESC
            LIMIT :limit
        """)

        result = await session.execute(
            semantic_sql,
            {"embedding": query_embedding, "limit": limit}
        )

        rows = result.fetchall()

        if rows:
            entities = []
            for row in rows:
                entity = Entity(**{k: v for k, v in row._mapping.items() if k != "score"})
                entities.append(entity)

            return ResolutionResult(
                status="ambiguous",
                match_type="semantic",
                candidates=entities,
                resolved_from=query,
            )

    except Exception as e:
        log.warning("Semantic search failed", error=str(e), query=query[:50])

    return None
