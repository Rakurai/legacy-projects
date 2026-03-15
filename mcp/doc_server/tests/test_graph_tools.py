"""
Integration tests for graph navigation tools.

Tests actual DB + graph execution via mock_ctx of:
- get_callers
- get_callees
- get_dependencies
- get_class_hierarchy
- get_related_entities
- get_related_files
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from server.db_models import Entity, Edge
from server.tools.graph import (
    get_callers,
    get_callees,
    get_dependencies,
    get_class_hierarchy,
    get_related_entities,
    get_related_files,
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
    """Returns empty hierarchy when no inherits edges exist."""
    eid = sample_entities[2].entity_id  # Character class — no inherits edges in test data
    result = await get_class_hierarchy(mock_ctx, entity_id=eid)

    assert result.entity_id == eid
    assert result.base_classes == []
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
    """Entity not in graph returns empty neighbors."""
    # Character class has no edges in sample_edges
    eid = sample_entities[2].entity_id
    result = await get_related_entities(mock_ctx, entity_id=eid)

    total = sum(len(v) for v in result.neighbors_by_relationship.values())
    assert total == 0


# ---------- get_related_files ----------

@pytest.mark.asyncio
async def test_get_related_files(mock_ctx, sample_entities, sample_edges):
    """Finds files related via includes edges."""
    result = await get_related_files(mock_ctx, file_path="src/fight.cc")

    assert result.file_path == "src/fight.cc"
    related_paths = [r["file_path"] for r in result.related_files]
    # file_fight_cc → file_character_hh (includes)
    assert "src/include/Character.hh" in related_paths


@pytest.mark.asyncio
async def test_get_related_files_no_includes(mock_ctx, sample_entities, sample_edges):
    """File with no includes returns empty list."""
    result = await get_related_files(mock_ctx, file_path="src/nonexistent.cc")

    assert result.related_files == []
