"""
Integration tests for capability system tools.

Tests actual DB execution via mock_ctx of:
- list_capabilities
- get_capability_detail
- compare_capabilities
- list_entry_points
- get_entry_point_info
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from server.db_models import Entity, Edge, Capability, CapabilityEdge, EntryPoint
from server.errors import CapabilityNotFoundError
from server.tools.capability import (
    list_capabilities,
    get_capability_detail,
    compare_capabilities,
    list_entry_points,
    get_entry_point_info,
)


# ---------- list_capabilities ----------

@pytest.mark.asyncio
async def test_list_capabilities(mock_ctx, sample_capabilities):
    """Lists all capabilities sorted by name."""
    result = await list_capabilities(mock_ctx)

    assert len(result.capabilities) == 3
    names = [c.name for c in result.capabilities]
    assert names == sorted(names)  # alphabetically ordered


@pytest.mark.asyncio
async def test_list_capabilities_fields(mock_ctx, sample_capabilities):
    """Capability summaries include all expected fields."""
    result = await list_capabilities(mock_ctx)

    cap = next(c for c in result.capabilities if c.name == "combat")
    assert cap.type == "domain"
    assert cap.function_count == 25
    assert cap.stability == "stable"
    assert isinstance(cap.doc_quality_dist, dict)


# ---------- get_capability_detail ----------

@pytest.mark.asyncio
async def test_get_capability_detail(
    mock_ctx, sample_capabilities, sample_capability_edges, sample_entities, sample_entry_points,
):
    """Returns full capability detail with dependencies."""
    result = await get_capability_detail(mock_ctx, capability="commands")

    detail = result.detail
    assert detail.name == "commands"
    assert detail.type == "policy"
    assert isinstance(detail.dependencies, list)
    # commands → combat dependency edge
    target_caps = [d["target_capability"] for d in detail.dependencies]
    assert "combat" in target_caps


@pytest.mark.asyncio
async def test_get_capability_detail_with_functions(mock_ctx, sample_capabilities, sample_entities):
    """include_functions=True populates function list."""
    result = await get_capability_detail(mock_ctx, capability="combat", include_functions=True)

    assert result.detail.functions is not None
    func_names = [f.name for f in result.detail.functions]
    assert "damage" in func_names


@pytest.mark.asyncio
async def test_get_capability_detail_not_found(mock_ctx, sample_capabilities):
    """Non-existent capability raises CapabilityNotFoundError."""
    with pytest.raises(CapabilityNotFoundError):
        await get_capability_detail(mock_ctx, capability="nonexistent_cap")


# ---------- compare_capabilities ----------

@pytest.mark.asyncio
async def test_compare_capabilities(mock_ctx, sample_capabilities, sample_entities, sample_edges):
    """Compares two capabilities: shared/unique deps and bridges."""
    result = await compare_capabilities(mock_ctx, capabilities=["combat", "commands"], limit=50)

    assert result.capabilities == ["combat", "commands"]
    assert isinstance(result.shared_dependencies, list)
    assert isinstance(result.unique_dependencies, dict)
    assert "combat" in result.unique_dependencies
    assert "commands" in result.unique_dependencies
    assert isinstance(result.bridge_entities, list)


# ---------- list_entry_points ----------

@pytest.mark.asyncio
async def test_list_entry_points(mock_ctx, sample_entities, sample_entry_points):
    """Lists entry point entities."""
    result = await list_entry_points(mock_ctx)

    assert len(result.entry_points) >= 1
    names = [ep.name for ep in result.entry_points]
    assert "do_kill" in names


@pytest.mark.asyncio
async def test_list_entry_points_with_capability_filter(mock_ctx, sample_entities, sample_entry_points):
    """Capability filter restricts entry points."""
    result = await list_entry_points(mock_ctx, capability="commands")

    for ep in result.entry_points:
        assert ep.capability == "commands"


@pytest.mark.asyncio
async def test_list_entry_points_with_name_pattern(mock_ctx, sample_entities, sample_entry_points):
    """Name pattern filter (SQL LIKE) restricts entry points."""
    result = await list_entry_points(mock_ctx, name_pattern="do_%")

    for ep in result.entry_points:
        assert ep.name.startswith("do_")


@pytest.mark.asyncio
async def test_list_entry_points_empty(mock_ctx, sample_entities, sample_entry_points):
    """Non-matching filter returns empty list."""
    result = await list_entry_points(mock_ctx, capability="nonexistent_cap")

    assert result.entry_points == []


# ---------- get_entry_point_info ----------

@pytest.mark.asyncio
async def test_get_entry_point_info(mock_ctx, sample_entities, sample_edges, sample_entry_points):
    """Entry point info shows capabilities exercised."""
    eid = sample_entities[1].entity_id  # do_kill
    result = await get_entry_point_info(mock_ctx, entity_id=eid)

    assert result.entry_point.entity_id == eid
    assert isinstance(result.capabilities_exercised, dict)
    # do_kill → damage (combat), damage → armor_absorb (combat)
    assert "combat" in result.capabilities_exercised


@pytest.mark.asyncio
async def test_get_entry_point_info_not_entry_point(mock_ctx, sample_entities, sample_edges):
    """Non-entry-point entity raises ValueError."""
    eid = sample_entities[0].entity_id  # damage (not an entry point)
    with pytest.raises(ValueError, match="not an entry point"):
        await get_entry_point_info(mock_ctx, entity_id=eid)
