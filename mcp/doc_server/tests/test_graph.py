"""
Unit tests for graph algorithms - compute_call_cone, get_callers, get_callees,
get_class_hierarchy.

These test pure functions that operate on a synthetic NetworkX graph,
so no database or async fixtures are needed.
"""

import networkx as nx
import pytest

from server.graph import (
    compute_call_cone,
    get_callers,
    get_callees,
    get_class_hierarchy,
)


@pytest.fixture
def sample_graph() -> nx.MultiDiGraph:
    """
    Build a synthetic dependency graph for testing.

    Structure:
        main → do_kill → damage → send_to_char
                       → affect_to_char
               → do_look → show_room_to_char
        Character ← inherits ← Player
        Character ← inherits ← MobilePrototype
    """
    g = nx.MultiDiGraph()

    # CALLS edges
    g.add_edge("main", "do_kill", key="calls", type="calls")
    g.add_edge("do_kill", "damage", key="calls", type="calls")
    g.add_edge("do_kill", "do_look", key="calls", type="calls")
    g.add_edge("damage", "send_to_char", key="calls", type="calls")
    g.add_edge("damage", "affect_to_char", key="calls", type="calls")
    g.add_edge("do_look", "show_room_to_char", key="calls", type="calls")

    # USES edges (should be ignored by calls-only traversals)
    g.add_edge("damage", "global_dam_stat", key="uses", type="uses")

    # INHERITS edges
    g.add_edge("Player", "Character", key="inherits", type="inherits")
    g.add_edge("MobilePrototype", "Character", key="inherits", type="inherits")

    return g


class TestComputeCallCone:
    """Tests for compute_call_cone."""

    def test_basic_cone(self, sample_graph: nx.MultiDiGraph):
        """Cone from do_kill should find direct and transitive callees."""
        cone = compute_call_cone(sample_graph, "do_kill", max_depth=5, max_size=200)
        assert set(cone["direct"]) == {"damage", "do_look"}
        assert set(cone["transitive"]) == {"send_to_char", "affect_to_char", "show_room_to_char"}
        assert cone["truncated"] is False

    def test_depth_limit(self, sample_graph: nx.MultiDiGraph):
        """Depth=1 should only yield direct callees."""
        cone = compute_call_cone(sample_graph, "do_kill", max_depth=1, max_size=200)
        assert set(cone["direct"]) == {"damage", "do_look"}
        assert cone["transitive"] == []

    def test_size_limit(self, sample_graph: nx.MultiDiGraph):
        """max_size=1 should truncate early."""
        cone = compute_call_cone(sample_graph, "do_kill", max_depth=5, max_size=1)
        total = len(cone["direct"]) + len(cone["transitive"])
        # Should be truncated since cone > 1
        assert cone["truncated"] is True

    def test_missing_seed(self, sample_graph: nx.MultiDiGraph):
        """Non-existent seed returns empty cone."""
        cone = compute_call_cone(sample_graph, "nonexistent")
        assert cone["direct"] == []
        assert cone["transitive"] == []
        assert cone["truncated"] is False

    def test_ignores_non_calls_edges(self, sample_graph: nx.MultiDiGraph):
        """Cone should NOT traverse USES or INHERITS edges."""
        cone = compute_call_cone(sample_graph, "damage", max_depth=5, max_size=200)
        assert "global_dam_stat" not in cone["direct"]
        assert "global_dam_stat" not in cone["transitive"]
        assert set(cone["direct"]) == {"send_to_char", "affect_to_char"}

    def test_leaf_node_cone(self, sample_graph: nx.MultiDiGraph):
        """Leaf node (no outgoing calls) should return empty cone."""
        cone = compute_call_cone(sample_graph, "send_to_char")
        assert cone["direct"] == []
        assert cone["transitive"] == []


class TestGetCallers:
    """Tests for get_callers."""

    def test_depth_1_callers(self, sample_graph: nx.MultiDiGraph):
        callers = get_callers(sample_graph, "damage", depth=1, limit=50)
        assert 1 in callers
        assert "do_kill" in callers[1]

    def test_depth_2_callers(self, sample_graph: nx.MultiDiGraph):
        callers = get_callers(sample_graph, "damage", depth=2, limit=50)
        assert 1 in callers
        assert "do_kill" in callers[1]
        assert 2 in callers
        assert "main" in callers[2]

    def test_missing_entity(self, sample_graph: nx.MultiDiGraph):
        callers = get_callers(sample_graph, "nonexistent")
        assert callers == {}

    def test_limit_truncates(self, sample_graph: nx.MultiDiGraph):
        callers = get_callers(sample_graph, "damage", depth=1, limit=1)
        assert len(callers.get(1, [])) <= 1


class TestGetCallees:
    """Tests for get_callees."""

    def test_depth_1_callees(self, sample_graph: nx.MultiDiGraph):
        callees = get_callees(sample_graph, "do_kill", depth=1, limit=50)
        assert 1 in callees
        assert set(callees[1]) == {"damage", "do_look"}

    def test_depth_2_callees(self, sample_graph: nx.MultiDiGraph):
        callees = get_callees(sample_graph, "do_kill", depth=2, limit=50)
        assert 1 in callees
        assert 2 in callees
        assert "send_to_char" in callees[2] or "affect_to_char" in callees[2]

    def test_missing_entity(self, sample_graph: nx.MultiDiGraph):
        callees = get_callees(sample_graph, "nonexistent")
        assert callees == {}


class TestGetClassHierarchy:
    """Tests for get_class_hierarchy."""

    def test_base_and_derived(self, sample_graph: nx.MultiDiGraph):
        hierarchy = get_class_hierarchy(sample_graph, "Character")
        assert hierarchy["base_classes"] == []  # Character has no bases
        assert set(hierarchy["derived_classes"]) == {"Player", "MobilePrototype"}

    def test_derived_class_bases(self, sample_graph: nx.MultiDiGraph):
        hierarchy = get_class_hierarchy(sample_graph, "Player")
        assert "Character" in hierarchy["base_classes"]
        assert hierarchy["derived_classes"] == []

    def test_missing_entity(self, sample_graph: nx.MultiDiGraph):
        hierarchy = get_class_hierarchy(sample_graph, "nonexistent")
        assert hierarchy["base_classes"] == []
        assert hierarchy["derived_classes"] == []
