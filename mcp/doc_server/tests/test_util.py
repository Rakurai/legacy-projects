"""
Unit tests for server.util error paths and edge cases.
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from server.util import fetch_entity_summaries, fetch_entity_map
from server.db_models import Entity


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
