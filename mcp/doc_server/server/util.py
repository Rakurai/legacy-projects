"""
Shared Utilities - Common helpers used across server modules.

Keeps utility code DRY and avoids duplication across tool/resource modules.
"""

from sqlalchemy import func, outerjoin
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from server.db_models import Entity, EntityUsage
from server.models import EntitySummary, UsageEntry


async def fetch_entity_summaries(
    session: AsyncSession,
    entity_ids: list[str],
) -> list[EntitySummary]:
    """Batch-fetch entities by ID and convert to EntitySummary. Preserves input ordering."""
    from server.converters import entity_to_summary

    if not entity_ids:
        return []

    result = await session.execute(select(Entity).where(Entity.entity_id.in_(entity_ids)))
    entities = result.scalars().all()
    entity_map = {e.entity_id: e for e in entities}

    return [entity_to_summary(entity_map[eid]) for eid in entity_ids if eid in entity_map]


async def fetch_entity_map(
    session: AsyncSession,
    entity_ids: list[str],
) -> dict[str, Entity]:
    """Batch-fetch entities by ID and return as {entity_id → Entity} dict."""
    if not entity_ids:
        return {}

    result = await session.execute(select(Entity).where(Entity.entity_id.in_(entity_ids)))
    return {e.entity_id: e for e in result.scalars().all()}


async def fetch_top_callers(
    session: AsyncSession,
    callee_id: str,
    limit: int = 5,
) -> list[UsageEntry]:
    """Return top callers for a callee entity, ranked by caller fan_in descending.

    Joins entity_usages against entities on caller_sig to look up fan_in.
    Unmatched callers default to 0. Used by explain_interface and get_entity.
    """
    fanin_sq = select(Entity.signature, func.max(Entity.fan_in).label("fan_in")).group_by(Entity.signature).subquery()
    stmt = (
        select(
            EntityUsage.caller_compound,
            EntityUsage.caller_sig,
            EntityUsage.description,
            func.coalesce(fanin_sq.c.fan_in, 0).label("caller_fan_in"),
        )
        .select_from(
            outerjoin(
                EntityUsage,
                fanin_sq,
                EntityUsage.caller_sig == fanin_sq.c.signature,  # type: ignore[arg-type]
            )
        )
        .where(EntityUsage.callee_id == callee_id)
        .order_by(func.coalesce(fanin_sq.c.fan_in, 0).desc())
        .limit(limit)
    )
    result = await session.execute(stmt)
    return [
        UsageEntry(
            caller_compound=row.caller_compound,
            caller_sig=row.caller_sig,
            description=row.description,
        )
        for row in result.all()
    ]
