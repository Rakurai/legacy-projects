"""
Integration tests for capability system tools.

Tests actual DB execution of:
- list_capabilities_tool
- get_capability_detail_tool
- compare_capabilities_tool
- list_entry_points_tool
- get_entry_point_info_tool
"""

import pytest
import networkx as nx
from sqlalchemy.ext.asyncio import AsyncSession

from server.db_models import Entity, Edge, Capability, CapabilityEdge, EntryPoint
from server.errors import CapabilityNotFoundError, EntityNotFoundError
from server.tools.capability import (
    ListCapabilitiesParams,
    GetCapabilityDetailParams,
    CompareCapabilitiesParams,
    ListEntryPointsParams,
    GetEntryPointInfoParams,
    list_capabilities_tool,
    get_capability_detail_tool,
    compare_capabilities_tool,
    list_entry_points_tool,
    get_entry_point_info_tool,
)


# ---------- list_capabilities_tool ----------

@pytest.mark.asyncio
async def test_list_capabilities(
    test_session: AsyncSession,
    sample_capabilities: list[Capability],
):
    """Lists all capabilities sorted by name."""
    result = await list_capabilities_tool(test_session, ListCapabilitiesParams())

    assert len(result.capabilities) == 3
    names = [c.name for c in result.capabilities]
    assert names == sorted(names)  # alphabetically ordered


@pytest.mark.asyncio
async def test_list_capabilities_fields(
    test_session: AsyncSession,
    sample_capabilities: list[Capability],
):
    """Capability summaries include all expected fields."""
    result = await list_capabilities_tool(test_session, ListCapabilitiesParams())

    cap = next(c for c in result.capabilities if c.name == "combat")
    assert cap.type == "domain"
    assert cap.function_count == 25
    assert cap.stability == "stable"
    assert isinstance(cap.doc_quality_dist, dict)


# ---------- get_capability_detail_tool ----------

@pytest.mark.asyncio
async def test_get_capability_detail(
    test_session: AsyncSession,
    sample_capabilities: list[Capability],
    sample_capability_edges: list[CapabilityEdge],
    sample_entities: list[Entity],
    sample_entry_points: list[EntryPoint],
):
    """Returns full capability detail with dependencies."""
    params = GetCapabilityDetailParams(capability="commands")
    result = await get_capability_detail_tool(test_session, params)

    detail = result.detail
    assert detail.name == "commands"
    assert detail.type == "policy"
    assert isinstance(detail.dependencies, list)
    # commands → combat dependency edge
    target_caps = [d["target_capability"] for d in detail.dependencies]
    assert "combat" in target_caps


@pytest.mark.asyncio
async def test_get_capability_detail_with_functions(
    test_session: AsyncSession,
    sample_capabilities: list[Capability],
    sample_entities: list[Entity],
):
    """include_functions=True populates function list."""
    params = GetCapabilityDetailParams(capability="combat", include_functions=True)
    result = await get_capability_detail_tool(test_session, params)

    assert result.detail.functions is not None
    func_names = [f.name for f in result.detail.functions]
    assert "damage" in func_names


@pytest.mark.asyncio
async def test_get_capability_detail_not_found(
    test_session: AsyncSession,
    sample_capabilities: list[Capability],
):
    """Non-existent capability raises CapabilityNotFoundError."""
    params = GetCapabilityDetailParams(capability="nonexistent_cap")
    with pytest.raises(CapabilityNotFoundError):
        await get_capability_detail_tool(test_session, params)


# ---------- compare_capabilities_tool ----------

@pytest.mark.asyncio
async def test_compare_capabilities(
    test_session: AsyncSession,
    sample_capabilities: list[Capability],
    sample_entities: list[Entity],
    sample_edges: list[Edge],
    sample_graph: nx.MultiDiGraph,
):
    """Compares two capabilities: shared/unique deps and bridges."""
    params = CompareCapabilitiesParams(capabilities=["combat", "commands"], limit=50)
    result = await compare_capabilities_tool(test_session, params, sample_graph)

    assert result.capabilities == ["combat", "commands"]
    assert isinstance(result.shared_dependencies, list)
    assert isinstance(result.unique_dependencies, dict)
    assert "combat" in result.unique_dependencies
    assert "commands" in result.unique_dependencies
    assert isinstance(result.bridge_entities, list)


# ---------- list_entry_points_tool ----------

@pytest.mark.asyncio
async def test_list_entry_points(
    test_session: AsyncSession,
    sample_entities: list[Entity],
    sample_entry_points: list[EntryPoint],
):
    """Lists entry point entities."""
    params = ListEntryPointsParams()
    result = await list_entry_points_tool(test_session, params)

    assert len(result.entry_points) >= 1
    names = [ep.name for ep in result.entry_points]
    assert "do_kill" in names


@pytest.mark.asyncio
async def test_list_entry_points_with_capability_filter(
    test_session: AsyncSession,
    sample_entities: list[Entity],
    sample_entry_points: list[EntryPoint],
):
    """Capability filter restricts entry points."""
    params = ListEntryPointsParams(capability="commands")
    result = await list_entry_points_tool(test_session, params)

    for ep in result.entry_points:
        assert ep.capability == "commands"


@pytest.mark.asyncio
async def test_list_entry_points_with_name_pattern(
    test_session: AsyncSession,
    sample_entities: list[Entity],
    sample_entry_points: list[EntryPoint],
):
    """Name pattern filter (SQL LIKE) restricts entry points."""
    params = ListEntryPointsParams(name_pattern="do_%")
    result = await list_entry_points_tool(test_session, params)

    for ep in result.entry_points:
        assert ep.name.startswith("do_")


@pytest.mark.asyncio
async def test_list_entry_points_empty(
    test_session: AsyncSession,
    sample_entities: list[Entity],
    sample_entry_points: list[EntryPoint],
):
    """Non-matching filter returns empty list."""
    params = ListEntryPointsParams(capability="nonexistent_cap")
    result = await list_entry_points_tool(test_session, params)

    assert result.entry_points == []


# ---------- get_entry_point_info_tool ----------

@pytest.mark.asyncio
async def test_get_entry_point_info(
    test_session: AsyncSession,
    sample_entities: list[Entity],
    sample_edges: list[Edge],
    sample_entry_points: list[EntryPoint],
    sample_graph: nx.MultiDiGraph,
):
    """Entry point info shows capabilities exercised."""
    eid = sample_entities[1].entity_id  # do_kill
    params = GetEntryPointInfoParams(entity_id=eid)
    result = await get_entry_point_info_tool(test_session, params, sample_graph)

    assert result.entry_point.entity_id == eid
    assert isinstance(result.capabilities_exercised, dict)
    # do_kill → damage (combat), damage → armor_absorb (combat)
    assert "combat" in result.capabilities_exercised


@pytest.mark.asyncio
async def test_get_entry_point_info_not_entry_point(
    test_session: AsyncSession,
    sample_entities: list[Entity],
    sample_edges: list[Edge],
    sample_graph: nx.MultiDiGraph,
):
    """Non-entry-point entity raises ValueError."""
    eid = sample_entities[0].entity_id  # damage (not an entry point)
    params = GetEntryPointInfoParams(entity_id=eid)
    with pytest.raises(ValueError, match="not an entry point"):
        await get_entry_point_info_tool(test_session, params, sample_graph)
