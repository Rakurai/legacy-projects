"""
Unit tests for server.util error paths and edge cases.
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from server.util import resolve_entity_id, fetch_entity_summaries, fetch_entity_map
from server.errors import EntityNotFoundError
from server.db_models import Entity


@pytest.mark.asyncio
async def test_resolve_entity_id_by_entity_id(test_session: AsyncSession, sample_entities: list[Entity]):
    """resolve_entity_id returns entity_id directly when provided."""
    result = await resolve_entity_id(test_session, "fight_8cc_1a2b3c4d5e6f", None)
    assert result == "fight_8cc_1a2b3c4d5e6f"


@pytest.mark.asyncio
async def test_resolve_entity_id_by_signature(test_session: AsyncSession, sample_entities: list[Entity]):
    """resolve_entity_id resolves from signature when entity_id is None."""
    result = await resolve_entity_id(
        test_session,
        None,
        "void damage(Character *ch, Character *victim, int dam)",
    )
    assert result == "fight_8cc_1a2b3c4d5e6f"


@pytest.mark.asyncio
async def test_resolve_entity_id_neither_provided(test_session: AsyncSession):
    """resolve_entity_id raises ValueError when neither param is given."""
    with pytest.raises(ValueError, match="Either entity_id or signature"):
        await resolve_entity_id(test_session, None, None)


@pytest.mark.asyncio
async def test_resolve_entity_id_bad_signature(test_session: AsyncSession, sample_entities: list[Entity]):
    """resolve_entity_id raises EntityNotFoundError for unknown signature."""
    with pytest.raises(EntityNotFoundError):
        await resolve_entity_id(test_session, None, "void nonexistent()")


@pytest.mark.asyncio
async def test_fetch_entity_summaries_empty_list(test_session: AsyncSession):
    """fetch_entity_summaries returns empty list for empty input."""
    result = await fetch_entity_summaries(test_session, [])
    assert result == []


@pytest.mark.asyncio
async def test_fetch_entity_summaries_preserves_order(test_session: AsyncSession, sample_entities: list[Entity]):
    """fetch_entity_summaries returns results in input order."""
    ids = [sample_entities[2].entity_id, sample_entities[0].entity_id]
    result = await fetch_entity_summaries(test_session, ids)

    assert len(result) == 2
    assert result[0].entity_id == sample_entities[2].entity_id
    assert result[1].entity_id == sample_entities[0].entity_id


@pytest.mark.asyncio
async def test_fetch_entity_summaries_skips_missing(test_session: AsyncSession, sample_entities: list[Entity]):
    """fetch_entity_summaries silently skips nonexistent IDs."""
    ids = [sample_entities[0].entity_id, "nonexistent_id"]
    result = await fetch_entity_summaries(test_session, ids)

    assert len(result) == 1
    assert result[0].entity_id == sample_entities[0].entity_id


@pytest.mark.asyncio
async def test_fetch_entity_map_empty_list(test_session: AsyncSession):
    """fetch_entity_map returns empty dict for empty input."""
    result = await fetch_entity_map(test_session, [])
    assert result == {}


@pytest.mark.asyncio
async def test_fetch_entity_map_returns_entities(test_session: AsyncSession, sample_entities: list[Entity]):
    """fetch_entity_map returns {entity_id: Entity} dict."""
    ids = [sample_entities[0].entity_id, sample_entities[1].entity_id]
    result = await fetch_entity_map(test_session, ids)

    assert len(result) == 2
    assert result[sample_entities[0].entity_id].name == "damage"
    assert result[sample_entities[1].entity_id].name == "do_kill"
