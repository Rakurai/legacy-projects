"""Integration tests for graph navigation tools."""

import pytest

from server.tools.graph import (
    get_callees,
    get_callers,
    get_class_hierarchy,
    get_dependencies,
    get_related_entities,
)

# ---------- get_callers ----------


@pytest.mark.asyncio
async def test_get_callers(mock_ctx, sample_entities, sample_edges):
    """Finds callers at depth 1."""
    eid = sample_entities[0].entity_id  # damage
    result = await get_callers(mock_ctx, entity_id=eid, depth=1)

    assert result.entity_id == eid
    assert 1 in result.callers_by_depth
    caller_names = [s.name for s in result.callers_by_depth[1]]
    assert "do_kill" in caller_names


@pytest.mark.asyncio
async def test_get_callers_no_callers(mock_ctx, sample_entities, sample_edges):
    """Entity with no callers returns empty depth map."""
    eid = sample_entities[1].entity_id  # do_kill (no one calls it)
    result = await get_callers(mock_ctx, entity_id=eid, depth=1)

    assert result.entity_id == eid
    total = sum(len(v) for v in result.callers_by_depth.values())
    assert total == 0


# ---------- get_callees ----------


@pytest.mark.asyncio
async def test_get_callees(mock_ctx, sample_entities, sample_edges):
    """Finds callees at depth 1."""
    eid = sample_entities[1].entity_id  # do_kill
    result = await get_callees(mock_ctx, entity_id=eid, depth=1)

    assert result.entity_id == eid
    assert 1 in result.callees_by_depth
    callee_names = [s.name for s in result.callees_by_depth[1]]
    assert "damage" in callee_names


@pytest.mark.asyncio
async def test_get_callees_depth_2(mock_ctx, sample_entities, sample_edges):
    """Depth-2 traversal finds transitive callees."""
    eid = sample_entities[1].entity_id  # do_kill
    result = await get_callees(mock_ctx, entity_id=eid, depth=2)

    # do_kill → damage (depth 1) → armor_absorb (depth 2)
    all_names = []
    for depth_summaries in result.callees_by_depth.values():
        all_names.extend(s.name for s in depth_summaries)
    assert "damage" in all_names
    assert "armor_absorb" in all_names


# ---------- get_dependencies ----------


@pytest.mark.asyncio
async def test_get_dependencies(mock_ctx, sample_entities, sample_edges):
    """Returns filtered dependencies."""
    eid = sample_entities[0].entity_id  # damage
    result = await get_dependencies(mock_ctx, entity_id=eid, direction="outgoing")

    assert result.entity_id == eid
    assert len(result.dependencies) >= 2
    # damage has outgoing: calls → armor_absorb, uses → max_damage
    rel_types = {d["relationship"] for d in result.dependencies}
    assert "calls" in rel_types
    assert "uses" in rel_types


@pytest.mark.asyncio
async def test_get_dependencies_with_relationship_filter(mock_ctx, sample_entities, sample_edges):
    """Relationship filter restricts results."""
    eid = sample_entities[0].entity_id  # damage
    result = await get_dependencies(mock_ctx, entity_id=eid, relationship="uses", direction="outgoing")

    for dep in result.dependencies:
        assert dep["relationship"] == "uses"
        assert dep["direction"] == "outgoing"


# ---------- get_class_hierarchy ----------


@pytest.mark.asyncio
async def test_get_class_hierarchy(mock_ctx, sample_entities, sample_edges):
    """Default direction='both' returns base + derived classes."""
    eid = sample_entities[2].entity_id  # Character class — inherits → Character.hh
    result = await get_class_hierarchy(mock_ctx, entity_id=eid)

    assert result.entity_id == eid
    # Character inherits Character.hh (as base class stand-in)
    base_names = [s.name for s in result.base_classes]
    assert "Character.hh" in base_names


@pytest.mark.asyncio
async def test_get_class_hierarchy_ancestors_only(mock_ctx, sample_entities, sample_edges):
    """direction='ancestors' returns only base_classes, derived empty."""
    eid = sample_entities[2].entity_id
    result = await get_class_hierarchy(mock_ctx, entity_id=eid, direction="ancestors")

    base_names = [s.name for s in result.base_classes]
    assert "Character.hh" in base_names
    assert result.derived_classes == []


@pytest.mark.asyncio
async def test_get_class_hierarchy_descendants_only(mock_ctx, sample_entities, sample_edges):
    """direction='descendants' returns only derived_classes, base empty."""
    eid = sample_entities[2].entity_id
    result = await get_class_hierarchy(mock_ctx, entity_id=eid, direction="descendants")

    assert result.base_classes == []
    # Character has no derived classes in test data
    assert result.derived_classes == []


# ---------- get_related_entities ----------


@pytest.mark.asyncio
async def test_get_related_entities(mock_ctx, sample_entities, sample_edges):
    """Returns neighbors grouped by relationship type."""
    eid = sample_entities[0].entity_id  # damage
    result = await get_related_entities(mock_ctx, entity_id=eid)

    assert result.entity_id == eid
    # damage has: incoming calls from do_kill, outgoing calls to armor_absorb, outgoing uses
    total = sum(len(v) for v in result.neighbors_by_relationship.values())
    assert total >= 1


@pytest.mark.asyncio
async def test_get_related_entities_isolated(mock_ctx, sample_entities, sample_edges):
    """Entity with only inherits edges returns non-empty neighbors."""
    # Character has exactly one edge: inherits → Character.hh
    eid = sample_entities[2].entity_id
    result = await get_related_entities(mock_ctx, entity_id=eid)

    total = sum(len(v) for v in result.neighbors_by_relationship.values())
    assert total == 1
