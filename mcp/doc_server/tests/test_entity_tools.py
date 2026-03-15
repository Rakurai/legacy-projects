"""
Integration tests for entity lookup tools.

Tests actual DB execution via mock_ctx of:
- resolve_entity
- get_entity (by id, by signature, with code, with neighbors)
- get_source_code
- list_file_entities
- get_file_summary
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from server.db_models import Entity, Edge
from server.errors import EntityNotFoundError
from server.tools.entity import (
    resolve_entity,
    get_entity,
    get_source_code,
    list_file_entities,
    get_file_summary,
)


# ---------- resolve_entity ----------

@pytest.mark.asyncio
async def test_resolve_entity_exact_name(mock_ctx, sample_entities):
    """Tool returns exact match for unambiguous entity name."""
    result = await resolve_entity(mock_ctx, query="do_kill")

    assert result.resolution_status == "exact"
    assert result.match_type == "name_exact"
    assert len(result.candidates) == 1
    assert result.candidates[0].name == "do_kill"


@pytest.mark.asyncio
async def test_resolve_entity_with_kind_filter(mock_ctx, sample_entities):
    """Tool respects kind filter."""
    result = await resolve_entity(mock_ctx, query="Character", kind="class")

    assert result.resolution_status == "exact"
    assert all(c.kind == "class" for c in result.candidates)


@pytest.mark.asyncio
async def test_resolve_entity_not_found(mock_ctx, sample_entities):
    """Tool returns not_found for unknown entities."""
    result = await resolve_entity(mock_ctx, query="zzz_unknown_xyz_42")

    assert result.resolution_status == "not_found"
    assert result.resolution_candidates == 0


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
async def test_get_entity_by_signature(mock_ctx, sample_entities):
    """Fetch entity by signature resolves correctly."""
    detail = await get_entity(
        mock_ctx,
        signature="void damage(Character *ch, Character *victim, int dam)",
    )
    assert detail.name == "damage"


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


# ---------- list_file_entities ----------

@pytest.mark.asyncio
async def test_list_file_entities(mock_ctx, sample_entities):
    """Lists all entities in a file ordered by start line."""
    result = await list_file_entities(mock_ctx, file_path="src/fight.cc")

    assert result.file_path == "src/fight.cc"
    # fight.cc has: max_damage (line 10), armor_absorb (line 50), damage (line 100), file entity
    assert len(result.entities) >= 3


@pytest.mark.asyncio
async def test_list_file_entities_with_kind_filter(mock_ctx, sample_entities):
    """Kind filter restricts results."""
    result = await list_file_entities(mock_ctx, file_path="src/fight.cc", kind="function")

    assert all(e.kind == "function" for e in result.entities)


@pytest.mark.asyncio
async def test_list_file_entities_empty(mock_ctx, sample_entities):
    """Non-existent file returns empty list."""
    result = await list_file_entities(mock_ctx, file_path="src/nonexistent.cc")

    assert result.entities == []


# ---------- get_file_summary ----------

@pytest.mark.asyncio
async def test_get_file_summary(mock_ctx, sample_entities):
    """Returns aggregated file stats."""
    result = await get_file_summary(mock_ctx, file_path="src/fight.cc")

    assert result.file_path == "src/fight.cc"
    assert result.entity_count >= 3
    assert "function" in result.entity_count_by_kind
    assert "combat" in result.capability_distribution
    assert len(result.top_entities_by_fan_in) >= 1


@pytest.mark.asyncio
async def test_get_file_summary_not_found(mock_ctx, sample_entities):
    """Non-existent file raises EntityNotFoundError."""
    with pytest.raises(EntityNotFoundError):
        await get_file_summary(mock_ctx, file_path="src/nonexistent.cc")
