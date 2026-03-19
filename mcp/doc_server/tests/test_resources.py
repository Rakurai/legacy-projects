"""
Integration tests for MCP resource handlers.

Tests actual DB execution of:
- get_capabilities_resource
- get_capability_detail_resource
- get_entity_resource
- get_file_entities_resource
- get_stats_resource
"""

import pytest
import networkx as nx
from sqlalchemy.ext.asyncio import AsyncSession

from server.db_models import Entity, Edge, Capability, CapabilityEdge, EntryPoint
from server.resources import (
    get_capabilities_resource,
    get_capability_detail_resource,
    get_entity_resource,
    get_file_entities_resource,
    get_stats_resource,
)


# ---------- get_capabilities_resource ----------


@pytest.mark.asyncio
async def test_capabilities_resource(
    test_session: AsyncSession,
    sample_capabilities: list[Capability],
):
    """Returns all capabilities in a dict."""
    data = await get_capabilities_resource(test_session)

    assert "capabilities" in data
    assert len(data["capabilities"]) == 3
    names = [c["name"] for c in data["capabilities"]]
    assert "combat" in names
    assert "commands" in names


@pytest.mark.asyncio
async def test_capabilities_resource_fields(
    test_session: AsyncSession,
    sample_capabilities: list[Capability],
):
    """Each capability dict has expected fields."""
    data = await get_capabilities_resource(test_session)

    cap = next(c for c in data["capabilities"] if c["name"] == "combat")
    assert cap["type"] == "domain"
    assert cap["function_count"] == 25


# ---------- get_capability_detail_resource ----------


@pytest.mark.asyncio
async def test_capability_detail_resource(
    test_session: AsyncSession,
    sample_capabilities: list[Capability],
    sample_capability_edges: list[CapabilityEdge],
    sample_entities: list[Entity],
):
    """Returns full capability detail with dependencies."""
    data = await get_capability_detail_resource(test_session, "commands")

    assert data["name"] == "commands"
    assert isinstance(data["dependencies"], list)
    target_caps = [d["target_capability"] for d in data["dependencies"]]
    assert "combat" in target_caps


@pytest.mark.asyncio
async def test_capability_detail_resource_not_found(
    test_session: AsyncSession,
    sample_capabilities: list[Capability],
):
    """Non-existent capability raises ValueError."""
    with pytest.raises(ValueError, match="not found"):
        await get_capability_detail_resource(test_session, "nonexistent_cap")


# ---------- get_entity_resource ----------


@pytest.mark.asyncio
async def test_entity_resource(
    test_session: AsyncSession,
    sample_entities: list[Entity],
):
    """Returns full entity detail dict."""
    eid = sample_entities[0].entity_id
    data = await get_entity_resource(test_session, eid)

    assert data["entity_id"] == eid
    assert data["name"] == "damage"
    assert data["kind"] == "function"
    assert data["brief"] is not None
    assert data["source_text"] is not None


@pytest.mark.asyncio
async def test_entity_resource_not_found(
    test_session: AsyncSession,
    sample_entities: list[Entity],
):
    """Non-existent entity raises ValueError."""
    with pytest.raises(ValueError, match="not found"):
        await get_entity_resource(test_session, "nonexistent_xyz")


# ---------- get_file_entities_resource ----------


@pytest.mark.asyncio
async def test_file_entities_resource(
    test_session: AsyncSession,
    sample_entities: list[Entity],
):
    """Returns entities for a file path."""
    data = await get_file_entities_resource(test_session, "src/fight.cc")

    assert data["file_path"] == "src/fight.cc"
    assert data["entity_count"] >= 3
    assert isinstance(data["entities"], list)


@pytest.mark.asyncio
async def test_file_entities_resource_empty(
    test_session: AsyncSession,
    sample_entities: list[Entity],
):
    """Non-existent file returns empty list."""
    data = await get_file_entities_resource(test_session, "src/nonexistent.cc")

    assert data["entity_count"] == 0
    assert data["entities"] == []


# ---------- get_stats_resource ----------


@pytest.mark.asyncio
async def test_stats_resource(
    test_session: AsyncSession,
    sample_entities: list[Entity],
    sample_capabilities: list[Capability],
    sample_entry_points: list[EntryPoint],
    sample_graph: nx.MultiDiGraph,
    sample_edges: list[Edge],
):
    """Returns aggregate statistics."""
    data = await get_stats_resource(
        test_session,
        graph=sample_graph,
        embedding_available=False,
    )

    assert "entity_stats" in data
    assert data["entity_stats"]["total_entities"] >= 3

    assert "graph_stats" in data
    assert data["graph_stats"]["total_nodes"] > 0
    assert data["graph_stats"]["total_edges"] > 0

    assert "capability_stats" in data
    assert data["capability_stats"]["total_capabilities"] == 3

    assert "server_info" in data
    assert data["server_info"]["version"] == "1.0.0"
    assert data["server_info"]["embedding_endpoint_available"] is False


@pytest.mark.asyncio
async def test_stats_resource_no_graph(
    test_session: AsyncSession,
    sample_entities: list[Entity],
    sample_capabilities: list[Capability],
    sample_entry_points: list[EntryPoint],
    sample_edges: list[Edge],
):
    """Stats work without graph (graceful degradation)."""
    data = await get_stats_resource(test_session, graph=None, embedding_available=True)

    assert data["graph_stats"]["total_nodes"] == 0
    assert data["graph_stats"]["total_edges"] == 0
    assert data["server_info"]["embedding_endpoint_available"] is True
