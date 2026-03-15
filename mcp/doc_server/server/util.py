"""
Shared Utilities - Common helpers used across server modules.

Keeps utility code DRY and avoids duplication across tool/resource modules.
"""

from sqlalchemy import case
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from server.db_models import Entity
from server.errors import EntityNotFoundError
from server.logging_config import log
from server.models import EntitySummary


def doc_quality_sort_key():
    """CASE expression mapping doc_quality → int for best-first ordering."""
    return case(
        (Entity.doc_quality == "high", 1),
        (Entity.doc_quality == "medium", 2),
        (Entity.doc_quality == "low", 3),
        else_=4,
    )


async def fetch_entity_summaries(
    session: AsyncSession,
    entity_ids: list[str],
) -> list[EntitySummary]:
    """Batch-fetch entities by ID and convert to EntitySummary. Preserves input ordering."""
    # Import here would be circular (converters → models, util → converters).
    # converters is lightweight and has no transitive deps back to util.
    from server.converters import entity_to_summary

    if not entity_ids:
        return []

    result = await session.execute(
        select(Entity).where(Entity.entity_id.in_(entity_ids))
    )
    entities = result.scalars().all()
    entity_map = {e.entity_id: e for e in entities}

    return [
        entity_to_summary(entity_map[eid])
        for eid in entity_ids
        if eid in entity_map
    ]


async def fetch_entity_map(
    session: AsyncSession,
    entity_ids: list[str],
) -> dict[str, Entity]:
    """Batch-fetch entities by ID and return as {entity_id → Entity} dict."""
    if not entity_ids:
        return {}

    result = await session.execute(
        select(Entity).where(Entity.entity_id.in_(entity_ids))
    )
    return {e.entity_id: e for e in result.scalars().all()}


async def resolve_entity_id(
    session: AsyncSession,
    entity_id: str | None,
    signature: str | None,
) -> str:
    """
    Resolve an entity_id from either entity_id or signature (FR-004).

    Prefers entity_id when both are provided.

    Raises:
        ValueError: If neither parameter is provided
        EntityNotFoundError: If signature doesn't match any entity
    """
    if entity_id:
        return entity_id

    if signature:
        result = await session.execute(
            select(Entity.entity_id)
            .where(Entity.signature == signature)
            .order_by(doc_quality_sort_key(), Entity.fan_in.desc())
            .limit(1)
        )
        row = result.scalar_one_or_none()
        if not row:
            raise EntityNotFoundError(signature, kind="entity")
        return row

    raise ValueError("Either entity_id or signature must be provided")
