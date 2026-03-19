"""
Integration tests for behavioral analysis tools.

Tests actual DB + graph execution via mock_ctx of:
- get_behavior_slice
- get_state_touches
"""

import pytest

from server.errors import EntityNotFoundError
from server.tools.behavior import (
    get_behavior_slice,
    get_state_touches,
)

# ---------- get_behavior_slice ----------


@pytest.mark.asyncio
async def test_behavior_slice_basic(mock_ctx, sample_entities, sample_edges):
    """Behavior slice computes call cone from entry point."""
    eid = sample_entities[1].entity_id  # do_kill
    result = await get_behavior_slice(mock_ctx, entity_id=eid, max_depth=3, max_cone_size=50)

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
async def test_behavior_slice_capabilities_touched(mock_ctx, sample_entities, sample_edges):
    """Behavior slice reports capabilities exercised by the cone."""
    eid = sample_entities[1].entity_id  # do_kill
    result = await get_behavior_slice(mock_ctx, entity_id=eid, max_depth=3, max_cone_size=50)

    caps = result.behavior.capabilities_touched
    assert isinstance(caps, dict)
    # damage and armor_absorb are in "combat"
    assert "combat" in caps


@pytest.mark.asyncio
async def test_behavior_slice_globals(mock_ctx, sample_entities, sample_edges):
    """Behavior slice detects global variable usage via USES edges."""
    eid = sample_entities[1].entity_id  # do_kill
    result = await get_behavior_slice(mock_ctx, entity_id=eid, max_depth=3, max_cone_size=50)

    globals_used = result.behavior.globals_used
    global_names = [g.name for g in globals_used]
    # damage → max_damage (uses)
    assert "max_damage" in global_names


@pytest.mark.asyncio
async def test_behavior_slice_not_found(mock_ctx, sample_entities, sample_edges):
    """Non-existent entity raises EntityNotFoundError."""
    with pytest.raises(EntityNotFoundError):
        await get_behavior_slice(mock_ctx, entity_id="nonexistent_xyz")


@pytest.mark.asyncio
async def test_behavior_slice_truncation_metadata(mock_ctx, sample_entities, sample_edges):
    """Truncation metadata is populated."""
    eid = sample_entities[1].entity_id
    result = await get_behavior_slice(mock_ctx, entity_id=eid, max_depth=3, max_cone_size=50)

    assert result.truncation.max_depth_requested == 3
    # do_kill → damage → armor_absorb: cone has 2 reachable nodes (entry point not counted)
    assert result.truncation.node_count == 2


# ---------- get_state_touches ----------


@pytest.mark.asyncio
async def test_state_touches_direct(mock_ctx, sample_entities, sample_edges):
    """Direct state touches finds variables via USES edges."""
    eid = sample_entities[0].entity_id  # damage
    result = await get_state_touches(mock_ctx, entity_id=eid)

    assert result.entity_id == eid
    direct_names = [u.name for u in result.direct_uses]
    assert "max_damage" in direct_names


@pytest.mark.asyncio
async def test_state_touches_transitive(mock_ctx, sample_entities, sample_edges):
    """Transitive state touches finds variables via CALLS→USES 2-hop."""
    eid = sample_entities[1].entity_id  # do_kill
    result = await get_state_touches(mock_ctx, entity_id=eid)

    assert result.entity_id == eid
    # do_kill calls damage, damage uses max_damage → transitive
    transitive_names = [u.name for u in result.transitive_uses]
    assert "max_damage" in transitive_names


@pytest.mark.asyncio
async def test_state_touches_side_effects(mock_ctx, sample_entities, sample_edges):
    """Side effect fields are no longer present."""
    eid = sample_entities[1].entity_id  # do_kill
    result = await get_state_touches(mock_ctx, entity_id=eid)

    assert not hasattr(result, "direct_side_effects")
    assert not hasattr(result, "transitive_side_effects")
