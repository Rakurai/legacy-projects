#!/usr/bin/env python3
"""
Phase 3, Pass 1 — Capability-level chunk formation.

Reads the evidence graph (capability_graph.json) and taxonomy (capability_defs.json),
and proposes implementation chunks based on dependency structure and fan-in tiers.

The unit of chunk formation is the capability group — not entry points.
Entry points are annotated as consequences (what gets enabled), not inputs.

Outputs: candidate_chunks.json
"""

import json
import sys
from collections import defaultdict
from pathlib import Path

# ── paths ────────────────────────────────────────────────────────────────────

BASE = Path(__file__).parent
GRAPH_PATH = BASE / "capability_graph.json"
DEFS_PATH = BASE / "capability_defs.json"
OUT_PATH = BASE / "candidate_chunks.json"

# ── fan-in thresholds ────────────────────────────────────────────────────────

UNIVERSAL_THRESHOLD = 10   # DAG fan-in >= 10 → foundation tier
SHARED_THRESHOLD = 3       # DAG fan-in >= 3 → shared tier
# below shared → leaf tier


def load_data():
    with open(GRAPH_PATH) as f:
        graph = json.load(f)
    with open(DEFS_PATH) as f:
        defs = json.load(f)
    return graph, defs


def compute_dag_fan_in(deps):
    """Compute fan-in using only in_dag edges (utility edges excluded)."""
    fan_in = defaultdict(int)
    for src, targets in deps.items():
        for tgt, info in targets.items():
            if info["in_dag"]:
                fan_in[tgt] += 1
    return dict(fan_in)


def compute_all_fan_in(deps):
    """Compute fan-in using all edges (including utility)."""
    fan_in = defaultdict(int)
    for src, targets in deps.items():
        for tgt, info in targets.items():
            fan_in[tgt] += 1
    return dict(fan_in)


def assign_tier(cap_name, cap_type, dag_fi, all_fi):
    """
    Assign implementation tier based on capability type and fan-in.

    Tiers (implementation order):
      0 - utility_foundation: utility groups, always needed
      1 - foundation: universal-fan-in services (DAG fan-in >= 10)
      2 - shared: moderate fan-in (DAG fan-in >= 3)
      3 - domain: domain/policy/projection groups with low fan-in
      4 - leaf: zero DAG fan-in, can be scheduled freely
    """
    if cap_type == "utility":
        return 0, "utility_foundation"

    if dag_fi >= UNIVERSAL_THRESHOLD:
        return 1, "foundation"

    if dag_fi >= SHARED_THRESHOLD:
        return 2, "shared"

    if dag_fi == 0:
        return 4, "leaf"

    return 3, "domain"


def compute_chunk_deps(deps, cap_to_chunk, caps):
    """
    Derive chunk-to-chunk dependency edges from capability-level edges.
    Only considers in_dag edges.
    Returns dict: {(src_chunk, tgt_chunk): {"edge_types": set, "total_calls": int}}
    """
    chunk_edges = defaultdict(lambda: {"edge_types": set(), "total_calls": 0, "cap_edges": []})

    for src, targets in deps.items():
        src_chunk = cap_to_chunk.get(src)
        if not src_chunk:
            continue
        for tgt, info in targets.items():
            tgt_chunk = cap_to_chunk.get(tgt)
            if not tgt_chunk or src_chunk == tgt_chunk:
                continue  # skip self-deps and utility-only edges within same chunk
            if info["in_dag"]:
                key = (src_chunk, tgt_chunk)
                chunk_edges[key]["edge_types"].add(info["edge_type"])
                chunk_edges[key]["total_calls"] += info["call_count"]
                chunk_edges[key]["cap_edges"].append({
                    "from_cap": src, "to_cap": tgt,
                    "edge_type": info["edge_type"],
                    "call_count": info["call_count"],
                })

    # convert sets to lists for JSON
    result = {}
    for (src, tgt), data in chunk_edges.items():
        result[f"{src}->{tgt}"] = {
            "source": src,
            "target": tgt,
            "edge_types": sorted(data["edge_types"]),
            "total_calls": data["total_calls"],
            "capability_edges": data["cap_edges"],
        }
    return result


def topological_sort(chunk_ids, chunk_edges):
    """
    Kahn's algorithm. Returns list of tiers (each tier is a set of chunks
    that can be implemented in parallel once all prior tiers are done).
    """
    # Build adjacency for implementation order.
    # In chunk_edges, source depends on target (source calls target).
    # For implementation order, target must come BEFORE source.
    # So we reverse: target → source in the topo-sort graph.
    in_degree = {c: 0 for c in chunk_ids}
    successors = defaultdict(set)

    for edge_key, edge in chunk_edges.items():
        src, tgt = edge["source"], edge["target"]
        if src in in_degree and tgt in in_degree:
            in_degree[src] += 1       # src waits for tgt
            successors[tgt].add(src)   # after tgt, unlock src

    # Kahn's with wave tracking
    queue = [c for c in chunk_ids if in_degree[c] == 0]
    waves = []
    visited = set()

    while queue:
        waves.append(sorted(queue))
        next_queue = []
        for node in queue:
            visited.add(node)
            for succ in successors[node]:
                in_degree[succ] -= 1
                if in_degree[succ] == 0:
                    next_queue.append(succ)
        queue = next_queue

    # detect cycles
    unvisited = set(chunk_ids) - visited
    return waves, unvisited


def compute_entry_point_enablement(graph, cap_to_chunk, chunks):
    """
    For each entry point, determine which chunks it requires.
    Then for each chunk, list the entry points that become fully enabled
    when that chunk (and all its transitive deps) are complete.
    """
    # Build chunk dependency closure (transitive deps for each chunk)
    chunk_edges_fwd = defaultdict(set)
    deps = graph["dependencies"]
    for src, targets in deps.items():
        src_chunk = cap_to_chunk.get(src)
        for tgt, info in targets.items():
            tgt_chunk = cap_to_chunk.get(tgt)
            if src_chunk and tgt_chunk and src_chunk != tgt_chunk and info["in_dag"]:
                chunk_edges_fwd[src_chunk].add(tgt_chunk)

    # For each entry point, find which chunks it needs
    # An entry point needs all chunks that contain any of its capabilities
    ep_chunks = {}
    for ep_name, ep in graph["entry_points"].items():
        needed = set()
        for cap in ep["capabilities"]:
            chunk = cap_to_chunk.get(cap)
            if chunk:
                needed.add(chunk)
        ep_chunks[ep_name] = needed

    # For each chunk, find entry points that need ONLY that chunk + its deps
    # First, compute transitive closure of chunk deps
    def transitive_deps(chunk_id):
        visited = set()
        stack = [chunk_id]
        while stack:
            c = stack.pop()
            if c in visited:
                continue
            visited.add(c)
            for dep in chunk_edges_fwd.get(c, []):
                stack.append(dep)
        return visited

    chunk_closures = {cid: transitive_deps(cid) for cid in chunks}

    # An entry point is "enabled by chunk X" if ep_chunks[ep] ⊆ closure(X)
    # Find the LATEST chunk that enables each entry point
    # (the chunk whose closure first covers all the EP's requirements)
    ep_enabling_chunk = {}
    for ep_name, needed in ep_chunks.items():
        if not needed:
            continue
        # The enabling chunk is the last one the EP needs — the one with highest impl_wave.
        best = None
        best_wave = -1
        for c in needed:
            w = chunks[c].get("impl_wave", 999)
            if w > best_wave:
                best_wave = w
                best = c
        ep_enabling_chunk[ep_name] = best

    # Collect per chunk
    chunk_enables = defaultdict(list)
    for ep_name, chunk_id in ep_enabling_chunk.items():
        ep = graph["entry_points"][ep_name]
        chunk_enables[chunk_id].append({
            "name": ep_name,
            "type": ep["type"],
            "earliest_wave": ep["earliest_wave"],
        })

    # Sort each chunk's enabled EPs by name
    for cid in chunk_enables:
        chunk_enables[cid].sort(key=lambda x: x["name"])

    return dict(chunk_enables)


def detect_bundling_opportunities(deps, caps):
    """
    Find policy/projection groups that serve only 1-2 domain groups.
    These are candidates for bundling into the domain chunk.
    """
    suggestions = []
    for tgt_name, tgt_cap in caps.items():
        if tgt_cap["type"] not in ("policy", "projection"):
            continue
        domain_consumers = []
        for src, targets in deps.items():
            if tgt_name in targets and targets[tgt_name]["in_dag"]:
                if caps[src]["type"] == "domain":
                    domain_consumers.append(src)
        if 1 <= len(domain_consumers) <= 2:
            suggestions.append({
                "support_group": tgt_name,
                "support_type": tgt_cap["type"],
                "domain_consumers": domain_consumers,
                "suggestion": f"Consider bundling {tgt_name} into {' or '.join(domain_consumers)}",
            })
    return suggestions


def generate_warnings(chunks, chunk_edges, cycles):
    """Generate warnings for problematic chunks."""
    warnings = []

    # Cycles
    if cycles:
        warnings.append({
            "type": "cycle",
            "message": f"Dependency cycle detected involving: {sorted(cycles)}",
            "chunks": sorted(cycles),
        })

    # Over-large chunks (member count)
    for cid, chunk in chunks.items():
        if chunk["member_count"] > 60:
            warnings.append({
                "type": "large_chunk",
                "message": f"{cid} has {chunk['member_count']} members — may need splitting",
                "chunks": [cid],
            })

    # Orphan capabilities (no deps in or out in DAG)
    for cid, chunk in chunks.items():
        has_in = any(e["target"] == cid for e in chunk_edges.values())
        has_out = any(e["source"] == cid for e in chunk_edges.values())
        if not has_in and not has_out and chunk["tier_name"] != "utility_foundation":
            warnings.append({
                "type": "orphan",
                "message": f"{cid} has no DAG dependencies in or out — verify it belongs in the plan",
                "chunks": [cid],
            })

    return warnings


def main():
    print("Loading data...")
    graph, defs = load_data()

    caps = graph["capabilities"]
    deps = graph["dependencies"]
    entry_points = graph["entry_points"]

    # ── Step 1: Fan-in computation ───────────────────────────────────────────
    print("Computing fan-in...")
    dag_fi = compute_dag_fan_in(deps)
    all_fi = compute_all_fan_in(deps)

    # ── Step 2: Assign tiers & build default chunks ──────────────────────────
    print("Assigning tiers...")
    chunks = {}
    cap_to_chunk = {}  # capability -> chunk_id

    for cap_name, cap in sorted(caps.items()):
        cap_type = cap["type"]
        fi_dag = dag_fi.get(cap_name, 0)
        fi_all = all_fi.get(cap_name, 0)
        tier_num, tier_name = assign_tier(cap_name, cap_type, fi_dag, fi_all)

        chunk_id = cap_name  # default: one chunk per capability
        cap_to_chunk[cap_name] = chunk_id

        # Fan-out: how many capabilities does this one depend on?
        fo_dag = 0
        fo_all = 0
        if cap_name in deps:
            for tgt, info in deps[cap_name].items():
                fo_all += 1
                if info["in_dag"]:
                    fo_dag += 1

        chunks[chunk_id] = {
            "chunk_id": chunk_id,
            "capabilities": [cap_name],
            "capability_type": cap_type,
            "tier_num": tier_num,
            "tier_name": tier_name,
            "wave": cap["wave"],
            "member_count": len(cap["members"]),
            "fan_in_dag": fi_dag,
            "fan_in_all": fi_all,
            "fan_out_dag": fo_dag,
            "fan_out_all": fo_all,
            "description": defs[cap_name]["desc"] if cap_name in defs else "",
            "migration_role": defs[cap_name].get("migration_role", "") if cap_name in defs else "",
            "target_surfaces": defs[cap_name].get("target_surfaces", []) if cap_name in defs else [],
        }

    # ── Step 3: Chunk-to-chunk dependency edges ──────────────────────────────
    print("Computing chunk dependencies...")
    chunk_edges = compute_chunk_deps(deps, cap_to_chunk, caps)

    # ── Step 4: Topological ordering ─────────────────────────────────────────
    print("Computing implementation order...")
    impl_waves, cycles = topological_sort(list(chunks.keys()), chunk_edges)

    # Assign implementation wave to each chunk
    for wave_idx, wave_chunks in enumerate(impl_waves):
        for cid in wave_chunks:
            chunks[cid]["impl_wave"] = wave_idx

    for cid in cycles:
        chunks[cid]["impl_wave"] = -1  # mark cycle members

    # ── Step 5: Entry-point enablement ───────────────────────────────────────
    print("Computing entry-point enablement...")
    chunk_enables = compute_entry_point_enablement(graph, cap_to_chunk, chunks)

    for cid, chunk in chunks.items():
        eps = chunk_enables.get(cid, [])
        chunk["enables_entry_points"] = len(eps)
        chunk["enabled_commands"] = [e["name"] for e in eps if e["type"] == "command"]
        chunk["enabled_spells"] = [e["name"] for e in eps if e["type"] == "spell"]
        chunk["enabled_specials"] = [e["name"] for e in eps if e["type"] == "special"]

    # ── Step 6: Bundling suggestions ─────────────────────────────────────────
    print("Detecting bundling opportunities...")
    bundle_suggestions = detect_bundling_opportunities(deps, caps)

    # ── Step 7: Warnings ─────────────────────────────────────────────────────
    print("Generating warnings...")
    warnings = generate_warnings(chunks, chunk_edges, cycles)

    # ── Assemble output ──────────────────────────────────────────────────────
    output = {
        "metadata": {
            "description": "Phase 3 Pass 1 — candidate implementation chunks",
            "source": "capability_graph.json",
            "total_chunks": len(chunks),
            "total_chunk_edges": len(chunk_edges),
            "implementation_waves": len(impl_waves),
            "cycles": sorted(cycles),
            "fan_in_thresholds": {
                "universal": UNIVERSAL_THRESHOLD,
                "shared": SHARED_THRESHOLD,
            },
        },
        "chunks": chunks,
        "chunk_dependencies": chunk_edges,
        "implementation_order": [
            {"wave": i, "chunks": wave}
            for i, wave in enumerate(impl_waves)
        ],
        "bundle_suggestions": bundle_suggestions,
        "warnings": warnings,
    }

    with open(OUT_PATH, "w") as f:
        json.dump(output, f, indent=2)

    # ── Summary ──────────────────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print(f"Output: {OUT_PATH}")
    print(f"Chunks: {len(chunks)}")
    print(f"Chunk dependency edges: {len(chunk_edges)}")
    print(f"Implementation waves: {len(impl_waves)}")
    if cycles:
        print(f"⚠ CYCLES: {sorted(cycles)}")

    print(f"\n--- Tier summary ---")
    tier_counts = defaultdict(list)
    for cid, c in sorted(chunks.items(), key=lambda x: (x[1]["tier_num"], x[1]["wave"])):
        tier_counts[c["tier_name"]].append(cid)
    for tier_name, members in sorted(tier_counts.items(), key=lambda x: chunks[x[1][0]]["tier_num"]):
        tier_num = chunks[members[0]]["tier_num"]
        print(f"  T{tier_num} {tier_name}: {members}")

    print(f"\n--- Implementation order ---")
    for i, wave in enumerate(impl_waves):
        descs = []
        for cid in wave:
            c = chunks[cid]
            descs.append(f"{cid}(T{c['tier_num']},w{c['wave']},{c['member_count']}m,fi={c['fan_in_dag']})")
        print(f"  Wave {i}: {', '.join(descs)}")

    print(f"\n--- Entry-point enablement ---")
    for cid, c in sorted(chunks.items(), key=lambda x: -x[1]["enables_entry_points"]):
        if c["enables_entry_points"] > 0:
            cmds = len(c["enabled_commands"])
            spells = len(c["enabled_spells"])
            specs = len(c["enabled_specials"])
            print(f"  {cid}: {c['enables_entry_points']} EPs ({cmds} cmd, {spells} spell, {specs} spec)")

    if bundle_suggestions:
        print(f"\n--- Bundle suggestions ---")
        for s in bundle_suggestions:
            print(f"  {s['suggestion']}")

    if warnings:
        print(f"\n--- Warnings ---")
        for w in warnings:
            print(f"  [{w['type']}] {w['message']}")


if __name__ == "__main__":
    main()
