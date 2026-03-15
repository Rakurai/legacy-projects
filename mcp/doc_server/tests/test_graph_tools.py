"""
Integration tests for graph navigation tools.

Tests actual DB + graph execution of:
- get_callers_tool
- get_callees_tool
- get_dependencies_tool
- get_class_hierarchy_tool
- get_related_entities_tool
- get_related_files_tool
"""

import pytest
import networkx as nx
from sqlalchemy.ext.asyncio import AsyncSession

from server.db_models import Entity, Edge
from server.tools.graph import (
    GetCallersParams,
    GetCalleesParams,
    GetDependenciesParams,
    GetClassHierarchyParams,
    GetRelatedEntitiesParams,
    GetRelatedFilesParams,
    get_callers_tool,
    get_callees_tool,
    get_dependencies_tool,
    get_class_hierarchy_tool,
    get_related_entities_tool,
    get_related_files_tool,
)


# ---------- get_callers_tool ----------

@pytest.mark.asyncio
async def test_get_callers(
    test_session: AsyncSession,
    sample_entities: list[Entity],
    sample_edges: list[Edge],
    sample_graph: nx.MultiDiGraph,
):
    """Finds callers at depth 1."""
    eid = sample_entities[0].entity_id  # damage
    params = GetCallersParams(entity_id=eid, depth=1)
    result = await get_callers_tool(test_session, params, sample_graph)

    assert result.entity_id == eid
    assert 1 in result.callers_by_depth
    caller_names = [s.name for s in result.callers_by_depth[1]]
    assert "do_kill" in caller_names


@pytest.mark.asyncio
async def test_get_callers_no_callers(
    test_session: AsyncSession,
    sample_entities: list[Entity],
    sample_edges: list[Edge],
    sample_graph: nx.MultiDiGraph,
):
    """Entity with no callers returns empty map."""
    eid = sample_entities[1].entity_id  # do_kill (top-level entry point)
    params = GetCallersParams(entity_id=eid, depth=1)
    result = await get_callers_tool(test_session, params, sample_graph)

    # do_kill has no callers in our test data
    total = sum(len(v) for v in result.callers_by_depth.values())
    assert total == 0


# ---------- get_callees_tool ----------

@pytest.mark.asyncio
async def test_get_callees(
    test_session: AsyncSession,
    sample_entities: list[Entity],
    sample_edges: list[Edge],
    sample_graph: nx.MultiDiGraph,
):
    """Finds callees at depth 1."""
    eid = sample_entities[1].entity_id  # do_kill
    params = GetCalleesParams(entity_id=eid, depth=1)
    result = await get_callees_tool(test_session, params, sample_graph)

    assert result.entity_id == eid
    assert 1 in result.callees_by_depth
    callee_names = [s.name for s in result.callees_by_depth[1]]
    assert "damage" in callee_names


@pytest.mark.asyncio
async def test_get_callees_depth_2(
    test_session: AsyncSession,
    sample_entities: list[Entity],
    sample_edges: list[Edge],
    sample_graph: nx.MultiDiGraph,
):
    """Depth-2 traversal finds transitive callees."""
    eid = sample_entities[1].entity_id  # do_kill
    params = GetCalleesParams(entity_id=eid, depth=2)
    result = await get_callees_tool(test_session, params, sample_graph)

    # depth 1: damage, depth 2: armor_absorb (damage→armor_absorb is calls)
    all_names = [
        s.name
        for depth_list in result.callees_by_depth.values()
        for s in depth_list
    ]
    assert "damage" in all_names
    assert "armor_absorb" in all_names


# ---------- get_dependencies_tool ----------

@pytest.mark.asyncio
async def test_get_dependencies_both(
    test_session: AsyncSession,
    sample_entities: list[Entity],
    sample_edges: list[Edge],
    sample_graph: nx.MultiDiGraph,
):
    """Both-direction dependencies include incoming and outgoing."""
    eid = sample_entities[0].entity_id  # damage
    params = GetDependenciesParams(entity_id=eid, direction="both")
    result = await get_dependencies_tool(test_session, params, sample_graph)

    assert result.entity_id == eid
    assert len(result.dependencies) >= 2  # at least incoming (do_kill) + outgoing (armor_absorb + max_damage)


@pytest.mark.asyncio
async def test_get_dependencies_filtered(
    test_session: AsyncSession,
    sample_entities: list[Entity],
    sample_edges: list[Edge],
    sample_graph: nx.MultiDiGraph,
):
    """Relationship filter restricts edge types."""
    eid = sample_entities[0].entity_id  # damage
    params = GetDependenciesParams(entity_id=eid, relationship="uses", direction="outgoing")
    result = await get_dependencies_tool(test_session, params, sample_graph)

    for dep in result.dependencies:
        assert dep["relationship"] == "uses"
        assert dep["direction"] == "outgoing"


@pytest.mark.asyncio
async def test_get_dependencies_not_in_graph(
    test_session: AsyncSession,
    sample_entities: list[Entity],
    sample_edges: list[Edge],
    sample_graph: nx.MultiDiGraph,
):
    """Entity not in graph returns empty dependencies."""
    # Remove a node to simulate not-in-graph (use Character which has no edges)
    eid = sample_entities[2].entity_id  # Character
    params = GetDependenciesParams(entity_id=eid, direction="both")
    result = await get_dependencies_tool(test_session, params, sample_graph)

    assert result.dependencies == []


# ---------- get_class_hierarchy_tool ----------

@pytest.mark.asyncio
async def test_get_class_hierarchy(
    test_session: AsyncSession,
    sample_entities: list[Entity],
    sample_edges: list[Edge],
    sample_graph: nx.MultiDiGraph,
):
    """Class hierarchy returns (possibly empty) base/derived lists."""
    eid = sample_entities[2].entity_id  # Character
    params = GetClassHierarchyParams(entity_id=eid)
    result = await get_class_hierarchy_tool(test_session, params, sample_graph)

    assert result.entity_id == eid
    # Character has no inherits edges in test data, so both lists may be empty
    assert isinstance(result.base_classes, list)
    assert isinstance(result.derived_classes, list)


# ---------- get_related_entities_tool ----------

@pytest.mark.asyncio
async def test_get_related_entities(
    test_session: AsyncSession,
    sample_entities: list[Entity],
    sample_edges: list[Edge],
    sample_graph: nx.MultiDiGraph,
):
    """Related entities groups neighbors by relationship type."""
    eid = sample_entities[0].entity_id  # damage
    params = GetRelatedEntitiesParams(entity_id=eid)
    result = await get_related_entities_tool(test_session, params, sample_graph)

    assert result.entity_id == eid
    total_neighbors = sum(len(v) for v in result.neighbors_by_relationship.values())
    # damage has: incoming calls from do_kill, outgoing calls to armor_absorb, outgoing uses to max_damage
    assert total_neighbors >= 3


@pytest.mark.asyncio
async def test_get_related_entities_isolated(
    test_session: AsyncSession,
    sample_entities: list[Entity],
    sample_edges: list[Edge],
    sample_graph: nx.MultiDiGraph,
):
    """Entity with no graph edges returns empty neighbors."""
    eid = sample_entities[2].entity_id  # Character (no edges)
    params = GetRelatedEntitiesParams(entity_id=eid)
    result = await get_related_entities_tool(test_session, params, sample_graph)

    total = sum(len(v) for v in result.neighbors_by_relationship.values())
    assert total == 0


# ---------- get_related_files_tool ----------

@pytest.mark.asyncio
async def test_get_related_files(
    test_session: AsyncSession,
    sample_entities: list[Entity],
    sample_edges: list[Edge],
    sample_graph: nx.MultiDiGraph,
):
    """Finds files related via includes edges."""
    params = GetRelatedFilesParams(file_path="src/fight.cc")
    result = await get_related_files_tool(test_session, params, sample_graph)

    assert result.file_path == "src/fight.cc"
    related_paths = [r["file_path"] for r in result.related_files]
    # file_fight_cc → file_character_hh (includes)
    assert "src/include/Character.hh" in related_paths


@pytest.mark.asyncio
async def test_get_related_files_no_includes(
    test_session: AsyncSession,
    sample_entities: list[Entity],
    sample_edges: list[Edge],
    sample_graph: nx.MultiDiGraph,
):
    """File with no includes returns empty list."""
    params = GetRelatedFilesParams(file_path="src/nonexistent.cc")
    result = await get_related_files_tool(test_session, params, sample_graph)

    assert result.related_files == []
