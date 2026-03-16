"""
NetworkX Graph - In-memory dependency graph for BFS/traversal.

Graph is loaded from the edges table at server startup and kept in memory (read-only).
All graph algorithms (call cone, callers/callees, class hierarchy) operate on this graph.
"""

import networkx as nx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from server.db_models import Edge
from server.logging_config import log

# -- Edge type constants (canonical lowercase, matching build_mcp_db normalization) --
CALLS = "calls"
USES = "uses"
INHERITS = "inherits"
INCLUDES = "includes"
CONTAINED_BY = "contained_by"


async def load_graph(session: AsyncSession) -> nx.MultiDiGraph:
    """
    Load dependency graph from edges table into NetworkX MultiDiGraph.

    Graph is read-only after load; supports concurrent reads (GIL-safe).
    Node IDs are entity_id (string). Edges have 'type' attribute (relationship).

    Also computes and stores edge_type_counts on the graph object for O(1) stats access.
    """
    log.info("Loading dependency graph from edges table")

    g = nx.MultiDiGraph()

    result = await session.execute(select(Edge))
    edges = result.scalars().all()

    edge_type_counts: dict[str, int] = {}
    for edge in edges:
        g.add_edge(
            edge.source_id,
            edge.target_id,
            key=edge.relationship,
            type=edge.relationship,
        )
        edge_type_counts[edge.relationship] = edge_type_counts.get(edge.relationship, 0) + 1

    # Store pre-computed edge counts on the graph for O(1) stats access (m-11)
    g.graph["edge_type_counts"] = edge_type_counts

    log.info(
        "Dependency graph loaded",
        nodes=g.number_of_nodes(),
        edges=g.number_of_edges(),
    )

    return g


def compute_call_cone(
    graph: nx.MultiDiGraph,
    seed_id: str,
    max_depth: int = 5,
    max_size: int = 200
) -> dict[str, list[str] | bool]:
    """
    Compute transitive call cone via BFS from seed function.

    Traverses CALLS edges (ignores USES, INHERITS, etc.) up to max_depth.
    Stops early if cone exceeds max_size to prevent performance degradation.

    Args:
        graph: Dependency graph
        seed_id: Starting entity ID
        max_depth: Maximum traversal depth (default 5)
        max_size: Maximum cone size (default 200)

    Returns:
        dict with keys:
            - direct: list[entity_id] (direct callees, depth=1)
            - transitive: list[entity_id] (transitive callees, depth>1)
            - truncated: bool (whether cone was truncated)
            - max_depth_reached: int (actual max depth reached)
    """
    if seed_id not in graph:
        log.warning("Seed entity not in graph", seed_id=seed_id)
        return {
            "direct": [],
            "transitive": [],
            "truncated": False,
            "max_depth_reached": 0
        }

    direct_callees: list[str] = []
    transitive_cone: list[str] = []
    visited: set[str] = {seed_id}
    queue: list[tuple[str, int]] = [(seed_id, 0)]
    max_depth_reached = 0

    while queue and len(transitive_cone) < max_size:
        node_id, depth = queue.pop(0)

        max_depth_reached = max(max_depth_reached, depth)

        if depth >= max_depth:
            continue

        for _, target, data in graph.out_edges(node_id, data=True):
            if data.get("type") != CALLS:
                continue

            if target in visited:
                continue

            visited.add(target)

            if depth == 0:
                direct_callees.append(target)
            else:
                transitive_cone.append(target)

            queue.append((target, depth + 1))

    truncated = len(transitive_cone) >= max_size or len(queue) > 0

    return {
        "direct": direct_callees,
        "transitive": transitive_cone,
        "truncated": truncated,
        "max_depth_reached": max_depth_reached
    }


def get_callers(
    graph: nx.MultiDiGraph,
    entity_id: str,
    depth: int = 1,
    limit: int = 50
) -> dict[int, list[str]]:
    """
    Get callers (entities with CALLS edges to this entity) up to depth levels.

    Args:
        graph: Dependency graph
        entity_id: Target entity ID
        depth: Maximum depth (1-3)
        limit: Maximum results per depth level

    Returns:
        dict mapping depth → list of entity IDs
        Example: {1: [caller1, caller2], 2: [indirect1, indirect2]}
    """
    if entity_id not in graph:
        return {}

    callers_by_depth: dict[int, list[str]] = {}
    visited: set[str] = {entity_id}
    current_level: set[str] = {entity_id}

    for d in range(1, depth + 1):
        next_level: set[str] = set()

        for node in current_level:
            for source, _, data in graph.in_edges(node, data=True):
                if data.get("type") != CALLS:
                    continue

                if source not in visited:
                    visited.add(source)
                    next_level.add(source)

        if not next_level:
            break

        callers_by_depth[d] = list(next_level)[:limit]
        current_level = next_level

    return callers_by_depth


def get_callees(
    graph: nx.MultiDiGraph,
    entity_id: str,
    depth: int = 1,
    limit: int = 50
) -> dict[int, list[str]]:
    """
    Get callees (entities this entity calls) up to depth levels.

    Args:
        graph: Dependency graph
        entity_id: Source entity ID
        depth: Maximum depth (1-3)
        limit: Maximum results per depth level

    Returns:
        dict mapping depth → list of entity IDs
    """
    if entity_id not in graph:
        return {}

    callees_by_depth: dict[int, list[str]] = {}
    visited: set[str] = {entity_id}
    current_level: set[str] = {entity_id}

    for d in range(1, depth + 1):
        next_level: set[str] = set()

        for node in current_level:
            for _, target, data in graph.out_edges(node, data=True):
                if data.get("type") != CALLS:
                    continue

                if target not in visited:
                    visited.add(target)
                    next_level.add(target)

        if not next_level:
            break

        callees_by_depth[d] = list(next_level)[:limit]
        current_level = next_level

    return callees_by_depth


def get_class_hierarchy(
    graph: nx.MultiDiGraph,
    entity_id: str
) -> dict[str, list[str]]:
    """
    Get class hierarchy (base classes and derived classes) via INHERITS edges.

    Args:
        graph: Dependency graph
        entity_id: Class entity ID

    Returns:
        dict with keys:
            - base_classes: list[entity_id] (ancestors)
            - derived_classes: list[entity_id] (descendants)
    """
    if entity_id not in graph:
        return {"base_classes": [], "derived_classes": []}

    base_classes: list[str] = []
    derived_classes: list[str] = []

    # Base classes (outgoing INHERITS edges)
    for _, target, data in graph.out_edges(entity_id, data=True):
        if data.get("type") == INHERITS:
            base_classes.append(target)

    # Derived classes (incoming INHERITS edges)
    for source, _, data in graph.in_edges(entity_id, data=True):
        if data.get("type") == INHERITS:
            derived_classes.append(source)

    return {
        "base_classes": base_classes,
        "derived_classes": derived_classes
    }
