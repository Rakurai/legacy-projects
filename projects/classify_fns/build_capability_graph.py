"""
Capability Dependency Graph Builder (v2)

Analyzes the Legacy C++ code graph to produce a typed capability dependency
graph suitable for implementation chunk planning.

Pipeline stages:
  1. Load artifacts (graph, entity DB, doc DB, capability defs, embeddings)
  2. Extract entry points (do_*, spell_*, spec_*)
  3. Map each entry point to transitive callees via BFS
  4. Classify callees: locked-list exact match, then embedding similarity fallback
  5. Build entry_point → capability bipartite map
  6. Derive capability → capability dependencies from callee→callee call edges
  7. Type the dependency edges based on group types
  8. Build DAG, break cycles, compute implementation waves
  9. Compute entry-point enablement per wave
 10. Export capability_graph.json

Inputs:
  - clustering/code_graph.gml      (networkx MultiDiGraph)
  - clustering/code_graph.json     (entity database)
  - clustering/doc_db.json         (LLM-generated function docs)
  - clustering/embeddings_cache.pkl (function embeddings)
  - capability_defs.json           (capability group definitions with locked lists)

Output:
  - capability_graph.json
"""

import json
import pickle
import time
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import networkx as nx
from sklearn.metrics.pairwise import cosine_similarity

# ── Module setup ─────────────────────────────────────────────────────

import legacy_common.doc_db as ddb
import legacy_common.doxygen_graph as dg
import legacy_common.doxygen_parse as dp
import legacy_common.openai_embeddings as oai_emb
from legacy_common import ARTIFACTS_DIR

# ── Paths ────────────────────────────────────────────────────────────

HERE = Path(__file__).resolve().parent
CAPABILITY_DEFS_PATH = HERE / "capability_defs.json"
EMBEDDING_CACHE_PATH = ARTIFACTS_DIR / "embeddings_cache.pkl"
OUTPUT_PATH = HERE / "capability_graph.json"

EDGE_THRESHOLD = 3          # min cross-capability call pairs for a dependency edge
EMBED_SIM_THRESHOLD = 0.40  # min cosine similarity for embedding-based classification
ENTRY_PREFIXES = ("do_", "spell_", "spec_")

# ── Type system for dependency edges ─────────────────────────────────
# Maps (src_type, tgt_type) → edge_kind.  Missing pairs default to "requires".
EDGE_TYPE_MAP = {
    # domain → X
    ("domain", "domain"):         "requires_core",
    ("domain", "policy"):         "requires_policy",
    ("domain", "projection"):     "requires_projection",
    ("domain", "infrastructure"): "requires_infrastructure",
    ("domain", "utility"):        "uses_utility",
    # policy → X
    ("policy", "domain"):         "requires_core",
    ("policy", "policy"):         "requires_policy",
    ("policy", "projection"):     "requires_projection",
    ("policy", "infrastructure"): "requires_infrastructure",
    ("policy", "utility"):        "uses_utility",
    # projection → X
    ("projection", "domain"):         "requires_core",
    ("projection", "policy"):         "requires_policy",
    ("projection", "projection"):     "requires_projection",
    ("projection", "infrastructure"): "requires_infrastructure",
    ("projection", "utility"):        "uses_utility",
    # infrastructure → X
    ("infrastructure", "domain"):         "requires_core",
    ("infrastructure", "policy"):         "requires_policy",
    ("infrastructure", "projection"):     "requires_projection",
    ("infrastructure", "infrastructure"): "requires_infrastructure",
    ("infrastructure", "utility"):        "uses_utility",
    # utility → X
    ("utility", "domain"):         "requires_core",
    ("utility", "policy"):         "requires_policy",
    ("utility", "projection"):     "requires_projection",
    ("utility", "infrastructure"): "requires_infrastructure",
    ("utility", "utility"):        "uses_utility",
}


# ── Helpers ──────────────────────────────────────────────────────────

def entry_point_name(sig: str) -> str:
    """Extract short name (do_kill, spell_fireball, spec_guard) from a signature."""
    for prefix in ENTRY_PREFIXES:
        idx = sig.find(prefix)
        if idx >= 0:
            end = sig.find("(", idx)
            return sig[idx:end] if end >= 0 else sig[idx:]
    return sig


def bare_name(sig: str) -> str:
    """Extract bare function name from a full C++ signature."""
    paren = sig.find("(")
    if paren > 0:
        sig = sig[:paren]
    space = sig.rfind(" ")
    if space > 0:
        sig = sig[space + 1:]
    return sig


def is_entry_point(name: str) -> bool:
    return any(f" {p}" in name or name.startswith(p) for p in ENTRY_PREFIXES)


def get_calls(g: nx.MultiDiGraph, node_id: str) -> set[str]:
    """Return nodes reachable via a single 'calls' edge."""
    return {v for _, v, ed in g.edges(node_id, data=True) if ed.get("type") == "calls"}


def resolve_doc(
    db: ddb.DocumentDB,
    entity_db: dp.EntityDatabase,
    node_id: str,
) -> tuple:
    """Look up the doc for a graph node.  Returns (doc, doc_text)."""
    try:
        eid = dg.get_body_eid(entity_db, node_id)
    except Exception:
        return None, None

    entity = entity_db.get(eid)
    if entity is None:
        return None, None

    cid = eid.compound
    sig = entity.signature
    doc = db.get_doc(cid, sig)
    if doc is None and cid in db:
        for _sig, d in db[cid].items():
            if d.name == entity.name and d.brief:
                doc = d
                break

    doc_text = doc.to_doxygen() if doc else None
    return doc, doc_text


def classify_edge(src_type: str, tgt_type: str) -> str:
    """Determine dependency edge kind from source/target group types."""
    return EDGE_TYPE_MAP.get((src_type, tgt_type), "requires")


# ── Stage 1: Load artifacts ─────────────────────────────────────────

def load_artifacts():
    """Load graph, entity DB, doc DB, embeddings, and capability definitions."""
    print("Stage 1: Loading artifacts...")

    graph = dg.load_graph(CLUSTERING_DIR / "code_graph.gml")
    entity_db = dp.load_db(CLUSTERING_DIR / "code_graph.json")
    doc_db = ddb.DocumentDB()
    doc_db.load(ddb.DOC_DB_PATH)

    with open(EMBEDDING_CACHE_PATH, "rb") as f:
        emb_cache: dict[str, np.ndarray] = pickle.load(f)

    with open(CAPABILITY_DEFS_PATH) as f:
        cap_defs: dict[str, dict] = json.load(f)

    print(f"  Graph: {graph.number_of_nodes()} nodes, {graph.number_of_edges()} edges")
    print(f"  Entity DB: {len(entity_db.entities)} entities")
    print(f"  Doc DB: {doc_db.count()} documents")
    print(f"  Embeddings cache: {len(emb_cache)} entries")
    print(f"  Capability groups: {len(cap_defs)}")
    print()

    return graph, entity_db, doc_db, emb_cache, cap_defs


# ── Stage 2: Extract entry points ───────────────────────────────────

def find_entry_points(graph: nx.MultiDiGraph) -> tuple[list[tuple[str, dict]], set[str]]:
    """Find all do_*, spell_*, spec_* entry points."""
    entries = [
        (n, d)
        for n, d in graph.nodes(data=True)
        if d.get("kind") == "function" and is_entry_point(d.get("name", ""))
    ]
    entries.sort(key=lambda x: entry_point_name(x[1].get("name", "")))
    entry_nodes = {n for n, _ in entries}

    do_count = sum(1 for _, d in entries if " do_" in d.get("name", ""))
    spell_count = sum(1 for _, d in entries if " spell_" in d.get("name", ""))
    spec_count = sum(1 for _, d in entries if " spec_" in d.get("name", ""))

    print(f"Stage 2: Entry points: {len(entries)} total")
    print(f"  do_*:    {do_count} command handlers")
    print(f"  spell_*: {spell_count} spell effects")
    print(f"  spec_*:  {spec_count} NPC special functions")
    print()

    return entries, entry_nodes


# ── Stage 3: Map entry points → transitive callees via BFS ──────────

def map_callees(
    graph: nx.MultiDiGraph,
    entity_db: dp.EntityDatabase,
    doc_db: ddb.DocumentDB,
    emb_cache: dict[str, np.ndarray],
    entries: list[tuple[str, dict]],
    entry_nodes: set[str],
) -> tuple[dict[str, dict[str, int]], dict[str, dict], set[str]]:
    """BFS from each entry point along 'calls' edges.

    Returns:
        cmd_callees: entry_name → {node_id: min_depth}
        callee_info: node_id → {name, sig, brief, doc_text, embedding, min_depth}
        all_callee_nodes: set of all callee node IDs
    """
    cmd_callees: dict[str, dict[str, int]] = {}
    callee_min_depth: dict[str, int] = {}
    all_callee_nodes: set[str] = set()

    for node_id, node_data in entries:
        name = entry_point_name(node_data.get("name", "?"))

        # BFS
        visited: dict[str, int] = {}
        queue: list[tuple[str, int]] = []
        for callee in get_calls(graph, node_id):
            if callee not in entry_nodes and callee != node_id:
                visited[callee] = 1
                queue.append((callee, 1))

        while queue:
            node, depth = queue.pop(0)
            for callee in get_calls(graph, node):
                if callee not in visited and callee not in entry_nodes:
                    visited[callee] = depth + 1
                    queue.append((callee, depth + 1))

        cmd_callees[name] = visited
        all_callee_nodes |= set(visited.keys())
        for nid, depth in visited.items():
            callee_min_depth[nid] = min(callee_min_depth.get(nid, 999), depth)

    # Build callee_info
    callee_info: dict[str, dict] = {}
    for node_id in sorted(all_callee_nodes):
        vd = graph.nodes[node_id]
        full_sig = vd.get("name", node_id)
        name = bare_name(full_sig)

        doc, doc_text = resolve_doc(doc_db, entity_db, node_id)

        # Resolve embedding from cache
        emb = None
        if doc and doc.mid and doc.mid in emb_cache:
            emb = emb_cache[doc.mid]

        callee_info[node_id] = {
            "name": name,
            "sig": full_sig,
            "brief": doc.brief if doc else None,
            "doc_text": doc_text,
            "embedding": emb,
            "min_depth": callee_min_depth.get(node_id, 999),
        }

    documented = sum(1 for v in callee_info.values() if v["brief"])
    with_emb = sum(1 for v in callee_info.values() if v["embedding"] is not None)
    depth1 = sum(1 for v in callee_info.values() if v["min_depth"] == 1)

    print(f"Stage 3: Transitive callees: {len(all_callee_nodes)}")
    print(f"  Direct (depth 1): {depth1}")
    print(f"  Deeper (depth >= 2): {len(all_callee_nodes) - depth1}")
    print(f"  With doc brief: {documented}")
    print(f"  With embedding: {with_emb}")
    print()

    return cmd_callees, callee_info, all_callee_nodes


# ── Stage 4: Classify callees into capability groups ─────────────────

def classify_callees(
    all_callee_nodes: set[str],
    callee_info: dict[str, dict],
    cap_defs: dict[str, dict],
) -> tuple[dict[str, str], dict[str, set[str]], list[str]]:
    """Classify each callee: locked-list match first, then embedding
    similarity fallback.

    Returns:
        callee_group: node_id → group_name (or "uncategorized")
        group_members: group_name → set of node IDs
        uncategorized: list of uncategorized node IDs
    """
    # Build locked-name → group lookup
    locked_name_to_group: dict[str, str] = {}
    for gname, gdef in cap_defs.items():
        for fn in gdef.get("locked", []):
            locked_name_to_group[fn] = gname

    # Build group description embeddings for fallback
    group_names = sorted(cap_defs.keys())
    group_descs = [cap_defs[g]["desc"] for g in group_names]
    print("  Embedding group descriptions for fallback classification...")
    group_desc_embeddings = oai_emb.embed_texts(group_descs, show_progress=True)

    callee_group: dict[str, str] = {}
    group_members: defaultdict[str, set[str]] = defaultdict(set)
    uncategorized: list[str] = []

    locked_matches = 0
    embedding_matches = 0

    for node_id in all_callee_nodes:
        info = callee_info.get(node_id, {})
        name = info.get("name", "")

        # 1. Locked-list exact match
        if name in locked_name_to_group:
            group = locked_name_to_group[name]
            callee_group[node_id] = group
            group_members[group].add(node_id)
            locked_matches += 1
            continue

        # 2. Embedding similarity fallback
        emb = info.get("embedding")
        if emb is not None:
            sims = cosine_similarity(emb.reshape(1, -1), group_desc_embeddings)[0]
            best_idx = int(np.argmax(sims))
            best_sim = float(sims[best_idx])

            if best_sim >= EMBED_SIM_THRESHOLD:
                group = group_names[best_idx]
                callee_group[node_id] = group
                group_members[group].add(node_id)
                embedding_matches += 1
                continue

        # 3. Uncategorized
        callee_group[node_id] = "uncategorized"
        group_members["uncategorized"].add(node_id)
        uncategorized.append(node_id)

    print(f"Stage 4: Classification results")
    print(f"  Locked-list matches: {locked_matches}")
    print(f"  Embedding matches (>={EMBED_SIM_THRESHOLD}): {embedding_matches}")
    print(f"  Uncategorized: {len(uncategorized)}")
    print()
    print(f"  Group membership counts:")
    for gname in sorted(group_members.keys()):
        count = len(group_members[gname])
        gtype = cap_defs.get(gname, {}).get("type", "?")
        print(f"    {gname:25s} [{gtype:15s}] {count:4d} members")
    print()

    return callee_group, dict(group_members), uncategorized


# ── Stage 5: Build entry-point → capability mapping ─────────────────

def build_entry_capability_map(
    cmd_callees: dict[str, dict[str, int]],
    callee_group: dict[str, str],
) -> tuple[dict[str, set[str]], Counter]:
    """Project entry_point→callee into entry_point→capability.

    Returns:
        cmd_caps: entry_name → set of capability group names
        cap_usage: Counter of how many entry points use each capability
    """
    cmd_caps: dict[str, set[str]] = {}
    for cmd, callees in cmd_callees.items():
        caps: set[str] = set()
        for callee_node in callees:
            group = callee_group.get(callee_node, "uncategorized")
            if group != "uncategorized":
                caps.add(group)
        cmd_caps[cmd] = caps

    cap_usage: Counter = Counter()
    for caps in cmd_caps.values():
        for cap in caps:
            cap_usage[cap] += 1

    print(f"Stage 5: Entry-point -> capability mapping")
    print(f"  Top 15 most-used capabilities:")
    for cap, count in cap_usage.most_common(15):
        print(f"    {count:4d} entry points use: {cap}")
    print()

    return cmd_caps, cap_usage


# ── Stage 6: Derive capability → capability dependencies ────────────

def derive_capability_dependencies(
    graph: nx.MultiDiGraph,
    all_callee_nodes: set[str],
    callee_group: dict[str, str],
    cap_defs: dict[str, dict],
) -> dict[str, dict[str, dict]]:
    """Follow callee→callee call edges to find cross-capability deps.

    Returns:
        cap_deps: src_cap → {tgt_cap: {"call_count": N, "edge_type": str}}
    """
    # Count raw cross-group calls
    raw_counts: defaultdict[str, Counter] = defaultdict(Counter)
    group_type = {g: d["type"] for g, d in cap_defs.items()}

    for node_id in all_callee_nodes:
        src_group = callee_group.get(node_id, "uncategorized")
        if src_group == "uncategorized":
            continue

        for _, target, ed in graph.edges(node_id, data=True):
            if ed.get("type") == "calls" and target in all_callee_nodes:
                tgt_group = callee_group.get(target, "uncategorized")
                if tgt_group != "uncategorized" and src_group != tgt_group:
                    raw_counts[src_group][tgt_group] += 1

    # Build typed edges above threshold
    cap_deps: dict[str, dict[str, dict]] = {}
    for src_cap in sorted(raw_counts.keys()):
        deps = {}
        for tgt_cap, count in raw_counts[src_cap].most_common():
            if count >= EDGE_THRESHOLD:
                src_type = group_type.get(src_cap, "domain")
                tgt_type = group_type.get(tgt_cap, "domain")
                edge_type = classify_edge(src_type, tgt_type)
                deps[tgt_cap] = {
                    "call_count": count,
                    "edge_type": edge_type,
                }
        if deps:
            cap_deps[src_cap] = deps

    print(f"Stage 6: Capability dependencies (>={EDGE_THRESHOLD} calls)")
    for src in sorted(cap_deps.keys()):
        deps = cap_deps[src]
        dep_strs = [f"{k}({v['call_count']},{v['edge_type']})" for k, v in
                     sorted(deps.items(), key=lambda x: -x[1]['call_count'])[:5]]
        print(f"  {src:25s} -> {', '.join(dep_strs)}")
    print()

    return cap_deps


# ── Stage 7: Build DAG, break cycles, compute waves ─────────────────

def build_wave_ordering(
    cap_defs: dict[str, dict],
    group_members: dict[str, set[str]],
    cap_deps: dict[str, dict[str, dict]],
    cap_usage: Counter,
) -> tuple[nx.DiGraph, dict[str, int], dict[int, list[str]]]:
    """Build capability DAG, break cycles, compute wave numbers.

    Utility edges (uses_utility) are excluded from wave computation
    since utilities should not dominate implementation ordering.
    """
    cap_graph = nx.DiGraph()

    # Add nodes for all groups with members
    for gname in cap_defs:
        if gname in group_members:
            cap_graph.add_node(gname, type=cap_defs[gname]["type"])
    if "uncategorized" in group_members:
        cap_graph.add_node("uncategorized", type="residual")

    # Add edges — exclude uses_utility for ordering purposes
    for src, deps in cap_deps.items():
        for tgt, info in deps.items():
            if src in cap_graph and tgt in cap_graph:
                edge_type = info["edge_type"]
                # All edge types contribute to the DAG except uses_utility
                if edge_type != "uses_utility":
                    cap_graph.add_edge(src, tgt,
                                       weight=info["call_count"],
                                       edge_type=edge_type)

    # Break cycles by removing weakest edge
    cycles_broken = 0
    while True:
        try:
            cycle = nx.find_cycle(cap_graph)
            min_edge = min(cycle, key=lambda e: cap_graph[e[0]][e[1]].get("weight", 1))
            w = cap_graph[min_edge[0]][min_edge[1]].get("weight", 1)
            print(f"  Breaking cycle: {min_edge[0]} -> {min_edge[1]} (weight={w})")
            cap_graph.remove_edge(min_edge[0], min_edge[1])
            cycles_broken += 1
        except nx.NetworkXNoCycle:
            break

    # Compute waves via longest-path layering
    longest_path: dict[str, int] = {}
    for cap in reversed(list(nx.topological_sort(cap_graph))):
        succs = list(cap_graph.successors(cap))
        if not succs:
            longest_path[cap] = 0
        else:
            longest_path[cap] = max(longest_path.get(s, 0) for s in succs) + 1

    wave_by_cap: dict[str, int] = {}
    waves: defaultdict[int, list[str]] = defaultdict(list)
    for cap in cap_graph.nodes():
        w = longest_path.get(cap, 0)
        wave_by_cap[cap] = w
        waves[w].append(cap)

    print(f"\nStage 7: Implementation waves ({cycles_broken} cycles broken)")
    for wave_num in sorted(waves.keys()):
        caps = sorted(waves[wave_num])
        print(f"\n  Wave {wave_num}:")
        for cap in caps:
            n_cmds = cap_usage.get(cap, 0)
            n_funcs = len(group_members.get(cap, set()))
            gtype = cap_defs.get(cap, {}).get("type", "?")
            deps = sorted(cap_graph.successors(cap))
            dep_str = f" -> {', '.join(deps)}" if deps else " (leaf)"
            print(f"    {cap:25s} [{gtype:14s}] {n_cmds:3d} cmds, {n_funcs:3d} funcs{dep_str}")
    print()

    return cap_graph, wave_by_cap, dict(waves)


# ── Stage 8: Entry-point enablement ─────────────────────────────────

def compute_enablement(
    waves: dict[int, list[str]],
    cmd_caps: dict[str, set[str]],
) -> dict[str, int]:
    """Determine at which wave each entry point becomes enabled."""
    cumulative_caps: set[str] = set()
    prev_enabled: set[str] = set()
    cmd_earliest_wave: dict[str, int] = {}

    print("Stage 8: Entry-point enablement")
    for wave_num in sorted(waves.keys()):
        cumulative_caps.update(waves[wave_num])
        enabled: set[str] = set()

        for cmd, caps in cmd_caps.items():
            required = caps - {"uncategorized"}
            if required and required.issubset(cumulative_caps):
                enabled.add(cmd)
            elif not required:
                enabled.add(cmd)

        newly = sorted(enabled - prev_enabled)
        for cmd in newly:
            cmd_earliest_wave[cmd] = wave_num

        print(f"  Wave {wave_num}: +{len(newly)} newly enabled "
              f"(total: {len(enabled)}/{len(cmd_caps)})")
        prev_enabled = enabled

    max_wave = max(waves.keys()) if waves else 0
    for cmd in cmd_caps:
        if cmd not in cmd_earliest_wave:
            cmd_earliest_wave[cmd] = max_wave + 1

    not_enabled = sum(1 for w in cmd_earliest_wave.values() if w > max_wave)
    if not_enabled:
        print(f"  Not enabled by any wave: {not_enabled}")
    print()

    return cmd_earliest_wave


# ── Stage 9: Export ──────────────────────────────────────────────────

def export_results(
    cap_graph: nx.DiGraph,
    group_members: dict[str, set[str]],
    callee_info: dict[str, dict],
    callee_group: dict[str, str],
    cap_defs: dict[str, dict],
    cap_deps: dict[str, dict[str, dict]],
    cap_usage: Counter,
    wave_by_cap: dict[str, int],
    waves: dict[int, list[str]],
    cmd_caps: dict[str, set[str]],
    cmd_earliest_wave: dict[str, int],
    uncategorized: list[str],
    output_path: Path = OUTPUT_PATH,
) -> None:
    """Write capability_graph.json with typed nodes and edges."""
    output: dict = {
        "metadata": {
            "groups": len(cap_defs),
            "entry_points": len(cmd_caps),
            "total_callees": len(callee_info),
            "uncategorized_count": len(uncategorized),
            "waves": len(waves),
            "edge_threshold": EDGE_THRESHOLD,
            "embed_sim_threshold": EMBED_SIM_THRESHOLD,
        },
        "capabilities": {},
        "dependencies": {},
        "waves": {},
        "entry_points": {},
        "uncategorized_callees": [],
    }

    # ── Capabilities ──
    for gname in sorted(cap_defs.keys()):
        if gname not in group_members:
            continue
        gdef = cap_defs[gname]
        members_info = []
        for nid in group_members[gname]:
            info = callee_info.get(nid, {})
            members_info.append({
                "name": info.get("name", "?"),
                "brief": info.get("brief"),
                "min_depth": info.get("min_depth", 999),
            })
        members_info.sort(key=lambda x: x["name"])

        output["capabilities"][gname] = {
            "type": gdef.get("type", "domain"),
            "description": gdef.get("desc", ""),
            "stability": gdef.get("stability", "stable"),
            "migration_role": gdef.get("migration_role", "core"),
            "target_surfaces": gdef.get("target_surfaces", ""),
            "wave": wave_by_cap.get(gname, -1),
            "entry_points_using": cap_usage.get(gname, 0),
            "function_count": len(group_members[gname]),
            "locked_count": len(gdef.get("locked", [])),
            "members": members_info,
        }

    # ── Typed dependencies ──
    for src in sorted(cap_deps.keys()):
        deps = cap_deps[src]
        typed_deps = {}
        for tgt, info in sorted(deps.items()):
            typed_deps[tgt] = {
                "edge_type": info["edge_type"],
                "call_count": info["call_count"],
                "in_dag": cap_graph.has_edge(src, tgt) if src in cap_graph and tgt in cap_graph else False,
            }
        output["dependencies"][src] = typed_deps

    # ── Waves ──
    for wave_num in sorted(waves.keys()):
        caps = sorted(waves[wave_num])
        output["waves"][str(wave_num)] = caps

    # ── Entry points ──
    for cmd in sorted(cmd_caps.keys()):
        caps = cmd_caps[cmd]
        non_uncat = sorted(caps - {"uncategorized"})
        entry_type = "command"
        if cmd.startswith("spell_"):
            entry_type = "spell"
        elif cmd.startswith("spec_"):
            entry_type = "special"
        output["entry_points"][cmd] = {
            "type": entry_type,
            "capabilities": non_uncat,
            "earliest_wave": cmd_earliest_wave.get(cmd, 0),
        }

    # ── Uncategorized ──
    for node_id in uncategorized:
        info = callee_info.get(node_id, {})
        output["uncategorized_callees"].append({
            "name": info.get("name", "?"),
            "sig": info.get("sig", "?"),
            "brief": info.get("brief"),
            "min_depth": info.get("min_depth", 999),
        })
    output["uncategorized_callees"].sort(key=lambda x: x["name"])

    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"Stage 9: Exported to {output_path}")
    print(f"  {len(output['capabilities'])} capabilities")
    print(f"  {sum(len(d) for d in output['dependencies'].values())} dependency edges")
    print(f"  {len(output['waves'])} waves")
    print(f"  {len(output['entry_points'])} entry points")
    print(f"  {len(output['uncategorized_callees'])} uncategorized callees")


# ── Main ─────────────────────────────────────────────────────────────

def main():
    t0 = time.time()

    graph, entity_db, doc_db, emb_cache, cap_defs = load_artifacts()
    entries, entry_nodes = find_entry_points(graph)
    cmd_callees, callee_info, all_callee_nodes = map_callees(
        graph, entity_db, doc_db, emb_cache, entries, entry_nodes,
    )
    callee_group, group_members, uncategorized = classify_callees(
        all_callee_nodes, callee_info, cap_defs,
    )
    cmd_caps, cap_usage = build_entry_capability_map(
        cmd_callees, callee_group,
    )
    cap_deps = derive_capability_dependencies(
        graph, all_callee_nodes, callee_group, cap_defs,
    )
    cap_graph, wave_by_cap, waves = build_wave_ordering(
        cap_defs, group_members, cap_deps, cap_usage,
    )
    cmd_earliest_wave = compute_enablement(waves, cmd_caps)

    # Print uncategorized sample
    print(f"Uncategorized callees ({len(uncategorized)}):")
    uncat_list = []
    for node_id in uncategorized:
        info = callee_info.get(node_id, {})
        uncat_list.append((info.get("name", "?"), info.get("brief", ""), info.get("min_depth", 999)))
    for name, brief, depth in sorted(set(uncat_list))[:40]:
        b = f" -- {brief[:70]}" if brief else ""
        print(f"  [d={depth}] {name}{b}")
    if len(uncat_list) > 40:
        print(f"  ... and {len(uncat_list) - 40} more")
    print()

    export_results(
        cap_graph, group_members, callee_info, callee_group, cap_defs,
        cap_deps, cap_usage, wave_by_cap, waves, cmd_caps,
        cmd_earliest_wave, uncategorized,
    )

    elapsed = time.time() - t0
    print(f"\nDone in {elapsed:.1f}s")


if __name__ == "__main__":
    main()
