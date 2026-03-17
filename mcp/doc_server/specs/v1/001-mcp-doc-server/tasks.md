---
description: "Implementation tasks for MCP Documentation Server"
---

# Tasks: MCP Documentation Server

**Feature**: 001-mcp-doc-server
**Input**: Design documents from `/specs/001-mcp-doc-server/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story. Tests are included (pragmatic/PoC-level per PATTERNS.md).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2)
- All paths relative to `.ai/mcp/doc_server/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project directory structure in .ai/mcp/doc_server/ per plan.md
- [X] T002 Initialize Python project with uv and create pyproject.toml with dependencies (FastMCP, Pydantic v2, SQLModel, SQLAlchemy[asyncio], pgvector, NetworkX, loguru, OpenAI SDK, pytest, pytest-asyncio)
- [X] T003 [P] Create docker-compose.yml for PostgreSQL 17 + pgvector container
- [X] T004 [P] Create .env.example with configuration template (PGHOST, PGPORT, PGDATABASE, PROJECT_ROOT, ARTIFACTS_DIR, LOG_LEVEL, EMBEDDING_*)
- [X] T005 [P] Create README.md with quick setup instructions
- [X] T006 [P] Configure ruff for linting and mypy for strict type checking

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Database & Schema

- [X] T007 Create build_helpers/__init__.py module structure
- [X] T008 Implement database schema as SQLModel table=True classes in server/db_models.py (Entity, Edge, Capability, CapabilityEdge, EntryPoint per data-model.md §1.6; use pgvector.sqlalchemy Vector, sqlalchemy TSVECTOR/JSONB columns; this is the CANONICAL schema location that build_helpers will import from)
- [X] T009 Create build_helpers/loaders.py with artifact validation (check all 6 required files exist and parse without errors)
- [X] T010 Implement entity loading in build_helpers/loaders.py (parse code_graph.json with doxygen_parse.load_db())
- [X] T011 Implement documentation loading in build_helpers/loaders.py (parse doc_db.json)

### Build Script Core

- [X] T012 Implement entity_processor.py with merge_entities() (1:1 join on compound_id + signature)
- [X] T013 Implement source code extraction in entity_processor.py (read from disk using body.fn, body.line, body.end_line)
- [X] T014 Implement derived metrics computation in entity_processor.py (doc_quality, fan_in, fan_out, is_bridge, is_entry_point)
- [X] T015 Implement side_effect_markers computation in entity_processor.py (BFS through CALLS, check against curated list, categorize)
- [X] T016 Implement tsvector generation in entity_processor.py (weighted: name=A, brief/details=B, definition=C, source_text=D)
- [X] T017 Implement graph_loader.py to parse code_graph.gml and extract edges for database
- [X] T018 Implement embeddings_loader.py to unpickle embeddings_cache.pkl and map to entity_id
- [X] T019 Implement build_mcp_db.py main pipeline (orchestrates all build_helpers modules, populates database, validates results)
- [X] T019a Implement entry_points table population in build_mcp_db.py (derive from entities WHERE is_entry_point=true, compute capabilities exercised via BFS)

### Server Core Infrastructure

- [X] T020 Create server/__init__.py module structure
- [X] T021 Implement server/config.py with Pydantic ServerConfig (pydantic-settings for .env loading)
- [X] T022 Implement server/models.py with all Pydantic API models (EntitySummary, EntityDetail, SearchResult, BehaviorSlice, ResolutionEnvelope, TruncationMetadata, V2-reserved shapes per data-model.md)
- [X] T022a [P] Note: server/db_models.py is created by T008 (canonical schema location); build_helpers modules import from server/db_models.py to avoid circular dependencies
- [X] T022b [P] Add provenance field to all response models in server/models.py (EntitySummary, EntityDetail, SearchResult, BehaviorSlice, CapabilityDetail per FR-044; values: doxygen_extracted, llm_generated, subsystem_narrative, precomputed, inferred, heuristic, measured)
- [X] T023 Implement server/db.py with SQLAlchemy async engine factory, async_sessionmaker, and repository classes (EntityRepository, EdgeRepository, CapabilityRepository per SQLMODEL.md repository pattern)
- [X] T024 Implement server/graph.py to load NetworkX MultiDiGraph from edges table at startup (via AsyncSession, see research.md §3)

### Logging Setup

- [X] T025 Configure loguru in server/config.py (structured logging to stderr, configurable levels, JSON/key-value format)

**Checkpoint**: Foundation ready - database schema exists, build script can populate database, server core infrastructure available - user story implementation can now begin

---

## Phase 3: User Story 1 - Entity Lookup and Documentation Access (Priority: P1) 🎯 MVP

**Goal**: AI assistant can resolve entity names, retrieve full documentation, access source code, and explore file-level entities

**Independent Test**: Query known entities (e.g., `damage` function, `Character` class, `game_loop_unix`) and verify returned documentation matches pre-computed artifacts in `.ai/artifacts/doc_db.json`

### Tests for User Story 1 (Happy-Path Integration Tests)

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T026 [P] [US1] Create tests/conftest.py with pytest fixtures (test DB, mock artifacts, async support)
- [X] T027 [P] [US1] Contract test for resolve_entity tool in tests/test_tools.py (validate input/output schemas)
- [X] T028 [P] [US1] Integration test for entity resolution pipeline in tests/test_resolution.py (exact match, ambiguous, not_found scenarios)

### Implementation for User Story 1

#### Resolution Pipeline

- [X] T029 [US1] Implement server/resolver.py with resolution pipeline (exact signature → exact name → prefix → keyword → semantic stages per FR-001)
- [X] T030 [US1] Implement exact signature match in resolver.py (SELECT WHERE signature = $1)
- [X] T031 [US1] Implement exact name match in resolver.py (SELECT WHERE name = $1, ranked by doc_quality + fan_in)
- [X] T032 [US1] Implement prefix match in resolver.py (SELECT WHERE name LIKE $1 || '%')
- [X] T033 [US1] Implement keyword search in resolver.py (ts_rank with plainto_tsquery)
- [X] T034 [US1] Implement semantic search in resolver.py (pgvector cosine similarity with explicit mode switching when embedding service unavailable)

#### Tool Implementations

- [X] T035 [US1] Create server/tools/__init__.py module structure
- [X] T036 [P] [US1] Implement resolve_entity tool in server/tools/entity.py (calls resolver.py, returns ResolutionEnvelope + candidates)
- [X] T037 [P] [US1] Implement get_entity tool in server/tools/entity.py (fetch EntityDetail by entity_id or signature, include_code and include_neighbors params; populate provenance field based on doc_state per FR-044)
- [X] T038 [P] [US1] Implement get_source_code tool in server/tools/entity.py (retrieve source_text with optional context lines from disk)
- [X] T039 [P] [US1] Implement list_file_entities tool in server/tools/entity.py (SELECT WHERE file_path = $1, filterable by kind)
- [X] T040 [P] [US1] Implement get_file_summary tool in server/tools/entity.py (aggregate stats: entity counts, capability distribution, doc_quality, top entities by fan_in, include graph)

#### Server Integration

- [X] T041 [US1] Register all US1 tools in server/server.py with FastMCP decorators; use FastMCP @lifespan decorator for DB engine + NetworkX graph initialization (tools access via ctx.lifespan_context)
- [X] T042 [US1] Add validation and error handling for US1 tools (MCP errors for hard failures, success with status indicators for degraded states)
- [X] T043 [US1] Add structured logging for US1 tool invocations (INFO level: parameters, duration, match_type)

**Checkpoint**: User Story 1 complete - entity resolution, full documentation retrieval, source code access, file exploration all functional and tested independently

---

## Phase 4: User Story 2 - Documentation Search (Priority: P2)

**Goal**: AI assistant can perform hybrid semantic + keyword search with filters and explicit degradation handling when embedding service is unavailable

**Independent Test**: Issue natural language queries (e.g., "poison damage over time", "player authentication") and verify results include relevant entities with high scores. Test keyword-only mode by disabling embedding endpoint.

### Tests for User Story 2

- [X] T044 [P] [US2] Contract test for search tool in tests/test_tools.py
- [X] T045 [P] [US2] Integration test for hybrid search in tests/test_search.py (semantic + keyword + exact boost, keyword-only mode when embedding unavailable)

### Implementation for User Story 2

- [X] T046 [US2] Implement server/search.py with hybrid search query builder (pgvector + full-text + exact match boost per data-model.md hybrid search query)
- [X] T047 [US2] Implement embedding query in search.py using OpenAI SDK (async, with explicit mode switching: search_mode=keyword_only when embedding service unavailable)
- [X] T048 [US2] Implement score normalization and combination in search.py (exact * 10 + semantic * 0.6 + keyword * 0.4)
- [X] T049 [US2] Implement search filters in search.py (kind, capability, min_doc_quality)
- [X] T050 [US2] Implement search tool in server/tools/search.py (calls search.py, returns SearchResult[] with search_mode indicator; include source parameter defaulting to 'entity', V2-reserved per FR-012)
- [X] T050a [US2] Implement provenance tagging for search results (set provenance field per FR-044: doxygen_extracted, llm_generated, subsystem_narrative based on doc_state)
- [X] T051 [US2] Register search tool in server/server.py with FastMCP decorator
- [X] T052 [US2] Add validation, error handling, and logging for search tool

**Checkpoint**: User Story 2 complete - hybrid search with semantic + keyword ranking, filtering, and explicit mode switching when embedding service unavailable

---

## Phase 5: User Story 3 - Dependency Graph Navigation (Priority: P3)

**Goal**: AI assistant can traverse dependency graph bidirectionally, explore class hierarchies, and identify related files

**Independent Test**: Query known entities with documented call relationships (e.g., `damage` calls `update_pos`, `do_kill` is called by `interpret`) and verify returned call chains match edges in code_graph.gml

### Tests for User Story 3

- [X] T053 [P] [US3] Contract test for graph navigation tools in tests/test_tools.py
- [X] T054 [P] [US3] Integration test for graph traversal in tests/test_graph.py (callers, callees, dependencies, hierarchies at various depths)

### Implementation for User Story 3

#### Graph Traversal Algorithms

- [X] T055 [US3] Implement BFS caller traversal in server/graph.py (backward CALLS edges, configurable depth 1-3, deduplication)
- [X] T056 [US3] Implement BFS callee traversal in server/graph.py (forward CALLS edges, configurable depth 1-3, deduplication)
- [X] T057 [US3] Implement filtered dependency traversal in server/graph.py (by relationship type: calls, uses, inherits, includes, contained_by)
- [X] T058 [US3] Implement class hierarchy traversal in server/graph.py (INHERITS edges, both directions: ancestors and descendants)

#### Tool Implementations

- [X] T059 [P] [US3] Implement get_callers tool in server/tools/graph.py (calls graph.py, returns callers_by_depth with TruncationMetadata; populate provenance='precomputed' per FR-044)
- [X] T060 [P] [US3] Implement get_callees tool in server/tools/graph.py (calls graph.py, returns callees_by_depth with TruncationMetadata; populate provenance='precomputed' per FR-044)
- [X] T061 [P] [US3] Implement get_dependencies tool in server/tools/graph.py (filtered by relationship + direction; populate provenance='precomputed' per FR-044)
- [X] T062 [P] [US3] Implement get_class_hierarchy tool in server/tools/graph.py (base classes and derived classes; populate provenance='precomputed' per FR-044)
- [X] T063 [P] [US3] Implement get_related_entities tool in server/tools/graph.py (all direct neighbors grouped by relationship type; populate provenance='precomputed' per FR-044)
- [X] T064 [P] [US3] Implement get_related_files tool in server/tools/graph.py (INCLUDES edges, co-dependency, shared entities; populate provenance='inferred' per FR-044)

#### Server Integration

- [X] T065 [US3] Register all US3 tools in server/server.py with FastMCP decorators
- [X] T066 [US3] Add validation, error handling, and logging for US3 tools

**Checkpoint**: User Story 3 complete - bidirectional graph traversal, class hierarchies, related files all functional and tested

---

## Phase 6: User Story 4 - Behavioral Analysis (Priority: P4)

**Goal**: AI assistant can compute call cones, analyze capabilities touched, identify side effects, and find hotspots

**Independent Test**: Compute behavior slices for known entry points (e.g., `do_kill`, `spell_fireball`) and validate call cones match BFS traversal of dependency graph. Verify side-effect markers are correctly categorized.

### Tests for User Story 4

- [X] T067 [P] [US4] Contract test for behavioral analysis tools in tests/test_tools.py
- [X] T068 [P] [US4] Integration test for behavior slice computation in tests/test_graph.py (call cone, capabilities touched, side effects)

### Implementation for User Story 4

#### Behavior Analysis Algorithms

- [X] T069 [US4] Implement call cone BFS in server/graph.py (max_depth=5, max_cone_size=200, separate direct vs transitive)
- [X] T070 [US4] Implement capability touch analysis in server/graph.py (map functions in cone to capabilities, count direct vs transitive)
- [X] T071 [US4] Implement global variable usage analysis in server/graph.py (USES edges from cone entities, label direct vs transitive)
- [X] T072 [US4] Implement side-effect marker extraction in server/graph.py (check cone functions against side_effect_markers JSONB field, categorize by type)

#### Tool Implementations

- [X] T073 [US4] Implement get_behavior_slice tool in server/tools/behavior.py (returns BehaviorSlice with full analysis; populate provenance='inferred' for computed call cone per FR-044)
- [X] T073a [US4] Implement wave ordering suppression per FR-053 (BehaviorSlice groups by depth but does NOT return explicit wave arrays)
- [X] T074 [US4] Implement get_state_touches tool in server/tools/behavior.py (direct + transitive global variable usage, side-effect markers; populate provenance='heuristic' per FR-044)
- [X] T075 [US4] Implement get_hotspots tool in server/tools/behavior.py (ranked by fan_in, fan_out, bridge, or underdocumented metrics)

#### Server Integration

- [X] T076 [US4] Register all US4 tools in server/server.py with FastMCP decorators
- [X] T077 [US4] Add validation, error handling, and logging for US4 tools

**Checkpoint**: User Story 4 complete - behavioral analysis with call cones, capability touches, side effects, and hotspot detection all functional

---

## Phase 7: User Story 5 - Capability System and Entry Point Analysis (Priority: P5)

**Goal**: AI assistant can navigate capability groups, understand architectural organization, analyze entry points, and compare capabilities

**Independent Test**: Compare returned capability definitions against capability_defs.json and relationships against capability_graph.json. Verify entry point detection correctly identifies `do_*`, `spell_*`, `spec_*` functions.

### Tests for User Story 5

- [X] T078 [P] [US5] Contract test for capability tools in tests/test_tools.py
- [X] T079 [P] [US5] Integration test for capability analysis in tests/test_graph.py (capability details, comparisons, entry point detection)

### Implementation for User Story 5

#### Tool Implementations

- [X] T080 [P] [US5] Implement list_capabilities tool in server/tools/capability.py (SELECT all from capabilities table with metadata; populate provenance='precomputed' per FR-044)
- [X] T081 [P] [US5] Implement get_capability_detail tool in server/tools/capability.py (capability + dependencies + entry points, optional full function list; populate provenance='precomputed' per FR-044)
- [X] T082 [P] [US5] Implement compare_capabilities tool in server/tools/capability.py (shared dependencies, unique dependencies, bridge entities; populate provenance='inferred' per FR-044)
- [X] T083 [P] [US5] Implement list_entry_points tool in server/tools/capability.py (SELECT WHERE is_entry_point=true, filterable by capability + name pattern; populate provenance='heuristic' per FR-044)
- [X] T084 [P] [US5] Implement get_entry_point_info tool in server/tools/capability.py (which capabilities entry point exercises with direct/transitive counts; populate provenance='inferred' per FR-044)

#### Server Integration

- [X] T085 [US5] Register all US5 tools in server/server.py with FastMCP decorators
- [X] T086 [US5] Add validation, error handling, and logging for US5 tools

**Checkpoint**: User Story 5 complete - capability system navigation, entry point analysis, architectural understanding all functional

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Resources, prompts, documentation, and final validation

### MCP Resources

- [X] T087 [P] Implement resources.py with legacy://capabilities resource handler
- [X] T088 [P] Implement resources.py with legacy://capability/{name} resource handler
- [X] T089 [P] Implement resources.py with legacy://entity/{entity_id} resource handler
- [X] T090 [P] Implement resources.py with legacy://file/{path} resource handler
- [X] T091 [P] Implement resources.py with legacy://stats resource handler
- [X] T092 Register all resources in server/server.py with FastMCP decorators

### MCP Prompts

- [X] T093 [P] Implement prompts.py with explain_entity prompt (multi-step entity analysis workflow)
- [X] T094 [P] Implement prompts.py with analyze_behavior prompt (behavioral analysis workflow)
- [X] T095 [P] Implement prompts.py with compare_entry_points prompt (entry point comparison workflow)
- [X] T096 [P] Implement prompts.py with explore_capability prompt (capability exploration workflow)
- [X] T097 Register all prompts in server/server.py with FastMCP decorators

### Documentation & Validation

- [X] T098 [P] Update README.md with complete setup instructions per quickstart.md
- [X] T099 [P] Add inline docstrings to all modules explaining design rationale
- [X] T100 Run build script validation (uv run python build_mcp_db.py) and verify database population succeeds
- [X] T101 Run server startup validation (uv run python -m server.server) and verify graph loads in < 5 seconds
- [X] T102 Run full test suite (uv run pytest tests/) and verify all tests pass
- [X] T103 Run mypy strict type checking (uv run mypy server/ build_helpers/ --strict) and resolve all errors
- [X] T104 Run ruff linting (uv run ruff check server/ build_helpers/) and resolve all issues
- [X] T105 Execute quickstart.md validation scenarios (entity resolution, hybrid search, behavior analysis)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - **BLOCKS all user stories**
- **User Stories (Phase 3-7)**: All depend on Foundational phase completion
  - User stories can proceed in parallel (if staffed)
  - Or sequentially in priority order (US1 → US2 → US3 → US4 → US5)
- **Polish (Phase 8)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational - Independent (reuses resolver.py from US1 but no blocking dependency)
- **User Story 3 (P3)**: Can start after Foundational - Independent (uses graph.py loaded in foundational)
- **User Story 4 (P4)**: Can start after Foundational - Independent (uses graph.py, extends with behavior algorithms)
- **User Story 5 (P5)**: Can start after Foundational - Independent (queries capabilities table)

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Models/schemas before algorithms
- Algorithms before tools
- Tools before server registration
- Story complete (all checkpoints passed) before moving to next priority

### Parallel Opportunities

**Setup Phase:**
- T003, T004, T005, T006 can run in parallel (different files)

**Foundational Phase:**
- T026, T027, T028 (test setup) can run in parallel with build script work
- Build helpers modules (T010-T018) can be developed in parallel after schema (T008) is complete

**User Story 1:**
- T027, T028 (tests) can run in parallel
- T036-T040 (tool implementations) can run in parallel after resolver.py (T029-T034) is complete

**User Story 2:**
- T044, T045 (tests) can run in parallel

**User Story 3:**
- T053, T054 (tests) can run in parallel
- T059-T064 (tool implementations) can run in parallel after graph algorithms (T055-T058) are complete

**User Story 4:**
- T067, T068 (tests) can run in parallel

**User Story 5:**
- T078, T079 (tests) can run in parallel
- T080-T084 (tool implementations) can all run in parallel (independent tools)

**Polish Phase:**
- T087-T091 (resources) can run in parallel
- T093-T096 (prompts) can run in parallel
- T098, T099 (documentation) can run in parallel

**Cross-Story Parallelism:**
- Once Foundational phase completes, all user stories (US1-US5) can start in parallel if team capacity allows
- Different developers can work on different user stories simultaneously

---

## Parallel Example: Foundational Phase

```bash
# After T008 (schema) completes, launch in parallel:
Task T010: "Implement entity loading in build_helpers/loaders.py"
Task T011: "Implement documentation loading in build_helpers/loaders.py"
Task T017: "Implement graph_loader.py to parse code_graph.gml"
Task T018: "Implement embeddings_loader.py to unpickle embeddings"

# Tests can start immediately in parallel:
Task T026: "Create tests/conftest.py with pytest fixtures"
Task T027: "Contract test for resolve_entity"
```

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together:
Task T027: "Contract test for resolve_entity tool in tests/test_tools.py"
Task T028: "Integration test for entity resolution pipeline in tests/test_resolution.py"

# After resolver.py completes, launch all tool implementations together:
Task T036: "Implement resolve_entity tool in server/tools/entity.py"
Task T037: "Implement get_entity tool in server/tools/entity.py"
Task T038: "Implement get_source_code tool in server/tools/entity.py"
Task T039: "Implement list_file_entities tool in server/tools/entity.py"
Task T040: "Implement get_file_summary tool in server/tools/entity.py"
```

---

## Parallel Example: All User Stories (With Team)

```bash
# Once Foundational (Phase 2) completes:
Developer A: Implement User Story 1 (T026-T043)
Developer B: Implement User Story 2 (T044-T052)
Developer C: Implement User Story 3 (T053-T066)
Developer D: Implement User Story 4 (T067-T077)
Developer E: Implement User Story 5 (T078-T086)

# Each story completes independently and integrates via shared infrastructure (db.py, graph.py, models.py)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T006)
2. Complete Phase 2: Foundational (T007-T025) - **CRITICAL GATE**
3. Complete Phase 3: User Story 1 (T026-T043)
4. **STOP and VALIDATE**: Run quickstart.md entity resolution scenarios
5. Deploy/demo if ready - **MVP delivered!**

### Incremental Delivery (Recommended)

1. Complete Setup + Foundational (T001-T025) → Foundation ready
2. Add User Story 1 (T026-T043) → Test independently → Deploy/Demo (**MVP!**)
3. Add User Story 2 (T044-T052) → Test independently → Deploy/Demo (search capability added)
4. Add User Story 3 (T053-T066) → Test independently → Deploy/Demo (graph navigation added)
5. Add User Story 4 (T067-T077) → Test independently → Deploy/Demo (behavioral analysis added)
6. Add User Story 5 (T078-T086) → Test independently → Deploy/Demo (capability system added)
7. Add Polish (T087-T105) → Complete feature

Each story adds value without breaking previous stories.

### Parallel Team Strategy

With 3+ developers:

1. Team completes Setup + Foundational together (T001-T025)
2. Once Foundational is done:
   - Developer A: User Story 1 (entity lookup)
   - Developer B: User Story 2 (search)
   - Developer C: User Story 3 (graph navigation)
   - (Optional) Developer D: User Story 4 (behavior)
   - (Optional) Developer E: User Story 5 (capabilities)
3. Stories complete independently and integrate via shared infrastructure
4. Merge in priority order: US1 → US2 → US3 → US4 → US5

---

## Notes

- [P] tasks = different files, no dependencies within same phase
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable
- Verify tests fail before implementing (TDD for PoC-level integration tests)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Build script (Phase 2) is CRITICAL - half the deliverable, blocks all user stories
- Server startup must load graph in < 5 seconds (performance requirement from spec.md)
- All tools must include resolution envelope for entity name parameters
- All list-returning tools must include truncation metadata
- All tools must populate provenance field per FR-044 (doxygen_extracted, llm_generated, subsystem_narrative, precomputed, inferred, heuristic, measured)
- Search must use explicit mode switching when embedding service unavailable (no "fallbacks" per PATTERNS.md)
- Database schema defined in server/db_models.py (canonical location); build_helpers imports from server to avoid circular dependencies
- Database access uses SQLModel table models + SQLAlchemy async sessions; repositories encapsulate queries per SQLMODEL.md
- Type checking with mypy --strict enforced (no `Any` in production paths)

---

## Task Count Summary

- **Phase 1 (Setup)**: 6 tasks
- **Phase 2 (Foundational)**: 22 tasks (includes 3 test setup tasks + T019a entry_points, T022a schema note, T022b provenance models)
- **Phase 3 (User Story 1)**: 18 tasks (3 test + 15 implementation)
- **Phase 4 (User Story 2)**: 10 tasks (2 test + 8 implementation, +T050a provenance)
- **Phase 5 (User Story 3)**: 14 tasks (2 test + 12 implementation)
- **Phase 6 (User Story 4)**: 12 tasks (2 test + 10 implementation, +T073a wave suppression)
- **Phase 7 (User Story 5)**: 9 tasks (2 test + 7 implementation)
- **Phase 8 (Polish)**: 19 tasks (resources, prompts, docs, validation)

**Total**: 110 tasks

**Parallel Opportunities**: ~40 tasks marked [P] can run in parallel within their phases

**Independent User Stories**: All 5 user stories can proceed in parallel after Foundational phase (if team capacity allows)

**Suggested MVP Scope**: Phase 1 + Phase 2 + Phase 3 (User Story 1 only) = **46 tasks**
