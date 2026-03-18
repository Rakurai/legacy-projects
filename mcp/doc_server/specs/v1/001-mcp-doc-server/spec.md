# Feature Specification: MCP Documentation Server

**Feature Branch**: `001-mcp-doc-server`
**Created**: 2026-03-14
**Status**: Draft
**Input**: User description: "MCP server to serve documentation on this project"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Entity Lookup and Documentation Access (Priority: P1) 🎯 MVP

An AI assistant needs to understand what a specific function, class, or variable does in the Legacy MUD codebase. The assistant can ask "What is `damage`?" and receive complete documentation including the function signature, parameter descriptions, return values, usage examples, source code location, and optionally the actual C++ source code. When multiple entities share the same name, the assistant receives a ranked list of candidates with enough context to choose the correct one.

**Why this priority**: Entity lookup is the foundational capability. Without reliable entity resolution and documentation retrieval, no other analysis can proceed. This is the MVP that makes the pre-computed documentation artifacts accessible to AI assistants.

**Independent Test**: Can be fully tested by querying known entities (e.g., `damage` function, `Character` class, `game_loop_unix` function) and verifying that returned documentation matches the pre-computed artifacts in `artifacts/doc_db.json`. Success means an assistant can explore the codebase without parsing raw JSON files.

**Acceptance Scenarios**:

1. **Given** an entity name with unique match, **When** assistant requests entity resolution, **Then** receive exact match with full documentation, source location, and metrics
2. **Given** an ambiguous entity name (e.g., "save" matches multiple functions), **When** assistant requests resolution, **Then** receive ranked candidate list with file paths, signatures, and brief descriptions to disambiguate
3. **Given** an entity identifier, **When** assistant requests full entity details with source code, **Then** receive complete documentation plus actual C++ source text from database
4. **Given** a source file path, **When** assistant requests all entities in that file, **Then** receive list of all functions, classes, variables, and structs defined in that file with summaries
5. **Given** a source file path, **When** assistant requests file summary, **Then** receive aggregated statistics including entity counts by type, capability distribution, and documentation quality breakdown

---

### User Story 2 - Documentation Search (Priority: P2)

An AI assistant working on poison damage mechanics needs to find all entities related to "poison spreading between characters". The assistant performs a hybrid search combining semantic similarity (using embeddings) with keyword matching, receiving ranked results that include both exact name matches and conceptually related entities. When the embedding service is unavailable, search gracefully degrades to keyword-only mode and explicitly reports the degraded state.

**Why this priority**: Search enables discovery of relevant code without knowing exact names. This is essential for exploratory tasks like "find all inventory management code" or "locate authentication logic". Search builds on Phase 1 entity infrastructure and adds discovery capabilities.

**Independent Test**: Can be tested by issuing natural language queries (e.g., "poison damage over time", "player authentication", "room descriptions") and verifying that results include relevant entities with high scores. Test fallback mode by disabling the embedding endpoint and confirming keyword-only results are returned with explicit fallback status.

**Acceptance Scenarios**:

1. **Given** a semantic query like "poison spreading between characters", **When** assistant performs hybrid search, **Then** receive ranked results combining embedding similarity and keyword matches with normalized scores
2. **Given** an exact entity name in search query, **When** assistant searches, **Then** that entity receives a score boost and appears at top of results
3. **Given** search filters for kind=function and capability=combat, **When** assistant searches, **Then** receive only functions from combat capability group
4. **Given** embedding service is unavailable, **When** assistant searches, **Then** receive keyword-only results with search_mode="keyword_fallback" explicitly indicated
5. **Given** search for low-quality documentation, **When** assistant filters by min_doc_quality=medium, **Then** receive only entities with medium or high documentation quality ratings

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

1. **Given** no parameters, **When** assistant lists capabilities, **Then** receive all 30 groups with types, descriptions, function counts, and documentation quality distributions
2. **Given** a capability name, **When** assistant requests capability detail, **Then** receive group definition, typed dependency edges, entry points, and optionally full function list
3. **Given** two or more capability names, **When** assistant compares capabilities, **Then** receive shared dependencies, unique dependencies per group, and bridge entities connecting them
4. **Given** a filter for capability=combat, **When** assistant lists entry points, **Then** receive only entry points that directly exercise combat capability functions
5. **Given** an entry point function name, **When** assistant requests entry point info, **Then** receive which capabilities the entry point touches with direct vs. transitive counts

---

### Edge Cases

- **Unknown entity name**: System returns successful MCP response with `not_found` status and nearest matches from full-text search (not an MCP error)
- **Ambiguous entity name with 50+ candidates**: Results are truncated to top 20 candidates ranked by score, with truncation metadata indicating total available; no pagination mechanism exists, users must refine query to see different results
- **Circular dependencies in call graph**: BFS traversal with visited set prevents infinite loops; each entity appears once at shortest path distance
- **Embedding service down during search**: System returns successful MCP response with keyword-only results and sets `search_mode: "keyword_fallback"` to indicate degraded state (not an MCP error)
- **Very large behavior slice (>1000 functions)**: Computation stops at configurable `max_cone_size` (default 200), returns partial results with truncation warning
- **Entity exists in database but source file deleted from disk**: Source code retrieval returns stored source_text from database (extracted at build time)
- **Source code on disk has changed since database build**: Stored source_text becomes stale; documentation remains valid. Users must rebuild database after code changes.
- **Graph traversal depth exceeds reasonable limit**: Depth is capped at maximum 5 for behavior analysis, 3 for general traversal to prevent performance degradation
- **Entity has no documentation (doc_quality=low)**: System returns entity with empty details/rationale fields; brief may be auto-generated from signature
- **Multiple files define entities with same compound_id**: Resolution pipeline disambiguates using file path and signature; all candidates returned with match metadata
- **Database connection failure**: System returns MCP error (hard failure) rather than successful response; client must handle connection retry or alert user
- **Invalid tool parameters** (e.g., depth=-1, invalid entity_id format): System returns MCP error with validation message rather than successful response with error indicator
- **Build script encounters missing artifact file**: Build process fails with clear error message indicating which artifact is missing and expected path
- **Build script encounters malformed artifact** (invalid JSON, corrupt pickle): Build process fails with validation error and line/byte position if applicable
- **Build script encounters entity with invalid source location**: Entity is included in database with source_text=NULL; server returns entity documentation without source code when requested

## Requirements *(mandatory)*

### Functional Requirements

#### Entity Resolution & Lookup

- **FR-001**: System MUST resolve entity names through multi-stage pipeline: exact signature match → exact name match → prefix match → full-text search → semantic search
- **FR-002**: System MUST return ranked candidate list with match metadata including match type, score, kind, file path, capability, brief, and documentation quality
- **FR-003**: System MUST support retrieving full entity records including identity, documentation fields, source location, capability, metrics, and optionally source code
- **FR-004**: System MUST include resolution envelope in all responses from tools accepting entity names, containing resolution_status (exact/ambiguous/not_found), resolved_from, match_type, and resolution_candidates
- **FR-005**: System MUST list all entities defined in a source file, filterable by entity kind (function, class, variable, struct, etc.)
- **FR-006**: System MUST provide file-level summaries including entity count by kind, capability distribution, documentation quality distribution, and top entities by fan-in

#### Search

- **FR-007**: System MUST perform hybrid search combining pgvector cosine similarity and Postgres full-text search with exact name/signature boost
- **FR-008**: System MUST degrade gracefully to keyword-only search when embedding endpoint is unavailable and report degradation via search_mode field
- **FR-009**: System MUST support search filtering by entity kind, capability group, and minimum documentation quality
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

- **FR-023**: System MUST list all capability groups with type, description, function count, stability indicator, and documentation quality distribution
- **FR-024**: System MUST provide detailed capability information including group definition, typed dependency edges, entry points, and optionally full function list
- **FR-025**: System MUST support comparing multiple capabilities showing shared dependencies, unique dependencies, and bridge entities
- **FR-026**: System MUST list entry points (do_*, spell_*, spec_* functions) filterable by capability and name pattern
- **FR-027**: System MUST report which capabilities an entry point exercises with direct vs. transitive function counts

#### Resources & Prompts

- **FR-028**: System MUST expose MCP resources at URIs: legacy://capabilities, legacy://capability/{name}, legacy://entity/{entity_id}, legacy://file/{path}, legacy://stats
- **FR-029**: System MUST provide canned MCP prompts for common workflows: explain_entity, analyze_behavior, compare_entry_points, explore_capability

#### Build Script & Data Pipeline

- **FR-030**: Build script MUST ingest all six source artifacts from `artifacts/` directory: entity database (code_graph.json), dependency graph (code_graph.gml), document database (doc_db.json), embeddings cache (embeddings_cache.pkl), capability definitions (capability_defs.json), and capability graph (capability_graph.json)
- **FR-031**: Build script MUST merge entity metadata with documentation records via 1:1 join on compound_id and signature, producing complete entity records
- **FR-032**: Build script MUST extract source code from disk at build time using entity source location data and store in database source_text column
- **FR-033**: Build script MUST extract C++ definition lines and store in database definition_text column
- **FR-034**: Build script MUST compute doc_quality classification (high/medium/low) based on doc_state, presence of details field, and presence of parameters field
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
- **FR-047**: Server MUST return successful MCP responses with explicit status indicators for degraded or partial results including embedding service unavailable (search_mode: keyword_fallback), result truncation (truncated: true), entity not found (resolution_status: not_found), or ambiguous resolution (resolution_status: ambiguous)

#### Observability

- **FR-048**: Server MUST emit structured logs to stderr in JSON or key-value format including tool invocations, database query execution, performance metrics, errors, and warnings
- **FR-049**: Server MUST support configurable log levels (DEBUG, INFO, WARNING, ERROR) via environment variable, defaulting to INFO level
- **FR-050**: Server MUST log at INFO level: server startup/shutdown, tool invocations with parameters, database connection events, embedding service availability changes, and performance metrics exceeding thresholds
- **FR-051**: Server MUST log at ERROR level: database connection failures, invalid tool parameters, internal errors, and any conditions resulting in MCP error responses

#### V2 Forward-Compatibility

- **FR-052**: Implementation MUST define V2-reserved response shapes (SubsystemSummary, SubsystemDocSummary, ContextBundle) in the model layer, even though they are unused by V1 tools, to prevent response-shape drift when V2 lands
- **FR-053**: V1 tools MUST NOT expose wave ordering data from capability artifacts in any tool response, maintaining the boundary between factual documentation and migration prescription

### Key Entities

- **Entity**: Core documentation record representing a function, class, variable, struct, or other code element. Contains identity (compound_id, name, kind, signature), documentation (brief, details, parameters, returns, rationale, usage notes), source location (file path, line range), metrics (fan_in, fan_out, doc_quality), and relationships (capability membership, is_entry_point, is_bridge).

- **Dependency Edge**: Typed relationship between entities representing CALLS, USES, INHERITS, INCLUDES, or CONTAINED_BY semantics. Contains source entity, target entity, edge type, and optional metadata. Forms a directed multigraph enabling graph traversal and analysis.

- **Capability Group**: Architectural grouping of related functions classified by type (domain, policy, projection, infrastructure, utility). Contains group name, description, function membership list, stability indicator, typed dependencies to other groups, and entry point mappings.

- **SearchResult**: Discriminated union envelope for search results supporting both entity matches and (V2) subsystem document matches. Contains result_type, score, search_mode, provenance label, and type-specific summary.

- **BehaviorSlice**: Computed analysis of function's transitive call cone. Contains seed function, direct callees list, transitive cone list, capabilities touched (direct/transitive counts), globals used, side-effect markers (categorized and labeled direct/transitive), and truncation metadata.

- **EntryPoint**: Special entity that serves as command entry point (do_*), spell entry point (spell_*), or special procedure (spec_*). Contains standard entity data plus capability exercise analysis showing which capability groups are touched directly and transitively.

- **Build Script**: Offline ETL pipeline that transforms raw documentation artifacts into queryable database. Ingests six source artifacts (entity database, dependency graph, document database, embeddings, capability definitions, capability graph), merges entity metadata with documentation, extracts source code from disk, computes derived metrics (doc_quality, fan_in/fan_out, is_bridge, side_effect_markers, is_entry_point), generates full-text search vectors, and populates database tables. Must be idempotent and complete within 5 minutes.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: AI assistants can resolve any entity name and receive correct documentation in under 100 milliseconds for single-entity lookup
- **SC-002**: Hybrid search queries return relevant results ranked by combined semantic and keyword score in under 500 milliseconds including embedding query
- **SC-003**: Graph traversal at depth 3 completes and returns results in under 200 milliseconds for typical entities (fan-in/fan-out < 50)
- **SC-004**: Behavior slice computation for entry points completes in under 1 second when call cone contains fewer than 200 functions
- **SC-005**: Server starts and loads dependency graph (25,000 edges) into memory in under 5 seconds
- **SC-006**: When embedding service is unavailable, search automatically falls back to keyword mode with explicit degradation reporting and no failures
- **SC-007**: Ambiguous entity names return ranked candidates with sufficient context for human or AI to select correct match without additional queries
- **SC-008**: 95% of entity lookups result in exact match (resolution_status=exact) without requiring disambiguation
- **SC-009**: Build script processes all artifacts (5,293 entities, 25,000 edges, 30 capabilities) and populates database in under 5 minutes
- **SC-010**: Build script produces identical database state on repeated runs from same input artifacts (idempotent operation)
- **SC-011**: All derived metrics (doc_quality, fan_in, fan_out, is_bridge, side_effect_markers) are correctly computed from source artifacts and match validation samples
- **SC-012**: Source code extraction captures 100% of entities with valid source locations, storing complete function/class definitions in database
- **SC-013**: Full-text search tsvector enables relevant keyword matches for natural language queries against entity documentation and source code
- **SC-014**: All server responses include structured provenance labels enabling consumers to assess data reliability (precomputed, inferred, heuristic, measured)

### Assumptions

- **A-001**: Pre-computed artifacts in `artifacts/` are complete, up-to-date, and internally consistent at time of database build; build script is run offline before server startup and not during server operation
- **A-002**: PostgreSQL database with pgvector extension is available and accessible via connection string in `.env` file
- **A-003**: OpenAI-compatible embedding endpoint is available for semantic search but system must function correctly if unavailable
- **A-004**: NetworkX in-memory graph constructed from ~25,000 edges fits in available memory (estimated ~100-200 MB) and is read-only after initial load (no thread safety concerns for concurrent reads)
- **A-005**: MCP client (VS Code, Claude Desktop) supports stdio transport and can invoke MCP tools/resources/prompts
- **A-006**: Source code files on disk match artifacts at database build time; users rebuild database after code changes
- **A-007**: Entity compound_id and signature combination uniquely identifies entities for join operations between artifacts
- **A-008**: Capability definitions, dependency edges, and function membership lists in `capability_defs.json` and `capability_graph.json` are authoritative
- **A-009**: Full-text search weighted tsvector composition (name=A, brief/details=B, definition=C, source_text=D) provides reasonable ranking for prose queries
- **A-010**: BFS traversal with visited set and configurable depth limits prevents performance degradation from circular dependencies or deep call chains

## Clarifications

### Session 2026-03-14

- Q: Server process lifecycle - single request per process vs. long-lived server? → A: Long-lived server handling multiple sequential requests (server starts once, handles multiple tool invocations over stdio until client disconnects)
- Q: Result pagination strategy - hard truncation vs. pagination support? → A: Hard truncation with metadata only (no pagination - tools return top N results with truncation indicator, no mechanism to fetch additional results)
- Q: Error response format - when to use MCP errors vs. success with error indicators? → A: Structured MCP errors for failures, success payloads with status fields for degraded/partial results (database errors and invalid parameters return MCP errors; degraded states like embedding service down or truncated results return success with explicit status indicators)
- Q: Request concurrency model - sequential vs. concurrent processing? → A: Async/event-loop based concurrency (server uses async/await for I/O-bound operations like database queries and embedding requests; NetworkX graph is read-only and accessed without locking)
- Q: Logging strategy for server operations and diagnostics? → A: Structured logging to stderr with configurable levels (INFO by default - JSON or key-value format logs including tool invocations, database queries, performance metrics, errors; level controlled via environment variable)
- **Note**: Added explicit build script requirements (FR-029 through FR-040) after user identified gap - build script is half the deliverable and needs testable functional requirements for artifact ingestion, derived data computation, source extraction, and idempotency

## Deployment Context *(optional)*

The MCP server runs as a **long-lived process** on developer machines, handling multiple sequential tool invocations until the client disconnects. The server uses **async/await** for I/O-bound operations (database queries via asyncpg, embedding API calls) to avoid blocking during network or disk operations. The in-memory NetworkX graph is read-only after initial load and supports concurrent access without locking. The server is typically invoked by AI coding assistants via stdio transport. Configuration is managed through a `.env` file containing:
- PostgreSQL connection string
- Embedding endpoint URL (optional)
- Project root path for source file access
- Artifacts directory path
- Log level (DEBUG/INFO/WARNING/ERROR, defaults to INFO)

PostgreSQL runs in a Docker container using `pgvector/pgvector:pg17` image. The database is populated by running an offline build script (`build_mcp_db.py`) that processes artifacts from `artifacts/` directory. The server executable is started via `uv run python -m server.server` from the project directory and remains active until the client terminates the connection.

The server integrates with MCP clients configured to recognize the `legacy://` URI scheme for resources and the documented tool/prompt interfaces. No authentication or network transport is required; all communication happens via stdin/stdout. The in-memory dependency graph (loaded at startup) persists across multiple tool invocations within a session. Structured logs are emitted to stderr (separate from MCP protocol on stdout) for monitoring, debugging, and performance analysis.
