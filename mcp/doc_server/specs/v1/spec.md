# Feature Specification: MCP Documentation Server


**Feature Branch**: `001-mcp-doc-server`
**Created**: 2026-03-14
**Status**: Implemented (V1)
**Input**: User description: "MCP server to serve documentation on this project"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Entity Lookup and Documentation Access (Priority: P1) 🎯 MVP

An AI assistant needs to understand what a specific function, class, or variable does in the Legacy MUD codebase. The assistant can search for "damage" and receive entity IDs in the results, then pass those IDs to `get_entity` for complete documentation including the function signature, parameter descriptions, return values, usage examples, source code location, and optionally the actual C++ source code. Entity IDs are deterministic (`{prefix}:{7hex}`) and stable across database rebuilds from the same artifacts.

**Why this priority**: Entity lookup is the foundational capability. Without reliable entity resolution and documentation retrieval, no other analysis can proceed. This is the MVP that makes the pre-computed documentation artifacts accessible to AI assistants.

**Independent Test**: Can be fully tested by querying known entities (e.g., `damage` function, `Character` class, `game_loop_unix` function) and verifying that returned documentation matches the pre-computed artifacts in `artifacts/generated_docs/`. Entity IDs are deterministic and stable across rebuilds. Success means an assistant can explore the codebase without parsing raw JSON files.

**Acceptance Scenarios**:

1. **Given** a search query with a unique match, **When** assistant searches, **Then** receive exact match with full documentation, source location, and metrics via entity_id
2. **Given** an ambiguous search query (e.g., "save" matches multiple functions), **When** assistant searches, **Then** receive ranked result list with file paths, signatures, and brief descriptions to disambiguate
3. **Given** an entity identifier, **When** assistant requests full entity details with source code, **Then** receive complete documentation plus actual C++ source text from database
4. **Given** a source file path, **When** assistant requests all entities in that file, **Then** receive list of all functions, classes, variables, and structs defined in that file with summaries
5. **Given** a source file path, **When** assistant requests file summary, **Then** receive aggregated statistics including entity counts by type and capability distribution

---

### User Story 2 - Documentation Search (Priority: P2)

An AI assistant working on poison damage mechanics needs to find all entities related to "poison spreading between characters". The assistant performs a multi-view hybrid search combining dual semantic similarity (doc + symbol embeddings), dual keyword matching (english + simple tsvectors), trigram fuzzy matching, and cross-encoder reranking. Results are ranked by cross-encoder relevance score with no per-query normalization.

**Why this priority**: Search enables discovery of relevant code without knowing exact names. This is essential for exploratory tasks like "find all inventory management code" or "locate authentication logic". Search builds on Phase 1 entity infrastructure and adds discovery capabilities.

**Independent Test**: Can be tested by issuing natural language queries (e.g., "poison damage over time", "player authentication", "room descriptions") and verifying that results include relevant entities with high cross-encoder scores. Test symbol queries by searching for C++ identifiers and verifying the correct entity ranks in top-3 via the symbol view.

**Acceptance Scenarios**:

1. **Given** a semantic query like "poison spreading between characters", **When** assistant performs hybrid search, **Then** receive ranked results scored by cross-encoder reranking across doc and symbol views
2. **Given** an exact entity name in search query, **When** assistant searches, **Then** that entity bypasses filtering and appears in results via exact-name priority tier
3. **Given** search filters for kind=function and capability=combat, **When** assistant searches, **Then** receive only functions from combat capability group
4. **Given** a C++ identifier query like `stc`, **When** assistant searches, **Then** the symbol view (simple tsvector, code-aware embedding) surfaces the matching entity above documentation-only matches


---

### User Story 3 - Dependency Graph Navigation (Priority: P3)

An AI assistant analyzing the `do_kill` command needs to understand what other functions it calls and which functions call it. The assistant can traverse the dependency graph bidirectionally at configurable depth (1-3 levels), discovering direct and transitive dependencies. The assistant can also explore class hierarchies to understand inheritance relationships, and identify related files through include relationships.

**Why this priority**: Graph navigation reveals call chains, inheritance structures, and module relationships. This is critical for understanding impact analysis ("what breaks if I change this?"), call flow tracing ("how does user input reach this function?"), and architectural understanding.

**Independent Test**: Can be tested by querying known entities with documented call relationships (e.g., `damage` calls `update_pos`, `do_kill` is called by `interpret`). Verify that returned call chains match edges in the pre-computed dependency graph (`code_graph.gml`). Success means an assistant can trace execution flows without reading source code.

**Acceptance Scenarios**:

1. **Given** a function name, **When** assistant requests callers at depth=2, **Then** receive both direct callers (depth 1) and their callers (depth 2) with path information
2. **Given** a function name, **When** assistant requests callees at depth=3, **Then** receive transitive call tree up to 3 levels deep with each entity appearing once at shortest path distance
3. **Given** a class name, **When** assistant requests class hierarchy, **Then** receive inheritance tree showing both parent classes and derived classes
4. **Given** a source file, **When** assistant requests related files, **Then** receive files connected via include relationships, co-dependency, or shared entity definitions
5. **Given** a large call tree exceeding result limit, **When** assistant requests dependencies, **Then** receive truncated results with metadata indicating total available count and what was returned


---

### User Story 4 - Behavioral Analysis (Priority: P4)

An AI assistant planning to migrate `do_kill` needs to understand its behavioral footprint: which other capabilities it exercises, what global state it touches, and what side effects it produces. The assistant requests a behavior slice and receives a call cone (all functions transitively called), capabilities touched (with direct vs. transitive counts), globals used, and categorized side-effect markers (messaging, persistence, state mutation, scheduling).

**Why this priority**: Behavioral analysis surfaces implicit dependencies and side effects that aren't obvious from signatures alone. This is essential for safe refactoring, migration planning, and blast radius estimation. It aggregates graph data into semantic categories meaningful for architectural decisions.

**Independent Test**: Can be tested by computing behavior slices for known entry points (e.g., `do_kill`, `spell_fireball`, `spec_cast_cleric`) and validating that call cones match BFS traversal of the dependency graph. Verify that side-effect markers are correctly categorized based on the curated side-effect function list. Success means an assistant can assess function complexity and risk without manual traversal.

**Acceptance Scenarios**:

1. **Given** an entry point function, **When** assistant requests behavior slice with max_depth=5, **Then** receive call cone with direct callees and full transitive closure separated
2. **Given** a behavior slice result, **When** reviewing capabilities touched, **Then** see which capability groups are exercised directly vs. transitively with function counts per group
3. **Given** a behavior slice result, **When** reviewing side effects, **Then** see effects categorized as messaging, persistence, state_mutation, or scheduling with direct/transitive labels
4. **Given** a function that touches global state, **When** assistant requests state touches, **Then** receive list of global variables used directly and transitively
5. **Given** behavior slice computation hitting max_cone_size limit, **When** assistant receives results, **Then** see truncation metadata and partial results with warning

---

### User Story 5 - Capability System and Entry Point Analysis (Priority: P5)

An AI assistant needs to understand the architectural organization of the codebase through capability groups. The assistant can list all 30 capabilities with their types (domain, policy, projection, infrastructure, utility), explore functions within a capability, examine typed dependencies between capabilities, and compare multiple capabilities to find shared vs. unique dependencies. The assistant can also identify entry points (commands, spells, special procedures) and see which capabilities each entry point exercises.

**Why this priority**: Capability analysis provides architectural context and higher-order organization. This enables assistants to understand subsystem boundaries, identify architectural hotspots, plan migrations by capability group, and reason about cross-cutting concerns. This is the final layer that ties all lower-level data into cohesive architectural understanding.

**Independent Test**: Can be tested by comparing returned capability definitions against `capability_defs.json` and capability relationships against `capability_graph.json`. Verify that entry point detection correctly identifies `do_*`, `spell_*`, and `spec_*` functions. Success means an assistant can navigate the codebase at the architectural level without reading individual files.

**Acceptance Scenarios**:

1. **Given** no parameters, **When** assistant lists capabilities, **Then** receive all 30 groups with types, descriptions, function counts, and stability indicators
2. **Given** a capability name, **When** assistant requests capability detail, **Then** receive group definition, typed dependency edges, entry points, and optionally full function list
3. **Given** two or more capability names, **When** assistant compares capabilities, **Then** receive shared dependencies, unique dependencies per group, and bridge entities connecting them
4. **Given** a filter for capability=combat, **When** assistant lists entry points, **Then** receive only entry points that directly exercise combat capability functions
5. **Given** an entry point function name, **When** assistant requests entry point info, **Then** receive which capabilities the entry point touches with direct vs. transitive counts

---

### Edge Cases

- **Unknown entity name**: System returns empty search results (not an MCP error)
- **Ambiguous entity name with 50+ candidates**: Results are truncated to top K candidates ranked by cross-encoder score; no pagination
- **Circular dependencies in call graph**: BFS traversal with visited set prevents infinite loops; each entity appears once at shortest path distance
- **Embedding provider or cross-encoder unavailable at startup**: Server fails fast with clear error. There is no keyword-only degraded mode.
- **Stale embedding artifact**: Source documentation has changed but artifact file still exists. System loads stale artifact without warning. Developer must delete artifact to trigger regeneration.
- **Corrupt embedding artifact**: Artifact file exists but is corrupted (partial write, invalid pickle). Build fails with clear error rather than loading garbage vectors.
- **First-run model download**: Local ONNX model files not yet cached on machine. System logs that download is occurring; handles download failures with clear error.
- **Embedding dimension mismatch at startup**: Configured dimension does not match provider's actual output. Server fails fast with clear error.
- **Entity with no documentation and no meaningful name**: May not survive filtering — acceptable; these entities are not useful search targets
- **Query contains both identifier tokens and prose**: Both symbol and doc channels contribute candidates; the cross-encoder ranks based on the best-matching view
- **Containment graph has incomplete paths**: Parse `definition_text` for `::` scoping as secondary source; if neither yields a scope, `qualified_name` = bare name
- **Very large behavior slice (>1000 functions)**: Computation stops at configurable `max_cone_size` (default 200), returns partial results with truncation warning
- **Entity exists in database but source file deleted from disk**: Source code retrieval returns stored source_text from database (extracted at build time)
- **Source code on disk has changed since database build**: Stored source_text becomes stale; documentation remains valid. Users must rebuild database after code changes.
- **Graph traversal depth exceeds reasonable limit**: Depth is capped at maximum 5 for behavior analysis, 3 for general traversal to prevent performance degradation
- **Entity has no documentation (brief is null)**: System returns entity with empty details/rationale fields; agents use `brief is not null` as the practical quality signal. Entity still receives a minimal embedding from kind+name+signature if doc-less.
- **Declaration/definition split entities**: Build pipeline deduplicates by grouping on `entity.id.member` hash, selecting the definition fragment (with body) as survivor, and merging documentation from declaration. Final database contains one record per logical entity.
- **Multiple files define entities with same compound_id**: Deterministic IDs from signature_map keys ensure unique identification
- **Database connection failure**: System returns MCP error (hard failure) rather than successful response; client must handle connection retry or alert user
- **Invalid tool parameters** (e.g., depth=-1, invalid entity_id format): System returns MCP error with validation message rather than successful response with error indicator
- **Build script encounters missing artifact file**: Build process fails with clear error message indicating which artifact is missing and expected path
- **Build script encounters malformed artifact** (invalid JSON, corrupt pickle): Build process fails with validation error and line/byte position if applicable
- **Build script encounters entity with invalid source location**: Build raises `BuildError` if line range exceeds file length (stale code graph). Entity with missing source file is logged as warning and proceeds with source_text=NULL.

## Requirements *(mandatory)*

### Functional Requirements

#### Entity Resolution & Lookup

- **FR-001**: System MUST support entity discovery through `search` tool with multi-stage pipeline: exact signature match → exact name match → prefix match → full-text search → semantic search
- **FR-002**: System MUST return ranked results with match metadata including match type, score, kind, file path, capability, and brief
- **FR-003**: System MUST support retrieving full entity records by `entity_id` (required parameter) including identity, documentation fields, source location, capability, metrics, and optionally source code

#### Search

- **FR-007**: System MUST perform multi-view hybrid search using five parallel candidate retrieval channels: doc semantic (pgvector cosine on `doc_embedding`), symbol semantic (pgvector cosine on `symbol_embedding`), doc keyword (`ts_rank` on `doc_search_vector`), symbol keyword (`ts_rank` on `symbol_search_vector`), and trigram (`pg_trgm` similarity on `symbol_searchable`). Results are ranked by cross-encoder reranking with no per-query score normalization.
- **FR-008**: Entity table MUST use dual embedding columns (`doc_embedding`, `symbol_embedding`) and dual tsvector columns (`doc_search_vector` with english dictionary, `symbol_search_vector` with simple dictionary). Entity table MUST include `symbol_searchable` TEXT column for trigram indexing and `qualified_name` TEXT column for C++ scoping.
- **FR-009**: System MUST support search filtering by entity kind and capability group
- **FR-010**: System MUST return search results using SearchResult envelope with result_type, score, winning_view, winning_score, and losing_score
- **FR-011**: Cross-encoder reranking MUST produce the final ranking. Per-candidate score = max(doc_ce_score, symbol_ce_score) for sentence-like queries, with query-shape-aware view selection for symbol-like queries. No per-query normalization.
- **FR-012**: Search tool MUST accept a `source` parameter (defaulting to `entity`) that is V2-reserved for unified search across entity docs and subsystem docs; in V1 only `entity` is functional

#### Graph Exploration

- **FR-013**: System MUST support caller and callee traversal at configurable depth (1-3 levels) with deduplication ensuring each entity appears once at shortest path
- **FR-014**: System MUST support dependency filtering by relationship type (calls, uses, inherits, includes, containment) and direction (incoming/outgoing)
- **FR-015**: System MUST provide class hierarchy exploration in both directions (parent classes and derived classes)
- **FR-017**: System MUST include truncation metadata in all graph and list results showing truncated status, total_available count, and returned count; system does NOT support pagination (results are hard-truncated to top N, clients must refine queries to access different result subsets)

#### Behavior Analysis

- **FR-018**: System MUST compute call cones via breadth-first search from seed functions, separating direct callees from transitive cone
- **FR-019**: System MUST report capabilities touched with direct vs. transitive counts and function lists per capability
- **FR-020**: System MUST report global variables used with direct vs. transitive access indicators

#### Capability System

- **FR-023**: System MUST list all capability groups with type, description, function count, and stability indicator
- **FR-024**: System MUST provide detailed capability information including group definition, typed dependency edges, entry points, and optionally full function list
- **FR-025**: System MUST support comparing multiple capabilities showing shared dependencies, unique dependencies, and bridge entities
- **FR-026**: System MUST list entry points (do_*, spell_*, spec_* functions) filterable by name pattern
- **FR-027**: System MUST report which capabilities an entry point exercises with direct vs. transitive function counts

#### Resources & Prompts

- **FR-028**: System MUST expose MCP resources at URIs: legacy://capabilities, legacy://capability/{name}, legacy://entity/{entity_id}, legacy://file/{path}, legacy://stats
- **FR-029**: System MUST provide canned MCP prompts for common workflows: explain_entity, analyze_behavior, compare_entry_points, explore_capability

#### Build Script & Data Pipeline

- **FR-030**: Build script MUST ingest all source artifacts from the configured artifacts directory: entity database (code_graph.json), dependency graph (code_graph.gml), per-compound documentation files (generated_docs/*.json), capability definitions (capability_defs.json), and capability graph (capability_graph.json). Embedding artifacts are optional — generated on demand when a provider is configured. `doc_db.json` and `signature_map.json` are no longer required.
- **FR-031**: Build script MUST load the dependency graph in two phases: first loading raw GML node IDs (via `load_graph_node_ids`) before entity merging to identify which compounds are graph-referenced, then loading full graph edges (via `load_graph_edges`) after entity ID assignment for metric computation.
- **FR-032**: Build script MUST deduplicate declaration/definition split entities by grouping on `entity.id.member` (Doxygen's authoritative member hash), selecting the definition fragment (where `entity.body is not None`) as the survivor, and merging documentation from declaration fragments onto the survivor when needed. Entities without a member hash (pure compounds) pass through as single entities. The signature map is computed on-the-fly from `EntityDatabase` and `DocumentDB` at build time — `signature_map.json` is no longer loaded as an artifact. Entity models, document models, and graph loader are imported from `legacy_common` (not reimplemented in `build_helpers/`).
- **FR-033**: Build script MUST extract source code from disk at build time using entity source location data and store in database source_text column. Build MUST raise `BuildError` if body-located entities exist but zero source texts are extracted (indicates `PROJECT_ROOT` misconfiguration). Build MUST raise `BuildError` if a source file exists but the line range is invalid (indicates stale code graph). Individual file-not-found or encoding errors MUST be logged as warnings but MUST NOT fail the build.
- **FR-034**: Build script MUST extract C++ definition lines and store in database definition_text column
- **FR-036**: Build script MUST compute fan_in and fan_out metrics by counting CALLS edges in dependency graph
- **FR-037**: Build script MUST compute is_bridge flag by checking whether function's incoming vs. outgoing CALLS neighbors span different capability groups
- **FR-039**: Build script MUST set is_entry_point flag for functions matching patterns: do_*, spell_*, spec_*
- **FR-040**: Build script MUST generate dual weighted tsvectors: `doc_search_vector` (english dictionary: name=A, brief+details=B, notes+rationale+params+returns=C) and `symbol_search_vector` (simple dictionary: name=A, qualified_name+signature=B, definition_text=C)
- **FR-041**: Build script MUST be idempotent, producing identical database state on repeated runs from same input artifacts
- **FR-042**: Build script MUST complete processing of all artifacts and database population in under 5 minutes for ~5,300 entities

#### Data Quality & Consistency

- **FR-043**: Server MUST serve only pre-computed data loaded from database; no runtime LLM inference
- **FR-044**: Server MUST provide responses that are deterministic and reproducible given identical database state
- **FR-046**: Server MUST maintain consistency between documentation records and source code through build-time extraction performed by build script; consistency is guaranteed only at build time, and users must rebuild the database after code changes (per assumption A-006)

#### Error Handling

- **FR-047**: Server MUST return MCP errors for hard failures including database connectivity errors, invalid tool parameters, malformed requests, or internal server errors
- **FR-048**: Server MUST return successful MCP responses with explicit status indicators for partial results including result truncation (truncated: true) or empty search results

#### Observability

- **FR-049**: Server MUST emit structured logs to stderr in JSON or key-value format including tool invocations, database query execution, performance metrics, errors, and warnings
- **FR-050**: Server MUST support configurable log levels (DEBUG, INFO, WARNING, ERROR) via environment variable, defaulting to INFO level
- **FR-051**: Server MUST log at INFO level: server startup/shutdown, tool invocations with parameters, database connection events, embedding service availability changes, and performance metrics exceeding thresholds
- **FR-052**: Server MUST log at ERROR level: database connection failures, invalid tool parameters, internal errors, and any conditions resulting in MCP error responses

#### V2 Forward-Compatibility

- **FR-053**: Implementation MUST define V2-reserved response shapes (SubsystemSummary, SubsystemDocSummary, ContextBundle) in the model layer, even though they are unused by V1 tools, to prevent response-shape drift when V2 lands
- **FR-054**: V1 tools MUST NOT expose wave ordering data from capability artifacts in any tool response, maintaining the boundary between factual documentation and migration prescription


#### Build Script: Capability Mapping & Data Corrections

- **FR-055**: Build script MUST assign capability group names to entities by building a name→capability mapping from `capability_graph.json` → `capabilities[name].members[].name` (approximately 848 assignments out of ~5,305 entities). The `doc.system` field is not used for capability assignment.
- **FR-056**: Build script MUST read capability descriptions from the `"desc"` key in `capability_defs.json` (not `"description"`)
- **FR-057**: Build script MUST compute `function_count` from `capability_graph.json` → `capabilities[name].function_count` (not from a `"functions"` key in capability_defs.json)
- **FR-058**: Build script MUST parse capability edges from `capability_graph.json` → `"dependencies"` as a nested dict (`source_cap → target_cap → {edge_type, call_count, in_dag}`), not from an `"edges"` flat list
- **FR-060**: Build script MUST assign entity capabilities before computing bridge flags (pipeline ordering dependency)
- **FR-061**: Build script MUST create all secondary indexes using the same engine/connection that creates tables, using `CREATE INDEX IF NOT EXISTS` for idempotent re-runs (14 secondary indexes required)


#### Embedding Provider

- **FR-062**: System MUST support a configurable embedding provider with at least two modes: "local" (bundled, no external service) and "hosted" (OpenAI-compatible endpoint), selectable via `EMBEDDING_PROVIDER` environment variable. Embedding is required — there is no keyword-only mode.
- **FR-063**: `EMBEDDING_PROVIDER` MUST be set to `"local"` or `"hosted"`. Server MUST fail fast at startup if it is not configured. There is no "no provider" mode.
- **FR-064**: When configured for local mode, the system MUST use dual embedding models: BAAI/bge-base-en-v1.5 for doc embeddings and jinaai/jina-embeddings-v2-base-code for symbol embeddings (both 768-dim). A cross-encoder model (Xenova/ms-marco-MiniLM-L-12-v2) MUST be loaded for reranking. All model names are configurable via environment variables.
- **FR-065**: The embedding cache MUST use type-specific artifact files named `embed_cache_{model_slug}_{dim}_{type}.pkl` (pickle format), where `{type}` is a string identifier for the embedding package (e.g., "doc", "symbol", "usages"). Each type has its own independent file so invalidating one type does not affect others.
- **FR-066**: The database build process MUST synchronize each embedding cache incrementally: load the existing cache file for that type if it exists; generate embeddings only for keys missing from the cache; prune keys present in the cache but absent from the current data set; save the updated cache file. Generation is skipped entirely when no keys are missing.
- **FR-066a**: The embedding cache synchronization mechanism MUST be schema-agnostic, operating on generic key-text-embedding mappings without knowledge of the specific data type.
- **FR-066b**: When loading entity embeddings, if a legacy cache file without type suffix exists but no typed suffix file exists, the build MUST log a warning. The build MUST NOT automatically migrate or fall back to legacy naming.
- **FR-067**: The database schema MUST use a vector column dimension that matches the configured embedding provider's output dimension (via `EMBEDDING_DIMENSION` env var, default 768), not a hardcoded value.
- **FR-068**: Doc embedding text MUST be assembled using labeled prose fields: `BRIEF: ...`, `DETAILS: ...`, `PARAMS: ...`, `RETURNS: ...`, `NOTES: ...`, `RATIONALE: ...` (omitting null/empty fields, falling back to bare name when all are empty). Symbol embedding text MUST be the qualified scoped signature in natural C++ form.
- **FR-069**: The runtime query embedding pathway MUST use the same provider and model that generated the stored vectors, ensuring dimensional and semantic consistency. Doc queries use the doc embedding model; symbol queries use the symbol embedding model.
- **FR-070**: The old hardcoded `embeddings_cache.pkl` artifact MUST NOT be required by build validation.
- **FR-071**: The system MUST validate at startup that the configured vector dimension matches the embedding provider's actual output dimension and fail fast with a clear error if they disagree.
- **FR-072**: Query-time embedding MUST NOT block the server's event loop. Server call sites MUST use `await provider.aembed(query)`. The provider owns the async surface.
- **FR-073**: Entities without documentation MUST receive a doc embedding from a minimal text (bare name). All entities MUST receive a symbol embedding from their qualified name or signature.


#### Deterministic Entity IDs

- **FR-074**: Build pipeline MUST compute entity IDs as `{prefix}:{sha256(canonical_key)[:7]}` where the canonical key is the signature_map tuple `(compound_id, signature_or_name)`
- **FR-075**: Prefix MUST be determined by entity kind: `fn` for function/define, `var` for variable, `cls` for class/struct, `file` for file, `sym` for everything else
- **FR-076**: Build pipeline MUST halt with a clear error on any ID collision (two different canonical keys producing the same prefixed hash)
- **FR-077**: `resolve_entity` tool MUST be removed from the MCP tool catalog (total tools: 20 → 19)
- **FR-078**: All tools that previously accepted `entity_id` and `signature` parameters MUST accept only `entity_id` as a required parameter
- **FR-079**: `ResolutionEnvelope` MUST be removed from all tool response shapes
- **FR-080**: `search` tool MUST remove the `min_doc_quality` parameter
- **FR-081**: `list_capabilities` and `get_capability_detail` responses MUST remove the `doc_quality_dist` field
- **FR-082**: `EntitySummary` MUST remove `doc_state` and `doc_quality` fields
- **FR-083**: `EntityDetail` MUST remove `compound_id`, `member_id`, `doc_state`, and `doc_quality` fields
- **FR-084**: `search` is the sole path from human-readable text to entity IDs — no other tool performs name-to-ID resolution
- **FR-085**: Schema MUST remove columns: `compound_id`, `member_id`, `doc_state`, `doc_quality` from the entities table
- **FR-086**: Schema MUST remove column: `doc_quality_dist` from the capabilities table
- **FR-087**: Build pipeline MUST carry all documentation fields (brief, details, params, returns, notes, rationale, usages) from doc_db through the merge without loss

#### Build Script: Data Completeness

- **FR-088**: Build pipeline MUST store `params` as `NULL` when the value is `None`, `{}`, or absent — not as an empty JSON object. The `JSONB` column MUST use `none_as_null=True`.
- **FR-089**: Build pipeline MUST generate embeddings for entities without a `Document` by constructing a minimal Doxygen-formatted text from `kind`, `name`, `signature`, and `file_path` — including structural compounds (file, dir, namespace). The tag mapping extends `Document.to_doxygen()` with structural compound tags (file, dir, typedef, union).
- **FR-090**: Build pipeline MUST log a structured summary after source extraction: body_located, extracted, failed, skipped, success_rate
- **FR-091**: Build pipeline MUST log a structured summary after embedding generation: doc_embeds, minimal_embeds, no_embed, coverage%

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: AI assistants can resolve any entity name via search and receive correct documentation in under 100 milliseconds for single-entity lookup
- **SC-002**: Hybrid search queries return relevant results ranked by combined semantic and keyword score in under 500 milliseconds including embedding query
- **SC-003**: Graph traversal at depth 3 completes and returns results in under 200 milliseconds for typical entities (fan-in/fan-out < 50)
- **SC-004**: Behavior slice computation for entry points completes in under 1 second when call cone contains fewer than 200 functions
- **SC-005**: Server starts and loads dependency graph (25,000 edges) into memory in under 5 seconds
- **SC-006**: Embedding provider and cross-encoder model are required. Server refuses to start when `EMBEDDING_PROVIDER` is not configured.
- **SC-007**: Ambiguous search queries return ranked results with sufficient context for human or AI to select correct match without additional queries
- **SC-009**: Build script processes all artifacts (5,293 entities, 25,000 edges, 30 capabilities) and populates database in under 5 minutes
- **SC-010**: Build script produces identical database state on repeated runs from same input artifacts (idempotent operation)
- **SC-011**: All derived metrics (fan_in, fan_out, is_bridge) are correctly computed from source artifacts and match validation samples
- **SC-012**: Source code extraction captures ≥90% of entities with valid body locations, storing complete function/class definitions in database. Build fails with `BuildError` on zero extraction or invalid line ranges.
- **SC-013**: Full-text search tsvector enables relevant keyword matches for natural language queries against entity documentation and source code
- **SC-015**: After a full build, approximately 848 entities have non-null capability assignment (from capability_graph.json members)
- **SC-016**: After a full build, at least 10 entities are flagged as bridge functions (is_bridge=true)
- **SC-017**: After a full build, all 30 capabilities have function_count > 0 and non-empty descriptions
- **SC-018**: After a full build, capability_edges table contains exactly 200 rows
- **SC-019**: After a full build, at least 19 database indexes exist (5 PKs + 14 secondary)
- **SC-020**: A developer can build the database and run semantic searches with zero external service dependencies by configuring local embedding mode
- **SC-021**: Embedding artifact generation for the full entity set completes within 5 minutes on a standard development machine
- **SC-022**: Query-time embedding adds less than 100ms of latency to search requests when using the local provider

- **SC-023**: Two consecutive builds from the same artifacts produce identical entity ID sets (100% determinism)
- **SC-024**: Zero ID collisions across ~5,305 entities (enforced by build-time collision detection)
- **SC-025**: After a full build, at least 95% of doc_db.json entries with non-empty brief have non-null brief in the database
- **SC-026**: An agent can complete search → get_entity → get_callers → get_behavior_slice using only entity_ids, with zero signature-based lookups
- **SC-027**: No tool in the MCP catalog accepts a `signature` parameter for entity lookup (15 tools total)

- **SC-028**: After a successful build, ≥95% of all entities have non-null `doc_embedding` and `symbol_embedding` in the database
- **SC-029**: After a successful build, `params IS NOT NULL` count matches meaningful parameter content (~1,800–2,100, not ~5,055)
- **SC-030**: Build with invalid `PROJECT_ROOT` exits with `BuildError` within the source extraction stage
- **SC-031**: Build with valid `PROJECT_ROOT` logs a structured extraction summary (body_located, extracted, failed, skipped, success_rate)
- **SC-032**: Build logs an embedding generation summary per type (doc, symbol, usages)
- **SC-033**: After each build, embedding cache log shows per-type sync status (added, pruned, or "up to date") for doc, symbol, and usages types

#### Multi-View Search Quality

- **SC-034**: Searching for a known bare name (`damage`, `stc`, `do_look`) returns that entity in the top-5 results
- **SC-035**: Searching for a C++ identifier (`Character`, `PLR_COLOR2`) returns the correct entity via symbol view, not entities whose documentation merely contains the word
- **SC-036**: A natural language query ("send formatted text to character output buffer") returns relevant entities ranked by cross-encoder score
- **SC-037**: A nonsense query ("xyzzy foobar baz") returns zero or near-zero results (CE model limitation may allow 1 marginal result)
- **SC-038**: No returned result has a score produced by per-query normalization — all scores come from cross-encoder reranking
- **SC-039**: After a full build, ≥90% of function entities have a non-empty `qualified_name` derived from the containment graph, using only namespace/class/struct/group as scoping containers (no file/directory paths)
- **SC-040**: Qualified names use C++ scoping containers only: `conn::GetSexState`, not `src/include/conn::State.hh::conn::GetSexState`

### Assumptions

- **A-001**: Pre-computed artifacts in `artifacts/` are complete, up-to-date, and internally consistent at time of database build; build script is run offline before server startup and not during server operation
- **A-002**: PostgreSQL database with pgvector extension is available and accessible via connection string in `.env` file
- **A-003**: Embedding is required via a configurable provider: local (bundled ONNX models) or hosted (OpenAI-compatible endpoint). There is no keyword-only mode. Doc embedding uses BAAI/bge-base-en-v1.5; symbol embedding uses jinaai/jina-embeddings-v2-base-code; cross-encoder reranking uses Xenova/ms-marco-MiniLM-L-12-v2. All models locked after empirical evaluation.
- **A-004**: NetworkX in-memory graph constructed from ~25,000 edges fits in available memory (estimated ~100-200 MB) and is read-only after initial load (no thread safety concerns for concurrent reads)
- **A-005**: MCP client (VS Code, Claude Desktop) supports stdio transport and can invoke MCP tools/resources/prompts
- **A-006**: Source code files on disk match artifacts at database build time; users rebuild database after code changes
- **A-007**: The signature map is now computed on-the-fly at build time from the loaded `EntityDatabase` and `DocumentDB`. `signature_map.json` is no longer a required artifact.
- **A-008**: Capability definitions, dependency edges, and function membership lists in `capability_defs.json` and `capability_graph.json` are authoritative
- **A-009**: Dual full-text search tsvectors provide complementary ranking: `doc_search_vector` (english dictionary, prose-oriented) and `symbol_search_vector` (simple dictionary, identifier-oriented). Combined with cross-encoder reranking, this produces high-quality results for both natural language and symbol queries.
- **A-010**: BFS traversal with visited set and configurable depth limits prevents performance degradation from circular dependencies or deep call chains
- **A-011**: The `capability_graph.json` member names match entity names in the entity database exactly. The `doc.system` field remains unused for capability assignment.
- **A-012**: The BAAI/bge-base-en-v1.5 model produces 768-dimensional vectors. This is verified at runtime; if a future model version changes dimensions, the config must be updated accordingly.
- **A-013**: Embedding ~5,300 entities locally takes approximately 1–3 minutes on a modern CPU. Single-query local embedding takes approximately 5–20ms. Both are acceptable for their respective use cases.
- **A-014**: After switching embedding providers, the developer is responsible for re-running the database build. The server does not detect dimension mismatches between the configured provider and vectors already in the database.
- **A-015**: The ONNX model files are cached locally by the FastEmbed library (in `~/.cache/fastembed/`) after initial download. First run requires internet access; subsequent runs are fully offline.

## Clarifications

### Session 2026-03-14

- Q: Server process lifecycle - single request per process vs. long-lived server? → A: Long-lived server handling multiple sequential requests (server starts once, handles multiple tool invocations over stdio until client disconnects)
- Q: Result pagination strategy - hard truncation vs. pagination support? → A: Hard truncation with metadata only (no pagination - tools return top N results with truncation indicator, no mechanism to fetch additional results)
- Q: Error response format - when to use MCP errors vs. success with error indicators? → A: Structured MCP errors for failures, success payloads with status fields for degraded/partial results (database errors and invalid parameters return MCP errors; degraded states like embedding service down or truncated results return success with explicit status indicators)
- Q: Request concurrency model - sequential vs. concurrent processing? → A: Async/event-loop based concurrency (server uses async/await for I/O-bound operations like database queries and embedding requests; NetworkX graph is read-only and accessed without locking)
- Q: Logging strategy for server operations and diagnostics? → A: Structured logging to stderr with configurable levels (INFO by default - JSON or key-value format logs including tool invocations, database queries, performance metrics, errors; level controlled via environment variable)

## Deployment Context *(optional)*

Long-lived stdio process on developer machines. Async I/O (database, embedding) with read-only in-memory graph. Configuration via `.env`. See MODEL.md for schema, Appendix B for embedding config, and PRD.md NFR-3 for deployment requirements.
