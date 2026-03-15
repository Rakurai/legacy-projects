"""
Integration tests for entity lookup tools.

Tests actual DB execution of:
- resolve_entity_tool
- get_entity_tool (by id, by signature, with code, with neighbors)
- get_source_code_tool
- list_file_entities_tool
- get_file_summary_tool
"""

import pytest
import networkx as nx
from sqlalchemy.ext.asyncio import AsyncSession

from server.db_models import Entity, Edge
from server.errors import EntityNotFoundError
from server.tools.entity import (
    ResolveEntityParams,
    GetEntityParams,
    GetSourceCodeParams,
    ListFileEntitiesParams,
    GetFileSummaryParams,
    resolve_entity_tool,
    get_entity_tool,
    get_source_code_tool,
    list_file_entities_tool,
    get_file_summary_tool,
)


# ---------- resolve_entity_tool ----------

@pytest.mark.asyncio
async def test_resolve_entity_exact_name(test_session: AsyncSession, sample_entities: list[Entity]):
    """Tool returns exact match for unambiguous entity name."""
    params = ResolveEntityParams(query="do_kill")
    result = await resolve_entity_tool(test_session, params, embedding_client=None)

    assert result.resolution_status == "exact"
    assert result.match_type == "name_exact"
    assert len(result.candidates) == 1
    assert result.candidates[0].name == "do_kill"


@pytest.mark.asyncio
async def test_resolve_entity_with_kind_filter(test_session: AsyncSession, sample_entities: list[Entity]):
    """Tool respects kind filter."""
    params = ResolveEntityParams(query="Character", kind="class")
    result = await resolve_entity_tool(test_session, params, embedding_client=None)

    assert result.resolution_status == "exact"
    assert all(c.kind == "class" for c in result.candidates)


@pytest.mark.asyncio
async def test_resolve_entity_not_found(test_session: AsyncSession, sample_entities: list[Entity]):
    """Tool returns not_found for unknown entities."""
    params = ResolveEntityParams(query="zzz_unknown_xyz_42")
    result = await resolve_entity_tool(test_session, params, embedding_client=None)

    assert result.resolution_status == "not_found"
    assert result.resolution_candidates == 0


# ---------- get_entity_tool ----------

@pytest.mark.asyncio
async def test_get_entity_by_id(test_session: AsyncSession, sample_entities: list[Entity]):
    """Fetch entity by entity_id returns full detail."""
    eid = sample_entities[0].entity_id
    params = GetEntityParams(entity_id=eid)
    detail = await get_entity_tool(test_session, params)

    assert detail.entity_id == eid
    assert detail.name == "damage"
    assert detail.kind == "function"
    assert detail.brief is not None
    assert detail.source_text is None  # include_code defaults to False


@pytest.mark.asyncio
async def test_get_entity_by_signature(test_session: AsyncSession, sample_entities: list[Entity]):
    """Fetch entity by signature resolves correctly."""
    params = GetEntityParams(
        signature="void damage(Character *ch, Character *victim, int dam)"
    )
    detail = await get_entity_tool(test_session, params)

    assert detail.name == "damage"


@pytest.mark.asyncio
async def test_get_entity_with_code(test_session: AsyncSession, sample_entities: list[Entity]):
    """include_code=True returns source_text."""
    eid = sample_entities[0].entity_id
    params = GetEntityParams(entity_id=eid, include_code=True)
    detail = await get_entity_tool(test_session, params)

    assert detail.source_text is not None
    assert "damage" in detail.source_text


@pytest.mark.asyncio
async def test_get_entity_with_neighbors(
    test_session: AsyncSession,
    sample_entities: list[Entity],
    sample_edges: list[Edge],
    sample_graph: nx.MultiDiGraph,
):
    """include_neighbors=True populates neighbor list from graph."""
    eid = sample_entities[0].entity_id  # damage
    params = GetEntityParams(entity_id=eid, include_neighbors=True)
    detail = await get_entity_tool(test_session, params, graph=sample_graph)

    assert detail.neighbors is not None
    assert len(detail.neighbors) >= 1
    neighbor_names = [n.name for n in detail.neighbors]
    # damage has incoming CALLS from do_kill, outgoing CALLS to armor_absorb, outgoing USES to max_damage
    assert "do_kill" in neighbor_names or "armor_absorb" in neighbor_names


@pytest.mark.asyncio
async def test_get_entity_not_found(test_session: AsyncSession, sample_entities: list[Entity]):
    """Missing entity raises EntityNotFoundError."""
    params = GetEntityParams(entity_id="nonexistent_id_xyz")
    with pytest.raises(EntityNotFoundError):
        await get_entity_tool(test_session, params)


# ---------- get_source_code_tool ----------

@pytest.mark.asyncio
async def test_get_source_code(test_session: AsyncSession, sample_entities: list[Entity]):
    """Returns source text and metadata."""
    eid = sample_entities[0].entity_id
    params = GetSourceCodeParams(entity_id=eid)
    result = await get_source_code_tool(test_session, params)

    assert result["entity_id"] == eid
    assert result["source_text"] is not None
    assert result["file_path"] == "src/fight.cc"
    assert result["start_line"] == 100


@pytest.mark.asyncio
async def test_get_source_code_not_found(test_session: AsyncSession, sample_entities: list[Entity]):
    """Missing entity raises EntityNotFoundError."""
    params = GetSourceCodeParams(entity_id="nonexistent_id_xyz")
    with pytest.raises(EntityNotFoundError):
        await get_source_code_tool(test_session, params)


# ---------- list_file_entities_tool ----------

@pytest.mark.asyncio
async def test_list_file_entities(test_session: AsyncSession, sample_entities: list[Entity]):
    """Lists all entities in a file ordered by start line."""
    params = ListFileEntitiesParams(file_path="src/fight.cc")
    result = await list_file_entities_tool(test_session, params)

    assert result["file_path"] == "src/fight.cc"
    entities = result["entities"]
    # fight.cc has: max_damage (line 10), armor_absorb (line 50), damage (line 100), file entity
    assert len(entities) >= 3


@pytest.mark.asyncio
async def test_list_file_entities_with_kind_filter(test_session: AsyncSession, sample_entities: list[Entity]):
    """Kind filter restricts results."""
    params = ListFileEntitiesParams(file_path="src/fight.cc", kind="function")
    result = await list_file_entities_tool(test_session, params)

    entities = result["entities"]
    assert all(e.kind == "function" for e in entities)


@pytest.mark.asyncio
async def test_list_file_entities_empty(test_session: AsyncSession, sample_entities: list[Entity]):
    """Non-existent file returns empty list."""
    params = ListFileEntitiesParams(file_path="src/nonexistent.cc")
    result = await list_file_entities_tool(test_session, params)

    assert result["entities"] == []


# ---------- get_file_summary_tool ----------

@pytest.mark.asyncio
async def test_get_file_summary(test_session: AsyncSession, sample_entities: list[Entity]):
    """Returns aggregated file stats."""
    params = GetFileSummaryParams(file_path="src/fight.cc")
    result = await get_file_summary_tool(test_session, params)

    assert result.file_path == "src/fight.cc"
    assert result.entity_count >= 3
    assert "function" in result.entity_count_by_kind
    assert "combat" in result.capability_distribution
    assert len(result.top_entities_by_fan_in) >= 1


@pytest.mark.asyncio
async def test_get_file_summary_not_found(test_session: AsyncSession, sample_entities: list[Entity]):
    """Non-existent file raises EntityNotFoundError."""
    params = GetFileSummaryParams(file_path="src/nonexistent.cc")
    with pytest.raises(EntityNotFoundError):
        await get_file_summary_tool(test_session, params)
