"""
Shared Utilities - Common helpers used across server modules.

Keeps utility code DRY and avoids duplication across tool/resource modules.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from server.db_models import Entity
from server.models import EntitySummary


async def fetch_entity_summaries(
    session: AsyncSession,
    entity_ids: list[str],
) -> list[EntitySummary]:
    """Batch-fetch entities by ID and convert to EntitySummary. Preserves input ordering."""
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
