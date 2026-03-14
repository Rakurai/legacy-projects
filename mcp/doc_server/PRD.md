# MCP Documentation Server — Product Requirements Document

## 1. Overview

### 1.1 Product

An MCP (Model Context Protocol) server that exposes the Legacy MUD codebase (~90 KLOC C++) as a searchable, analysis-capable knowledge store for AI coding assistants.

### 1.2 Purpose

AI assistants working on the Legacy codebase need structured access to pre-computed documentation artifacts — entity-level documentation, dependency graphs, embeddings, capability classifications, and source code — without parsing raw JSON or loading large files into context. This server provides that access through a standardized MCP tool/resource/prompt interface.

### 1.3 Users

- **AI coding assistants** (Claude, Copilot, Cursor, etc.) operating in development sessions against the Legacy codebase
- **Migration agents** that need factual and structural understanding of the legacy code to inform rewrite decisions
- **Developers** using AI-assisted tooling for codebase exploration and understanding

### 1.4 Scope boundary

The server exposes **factual, structural, and behavioral** information about the legacy codebase. It does **not** prescribe migration strategy, target architecture, implementation ordering, or architectural destination guesses. Those are concerns of consuming agents.

---

## 2. Goals and Non-Goals

### 2.1 Goals

1. **Entity lookup** — resolve entity names to full documentation records with source code, supporting disambiguation of ambiguous bare names.
2. **Hybrid search** — combine keyword (full-text) and semantic (embedding-based) search across entity documentation and source code.
3. **Graph exploration** — expose the dependency graph (calls, uses, inherits, includes, containment) for traversal at configurable depth.
4. **Behavior analysis** — derive behavioral views from the graph: call cones, side-effect markers, state touches, hotspot detection.
5. **Capability browsing** — expose the 30 capability groups with their typed dependencies, entry point mappings, and function membership.
6. **Graceful degradation** — function correctly when the embedding endpoint is unavailable, falling back to keyword search with explicit mode reporting.
7. **Deterministic serving** — all data is pre-computed and loaded from a database. No LLM inference at runtime. Responses are reproducible.
8. **V2 readiness** — schema and response shapes are designed so that hierarchical system documentation (subsystem narratives, entity↔subsystem links) can be added without reworking V1 tables or tools.

### 2.2 Non-Goals

1. Migration prescriptions (target surfaces, migration modes, wave ordering, chunk sequencing).
2. Runtime LLM inference or dynamic documentation generation.
3. Write access — the server is read-only; data changes require re-running the offline build script.
4. Multi-codebase support — this server serves one codebase (Legacy MUD).
5. Authentication or multi-tenancy.

---

## 3. Data Requirements

### 3.1 Source artifacts

The build script ingests the following pre-computed artifacts from `.ai/artifacts/`:

| Artifact | Format | Key content |
|----------|--------|-------------|
| Entity Database (`code_graph.json`) | JSON | 5,305 entities with identity, source locations, cross-references |
| Dependency Graph (`code_graph.gml`) | GML | ~5,300 entity nodes, ~25K typed edges (CALLS, USES, INHERITS, INCLUDES, CONTAINED_BY) |
| Document Database (`doc_db.json`) | JSON | 5,293 LLM-generated docs: brief, details, params, returns, rationale, usages |
| Embeddings Cache (`embeddings_cache.pkl`) | Pickle | 5,293 × 4,096 float32 L2-normalized vectors |
| Capability Definitions (`capability_defs.json`) | JSON | 30 groups typed as domain/policy/projection/infrastructure/utility |
| Capability Graph (`capability_graph.json`) | JSON | Typed inter-group dependency edges, entry point mappings |

### 3.2 Source code

The build script extracts entity source code from the C++ files on disk at build time and stores it in the database (~5 MB total). The MCP server does not read source files at runtime.

### 3.3 Database

PostgreSQL with pgvector extension. All artifacts are transformed and loaded by an offline build script (`build_mcp_db.py`). The server connects to this database at runtime.

### 3.4 In-memory graph

A NetworkX MultiDiGraph is constructed from the `edges` table at server startup (~25K rows). Used for BFS, path-finding, and call cone computation. Not persisted; rebuilt on every server start.

---

## 4. Functional Requirements

### FR-1: Entity Resolution

**FR-1.1** The server must support resolving entity names via a multi-stage pipeline: exact signature match → exact name match → prefix match → full-text search → semantic search.

**FR-1.2** Resolution must return a ranked candidate list with match metadata (match type, score, kind, file path, capability, brief, doc quality).

**FR-1.3** All tools that accept entity names (not just `resolve_entity`) must perform internal resolution and include a resolution envelope in the response: `resolution_status` (exact/ambiguous/not_found), `resolved_from`, `match_type`, `resolution_candidates`.

**FR-1.4** `resolve_entity` must support a `verbose` flag that includes per-stage pipeline details for each candidate.

### FR-2: Entity Detail

**FR-2.1** `get_entity` must return the full entity record: identity, documentation fields, source location, capability, doc quality, precomputed metrics (fan-in, fan-out, is_bridge, side-effect markers).

**FR-2.2** `get_entity` must support optional `include_code` (returns stored source text) and `include_neighbors` (returns direct graph neighbors with edge types).

**FR-2.3** `get_source_code` must resolve by name and return stored source code, file path, and line range. When `context_lines > 0`, surrounding lines are read from disk.

**FR-2.4** `list_file_entities` must list all entities in a source file as EntitySummary objects, filterable by kind.

**FR-2.5** `get_file_summary` must return aggregate file-level information: entity count by kind, capability distribution, doc quality distribution, top entities by fan-in, include graph.

### FR-3: Search

**FR-3.1** The `search` tool must combine pgvector cosine similarity and Postgres full-text search rank, with an exact name/signature boost.

**FR-3.2** Search results must use the `SearchResult` envelope (§4.5 of design doc): `result_type`, `score`, `search_mode`, `provenance`, and type-specific `summary`.

**FR-3.3** When the embedding endpoint is unavailable, search must fall back to keyword-only and report `search_mode: "keyword_fallback"`.

**FR-3.4** Search must support filtering by `kind`, `capability`, and `min_doc_quality`.

**FR-3.5** Search must accept a `source` parameter (defaulting to `entity`) that is V2-reserved for unified search across entity docs and subsystem docs.

### FR-4: Graph Exploration

**FR-4.1** `get_callers` and `get_callees` must support configurable depth (1–3) with deduplication (each entity appears once at shortest path depth).

**FR-4.2** `get_dependencies` must support filtering by relationship type and direction.

**FR-4.3** `get_class_hierarchy` must return inheritance trees in both directions.

**FR-4.4** `get_related_entities` must return all direct neighbors grouped by relationship type and direction.

**FR-4.5** `get_related_files` must return files related via INCLUDES edges, co-dependency, or shared entities.

**FR-4.6** All graph tools must include truncation metadata: `truncated`, `total_available`, `returned`.

### FR-5: Behavior Analysis

**FR-5.1** `get_behavior_slice` must compute a call cone via BFS from a seed function, returning direct callees and transitive call cone separately.

**FR-5.2** `get_behavior_slice` must report capabilities touched (with direct vs. transitive counts), globals used (direct vs. transitive), and side-effect markers (categorized and tagged with direct/transitive).

**FR-5.3** `get_state_touches` must separate direct uses/side-effects (depth=1) from transitive uses/side-effects (depth>1).

**FR-5.4** `get_hotspots` must support ranking by fan_in, fan_out, bridge (cross-capability), and underdocumented (low doc_quality), with kind and capability filters.

**FR-5.5** All behavior analysis tools must include provenance labels and confidence levels per data item.

### FR-6: Capability Tools

**FR-6.1** `list_capabilities` must return all 30 groups with type, description, function count, stability, and doc quality distribution.

**FR-6.2** `get_capability_detail` must return group definition, typed dependency edges, entry points, and optionally the full function list.

**FR-6.3** `list_entry_points` must support filtering by capability and name pattern.

**FR-6.4** `compare_capabilities` must show shared vs. unique dependencies and bridge entities for 2+ capability groups.

**FR-6.5** `get_entry_point_info` must report which capabilities the entry point exercises with direct/transitive counts.

### FR-7: Resources

**FR-7.1** The server must expose MCP resources at these URIs:
- `legacy://capabilities` — all capability groups
- `legacy://capability/{name}` — single group detail
- `legacy://entity/{entity_id}` — full entity record
- `legacy://file/{path}` — entities in a source file
- `legacy://stats` — summary statistics

### FR-8: Prompts

**FR-8.1** The server must expose canned MCP prompts for common workflows:
- `explain_entity` — resolve + full docs + neighbors + source
- `analyze_behavior` — behavior slice + capabilities + side effects
- `compare_entry_points` — shared vs. unique callees across entry points
- `explore_capability` — functions, dependencies, hotspots for a capability

### FR-9: Response Shape Consistency

**FR-9.1** All list-returning tools must use `EntitySummary` as the base shape.

**FR-9.2** All tools accepting entity names must include a resolution envelope.

**FR-9.3** All graph and list tools must include truncation metadata.

**FR-9.4** Derived/analysis tools must tag data items with provenance labels from the defined taxonomy.

**FR-9.5** V2-reserved response shapes (`SearchResult`, `SubsystemSummary`, `SubsystemDocSummary`, `ContextBundle`) must be defined in the implementation's model layer, even though they are unused in V1.

---

## 5. Non-Functional Requirements

### NFR-1: Performance

**NFR-1.1** Server startup (including NetworkX graph construction from ~25K edge rows) must complete in under 5 seconds.

**NFR-1.2** Single-entity lookup (`resolve_entity`, `get_entity`) must respond in under 100ms.

**NFR-1.3** Hybrid search must respond in under 500ms including embedding query.

**NFR-1.4** Graph traversal tools at depth ≤ 3 must respond in under 200ms.

**NFR-1.5** Behavior slice computation (BFS up to depth 5, max 200 cone entities) must respond in under 1 second.

### NFR-2: Reliability

**NFR-2.1** The server must function without the embedding endpoint, degrading search to keyword-only and reporting the degradation explicitly.

**NFR-2.2** Resolution of unknown entities must return `not_found` with nearest matches rather than raising errors.

**NFR-2.3** The build script must be idempotent — re-running it produces the same database state.

### NFR-3: Deployment

**NFR-3.1** The server must run via stdio transport for local MCP client integration (VS Code, Claude Desktop).

**NFR-3.2** PostgreSQL must run in a Docker container (`pgvector/pgvector:pg17`).

**NFR-3.3** All configuration must be via `.env` file: Postgres connection, embedding endpoint, project root, artifacts directory, log level.

**NFR-3.4** The server must be runnable via `uv run python -m server.server` from the project directory.

### NFR-4: Maintainability

**NFR-4.1** Database contents are rebuilt from artifacts by running `build_mcp_db.py`. No manual data entry.

**NFR-4.2** Full-text search vectors must use weighted tsvector composition (name=A, brief/details=B, definition=C, source_text=D).

**NFR-4.3** Wave ordering from capability artifacts must not be exposed in V1 tool responses to maintain the "no migration prescription" boundary.

### NFR-5: Observability

**NFR-5.1** The server must emit structured logs to stderr (separate from MCP protocol on stdout) with configurable log level via environment variable, defaulting to INFO.

**NFR-5.2** Logged events must include: tool invocations, database connection lifecycle, embedding service availability changes, errors, and performance metrics exceeding thresholds.

---

## 6. Build Script Requirements

### BR-1: Artifact Processing

**BR-1.1** The build script must load all six source artifacts using the existing `clustering/` Python modules (doxygen_parse, doxygen_graph, doc_db, openai_embeddings).

**BR-1.2** For each entity, the build script must merge entity metadata with its documentation record (1:1 join on compound_id + signature).

**BR-1.3** Source code must be extracted from disk at build time using entity source location data and stored in the `source_text` column.

**BR-1.4** The `definition_text` column must be populated with the C++ definition line.

### BR-2: Derived Data

**BR-2.1** `doc_quality` must be computed as high/medium/low based on doc_state + presence of details/params.

**BR-2.2** `fan_in` and `fan_out` must be computed from CALLS edges.

**BR-2.3** `is_bridge` must be computed by checking whether incoming vs. outgoing CALLS neighbors span different capability groups.

**BR-2.4** `side_effect_markers` must be computed by checking each function's CALLS edges against the curated side-effect function list.

**BR-2.5** `is_entry_point` must be set for `do_*`, `spell_*`, `spec_*` functions.

**BR-2.6** Weighted tsvector must be generated including name, brief, details, definition_text, and source_text.

### BR-3: Idempotency and Performance

**BR-3.1** The build script must drop and recreate tables on each run (or use `CREATE ... IF NOT EXISTS` with `TRUNCATE`).

**BR-3.2** The build script must complete processing of all artifacts and database population in under 5 minutes for ~5,300 entities.

---

## 7. Implementation Phasing

| Phase | Scope | Key deliverables |
|-------|-------|-----------------|
| 1 | Database + Core Lookup | `build_mcp_db.py`, `resolve_entity`, `get_entity`, `get_source_code`, `list_file_entities`, `get_file_summary`, resources |
| 2 | Search | Hybrid search with fallback mode, `search` tool |
| 3 | Graph Exploration | NetworkX loading, `get_callers`, `get_callees`, `get_dependencies`, `get_class_hierarchy`, `get_related_entities`, `get_related_files` |
| 4 | Behavior Analysis | `get_behavior_slice`, `get_state_touches`, `get_hotspots` |
| 5 | Capabilities + Prompts | `list_capabilities`, `get_capability_detail`, `list_entry_points`, `compare_capabilities`, `get_entry_point_info`, canned prompts |

Phases are sequential; each builds on the prior phase's infrastructure.

---

## 8. Acceptance Criteria

### Phase 1

- [ ] `build_mcp_db.py` populates all tables from artifacts without errors
- [ ] `resolve_entity("damage", kind="function")` returns ranked candidates including `void damage(Character *ch, ...)` from `src/fight.cc`
- [ ] `get_entity` returns full record with all documentation fields, metrics, and optional source code
- [ ] `list_file_entities("src/fight.cc")` returns all entities in that file
- [ ] `get_file_summary("src/fight.cc")` returns entity counts, capability breakdown, doc quality distribution
- [ ] Resources (`legacy://entity/*`, `legacy://file/*`, `legacy://stats`) return correct data

### Phase 2

- [ ] `search("poison spreading between characters")` returns relevant entities ranked by combined score
- [ ] With embedding endpoint down, search returns results with `search_mode: "keyword_fallback"`
- [ ] Filtering by kind, capability, and min_doc_quality works correctly

### Phase 3

- [ ] `get_callers("damage", depth=2)` returns transitive callers with path information
- [ ] `get_dependencies("Character", relationship="inherits")` returns class hierarchy
- [ ] All graph tools include truncation metadata when results are capped
- [ ] Resolution envelope present on all name-accepting graph tools

### Phase 4

- [ ] `get_behavior_slice("do_kill", max_depth=5)` returns call cone with direct/transitive separation
- [ ] Side-effect markers correctly categorized (messaging, persistence, state_mutation, scheduling)
- [ ] `get_hotspots(metric="bridge")` returns cross-capability entities
- [ ] Provenance labels present on all derived data items

### Phase 5

- [ ] `list_capabilities` returns all 30 groups with correct types
- [ ] `compare_capabilities(["combat", "magic"])` shows shared/unique dependencies
- [ ] `list_entry_points(capability="combat")` returns filtered entry points
- [ ] All four canned prompts produce coherent analysis output

---

## 9. Dependencies

### Runtime

| Dependency | Purpose |
|-----------|---------|
| PostgreSQL 17 + pgvector | Relational storage, full-text search, vector similarity |
| FastMCP | MCP server framework |
| asyncpg | Async Postgres driver |
| NetworkX | In-memory graph algorithms |
| OpenAI-compatible embedding endpoint | Query embedding for semantic search (optional — degrades gracefully) |

### Build-time

| Dependency | Purpose |
|-----------|---------|
| Existing `clustering/` Python modules | Artifact parsing (doxygen_parse, doxygen_graph, doc_db, openai_embeddings) |
| C++ source files on disk | Source code extraction at build time |

---

## 10. Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Embedding endpoint unavailable | Semantic search disabled | Explicit `keyword_fallback` mode; agents warned via `search_mode` field |
| Large call cones exceed response limits | Truncated behavior slices | `max_cone_size` parameter + truncation metadata in response |
| Entity resolution returns wrong entity | Agent proceeds with incorrect context | Two-step resolve/get workflow; ambiguity explicitly flagged in resolution envelope |
| Source code on disk out of sync with artifacts | Stale `source_text` in DB | Build script extracts source at build time; rebuild after code changes |
| tsvector code tokens dominate search ranking | Prose queries return irrelevant code matches | Weighted tsvector composition: name=A, brief/details=B, definition=C, source_text=D |

---

## 11. Future (V2)

V2 adds hierarchical system documentation: subsystem narratives from `.ai/docs/components/*.md`, entity↔subsystem mappings, and unified search across code entities and system-level prose. V2 is fully additive — no V1 tables or tools change. See DESIGN.md §18 for details.

V1 forward-compatibility measures:
- `SearchResult` envelope supports discriminated result types
- `SubsystemSummary`, `SubsystemDocSummary`, and `ContextBundle` shapes pre-defined
- `EntitySummary` supports opt-in `subsystems` field
- `search` tool accepts V2-reserved `source` parameter
- No `subsystem` column on `entities` — entity↔subsystem is a separate join table

---

## References

- [DESIGN.md](DESIGN.md) — full technical design document
- [artifacts.md](../../gen_docs/artifacts.md) — detailed artifact documentation
