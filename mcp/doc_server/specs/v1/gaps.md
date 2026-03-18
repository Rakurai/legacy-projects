# Spec Gaps — Extracted from Historical DESIGN.md

> **Source:** `DESIGN.md` (initial design draft, pre-dates PRD/SPEC/MODEL).
> **Purpose:** Content not intentionally superseded by canonical docs.
> Decide per-section: real gap → integrate into canonical docs, or abandoned facet → delete.
>
> **Discrepancy warning:** Some details here conflict with the canonical docs.
> Conflicts are called out inline. Canonical docs are authoritative for V1.

---

## 1. Curated Side-Effect Marker Functions

MODEL.md §4 step 7 says *"compute … side_effect_markers"* and the schema defines the JSONB column, but neither MODEL.md nor any contract lists the actual functions. The build script needs this reference.

| Category | Functions |
|----------|-----------|
| Messaging | `act`, `send_to_char`, `printf_to_char`, `send_to_room` |
| Persistence | `save_char_obj`, `fwrite_char`, `do_save` |
| State mutation | `extract_char`, `char_from_room`, `char_to_room`, `obj_from_char`, `obj_to_char`, `obj_to_room` |
| Scheduling | `event_add`, various `WAIT_STATE` macros |
| Combat | `set_fighting`, `stop_fighting`, `damage`, `raw_kill` |

> **Discrepancy:** MODEL.md's schema comment lists 4 JSONB keys (`messaging`, `persistence`, `state_mutation`, `scheduling`). DESIGN.md adds a 5th category **combat**. Decide whether combat markers should be a separate category or folded into state_mutation.

---

## 2. Provenance Label Taxonomy

MODEL.md uses provenance as inline `Literal` types on Pydantic models but has no centralized reference. DESIGN.md §4.4 defines the full taxonomy:

### 2.1 Provenance Labels

| Label | Meaning |
|-------|---------|
| `graph_calls` | Direct from CALLS edges |
| `graph_uses` | Direct from USES edges |
| `graph_inherits` | Direct from INHERITS edges |
| `graph_transitive` | Multi-hop graph traversal (BFS) |
| `side_effect_marker` | Matched curated side-effect function list |
| `capability_map` | From capability group classification |
| `precomputed` | Computed at build time and stored |

### 2.2 Confidence Scale

Each derived result item also carries a `confidence` field:

| Level | Meaning |
|-------|---------|
| `direct` | Single-hop, exact |
| `heuristic` | Curated list match or shallow transitive |
| `transitive` | Multi-hop, approximate |

---

## 3. Design Decisions / Rationale (ADR candidates)

The canonical docs describe *what* but not *why*. These explain the reasoning behind key architectural choices.

### 3.1 PostgreSQL + pgvector (not in-memory)

Combining relational indexes, full-text search, and vector similarity in one system. The MCP server is a thin query + traversal layer using SQLModel table models with SQLAlchemy async sessions (asyncpg driver). No artifact files loaded at runtime. Rebuild by re-running the build script.

### 3.2 NetworkX for graph traversal

The in-memory graph is built from the `edges` table on startup (~25K rows → milliseconds to construct). NetworkX provides BFS, path-finding, centrality, and other graph algorithms we need for behavior slices and hotspot analysis. No reason to reimplement.

### 3.3 Embedding model as a runtime dependency

Semantic search requires a running embedding endpoint to encode queries. Connection details in `.env`. When unavailable, search switches to keyword-only mode and reports `search_mode: "keyword_fallback"` explicitly so agents don't overtrust results.

### 3.4 Side-effect markers via curated list

Rather than LLM-analyzing every function for side effects, we maintain a curated list of ~20-30 known side-effect functions (messaging, persistence, state mutation, scheduling). The build script checks each function's CALLS edges against this list. Low effort, high signal.

### 3.5 Capabilities ≠ subsystems

The `capability` column on entities represents a **typed semantic grouping** inferred from legacy code evidence. Each of the 30 capability groups is classified as one of: **domain** (reusable gameplay behavior like combat, magic, movement), **policy** (validation, permissions, state checks), **projection** (rendering, messaging, visible output), **infrastructure** (persistence, database, technical services), or **utility** (low-level helpers like string operations, flags, numerics). The groups were derived by analyzing the static call graph: entry points (do\_\*, spell\_\*, spec\_\*) are traced to transitive callees, which are classified against curated locked lists with embedding-similarity fallback.

The capability graph also carries typed dependency edges between groups (requires\_core, requires\_policy, uses\_utility, etc.) and wave ordering — these serve migration chunk planning but are also useful for understanding which functional concerns depend on which. **Note:** V1 tools do not expose wave ordering directly. The ordering exists in the source artifact (`capability_graph.json`) and is available for future specialized tooling, but surfacing it in V1 responses would blur the line between factual documentation and migration prescription.

Key differences from systems/subsystems:
- An entity may belong to one capability group but participate in multiple systems (e.g., `act()` is in the `output` capability but is used by nearly every system).
- A system like "Combat" spans multiple capability groups (combat, affects, attributes, output, persistence).
- True utility functions (string\_ops, flags, numerics) belong to a capability but have no meaningful system affiliation.
- Not all capabilities are domain-level — policy, projection, infrastructure, and utility groups exist at a different abstraction level than domain groups, and the `type` field distinguishes them.

### 3.6 No migration prescriptions

The server exposes factual and structural information only. No target surfaces, migration modes, implementation ordering, or architectural destination guesses. Those are the consuming agent's concerns.

---

## 4. Worked Examples (Tool Interactions)

The contracts define tool schemas but contain no worked request/response examples. These are useful as implementation reference and potential test fixtures.

### 4.1 Resolve + Fetch workflow

> **Note:** Entity IDs shown below use V1 Doxygen format (`compound_member`). These are **not stable** across Doxygen runs. ~~Design 005 replaces them with deterministic `{prefix}:{7 hex}` IDs.~~ **Implemented per spec 005**: entity IDs are now deterministic `{prefix}:{7hex}` format. The `resolve_entity` tool shown below is retired; `search` is the sole discovery path. `doc_quality` fields shown below are removed.

```
→ search(query="damage", kind="function")  <!-- spec 005: search replaces resolve_entity -->
← {
    search_mode: "hybrid",
    results: [
      { result_type: "entity", score: 1.0, entity_summary:
        { entity_id: "fn:a1b2c3d", signature: "void damage(Character *ch, Character *victim, int dam, int dt, int class_, bool show)",
          kind: "function", file_path: "src/fight.cc", capability: "combat",
          brief: "Apply damage from ch to victim..." } },
      { result_type: "entity", score: 1.0, entity_summary:
        { entity_id: "fn:e4f5g6h", signature: "void damage(Object *obj, int amount)",
          kind: "function", file_path: "src/act_wiz.cc", capability: null,
          brief: "Apply damage to an object..." } },
    ]
  }

→ get_entity(entity_id="fn:a1b2c3d", include_neighbors=true)  <!-- spec 005: entity_id only -->
← { full entity detail + neighbor list as EntitySummary objects }
```

### 4.2 Behavior slice for an entry point

```
→ get_behavior_slice(entity_id="fn:x1y2z3w", max_depth=5, max_cone_size=200)  <!-- spec 005: entity_id only; resolution fields removed -->
← {
    truncated: false,
    confidence: "high",
    entry_point: { signature: "void do_kill(Character *ch, String argument)", ... },  <!-- spec 005: doc_quality removed from entry_point -->
    direct_callees: [
      { signature: "void multi_hit(...)", capability: "combat", provenance: "graph" },
      { signature: "void send_to_char(...)", capability: "output", provenance: "graph" }
    ],
    transitive_call_cone: [
      { signature: "void one_hit(...)", depth: 2, capability: "combat", provenance: "graph" },
      { signature: "void damage(...)", depth: 3, capability: "combat", provenance: "graph" },
      ...
    ],
    capabilities_touched: {
      "combat": { direct: 2, transitive: 10 },
      "affects": { direct: 0, transitive: 3 },
      "attributes": { direct: 1, transitive: 7 },
      "visibility_rules": { direct: 0, transitive: 2 }
    },
    globals_used: {
      direct: ["char_list"],
      transitive: ["fight_table", "affect_table", ...]
    },
    side_effect_markers: {
      messaging: [
        { entity: "act", direct: true },
        { entity: "send_to_char", direct: true }
      ],
      state_mutation: [
        { entity: "set_fighting", direct: false },
        { entity: "char_from_room", direct: false }
      ],
      persistence: []
    }
  }
```

### 4.3 Semantic search

```
→ search(query="poison spreading between characters", top_k=5)  <!-- spec 005: search replaces resolve for discovery -->
← [
    { signature: "void plague_spread(Character *ch)", score: 0.89,
      search_mode: "hybrid", provenance: "precomputed", ... },  <!-- spec 005: doc_quality removed; provenance updated -->
    { signature: "void spell_plague(int sn, int level, Character *ch, void *vo, int target)",
      score: 0.82, provenance: "precomputed", ... },
    ...
  ]
```

### 4.4 File summary

```
→ get_file_summary(file_path="src/fight.cc")
← {
    file_path: "src/fight.cc",
    entity_count: { function: 42, variable: 8, total: 50 },
    capabilities: { "combat": 38, "affects": 4, "attributes": 6 },
    <!-- spec 005: doc_quality_distribution removed from file summary -->
    key_entities: [
      { signature: "void damage(...)", fan_in: 47, kind: "function", brief: "..." },
      { signature: "void multi_hit(...)", fan_in: 12, kind: "function", brief: "..." }
    ],
    includes: ["src/include/merc.hh", "src/include/fight.hh"],
    included_by: ["src/act_move.cc", "src/magic.cc"]
  }
```

---

## 5. V2 — Hierarchical System Documentation

> **Note:** This entire section is an early V2 design from before formal V2 planning began.
> Compare against current V2 planning docs to decide what's still relevant.
>
> **Known discrepancy:** §5.2 uses `VECTOR(4096)` — should be configurable `VECTOR(N)` per spec 004.

### 5.1 Motivation

V1 is function-forward: every tool resolves, describes, and traverses individual code entities. V2 adds a **system-level narrative layer** drawn from the project's existing architectural documentation (`docs/components/*.md`, `docs/subsystems.md`) — 23 subsystem documents totaling ~4,500 lines of curated prose covering features, responsibilities, component breakdowns, implementation details, key files, system behaviors, and inter-system dependencies.

This prose captures knowledge that per-entity documentation cannot compose on its own: *"the combat system resolves attacks in a per-round cycle: hit check → damage calc → defensive rolls → elemental cascading → death processing with corpse creation"* is a system-level narrative, not something derivable from the brief of `damage()` or `raw_kill()`.

### 5.2 Why not in V1

The mapping between entities and systems is not mechanical:

- **Many-to-many relationships.** An entity like `act()` belongs to the `output` capability but participates in virtually every system. `affect_to_char()` is in the `affects` capability but is called by combat, magic, object effects, and MobProgs. Hardcoding a single `subsystem` foreign key would be lossy.
- **Capabilities ≠ systems.** The existing `capability` column groups entities by typed semantic responsibility (what they enable), not by architectural role (what system they serve). These are complementary but distinct taxonomies — a system like "Combat" spans capabilities (combat, affects, attributes, output, persistence), and a capability like `string_ops` is a utility used across all systems.
- **Curation needed.** Mechanically parsing section headings and keyword-matching entities to systems will produce noisy, overconfident mappings. The right approach is agent-assisted curation: walk the documents, use the doc server to research cross-references, and make intelligent decisions about where to split, merge, and connect.

V1's schema and tools are designed so that V2 can be added without reworking the entity-level services.

### 5.3 Schema additions

```sql
-- System/subsystem hierarchy
CREATE TABLE subsystems (
    id              TEXT PRIMARY KEY,       -- 'combat_system', 'affect_system', ...
    name            TEXT NOT NULL,          -- 'Combat System'
    parent_id       TEXT REFERENCES subsystems(id),  -- nullable; allows nesting
    description     TEXT,                   -- overview paragraph
    source_file     TEXT,                   -- 'components/combat_system.md'
    depends_on      JSONB,                  -- ['character_data_model', 'affect_system', ...]
    depended_on_by  JSONB                   -- ['quest_system', 'pvp', ...]
);

-- Subsystem documentation sections (chunked for search)
CREATE TABLE subsystem_docs (
    id              SERIAL PRIMARY KEY,
    subsystem_id    TEXT NOT NULL REFERENCES subsystems(id),
    section_path    TEXT NOT NULL,          -- 'Core Components > Attack Resolution'
    heading         TEXT NOT NULL,
    section_kind    TEXT NOT NULL,          -- closed enum: overview, responsibilities, key_components,
                                           --   implementation, dependencies, behaviors, future
                                           -- mechanically classified from heading text at build time
    is_overview     BOOLEAN DEFAULT FALSE,  -- true for the canonical overview section per subsystem
    body            TEXT NOT NULL,          -- markdown content of this section
    source_file     TEXT NOT NULL,
    line_range      INT4RANGE,
    embedding       VECTOR(4096),           -- ⚠ should be VECTOR(N), configurable per spec 004
    search_vector   TSVECTOR
);

-- Many-to-many: entity ↔ subsystem (curated, not mechanical)
CREATE TABLE entity_subsystem_links (
    entity_id       TEXT NOT NULL REFERENCES entities(entity_id),
    subsystem_id    TEXT NOT NULL REFERENCES subsystems(id),
    role            TEXT NOT NULL,          -- closed enum: core, entry_point, supporting, utility, integration
    link_source     TEXT NOT NULL DEFAULT 'curated',  -- curated (agent-verified), inferred (heuristic), imported (bulk)
    confidence      TEXT NOT NULL DEFAULT 'high',     -- high, medium, low
    notes           TEXT,                   -- short rationale for this link
    evidence        JSONB,                  -- structured provenance: {doc_sections: [...], capabilities: [...],
                                           --   seed_entry_points: [...], matched_files: [...], rationale: "..."}
    PRIMARY KEY (entity_id, subsystem_id)
);

-- System-level dependency graph (parsed from subsystems.md)
CREATE TABLE subsystem_edges (
    source_id       TEXT NOT NULL REFERENCES subsystems(id),
    target_id       TEXT NOT NULL REFERENCES subsystems(id),
    relationship    TEXT NOT NULL,          -- 'depends_on', 'bidirectional'
    PRIMARY KEY (source_id, target_id)
);
```

#### Design choices

- **`entity_subsystem_links` is many-to-many** — `damage()` can be `core` to Combat and `supporting` to Magic. `act()` can be `utility` to everything that uses output formatting.
- **`role` is a closed enum** (`core`, `entry_point`, `supporting`, `utility`, `integration`) — free-text roles drift fast; a small controlled vocabulary keeps the curation consistent.
- **`link_source` and `confidence` are separate fields** — `link_source` records provenance (where the link came from), `confidence` records trust level. These are orthogonal: a curated link can be `medium` confidence if the agent was uncertain.
- **`evidence` JSONB** provides traceable provenance per link — which doc sections, capabilities, entry points, or source files motivated the link.
- **`section_kind`** is a closed enum mechanically classified from heading text — enables retrieval strategies like "give me the overview first, then implementation details."
- **`is_overview` flag** identifies the canonical overview section per subsystem — `get_subsystem` always leads with this section, preventing chunk-soup results.
- **Nesting via `parent_id`** — "Dynamic Loot Generation" can be a child of "Object System" if the curation agent decides that's the right split.

### 5.4 V2 tools

| Tool | Description |
|------|-------------|
| `search` (enhanced) | Unified search across entity docs AND subsystem docs. `source` parameter filters to `entity`, `subsystem_doc`, or `all`. |
| `get_subsystem` | Full subsystem detail: overview section first (via `is_overview`), then other sections ordered by `section_kind` priority, curated entity links, dependency edges. |
| `list_subsystems` | All subsystems with hierarchy, entity counts, and doc quality distribution. |
| `get_subsystem_context` | Given an entity, return a `ContextBundle`: the entity's subsystem(s), relevant doc sections, capability framing, and related entities. |
| `get_subsystem_dependencies` | System-level dependency graph for a given subsystem. |
| `search_subsystem_docs` | Semantic + keyword search scoped to subsystem prose. |

#### Retrieval strategy for `get_subsystem_context`

Rerank rather than dump all linked sections:

1. Subsystem overview section (`is_overview = true`)
2. Sections whose text mentions the entity or directly related functions
3. Sections whose `section_kind` aligns with the entity's capability or file context
4. Dependency sections only after the above

Each returned section includes an `inclusion_reason` field:
- `overview_section` — canonical overview for the subsystem
- `mentions_entity` — section body references the entity name or a close neighbor
- `same_capability` — section content aligns with the entity's capability group
- `linked_subsystem` — entity is linked to this subsystem (general membership)
- `matches_behavior_terms` — section matches behavioral query terms

#### Design principle

V1 tools answer *"what is this code object?"* — V2 context tools answer *"what larger system narrative helps interpret it?"* These remain separate tool families; `get_subsystem_context` is additive, not a replacement for `get_entity`.

### 5.5 V2 build process

Two distinct stages: **mechanical ingestion** and **agent-assisted curation**. The curation agent does not write directly to the database — it produces **versioned intermediate artifacts** that a build script ingests.

#### 5.5.1 Curation artifacts

Stored in `artifacts/v2/`:

| Artifact | Format | Description |
|----------|--------|-------------|
| `subsystems_seed.json` | JSON array | Subsystem records: id, name, parent_id, description, source_file, depends_on, depended_on_by |
| `subsystem_doc_chunks.jsonl` | JSONL | One record per doc section: subsystem_id, section_path, heading, section_kind, is_overview, body, source_file, line_range |
| `entity_subsystem_links.jsonl` | JSONL | One record per link: entity_id, subsystem_id, role, link_source, confidence, notes, evidence |
| `subsystem_edges.json` | JSON array | Parsed dependency edges: source_id, target_id, relationship |
| `curation_flags.jsonl` | JSONL | Unresolved cases, gaps, and review flags from the curation agent |

Why intermediate files rather than direct DB writes:
- **Reviewable** — diffs show exactly what the curation agent changed
- **Re-ingestable** — `build_v2_db.py` can re-import without rerunning the curation agent
- **Human-correctable** — errors can be fixed in the JSONL and re-ingested
- **Validatable** — lint rules can run before DB load
- **Versionable** — git-tracked curation state with clear history

#### 5.5.2 Build pipeline

1. **Seed subsystems** (mechanical) — parse `subsystems.md` for the 23 named systems → `subsystems_seed.json`
2. **Chunk component docs** (mechanical) — split each `components/*.md` by `##`/`###` headings, classify `section_kind` from heading text, mark `is_overview` → `subsystem_doc_chunks.jsonl`
3. **Parse dependency declarations** (mechanical) — extract "Depends on" / "Depended on by" from `subsystems.md` → `subsystem_edges.json`
4. **Curate entity↔subsystem links** (agent-assisted) — the curation agent uses V1 tools (search, behavior slices, capability detail) to walk each subsystem, identify participating entities, assign roles and confidence, record evidence → `entity_subsystem_links.jsonl` + `curation_flags.jsonl`
5. **Validate** — run lint rules against the artifacts
6. **Ingest** — `build_v2_db.py` reads all artifacts, embeds doc chunks, populates Postgres tables

#### 5.5.3 Validation rules

- Every subsystem has at least one `is_overview` doc chunk
- Every `entity_id` in links references an existing entity in the V1 `entities` table
- Every `subsystem_id` in links and docs references a subsystem in `subsystems_seed.json`
- `entry_point` role links target only `kind = 'function'` entities
- `utility` role is used sparingly (warn if >30% of a subsystem's links are utility)
- Orphan entities report: entities with no subsystem link (informational, not blocking)
- Orphan subsystems report: subsystems with no entity links (likely a curation gap)

### 5.6 V1 forward-compatibility

V1 is structured so V2 requires **no changes to existing tables or tools**:

- The `entities` table has no `subsystem` column — entity↔subsystem is a separate join table.
- The `capability` column stays as-is; it and `subsystem_id` are independent classification axes.
- V1 tools continue to work unchanged. V2 tools are additive.
- The `search` tool's `SearchResult` envelope is designed for V2: `result_type` discriminates entity vs. subsystem results, so V2 unified search extends the shape without breaking it.
- The `EntitySummary` shape gains an optional `subsystems` field (list of `{id, name, role}`) populated from the join table when `include_subsystems=true` is passed. In V1 this parameter does not exist and the field is absent.
- V2 response shapes (`SubsystemSummary`, `SubsystemDocSummary`, `ContextBundle`) are pre-defined in MODEL.md §3.7 to prevent one-off blob shapes.

---

## 6. Future Extensions

Ideas mentioned in DESIGN.md but not captured elsewhere.

- **Source-span cross-references** — attach call edges to exact source line ranges (using `codeline_refs` data from file compounds), enabling "damage() calls raw\_kill() at line 342 in the death-handling branch" rather than just "damage calls raw\_kill."
- **Guard/policy extraction** — mine common condition patterns (safe room checks, trust gates, NPC/player restrictions) from source and link them to entities.
- **Message template catalog** — parse `act()` format strings and `send_to_char` calls into structured message inventories.
- **Diff-aware impact analysis** — given a set of changed files, find all affected entities and their downstream dependents via the graph.
- **Incremental rebuild** — detect changed artifacts and update only affected database rows instead of full rebuild.

---

## 7. doc_quality Derivation Rules

<!-- spec 005: doc_quality and doc_state columns removed from schema. This section is historical only.
     Quality assessment belongs to artifact creation, not server/agent interaction.
     Agents use `brief is not null` as the practical quality signal. -->

~~MODEL.md says `doc_quality` is derived but doesn't specify the exact logic. DESIGN.md §7.2 gives the rules:~~

- **high** — `doc_state` is `refined_summary` or `refined_usage` AND `details` is non-empty AND `params` coverage exists (for functions)
- **medium** — `doc_state` is `generated_summary` or `refined_*` but missing details/params
- **low** — `doc_state` is `extracted_summary` (no LLM-generated docs) OR brief is empty
