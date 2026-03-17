# V2 Ingestion Plan — Hierarchical System Documentation

**Feature**: `002-mcp-doc-server-v2`
**Created**: 2026-03-14
**Status**: Draft (pre-planning research)
**Purpose**: Document the envisioned approach for populating V2 database tables from subsystem documentation

---

## Source Material Assessment

All 23 component docs are the **single authoritative source** for ingestion. Each follows the canonical heading structure: Overview → Responsibilities → Core Components → Implementation Details → Key Files → System Behaviors → Dependencies and Relationships.

`subsystems.md` is **not used** for doc section chunking — its content has been merged into the component docs. It is only used for extracting subsystem names, group hierarchy, and cross-system dependency declarations ("Depends on" / "Depended on by" lines).

| Document | Lines |
|----------|-------|
| utilities | 400 |
| admin_controls | 331 |
| game_engine | 326 |
| logging_and_monitoring | 297 |
| memory_and_gc | 285 |
| status_and_look_commands | 268 |
| networking | 258 |
| builder_commands | 258 |
| mobprog_system | 251 |
| event_dispatcher | 242 |
| in_game_editor | 240 |
| character_system | 239 |
| persistence | 234 |
| world_visualization | 224 |
| world_system | 222 |
| object_system | 177 |
| social_and_communication | 150 |
| economy | 145 |
| command_interpreter | 142 |
| user_experience_enhancers | 137 |
| help_system | 137 |
| organizations_and_pvp | 134 |
| quests | 126 |

Total: ~5,200 lines of curated narrative prose across all component docs.

### Complementary Sources

- **`subsystems.md`** — 718 lines. Used **only** for extracting subsystem names (23 subsystems + 6 group headings), dependency declarations, and the ASCII dependency diagram. Not used for doc section chunking.
- **`components/*.md`** — The single source of truth for all doc section content. Each file follows the canonical heading structure.

---

## Phase A: Mechanical Ingestion (No Agent Needed)

Deterministic, runs in `build_v2_db.py`. Produces intermediate artifacts that can be validated before DB load.

### A.1 — Subsystem Records → `subsystems` table

**Source**: `subsystems.md` headings and structure.

Parse the 23 numbered subsystems (`### N. Name`) and their group headings (`## Group`):

| Field | Source | Example |
|-------|--------|---------|
| `id` | Derived from heading (slugified) | `game_engine`, `combat_system` |
| `name` | `### N. Name` heading text | "Game Engine", "Combat System" |
| `parent_id` | `## Group` heading → parent subsystem | `core_infrastructure` |
| `description` | First paragraph after heading | "The heartbeat of the server. Owns the main loop..." |
| `source_file` | Match to `components/*.md` by name | `components/game_engine.md` |
| `depends_on` | "Depends on:" line, parsed and normalized | `["utilities", "memory_and_gc", "event_dispatcher"]` |
| `depended_on_by` | "Depended on by:" line, parsed and normalized | `["combat_system", "quest_system"]` |

**Hierarchy**: The 6 `## Group` headings (Core Infrastructure, Entity Systems, Game Mechanics, Content & Scripting, Player Interaction, Operations) become parent subsystems, giving a 2-level hierarchy. ~29 total records (23 systems + 6 layer groups).

**Special handling**:
- "Everything" / "all player-facing systems" → expand to all other subsystem IDs
- "bidirectional" dependencies (e.g., Magic ↔ Combat mentioned in both) → two `depends_on` edges
- Fuzzy name normalization map: "Memory & GC" → `memory_and_gc`, "Character Data Model" → `character_data_model`

### A.2 — Subsystem Dependency Edges → `subsystem_edges` table

**Source**: "Depends on:" / "Depended on by:" lines in `subsystems.md`.

| Field | Example |
|-------|---------|
| `source_id` | `combat_system` |
| `target_id` | `character_data_model` |
| `relationship` | `depends_on` |

Estimated: ~60–80 edges.

Bidirectional relationships (e.g., Combat ↔ Magic) produce two edges: `combat_system → magic_system (depends_on)` and `magic_system → combat_system (depends_on)`.

### A.3 — Doc Section Chunks → `subsystem_docs` table

**Source**: All 23 `components/*.md` files.

Split at `##`/`###` heading boundaries. Each heading produces one record:

| Field | Source | Example |
|-------|--------|---------|
| `subsystem_id` | Filename match | `game_engine` |
| `section_path` | Heading hierarchy | "Core Components > Game Loop System" |
| `heading` | The heading text | "Game Loop System" |
| `section_kind` | Classified from heading (see table below) | `key_components` |
| `is_overview` | heading == "Overview" | `true` for exactly one per subsystem |
| `body` | Markdown text between this heading and the next | Full section content |
| `source_file` | Filepath | `components/game_engine.md` |
| `line_range` | Computed start/end lines | `[40, 57]` |

#### `section_kind` Classification

Mechanical mapping from the canonical heading structure:

| Heading pattern | → `section_kind` |
|-----------------|-------------------|
| "Overview" | `overview` |
| "Responsibilities" | `responsibilities` |
| "Core Components", "Key Files" | `key_components` |
| "Implementation Details", "...Implementation" | `implementation` |
| "Dependencies and Relationships" | `dependencies` |
| "System Behaviors" | `behaviors` |

All docs use the same canonical headings, so classification is trivially deterministic.

#### Embedding + tsvector generation

Runs on each chunk's body text during the build:
- Embedding via the configured embedding endpoint (same as V1 entity embeddings)
- Weighted tsvector: heading text = weight A, body text = weight B

**Estimated yield**: ~200–250 doc sections from the 23 component docs.

### A.4 — Intermediate Artifact Output

Phase A produces these files in `.ai/artifacts/v2/`:

| Artifact | Format | Content |
|----------|--------|---------|
| `subsystems_seed.json` | JSON array | ~29 subsystem records |
| `subsystem_doc_chunks.jsonl` | JSONL | ~200–250 doc section records |
| `subsystem_edges.json` | JSON array | ~60–80 dependency edges |

These are validated (FR-015 through FR-017) before DB ingestion.

---

## Phase B: Agent-Assisted Curation (Entity↔Subsystem Links)

The curation agent populates `entity_subsystem_links` — the many-to-many mapping connecting ~5,300 code entities to 23 subsystems with roles and evidence. This is where the quality of V2 is made or lost.

### B.1 — Strategy: Subsystem-Centric Walk

The agent works **one subsystem at a time**, using V1 MCP tools. For each subsystem:

#### Step 1 — Seed from component docs (mechanical + agent verification)

All component docs list "Key Source Areas" (or equivalent file/component references) with filenames:

```
## Key Source Areas
- `fight.cc` — core combat loop, attack/damage/death resolution
- `effects.cc` — elemental damage effects
```

For each listed file:
- `list_file_entities("src/fight.cc")` → all entities in that file are candidates
- Agent assigns roles: functions central to the subsystem's purpose → `core`; helper functions → `supporting`; entry points (`do_*`, `spell_*`, `spec_*`) → `entry_point`

For named functions in prose (e.g., "the `act()` system", "`damage()` calculation"):
- `resolve_entity("damage")` → link with `core` role at `high` confidence

#### Step 2 — Expand from entry points

Identify the entry points that belong to each subsystem:
- Combat: `do_kill`, `do_flee`, `do_rescue`, `do_bash`, `do_kick`, etc.
- Magic: `spell_fireball`, `spell_cure_light`, `spell_plague`, etc.
- Admin: `do_set`, `do_stat`, `do_transfer`, `do_purge`, etc.

Use `get_behavior_slice(entity="do_kill", max_depth=3)` to get the call cone:
- Direct callees in the same capability → `core` or `supporting` role
- Direct callees in a *different* capability → `integration` role (cross-system bridge)
- Transitive-only functions present at depth 2+ → `supporting` at lower confidence

#### Step 3 — Capability group cross-reference

V1's 30 capability groups map naturally to subsystems in many cases:

| Capability group | → Subsystem |
|-----------------|-------------|
| `combat` | Combat System |
| `affects` | Affect System |
| `magic` | Magic System |
| `persistence` | Persistence |
| `output` | Social & Communication (partially) |
| `string_ops`, `flags`, `numerics` | Utilities |

Use `get_capability_detail(capability="combat", include_functions=true)` → bulk-link functions to matching subsystem:
- Initial link_source: `inferred`, confidence: `medium`
- Agent reviews and promotes to `curated`/`high` for clearly correct mappings

#### Step 4 — Handle cross-cutting entities

Functions like `act()`, `send_to_char()`, `affect_to_char()` participate in many systems. The agent creates **separate links with different roles**:

| Entity | Subsystem | Role | Evidence |
|--------|-----------|------|----------|
| `act()` | Game Engine | `core` | Defined in game engine, owns message dispatch |
| `act()` | Combat System | `utility` | Called for combat messages |
| `act()` | Social & Communication | `utility` | Called for social/channel output |
| `affect_to_char()` | Affect System | `core` | Primary API for applying affects |
| `affect_to_char()` | Combat System | `supporting` | Combat applies affects (poison, stun) |
| `affect_to_char()` | Magic System | `supporting` | Spells apply affects |
| `damage()` | Combat System | `core` | Central damage resolution |
| `damage()` | Magic System | `supporting` | Spells invoke damage |

The `evidence` JSONB field records what motivated each link:
```json
{
  "doc_sections": ["combat_system/features"],
  "capabilities": ["combat"],
  "seed_entry_points": ["do_kill"],
  "matched_files": ["src/fight.cc"],
  "rationale": "damage() is the central damage application function, defined in fight.cc"
}
```

#### Step 5 — Flag gaps and ambiguities

The agent writes `curation_flags.jsonl` for cases requiring human review:
- Entities in "Key Source Areas" files that don't clearly belong to the subsystem
- Functions reachable from multiple subsystems where `core` vs. `supporting` is ambiguous
- Subsystems with very few `core` entities (likely a curation gap)
- The ~2,400 variable entities (harder to assign than functions)

### B.2 — What Will and Won't Get Linked

#### Will be linked (~2,000–4,000 links)

- **Functions explicitly named in docs** → `core` role, `curated` source, `high` confidence
- **Functions in "Key Source Areas" files** → `core` or `supporting`, `curated`, `high`/`medium`
- **Entry points** (`do_*`, `spell_*`, `spec_*`) → `entry_point` role for the subsystem they serve
- **Functions in matching capability groups** → `supporting` or `core`, `inferred`/`curated`, `medium`/`high`
- **Cross-system bridge functions** → `integration` or `utility` role in consuming subsystems
- **Key global variables** (e.g., `char_list`, `fight_table`, `affect_table`) → `core` to owning subsystem

#### Won't be linked (expected orphans)

- **Most variables** (~2,400 entities) — field-level variables and local struct members are too granular for subsystem assignment
- **Most defines/typedefs/enums** (~100 entities) — except a few key ones (`IS_NPC`, `WAIT_STATE`)
- **True utility functions** (string_ops, flags, numerics) → linked to Utilities as `core` only, *not* linked to every consuming subsystem as `utility` (would create noise)

The orphan entity report (FR-020) will flag these. This is expected and acceptable — not every entity needs a subsystem link.

### B.3 — Curation Artifact Output

| Artifact | Estimated Size | Content |
|----------|---------------|---------|
| `entity_subsystem_links.jsonl` | ~2,000–4,000 records | One record per entity↔subsystem link |
| `curation_flags.jsonl` | ~100–300 records | Unresolved cases for human review |

Each link record:
```json
{
  "entity_id": "fight_8cc_abc123...",
  "subsystem_id": "combat_system",
  "role": "core",
  "link_source": "curated",
  "confidence": "high",
  "notes": "Central damage resolution function, defined in fight.cc",
  "evidence": {
    "doc_sections": ["combat_system/features"],
    "capabilities": ["combat"],
    "seed_entry_points": ["do_kill"],
    "matched_files": ["src/fight.cc"],
    "rationale": "damage() is the central damage application function"
  }
}
```

---

## Summary: What Gets Inserted

| Table | Record Count | Source | Phase |
|-------|-------------|--------|-------|
| `subsystems` | ~29 (23 systems + 6 layer groups) | Mechanical from subsystems.md | A |
| `subsystem_docs` | ~200–250 sections | Mechanical from components/*.md | A |
| `subsystem_edges` | ~60–80 | Mechanical from dependency declarations | A |
| `entity_subsystem_links` | ~2,000–4,000 | Agent-curated using V1 tools | B |
| Embeddings on `subsystem_docs` | ~200–250 vectors | Generated at build time | A |

---

## Open Questions

1. **Group headings as parent subsystems**: Should the 6 `## Group` headings (Core Infrastructure, Entity Systems, etc.) become parent subsystem records, or remain as metadata tags? Making them parents gives a 2-level hierarchy; keeping them flat is simpler.

2. **Variable entity linking scope**: How aggressively should the curation agent attempt to link variable entities? Conservative (only key globals like `char_list`) vs. moderate (all global/static variables) vs. aggressive (including struct fields).

3. **Utility function fan-out**: Should `act()`, `send_to_char()`, etc. get `utility` links to every subsystem that calls them, or only to the top N consumers? Linking to all creates many low-value links; linking to none loses real architectural context.
