"""
Integration tests for behavioral analysis tools.

Tests actual DB + graph execution of:
- get_behavior_slice_tool
- get_state_touches_tool
- get_hotspots_tool
"""

import pytest
import networkx as nx
from sqlalchemy.ext.asyncio import AsyncSession

from server.db_models import Entity, Edge
from server.errors import EntityNotFoundError
from server.tools.behavior import (
    GetBehaviorSliceParams,
    GetStateTouchesParams,
    GetHotspotsParams,
    get_behavior_slice_tool,
    get_state_touches_tool,
    get_hotspots_tool,
)


# ---------- get_behavior_slice_tool ----------

@pytest.mark.asyncio
async def test_behavior_slice_basic(
    test_session: AsyncSession,
    sample_entities: list[Entity],
    sample_edges: list[Edge],
    sample_graph: nx.MultiDiGraph,
):
    """Behavior slice computes call cone from entry point."""
    eid = sample_entities[1].entity_id  # do_kill
    params = GetBehaviorSliceParams(entity_id=eid, max_depth=3, max_cone_size=50)
    result = await get_behavior_slice_tool(test_session, params, sample_graph)

    b = result.behavior
    assert b.entry_point.entity_id == eid
    assert isinstance(b.direct_callees, list)
    assert isinstance(b.transitive_cone, list)

    # do_kill → damage (direct), damage → armor_absorb (transitive)
    direct_names = [s.name for s in b.direct_callees]
    assert "damage" in direct_names

    transitive_names = [s.name for s in b.transitive_cone]
    assert "armor_absorb" in transitive_names


@pytest.mark.asyncio
async def test_behavior_slice_capabilities_touched(
    test_session: AsyncSession,
    sample_entities: list[Entity],
    sample_edges: list[Edge],
    sample_graph: nx.MultiDiGraph,
):
    """Behavior slice reports capabilities exercised by the cone."""
    eid = sample_entities[1].entity_id  # do_kill
    params = GetBehaviorSliceParams(entity_id=eid, max_depth=3, max_cone_size=50)
    result = await get_behavior_slice_tool(test_session, params, sample_graph)

    caps = result.behavior.capabilities_touched
    assert isinstance(caps, dict)
    # damage and armor_absorb are in "combat"
    assert "combat" in caps


@pytest.mark.asyncio
async def test_behavior_slice_side_effects(
    test_session: AsyncSession,
    sample_entities: list[Entity],
    sample_edges: list[Edge],
    sample_graph: nx.MultiDiGraph,
):
    """Behavior slice extracts side effect markers."""
    eid = sample_entities[1].entity_id  # do_kill
    params = GetBehaviorSliceParams(entity_id=eid, max_depth=3, max_cone_size=50)
    result = await get_behavior_slice_tool(test_session, params, sample_graph)

    se = result.behavior.side_effects
    assert isinstance(se, dict)
    # damage has messaging + state_mutation markers
    assert "messaging" in se or "state_mutation" in se


@pytest.mark.asyncio
async def test_behavior_slice_globals(
    test_session: AsyncSession,
    sample_entities: list[Entity],
    sample_edges: list[Edge],
    sample_graph: nx.MultiDiGraph,
):
    """Behavior slice detects global variable usage via USES edges."""
    eid = sample_entities[1].entity_id  # do_kill
    params = GetBehaviorSliceParams(entity_id=eid, max_depth=3, max_cone_size=50)
    result = await get_behavior_slice_tool(test_session, params, sample_graph)

    globals_used = result.behavior.globals_used
    global_names = [g.name for g in globals_used]
    # damage → max_damage (uses)
    assert "max_damage" in global_names


@pytest.mark.asyncio
async def test_behavior_slice_not_found(
    test_session: AsyncSession,
    sample_entities: list[Entity],
    sample_edges: list[Edge],
    sample_graph: nx.MultiDiGraph,
):
    """Non-existent entity raises EntityNotFoundError."""
    params = GetBehaviorSliceParams(entity_id="nonexistent_xyz")
    with pytest.raises(EntityNotFoundError):
        await get_behavior_slice_tool(test_session, params, sample_graph)


@pytest.mark.asyncio
async def test_behavior_slice_truncation_metadata(
    test_session: AsyncSession,
    sample_entities: list[Entity],
    sample_edges: list[Edge],
    sample_graph: nx.MultiDiGraph,
):
    """Truncation metadata is populated."""
    eid = sample_entities[1].entity_id
    params = GetBehaviorSliceParams(entity_id=eid, max_depth=3, max_cone_size=50)
    result = await get_behavior_slice_tool(test_session, params, sample_graph)

    assert result.truncation.max_depth_requested == 3
    assert result.truncation.node_count >= 0


# ---------- get_state_touches_tool ----------

@pytest.mark.asyncio
async def test_state_touches_direct(
    test_session: AsyncSession,
    sample_entities: list[Entity],
    sample_edges: list[Edge],
    sample_graph: nx.MultiDiGraph,
):
    """Direct state touches finds variables via USES edges."""
    eid = sample_entities[0].entity_id  # damage
    params = GetStateTouchesParams(entity_id=eid)
    result = await get_state_touches_tool(test_session, params, sample_graph)

    assert result.entity_id == eid
    direct_names = [u.name for u in result.direct_uses]
    assert "max_damage" in direct_names


@pytest.mark.asyncio
async def test_state_touches_transitive(
    test_session: AsyncSession,
    sample_entities: list[Entity],
    sample_edges: list[Edge],
    sample_graph: nx.MultiDiGraph,
):
    """Transitive state touches finds variables via CALLS→USES 2-hop."""
    eid = sample_entities[1].entity_id  # do_kill
    params = GetStateTouchesParams(entity_id=eid)
    result = await get_state_touches_tool(test_session, params, sample_graph)

    assert result.entity_id == eid
    # do_kill calls damage, damage uses max_damage → transitive
    transitive_names = [u.name for u in result.transitive_uses]
    assert "max_damage" in transitive_names


@pytest.mark.asyncio
async def test_state_touches_side_effects(
    test_session: AsyncSession,
    sample_entities: list[Entity],
    sample_edges: list[Edge],
    sample_graph: nx.MultiDiGraph,
):
    """Side effects are extracted from callees."""
    eid = sample_entities[1].entity_id  # do_kill
    params = GetStateTouchesParams(entity_id=eid)
    result = await get_state_touches_tool(test_session, params, sample_graph)

    assert isinstance(result.direct_side_effects, list)
    assert isinstance(result.transitive_side_effects, list)
    # damage (direct callee of do_kill) has side_effect_markers
    categories = [m.category for m in result.direct_side_effects]
    assert "messaging" in categories or "state_mutation" in categories


# ---------- get_hotspots_tool ----------

@pytest.mark.asyncio
async def test_hotspots_fan_in(test_session: AsyncSession, sample_entities: list[Entity]):
    """Fan-in hotspots ranked by fan_in descending."""
    params = GetHotspotsParams(metric="fan_in", limit=5)
    result = await get_hotspots_tool(test_session, params)

    assert result.metric == "fan_in"
    assert len(result.hotspots) >= 1
    # damage has fan_in=23 (highest)
    assert result.hotspots[0].name == "damage"


@pytest.mark.asyncio
async def test_hotspots_fan_out(test_session: AsyncSession, sample_entities: list[Entity]):
    """Fan-out hotspots ranked by fan_out descending."""
    params = GetHotspotsParams(metric="fan_out", limit=5)
    result = await get_hotspots_tool(test_session, params)

    assert result.metric == "fan_out"
    assert len(result.hotspots) >= 1
    # do_kill has fan_out=15 (highest)
    assert result.hotspots[0].name == "do_kill"


@pytest.mark.asyncio
async def test_hotspots_bridge(test_session: AsyncSession, sample_entities: list[Entity]):
    """Bridge hotspots filter to is_bridge=True."""
    params = GetHotspotsParams(metric="bridge", limit=5)
    result = await get_hotspots_tool(test_session, params)

    assert result.metric == "bridge"
    # Only damage has is_bridge=True
    if result.hotspots:
        assert result.hotspots[0].name == "damage"


@pytest.mark.asyncio
async def test_hotspots_underdocumented(test_session: AsyncSession, sample_entities: list[Entity]):
    """Underdocumented hotspots filter to low/medium quality."""
    params = GetHotspotsParams(metric="underdocumented", limit=5)
    result = await get_hotspots_tool(test_session, params)

    assert result.metric == "underdocumented"
    for h in result.hotspots:
        assert h.doc_quality in ("low", "medium")


@pytest.mark.asyncio
async def test_hotspots_with_capability_filter(test_session: AsyncSession, sample_entities: list[Entity]):
    """Capability filter restricts results."""
    params = GetHotspotsParams(metric="fan_in", capability="combat", limit=5)
    result = await get_hotspots_tool(test_session, params)

    for h in result.hotspots:
        assert h.capability == "combat"


@pytest.mark.asyncio
async def test_hotspots_with_kind_filter(test_session: AsyncSession, sample_entities: list[Entity]):
    """Kind filter restricts results."""
    params = GetHotspotsParams(metric="fan_in", kind="function", limit=5)
    result = await get_hotspots_tool(test_session, params)

    for h in result.hotspots:
        assert h.kind == "function"
