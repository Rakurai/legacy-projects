"""Integration tests for entity lookup tools."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from server.db_models import Entity, Edge
from server.errors import EntityNotFoundError
from server.tools.entity import (
    get_entity,
    get_source_code,
)


# ---------- get_entity ----------

@pytest.mark.asyncio
async def test_get_entity_by_id(mock_ctx, sample_entities):
    """Fetch entity by entity_id returns full detail."""
    eid = sample_entities[0].entity_id
    detail = await get_entity(mock_ctx, entity_id=eid)

    assert detail.entity_id == eid
    assert detail.name == "damage"
    assert detail.kind == "function"
    assert detail.brief is not None
    assert detail.source_text is None  # include_code defaults to False


@pytest.mark.asyncio
async def test_get_entity_with_code(mock_ctx, sample_entities):
    """include_code=True returns source_text."""
    eid = sample_entities[0].entity_id
    detail = await get_entity(mock_ctx, entity_id=eid, include_code=True)

    assert detail.source_text is not None
    assert "damage" in detail.source_text


@pytest.mark.asyncio
async def test_get_entity_with_neighbors(mock_ctx, sample_entities, sample_edges):
    """include_neighbors=True populates neighbor list from graph."""
    eid = sample_entities[0].entity_id  # damage
    detail = await get_entity(mock_ctx, entity_id=eid, include_neighbors=True)

    assert detail.neighbors is not None
    assert len(detail.neighbors) >= 1
    neighbor_names = [n.name for n in detail.neighbors]
    # damage has incoming CALLS from do_kill, outgoing CALLS to armor_absorb, outgoing USES to max_damage
    assert "do_kill" in neighbor_names or "armor_absorb" in neighbor_names


@pytest.mark.asyncio
async def test_get_entity_not_found(mock_ctx, sample_entities):
    """Missing entity raises EntityNotFoundError."""
    with pytest.raises(EntityNotFoundError):
        await get_entity(mock_ctx, entity_id="nonexistent_id_xyz")


# ---------- get_source_code ----------

@pytest.mark.asyncio
async def test_get_source_code(mock_ctx, sample_entities):
    """Returns source text and metadata."""
    eid = sample_entities[0].entity_id
    result = await get_source_code(mock_ctx, entity_id=eid)

    assert result.entity_id == eid
    assert result.source_text is not None
    assert result.file_path == "src/fight.cc"
    assert result.start_line == 100


@pytest.mark.asyncio
async def test_get_source_code_not_found(mock_ctx, sample_entities):
    """Missing entity raises EntityNotFoundError."""
    with pytest.raises(EntityNotFoundError):
        await get_source_code(mock_ctx, entity_id="nonexistent_id_xyz")
