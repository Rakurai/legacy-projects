# MCP Documentation Server — Design Document

This document describes the design for an MCP server that exposes the Legacy MUD codebase as a searchable, analysis-capable knowledge store for AI assistants. It is not just documentation lookup — it is a small **analysis service** that surfaces entity documentation, structural relationships, behavioral context, and derived views from pre-computed artifacts.

---

## 1. Motivation

We have a rich set of pre-computed documentation artifacts for a ~90 KLOC C++ MUD codebase:

- **5,293 documented entities** (functions, variables, classes, structs, files, etc.) with LLM-generated briefs, details, parameter descriptions, rationale, and usage notes.
- **A dependency graph** (~5,300 entity nodes + location nodes, ~25,000+ typed edges) encoding calls, uses, inheritance, containment, and include relationships.
- **4,096-dimensional embeddings** for every entity docstring, enabling semantic similarity search.
- **30 capability group definitions** classifying functions into typed groups (domain, policy, projection, infrastructure, utility) with descriptions, locked function lists, and typed dependency edges between groups.
- **Source location data** (file path, start line, end line) for every entity, enabling on-demand code retrieval.

An MCP server makes this data directly accessible to AI coding assistants (Copilot, Claude, Cursor, etc.) during development sessions, without requiring the assistant to parse raw JSON or load large files into context.

### 1.1 Scope — What This Server Exposes

The server provides **factual, structural, and behavioral** information about the legacy codebase:

- **What it is** — entity identity, LLM-generated documentation, actual source code
- **What it does** — capability group membership, call cone, heuristic side-effect markers
- **What it touches** — globals/types used, state dependencies (via USES edges and side-effect markers)
- **How it relates** — callers, callees, inheritance, containment, file membership

### 1.2 What This Server Does NOT Expose

The server does **not** prescribe architectural decisions or migration strategy:

- No recommended target surfaces (e.g. "should become an Evennia CmdSet")
- No migration modes (native / adaptation / replacement / substrate)
- No implementation phase or wave ordering
- No architectural destination guesses

These are concerns of the migration agent consuming this server, not the source documentation server itself.

---

## 2. Source Artifacts

Full details in [artifacts.md](../../gen_docs/artifacts.md). Summary of what the build script ingests:

| Artifact | Path | Format | Size | Description |
|----------|------|--------|------|-------------|
| Entity Database | `code_graph.json` | JSON array | 5,305 entities | Every Doxygen-recognized entity (functions, classes, structs, variables, files, etc.) with identity, source locations (`body.fn`, `body.line`, `body.end_line`), definition/argsstring, and cross-reference lists. |
| Dependency Graph | `code_graph.gml` | GML (NetworkX) | ~5,300 entity nodes, ~25K edges | Typed directed multigraph: CALLS, USES, INHERITS, INCLUDES, CONTAINED_BY, REPRESENTED_BY. |
| Document Database | `doc_db.json` | JSON dict | 5,293 documents | LLM-generated documentation per entity: brief, details, params, returns, notes, rationale, usages. Keyed by `(compound_id, signature)`. |
| Embeddings Cache | `embeddings_cache.pkl` | Pickle (numpy) | 5,293 × 4,096 float32 (~83 MB) | L2-normalized doc embeddings keyed by member ID string. |
| Capability Defs | `capability_defs.json` | JSON dict | 30 groups | Capability group definitions: type (domain/policy/projection/infrastructure/utility), description, locked function lists, stability. |
| Capability Graph | `capability_graph.json` | JSON dict | 30 caps, 633 entry points | Group→group typed dependency edges with call counts; entry point→capability mapping; wave ordering. |

All artifacts live in `.ai/artifacts/` at the repository root.

### Entity kind breakdown

| Kind | Count | Level |
|------|-------|-------|
| function | 2,365 | member |
| variable | 2,369 | member |
| file | 217 | compound |
| struct | 80 | compound |
| group | 85 | compound |
| class | 56 | compound |
| define | 82 | member |
| dir | 20 | compound |
| enum | 11 | member |
| namespace | 11 | compound |
| typedef | 9 | member |

---

## 3. Identity Model & Primary Keys

### 3.1 Internal ID: Doxygen Entity ID

Every entity has a Doxygen-derived ID in the form `{compound}_{member}` (for members) or `{compound}` (for compounds). Examples:

- Compound: `structrace__type`, `class_character`, `fight_8cc`
- Member: `fight_8cc_1a2b3c4d5e6f7890abcdef1234567890ab`

These are **opaque, ugly, and not user-facing**. They serve as the internal primary key (`entity_id`) in the database and graph, preserving compatibility with the existing artifact pipeline.

### 3.2 User-Facing Identification: Scoped Symbol + Signature

Users and tool parameters work with human-readable identifiers:

- **Functions:** full C++ signature — `void do_look(Character *ch, String argument)`. Unique within the codebase (scoped symbols in C/C++ are unique; Doxygen signatures are always unique).
- **Compounds (classes, structs, files):** scoped name — `Character`, `race_type`, `src/fight.cc`.
- **Variables/defines:** scoped name including owning compound context if needed.

The database stores both `entity_id` (internal PK) and `signature` (the user-facing key, which is also unique). Tool parameters accept the human-readable form; resolution maps it to the internal ID.

### 3.3 Resolve vs. Get (two-step workflow)

Name-based queries can be ambiguous (bare names like `level` may match a variable, a function, and a struct field). To avoid silent wrong-entity errors:

1. **`resolve_entity(query)`** — returns a ranked candidate list with match metadata (match type, kind, file, owning compound, signature). The agent disambiguates.
2. **`get_entity(entity_id)`** — fetches full detail for a specific entity by its internal ID (returned from resolve). No ambiguity.

This prevents the common MCP failure mode where a tool returns "the wrong plausible entity" and the agent keeps going.

---

## 4. Standard Response Shapes

All tools use consistent, reusable data shapes to reduce schema drift and make agent prompting predictable.

### 4.1 `EntitySummary`

The compact entity representation used in every list-returning tool:

| Field | Type | Description |
|-------|------|-------------|
| `entity_id` | string | Internal ID (for passing to `get_entity`) |
| `signature` | string | Full human-readable signature |
| `name` | string | Bare name |
| `kind` | string | function, variable, class, struct, file, etc. |
| `file_path` | string? | Source file path |
| `capability` | string? | Capability group |
| `brief` | string? | One-line summary |
| `doc_state` | string | Documentation quality state |
| `doc_quality` | string | Derived quality bucket: `high`, `medium`, `low` |
| `fan_in` | int | Incoming CALLS edges |
| `fan_out` | int | Outgoing CALLS edges |

All list-returning tools embed `EntitySummary` as the base, adding tool-specific fields alongside.

In V2, tools that accept `include_subsystems=true` (default: false) will populate an additional `subsystems` field: list of `{id, name, role}` from the entity↔subsystem join table. In V1 this field is absent.

### 4.2 Resolution Envelope

Every tool that accepts an entity by name/signature (not just `resolve_entity`) wraps its response with resolution metadata:

| Field | Type | Description |
|-------|------|-------------|
| `resolution_status` | string | `exact` — unique match; `ambiguous` — multiple candidates (first used); `not_found` — no match |
| `resolved_from` | string | The query string that was resolved |
| `match_type` | string | How the top result matched: `entity_id`, `signature_exact`, `name_exact`, `name_prefix`, `keyword`, `semantic` |
| `resolution_candidates` | int | Number of candidates found (1 for exact) |

When `resolution_status` is `ambiguous`, the tool still executes against the top-ranked candidate but includes `resolution_candidates` count so the agent knows to disambiguate. When `not_found`, the tool returns an error with nearest matches.

Tools that accept `entity_id` directly skip resolution and always return `resolution_status: "exact"`.

### 4.3 Truncation Metadata

All graph-traversal and list-returning tools include truncation info:

| Field | Type | Description |
|-------|------|-------------|
| `truncated` | bool | Whether results were capped |
| `node_count` | int | Actual result count returned |
| `total_available` | int? | Total matches before truncation (if known) |
| `max_depth_requested` | int? | Depth limit requested |
| `max_depth_reached` | int? | Deepest level actually traversed |
| `truncation_reason` | string? | `depth_limit`, `node_limit`, or `none` |

This prevents agents from assuming completeness when they received a partial result set.

### 4.4 Provenance Labels

Derived/analysis tools tag each piece of data with how it was obtained:

| Label | Meaning |
|-------|---------|
| `graph_calls` | Direct from CALLS edges |
| `graph_uses` | Direct from USES edges |
| `graph_inherits` | Direct from INHERITS edges |
| `graph_transitive` | Multi-hop graph traversal (BFS) |
| `side_effect_marker` | Matched curated side-effect function list |
| `capability_map` | From capability group classification |
| `precomputed` | Computed at build time and stored |

Each derived result item includes a `provenance` field indicating its source, and a `confidence` field: `direct` (single-hop, exact), `heuristic` (curated list match or shallow transitive), or `transitive` (multi-hop, approximate).

### 4.5 `SearchResult` Envelope

The `search` tool returns results wrapped in a discriminated union that anticipates V2's unified search across entity docs and subsystem docs:

| Field | Type | Description |
|-------|------|-------------|
| `result_type` | string | `entity` (V1), or `subsystem` / `subsystem_doc` (V2) |
| `score` | float | Combined relevance score |
| `search_mode` | string | `hybrid`, `semantic_only`, or `keyword_fallback` |
| `provenance` | string | Doc source: `doxygen_extracted`, `llm_generated`, `subsystem_narrative` (V2) |
| `summary` | object | Type-specific summary: `EntitySummary` for entities, `SubsystemSummary` or `SubsystemDocSummary` for V2 types |

In V1, `result_type` is always `entity` and `summary` is always `EntitySummary`. V2 adds new result types without breaking the shape.

### 4.6 V2-Reserved Shapes

These shapes are defined now to prevent response-shape drift when V2 lands. They are **not used by V1 tools**.

#### `SubsystemSummary`

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Subsystem identifier |
| `name` | string | Human-readable name |
| `parent_id` | string? | Parent subsystem (for nesting) |
| `description` | string | Overview paragraph |
| `source_file` | string | Source markdown file |
| `entity_count` | int | Linked entities |
| `doc_section_count` | int | Chunked documentation sections |
| `depends_on_count` | int | Upstream dependencies |
| `depended_on_by_count` | int | Downstream dependents |

#### `SubsystemDocSummary`

| Field | Type | Description |
|-------|------|-------------|
| `id` | int | Section identifier |
| `subsystem_id` | string | Owning subsystem |
| `subsystem_name` | string | Owning subsystem name |
| `section_path` | string | Hierarchical path: `Core Components > Attack Resolution` |
| `heading` | string | Section heading |
| `section_kind` | string | Section type: `overview`, `responsibilities`, `key_components`, `implementation`, `dependencies`, `behaviors`, `future` |
| `source_file` | string | Source markdown file |
| `line_range` | range? | Line range in source |
| `excerpt` | string | First ~200 chars of body text |

#### `ContextBundle`

A structured response pattern for V2 tools that assemble mixed entity/system context. Not used in V1, but defined to prevent one-off blob shapes in V2:

| Field | Type | Description |
|-------|------|-------------|
| `focus_type` | string | `entity`, `subsystem`, `capability`, or `entry_point` |
| `focus` | object | The primary object (EntitySummary, SubsystemSummary, or capability detail) |
| `related_entities` | EntitySummary[] | Relevant code entities |
| `related_capabilities` | object[] | Relevant capability groups |
| `related_subsystems` | SubsystemSummary[] | Relevant subsystems (V2) |
| `relevant_doc_sections` | object[] | Subsystem doc sections with `inclusion_reason` (V2) |
| `confidence_notes` | string? | Overall confidence assessment |
| `truncated` | bool | Whether any component was truncated |

---

## 5. Architecture

### 5.1 Overall Design

```
┌──────────────────────────────────┐
│  .ai/artifacts/                  │
│  code_graph.json, doc_db.json,   │
│  code_graph.gml, embeddings,     │
│  capability_defs/graph           │
└──────────────┬───────────────────┘
               │
               ▼
┌──────────────────────────────────┐
│  build_mcp_db.py                 │
│  (offline, run once)             │
│                                  │
│  ┌─ Parse artifacts ──────────┐  │
│  │  Merge entity + doc (1:1)  │  │
│  │  Assign capability column  │  │
│  │  Compute graph metrics     │  │
│  │  Detect side-effect markers│  │
│  └────────────────────────────┘  │
│              │                   │
│              ▼                   │
│  ┌─ PostgreSQL + pgvector ────┐  │
│  │  entities table            │  │
│  │  edges table               │  │
│  │  capabilities table        │  │
│  │  capability_edges table    │  │
│  │  entry_points table        │  │
│  └────────────────────────────┘  │
└──────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────┐
│  MCP Server (FastMCP)            │
│                                  │
│  On startup:                     │
│   • Connect to Postgres          │
│   • SELECT * FROM edges          │
│   • Build NetworkX MultiDiGraph  │
│                                  │
│  At request time:                │
│   • SQL for lookup / search      │
│   • pgvector for similarity      │
│   • NetworkX for graph traversal │
│   • Disk read for source code    │
└──────────────────────────────────┘
```

### 5.2 Framework: FastMCP

[FastMCP](https://github.com/jlowin/fastmcp) — the actively-maintained high-level Python MCP framework, built on the official `mcp` SDK. Provides decorator-based tool/resource/prompt registration, supports stdio and SSE transports, and works well with Pydantic models for typed responses.

We avoid overcommitting to a specific API version in this design; the core patterns (decorated tool functions, typed parameters, structured returns) are stable across FastMCP releases.

### 5.3 PostgreSQL + pgvector

A local PostgreSQL instance (containerized) with the `pgvector` extension provides:

- **Vector similarity search** — `pgvector` indexes for embedding-based semantic search, replacing in-process numpy math.
- **Full-text search** — `tsvector`/`tsquery` for keyword search across names, briefs, details, definitions. This gives us proper ranked keyword search for free.
- **Relational indexes** — B-tree indexes on name, kind, file path, capability, signature for fast exact/prefix lookups.

The MCP server connects to Postgres on startup and queries it at request time. No artifact files are loaded at runtime. Connection details come from `.env`.

### 5.4 In-Memory Graph

The ~25K edges are small enough to hold in memory. At startup the server runs `SELECT source_id, target_id, relationship FROM edges` and builds a NetworkX `MultiDiGraph`. This gives us:

- Multi-hop traversal (BFS for call cones, behavior slices)
- Fan-in/fan-out computation
- Centrality metrics
- Path finding

NetworkX is the right tool here — no reason to reimplement graph algorithms. Building from ~25K edge rows takes milliseconds.

### 5.5 Embedding Queries

The server needs a running embedding endpoint to encode user queries at search time. Configuration via `.env`:

```
EMBEDDING_BASE_URL=http://localhost:4000/v1
EMBEDDING_API_KEY=lm-studio
EMBEDDING_MODEL=text-embedding-qwen3-embedding-8b
```

Uses the same `openai_embeddings` module pattern already in the codebase. Query embedding is fast (~50ms local).

**If the embedding endpoint is unavailable**, `search` falls back to Postgres full-text search only, and the response includes:

```json
{ "search_mode": "keyword_fallback", "warning": "Embedding server unavailable" }
```

This makes the degradation explicit so agents don't overtrust poor results.

---

## 6. Database Schema

### 6.1 `entities` Table

Entity and document data merged 1:1 (every entity has exactly one doc record).

```sql
CREATE TABLE entities (
    -- Identity (internal)
    entity_id       TEXT PRIMARY KEY,       -- doxygen compound_member ID
    compound_id     TEXT NOT NULL,          -- doxygen compound refid
    member_id       TEXT,                   -- member hex hash (NULL for compounds)
    
    -- Identity (user-facing)
    name            TEXT NOT NULL,          -- bare name: "do_look", "race_type"
    signature       TEXT NOT NULL UNIQUE,   -- full signature: "void do_look(Character *ch, String argument)"
    kind            TEXT NOT NULL,          -- function, variable, class, struct, file, ...
    entity_type     TEXT NOT NULL,          -- compound or member
    
    -- Source location
    file_path       TEXT,                   -- "src/fight.cc"
    body_start_line INTEGER,
    body_end_line   INTEGER,
    decl_file_path  TEXT,
    decl_line       INTEGER,
    
    -- Source code (extracted at build time from disk)
    definition_text TEXT,                   -- C++ definition line: "void do_look(Character *ch, String argument)"
    source_text     TEXT,                   -- full body source code (~5 MB total for all entities)
    
    -- Documentation
    brief           TEXT,
    details         TEXT,
    params          JSONB,                  -- {param_name: description}
    returns         TEXT,
    notes           TEXT,
    rationale       TEXT,
    usages          JSONB,                  -- {caller_key: usage_description}
    doc_state       TEXT,                   -- extracted_summary, refined_summary, etc.
    doc_quality     TEXT,                   -- derived: high, medium, low (see §7.2)
    
    -- Classification
    capability      TEXT,                   -- capability group name (nullable; see §16.5 — this is NOT a subsystem)
    is_entry_point  BOOLEAN DEFAULT FALSE,
    
    -- Precomputed metrics (from build script)
    fan_in          INTEGER DEFAULT 0,      -- number of incoming CALLS edges
    fan_out         INTEGER DEFAULT 0,      -- number of outgoing CALLS edges
    is_bridge       BOOLEAN DEFAULT FALSE,  -- callers/callees span different capabilities
    side_effect_markers JSONB,              -- {messaging: [...], persistence: [...], state_mutation: [...], scheduling: [...]}
    
    -- Embedding
    embedding       vector(4096),           -- pgvector column (doc embedding)
    
    -- Full-text search
    search_vector   tsvector                -- generated from name + brief + details + definition_text + source_text
    -- Implementation note: use weighted tsvector composition to prevent code tokens
    -- from swamping prose relevance:
    --   setweight(to_tsvector(name), 'A') ||
    --   setweight(to_tsvector(brief || details), 'B') ||
    --   setweight(to_tsvector(definition_text), 'C') ||
    --   setweight(to_tsvector(source_text), 'D')
);

-- Indexes
CREATE INDEX idx_entities_name ON entities (name);
CREATE INDEX idx_entities_kind ON entities (kind);
CREATE INDEX idx_entities_file ON entities (file_path);
CREATE INDEX idx_entities_capability ON entities (capability);
CREATE INDEX idx_entities_entry ON entities (is_entry_point) WHERE is_entry_point;
CREATE INDEX idx_entities_bridge ON entities (is_bridge) WHERE is_bridge;
CREATE INDEX idx_entities_search ON entities USING GIN (search_vector);
CREATE INDEX idx_entities_embedding ON entities USING ivfflat (embedding vector_cosine_ops) WITH (lists = 50);
```

### 6.2 `edges` Table

```sql
CREATE TABLE edges (
    source_id       TEXT NOT NULL REFERENCES entities(entity_id),
    target_id       TEXT NOT NULL REFERENCES entities(entity_id),
    relationship    TEXT NOT NULL,          -- calls, uses, inherits, includes, contained_by
    PRIMARY KEY (source_id, target_id, relationship)
);

CREATE INDEX idx_edges_source ON edges (source_id);
CREATE INDEX idx_edges_target ON edges (target_id);
CREATE INDEX idx_edges_rel ON edges (relationship);
```

### 6.3 `capabilities` Table

```sql
CREATE TABLE capabilities (
    name            TEXT PRIMARY KEY,
    type            TEXT NOT NULL,          -- domain, policy, projection, infrastructure, or utility
    description     TEXT,
    stability       TEXT,
    function_count  INTEGER DEFAULT 0
);
```

### 6.4 `capability_edges` Table

```sql
CREATE TABLE capability_edges (
    source_cap      TEXT NOT NULL REFERENCES capabilities(name),
    target_cap      TEXT NOT NULL REFERENCES capabilities(name),
    edge_type       TEXT NOT NULL,          -- requires_core, uses_utility, etc.
    call_count      INTEGER DEFAULT 0,
    in_dag          BOOLEAN DEFAULT FALSE,
    PRIMARY KEY (source_cap, target_cap)
);
```

### 6.5 `entry_points` Table

```sql
CREATE TABLE entry_points (
    name            TEXT PRIMARY KEY,       -- do_kill, spell_fireball, etc.
    entity_id       TEXT REFERENCES entities(entity_id),
    capabilities    JSONB,                  -- list of capability names exercised
    entry_type      TEXT                    -- do_, spell_, spec_
);
```

---

## 7. Build Script — `build_mcp_db.py`

An offline script that reads the raw artifacts and populates PostgreSQL. Run once, re-run when documentation pipeline produces new artifacts.

### 7.1 Pipeline

```python
# 1. Load raw artifacts from .ai/artifacts/ (reusing existing clustering/ modules)
ARTIFACTS = Path(os.environ["ARTIFACTS_DIR"])  # .ai/artifacts
entity_db = doxygen_parse.load_db(ARTIFACTS / "code_graph.json")
graph = doxygen_graph.load_graph(ARTIFACTS / "code_graph.gml")
doc_db = DocumentDB().load(ARTIFACTS / "doc_db.json")
embeddings = pickle.load(ARTIFACTS / "embeddings_cache.pkl")
cap_defs = json.load(ARTIFACTS / "capability_defs.json")
cap_graph = json.load(ARTIFACTS / "capability_graph.json")

# 2. For each entity: merge entity + doc, extract source, assign capability, compute metrics
for entity in entity_db.entities.values():
    doc = doc_db.get_doc(entity.id.compound, entity.signature)
    source_text = read_source_from_disk(entity, PROJECT_ROOT)  # extract body from .cc/.hh files
    definition_text = build_definition_text(entity)             # "void do_look(Character *ch, String argument)"
    capability = resolve_capability(entity, cap_defs, cap_graph)
    fan_in, fan_out = compute_fan_in_out(graph, entity)
    side_effects = detect_side_effects(graph, entity, SIDE_EFFECT_MARKERS)
    is_bridge = detect_bridge(graph, entity, cap_membership)
    doc_quality = compute_doc_quality(doc, entity)
    embedding = embeddings.get(entity.id.member or str(entity.id))
    # → INSERT INTO entities (...)

# 3. Extract edges from graph (filtering out location nodes)
for u, v, data in graph.edges(data=True):
    if data.get("type") in (CALLS, USES, INHERITS, INCLUDES, CONTAINED_BY):
        # → INSERT INTO edges (source_id, target_id, relationship)

# 4. Load capabilities + capability edges
for name, defn in cap_defs.items():
    # → INSERT INTO capabilities (...)
for src, targets in cap_graph["dependencies"].items():
    for tgt, info in targets.items():
        # → INSERT INTO capability_edges (...)

# 5. Load entry points
for ep_name, ep_data in cap_graph["entry_points"].items():
    # → INSERT INTO entry_points (...)

# 6. Generate tsvector column (includes source code for code-level keyword search)
# UPDATE entities SET search_vector = to_tsvector('english',
#   coalesce(name,'') || ' ' || coalesce(brief,'') || ' ' ||
#   coalesce(details,'') || ' ' || coalesce(definition_text,'') || ' ' ||
#   coalesce(source_text,''))
```

### 7.2 Precomputed Derived Data

The build script computes and stores:

- **Source code extraction** — for each entity with `body.fn`, `body.line`, `body.end_line`, read the source from disk and store as `source_text` (~5 MB total). This eliminates the runtime dependency on correct source checkout path and enables full-text search over code content (e.g. searching for `IS_NPC` or `WAIT_STATE`).

- **Definition text** — the C++ definition line (`definition + argsstring` for functions, name for others). Stored separately for search indexing.

- **`doc_quality`** — a derived quality bucket computed from multiple signals:
  - `high` — `doc_state` is `refined_summary` or `refined_usage` AND `details` is non-empty AND `params` coverage exists (for functions)
  - `medium` — `doc_state` is `generated_summary` or `refined_*` but missing details/params
  - `low` — `doc_state` is `extracted_summary` (no LLM-generated docs) OR brief is empty

  Stored as a column. Helps agents decide whether to trust docs or fetch source.

- **Fan-in / fan-out** per entity (CALLS edges only) — stored as columns on `entities`.

- **Side-effect markers** — for each function, check if its CALLS edges include known side-effect targets. Stored as a JSONB column. The marker list is a curated set of ~20-30 functions:
  - **Messaging:** `act`, `send_to_char`, `printf_to_char`, `send_to_room`
  - **Persistence:** `save_char_obj`, `fwrite_char`, `do_save`
  - **State mutation:** `extract_char`, `char_from_room`, `char_to_room`, `obj_from_char`, `obj_to_char`, `obj_to_room`
  - **Scheduling:** `event_add`, various `WAIT_STATE` macros
  - **Combat:** `set_fighting`, `stop_fighting`, `damage`, `raw_kill`

  This is a one-time curated list, not per-entity LLM research.

- **`is_entry_point`** flag — true for `do_*`, `spell_*`, `spec_*` functions.

- **`is_bridge`** flag — true for entities whose callers and callees span different capability groups. Computed by checking whether the sets of capabilities touched by incoming vs. outgoing CALLS neighbors have non-trivial differences.

### 7.3 Error Handling

- **Missing artifact file** — the build script exits with a clear error naming the missing file and its expected path.
- **Malformed artifact** (invalid JSON, corrupt pickle) — the build script exits with a validation error and byte/line position if available.
- **Invalid source location** (file missing on disk, line range out of bounds) — the entity is inserted with `source_text = NULL`; the server returns documentation without source code when requested.
- **Entity without matching doc record** — the entity is inserted with empty documentation fields and `doc_quality = 'low'`.

### 7.4 Running

```bash
cd .ai/mcp/doc_server
uv run python build_mcp_db.py          # reads .env for PG connection + ARTIFACTS_DIR
```

The build script should complete in under 5 minutes for ~5,300 entities. It is idempotent — re-running produces the same database state.

---

## 8. Exposed Tools

### 8.1 Resolution & Lookup

All tools that accept an entity name/signature (rather than a pre-resolved `entity_id`) perform internal resolution and include a **resolution envelope** in the response:

| Field | Description |
|-------|-------------|
| `resolution_status` | `exact` (single match), `ambiguous` (multiple candidates — first used), `not_found` |
| `resolved_from` | The query string that was resolved |
| `candidates` | (only when `ambiguous`) — ranked candidate list so the caller can refine |

#### `resolve_entity`

Search for entities by name or text, returning a ranked candidate list for disambiguation.

| Parameter | Type | Description |
|-----------|------|-------------|
| `query` | string | Bare name, partial name, signature fragment, or natural language |
| `kind` | string? | Filter by entity kind |
| `limit` | int | Max candidates (default: 10) |
| `verbose` | bool | Include pipeline stage details for each candidate (default: false) |

**Returns** a resolution envelope plus a list of candidates, each as an **EntitySummary**:

| Field | Description |
|-------|-------------|
| `entity_id` | Internal ID (for passing to `get_entity`) |
| `signature` | Full human-readable signature |
| `kind` | Entity kind |
| `file_path` | Source file |
| `capability` | Capability group (if assigned) |
| `brief` | One-line summary |
| `doc_quality` | `high`, `medium`, or `low` |
| `match_type` | How it matched: `signature_exact`, `name_exact`, `name_prefix`, `keyword`, `semantic` |
| `score` | Relevance score (1.0 for exact, decreasing) |

When `verbose=true`, each candidate additionally includes `pipeline_stages` — the list of stages that produced this match and their individual scores. This subsumes the old `explain_resolution` concept.

**Resolution pipeline** (executed in order, results merged and ranked):

1. Exact signature match (Postgres `WHERE signature = query`)
2. Exact name match (`WHERE name = query`, may return multiples)
3. Prefix match (`WHERE name ILIKE query || '%'`)
4. Full-text search (`WHERE search_vector @@ plainto_tsquery(query)`)
5. Semantic search (`ORDER BY embedding <=> query_embedding LIMIT k`) — only if embedding endpoint is available

#### `get_entity`

Fetch full detail for a specific entity by internal ID.

| Parameter | Type | Description |
|-----------|------|-------------|
| `entity_id` | string | Internal entity ID (from `resolve_entity`) |
| `include_code` | bool | Include stored source code (default: false) |
| `include_neighbors` | bool | Include direct graph neighbors with edge types (default: false) |

**Returns:** Full entity record including all documentation fields, definition text, source location, capability, `doc_quality`, metrics (fan-in/fan-out, is_bridge, side_effect_markers), plus optionally:
- `source_text` — the entity's source code (stored in DB at build time, not read from disk at runtime)
- Direct neighbors: list of `{entity_id, signature, kind, relationship, direction}` tuples (EntitySummary shape)

#### `get_source_code`

Retrieve source code for an entity by name (convenience wrapper: resolves → returns stored source).

| Parameter | Type | Description |
|-----------|------|-------------|
| `entity_name` | string | Entity name or signature |
| `context_lines` | int | Extra lines above/below (default: 0) |

**Returns:** Resolution envelope + source code text, file path, line range, and `doc_quality`. When `context_lines > 0`, the surrounding lines are read from disk (the stored `source_text` covers only the entity body).

#### `list_file_entities`

List all entities defined in a source file.

| Parameter | Type | Description |
|-----------|------|-------------|
| `file_path` | string | Source file path (e.g. `src/fight.cc`) |
| `kind` | string? | Filter by entity kind |

**Returns:** List of EntitySummary objects for the file: `{entity_id, signature, kind, line_range, brief, doc_quality, capability}`.

#### `get_file_summary`

High-level summary of a source file: what it contains, its role in the codebase, and key metrics.

| Parameter | Type | Description |
|-----------|------|-------------|
| `file_path` | string | Source file path (e.g. `src/fight.cc`) |

**Returns:**

| Field | Description |
|-------|-------------|
| `file_path` | Canonical path |
| `entity_count` | Total entities in this file, broken down by kind |
| `capabilities` | Set of capability groups that entities in this file belong to, with counts |
| `doc_quality_distribution` | `{high: N, medium: N, low: N}` |
| `key_entities` | Top entities by fan-in (most called from outside) — EntitySummary shape |
| `includes` | Files this file includes (from INCLUDES edges) |
| `included_by` | Files that include this file |

### 8.2 Search

#### `search`

Hybrid search combining keyword and semantic similarity.

| Parameter | Type | Description |
|-----------|------|-------------|
| `query` | string | Natural language search query |
| `top_k` | int | Number of results (default: 10) |
| `kind` | string? | Filter by entity kind |
| `capability` | string? | Filter to capability group |
| `min_doc_quality` | string? | Filter: `high`, `medium`, or `low` (default: no filter) |
| `source` | string? | V2-reserved: `entity` (default), `subsystem_doc`, or `all`. V1 always uses `entity`. |

**Returns** a ranked list of `SearchResult` envelopes (see §4.5). In V1, `result_type` is always `entity` and `summary` is always `EntitySummary`.

When the embedding endpoint is available, results are ranked by a combination of:
- pgvector cosine similarity
- Postgres full-text search rank
- Exact name/signature boost

When embedding service is unavailable, search switches to keyword-only mode and reports `search_mode: "keyword_fallback"`.

### 8.3 Graph Exploration

All graph tools accept either an `entity_id` (from resolve) or a `name`/`signature` (resolved internally, with resolution envelope in response). All graph tools include **truncation metadata** when results are capped:

| Field | Description |
|-------|-------------|
| `truncated` | `true` if the result set was capped |
| `total_available` | Total count before truncation |
| `returned` | Count actually returned |

#### `get_callers`

| Parameter | Type | Description |
|-----------|------|-------------|
| `entity` | string | Entity ID, name, or signature |
| `depth` | int | Traversal depth (default: 1, max: 3) |
| `limit` | int | Max results (default: 50) |

**Returns:** Resolution envelope + truncation metadata + for each caller: `{entity_id, signature, kind, file_path, brief, doc_quality, edge_type, depth}`. At depth > 1, also includes a `path` field showing the call chain. Results are deduplicated (each entity appears once with its shortest path).

#### `get_callees`

Same parameters and structure as `get_callers`, traversing outgoing CALLS edges.

#### `get_dependencies`

| Parameter | Type | Description |
|-----------|------|-------------|
| `entity` | string | Entity ID, name, or signature |
| `relationship` | string? | Filter: `calls`, `uses`, `inherits`, `includes`, `contained_by` (default: all) |
| `direction` | string | `outgoing` or `incoming` (default: `outgoing`) |
| `limit` | int | Max results (default: 50) |

**Returns:** Resolution envelope + truncation metadata + typed list of `{entity_id, signature, kind, relationship, brief, doc_quality}`.

#### `get_class_hierarchy`

| Parameter | Type | Description |
|-----------|------|-------------|
| `class_name` | string | Class or struct name |
| `direction` | string | `ancestors`, `descendants`, or `both` (default: `both`) |

**Returns:** Resolution envelope + inheritance tree with documentation per class/struct.

#### `get_related_entities`

Unified neighbor view: all entities directly connected to the target, grouped by relationship type and direction.

| Parameter | Type | Description |
|-----------|------|-------------|
| `entity` | string | Entity ID, name, or signature |
| `relationships` | string[]? | Filter to specific types (default: all) |
| `limit` | int | Max results per relationship type (default: 20) |

**Returns:** Resolution envelope + a map of `{relationship_type → {incoming: EntitySummary[], outgoing: EntitySummary[]}}` with truncation metadata per group.

#### `get_related_files`

Given a source file, return files that are structurally related (via INCLUDES edges, shared entities, or co-occurrence in call chains).

| Parameter | Type | Description |
|-----------|------|-------------|
| `file_path` | string | Source file path |
| `relationship` | string? | Filter: `includes`, `included_by`, `co_dependent` (default: all) |

**Returns:** For each related file: `{file_path, relationship, shared_entity_count, capabilities_in_common}`.

### 8.4 Behavior Analysis (Derived Views)

These tools compute derived views from the graph + entity data at request time. No extra precomputation or LLM calls needed. All derived views carry **provenance labels** (see §4.4) indicating data source — e.g. `graph_calls` for direct CALLS edges, `graph_transitive` for multi-hop BFS, `side_effect_marker` for curated list matches — and a **confidence** field: `direct`, `heuristic`, or `transitive`.

#### `get_behavior_slice`

Given an entry point or seed function, return a structured summary of its behavioral footprint.

| Parameter | Type | Description |
|-----------|------|-------------|
| `entity` | string | Entry point name, entity ID, or signature |
| `max_depth` | int | Call cone depth (default: 5) |
| `max_cone_size` | int | Max entities in call cone (default: 200) |

**Returns:** Resolution envelope + truncation metadata +

| Field | Provenance | Description |
|-------|-----------|-------------|
| `entry_point` | doc | The seed entity with full docs |
| `direct_callees` | graph | Functions called directly by the seed (depth=1), each as EntitySummary |
| `transitive_call_cone` | graph | All transitively reachable functions (depth>1), deduplicated, each with `{entity_id, signature, kind, brief, depth, capability}` |
| `capabilities_touched` | graph | Map of `{capability_name → {direct: N, transitive: N}}` — counts separated by direct vs. transitive |
| `globals_used` | graph | Variables/types reachable via USES edges, with `{direct: [...], transitive: [...]}` separation |
| `side_effect_markers` | curated | Functions in the cone matching curated markers, categorized and tagged: `{messaging: [{entity, direct: bool}, ...], persistence: [...], state_mutation: [...], scheduling: [...]}` |
| `fan_in` / `fan_out` | graph | Aggregate metrics for the seed |
| `confidence` | mixed | Overall confidence based on `doc_quality` distribution in the cone |

This is pure graph traversal — BFS over the in-memory NetworkX graph, then SQL lookups for entity details. The direct/transitive split lets agents distinguish "this function directly sends messages" from "something 5 calls deep does."

#### `get_state_touches`

For a given entity, show what state it reads/writes (approximated from USES edges and side-effect markers).

| Parameter | Type | Description |
|-----------|------|-------------|
| `entity` | string | Entity ID, name, or signature |

**Returns:** Resolution envelope +

| Field | Provenance | Description |
|-------|-----------|-------------|
| `direct_uses` | graph | Variables/types this entity directly USES (from graph edges) |
| `direct_side_effects` | curated | Side-effect markers from this entity's **own** CALLS (depth=1) |
| `transitive_uses` | graph | Variables/types reachable within 2 hops of CALLS → USES |
| `transitive_side_effects` | curated | Side-effect markers from callees at depth 2+ |
| `confidence` | mixed | Based on completeness of USES edges for this entity |

#### `get_hotspots`

Return entities ranked by structural importance or complexity.

| Parameter | Type | Description |
|-----------|------|-------------|
| `metric` | string | `fan_in`, `fan_out`, `bridge` (cross-capability), `underdocumented` |
| `kind` | string? | Filter by entity kind |
| `capability` | string? | Filter to capability group |
| `limit` | int | Max results (default: 20) |

**Precomputed in the build script** and stored as columns on `entities`:
- `fan_in` / `fan_out` — CALLS edge counts
- Bridge entities — functions with `is_bridge = true` (callers/callees span different capability groups)
- Underdocumented — `doc_quality = 'low'` (no LLM-generated docs or empty details)

### 8.5 Capability Tools

#### `list_capabilities`

List all 30 capability groups.

**Returns:** `{name, type, description, function_count, stability, doc_quality_distribution}` for each group.

#### `get_capability_detail`

| Parameter | Type | Description |
|-----------|------|-------------|
| `capability` | string | Group name |
| `include_functions` | bool | List all member functions (default: false) |
| `include_dependencies` | bool | Show inter-group dependency edges (default: true) |

**Returns:** Group definition, dependency edges `{target, edge_type, call_count}`, entry points using this capability, and optionally the full function list (as EntitySummary objects with truncation metadata).

#### `list_entry_points`

List entry points, optionally filtered by capability or pattern.

| Parameter | Type | Description |
|-----------|------|-------------|
| `capability` | string? | Filter to entry points that exercise this capability |
| `pattern` | string? | Name pattern filter (e.g. `do_*`, `spell_*`) |
| `limit` | int | Max results (default: 50) |

**Returns:** List of EntitySummary objects for each entry point, with `capabilities_touched` (list of capability groups the entry point's call cone reaches) and truncation metadata.

#### `compare_capabilities`

Compare two or more capability groups side by side.

| Parameter | Type | Description |
|-----------|------|-------------|
| `capabilities` | string[] | 2+ capability group names |

**Returns:** For each capability: `{name, function_count, entry_point_count, stability, doc_quality_distribution}`, plus:
- `shared_dependencies` — dependency edges common to all listed capabilities
- `unique_dependencies` — per-capability dependencies not shared with others
- `bridge_entities` — entities that span the listed capabilities (EntitySummary shape)

#### `get_entry_point_info`

| Parameter | Type | Description |
|-----------|------|-------------|
| `entry_point` | string | Entry point name (e.g. `do_kill`) |

**Returns:** Resolution envelope + which capabilities this entry point exercises (with direct/transitive counts), key direct callees (EntitySummary shape), and call cone summary metrics.

---

## 9. Exposed Resources

MCP resources provide static/semi-static context that clients can pull without tool calls.

| Resource URI | Description |
|-------------|-------------|
| `legacy://capabilities` | All 30 capability groups with descriptions |
| `legacy://capability/{name}` | Single capability group detail + dependencies |
| `legacy://entity/{entity_id}` | Full entity record |
| `legacy://file/{path}` | All entities in a source file |
| `legacy://stats` | Summary stats: entity counts by kind, doc state distribution, graph metrics |

---

## 10. Exposed Prompts

Canned analysis recipes for common investigative workflows. These are MCP prompts — structured templates the client can invoke, not migration prescriptions.

| Prompt | Description |
|--------|-------------|
| `explain_entity` | Given an entity name: resolve it, fetch full docs + neighbors + source code, and present a structured explanation |
| `analyze_behavior` | Given an entry point: get behavior slice, list capabilities touched, side effects, and state dependencies |
| `compare_entry_points` | Given 2+ entry point names: show shared vs. unique callees, capability overlap, state touch differences |
| `explore_capability` | Given a capability group: list functions, show dependencies, highlight hotspots and entry points |

---

## 11. Configuration

All connection details in `.env` (loaded by both `build_mcp_db.py` and the MCP server):

```env
# PostgreSQL
PGHOST=localhost
PGPORT=5432
PGDATABASE=legacy_docs
PGUSER=legacy
PGPASSWORD=...

# Embedding endpoint (OpenAI-compatible)
EMBEDDING_BASE_URL=http://localhost:4000/v1
EMBEDDING_API_KEY=lm-studio
EMBEDDING_MODEL=text-embedding-qwen3-embedding-8b

# Project root (used by build script only — for source code extraction at build time)
PROJECT_ROOT=/path/to/legacy

# Artifacts directory (pre-computed documentation artifacts)
ARTIFACTS_DIR=/path/to/legacy/.ai/artifacts

# Logging
LOG_LEVEL=INFO                  # DEBUG, INFO, WARNING, ERROR
```

### 11.1 Observability

The server emits structured logs to **stderr** (separate from MCP protocol on stdout) via `loguru`. Log level is controlled by `LOG_LEVEL` in `.env`, defaulting to `INFO`.

- **INFO:** server startup/shutdown, tool invocations with parameters, database connection events, embedding service availability changes, performance metrics exceeding thresholds.
- **ERROR:** database connection failures, invalid tool parameters, internal errors, any condition producing an MCP error response.
- **DEBUG:** SQL queries, embedding requests, resolution pipeline stages, graph traversal details.

Log format is JSON or structured key-value, suitable for machine parsing.

---

## 12. Project Structure

```
.ai/
├── artifacts/                  # Pre-computed documentation artifacts (input to build)
│   ├── code_graph.json
│   ├── code_graph.gml
│   ├── doc_db.json
│   ├── embeddings_cache.pkl
│   ├── capability_defs.json
│   └── capability_graph.json
├── gen_docs/
│   └── clustering/             # Artifact generation modules (reused by build script)
│       ├── doxygen_parse.py
│       ├── doxygen_graph.py
│       ├── doc_db.py
│       └── openai_embeddings.py
└── mcp/
    └── doc_server/             # This project
        ├── DESIGN.md           # This document
        ├── server/
        │   ├── __init__.py
        │   ├── server.py       # FastMCP app: tool/resource/prompt registration
        │   ├── db.py           # SQLAlchemy async engine + session factory, repositories
        │   ├── db_models.py     # SQLModel table=True definitions (Entity, Edge, etc.)
        │   ├── graph.py        # NetworkX graph (loaded from edges table at startup)
        │   ├── search.py       # Hybrid search (pgvector + full-text + name boost)
        │   ├── resolver.py     # Resolution pipeline + envelope generation
        │   └── models.py       # Pydantic API response models (EntitySummary, envelopes, etc.)
        ├── build_mcp_db.py     # Offline: artifacts → PostgreSQL
        └── .env                # Connection config (gitignored)
```

---

## 13. Dependencies

```toml
[project.optional-dependencies]
mcp = [
    "fastmcp",
    "sqlmodel",              # ORM + table definitions (extends Pydantic)
    "sqlalchemy[asyncio]",   # async engine + session (uses asyncpg driver)
    "asyncpg",               # async Postgres driver (transitive, but pinned)
    "pgvector",             # pgvector Python support
    "networkx>=3.6",
    "numpy>=2.4",
    "pydantic>=2.12",
    "loguru>=0.7",
    "openai>=2.26",         # embedding queries
    "python-dotenv",
]
```

---

## 14. Running

### Build the database

```bash
# Start Postgres container (with pgvector)
docker run -d --name legacy-pgvector \
  -e POSTGRES_DB=legacy_docs \
  -e POSTGRES_USER=legacy \
  -e POSTGRES_PASSWORD=... \
  -p 5432:5432 \
  pgvector/pgvector:pg17

# Populate from artifacts
cd .ai/mcp/doc_server
uv run python build_mcp_db.py
```

### Run the MCP server

```bash
# stdio mode (for VS Code / Claude Desktop)
cd .ai/mcp/doc_server
uv run python -m server.server
```

### Client configuration

**VS Code (`.vscode/mcp.json`):**
```json
{
  "servers": {
    "legacy-docs": {
      "command": "uv",
      "args": ["run", "python", "-m", "server.server"],
      "cwd": "${workspaceFolder}/.ai/mcp/doc_server"
    }
  }
}
```

---

## 15. Implementation Phases

**Phase 1 — Database + Core Lookup**
- `build_mcp_db.py`: parse artifacts, populate Postgres (including source extraction, doc_quality, side-effect markers)
- `resolve_entity`, `get_entity`, `get_source_code`, `list_file_entities`, `get_file_summary`
- Resources: `legacy://entity/*`, `legacy://file/*`, `legacy://stats`

**Phase 2 — Search**
- Hybrid search: pgvector similarity + full-text + name boost
- `search` tool with keyword-only mode reporting and provenance labels

**Phase 3 — Graph Exploration**
- Load edges → NetworkX at startup
- `get_callers`, `get_callees`, `get_dependencies`, `get_class_hierarchy`, `get_related_entities`, `get_related_files`
- Truncation metadata on all graph tools

**Phase 4 — Behavior Analysis**
- `get_behavior_slice`, `get_state_touches`, `get_hotspots`
- Direct/transitive separation, provenance labels, confidence levels

**Phase 5 — Capabilities + Prompts**
- `list_capabilities`, `get_capability_detail`, `list_entry_points`, `compare_capabilities`, `get_entry_point_info`
- Canned analysis prompts

---

## 16. Design Decisions

### 16.1 PostgreSQL + pgvector (not in-memory)

Combining relational indexes, full-text search, and vector similarity in one system. The MCP server is a thin query + traversal layer using SQLModel table models with SQLAlchemy async sessions (asyncpg driver). No artifact files loaded at runtime. Rebuild by re-running the build script.

### 16.2 NetworkX for graph traversal

The in-memory graph is built from the `edges` table on startup (~25K rows → milliseconds to construct). NetworkX provides BFS, path-finding, centrality, and other graph algorithms we need for behavior slices and hotspot analysis. No reason to reimplement.

### 16.3 Embedding model as a runtime dependency

Semantic search requires a running embedding endpoint to encode queries. Connection details in `.env`. When unavailable, search switches to keyword-only mode and reports `search_mode: "keyword_fallback"` explicitly so agents don't overtrust results.

### 16.4 Side-effect markers via curated list

Rather than LLM-analyzing every function for side effects, we maintain a curated list of ~20-30 known side-effect functions (messaging, persistence, state mutation, scheduling). The build script checks each function's CALLS edges against this list. Low effort, high signal.

### 16.5 Capabilities ≠ subsystems

The `capability` column on entities represents a **typed semantic grouping** inferred from legacy code evidence. Each of the 30 capability groups is classified as one of: **domain** (reusable gameplay behavior like combat, magic, movement), **policy** (validation, permissions, state checks), **projection** (rendering, messaging, visible output), **infrastructure** (persistence, database, technical services), or **utility** (low-level helpers like string operations, flags, numerics). The groups were derived by analyzing the static call graph: entry points (do_\*, spell_\*, spec_\*) are traced to transitive callees, which are classified against curated locked lists with embedding-similarity fallback.

The capability graph also carries typed dependency edges between groups (requires_core, requires_policy, uses_utility, etc.) and wave ordering — these serve migration chunk planning but are also useful for understanding which functional concerns depend on which. **Note:** V1 tools do not expose wave ordering directly. The ordering exists in the source artifact (`capability_graph.json`) and is available for future specialized tooling, but surfacing it in V1 responses would blur the line between factual documentation and migration prescription.

This is a distinct concept from **systems/subsystems/features**, which represent the higher-level architectural components of the game ("the Combat System", "the Affect System", "the Networking layer"). The project has rich system-level documentation in `.ai/docs/components/` and `.ai/docs/subsystems.md`, but these operate at a different level of abstraction.

Key differences:
- An entity may belong to one capability group but participate in multiple systems (e.g., `act()` is in the `output` capability but is used by nearly every system).
- A system like "Combat" spans multiple capability groups (combat, affects, attributes, output, persistence).
- True utility functions (string_ops, flags, numerics) belong to a capability but have no meaningful system affiliation.
- Not all capabilities are domain-level — policy, projection, infrastructure, and utility groups exist at a different abstraction level than domain groups, and the `type` field distinguishes them.

V1 serves capabilities as-is. V2 will add the system/subsystem layer with careful agent-assisted curation (see §18).

### 16.6 No migration prescriptions

The server exposes factual and structural information only. No target surfaces, migration modes, implementation ordering, or architectural destination guesses. Those are the consuming agent's concerns.

---

## 17. Example Interactions

### Resolve + Fetch workflow

```
→ resolve_entity(query="damage", kind="function")
← {
    resolution_status: "ambiguous",
    resolved_from: "damage",
    candidates: [
      { entity_id: "fight_8cc_abc123...", signature: "void damage(Character *ch, Character *victim, int dam, int dt, int class_, bool show)",
        kind: "function", file_path: "src/fight.cc", capability: "combat", doc_quality: "high",
        match_type: "name_exact", score: 1.0, brief: "Apply damage from ch to victim..." },
      { entity_id: "act_wiz_8cc_def456...", signature: "void damage(Object *obj, int amount)",
        kind: "function", file_path: "src/act_wiz.cc", capability: null, doc_quality: "medium",
        match_type: "name_exact", score: 1.0, brief: "Apply damage to an object..." },
    ]
  }

→ get_entity(entity_id="fight_8cc_abc123...", include_neighbors=true)
← { full entity detail + doc_quality: "high" + neighbor list as EntitySummary objects }
```

### Behavior slice for an entry point

```
→ get_behavior_slice(entity="do_kill", max_depth=5, max_cone_size=200)
← {
    resolution_status: "exact",
    resolved_from: "do_kill",
    truncated: false,
    confidence: "high",
    entry_point: { signature: "void do_kill(Character *ch, String argument)", doc_quality: "high", ... },
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

### Semantic search

```
→ search(query="poison spreading between characters", top_k=5)
← [
    { signature: "void plague_spread(Character *ch)", score: 0.89,
      search_mode: "hybrid", doc_quality: "high", provenance: "llm_generated", ... },
    { signature: "void spell_plague(int sn, int level, Character *ch, void *vo, int target)",
      score: 0.82, doc_quality: "medium", provenance: "llm_generated", ... },
    ...
  ]
```

### File summary

```
→ get_file_summary(file_path="src/fight.cc")
← {
    file_path: "src/fight.cc",
    entity_count: { function: 42, variable: 8, total: 50 },
    capabilities: { "combat": 38, "affects": 4, "attributes": 6 },
    doc_quality_distribution: { high: 30, medium: 15, low: 5 },
    key_entities: [
      { signature: "void damage(...)", fan_in: 47, kind: "function", brief: "..." },
      { signature: "void multi_hit(...)", fan_in: 12, kind: "function", brief: "..." }
    ],
    includes: ["src/include/merc.hh", "src/include/fight.hh"],
    included_by: ["src/act_move.cc", "src/magic.cc"]
  }
```

---

## 18. V2 — Hierarchical System Documentation

V1 is function-forward: every tool resolves, describes, and traverses individual code entities. V2 adds a **system-level narrative layer** drawn from the project's existing architectural documentation (`.ai/docs/components/*.md`, `.ai/docs/subsystems.md`) — 23 subsystem documents totaling ~4,500 lines of curated prose covering features, responsibilities, component breakdowns, implementation details, key files, system behaviors, and inter-system dependencies.

This prose captures knowledge that per-entity documentation cannot compose on its own: *"the combat system resolves attacks in a per-round cycle: hit check → damage calc → defensive rolls → elemental cascading → death processing with corpse creation"* is a system-level narrative, not something derivable from the brief of `damage()` or `raw_kill()`.

### 18.1 Why not in V1

The mapping between entities and systems is not mechanical:

- **Many-to-many relationships.** An entity like `act()` belongs to the `output` capability but participates in virtually every system. `affect_to_char()` is in the `affects` capability but is called by combat, magic, object effects, and MobProgs. Hardcoding a single `subsystem` foreign key would be lossy.
- **Capabilities ≠ systems.** The existing `capability` column groups entities by typed semantic responsibility (what they enable), not by architectural role (what system they serve). These are complementary but distinct taxonomies — a system like "Combat" spans capabilities (combat, affects, attributes, output, persistence), and a capability like `string_ops` is a utility used across all systems.
- **Curation needed.** Mechanically parsing section headings and keyword-matching entities to systems will produce noisy, overconfident mappings. The right approach is agent-assisted curation: walk the documents, use the doc server to research cross-references, and make intelligent decisions about where to split, merge, and connect.

V1's schema and tools are designed so that V2 can be added without reworking the entity-level services.

### 18.2 Schema additions (V2)

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
    embedding       VECTOR(4096),
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

Key design choices:
- **`entity_subsystem_links` is many-to-many** — `damage()` can be `core` to Combat and `supporting` to Magic. `act()` can be `utility` to everything that uses output formatting.
- **`role` is a closed enum** (`core`, `entry_point`, `supporting`, `utility`, `integration`) — free-text roles drift fast; a small controlled vocabulary keeps the curation consistent.
- **`link_source` and `confidence` are separate fields** — `link_source` records provenance (where the link came from: curated by agent, inferred by heuristic, or imported from a bulk process), while `confidence` records trust level (how reliable the mapping is). These are orthogonal: a curated link can be `medium` confidence if the agent was uncertain.
- **`evidence` JSONB** provides traceable provenance per link — which doc sections, capabilities, entry points, or source files motivated the link. Essential for long-term maintainability of curated mappings. Not verbose, just enough to answer "why is this entity linked here?"
- **`section_kind` on `subsystem_docs`** is a closed enum mechanically classified from heading text — enables retrieval strategies like "give me the overview first, then implementation details."
- **`is_overview` flag** identifies the canonical overview section per subsystem — `get_subsystem` always leads with this section, preventing chunk-soup results.
- **`subsystems` supports nesting** via `parent_id` — so "Dynamic Loot Generation" can be a child of "Object System" if the curation agent decides that's the right split.

### 18.3 V2 tools

| Tool | Description |
|------|-------------|
| `search` (enhanced) | Unified search across entity docs AND subsystem docs. Uses `SearchResult` envelope (§4.5) with `result_type` discriminator. `source` parameter filters to `entity`, `subsystem_doc`, or `all`. |
| `get_subsystem` | Full subsystem detail: overview section first (via `is_overview`), then other sections ordered by `section_kind` priority, curated entity links, dependency edges. Returns `SubsystemSummary` + sections. |
| `list_subsystems` | All subsystems with hierarchy, entity counts, and doc quality distribution. Returns `SubsystemSummary[]`. |
| `get_subsystem_context` | Given an entity, return a `ContextBundle` (§4.6) assembling: the entity's subsystem(s), relevant doc sections, capability framing, and related entities. |
| `get_subsystem_dependencies` | System-level dependency graph: what subsystems depend on/are depended on by a given subsystem. |
| `search_subsystem_docs` | Semantic + keyword search scoped to subsystem prose. Returns `SubsystemDocSummary[]`. |

#### Retrieval strategy for `get_subsystem_context`

When returning subsystem doc sections for an entity, the tool should **rerank** rather than dumping all linked sections:

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

This keeps mixed narrative/code context interpretable rather than opaque.

#### Design principle

V1 tools answer *"what is this code object?"* — V2 context tools answer *"what larger system narrative helps interpret it?"* These remain separate tool families; `get_subsystem_context` is additive, not a replacement for `get_entity`.

### 18.4 V2 build process

The V2 build has two distinct stages: **mechanical ingestion** and **agent-assisted curation**. Critically, the curation agent does not write directly to the database — it produces **versioned intermediate artifacts** that a build script ingests.

#### 18.4.1 Curation artifacts

The agent produces the following intermediate files (stored in `.ai/artifacts/v2/`):

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
- **Validatable** — lint rules can run before DB load (see §18.4.3)
- **Versionable** — git-tracked curation state with clear history

#### 18.4.2 Build pipeline

1. **Seed subsystems** (mechanical) — parse `subsystems.md` for the 23 named systems → `subsystems_seed.json`
2. **Chunk component docs** (mechanical) — split each `components/*.md` by `##`/`###` headings, classify `section_kind` from heading text, mark `is_overview` → `subsystem_doc_chunks.jsonl`
3. **Parse dependency declarations** (mechanical) — extract "Depends on" / "Depended on by" from `subsystems.md` → `subsystem_edges.json`
4. **Curate entity↔subsystem links** (agent-assisted) — the curation agent uses V1 tools (search, behavior slices, capability detail) to walk each subsystem, identify participating entities, assign roles and confidence, record evidence → `entity_subsystem_links.jsonl` + `curation_flags.jsonl`
5. **Validate** — run lint rules (§18.4.3) against the artifacts
6. **Ingest** — `build_v2_db.py` reads all artifacts, embeds doc chunks, populates Postgres tables

#### 18.4.3 Validation rules

Before DB ingestion, the following lint rules should pass:

- Every subsystem has at least one `is_overview` doc chunk
- Every `entity_id` in links references an existing entity in the V1 `entities` table
- Every `subsystem_id` in links and docs references a subsystem in `subsystems_seed.json`
- `entry_point` role links target only `kind = 'function'` entities
- `utility` role is used sparingly (warn if >30% of a subsystem's links are utility)
- Orphan entities report: entities with no subsystem link (informational, not blocking)
- Orphan subsystems report: subsystems with no entity links (likely a curation gap)

### 18.5 V1 forward-compatibility

V1 is structured so V2 requires **no changes to existing tables or tools**:

- The `entities` table has no `subsystem` column to migrate — entity↔subsystem is a separate join table.
- The `capability` column stays as-is; it and `subsystem_id` are independent classification axes.
- V1 tools continue to work unchanged. V2 tools are additive.
- The `search` tool's `SearchResult` envelope (§4.5) is designed for V2: `result_type` discriminates entity vs. subsystem results, so V2 unified search extends the shape without breaking it.
- The `EntitySummary` shape gains an optional `subsystems` field (list of `{id, name, role}`) populated from the join table when `include_subsystems=true` is passed. In V1 this parameter does not exist and the field is absent.
- V2 response shapes (`SubsystemSummary`, `SubsystemDocSummary`, `ContextBundle`) are pre-defined in §4.6 to prevent one-off blob shapes.

---

## 19. Other Future Extensions

- **Source-span cross-references** — attach call edges to exact source line ranges (using `codeline_refs` data from file compounds), enabling "damage() calls raw_kill() at line 342 in the death-handling branch" rather than just "damage calls raw_kill."
- **Guard/policy extraction** — mine common condition patterns (safe room checks, trust gates, NPC/player restrictions) from source and link them to entities.
- **Message template catalog** — parse `act()` format strings and `send_to_char` calls into structured message inventories.
- **Diff-aware impact analysis** — given a set of changed files, find all affected entities and their downstream dependents via the graph.
- **Incremental rebuild** — detect changed artifacts and update only affected database rows instead of full rebuild.
