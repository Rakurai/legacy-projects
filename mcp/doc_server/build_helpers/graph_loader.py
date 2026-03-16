"""
Graph Loader - Parse code_graph.gml and compute graph-derived metrics.

Loads dependency graph from GML file and:
- Extracts edges for database population
- Computes fan_in/fan_out metrics
- Identifies bridge functions (cross-capability edges)
- Categorizes side-effect markers

Uses existing doxygen_graph.py parser to load GML.
"""

from collections import defaultdict
from pathlib import Path

from build_helpers.artifact_models import load_gml_graph
from build_helpers.entity_processor import SIDE_EFFECT_FUNCTIONS, MergedEntity
from server.logging_config import log

# Maximum BFS depth when scanning for transitive side-effect calls
_SIDE_EFFECT_BFS_DEPTH = 2


def load_graph_edges(
    artifacts_dir: Path,
    merged_entities: list[MergedEntity]
) -> list[tuple[str, str, str]]:
    """
    Load edges from code_graph.gml and convert node IDs to entity IDs.

    Graph stores node IDs as either bare member hash or compound ID.
    We need to convert these to full entity_id format (compound_member).

    Args:
        artifacts_dir: Path to artifacts directory
        merged_entities: List of merged entities for ID mapping

    Returns:
        List of (source_entity_id, target_entity_id, relationship) tuples
    """
    gml_path = artifacts_dir / "code_graph.gml"
    log.info("Loading dependency graph from GML", path=str(gml_path))

    g = load_gml_graph(gml_path)

    # Build mapping from graph node ID to entity ID
    # Graph uses: member hash for members, compound ID for compounds
    # Entity uses: "compound_member" for members, "compound" for compounds
    node_to_entity: dict[str, str] = {}
    for entity in merged_entities:
        # For members: map member hash -> full entity_id
        if entity.member_id:
            node_to_entity[entity.member_id] = entity.entity_id
        # For compounds: map compound -> entity_id (same)
        node_to_entity[entity.compound_id] = entity.entity_id

    edges_set: set[tuple[str, str, str]] = set()
    skipped = 0

    for source, target, data in g.edges(data=True):
        # Filter to entity-to-entity edges (exclude location nodes)
        source_type = g.nodes[source].get("type", "")
        target_type = g.nodes[target].get("type", "")

        if source_type in ("compound", "member") and target_type in ("compound", "member"):
            # Convert graph node IDs to entity IDs
            source_entity = node_to_entity.get(source)
            target_entity = node_to_entity.get(target)

            if source_entity and target_entity:
                edge_type = data.get("type", "unknown")
                edges_set.add((source_entity, target_entity, edge_type))
            else:
                skipped += 1

    edges = list(edges_set)
    log.info("Dependency graph edges loaded", edge_count=len(edges), skipped=skipped)
    return edges


def compute_fan_metrics(
    merged_entities: list[MergedEntity],
    edges: list[tuple[str, str, str]]
) -> None:
    """
    Compute fan_in and fan_out metrics from CALLS edges.

    - fan_in: Number of CALLS edges targeting this entity
    - fan_out: Number of CALLS edges from this entity

    Updates merged_entity.fan_in and merged_entity.fan_out in place.

    Args:
        merged_entities: List of merged entity records
        edges: List of (source_id, target_id, relationship) tuples
    """
    log.info("Computing fan_in and fan_out metrics")

    # Build maps for efficient lookup
    fan_in_map: dict[str, int] = defaultdict(int)
    fan_out_map: dict[str, int] = defaultdict(int)

    for source, target, relationship in edges:
        if relationship.lower() == "calls":
            fan_out_map[source] += 1
            fan_in_map[target] += 1

    # Update entities
    for merged in merged_entities:
        entity_id = merged.entity_id
        merged.fan_in = fan_in_map.get(entity_id, 0)
        merged.fan_out = fan_out_map.get(entity_id, 0)

    log.info("Fan metrics computed")


def compute_bridge_flags(
    merged_entities: list[MergedEntity],
    edges: list[tuple[str, str, str]]
) -> None:
    """
    Compute is_bridge flag for functions with cross-capability CALLS.

    A function is a bridge if its callers and callees span different capabilities.

    Updates merged_entity.is_bridge in place.

    Args:
        merged_entities: List of merged entity records
        edges: List of (source_id, target_id, relationship) tuples
    """
    log.info("Computing bridge flags")

    # Build entity_id → capability map
    capability_map: dict[str, str | None] = {
        merged.entity_id: merged.capability for merged in merged_entities
    }

    # Build adjacency lists for CALLS edges
    callers: dict[str, list[str]] = defaultdict(list)
    callees: dict[str, list[str]] = defaultdict(list)

    for source, target, relationship in edges:
        if relationship.lower() == "calls":
            callers[target].append(source)
            callees[source].append(target)

    bridge_count = 0

    for merged in merged_entities:
        entity_id = merged.entity_id
        entity_cap = merged.capability

        if not entity_cap:
            continue

        # Check if callers span different capabilities
        caller_caps = {capability_map.get(c) for c in callers[entity_id] if capability_map.get(c)}
        callee_caps = {capability_map.get(c) for c in callees[entity_id] if capability_map.get(c)}

        # Remove None and entity's own capability
        caller_caps.discard(None)
        caller_caps.discard(entity_cap)
        callee_caps.discard(None)
        callee_caps.discard(entity_cap)

        # Bridge if callers AND callees span different capabilities than this entity
        if caller_caps and callee_caps:
            merged.is_bridge = True
            bridge_count += 1

    log.info("Bridge flags computed", bridge_count=bridge_count)


def compute_side_effect_markers(
    merged_entities: list[MergedEntity],
    edges: list[tuple[str, str, str]]
) -> None:
    """
    Compute side_effect_markers by categorizing called functions.

    For each entity, traverse CALLS edges and check if callees are in the
    curated side-effect function list. Categorize by type (messaging, persistence,
    state_mutation, scheduling).

    Tracks direct vs. transitive markers (depth 1 vs. depth >1).

    Updates merged_entity.side_effect_markers in place.

    Args:
        merged_entities: List of merged entity records
        edges: List of (source_id, target_id, relationship) tuples
    """
    log.info("Computing side-effect markers")

    # Build entity_id → name map
    name_map: dict[str, str] = {
        merged.entity_id: merged.entity.name for merged in merged_entities
    }

    # Build adjacency list for CALLS edges
    callees_map: dict[str, list[str]] = defaultdict(list)
    for source, target, relationship in edges:
        if relationship.lower() == "calls":
            callees_map[source].append(target)

    # Build reverse lookup: function name → side-effect category
    effect_category: dict[str, str] = {}
    for category, funcs in SIDE_EFFECT_FUNCTIONS.items():
        for func in funcs:
            effect_category[func] = category

    # Compute side effects for each entity
    for merged in merged_entities:
        entity_id = merged.entity_id
        markers: dict[str, list[str]] = {
            "messaging": [],
            "persistence": [],
            "state_mutation": [],
            "scheduling": []
        }

        # BFS to depth _SIDE_EFFECT_BFS_DEPTH (direct + one level transitive)
        visited: set[str] = {entity_id}
        queue: list[tuple[str, int]] = [(entity_id, 0)]

        while queue:
            current, depth = queue.pop(0)

            if depth >= _SIDE_EFFECT_BFS_DEPTH:
                continue

            for callee in callees_map[current]:
                if callee in visited:
                    continue

                visited.add(callee)
                callee_name = name_map.get(callee, "")

                # Check if callee is a side-effect function
                if callee_name in effect_category:
                    category = effect_category[callee_name]
                    markers[category].append(callee_name)

                queue.append((callee, depth + 1))

        # Only store non-empty markers
        merged.side_effect_markers = {k: v for k, v in markers.items() if v}

    log.info("Side-effect markers computed")
