#!/usr/bin/env python3
"""
Phase 3, Pass 2 — Apply curated review decisions to produce chunk_registry.json.

Reads candidate_chunks.json and applies reviewer decisions:
- implementation mode (native / adaptation / reference / replacement / substrate)
- umbrella annotations
- planning phase assignment (A/B/C/D)
- updated sequencing notes
"""

import json
from pathlib import Path

BASE = Path(__file__).parent
CANDIDATES_PATH = BASE / "candidate_chunks.json"
OUT_PATH = BASE / "chunk_registry.json"

# ── Reviewer decisions ───────────────────────────────────────────────────────

# Implementation modes:
#   native          — real target-side game logic to build
#   adaptation      — thin compatibility/integration layer over Evennia/Python
#   reference       — preserves understanding, no real implementation needed
#   replacement     — replaced by Evennia contrib or Python stdlib
#   substrate       — Evennia already provides this; integration concern only
IMPL_MODES = {
    "world_structure":    "native",
    "state_rules":        "native",
    "attributes":         "native",
    "visibility_rules":   "native",
    "skills_progression": "native",
    "movement":           "native",
    "affects":            "native",
    "objects":            "native",
    "combat":             "native",
    "quests":             "native",
    "clans":              "native",
    "pvp":                "native",
    "social":             "native",
    "notes":              "native",
    "economy":            "native",
    "npc_behavior":       "native",
    "magic":              "native",
    "numerics":           "native",
    "entity_lookup":      "adaptation",
    "output":             "adaptation",
    "display":            "adaptation",
    "arg_parsing":        "adaptation",
    "admin":              "adaptation",
    "flags":              "reference",
    "string_ops":         "reference",
    "memory":             "reference",
    "text_editing":       "replacement",
    "imaging":            "replacement",
    "runtime":            "substrate",
    "persistence":        "native",
}

# Umbrella chunks: will likely need multiple spec dossiers
UMBRELLA = {"world_structure", "affects", "persistence", "objects"}

# Planning phases (reviewer's recommended implementation progression)
#   A — target substrate decisions (architectural commitment, not chunk implementation)
#   B — foundational game semantics (first real reusable contracts)
#   C — first user-visible vertical slices
#   D — heavier systemic features
PLANNING_PHASES = {
    # Phase B — foundational
    "world_structure":    "B",
    "state_rules":        "B",
    "attributes":         "B",
    "visibility_rules":   "B",
    "output":             "B",
    "entity_lookup":      "B",
    "skills_progression": "B",
    # Phase C — vertical slices
    "movement":           "C",
    "display":            "C",
    "objects":            "C",
    "social":             "C",
    "notes":              "C",
    # Phase D — heavier systemic
    "affects":            "D",
    "combat":             "D",
    "magic":              "D",
    "quests":             "D",
    "clans":              "D",
    "pvp":                "D",
    "npc_behavior":       "D",
    "economy":            "D",
    "persistence":        "D",
    # Not phased — reference/replacement/substrate
    "flags":              None,
    "string_ops":         None,
    "numerics":           None,
    "imaging":            None,
    "memory":             None,
    "text_editing":       None,
    "runtime":            None,
    "admin":              "B",
    "arg_parsing":        None,
}

# Reviewer notes per chunk
NOTES = {
    "world_structure": "Umbrella chunk. Target-side breakup: room/exit typeclasses, prototypes/content generation, world metadata/mapping, calendar/weather. Do not let it become one giant module.",
    "state_rules": "One of the most important early chunks. Lock functions + permission checks in rules modules.",
    "attributes": "Foundational. Traits handler/contrib + derived-stat rules.",
    "visibility_rules": "Small, clean policy boundary. return_appearance filtering + lock functions.",
    "output": "Adapter chunk. Preserve user-visible messaging semantics; map to Evennia-native msg/display surfaces. Do not port legacy transport internals.",
    "admin": "Support chunk, not a core architectural driver. Admin CmdSet + logging utilities.",
    "skills_progression": "Core domain system. Traits handler + skills rules + progression handler.",
    "notes": "Small self-contained domain feature. Msg system or board contrib + note handler.",
    "entity_lookup": "Cross-cutting search/resolution service. Keep standalone — merging into objects would make the plan more DIKU-shaped than Evennia-shaped. Target: search functions + DefaultObject.search overrides.",
    "magic": "Small standalone chunk. Spell dispatch, saves, dispels, incantation — a real semantic seam separate from skill lookup/progression.",
    "movement": "Core domain system. Movement rules + exit/room typeclass hooks.",
    "affects": "Umbrella chunk. Likely becomes a single handler/service in target. Do not split during planning — only split during spec writing if dossier shows clearly separate implementation surfaces.",
    "npc_behavior": "Late and architecture-sensitive. Depends on chosen NPC model, Script strategy, event/trigger integration, runtime surfaces.",
    "pvp": "Small leaf. Defer to late migration.",
    "objects": "Umbrella chunk. Keep separate from entity_lookup. Likely multi-spec later. Object handlers + rules + prototypes + shop layer.",
    "display": "Projection-only consumer. return_appearance + get_display_* hooks + display helpers.",
    "persistence": "Umbrella chunk. Will dissolve into multiple target-side surfaces: character/object save state, content import/area conversion, notes/social persistence, clan/war persistence, SQL integration.",
    "quests": "Self-contained feature. Quest handler + Script + rules.",
    "clans": "Clean organizational system. Tags/locks + clan handler + global Script.",
    "social": "Small leaf. Social CmdSet + channel contrib/handler.",
    "economy": "Standalone leaf. Economy is distinct from object lifecycle even if they share Evennia surfaces. Late/optional until validated by user-story priority.",
    "flags": "Reference-only. Do not build a flag system unless a specific legacy-visible behavior demands it. Use Evennia tags/locks.",
    "string_ops": "Reference-only. Use Python string behavior by default; preserve legacy-specific text quirks only where they affect UX.",
    "numerics": "Small, safe, useful utility. Keep as real chunk.",
    "imaging": "Defer/drop. Only resurrect if world-map presentation requires it.",
    "memory": "Reference-only. Not needed — Python GC.",
    "text_editing": "Use EvEditor contrib unless legacy editor exposes must-preserve behaviors.",
    "arg_parsing": "Adaptation layer. Capture legacy parsing quirks only where behavior matters. Not a major implementation focus.",
    "combat": "Major late heavy chunk. Dependency breadth (13 chunks) makes late wave correct.",
    "runtime": "Evennia-provided substrate. The game loop, tickers, Scripts already exist. Game-specific hooks are integration concerns attached to other chunks, not a standalone deliverable.",
}

# Vertical slice assignments (Phase C sub-grouping)
VERTICAL_SLICES = {
    "slice_1_inspect_navigate": {
        "name": "Inspect & Navigate",
        "description": "Room exists, can move, can look, can resolve targets. First playable milestone.",
        "primary_chunks": ["movement", "display"],
        "supporting_chunks": ["world_structure", "visibility_rules", "output", "entity_lookup"],
    },
    "slice_2_manipulate_objects": {
        "name": "Manipulate Objects",
        "description": "Can pick up, drop, wear, remove objects. Basic inventory.",
        "primary_chunks": ["objects"],
        "supporting_chunks": ["entity_lookup", "attributes", "state_rules"],
    },
    "slice_3_communication": {
        "name": "Communication",
        "description": "Chat channels, tells, notes, social actions.",
        "primary_chunks": ["social", "notes"],
        "supporting_chunks": ["output"],
    },
}


def main():
    with open(CANDIDATES_PATH) as f:
        candidates = json.load(f)

    chunks = {}
    for cid, c in candidates["chunks"].items():
        chunk = {
            "chunk_id": cid,
            "capabilities": c["capabilities"],
            "capability_type": c["capability_type"],
            "implementation_mode": IMPL_MODES[cid],
            "planning_phase": PLANNING_PHASES.get(cid),
            "is_umbrella": cid in UMBRELLA,
            "decision_notes": NOTES.get(cid, ""),
            # From candidate data
            "tier_num": c["tier_num"],
            "tier_name": c["tier_name"],
            "evidence_wave": c["wave"],
            "impl_wave": c["impl_wave"],
            "member_count": c["member_count"],
            "fan_in_dag": c["fan_in_dag"],
            "fan_in_all": c["fan_in_all"],
            "fan_out_dag": c["fan_out_dag"],
            "fan_out_all": c["fan_out_all"],
            "description": c["description"],
            "migration_role": c["migration_role"],
            "target_surfaces": c["target_surfaces"],
            # Entry-point enablement
            "enables_entry_points": c["enables_entry_points"],
            "enabled_commands": c["enabled_commands"],
            "enabled_spells": c["enabled_spells"],
            "enabled_specials": c["enabled_specials"],
        }
        chunks[cid] = chunk

    # Chunk dependencies — carry forward from candidates
    chunk_deps = candidates["chunk_dependencies"]

    # Implementation mode summary
    mode_groups = {}
    for cid, c in chunks.items():
        mode = c["implementation_mode"]
        mode_groups.setdefault(mode, []).append(cid)

    phase_groups = {}
    for cid, c in chunks.items():
        ph = c["planning_phase"]
        if ph:
            phase_groups.setdefault(ph, []).append(cid)

    registry = {
        "metadata": {
            "description": "Chunk registry — Phase 3 Pass 2 curated output",
            "source": "candidate_chunks.json + reviewer decisions",
            "total_chunks": len(chunks),
            "by_implementation_mode": {k: sorted(v) for k, v in sorted(mode_groups.items())},
            "by_planning_phase": {k: sorted(v) for k, v in sorted(phase_groups.items())},
            "umbrella_chunks": sorted(UMBRELLA),
        },
        "chunks": chunks,
        "chunk_dependencies": chunk_deps,
        "implementation_order": candidates["implementation_order"],
        "vertical_slices": VERTICAL_SLICES,
    }

    with open(OUT_PATH, "w") as f:
        json.dump(registry, f, indent=2)

    # Summary
    print(f"Output: {OUT_PATH}")
    print(f"Total chunks: {len(chunks)}")
    print()
    print("--- By implementation mode ---")
    for mode, members in sorted(mode_groups.items()):
        print(f"  {mode}: {sorted(members)}")
    print()
    print("--- By planning phase ---")
    for ph, members in sorted(phase_groups.items()):
        print(f"  Phase {ph}: {sorted(members)}")
    print()
    print("--- Umbrella chunks ---")
    print(f"  {sorted(UMBRELLA)}")
    print()
    print("--- Vertical slices (Phase C) ---")
    for sid, s in VERTICAL_SLICES.items():
        print(f"  {s['name']}: primary={s['primary_chunks']}, supporting={s['supporting_chunks']}")


if __name__ == "__main__":
    main()
