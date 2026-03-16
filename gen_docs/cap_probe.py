#!/usr/bin/env python3
"""
cap_probe — batch tool for tuning capability_defs.json descriptions.

Iterates over every group in capability_defs.json, embeds its description
against the full callee embedding pool, and writes per-group result files
to .ai/gen_docs/cap_probe_results/.

Each file shows every function above a similarity threshold together with
its doxygen documentation.  If a group has an "avoid" field, functions
more similar to the avoid text are marked [AVOIDED].

Usage:

    # Run all groups at default threshold (0.40), with doxygen docs
    python cap_probe.py

    # Custom threshold, compact (no doxygen text)
    python cap_probe.py --threshold 0.35 --no-doc

    # Include avoided functions in output
    python cap_probe.py --show-avoided

    # Probe a single group (writes only that file)
    python cap_probe.py --group output

    # Probe raw text (writes to cap_probe_results/_custom.txt)
    python cap_probe.py --text "combat damage calculation"
"""
from __future__ import annotations

import argparse
import json
import pickle
import sys
from pathlib import Path
from collections import defaultdict

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

HERE = Path(__file__).resolve().parent
CLUSTERING_DIR = HERE / "clustering"
if str(CLUSTERING_DIR) not in sys.path:
    sys.path.insert(0, str(CLUSTERING_DIR))

import doc_db as ddb
import doxygen_graph as dg
import doxygen_parse as dp


# ── Loading (cached across invocations via module-level globals) ─────

_cache: dict = {}

def _load():
    """Load all artifacts once."""
    if _cache:
        return _cache

    print("Loading artifacts...", file=sys.stderr)

    # Graph, entity DB, doc DB
    graph = dg.load_graph(CLUSTERING_DIR / "code_graph.gml")
    entity_db = dp.load_db(CLUSTERING_DIR / "code_graph.json")
    doc_database = ddb.DocumentDB()
    doc_database.load(ddb.DOC_DB_PATH)

    # Embeddings cache
    with open(CLUSTERING_DIR / "embeddings_cache.pkl", "rb") as f:
        all_embeddings: dict[str, np.ndarray] = pickle.load(f)

    # Capability defs
    with open(HERE / "capability_defs.json") as f:
        cap_defs: dict[str, dict] = json.load(f)

    # Classification results (if available)
    cls_path = HERE / "capability_classifications.json"
    classifications = {}
    if cls_path.exists():
        with open(cls_path) as f:
            cls_data = json.load(f)
        classifications = cls_data.get("classifications", {})

    # OpenAI embedding model
    import openai_embeddings as oai_emb

    # Build callee pool: node_id → (name, embedding, doc_text, brief, current_group)
    # Re-derive callee info from graph (same logic as notebook)
    ENTRY_PREFIXES = ("do_", "spell_", "spec_")

    def is_entry_point(name: str) -> bool:
        return any(f" {p}" in name or name.startswith(p) for p in ENTRY_PREFIXES)

    def bare_name(sig: str) -> str:
        paren = sig.find("(")
        if paren > 0:
            sig = sig[:paren]
        space = sig.rfind(" ")
        if space > 0:
            sig = sig[space + 1:]
        return sig

    entry_nodes = {
        n for n, d in graph.nodes(data=True)
        if d.get("kind") == "function" and is_entry_point(d.get("name", ""))
    }

    # BFS to collect all transitive callees
    def get_calls(g, node_id):
        return {v for _, v, ed in g.edges(node_id, data=True) if ed.get("type") == "calls"}

    all_callees: set[str] = set()
    for ep in entry_nodes:
        visited = set()
        queue = list(get_calls(graph, ep) - entry_nodes - {ep})
        visited.update(queue)
        while queue:
            node = queue.pop(0)
            for callee in get_calls(graph, node):
                if callee not in visited and callee not in entry_nodes:
                    visited.add(callee)
                    queue.append(callee)
        all_callees |= visited

    # Build pool
    pool: dict[str, dict] = {}
    for nid in sorted(all_callees):
        nd = graph.nodes[nid]
        sig = nd.get("name", nid)
        name = bare_name(sig)

        # Resolve doc
        doc = None
        doc_text = None
        try:
            eid = dg.get_body_eid(entity_db, nid)
            entity = entity_db.get(eid)
            if entity:
                doc = doc_database.get_doc(eid.compound, entity.signature)
                if doc is None and eid.compound in doc_database:
                    for _sig, d in doc_database[eid.compound].items():
                        if d.name == entity.name and d.brief:
                            doc = d
                            break
        except Exception:
            pass

        if doc:
            doc_text = doc.to_doxygen()

        # Embedding: try cache, else skip
        emb = None
        if doc and doc.mid and doc.mid in all_embeddings:
            emb = all_embeddings[doc.mid]

        if emb is None:
            continue  # can't probe without embedding

        # Current classification
        cls_info = classifications.get(nid, {})
        current_group = cls_info.get("group", None)

        pool[nid] = {
            "name": name,
            "sig": sig,
            "brief": doc.brief if doc else None,
            "doc_text": doc_text,
            "embedding": emb,
            "current_group": current_group,
        }

    # Pre-stack embeddings for vectorised similarity
    pool_ids = list(pool.keys())
    pool_matrix = np.stack([pool[nid]["embedding"] for nid in pool_ids])

    # Build locked index: name → group, and per-group sets of names
    locked_by_group: dict[str, set[str]] = {}
    locked_name_to_group: dict[str, str] = {}
    for gname, gdef in cap_defs.items():
        names = set(gdef.get("locked", []))
        locked_by_group[gname] = names
        for n in names:
            locked_name_to_group[n] = gname

    # Map pool node_ids to their locked group (if any)
    locked_nids: dict[str, str] = {}  # nid → group
    for nid in pool_ids:
        name = pool[nid]["name"]
        if name in locked_name_to_group:
            locked_nids[nid] = locked_name_to_group[name]

    _cache.update(
        graph=graph, entity_db=entity_db, doc_db=doc_database,
        all_embeddings=all_embeddings, cap_defs=cap_defs,
        sbert=None, oai_emb=oai_emb, pool=pool, pool_ids=pool_ids, pool_matrix=pool_matrix,
        classifications=classifications,
        locked_by_group=locked_by_group, locked_nids=locked_nids,
    )
    total_locked = sum(len(s) for s in locked_by_group.values())
    mapped = len(locked_nids)
    print(f"Loaded {len(pool)} callees with embeddings ({total_locked} locked defs, {mapped} matched in pool).", file=sys.stderr)
    return _cache


def encode(text: str) -> np.ndarray:
    c = _load()
    return c["oai_emb"].embed_single(text)


def probe(desc_text: str, threshold: float = 0.40,
          avoid_text: str | None = None, avoid_threshold: float | None = None,
          show_avoided: bool = False,
          only_foreign_group: str | None = None,
          include_locked: bool = False) -> list[dict]:
    """
    Embed desc_text and return all callees above threshold.

    If avoid_text is provided, any callee whose similarity to avoid_text
    exceeds its similarity to desc_text (or exceeds avoid_threshold) is
    marked as "avoided".

    If include_locked is False (default), functions that appear in any
    group's "locked" list are silently excluded from results.
    When True, they appear with a 'locked_group' field set.

    Returns list of dicts sorted by descending similarity.
    """
    c = _load()
    pool = c["pool"]
    pool_ids = c["pool_ids"]
    pool_matrix = c["pool_matrix"]
    locked_nids = c["locked_nids"]

    desc_vec = encode(desc_text).reshape(1, -1)
    sims = cosine_similarity(pool_matrix, desc_vec).flatten()

    avoid_sims = None
    if avoid_text:
        avoid_vec = encode(avoid_text).reshape(1, -1)
        avoid_sims = cosine_similarity(pool_matrix, avoid_vec).flatten()

    results = []
    for i, nid in enumerate(pool_ids):
        sim = float(sims[i])
        if sim < threshold and not show_avoided:
            continue

        info = pool[nid]

        # Locked filtering
        locked_group = locked_nids.get(nid)
        if locked_group and not include_locked:
            continue

        avoided = False
        avoid_sim = None

        if avoid_sims is not None:
            avoid_sim = float(avoid_sims[i])
            if avoid_threshold is not None:
                avoided = avoid_sim >= avoid_threshold
            else:
                avoided = avoid_sim > sim

        if only_foreign_group and info["current_group"] == only_foreign_group:
            continue

        if sim < threshold and not (show_avoided and avoided):
            continue

        results.append({
            "node_id": nid,
            "name": info["name"],
            "sig": info["sig"],
            "brief": info["brief"],
            "similarity": sim,
            "avoided": avoided,
            "avoid_similarity": avoid_sim,
            "current_group": info["current_group"],
            "locked_group": locked_group,
            "doc_text": info["doc_text"],
        })

    results.sort(key=lambda r: -r["similarity"])
    return results


def format_results(results: list[dict], show_doc: bool = True,
                   show_avoided: bool = False) -> str:
    """Format probe results as a string."""
    lines = []
    avoided_count = 0
    locked_count = 0
    matched_count = 0
    for r in results:
        if r["avoided"]:
            avoided_count += 1
            if not show_avoided:
                continue

        is_locked = bool(r.get("locked_group"))
        if is_locked:
            locked_count += 1

        tag = ""
        if r["avoided"]:
            tag = " [AVOIDED]"
        elif is_locked:
            tag = f" [LOCKED→{r['locked_group']}]"
        elif r["current_group"]:
            tag = f" [{r['current_group']}]"

        brief = f" — {r['brief'][:70]}" if r["brief"] else ""
        avoid_str = ""
        if r["avoid_similarity"] is not None:
            avoid_str = f"  avoid={r['avoid_similarity']:.3f}"

        lines.append(f"  {r['similarity']:.3f}{avoid_str}  {r['name']:40s}{brief}{tag}")

        if show_doc and r["doc_text"]:
            for line in r["doc_text"].split("\n"):
                lines.append(f"    {line}")
            lines.append("")

        matched_count += 1

    total = len(results)
    not_avoided = total - avoided_count
    parts = [f"{not_avoided - locked_count} matched"]
    if locked_count:
        parts.append(f"{locked_count} locked")
    parts.append(f"{avoided_count} avoided")
    parts.append(f"{total} total above threshold")
    lines.append(f"\n--- {', '.join(parts)} ---")
    return "\n".join(lines)


RESULTS_DIR = HERE / "cap_probe_results"


def probe_group(group_name: str, cap_defs: dict, threshold: float,
                show_doc: bool, show_avoided: bool,
                include_locked: bool = False) -> str:
    """Probe a single group and return formatted output."""
    defn = cap_defs[group_name]
    desc_text = defn["desc"]
    avoid_text = defn.get("avoid")
    locked_list = defn.get("locked", [])

    header_lines = [
        f"=== {group_name} ({defn['type']}) ===",
        f"Stability: {defn.get('stability', 'n/a')}",
        f"Desc ({len(desc_text)} chars): {desc_text}",
    ]
    if avoid_text:
        header_lines.append(f"Avoid ({len(avoid_text)} chars): {avoid_text}")
    if locked_list:
        header_lines.append(f"Locked: {len(locked_list)} functions")
    header_lines.append(f"Threshold: {threshold}")
    header_lines.append("")

    results = probe(
        desc_text, threshold,
        avoid_text=avoid_text,
        show_avoided=show_avoided,
        include_locked=include_locked,
    )

    # Filter: only keep functions locked to THIS group (or unlocked matches)
    results = [
        r for r in results
        if not r.get("locked_group") or r["locked_group"] == group_name
    ]

    body = format_results(results, show_doc=show_doc, show_avoided=show_avoided)
    return "\n".join(header_lines) + "\n" + body


def generate_diagnostic(show_doc: bool = False) -> str:
    """Generate a single diagnostic document grouping all locked functions
    by their group, each sorted by similarity to the group description.

    For each group: embed the description, compute similarity of every locked
    member to that description, and list them in descending similarity order.
    Groups are sorted by their mean locked-member similarity (ascending, so
    weakest groups appear first).
    """
    c = _load()
    cap_defs = c["cap_defs"]
    pool = c["pool"]
    pool_ids = c["pool_ids"]
    pool_matrix = c["pool_matrix"]
    locked_nids = c["locked_nids"]

    # Reverse map: pool name → nid
    name_to_nid = {pool[nid]["name"]: nid for nid in pool_ids}

    group_reports: list[tuple[float, str, str]] = []  # (mean_sim, group_name, text)

    overall_sims: list[float] = []

    for gname, gdef in cap_defs.items():
        locked_names = gdef.get("locked", [])
        if not locked_names:
            continue

        desc = gdef["desc"]
        gtype = gdef["type"]
        stability = gdef.get("stability", "")

        # Embed group description
        desc_vec = encode(desc).reshape(1, -1)

        # Compute similarity for every locked member
        rows: list[tuple[float, str, str | None, str | None]] = []  # (sim, name, brief, doc_text)
        missing: list[str] = []
        for fn_name in locked_names:
            nid = name_to_nid.get(fn_name)
            if nid is None:
                missing.append(fn_name)
                continue
            info = pool[nid]
            emb = info["embedding"].reshape(1, -1)
            sim = float(cosine_similarity(emb, desc_vec)[0, 0])
            rows.append((sim, fn_name, info["brief"], info["doc_text"]))

        rows.sort(key=lambda r: -r[0])
        sims = [r[0] for r in rows]
        overall_sims.extend(sims)
        mean_sim = np.mean(sims) if sims else 0.0
        min_sim = min(sims) if sims else 0.0
        max_sim = max(sims) if sims else 0.0

        lines: list[str] = []
        lines.append(f"{'='*80}")
        lines.append(f"[{gtype}] {gname}  (stability: {stability})")
        lines.append(f"  desc: {desc[:120]}{'…' if len(desc) > 120 else ''}")
        lines.append(f"  locked: {len(locked_names)} functions, {len(rows)} with embeddings")
        lines.append(f"  sim to desc — mean: {mean_sim:.3f}  min: {min_sim:.3f}  max: {max_sim:.3f}")
        if missing:
            lines.append(f"  ⚠ missing from pool: {', '.join(missing)}")
        lines.append("")

        for sim, name, brief, doc_text in rows:
            b = f" — {brief[:70]}" if brief else ""
            lines.append(f"  {sim:.3f}  {name:40s}{b}")
            if show_doc and doc_text:
                for dl in doc_text.split("\n"):
                    lines.append(f"    {dl}")
                lines.append("")

        lines.append("")
        group_reports.append((mean_sim, gname, "\n".join(lines)))

    # Sort groups by mean similarity ascending (weakest first)
    group_reports.sort(key=lambda t: t[0])

    # Header
    total_locked = sum(len(d.get("locked", [])) for d in cap_defs.values())
    overall_mean = np.mean(overall_sims) if overall_sims else 0.0
    header_lines = [
        f"DIAGNOSTIC — locked functions vs group descriptions",
        f"Groups: {len([g for g in cap_defs.values() if g.get('locked')])}  "
        f"Total locked: {total_locked}  "
        f"Overall mean sim: {overall_mean:.3f}",
        f"Sorted by group mean similarity (ascending — weakest groups first)",
        "",
    ]

    return "\n".join(header_lines) + "\n".join(text for _, _, text in group_reports)


def main():
    parser = argparse.ArgumentParser(
        description="Probe capability_defs.json descriptions against callee embeddings.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--group", "-g",
                        help="Probe only this group (default: all groups)")
    parser.add_argument("--text", "-t",
                        help="Probe raw text (writes to _custom.txt)")
    parser.add_argument("--threshold", type=float, default=0.40,
                        help="Min cosine similarity (default: 0.40)")
    parser.add_argument("--show-avoided", action="store_true",
                        help="Include avoided functions in output")
    parser.add_argument("--no-doc", action="store_true",
                        help="Compact output: don't show full doxygen text")
    parser.add_argument("--include-locked", action="store_true",
                        help="Include locked functions in output (hidden by default)")
    parser.add_argument("--list-groups", action="store_true",
                        help="List all available group names and exit")
    parser.add_argument("--diagnostic", action="store_true",
                        help="Generate a single diagnostic report of all locked functions "
                             "grouped and sorted by similarity to their group description")

    args = parser.parse_args()

    c = _load()
    cap_defs = c["cap_defs"]

    if args.list_groups:
        for name, d in cap_defs.items():
            avoid_tag = " [has avoid]" if d.get("avoid") else ""
            locked_n = len(d.get("locked", []))
            locked_tag = f" [{locked_n} locked]" if locked_n else ""
            print(f"  {name:25s} ({d['type']:14s}) {d.get('stability','')}{avoid_tag}{locked_tag}")
        return

    RESULTS_DIR.mkdir(exist_ok=True)
    show_doc = not args.no_doc

    # ── Diagnostic mode ──────────────────────────────────────────────
    if args.diagnostic:
        report = generate_diagnostic(show_doc=show_doc)
        out_path = RESULTS_DIR / "_diagnostic.txt"
        out_path.write_text(report)
        print(f"Wrote diagnostic to {out_path}")
        return

    # ── Raw text mode ────────────────────────────────────────────────
    if args.text:
        results = probe(args.text, args.threshold, show_avoided=args.show_avoided,
                        include_locked=args.include_locked)
        header = f"=== Custom probe ===\nText: {args.text}\nThreshold: {args.threshold}\n"
        body = format_results(results, show_doc=show_doc, show_avoided=args.show_avoided)
        out_path = RESULTS_DIR / "_custom.txt"
        out_path.write_text(header + "\n" + body)
        print(f"Wrote {out_path}")
        return

    # ── Determine groups to probe ────────────────────────────────────
    if args.group:
        if args.group not in cap_defs:
            print(f"Unknown group '{args.group}'. Use --list-groups to see options.",
                  file=sys.stderr)
            sys.exit(1)
        groups = [args.group]
    else:
        groups = list(cap_defs.keys())

    # ── Probe each group and write results ───────────────────────────
    for group_name in groups:
        output = probe_group(
            group_name, cap_defs, args.threshold,
            show_doc=show_doc, show_avoided=args.show_avoided,
            include_locked=args.include_locked,
        )
        out_path = RESULTS_DIR / f"{group_name}.txt"
        out_path.write_text(output)
        # Brief summary to stdout
        defn = cap_defs[group_name]
        results = probe(defn["desc"], args.threshold, avoid_text=defn.get("avoid"),
                        include_locked=args.include_locked)
        matched = sum(1 for r in results if not r["avoided"] and not r.get("locked_group"))
        avoided = sum(1 for r in results if r["avoided"])
        locked = sum(1 for r in results if r.get("locked_group"))
        locked_str = f"  {locked:3d} locked" if args.include_locked else ""
        print(f"  {group_name:25s}  {matched:4d} matched  {avoided:3d} avoided{locked_str}  → {out_path.name}")

    print(f"\nWrote {len(groups)} files to {RESULTS_DIR}/")


if __name__ == "__main__":
    main()
