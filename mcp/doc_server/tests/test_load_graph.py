"""
Integration tests for server.graph.load_graph().

Verifies that the graph is correctly loaded from the edges table,
including edge type counts pre-computation.
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from server.db_models import Entity, Edge
from server.graph import load_graph, CALLS, USES, INCLUDES


@pytest.mark.asyncio
async def test_load_graph_basic(test_session: AsyncSession, sample_entities: list[Entity], sample_edges: list[Edge]):
    """load_graph returns a graph with correct node and edge counts."""
    graph = await load_graph(test_session)

    # Edges table has 4 edges; each edge adds both source and target as nodes
    assert graph.number_of_edges() == len(sample_edges)
    assert graph.number_of_nodes() > 0


@pytest.mark.asyncio
async def test_load_graph_edge_types(test_session: AsyncSession, sample_entities: list[Entity], sample_edges: list[Edge]):
    """load_graph preserves edge relationship types."""
    graph = await load_graph(test_session)

    # Check that edge types are stored correctly
    edge_types = set()
    for u, v, data in graph.edges(data=True):
        edge_types.add(data["type"])

    assert CALLS in edge_types
    assert USES in edge_types
    assert INCLUDES in edge_types


@pytest.mark.asyncio
async def test_load_graph_edge_type_counts(test_session: AsyncSession, sample_entities: list[Entity], sample_edges: list[Edge]):
    """load_graph pre-computes edge_type_counts on the graph object."""
    graph = await load_graph(test_session)

    counts = graph.graph["edge_type_counts"]
    assert isinstance(counts, dict)
    assert counts[CALLS] == 2    # do_kill→damage, damage→armor_absorb
    assert counts[USES] == 1     # damage→max_damage
    assert counts[INCLUDES] == 1  # fight.cc→Character.hh


@pytest.mark.asyncio
async def test_load_graph_empty_table(test_session: AsyncSession):
    """load_graph with no edges returns an empty graph with empty counts."""
    graph = await load_graph(test_session)

    assert graph.number_of_nodes() == 0
    assert graph.number_of_edges() == 0
    assert graph.graph["edge_type_counts"] == {}


@pytest.mark.asyncio
async def test_load_graph_connectivity(test_session: AsyncSession, sample_entities: list[Entity], sample_edges: list[Edge]):
    """load_graph produces correct source→target edges for BFS traversal."""
    graph = await load_graph(test_session)

    # do_kill → damage should exist
    assert graph.has_edge(
        sample_entities[1].entity_id,
        sample_entities[0].entity_id,
    )

    # damage → armor_absorb should exist
    assert graph.has_edge(
        sample_entities[0].entity_id,
        sample_entities[4].entity_id,
    )

    # Reverse direction should NOT exist (directed graph)
    assert not graph.has_edge(
        sample_entities[0].entity_id,
        sample_entities[1].entity_id,
    )
