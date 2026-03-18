# Feature Specification: MCP Documentation Server

<!-- Canonical V1 specification. Incorporates changes from 003-fix-mcp-db-build, 004-local-fastembed-provider, 005-mcp-key-issue, 006-legacy-common-integration, and 007-data-completeness. -->
**Feature Branch**: `001-mcp-doc-server`
**Created**: 2026-03-14
**Status**: Implemented (V1)
**Input**: User description: "MCP server to serve documentation on this project"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Entity Lookup and Documentation Access (Priority: P1) 🎯 MVP

An AI assistant needs to understand what a specific function, class, or variable does in the Legacy MUD codebase. The assistant can search for "damage" and receive entity IDs in the results, then pass those IDs to `get_entity` for complete documentation including the function signature, parameter descriptions, return values, usage examples, source code location, and optionally the actual C++ source code. Entity IDs are deterministic (`{prefix}:{7hex}`) and stable across database rebuilds from the same artifacts. <!-- spec 005: resolve_entity retired; search is the sole discovery path; entity_id is deterministic -->

**Why this priority**: Entity lookup is the foundational capability. Without reliable entity resolution and documentation retrieval, no other analysis can proceed. This is the MVP that makes the pre-computed documentation artifacts accessible to AI assistants.

**Independent Test**: Can be fully tested by querying known entities (e.g., `damage` function, `Character` class, `game_loop_unix` function) and verifying that returned documentation matches the pre-computed artifacts in `artifacts/generated_docs/`. Entity IDs are deterministic and stable across rebuilds. Success means an assistant can explore the codebase without parsing raw JSON files. <!-- spec 005: deterministic IDs --> <!-- spec 006: doc source is generated_docs/, not doc_db.json -->

**Acceptance Scenarios**:

1. **Given** a search query with a unique match, **When** assistant searches, **Then** receive exact match with full documentation, source location, and metrics via entity_id <!-- spec 005: search replaces resolve_entity -->
2. **Given** an ambiguous search query (e.g., "save" matches multiple functions), **When** assistant searches, **Then** receive ranked result list with file paths, signatures, and brief descriptions to disambiguate
3. **Given** an entity identifier, **When** assistant requests full entity details with source code, **Then** receive complete documentation plus actual C++ source text from database
4. **Given** a source file path, **When** assistant requests all entities in that file, **Then** receive list of all functions, classes, variables, and structs defined in that file with summaries
5. **Given** a source file path, **When** assistant requests file summary, **Then** receive aggregated statistics including entity counts by type and capability distribution <!-- spec 005: doc_quality_distribution removed from file summary -->

---

### User Story 2 - Documentation Search (Priority: P2)

An AI assistant working on poison damage mechanics needs to find all entities related to "poison spreading between characters". The assistant performs a hybrid search combining semantic similarity (using embeddings) with keyword matching, receiving ranked results that include both exact name matches and conceptually related entities. When the embedding service is unavailable, search gracefully degrades to keyword-only mode and explicitly reports the degraded state.

**Why this priority**: Search enables discovery of relevant code without knowing exact names. This is essential for exploratory tasks like "find all inventory management code" or "locate authentication logic". Search builds on Phase 1 entity infrastructure and adds discovery capabilities.

**Independent Test**: Can be tested by issuing natural language queries (e.g., "poison damage over time", "player authentication", "room descriptions") and verifying that results include relevant entities with high scores. Test fallback mode by omitting the embedding provider configuration (or setting `EMBEDDING_PROVIDER` to none) and confirming keyword-only results are returned with explicit fallback status. <!-- Updated per spec 004: test fallback by provider config, not endpoint disabling -->

**Acceptance Scenarios**:

1. **Given** a semantic query like "poison spreading between characters", **When** assistant performs hybrid search, **Then** receive ranked results combining embedding similarity and keyword matches with normalized scores
2. **Given** an exact entity name in search query, **When** assistant searches, **Then** that entity receives a score boost and appears at top of results
3. **Given** search filters for kind=function and capability=combat, **When** assistant searches, **Then** receive only functions from combat capability group
4. **Given** embedding service is unavailable, **When** assistant searches, **Then** receive keyword-only results with search_mode="keyword_fallback" explicitly indicated
<!-- spec 005: Acceptance scenario 5 (min_doc_quality filter) removed; min_doc_quality parameter retired -->

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
<!-- spec 005: resolution envelope no longer present on graph tools; tools accept only entity_id -->

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

1. **Given** no parameters, **When** assistant lists capabilities, **Then** receive all 30 groups with types, descriptions, function counts, and stability indicators <!-- spec 005: doc_quality_dist removed from capability responses -->
2. **Given** a capability name, **When** assistant requests capability detail, **Then** receive group definition, typed dependency edges, entry points, and optionally full function list
3. **Given** two or more capability names, **When** assistant compares capabilities, **Then** receive shared dependencies, unique dependencies per group, and bridge entities connecting them
4. **Given** a filter for capability=combat, **When** assistant lists entry points, **Then** receive only entry points that directly exercise combat capability functions
5. **Given** an entry point function name, **When** assistant requests entry point info, **Then** receive which capabilities the entry point touches with direct vs. transitive counts

---

### Edge Cases

- **Unknown entity name**: System returns empty search results with `search_mode` indicator (not an MCP error) <!-- spec 005: resolve_entity retired; search handles discovery -->
- **Ambiguous entity name with 50+ candidates**: Results are truncated to top 20 candidates ranked by score, with truncation metadata indicating total available; no pagination mechanism exists, users must refine query to see different results
- **Circular dependencies in call graph**: BFS traversal with visited set prevents infinite loops; each entity appears once at shortest path distance
- **Embedding service down during search**: System returns successful MCP response with keyword-only results and sets `search_mode: "keyword_fallback"` to indicate degraded state (not an MCP error)
- **No embedding provider configured**: System operates in keyword-only mode permanently until provider is configured. All searches return `search_mode: "keyword_fallback"`. <!-- Added per spec 004 -->
- **Embedding provider error at query time**: System logs error, degrades to keyword-only for that request, returns `search_mode: "keyword_fallback"` <!-- Added per spec 004 -->
- **Stale embedding artifact**: Source documentation has changed but artifact file still exists. System loads stale artifact without warning. Developer must delete artifact to trigger regeneration. <!-- Added per spec 004 -->
- **Corrupt embedding artifact**: Artifact file exists but is corrupted (partial write, invalid pickle). Build fails with clear error rather than loading garbage vectors. <!-- Added per spec 004 -->
- **First-run model download**: Local ONNX model files not yet cached on machine. System logs that download is occurring; handles download failures with clear error. <!-- Added per spec 004 -->
- **Embedding dimension mismatch at startup**: Configured dimension does not match provider's actual output. Server fails fast with clear error. <!-- Added per spec 004 -->
- **Very large behavior slice (>1000 functions)**: Computation stops at configurable `max_cone_size` (default 200), returns partial results with truncation warning
- **Entity exists in database but source file deleted from disk**: Source code retrieval returns stored source_text from database (extracted at build time)
- **Source code on disk has changed since database build**: Stored source_text becomes stale; documentation remains valid. Users must rebuild database after code changes.
- **Graph traversal depth exceeds reasonable limit**: Depth is capped at maximum 5 for behavior analysis, 3 for general traversal to prevent performance degradation
- **Entity has no documentation (brief is null)**: System returns entity with empty details/rationale fields; agents use `brief is not null` as the practical quality signal. Entity still receives a minimal embedding from kind+name+signature if doc-less. <!-- spec 005: doc_quality removed; null-brief check replaces quality bucket --> <!-- spec 007: doc-less entities get minimal embeddings -->
- **Multiple files define entities with same compound_id**: Deterministic IDs from signature_map keys ensure unique identification <!-- spec 005: entity_id is deterministic, not Doxygen-format -->
- **Database connection failure**: System returns MCP error (hard failure) rather than successful response; client must handle connection retry or alert user
- **Invalid tool parameters** (e.g., depth=-1, invalid entity_id format): System returns MCP error with validation message rather than successful response with error indicator
- **Build script encounters missing artifact file**: Build process fails with clear error message indicating which artifact is missing and expected path
- **Build script encounters malformed artifact** (invalid JSON, corrupt pickle): Build process fails with validation error and line/byte position if applicable
- **Build script encounters entity with invalid source location**: Build raises `BuildError` if line range exceeds file length (stale code graph). Entity with missing source file is logged as warning and proceeds with source_text=NULL. <!-- spec 007: invalid line range = build failure (stale graph); missing file = warning -->

## Requirements *(mandatory)*

### Functional Requirements

#### Entity Resolution & Lookup

- **FR-001**: System MUST support entity discovery through `search` tool with multi-stage pipeline: exact signature match → exact name match → prefix match → full-text search → semantic search <!-- spec 005: resolve_entity retired; search subsumes the resolution pipeline -->
- **FR-002**: System MUST return ranked results with match metadata including match type, score, kind, file path, capability, and brief
- **FR-003**: System MUST support retrieving full entity records by `entity_id` (required parameter) including identity, documentation fields, source location, capability, metrics, and optionally source code <!-- spec 005: entity_id is the sole lookup key; signature no longer accepted -->
- **FR-004**: ~~System MUST include resolution envelope in all responses from tools accepting entity names~~ <!-- spec 005: REMOVED — ResolutionEnvelope retired; tools accept only entity_id -->
- **FR-005**: System MUST list all entities defined in a source file, filterable by entity kind (function, class, variable, struct, etc.)
- **FR-006**: System MUST provide file-level summaries including entity count by kind, capability distribution, and top entities by fan-in <!-- spec 005: doc_quality_distribution removed from file summary -->

#### Search

- **FR-007**: System MUST perform hybrid search combining pgvector cosine similarity and Postgres full-text search with exact name/signature boost
- **FR-008**: System MUST degrade gracefully to keyword-only search when no embedding provider is configured or when a configured provider encounters an error, and report degradation via search_mode field <!-- Updated per spec 004: provider-based system replaces single endpoint -->
- **FR-009**: System MUST support search filtering by entity kind and capability group <!-- spec 005: min_doc_quality filter removed -->
- **FR-010**: System MUST return search results using SearchResult envelope with result_type, score, search_mode, and provenance
- **FR-011**: System MUST normalize and combine search scores from semantic and keyword sources into unified ranking
- **FR-012**: Search tool MUST accept a `source` parameter (defaulting to `entity`) that is V2-reserved for unified search across entity docs and subsystem docs; in V1 only `entity` is functional

#### Graph Exploration

- **FR-013**: System MUST support caller and callee traversal at configurable depth (1-3 levels) with deduplication ensuring each entity appears once at shortest path
- **FR-014**: System MUST support dependency filtering by relationship type (calls, uses, inherits, includes, containment) and direction (incoming/outgoing)
- **FR-015**: System MUST provide class hierarchy exploration in both directions (parent classes and derived classes)
- **FR-016**: System MUST identify related files via include relationships, co-dependency, or shared entity definitions
- **FR-017**: System MUST include truncation metadata in all graph and list results showing truncated status, total_available count, and returned count; system does NOT support pagination (results are hard-truncated to top N, clients must refine queries to access different result subsets)

#### Behavior Analysis

- **FR-018**: System MUST compute call cones via breadth-first search from seed functions, separating direct callees from transitive cone
- **FR-019**: System MUST report capabilities touched with direct vs. transitive counts and function lists per capability
- **FR-020**: System MUST report global variables used with direct vs. transitive access indicators
- **FR-021**: System MUST categorize side-effect markers as messaging, persistence, state_mutation, or scheduling with direct/transitive labels
- **FR-022**: System MUST support hotspot detection ranked by fan_in, fan_out, bridge (cross-capability), or underdocumented, with kind and capability filters

#### Capability System

- **FR-023**: System MUST list all capability groups with type, description, function count, and stability indicator <!-- spec 005: doc_quality_dist removed from capability responses -->
- **FR-024**: System MUST provide detailed capability information including group definition, typed dependency edges, entry points, and optionally full function list
- **FR-025**: System MUST support comparing multiple capabilities showing shared dependencies, unique dependencies, and bridge entities
- **FR-026**: System MUST list entry points (do_*, spell_*, spec_* functions) filterable by capability and name pattern
- **FR-027**: System MUST report which capabilities an entry point exercises with direct vs. transitive function counts

#### Resources & Prompts

- **FR-028**: System MUST expose MCP resources at URIs: legacy://capabilities, legacy://capability/{name}, legacy://entity/{entity_id}, legacy://file/{path}, legacy://stats
- **FR-029**: System MUST provide canned MCP prompts for common workflows: explain_entity, analyze_behavior, compare_entry_points, explore_capability

#### Build Script & Data Pipeline

- **FR-030**: Build script MUST ingest all source artifacts from the configured artifacts directory: entity database (code_graph.json), dependency graph (code_graph.gml), per-compound documentation files (generated_docs/*.json), capability definitions (capability_defs.json), and capability graph (capability_graph.json). Embedding artifacts are optional — generated on demand when a provider is configured. `doc_db.json` and `signature_map.json` are no longer required. <!-- Updated per specs 003/004: added signature_map, removed embeddings_cache.pkl from required list, embeddings now optional/auto-generated --> <!-- spec 006: doc_db.json and signature_map.json removed from required artifacts; generated_docs/ is the document source -->
- **FR-031**: Build script MUST merge entity metadata with documentation records. The signature map is computed on-the-fly from `EntityDatabase` and `DocumentDB` at build time — `signature_map.json` is no longer loaded as an artifact. Entity models, document models, and graph loader are imported from `legacy_common` (not reimplemented in `build_helpers/`). <!-- Updated per spec 003 FR-002: sig_map replaces compound_id+signature join --> <!-- spec 006: signature_map computed on-the-fly; build_helpers/artifact_models.py and embed_text.py deleted; models imported from legacy_common -->
- **FR-032**: Build script MUST extract source code from disk at build time using entity source location data and store in database source_text column. Build MUST raise `BuildError` if body-located entities exist but zero source texts are extracted (indicates `PROJECT_ROOT` misconfiguration). Build MUST raise `BuildError` if a source file exists but the line range is invalid (indicates stale code graph). Individual file-not-found or encoding errors MUST be logged as warnings but MUST NOT fail the build. <!-- spec 007: fail-fast validation; narrowed exceptions to (OSError, UnicodeDecodeError) -->
- **FR-033**: Build script MUST extract C++ definition lines and store in database definition_text column
- **FR-034**: ~~Build script MUST compute doc_quality classification (high/medium/low)~~ <!-- spec 005: REMOVED — doc_quality and doc_state columns dropped -->
- **FR-035**: Build script MUST compute fan_in and fan_out metrics by counting CALLS edges in dependency graph
- **FR-036**: Build script MUST compute is_bridge flag by checking whether function's incoming vs. outgoing CALLS neighbors span different capability groups
- **FR-037**: Build script MUST compute side_effect_markers by checking each function's CALLS edges against curated side-effect function list and categorizing as messaging, persistence, state_mutation, or scheduling
- **FR-038**: Build script MUST set is_entry_point flag for functions matching patterns: do_*, spell_*, spec_*
- **FR-039**: Build script MUST generate weighted tsvector for full-text search with weights: name=A, brief/details=B, definition_text=C, source_text=D
- **FR-040**: Build script MUST be idempotent, producing identical database state on repeated runs from same input artifacts
- **FR-041**: Build script MUST complete processing of all artifacts and database population in under 5 minutes for ~5,300 entities

#### Data Quality & Consistency

- **FR-042**: Server MUST serve only pre-computed data loaded from database; no runtime LLM inference
- **FR-043**: Server MUST provide responses that are deterministic and reproducible given identical database state
- **FR-044**: Server MUST tag all derived/analysis data items with provenance labels (inferred, heuristic, precomputed, measured)
- **FR-045**: Server MUST maintain consistency between documentation records and source code through build-time extraction performed by build script; consistency is guaranteed only at build time, and users must rebuild the database after code changes (per assumption A-006)

#### Error Handling

- **FR-046**: Server MUST return MCP errors for hard failures including database connectivity errors, invalid tool parameters, malformed requests, or internal server errors
- **FR-047**: Server MUST return successful MCP responses with explicit status indicators for degraded or partial results including embedding service unavailable (search_mode: keyword_fallback), result truncation (truncated: true), or empty search results <!-- spec 005: resolution_status indicators removed (resolve_entity retired) -->

#### Observability

- **FR-048**: Server MUST emit structured logs to stderr in JSON or key-value format including tool invocations, database query execution, performance metrics, errors, and warnings
- **FR-049**: Server MUST support configurable log levels (DEBUG, INFO, WARNING, ERROR) via environment variable, defaulting to INFO level
- **FR-050**: Server MUST log at INFO level: server startup/shutdown, tool invocations with parameters, database connection events, embedding service availability changes, and performance metrics exceeding thresholds
- **FR-051**: Server MUST log at ERROR level: database connection failures, invalid tool parameters, internal errors, and any conditions resulting in MCP error responses

#### V2 Forward-Compatibility

- **FR-052**: Implementation MUST define V2-reserved response shapes (SubsystemSummary, SubsystemDocSummary, ContextBundle) in the model layer, even though they are unused by V1 tools, to prevent response-shape drift when V2 lands
- **FR-053**: V1 tools MUST NOT expose wave ordering data from capability artifacts in any tool response, maintaining the boundary between factual documentation and migration prescription

<!-- FRs added per spec 003 (build script fixes) -->
#### Build Script: Capability Mapping & Data Corrections

- **FR-054**: Build script MUST assign capability group names to entities by building a name→capability mapping from `capability_graph.json` → `capabilities[name].members[].name` (approximately 848 assignments out of ~5,305 entities). The `doc.system` field is not used for capability assignment.
- **FR-055**: Build script MUST read capability descriptions from the `"desc"` key in `capability_defs.json` (not `"description"`)
- **FR-056**: Build script MUST compute `function_count` from `capability_graph.json` → `capabilities[name].function_count` (not from a `"functions"` key in capability_defs.json)
- **FR-057**: Build script MUST parse capability edges from `capability_graph.json` → `"dependencies"` as a nested dict (`source_cap → target_cap → {edge_type, call_count, in_dag}`), not from an `"edges"` flat list
- **FR-058**: ~~Build script MUST compute `doc_quality_dist` for each capability by aggregating doc_quality from entities assigned to that capability group~~ <!-- spec 005: REMOVED — doc_quality_dist dropped from capabilities table -->
- **FR-059**: Build script MUST assign entity capabilities before computing bridge flags (pipeline ordering dependency)
- **FR-060**: Build script MUST create all secondary indexes using the same engine/connection that creates tables, using `CREATE INDEX IF NOT EXISTS` for idempotent re-runs (14 secondary indexes required)

<!-- FRs added per spec 004 (embedding provider) -->
#### Embedding Provider

- **FR-061**: System MUST support a configurable embedding provider with at least two modes: "local" (bundled, no external service) and "hosted" (OpenAI-compatible endpoint), selectable via `EMBEDDING_PROVIDER` environment variable
- **FR-062**: System MUST support a "no provider" mode where embedding is entirely disabled and all search degrades to keyword-only. This MUST be the default when no provider is configured.
- **FR-063**: When configured for local mode, the system MUST default to the bundled ONNX-based embedding model BAAI/bge-base-en-v1.5 (768-dim). The model name MUST be configurable via `EMBEDDING_LOCAL_MODEL`.
- **FR-064**: The database build process MUST load embedding vectors from a cached artifact file if one matching the current model configuration exists. Artifact files are named `embed_cache_{model_slug}_{dim}.pkl` (pickle format).
- **FR-065**: The database build process MUST generate embeddings on demand when no matching artifact file exists and an embedding provider is configured, then save the result as an artifact for future builds.
- **FR-066**: The database schema MUST use a vector column dimension that matches the configured embedding provider's output dimension (via `EMBEDDING_DIMENSION` env var, default 768), not a hardcoded value.
- **FR-067**: The text used for embedding each entity with documentation MUST be a structured Doxygen-formatted docstring reconstructed from entity documentation fields via `Document.to_doxygen()` (name, kind, brief, details, params, returns, notes, rationale). <!-- spec 007: clarified "with documentation" vs doc-less entities -->
- **FR-068**: The runtime query embedding pathway MUST use the same provider and model that generated the stored vectors, ensuring dimensional and semantic consistency.
- **FR-069**: The old hardcoded `embeddings_cache.pkl` artifact MUST NOT be required by build validation.
- **FR-070**: The system MUST validate at startup that the configured vector dimension matches the embedding provider's actual output dimension and fail fast with a clear error if they disagree.
- **FR-071**: The local embedding provider MUST NOT block the server's event loop during query-time embedding. Embedding computation MUST be offloaded to a background thread.
- **FR-072**: Entities without a `Document` but with a name, signature, or kind MUST receive a minimal embedding generated from a Doxygen-formatted text combining `kind`, `name`, `signature`, and `file_path`. This includes structural compounds (file, dir, namespace). Only entities where all three of name, signature, and kind are empty/null may be skipped. <!-- spec 007: replaces "no documentable content" with explicit minimal embedding for doc-less entities -->

<!-- FRs added per spec 005 (deterministic IDs, doc merge fix, tool simplification) -->
#### Deterministic Entity IDs

- **FR-073**: Build pipeline MUST compute entity IDs as `{prefix}:{sha256(canonical_key)[:7]}` where the canonical key is the signature_map tuple `(compound_id, signature_or_name)`
- **FR-074**: Prefix MUST be determined by entity kind: `fn` for function/define, `var` for variable, `cls` for class/struct, `file` for file, `sym` for everything else
- **FR-075**: Build pipeline MUST halt with a clear error on any ID collision (two different canonical keys producing the same prefixed hash)
- **FR-076**: `resolve_entity` tool MUST be removed from the MCP tool catalog (total tools: 20 → 19)
- **FR-077**: All tools that previously accepted `entity_id` and `signature` parameters MUST accept only `entity_id` as a required parameter
- **FR-078**: `ResolutionEnvelope` MUST be removed from all tool response shapes
- **FR-079**: `search` tool MUST remove the `min_doc_quality` parameter
- **FR-080**: `list_capabilities` and `get_capability_detail` responses MUST remove the `doc_quality_dist` field
- **FR-081**: `EntitySummary` MUST remove `doc_state` and `doc_quality` fields
- **FR-082**: `EntityDetail` MUST remove `compound_id`, `member_id`, `doc_state`, and `doc_quality` fields
- **FR-083**: `search` is the sole path from human-readable text to entity IDs — no other tool performs name-to-ID resolution
- **FR-084**: Schema MUST remove columns: `compound_id`, `member_id`, `doc_state`, `doc_quality` from the entities table
- **FR-085**: Schema MUST remove column: `doc_quality_dist` from the capabilities table
- **FR-086**: Build pipeline MUST carry all documentation fields (brief, details, params, returns, notes, rationale, usages) from doc_db through the merge without loss

<!-- FRs added per spec 007 (data completeness fixes) -->
#### Build Script: Data Completeness

- **FR-087**: Build pipeline MUST store `params` as `NULL` when the value is `None`, `{}`, or absent — not as an empty JSON object. The `JSONB` column MUST use `none_as_null=True`.
- **FR-088**: Build pipeline MUST generate embeddings for entities without a `Document` by constructing a minimal Doxygen-formatted text from `kind`, `name`, `signature`, and `file_path` — including structural compounds (file, dir, namespace). The tag mapping extends `Document.to_doxygen()` with structural compound tags (file, dir, typedef, union).
- **FR-089**: Build pipeline MUST log a structured summary after source extraction: body_located, extracted, failed, skipped, success_rate
- **FR-090**: Build pipeline MUST log a structured summary after embedding generation: doc_embeds, minimal_embeds, no_embed, coverage%

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: AI assistants can resolve any entity name via search and receive correct documentation in under 100 milliseconds for single-entity lookup <!-- spec 005: search replaces resolve_entity -->
- **SC-002**: Hybrid search queries return relevant results ranked by combined semantic and keyword score in under 500 milliseconds including embedding query
- **SC-003**: Graph traversal at depth 3 completes and returns results in under 200 milliseconds for typical entities (fan-in/fan-out < 50)
- **SC-004**: Behavior slice computation for entry points completes in under 1 second when call cone contains fewer than 200 functions
- **SC-005**: Server starts and loads dependency graph (25,000 edges) into memory in under 5 seconds
- **SC-006**: When no embedding provider is configured or the provider encounters an error, search automatically falls back to keyword mode with explicit degradation reporting and no failures <!-- Updated per spec 004: reflects provider-based system -->
- **SC-007**: Ambiguous search queries return ranked results with sufficient context for human or AI to select correct match without additional queries <!-- spec 005: search replaces resolve_entity -->
- **SC-008**: ~~95% of entity lookups result in exact match (resolution_status=exact)~~ <!-- spec 005: REMOVED — resolve_entity retired; agents use search + entity_id pattern -->
- **SC-009**: Build script processes all artifacts (5,293 entities, 25,000 edges, 30 capabilities) and populates database in under 5 minutes
- **SC-010**: Build script produces identical database state on repeated runs from same input artifacts (idempotent operation)
- **SC-011**: All derived metrics (fan_in, fan_out, is_bridge, side_effect_markers) are correctly computed from source artifacts and match validation samples <!-- spec 005: doc_quality removed from derived metrics -->
- **SC-012**: Source code extraction captures ≥90% of entities with valid body locations, storing complete function/class definitions in database. Build fails with `BuildError` on zero extraction or invalid line ranges. <!-- spec 007: ≥90% threshold; fail-fast on zero/invalid -->
- **SC-013**: Full-text search tsvector enables relevant keyword matches for natural language queries against entity documentation and source code
- **SC-014**: All server responses include structured provenance labels enabling consumers to assess data reliability (precomputed, inferred, heuristic, measured)

<!-- Success criteria added per specs 003/004 -->
- **SC-015**: After a full build, approximately 848 entities have non-null capability assignment (from capability_graph.json members)
- **SC-016**: After a full build, at least 10 entities are flagged as bridge functions (is_bridge=true)
- **SC-017**: After a full build, all 30 capabilities have function_count > 0 and non-empty descriptions
- **SC-018**: After a full build, capability_edges table contains exactly 200 rows
- **SC-019**: After a full build, at least 19 database indexes exist (5 PKs + 14 secondary)
- **SC-020**: A developer can build the database and run semantic searches with zero external service dependencies by configuring local embedding mode
- **SC-021**: Embedding artifact generation for the full entity set completes within 5 minutes on a standard development machine
- **SC-022**: Query-time embedding adds less than 100ms of latency to search requests when using the local provider

<!-- Success criteria added per spec 005 -->
- **SC-023**: Two consecutive builds from the same artifacts produce identical entity ID sets (100% determinism)
- **SC-024**: Zero ID collisions across ~5,305 entities (enforced by build-time collision detection)
- **SC-025**: After a full build, at least 95% of doc_db.json entries with non-empty brief have non-null brief in the database
- **SC-026**: An agent can complete search → get_entity → get_callers → get_behavior_slice using only entity_ids, with zero signature-based lookups
- **SC-027**: No tool in the MCP catalog accepts a `signature` parameter for entity lookup (19 tools total)

<!-- Success criteria added per spec 007 -->
- **SC-028**: After a successful build, ≥95% of all entities have non-null `embedding` in the database (doc-less entities receive minimal embeddings)
- **SC-029**: After a successful build, `params IS NOT NULL` count matches meaningful parameter content (~1,800–2,100, not ~5,055)
- **SC-030**: Build with invalid `PROJECT_ROOT` exits with `BuildError` within the source extraction stage
- **SC-031**: Build with valid `PROJECT_ROOT` logs a structured extraction summary (body_located, extracted, failed, skipped, success_rate)
- **SC-032**: Build logs an embedding generation summary (doc_embeds, minimal_embeds, no_embed, coverage%)

### Assumptions

- **A-001**: Pre-computed artifacts in `artifacts/` are complete, up-to-date, and internally consistent at time of database build; build script is run offline before server startup and not during server operation
- **A-002**: PostgreSQL database with pgvector extension is available and accessible via connection string in `.env` file
- **A-003**: Embedding is available via a configurable provider: local (bundled ONNX model, default), hosted (OpenAI-compatible endpoint), or none (keyword-only). System must function correctly without any embedding provider configured. <!-- Updated per spec 004: replaces single hosted endpoint assumption -->
- **A-004**: NetworkX in-memory graph constructed from ~25,000 edges fits in available memory (estimated ~100-200 MB) and is read-only after initial load (no thread safety concerns for concurrent reads)
- **A-005**: MCP client (VS Code, Claude Desktop) supports stdio transport and can invoke MCP tools/resources/prompts
- **A-006**: Source code files on disk match artifacts at database build time; users rebuild database after code changes
- **A-007**: ~~The signature map (`signature_map.json`) bridges entity IDs from `code_graph.json` to `(compound_id, signature)` documentation keys in `doc_db.json`. It is a **derived artifact** — regenerated from `code_graph.json` + `doc_db.json` via `build_signature_map.py`.~~ The signature map is now computed on-the-fly at build time from the loaded `EntityDatabase` and `DocumentDB`. `signature_map.json` is no longer a required artifact. <!-- Updated per spec 003: replaces compound_id+signature assumption --> <!-- spec 006: signature_map computed on-the-fly; json artifact no longer required -->
- **A-008**: Capability definitions, dependency edges, and function membership lists in `capability_defs.json` and `capability_graph.json` are authoritative
- **A-009**: Full-text search weighted tsvector composition (name=A, brief/details=B, definition=C, source_text=D) provides reasonable ranking for prose queries
- **A-010**: BFS traversal with visited set and configurable depth limits prevents performance degradation from circular dependencies or deep call chains
- **A-011**: The `capability_graph.json` member names match entity names in the entity database exactly. The `doc.system` field remains unused for capability assignment. <!-- Added per spec 003 -->
- **A-012**: The BAAI/bge-base-en-v1.5 model produces 768-dimensional vectors. This is verified at runtime; if a future model version changes dimensions, the config must be updated accordingly. <!-- Added per spec 004 -->
- **A-013**: Embedding ~5,300 entities locally takes approximately 1–3 minutes on a modern CPU. Single-query local embedding takes approximately 5–20ms. Both are acceptable for their respective use cases. <!-- Added per spec 004 -->
- **A-014**: After switching embedding providers, the developer is responsible for re-running the database build. The server does not detect dimension mismatches between the configured provider and vectors already in the database. <!-- Added per spec 004 -->
- **A-015**: The ONNX model files are cached locally by the FastEmbed library (in `~/.cache/fastembed/`) after initial download. First run requires internet access; subsequent runs are fully offline. <!-- Added per spec 004 -->

## Clarifications

### Session 2026-03-14

- Q: Server process lifecycle - single request per process vs. long-lived server? → A: Long-lived server handling multiple sequential requests (server starts once, handles multiple tool invocations over stdio until client disconnects)
- Q: Result pagination strategy - hard truncation vs. pagination support? → A: Hard truncation with metadata only (no pagination - tools return top N results with truncation indicator, no mechanism to fetch additional results)
- Q: Error response format - when to use MCP errors vs. success with error indicators? → A: Structured MCP errors for failures, success payloads with status fields for degraded/partial results (database errors and invalid parameters return MCP errors; degraded states like embedding service down or truncated results return success with explicit status indicators)
- Q: Request concurrency model - sequential vs. concurrent processing? → A: Async/event-loop based concurrency (server uses async/await for I/O-bound operations like database queries and embedding requests; NetworkX graph is read-only and accessed without locking)
- Q: Logging strategy for server operations and diagnostics? → A: Structured logging to stderr with configurable levels (INFO by default - JSON or key-value format logs including tool invocations, database queries, performance metrics, errors; level controlled via environment variable)
- **Note**: Added explicit build script requirements (FR-029 through FR-040) after user identified gap - build script is half the deliverable and needs testable functional requirements for artifact ingestion, derived data computation, source extraction, and idempotency

## Deployment Context *(optional)*

Long-lived stdio process on developer machines. Async I/O (database, embedding) with read-only in-memory graph. Configuration via `.env`. See MODEL.md for schema, Appendix B for embedding config, and PRD.md NFR-3 for deployment requirements.
