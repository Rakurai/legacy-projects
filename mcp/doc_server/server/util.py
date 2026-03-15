"""
Shared Utilities - Common helpers used across server modules.

Keeps utility code DRY and avoids duplication across tool/resource modules.
"""

import json
from typing import Any

from sqlalchemy import case
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from server.db_models import Entity
from server.logging_config import log


def doc_quality_sort_key():
    """
    Return a SQLAlchemy CASE expression that maps doc_quality text values
    to integers for proper semantic ordering (high=1, medium=2, low=3).

    Use with .asc() for best-first ordering.
    """
    return case(
        {"high": 1, "medium": 2, "low": 3},
        value=Entity.doc_quality,
        else_=4,
    )


def parse_json_field(val: Any) -> Any:
    """
    Parse a JSON column value that may arrive as a string from asyncpg.

    PostgreSQL JSON/JSONB columns are sometimes returned as raw strings
    by asyncpg depending on the query path. This normalizes them.

    Args:
        val: Column value (dict, list, str, or None)

    Returns:
        Parsed Python object, or None if unparseable
    """
    if isinstance(val, str):
        try:
            return json.loads(val)
        except (json.JSONDecodeError, TypeError):
            return None
    return val


async def fetch_entity_summaries(
    session: AsyncSession,
    entity_ids: list[str],
) -> list["EntitySummary"]:
    """
    Batch-fetch entities by ID and convert to EntitySummary objects.

    Preserves ordering of input IDs. Silently skips IDs not found in DB.

    Args:
        session: Async database session
        entity_ids: Entity IDs to fetch

    Returns:
        Ordered list of EntitySummary objects
    """
    from server.resolver import entity_to_summary

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
    """
    Batch-fetch entities by ID and return as a dict.

    Args:
        session: Async database session
        entity_ids: Entity IDs to fetch

    Returns:
        Dict mapping entity_id → Entity
    """
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
    Resolve an entity_id from either entity_id or signature.

    Used by tools that accept entity_id|signature per FR-004.
    Prefers entity_id when both are provided.

    Args:
        session: Database session
        entity_id: Optional direct entity ID
        signature: Optional entity signature

    Returns:
        Resolved entity_id string

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
            from server.errors import EntityNotFoundError
            raise EntityNotFoundError(signature, kind="entity")
        return row

    raise ValueError("Either entity_id or signature must be provided")
