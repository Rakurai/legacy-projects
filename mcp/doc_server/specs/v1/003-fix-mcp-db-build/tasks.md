# Tasks: Fix MCP Database Build Script

**Input**: Design documents from `/specs/003-fix-mcp-db-build/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, quickstart.md

**Tests**: Not explicitly requested in spec. Validation via existing `test_database.py` after full build.

**Organization**: Tasks grouped by user story. US1 and US2 are P1 (MVP), US3-US5 are P2 (follow-on).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2)
- Includes exact file paths in descriptions

---

## Phase 1: Setup

**Purpose**: No project initialization needed — this is a bugfix to an existing project. Load capability graph earlier in the pipeline.

- [x] T001 Reorder `main()` to load capability graph before graph metrics computation in `.ai/mcp/doc_server/build_mcp_db.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Add capability assignment infrastructure that US1 (indexes) doesn't need but US2-US5 all require. Also the foundation for correct `doc_quality_dist` computation.

**⚠️ CRITICAL**: US3 (bridge detection) depends on US2 (capability mapping). US4 (function counts) and US5 (capability edges) depend on correct `cap_graph` parsing.

- [x] T002 Add `assign_capabilities()` function to build name→capability mapping from `cap_graph["capabilities"]` members in `.ai/mcp/doc_server/build_helpers/entity_processor.py`
- [x] T003 Add `_capability` instance variable to `MergedEntity.__init__()` and update `capability` property to prefer it over `doc.system` in `.ai/mcp/doc_server/build_helpers/entity_processor.py`
- [x] T004 Call `assign_capabilities(merged_entities, cap_graph)` in `main()` after merge and before bridge detection in `.ai/mcp/doc_server/build_mcp_db.py`

**Checkpoint**: Entity capability assignment infrastructure ready

---

## Phase 3: User Story 1 — Database Indexes Created Successfully (Priority: P1) 🎯 MVP

**Goal**: All 14 secondary indexes are created successfully after `build_mcp_db.py` runs.

**Independent Test**: `SELECT COUNT(*) FROM pg_indexes WHERE schemaname = 'public'` returns ≥ 19.

### Implementation for User Story 1

- [x] T005 [US1] Refactor `drop_and_create_schema()` to accept `engine` parameter instead of `session` and use it for `create_all()` in `.ai/mcp/doc_server/build_mcp_db.py`
- [x] T006 [US1] Move index creation to use `engine.begin()` with `CREATE INDEX IF NOT EXISTS` in `.ai/mcp/doc_server/build_mcp_db.py`
- [x] T007 [US1] Update `main()` to pass `db_manager.engine` to `drop_and_create_schema()` and call it outside the session context manager in `.ai/mcp/doc_server/build_mcp_db.py`

**Checkpoint**: Run `uv run python build_mcp_db.py` then verify 19+ indexes via `test_database.py`

---

## Phase 4: User Story 2 — Entity-to-Capability Mapping Populated (Priority: P1) 🎯 MVP

**Goal**: ~848 entities have their `capability` field set from `capability_graph.json` members.

**Independent Test**: `SELECT COUNT(*) FROM entities WHERE capability IS NOT NULL` ≈ 848.

### Implementation for User Story 2

- [x] T008 [US2] Fix docstring for `load_capability_graph()` to document actual nested dict format (`dependencies`, `capabilities.members`) in `.ai/mcp/doc_server/build_helpers/loaders.py`

**Checkpoint**: Run full build, query entities — ~848 should have capability set. Bridge detection (US3) should now also produce results automatically.

---

## Phase 5: User Story 3 — Bridge Functions Detected (Priority: P2)

**Goal**: Entities with cross-capability callers AND callees are flagged `is_bridge = true`.

**Independent Test**: `SELECT COUNT(*) FROM entities WHERE is_bridge = true` > 10.

### Implementation for User Story 3

No additional code changes required. Bridge detection is a cascading fix from US2 (capability assignment). The existing `compute_bridge_flags()` in `.ai/mcp/doc_server/build_helpers/graph_loader.py` works correctly once capabilities are populated.

- [x] T009 [US3] Verify bridge detection produces > 10 results after full build by running `uv run python test_database.py` and checking bridge function output

**Checkpoint**: Bridge functions appear in test output

---

## Phase 6: User Story 4 — Capability Function Counts and Descriptions Correct (Priority: P2)

**Goal**: All 30 capabilities have correct `function_count > 0` and non-empty `description`.

**Independent Test**: `SELECT COUNT(*) FROM capabilities WHERE function_count = 0` = 0.

### Implementation for User Story 4

- [x] T010 [P] [US4] Fix `populate_capabilities()` to read description from `cap_def.get("desc", "")` instead of `"description"` in `.ai/mcp/doc_server/build_mcp_db.py`
- [x] T011 [P] [US4] Fix `populate_capabilities()` to read `function_count` from `cap_graph["capabilities"][cap_name]["function_count"]` instead of `len(cap_def.get("functions", []))` in `.ai/mcp/doc_server/build_mcp_db.py`
- [x] T012 [US4] Fix `populate_capabilities()` to compute `doc_quality_dist` by aggregating entity doc_quality per capability instead of hard-coded zeros in `.ai/mcp/doc_server/build_mcp_db.py`

**Checkpoint**: All capabilities show correct function counts and descriptions in test output

---

## Phase 7: User Story 5 — Capability Edges Populated (Priority: P2)

**Goal**: `capability_edges` table contains 200 rows from `capability_graph.json` dependencies.

**Independent Test**: `SELECT COUNT(*) FROM capability_edges` = 200.

### Implementation for User Story 5

- [x] T013 [US5] Fix `populate_capabilities()` capability edges section to parse `cap_graph.get("dependencies", {})` as nested dict instead of `cap_graph.get("edges", [])` as flat list in `.ai/mcp/doc_server/build_mcp_db.py`

**Checkpoint**: 200 capability edges appear in test output

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Full validation and cleanup

- [x] T014 Run full build (`uv run python build_mcp_db.py`) and validate all success criteria via `uv run python test_database.py`
- [x] T015 Verify build completes in < 60 seconds (SC-007)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — reorder `main()` pipeline
- **Phase 2 (Foundational)**: Depends on Phase 1 — adds capability assignment
- **Phase 3 (US1 — Indexes)**: Independent of Phase 2 — can run in parallel with US2
- **Phase 4 (US2 — Capabilities)**: Depends on Phase 2 — uses new `assign_capabilities()`
- **Phase 5 (US3 — Bridges)**: Depends on US2 (cascading fix, no code changes)
- **Phase 6 (US4 — Counts/Desc)**: Independent of US2/US3 — parallel with Phase 4
- **Phase 7 (US5 — Cap Edges)**: Independent of US2/US3/US4 — parallel with Phase 4
- **Phase 8 (Polish)**: Depends on all phases complete

### User Story Dependencies

- **US1 (P1)**: Independent — index fix is self-contained in `drop_and_create_schema()`
- **US2 (P1)**: Depends on Phase 2 foundational work (capability assignment function)
- **US3 (P2)**: Depends on US2 only (cascading fix, no new code)
- **US4 (P2)**: Independent of US2 — field name fixes in `populate_capabilities()`
- **US5 (P2)**: Independent of US2 — format fix in `populate_capabilities()`

### Parallel Opportunities

Within the build script, T010 and T011 can be done in parallel (different parts of same function).
US1, US4, and US5 are independent and can be implemented in parallel.
US3 requires no implementation, only verification after US2.

---

## Parallel Example: Independent Fixes

```bash
# These can run in parallel (different concerns, same file but different functions):
T005-T007: Fix index creation engine (drop_and_create_schema)
T010-T011: Fix capability field names (populate_capabilities)
T013:      Fix capability edges parsing (populate_capabilities)
```

---

## Implementation Strategy

### MVP First (US1 + US2)

1. **Phase 1**: Reorder pipeline (T001) — 1 min
2. **Phase 2**: Add capability assignment (T002-T004) — 5 min
3. **Phase 3**: Fix index creation (T005-T007) — 10 min
4. **Phase 4**: Fix docstring (T008) — 2 min
5. **VALIDATE**: Run build + test → verify SC-001 (19 indexes), SC-002 (~848 caps), SC-003 (bridges > 10)

### Complete Delivery (US4 + US5)

6. **Phase 6**: Fix capability counts/desc (T010-T012) — 5 min
7. **Phase 7**: Fix capability edges (T013) — 5 min
8. **Phase 8**: Full validation (T014-T015) — 2 min

### Total Estimated Time: ~30 minutes implementation + build/test cycles

---

## Notes

- All changes confined to 3 files: `build_mcp_db.py`, `entity_processor.py`, `loaders.py`
- Schema (`server/db_models.py`) is untouched
- No new dependencies or files
- US3 (bridge detection) requires zero code changes — it's a cascading fix from US2
- The `populate_capabilities()` function in `build_mcp_db.py` receives 3 separate fixes (T010, T011-T012, T013)
