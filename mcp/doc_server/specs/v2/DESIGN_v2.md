# MCP Documentation Server — V2 Design: System-Level Documentation

This document specifies V2 of the MCP documentation server. It builds on the
implemented V1 design ([DESIGN.md](design.md)) and incorporates the taxonomy
decisions documented in [v2_indexing.md](v2_indexing.md).

**V1 is locked.** This document describes only V2 additions. V1 tables, tools,
and response shapes are unchanged. V2 is purely additive.

---

## 1. Overview

V1 is entity-forward: every tool resolves, describes, and traverses individual code
entities (functions, classes, variables). V2 adds a **system-level narrative layer**:
curated prose describing how larger game systems work, chunked for semantic search,
and linked to code entities via a many-to-many join table.

V1 answers: *"What is this code object?"*
V2 answers: *"What larger system narrative helps interpret it?"*

These are separate tool families. V2 is additive, not a replacement.

### 1.1 What V2 provides

- **19 systems** + **3 support entries** organized in a shallow hierarchy with typed
  cross-references (see v2_indexing.md §5.6 for the full list)
- **Curated narrative documentation** chunked for semantic search, with grounding
  status and chunk-to-code evidence
- **Many-to-many entity↔system links** with role, provenance, and confidence
- **System-level dependency graph** enabling cross-system navigation
- **Unified search** across entity docs (V1) and system narrative docs (V2)

### 1.2 What V2 does NOT provide

Same principle as V1: no migration prescriptions, no architectural destination guesses,
no implementation ordering. Factual and structural information only.

---

## 2. Schema

All V2 tables are new. No V1 tables are modified.

### 2.1 `subsystems` Table

```sql
CREATE TABLE subsystems (
    id              TEXT PRIMARY KEY,       -- 'combat', 'affect_system', 'utilities', ...
    name            TEXT NOT NULL,          -- 'Combat', 'Affect System', 'Utilities'
    parent_id       TEXT REFERENCES subsystems(id),  -- nullable; features nest under systems
    kind            TEXT NOT NULL,          -- closed enum: 'system', 'feature', 'support'
                                           -- reserved: 'aspect' (for future cross-cutting pattern docs)
    layer           TEXT,                   -- closed enum: 'infrastructure', 'data_model',
                                           --   'game_mechanic', 'content_system',
                                           --   'player_feature', 'operations'
    description     TEXT,                   -- overview paragraph
    source_file     TEXT,                   -- 'components/combat.md'
    depends_on      JSONB,                  -- ['character_data', 'affect_system', ...]
    depended_on_by  JSONB                   -- ['quests', 'clans_pvp', ...]
);

-- Indexes
CREATE INDEX idx_subsystems_parent ON subsystems (parent_id);
CREATE INDEX idx_subsystems_kind ON subsystems (kind);
CREATE INDEX idx_subsystems_layer ON subsystems (layer);
```

#### `kind` enum

| Value | Meaning | Qualification criteria |
|-------|---------|----------------------|
| `system` | Top-level, independently navigable | Has stable identity, own behavioral narrative, meaningful peer edges, is a navigation destination, can own nontrivial overview + sections |
| `feature` | Child of a system | Substantial enough for its own doc section (~200-500 words), but scoped within a parent system's narrative |
| `support` | Reference documentation | Real topic, but lacks independent behavioral narrative — helper/utility catalog |
| `aspect` | *(Reserved)* | Cross-cutting pattern docs. Not used in initial V2; reserved for future expansion. |

#### `layer` enum

| Value | Definition | Boundary rule |
|-------|-----------|---------------|
| `infrastructure` | Technical plumbing with no game semantics | Code that could exist in any server application, not specific to a MUD |
| `data_model` | Core entity structures and their accessors | Defines *what things are*, not *what they do* |
| `game_mechanic` | Rules and behaviors that define gameplay | Implements game rules — removing it changes how the game plays |
| `content_system` | Systems primarily about authored game content or content authoring/runtime interpretation | Primary purpose is managing authored artifacts (scripts, help entries, notes) and their runtime interpretation |
| `player_feature` | Systems primarily about player-facing interaction loops and gameplay services | Primary purpose is a player-facing interaction loop or gameplay service (questing, trading, chatting) |
| `operations` | Admin/builder tools, persistence, operational infrastructure | Serves operators/builders, not players directly |

When a system straddles `content_system` / `player_feature`, pick the dominant purpose
and express the secondary concern via `subsystem_edges`.

### 2.2 `subsystem_docs` Table

```sql
CREATE TABLE subsystem_docs (
    id              SERIAL PRIMARY KEY,
    subsystem_id    TEXT NOT NULL REFERENCES subsystems(id),
    section_path    TEXT NOT NULL,          -- 'Core Components > Attack Resolution'
    heading         TEXT NOT NULL,
    section_kind    TEXT NOT NULL,          -- closed enum: overview, responsibilities,
                                           --   key_components, implementation,
                                           --   dependencies, behaviors, future
    is_overview     BOOLEAN DEFAULT FALSE,  -- true for the canonical overview section
    narrative_role  TEXT,                   -- derived at build time from section_kind +
                                           --   heading heuristics: overview, mechanism,
                                           --   dependency, edge_case, admin, history
    grounding_status TEXT NOT NULL DEFAULT 'mixed',
                                           -- closed enum: grounded, mixed, weak, rejected
    body            TEXT NOT NULL,          -- markdown content of this section
    evidence        JSONB,                  -- chunk-to-code provenance:
                                           --   {entity_ids: [...], capabilities: [...],
                                           --    files: [...], confidence_note: "..."}
    source_file     TEXT NOT NULL,
    line_range      INT4RANGE,
    embedding       VECTOR(4096),
    search_vector   TSVECTOR
);

-- Indexes
CREATE INDEX idx_subdocs_subsystem ON subsystem_docs (subsystem_id);
CREATE INDEX idx_subdocs_kind ON subsystem_docs (section_kind);
CREATE INDEX idx_subdocs_grounding ON subsystem_docs (grounding_status);
CREATE INDEX idx_subdocs_overview ON subsystem_docs (is_overview) WHERE is_overview;
CREATE INDEX idx_subdocs_search ON subsystem_docs USING GIN (search_vector);
CREATE INDEX idx_subdocs_embedding ON subsystem_docs
    USING ivfflat (embedding vector_cosine_ops) WITH (lists = 20);
```

#### `grounding_status` enum

| Value | Meaning | Retrieval effect |
|-------|---------|-----------------|
| `grounded` | Content verified against actual codebase — describes what the code does | Preferred in retrieval; full trust |
| `mixed` | Mostly accurate but contains some unverified claims | Default; moderate trust |
| `weak` | Contains significant speculation or inflation beyond code reality | Downranked in retrieval; trust warning to agent |
| `rejected` | Determined to be hallucinated or factually wrong; retained for audit | Excluded from retrieval by default |

#### `narrative_role` derivation

Derived at build time from `section_kind` + heading text heuristics:

| Role | Derived from | Purpose |
|------|-------------|---------|
| `overview` | `section_kind = 'overview'` or `is_overview = true` | System identity and high-level description |
| `mechanism` | `section_kind IN ('key_components', 'implementation', 'behaviors')` | How the system works — the narrative arc |
| `dependency` | `section_kind = 'dependencies'` | What this system depends on and what depends on it |
| `edge_case` | Heading contains "special", "edge", "exception", "limitation" | Non-obvious behaviors and constraints |
| `admin` | Heading contains "admin", "builder", "wizard", "immortal" | Operator-facing functionality |
| `history` | Heading contains "history", "legacy", "deprecated", "migration" | Archaeological context |

Agents use `narrative_role` for reading order: overview → mechanism → dependency →
edge_case, rather than receiving a flat bag of chunks.

#### `evidence` JSONB format

```json
{
    "entity_ids": ["fight_8cc_abc123", "fight_8cc_def456"],
    "capabilities": ["combat", "affects"],
    "files": ["src/fight.cc", "src/effects.cc"],
    "confidence_note": "Verified against fight.cc damage() call chain"
}
```

Populated during curation. Enables precise reranking in `get_subsystem_context` —
instead of relying solely on text mentions and embeddings, the evidence payload
provides structured entity↔chunk links.

### 2.3 `entity_subsystem_links` Table

Unchanged from DESIGN.md §18.2:

```sql
CREATE TABLE entity_subsystem_links (
    entity_id       TEXT NOT NULL REFERENCES entities(entity_id),
    subsystem_id    TEXT NOT NULL REFERENCES subsystems(id),
    role            TEXT NOT NULL,          -- closed enum: core, entry_point, supporting,
                                           --   utility, integration
    link_source     TEXT NOT NULL DEFAULT 'curated',
                                           -- curated, inferred, imported
    confidence      TEXT NOT NULL DEFAULT 'high',
                                           -- high, medium, low
    notes           TEXT,
    evidence        JSONB,                  -- {doc_sections, capabilities, seed_entry_points,
                                           --   matched_files, rationale}
    PRIMARY KEY (entity_id, subsystem_id)
);

CREATE INDEX idx_esl_subsystem ON entity_subsystem_links (subsystem_id);
CREATE INDEX idx_esl_role ON entity_subsystem_links (role);
```

### 2.4 `subsystem_edges` Table

Unchanged from DESIGN.md §18.2:

```sql
CREATE TABLE subsystem_edges (
    source_id       TEXT NOT NULL REFERENCES subsystems(id),
    target_id       TEXT NOT NULL REFERENCES subsystems(id),
    relationship    TEXT NOT NULL,          -- 'depends_on', 'bidirectional'
    PRIMARY KEY (source_id, target_id)
);
```

---

## 3. Response Shapes

V2 extends the V1 response vocabulary with the shapes pre-declared in DESIGN.md §4.6,
plus refinements from team review.

### 3.1 `SubsystemSummary` (updated)

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Subsystem identifier |
| `name` | string | Human-readable name |
| `parent_id` | string? | Parent subsystem |
| `kind` | string | `system`, `feature`, or `support` |
| `layer` | string? | `infrastructure`, `data_model`, `game_mechanic`, `content_system`, `player_feature`, `operations` |
| `description` | string | Overview paragraph |
| `source_file` | string | Source markdown file |
| `entity_count` | int | Linked entities |
| `doc_section_count` | int | Chunked documentation sections |
| `grounded_section_count` | int | Sections with `grounding_status = 'grounded'` |
| `depends_on_count` | int | Upstream dependencies |
| `depended_on_by_count` | int | Downstream dependents |

### 3.2 `SubsystemDocSummary` (updated)

| Field | Type | Description |
|-------|------|-------------|
| `id` | int | Section identifier |
| `subsystem_id` | string | Owning subsystem |
| `subsystem_name` | string | Owning subsystem name |
| `section_path` | string | Hierarchical path: `Core Components > Attack Resolution` |
| `heading` | string | Section heading |
| `section_kind` | string | `overview`, `responsibilities`, `key_components`, `implementation`, `dependencies`, `behaviors`, `future` |
| `narrative_role` | string? | Derived: `overview`, `mechanism`, `dependency`, `edge_case`, `admin`, `history` |
| `grounding_status` | string | `grounded`, `mixed`, `weak`, `rejected` |
| `source_file` | string | Source markdown file |
| `line_range` | range? | Line range in source |
| `excerpt` | string | First ~200 chars of body text |
| `evidence` | object? | `{entity_ids, capabilities, files}` — only when requested |

### 3.3 `ContextBundle` (updated)

| Field | Type | Description |
|-------|------|-------------|
| `focus_type` | string | `entity`, `subsystem`, `capability`, or `entry_point` |
| `focus` | object | The primary object |
| `related_entities` | EntitySummary[] | Relevant code entities |
| `related_capabilities` | object[] | Relevant capability groups |
| `related_subsystems` | SubsystemSummary[] | Relevant subsystems |
| `relevant_doc_sections` | object[] | Doc sections with `inclusion_reason` and `narrative_role` |
| `confidence_notes` | string? | Overall confidence including grounding assessment |
| `truncated` | bool | Whether any component was truncated |

### 3.4 `EntitySummary` extension

V1's `EntitySummary` gains an optional field when `include_subsystems=true`:

| Field | Type | Description |
|-------|------|-------------|
| `subsystems` | object[]? | `[{id, name, kind, role}]` from the join table. Absent in V1. |

---

## 4. Tools

### 4.1 Enhanced V1 tools

#### `search` (enhanced)

Existing V1 tool with additional parameter and result types:

| New Parameter | Type | Description |
|---------------|------|-------------|
| `source` | string? | `entity` (default, V1 behavior), `subsystem_doc`, or `all` |
| `min_grounding` | string? | Filter subsystem doc results: `grounded`, `mixed` (default: no filter) |

When `source` is `subsystem_doc` or `all`, results include `SubsystemDocSummary`
entries in the `SearchResult` envelope (DESIGN.md §4.5) with `result_type:
"subsystem_doc"`. V1 callers passing no `source` parameter get unchanged behavior.

Grounding-aware ranking: when subsystem doc results are included, `grounded` chunks
receive a ranking boost over `mixed`, and `weak` chunks are penalized. `rejected`
chunks are excluded by default.

#### `list_file_entities` / `get_entity` (enhanced)

When `include_subsystems=true` is passed, the `EntitySummary` or full entity response
includes the `subsystems` field — list of `{id, name, kind, role}` from the join table.

### 4.2 New V2 tools

#### `list_subsystems`

List all subsystems with hierarchy and summary metrics.

| Parameter | Type | Description |
|-----------|------|-------------|
| `kind` | string? | Filter: `system`, `feature`, `support` (default: all) |
| `layer` | string? | Filter to layer |
| `parent_id` | string? | Filter to children of a specific system |

**Returns:** `SubsystemSummary[]` with truncation metadata.

#### `get_subsystem`

Full subsystem detail with overview-first section ordering.

| Parameter | Type | Description |
|-----------|------|-------------|
| `subsystem_id` | string | Subsystem identifier |
| `include_sections` | bool | Include doc sections (default: true) |
| `include_entities` | bool | Include linked entities (default: false) |
| `include_dependencies` | bool | Include dependency edges (default: true) |
| `min_grounding` | string? | Filter sections: `grounded`, `mixed` (default: include all non-rejected) |

**Returns:** `SubsystemSummary` + sections ordered by `narrative_role` priority
(overview → mechanism → dependency → edge_case → admin → history), each as
`SubsystemDocSummary` with full body text. Optionally includes linked entities
as `EntitySummary[]` with role and confidence, and dependency edges.

`rejected` sections are excluded by default. `weak` sections are included but
flagged with their `grounding_status` so agents can decide whether to trust them.

#### `get_subsystem_context`

Given an entity, assemble relevant system narrative context.

| Parameter | Type | Description |
|-----------|------|-------------|
| `entity` | string | Entity ID, name, or signature |
| `max_sections` | int | Max doc sections to return (default: 10) |
| `min_grounding` | string? | Filter: `grounded`, `mixed` (default: no filter) |

**Returns:** Resolution envelope + `ContextBundle` (§3.3).

**Retrieval strategy** (reranking, not dumping):

1. Subsystem overview section (`is_overview = true`) for each linked subsystem
2. Sections whose `evidence.entity_ids` include the target entity or direct neighbors
3. Sections whose text mentions the entity name or close neighbor names
4. Sections whose capability alignment matches the entity's capability
5. Dependency sections only after the above

Each returned section includes:
- `inclusion_reason`: `overview_section`, `evidence_match`, `mentions_entity`,
  `same_capability`, `linked_subsystem`, `matches_behavior_terms`
- `narrative_role`: for reading order
- `grounding_status`: for trust assessment

This tool is the primary V2 context tool. It does **not** replace `get_entity` — it
is additive. An agent investigating code calls `get_entity` for the code-level view,
then `get_subsystem_context` for the narrative view.

#### `get_subsystem_dependencies`

System-level dependency graph navigation.

| Parameter | Type | Description |
|-----------|------|-------------|
| `subsystem_id` | string | Subsystem identifier |
| `direction` | string | `upstream`, `downstream`, or `both` (default: `both`) |
| `depth` | int | Traversal depth (default: 1, max: 3) |

**Returns:** Dependency tree with `SubsystemSummary` at each node,
relationship types, and truncation metadata.

#### `search_subsystem_docs`

Semantic + keyword search scoped to subsystem narrative prose.

| Parameter | Type | Description |
|-----------|------|-------------|
| `query` | string | Natural language search query |
| `top_k` | int | Number of results (default: 10) |
| `subsystem_id` | string? | Scope to a specific subsystem |
| `section_kind` | string? | Filter by section kind |
| `min_grounding` | string? | Filter: `grounded`, `mixed` (default: no filter) |

**Returns:** Ranked list of `SubsystemDocSummary` with scores, search mode,
and grounding status. Uses same hybrid search infrastructure as V1 `search`
(pgvector + full-text + name boost), applied to `subsystem_docs` table.

---

## 5. Build Pipeline

V2 build extends V1. The V1 build (`build_mcp_db.py`) is unchanged and runs first.
V2 build (`build_v2_db.py`) populates the new tables.

### 5.1 Pipeline stages

```
Stage 0: Documentation rewrite (manual)
  ├─ Rewrite docs/components/*.md per system list and format spec (§5.2)
  ├─ One file per system, structured headings, inline metadata tags
  ├─ All classification encoded in the document itself
  └─ Output: chunking-ready markdown files

Stage 1: Chunk production (mechanical — string split + regex only)
  ├─ Split each file on ## headings
  ├─ Extract inline tags via regex
  ├─ Read YAML frontmatter for system-level metadata
  ├─ Record line ranges
  └─ Output: chunk_candidates.jsonl

Stage 2: Curation (agent-assisted)
  ├─ Assess grounding_status per chunk (using V1 tools)
  ├─ Attach evidence (entity_ids, capabilities, files)
  ├─ Curate entity↔subsystem links
  ├─ Flag unresolved issues
  └─ Output: curation artifacts (§5.4)

Stage 3: Validation (automated)
  ├─ Run lint rules (§5.6)
  └─ Output: validation report + curation_flags.jsonl

Stage 4: Ingestion (build_v2_db.py)
  ├─ Read validated curation artifacts
  ├─ Embed doc chunks (via embedding endpoint)
  ├─ Generate tsvector columns
  └─ Populate Postgres tables
```

**Key workflow principle:** All classification intelligence lives in the manually
written documents (Stage 0), not in the parser (Stage 1). Stage 1 is trivial code —
split on headings, extract tags with regex, read frontmatter. No NLP, no heuristic
heading classification, no ambiguity.

### 5.2 Document format specification

Each system gets one markdown file in `docs/components/`. The file structure
encodes all metadata needed for mechanical chunking.

#### File-level: YAML frontmatter

```yaml
---
id: combat
name: Combat
kind: system
layer: game_mechanic
parent: null
depends_on: [character_data, affect_system, object_system]
depended_on_by: [quests, clans_pvp, mobprog_npc_ai]
---
```

The frontmatter is the single source of truth for the `subsystems` table row.
Stage 1 parses it with a YAML library (not regex). Fields map 1:1 to table columns.

For features with a parent:
```yaml
---
id: loot_generation
name: Loot Generation
kind: feature
layer: game_mechanic
parent: object_system
---
```

For support entries:
```yaml
---
id: utilities
name: Utilities
kind: support
layer: infrastructure
---
```

#### Section-level: tagged headings

Each `##` heading starts a chunk. Metadata is encoded in an HTML comment tag
immediately after the heading:

```markdown
## Overview
<!-- section: overview | grounding: grounded -->

The combat system resolves attacks in a per-round cycle driven by
`violence_update()`. Each fighting character gets a `multi_hit()` call
that processes primary attacks, secondary attacks, and dual-wield...

## Attack Resolution
<!-- section: key_components | grounding: grounded | role: mechanism -->

Per-round hit calculation considering weapon skill, dexterity, level
difference, and situational modifiers...

## Death & Corpse Processing
<!-- section: key_components | grounding: mixed | role: edge_case -->

When damage reduces a character below 0 HP, `raw_kill()` handles...

## Dependencies
<!-- section: dependencies | grounding: grounded | role: dependency -->

- **Affect System**: sanctuary halving, poison DOT, stat modifiers
- **Object System**: weapon damage dice, armor AC, elemental degradation
- **Character Data**: attributes, HP, position, fighting state
```

#### Tag format

The HTML comment tag uses a simple `key: value` format with `|` separators:

```
<!-- section: <section_kind> | grounding: <grounding_status> | role: <narrative_role> -->
```

| Tag | Required | Values | Maps to column |
|-----|----------|--------|----------------|
| `section` | yes | `overview`, `responsibilities`, `key_components`, `implementation`, `dependencies`, `behaviors`, `future` | `section_kind` |
| `grounding` | yes | `grounded`, `mixed`, `weak` | `grounding_status` |
| `role` | no | `overview`, `mechanism`, `dependency`, `edge_case`, `admin`, `history` | `narrative_role` |

Rules:
- If `role` is omitted, Stage 1 derives it from `section` using the mapping in §2.2.
- `is_overview` is set to `true` when `section: overview`.
- `section_path` is built from the heading hierarchy: `## Foo` under a file named
  `combat.md` becomes `Combat > Foo`.

#### `###` sub-headings

Sub-headings (`###`) within a `##` section are **not** separate chunks. They're part
of the parent `##` chunk's body. This keeps chunk boundaries simple (split on `##`
only) while allowing internal structure.

```markdown
## Attack Resolution
<!-- section: key_components | grounding: grounded | role: mechanism -->

### Hit Calculation
Per-round hit check considering weapon skill, dexterity...

### Damage Calculation
Base weapon damage modified by damroll, skill proficiency...

### Defensive Rolls
Dodge, parry, and shield block with skill-based chances...
```

This produces one chunk ("Attack Resolution") with the `###` sub-headings preserved
in the body text.

#### What this means for Stage 1

The Stage 1 parser is ~50 lines of code:

```python
# Pseudocode
for file in glob("components/*.md"):
    frontmatter = yaml.safe_load(...)           # system metadata
    sections = re.split(r'^## ', body, flags=re.MULTILINE)
    for section in sections:
        heading = first_line(section)
        tag_match = re.search(r'<!-- (.+?) -->', section)
        tags = parse_tags(tag_match)              # split on |, strip, key:value
        body = strip_tag_line(section)
        emit_chunk(heading, tags, body, line_range)
```

No heuristics. No heading-text classification. No ambiguity about what `section_kind`
a section should be. The author decided that at write time.

### 5.3 Stage 0: Documentation rewrite

Before Stage 1 can run, the existing docs must be rewritten to match the format spec.
This is manual work, guided by the agreed system list (v2_indexing.md §5.6).

**Scope:**
- One file per system/feature/support entry (19 systems + 3 support + features)
- Each file follows the format spec (§5.2): YAML frontmatter + tagged `##` sections
- Content is grounded: describes what the code actually does, cross-referenced against
  source files and V1 entity docs
- No duplication: each narrative topic appears in exactly one file. Other systems
  reference via prose cross-references (e.g., "see [Combat > Death Processing](combat.md#death--corpse-processing)")
- Hallucinated content from current docs is discarded, not carried forward
- `grounding` tags are honest: mark `mixed` or `weak` when unsure rather than
  defaulting to `grounded`

**File naming convention:** `{subsystem_id}.md` — e.g., `combat.md`, `affect_system.md`,
`utilities.md`, `loot_generation.md`.

**Dissolved docs:** The following current files are retired and their accurate content
redistributed into the new files:
- `character_system.md` → `character_data.md`, `combat.md`, `magic.md`, `affect_system.md`, `skills_progression.md`
- `user_experience_enhancers.md` → aliases into `command_interpreter.md`, marriage into `social_communication.md`, paintball dropped or into `clans_pvp.md`
- `world_visualization.md` → `world_system.md`
- `status_and_look_commands.md` → distributed across relevant system files
- `logging_and_monitoring.md` → `utilities.md`
- `admin_controls.md` + `builder_commands.md` → `admin_builder_tools.md`

### 5.4 Curation artifacts

Stored in `artifacts/v2/`, git-tracked, human-reviewable:

| Artifact | Format | Description |
|----------|--------|-------------|
| `subsystems_seed.json` | JSON array | Extracted from frontmatter of all doc files. System records: id, name, parent_id, kind, layer, description, source_file, depends_on, depended_on_by |
| `chunk_candidates.jsonl` | JSONL | Stage 1 output: one record per `##` section with heading, section_path, tags (section_kind, grounding_status, narrative_role), body, source_file, line_range. Ownership is already determined by file. |
| `subsystem_doc_chunks.jsonl` | JSONL | Stage 2 output: curated chunks with final grounding_status (may be upgraded/downgraded from author's tag), evidence, and potentially rewritten body text |
| `entity_subsystem_links.jsonl` | JSONL | One record per link: entity_id, subsystem_id, role, link_source, confidence, notes, evidence |
| `subsystem_edges.json` | JSON array | Extracted from frontmatter `depends_on`/`depended_on_by` fields |
| `curation_flags.jsonl` | JSONL | Unresolved cases, gaps, grounding disagreements, and review flags |

Note: `subsystems_seed.json` and `subsystem_edges.json` are now mechanically
extractable from frontmatter — no manual curation needed for system identity or
dependency declarations.

Why intermediate files rather than direct DB writes:
- **Reviewable** — diffs show exactly what the curation agent changed
- **Re-ingestable** — `build_v2_db.py` can re-import without rerunning the curation agent
- **Human-correctable** — errors can be fixed in the JSONL and re-ingested
- **Validatable** — lint rules run before DB load
- **Versionable** — git-tracked curation state with clear history

### 5.5 Chunk candidate format

Each record in `chunk_candidates.jsonl` (output of Stage 1):

```json
{
    "chunk_id": "combat::attack_resolution",
    "subsystem_id": "combat",
    "source_file": "components/combat.md",
    "heading": "Attack Resolution",
    "section_path": "Combat > Attack Resolution",
    "section_kind": "key_components",
    "narrative_role": "mechanism",
    "grounding_status": "grounded",
    "is_overview": false,
    "body": "Per-round hit calculation considering weapon skill...",
    "line_range": [24, 58]
}
```

All fields except `body` and `line_range` are extracted directly from the document
structure and tags. No inference needed.

### 5.6 Validation rules

Run after curation, before ingestion:

**Structural integrity:**
- Every subsystem in `subsystems_seed.json` has at least one `is_overview` doc chunk
- Every `entity_id` in links references an existing entity in V1 `entities` table
- Every `subsystem_id` in links and docs references a subsystem in `subsystems_seed.json`
- `entry_point` role links target only `kind = 'function'` entities

**Quality checks:**
- `utility` role used sparingly (warn if >30% of a subsystem's links are utility)
- warn if a `kind: system` subsystem has fewer than 3 doc chunks
- warn if a `kind: support` subsystem has more doc chunks than the median `kind: system`

**Canonical ownership conflict detection:**
- Flag chunks with cosine similarity > 0.92 but different subsystem owners
- Flag repeated headings (e.g., "Combat System", "Shop System", "Data Tables") across
  different subsystem owners
- Flag chunks whose `evidence.entity_ids` overlap > 50% with another chunk under a
  different owner

**Orphan detection (informational, not blocking):**
- Entities with no subsystem link
- Subsystems with no entity links (likely a curation gap)
- Subsystems with no `grounded` doc chunks (likely needs rewrite)

### 5.7 Running

```bash
# V1 build (prerequisite, unchanged)
cd mcp/doc_server
uv run python build_mcp_db.py

# V2 build
uv run python build_v2_db.py          # reads .env + artifacts/v2/
```

Build order: V1 first (entities, edges, capabilities), then V2 (subsystems, docs, links).
V2 build validates foreign key references against V1 data.

---

## 6. Curation Agent Contract

The curation agent uses V1 tools during the curation stage. This section defines the
rules and conventions it must follow.

### 6.1 Scope

The curation agent:
- Assesses grounding status by cross-referencing prose claims against V1 entity docs
  and source code (`get_entity`, `get_source_code`, `search`)
- Validates or adjusts the author's `grounding` tag (upgrade/downgrade based on evidence)
- Attaches evidence (entity IDs, capabilities, files) to each retained chunk
- Creates entity↔subsystem links by walking each system's doc, using behavior slices
  and capability details to identify participating entities
- Flags unresolved decisions in `curation_flags.jsonl`

The curation agent does **not**:
- Modify V1 tables or artifacts
- Assign subsystem ownership — ownership is determined by file placement (Stage 0)
- Invent new systems not in the agreed list without flagging for review
- Assign `grounding_status: grounded` without verifying claims against code
- Create duplicate prose — the one-file-per-system rule from Stage 0 prevents this

### 6.2 Layer boundary rules

For assigning the `layer` field:

- **`content_system`**: the system's primary purpose is managing authored artifacts and
  their runtime interpretation. *Test:* if you removed the authored content, would the
  system have no purpose? Examples: MobProg (scripts), Help (help entries), Notes (posts).
- **`player_feature`**: the system's primary purpose is a player-facing interaction loop
  or gameplay service. *Test:* does the system define a loop the player engages with?
  Examples: Quests (accept→hunt→complete), Economy (earn→spend→trade), Social (chat loops).

When a system straddles: pick the dominant purpose, express the secondary via edges.

### 6.3 `kind` assignment rules

- `kind: system` — satisfies most of: stable identity, own behavioral narrative,
  meaningful peer edges, navigation destination, nontrivial overview
- `kind: feature` — substantial enough for its own doc section, but scoped within
  a parent system
- `kind: support` — real topic, but reference catalog rather than behavioral narrative

### 6.4 Evidence requirements

For `entity_subsystem_links`:
- `core` and `entry_point` roles require `confidence: high` and at least 2 evidence
  fields populated
- `supporting` role requires at least 1 evidence field
- `utility` role may have minimal evidence (the link itself is the primary assertion)

For `subsystem_docs`:
- `grounded` chunks must have at least `entity_ids` or `files` populated in evidence
- `mixed` chunks should have evidence where available
- `weak` and `rejected` chunks: evidence optional (the grounding assessment is the
  primary signal)

---

## 7. Retrieval Design

### 7.1 Grounding-aware ranking

All V2 tools that return doc sections apply grounding-aware ranking:

| `grounding_status` | Ranking effect | Default visibility |
|--------------------|--------------|--------------------|
| `grounded` | Boost (+0.1 score) | Always included |
| `mixed` | Neutral | Included |
| `weak` | Penalty (−0.15 score) | Included with status flag |
| `rejected` | Excluded | Excluded (available via explicit filter) |

Agents see `grounding_status` on every returned section and can make trust decisions.
This is the narrative analog of V1's `doc_quality` on entities.

### 7.2 Overview-first retrieval

`get_subsystem` always returns the `is_overview` section first, followed by other
sections ordered by `narrative_role`:

1. `overview` — system identity and high-level description
2. `mechanism` — how the system works
3. `dependency` — what it depends on
4. `edge_case` — non-obvious behaviors
5. `admin` — operator-facing functionality
6. `history` — archaeological context

### 7.3 Context assembly (`get_subsystem_context`)

For a given entity, the tool assembles cross-system context using this priority:

1. Overview sections of linked subsystems (via `entity_subsystem_links`)
2. Sections where `evidence.entity_ids` includes the target or its direct neighbors
3. Sections where body text mentions the entity name
4. Sections where capability alignment matches
5. Dependency sections of linked subsystems
6. Overview sections of adjacent subsystems (via `subsystem_edges`)

Each section carries `inclusion_reason` and `narrative_role`, making the result
interpretable rather than opaque. The agent gets a structured reading order, not a
bag of hits.

---

## 8. V1 Forward-Compatibility

All forward-compatibility guarantees from DESIGN.md §18.5 hold:

- V1 tables unchanged — entity↔subsystem is a separate join table
- `capability` column stays as-is; independent from `subsystem_id`
- V1 tools continue to work unchanged; V2 tools are additive
- `SearchResult` envelope discriminates `entity` vs `subsystem_doc` via `result_type`
- `EntitySummary` gains optional `subsystems` field only when `include_subsystems=true`
- V2 response shapes (`SubsystemSummary`, `SubsystemDocSummary`, `ContextBundle`) are
  pre-defined in DESIGN.md §4.6 and refined here

---

## 9. Implementation Phases

### Phase V2.0 — Documentation Rewrite (Stage 0)
- Rewrite `docs/components/*.md` per system list and format spec (§5.2)
- One file per system/feature/support entry
- All classification metadata encoded in frontmatter + inline tags
- Content grounded against source code

### Phase V2.1 — Schema + Mechanical Chunking
- Create V2 tables in Postgres
- Implement chunk production from source docs (Stage 1 — string split + regex)
- Implement `build_v2_db.py` ingestion pipeline
- Implement validation rules

### Phase V2.2 — Curation
- Run curation agent against chunk candidates using V1 tools
- Produce all curation artifacts
- Run validation, resolve flags
- Ingest into database

### Phase V2.3 — Tools
- `list_subsystems`, `get_subsystem`
- `search` enhancement (source parameter, grounding filter)
- `get_entity` / `list_file_entities` enhancement (`include_subsystems`)

### Phase V2.4 — Context Assembly
- `get_subsystem_context` with reranking
- `get_subsystem_dependencies`
- `search_subsystem_docs`

---

## 10. Classification Axes Summary

Four complementary classification axes serve different retrieval needs:

| Axis | Lives on | Granularity | Cardinality per entity | Question answered |
|------|----------|-------------|----------------------|-------------------|
| **Capability** | `entities.capability` | Function-level | 1 | *What semantic responsibility does this code fulfill?* |
| **System** | `entity_subsystem_links` | Architectural | Many (with role) | *What system narrative helps interpret this code?* |
| **Kind** | `subsystems.kind` | System-level | 1 per system | *What sort of navigational object is this?* |
| **Layer** | `subsystems.layer` | System-level | 1 per system | *What abstraction level is this system?* |

No axis replaces another. Together they give agents four ways to find and filter
relevant context for any piece of code.

---

## 11. Project Structure (V2 additions)

```

├── artifacts/
│   └── v2/                         # V2 curation artifacts (git-tracked)
│       ├── subsystems_seed.json
│       ├── chunk_candidates.jsonl   # Stage 1 output
│       ├── subsystem_doc_chunks.jsonl  # Stage 2 output (curated)
│       ├── entity_subsystem_links.jsonl
│       ├── subsystem_edges.json
│       └── curation_flags.jsonl
├── docs/
│   ├── components/                  # Source docs (Stage 0 output, Stage 1 input)
│   │   ├── combat.md               # YAML frontmatter + tagged ## sections
│   │   ├── magic.md
│   │   ├── affect_system.md
│   │   ├── character_data.md
│   │   ├── loot_generation.md      # kind: feature, parent: object_system
│   │   ├── utilities.md            # kind: support
│   │   └── ...
│   └── subsystems.md               # Retired after V2 ingestion
└── mcp/
    └── doc_server/
        ├── DESIGN.md                # V1 spec (locked)
        ├── DESIGN_v2.md             # This document
        ├── v2_indexing.md           # Problem statement + taxonomy decisions
        ├── build_mcp_db.py          # V1 build (unchanged)
        ├── build_v2_db.py           # V2 build
        └── server/
            ├── server.py            # Tool registration (V1 + V2)
            ├── subsystem_tools.py   # V2 tool implementations
            ├── subsystem_models.py  # V2 Pydantic response models
            └── ...                  # V1 modules (unchanged)
```
