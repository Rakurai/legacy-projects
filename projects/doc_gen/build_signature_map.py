"""Regenerate signature_map.json from current code_graph.json + doc_db.json.

signature_map bridges two keying schemes:
  - doc_db keys: (compound_id, signature) tuples — stable across Doxygen re-runs
  - entity_ids: compound_id or compound_id_memberhash — change when Doxygen regenerates

Run after regenerating code_graph.json (Phase 0) to re-sync entity_ids.

Usage:
    uv run python projects/doc_gen/build_signature_map.py
"""

import json
from pathlib import Path

from legacy_common import ARTIFACTS_DIR

CODE_GRAPH_PATH = ARTIFACTS_DIR / "code_graph.json"
DOC_DB_PATH = ARTIFACTS_DIR / "doc_db.json"
SIGNATURE_MAP_PATH = ARTIFACTS_DIR / "signature_map.json"


def build_entity_id(entity: dict) -> str:
    cid = entity["id"]["compound"]
    mid = entity["id"].get("member")
    return f"{cid}_{mid}" if mid else cid


def build_signature(entity: dict) -> str:
    defn = entity.get("definition")
    args = entity.get("argsstring")
    if defn and args is not None:
        return f"{defn}{args}"
    return entity.get("name", "")


def build_signature_map() -> dict[str, str]:
    with open(CODE_GRAPH_PATH) as f:
        entities = json.load(f)
    with open(DOC_DB_PATH) as f:
        doc_db = json.load(f)

    # (compound_id, signature) -> entity_id from code_graph.json
    # When duplicates exist, prefer the entity with a body location.
    cg_lookup: dict[str, str] = {}
    cg_has_body: dict[str, bool] = {}

    for e in entities:
        key = repr((e["id"]["compound"], build_signature(e)))
        entity_id = build_entity_id(e)
        has_body = bool(e.get("body", {}).get("fn"))

        if key in cg_lookup:
            if has_body and not cg_has_body[key]:
                cg_lookup[key] = entity_id
                cg_has_body[key] = has_body
        else:
            cg_lookup[key] = entity_id
            cg_has_body[key] = has_body

    # Build map: union of doc_db keys and code_graph keys
    sig_map: dict[str, str] = {}
    matched = 0
    unmatched_doc_keys = []

    for doc_key in doc_db:
        if doc_key in cg_lookup:
            sig_map[doc_key] = cg_lookup[doc_key]
            matched += 1
        else:
            unmatched_doc_keys.append(doc_key)

    # Add code_graph entities not in doc_db
    extra = 0
    for key, eid in cg_lookup.items():
        if key not in sig_map:
            sig_map[key] = eid
            extra += 1

    print(f"doc_db entries matched to code_graph: {matched}")
    if unmatched_doc_keys:
        print(f"doc_db entries with no code_graph match: {len(unmatched_doc_keys)}")
    print(f"code_graph entries not in doc_db (added): {extra}")
    print(f"Total signature_map entries: {len(sig_map)}")

    return sig_map


def main() -> None:
    sig_map = build_signature_map()

    # Compare with existing if present
    if SIGNATURE_MAP_PATH.exists():
        with open(SIGNATURE_MAP_PATH) as f:
            old = json.load(f)
        preserved = sum(1 for k, v in old.items() if sig_map.get(k) == v)
        rekeyed = sum(1 for k, v in old.items() if k in sig_map and sig_map[k] != v)
        dropped = sum(1 for k in old if k not in sig_map)
        print(f"\nVs existing signature_map.json ({len(old)} entries):")
        print(f"  Preserved: {preserved}")
        print(f"  Rekeyed (new entity_id): {rekeyed}")
        print(f"  Dropped: {dropped}")

    with open(SIGNATURE_MAP_PATH, "w") as f:
        json.dump(sig_map, f, indent=2)
    print(f"\nWrote {SIGNATURE_MAP_PATH}")


if __name__ == "__main__":
    main()
