# Tasks: Dead Code Purge & API Cleanup

**Input**: Design documents from `/specs/008-dead-code-api-cleanup/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/tools.md, quickstart.md

**Tests**: Tests are included where existing tests need modification or removal. No TDD approach — this is a subtraction spec.

**Organization**: Tasks are grouped by user story (P1–P3). Each story can be implemented and tested independently after the foundational phase.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup

**Purpose**: No new project structure needed. This phase handles shared prerequisites that unblock all user stories.

- [X] T001 Remove `SideEffectCategory`, `Confidence`, `Provenance`, and `HotspotMetric` enums from `mcp/doc_server/server/enums.py`
- [X] T002 Remove `SideEffectMarker` model and `provenance` field from all models in `mcp/doc_server/server/models.py` (EntitySummary, EntityNeighbor, EntityDetail, SearchResult, CapabilityTouch, GlobalTouch, BehaviorSlice, CapabilitySummary, CapabilityDetail); remove `side_effects` dict from BehaviorSlice; remove `side_effect_markers` from EntityDetail; remove `SideEffectCategory`, `Confidence`, `Provenance` imports
- [X] T003 Remove `Entity.side_effect_markers` JSONB field from `mcp/doc_server/server/db_models.py`
- [X] T004 Remove `provenance=` assignments and `side_effect_markers=` pass-through from all converter functions in `mcp/doc_server/server/converters.py`; remove `Provenance` import
- [X] T005 [P] Remove `Provenance` import and `provenance=` assignment in search result construction in `mcp/doc_server/server/search.py`
- [X] T006 [P] Remove `side_effect_markers` from entity resource dict in `mcp/doc_server/server/resources.py`
- [X] T007 Remove `side_effect_markers` from test fixtures in `mcp/doc_server/tests/conftest.py`

**Checkpoint**: All dead enums, model fields, DB columns, and converter references removed. Remaining work is tool-level changes.

---

## Phase 2: Foundational (Build Pipeline Cleanup)

**Purpose**: Remove dead code from the build pipeline. MUST complete before database rebuild validation.

- [X] T008 [P] Remove `SIDE_EFFECT_FUNCTIONS` dict and `MergedEntity.side_effect_markers` attribute from `mcp/doc_server/build_helpers/entity_processor.py`
- [X] T009 [P] Remove `compute_side_effect_markers()` function, `_SIDE_EFFECT_BFS_DEPTH` constant, and `SIDE_EFFECT_FUNCTIONS` import from `mcp/doc_server/build_helpers/graph_loader.py`
- [X] T010 Remove `compute_side_effect_markers` import and call, and `side_effect_markers=` assignment in `populate_entities()` from `mcp/doc_server/build_mcp_db.py`

**Checkpoint**: Build pipeline no longer computes or persists dead fields. Ready for tool-level changes.

---

## Phase 3: User Story 1 — Smaller, Accurate Tool Responses (Priority: P1) 🎯 MVP

**Goal**: All entity-returning tools produce responses with zero vestigial fields. No `provenance`, `side_effect_markers`, or `side_effects` in any API response.

**Independent Test**: Call every entity-returning tool and verify no response contains removed field names. Run `uv run pytest tests/ -v` and confirm all tests pass.

### Implementation for User Story 1

- [X] T011 [P] [US1] Remove `_extract_side_effects_for_entities()` function, all side-effect extraction from `get_behavior_slice` (remove `side_effects=` construction and `side_effects` argument to `BehaviorSlice`), and all side-effect extraction from `get_state_touches` (remove `direct_side_effects`/`transitive_side_effects` from `StateTouchesResponse` construction and the indirect callee fetch block) in `mcp/doc_server/server/tools/behavior.py`; remove `SideEffectCategory`, `Confidence`, `Provenance`, `SideEffectMarker` imports
- [X] T012 [P] [US1] Remove `provenance=` from capability detail construction in `mcp/doc_server/server/tools/capability.py`
- [X] T013 [P] [US1] Remove provenance assertions and side-effect assertions from `mcp/doc_server/tests/test_behavior_tools.py` (update `test_behavior_slice` to not check `side_effects`; update `test_state_touches` to not check `direct_side_effects`/`transitive_side_effects`)
- [X] T014 [P] [US1] Remove provenance-specific tests from `mcp/doc_server/tests/test_converters.py` (remove `TestProvenanceFor` class and provenance assertions)
- [X] T015 [P] [US1] Remove `_provenance_for` import, tests, and provenance assertions from `mcp/doc_server/tests/test_search_units.py`
- [X] T016 [P] [US1] Remove provenance assertions from `mcp/doc_server/tests/test_search.py` (remove `test_search_provenance_tagging` test or provenance field checks)
- [X] T017 [P] [US1] Remove side_effect_markers assertions from `mcp/doc_server/tests/test_resources.py`

**Checkpoint**: All API responses are clean of dead fields. Tests pass. SC-002 and SC-007 are satisfied.

---

## Phase 4: User Story 2 — Reduced Tool Surface (Priority: P2)

**Goal**: Tool count drops from 19 to 15. Four low-value tools are removed along with their response models and tests.

**Independent Test**: List registered tools and verify exactly 15. Verify removed tool names are not callable.

### Implementation for User Story 2

- [X] T018 [P] [US2] Remove `get_hotspots` tool function and `HotspotsResponse` model from `mcp/doc_server/server/tools/behavior.py`; remove `HotspotMetric` import
- [X] T019 [P] [US2] Remove `get_file_summary` tool function, `FileSummaryResponse` model, `list_file_entities` tool function, and `ListFileEntitiesResponse` model from `mcp/doc_server/server/tools/entity.py`
- [X] T020 [P] [US2] Remove `get_related_files` tool function and `RelatedFilesResponse` model from `mcp/doc_server/server/tools/graph.py`
- [X] T021 [P] [US2] Remove 6 hotspot tests (`test_hotspots_fan_in`, `_fan_out`, `_bridge`, `_underdocumented`, `_with_capability_filter`, `_with_kind_filter`) from `mcp/doc_server/tests/test_behavior_tools.py`
- [X] T022 [P] [US2] Remove 5 tests (`test_list_file_entities`, `_with_kind_filter`, `_empty`, `test_get_file_summary`, `_not_found`) from `mcp/doc_server/tests/test_entity_tools.py`
- [X] T023 [P] [US2] Remove 2 related_files tests (`test_get_related_files`, `test_get_related_files_no_includes`) from `mcp/doc_server/tests/test_graph_tools.py`

**Checkpoint**: Exactly 15 tools registered. SC-001 satisfied. Removed tool tests cleaned up.

---

## Phase 5: User Story 3 — Correct Entry Point / Capability Semantics (Priority: P2)

**Goal**: `get_capability_detail` returns entry points that route into a capability (via transitive call cone). `list_entry_points` drops the `capability` parameter.

**Independent Test**: Call `get_capability_detail("combat")` and verify non-empty `entry_points`. Call `list_entry_points` and verify it does not accept `capability`.

### Implementation for User Story 3

- [X] T024 [US3] Enrich `EntryPoint.capabilities` JSONB at build time in `mcp/doc_server/build_mcp_db.py` `populate_entry_points()`: compute call cone per entry point and collect all capability names touched transitively, storing the full list in the JSONB column
- [X] T025 [US3] Fix `get_capability_detail` entry_points query in `mcp/doc_server/server/tools/capability.py`: replace `Entity.capability == capability` join with query on `EntryPoint.capabilities` JSONB containment (e.g., `EntryPoint.capabilities.contains([capability])` or cast + `ANY`)
- [X] T026 [US3] Remove `capability` parameter from `list_entry_points` in `mcp/doc_server/server/tools/capability.py`; remove the `Entity.capability == capability` filter branch
- [X] T027 [P] [US3] Update `mcp/doc_server/tests/test_capability_tools.py` if it tests `list_entry_points` with capability filter — remove or update those assertions

**Checkpoint**: SC-006 satisfied — `get_capability_detail` returns non-empty entry_points for capabilities with command dispatchers.

---

## Phase 6: User Story 4 — Tool Parameters Match Contracts (Priority: P3)

**Goal**: Every tool parameter name, default, and value set matches the published contract.

**Independent Test**: Call each modified tool with contract-specified parameters and verify correct behavior.

### Implementation for User Story 4

- [X] T028 [US4] Rename `limit` → `top_k` (default `20` → `10`) in `mcp/doc_server/server/tools/search.py` tool signature, log call, and pass-through to `hybrid_search(limit=top_k)`
- [X] T029 [US4] Add `direction` parameter (`"ancestors"` | `"descendants"` | `"both"`, default `"both"`) to `get_class_hierarchy` in `mcp/doc_server/server/tools/graph.py` and `mcp/doc_server/server/graph.py` helper; gate base_classes/derived_classes collection on direction value
- [X] T030 [US4] Change `get_dependencies` default `direction` from `"both"` to `"outgoing"` in `mcp/doc_server/server/tools/graph.py`
- [X] T031 [US4] Restructure `get_related_entities` in `mcp/doc_server/server/tools/graph.py`: rename `limit` → `limit_per_type` (default `100` → `20`); remove global truncation; group neighbors first, then truncate per group
- [X] T032 [P] [US4] Rename `limit` → `top_k` in search test calls in `mcp/doc_server/tests/test_search_tool.py`
- [X] T033 [P] [US4] Add `direction` parameter tests for `get_class_hierarchy` in `mcp/doc_server/tests/test_graph_tools.py` (test `ancestors` returns only base_classes, `descendants` returns only derived_classes, `both` returns both)

**Checkpoint**: SC-005 satisfied — all tool parameters match contracts. Full test suite passes.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Documentation updates, contract sync, final validation.

- [X] T034 [P] Update `mcp/doc_server/specs/v1/contracts/tools.md` to reflect all parameter renames, removed tools, and entry point semantics changes per `specs/008-dead-code-api-cleanup/contracts/tools.md`
- [X] T035 [P] Add documentation note to `list_entry_points` docstring and `get_capability_detail` docstring in `mcp/doc_server/server/tools/capability.py` explaining that entry points have `capability=NULL` by design (dispatch vs implementation)
- [X] T036 Run quickstart.md verification commands: `uv run pytest tests/ -v`, `uv run mypy server/`, `uv run ruff check .`, grep for dead symbol references, verify tool count is 15
- [X] T037 Validate full database rebuild: run `uv run python -m build_script.build_mcp_db` against artifacts and confirm schema loads without errors (covers SC-003)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — start immediately
- **Phase 2 (Build Pipeline)**: Independent of Phase 1 (different files) — can run in parallel
- **Phases 3-6 (User Stories)**: All depend on Phase 1 completion (models/enums must be removed first)
  - **US1 (Phase 3)**: Depends on Phase 1 only
  - **US2 (Phase 4)**: Depends on Phase 1; **file conflict with US1** — T011 (US1) and T018 (US2) both modify `behavior.py`, T013 (US1) and T021 (US2) both modify `test_behavior_tools.py`. Phase 4 MUST follow Phase 3 completion to avoid merge conflicts
  - **US3 (Phase 5)**: Depends on Phase 2 (build pipeline changes for EntryPoint enrichment)
  - **US4 (Phase 6)**: Independent — can run after Phase 1
- **Phase 7 (Polish)**: Depends on all phases complete

### User Story Dependencies

- **US1 (P1)**: Can start after Phase 1 — no dependencies on other stories
- **US2 (P2)**: Can start after Phase 3 — shares `behavior.py` and `test_behavior_tools.py` with US1
- **US3 (P2)**: Can start after Phase 2 — independent of US1/US2
- **US4 (P3)**: Can start after Phase 1 — independent of US1/US2/US3

### Parallel Opportunities

Within each phase, tasks marked [P] can run in parallel (they touch different files).

Key parallel batches:
- T005 + T006 (search.py + resources.py) — parallel in Phase 1
- T008 + T009 (entity_processor.py + graph_loader.py) — parallel in Phase 2
- T011 + T012 (behavior.py + capability.py) — parallel in Phase 3
- T018 + T019 + T020 (behavior.py + entity.py + graph.py) — parallel in Phase 4
- T028 through T031 are sequential (T029-T031 touch graph.py and must be ordered; T028 touches search.py)
- T032 + T033 (test files) — parallel in Phase 6

---

## Parallel Example: User Story 2

```bash
# All tool removals touch different files — launch in parallel:
T018: Remove get_hotspots from behavior.py
T019: Remove get_file_summary + list_file_entities from entity.py
T020: Remove get_related_files from graph.py

# All test removals touch different files — launch in parallel:
T021: Remove hotspot tests from test_behavior_tools.py
T022: Remove entity tests from test_entity_tools.py
T023: Remove graph tests from test_graph_tools.py
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Remove dead enums, models, DB fields
2. Complete Phase 2: Clean build pipeline (parallel with Phase 1)
3. Complete Phase 3: Update behavior/capability tools and tests
4. **STOP and VALIDATE**: Run full test suite — all entity responses are clean
5. SC-002 and SC-007 met

### Incremental Delivery

1. Phase 1 + 2 → Foundation clean
2. Add US1 (Phase 3) → All responses clean → Validate (MVP!)
3. Add US2 (Phase 4) → Tool count = 15 → Validate
4. Add US3 (Phase 5) → Entry point semantics correct → Validate
5. Add US4 (Phase 6) → Parameters match contracts → Validate
6. Phase 7 → Docs and final verification → Done
