# Tasks: V1 Known Issue Fixes

**Input**: Design documents from `/specs/002-v1-issue-fixes/`
**Branch**: `002-v1-issue-fixes`

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on in-progress tasks)
- **[Story]**: User story this task belongs to (US1=contract seed discovery + graph traversal, US2=graph traversal, US3=search noise filtering)
- Note: US1 and US2 are served by the same I-001 fix; they are grouped in a single phase

---

## Phase 1: Setup

**Purpose**: Confirm baseline before changes

- [X] T001 Run existing test suite to establish baseline: `cd mcp/doc_server && uv run pytest tests/ -v` — all tests must pass before any changes are made

---

## Phase 2: Foundational (Blocking Prerequisite)

**Purpose**: `load_graph_node_ids()` is required by `merge_entities()` in US1/US2. Must be complete before entity merge work begins.

**⚠️ CRITICAL**: US1/US2 implementation (Phase 3) cannot begin until this phase is complete.

- [X] T002 Add `load_graph_node_ids(artifacts_path: Path) -> frozenset[str]` to `mcp/doc_server/build_helpers/graph_loader.py` — reads raw GML via `nx.read_gml`, returns `frozenset(G.nodes())`; no entity lookup; fully typed; `from loguru import logger as log` for any logging

**Checkpoint**: Foundation ready — US1/US2 entity merge work can begin

---

## Phase 3: User Stories 1 & 2 — Entity Merge (Priority: P1) 🎯 MVP

**Goal**: Every logical entity is stored as a single unified database record carrying both graph metrics and documentation. Contract seed discovery and graph traversal yield complete data.

**Independent Test**: Query the rebuilt database for `stc` — expect one record with `fan_in=640`, `is_contract_seed=true`, and non-empty `calling_patterns` via `explain_interface`.

### Implementation for User Stories 1 & 2

> **Before starting T004**: Confirm the exact attribute name for file path on `DoxygenEntity` from type stubs in `packages/legacy_common/` (likely `entity.location.file` or `entity.location` — verify before writing the dedup key). This takes ~5 minutes and prevents a rework loop.

- [X] T003 [US1] Add `TestMergeEntitiesDedup` test class to `mcp/doc_server/tests/test_entity_processor.py` with three cases: (a) split pair → one MergedEntity with merged doc; (b) neither compound in GML node set → `BuildError`; (c) single entity (no split) → unchanged — draft skeleton can be written in parallel with T004, but finalize and run only after T004's new `merge_entities(graph_node_ids)` signature is in place; depends on T004 to run

- [X] T004 [P] [US1] Modify `merge_entities()` in `mcp/doc_server/build_helpers/entity_processor.py`:
  - Change signature to `merge_entities(entity_db, doc_db, graph_node_ids: frozenset[str]) -> list[MergedEntity]`
  - After collecting all entities, group by `(entity.name, entity.signature, entity.location.file)` — verify exact DoxygenEntity attribute for file path from type stubs in `packages/legacy_common/`
  - For single-entity groups: construct `MergedEntity` as before
  - For multi-entity groups: select survivor whose `entity.id.member or entity.id.compound` is in `graph_node_ids`; if neither → `raise BuildError(...)`; if both → prefer definition file (`.cc`/`.cpp`); copy `doc` from sibling onto survivor when `survivor.doc is None`; emit `log.info("split entity merged", name=..., surviving_compound=..., discarded_compound=...)`
  - Return deduplicated list

- [X] T005 [US1] Update `build_mcp_db.py::main()` — call `load_graph_node_ids(config.artifacts_path)` before the `merge_entities()` call; pass the returned `frozenset[str]` as the `graph_node_ids` argument to `merge_entities()`; depends on T002 and T004

- [X] T006 [US1] Run test suite: `cd mcp/doc_server && uv run pytest tests/test_entity_processor.py -v` — T003 tests must pass; no existing tests may regress; depends on T003, T004

- [X] T007 [US1] Rebuild database: `cd mcp/doc_server && uv run python -m build_script.build_mcp_db` — confirm build log emits "split entity merged" entries for known split pairs (`stc`, `damage`, `interpret`); confirm entity count decreases vs pre-fix baseline; depends on T005

- [X] T008 [US1] Verify I-004 regression via running MCP server: (a) `search(query="stc")` → one result with `fan_in=640` and `is_contract_seed=true`; `explain_interface` on returned entity_id → `calling_patterns` non-empty; (b) `search(query="damage")` → one result (not two); (c) `search(query="interpret")` → one result with `calling_patterns` non-empty via `explain_interface` — covers US2 scenario 2 (general case); depends on T007

**Checkpoint**: US1 and US2 fully functional. Single entity record per logical entity. Contract seed discovery and graph traversal return complete data.

---

## Phase 4: User Story 3 — Search Noise Filtering (Priority: P2)

**Goal**: Queries with no meaningful match return zero results. Score reflects absolute match quality, not per-query rank.

**Independent Test**: `search(query="xyzzy_nonexistent_9f3k")` returns zero results. `search(query="stc")` returns the stc entity as first result with score > 1.0.

### Implementation for User Story 3

- [X] T009 [P] [US3] Add score threshold contract tests to `mcp/doc_server/tests/test_search_tool.py`:
  - `test_nonsense_query_returns_no_results` — mock search to return a result with score below threshold, assert it is excluded
  - `test_exact_match_score_dominates` — mock exact match to score ≥ 10.0, assert it is included regardless of threshold
  - Parallel with T010–T012 since different file

- [X] T010 [US3] Add intra-query keyword score normalization to `_merge_scores()` in `mcp/doc_server/server/search.py`:
  - Before applying `_KEYWORD_WEIGHT`, normalize: `if keyword_scores: max_kw = max(keyword_scores.values()); keyword_scores = {eid: s / max_kw for eid, s in keyword_scores.items()}`
  - This bounds keyword contribution to `[0, 0.4]` regardless of `ts_rank()` magnitude

- [X] T011 [US3] Add `_SCORE_THRESHOLD: float = 0.2` constant at module level in `mcp/doc_server/server/search.py`; replace the per-query normalization block in `hybrid_search()` (lines ~167–169 and the `min(score / normalizer, 1.0)` application) with: exclude results where `score < _SCORE_THRESHOLD`; exact matches score ≥ 10.0 and always pass — no special-casing needed; note: if empirical validation in T013 shows SC-003 is not met, adjust `_SCORE_THRESHOLD` upward and re-run T013; depends on T010

- [X] T012 [US3] Apply the same threshold filter to `hybrid_search_usages()` in `mcp/doc_server/server/search.py` — remove per-query normalization block (~lines 313–314), apply `_SCORE_THRESHOLD` exclusion uniformly (no exact-match carve-out for usage search per FR-008); depends on T010

- [X] T013 [US3] Validate threshold against SC-003 and SC-004: run the MCP server against the built database; confirm `search(query="xyzzy_nonexistent_9f3k")` returns zero results (SC-003); confirm `search(query="stc")` returns stc as first result (SC-004); if SC-003 fails, adjust `_SCORE_THRESHOLD` in T011 and rerun; depends on T011, T012

- [X] T014 [US3] Run test suite: `cd mcp/doc_server && uv run pytest tests/test_search_tool.py -v` — T009 tests must pass; no existing tests may regress; depends on T009, T011, T012

**Checkpoint**: US3 fully functional. Nonsense queries return zero results. Exact-name queries return the target entity.

---

## Phase 5: Polish & Cross-Cutting Concerns

- [X] T015 [P] Run full regression suite: `cd mcp/doc_server && uv run pytest tests/ -v` — all tests must pass including pre-existing 37 tests

- [X] T016 [P] Type check: `cd mcp/doc_server && uv run mypy server/ build_helpers/` — strict mode, zero errors; `build_helpers/` included because I-001 adds new typed functions there

- [X] T017 [P] Lint and format: `uv run ruff check . && uv run ruff format .` — zero violations

---

## Audit Remediation

> Generated by `/speckit.audit` on 2026-03-20. SD-001/SD-002 dedup key correctness under separate investigation.

- [X] T018 [AR] Fix CV-001: Move `from collections import defaultdict` from inside `merge_entities()` body to module-level imports in `mcp/doc_server/build_helpers/entity_processor.py:220` — it is a stdlib import and belongs at the top of the file with the other imports
- [X] T019 [AR] Fix OE-001: Inline `_node_id()` helper into its single call site in `mcp/doc_server/build_helpers/entity_processor.py:248` — replace `_node_id(e)` with `(str(e.id.member) if e.id.member else str(e.id.compound))` and remove the function definition at lines 192–194
- [X] T020 [AR] Fix CQ-001: In `mcp/doc_server/tests/test_entity_processor.py:140`, change `type="decl"` to `type="file"` in the `DoxygenLocation` constructor used for file locations in `_make_entity()` helper
- [X] T021 [AR] Fix TQ-001: Remove `test_nonsense_query_returns_no_results` from `mcp/doc_server/tests/test_search_tool.py` — it is functionally identical to the pre-existing `test_search_tool_empty_results`; the threshold semantics it was intended to test are already covered by `test_returned_results_score_gte_threshold`
- [X] T022 [AR] Fix SD-001/SD-002: Rewrite dedup key and survivor selection in `merge_entities()` in `mcp/doc_server/build_helpers/entity_processor.py`:
  - **Grouping key**: Group by `entity.id.member` (Doxygen's authoritative member hash) instead of `(entity.name, entity.kind, entity.decl.fn)`. The current key incorrectly groups unrelated entities that share name/kind/file — e.g., `name` fields from 11 different structs in merc.hh all map to the same key.
  - **Entities where `entity.id.member is None`**: Pure compound entities that cannot be split pairs — pass through as single-entity groups unchanged.
  - **Survivor selection**: Replace the `.cc/.cpp` file-extension heuristic with `entity.body is not None` — Doxygen sets `body` only on the definition fragment, never on the declaration. This is deterministic with no fallback needed. If no fragment has `body is not None`, raise `BuildError` (no definition exists in graph).
  - **Remove `_node_id()` helper call** from multi-entity path: with `entity.id.member` grouping, all fragments in a multi-entity group are already confirmed to share the same member hash, so `graph_node_ids` lookup is still needed to find which compound is in the graph, but survivor is determined by `entity.body` not by file extension.
  - **Update `TestMergeEntitiesDedup`** tests in `mcp/doc_server/tests/test_entity_processor.py` to construct test entities with a shared `entity.id.member` hash and verify `entity.body` drives survivor selection.
  - Run full test suite after: `uv run pytest tests/ -v`

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies
- **Phase 2 (Foundational)**: Depends on Phase 1
- **Phase 3 (US1/US2)**: Depends on Phase 2 (T002 must be complete)
- **Phase 4 (US3)**: Independent of Phase 3 — can begin after Phase 1; no dependency on entity merge work
- **Phase 5 (Polish)**: Depends on Phases 3 and 4 complete

### User Story Dependencies

- **US1/US2 (Phase 3)**: Requires T002 (foundational `load_graph_node_ids`)
- **US3 (Phase 4)**: Independent — `server/search.py` changes do not depend on build pipeline changes

### Within Phase 3

```
T002 (foundational) → T004 (merge_entities impl) → T003 (tests, finalized) → T006 (test run)
                                                  → T005 (build_mcp_db reorder) → T007 (rebuild) → T008 (verify I-004)
```

### Within Phase 4

```
T010 (_merge_scores normalization) → T011 (hybrid_search threshold)
                                   → T012 (hybrid_search_usages threshold) → T013 (empirical validation)
T009 (tests) ──────────────────────────────────────────────────────────────────┘ (T014 runs after T009+T011+T012)
```

---

## Parallel Opportunities

### Phase 3 parallelism

```bash
# T003 skeleton can be drafted while T004 is being written (different files),
# but T003 must be finalized and run only after T004's signature is committed.
# True parallel: T004 and T005 touch different files once T002 is done.
Task T004: "Modify merge_entities() dedup logic in entity_processor.py"
Task T005: "Update build_mcp_db.py call site"  # only after T002+T004
```

### Phase 4 parallelism

```bash
# These can run concurrently with each other (same file, but different functions):
# Start T010 first, then T011 and T012 are sequential in the same file.
# T009 (tests, different file) is parallel with all of T010–T012.
Task T009: "Add score threshold tests in test_search_tool.py"
Task T010: "Normalize keyword scores in _merge_scores()"
```

### Phase 3 vs Phase 4 parallelism

Phase 4 (US3) has no dependency on Phase 3 (US1/US2). They touch entirely different files:
- Phase 3: `graph_loader.py`, `entity_processor.py`, `build_mcp_db.py`, `test_entity_processor.py`
- Phase 4: `server/search.py`, `test_search_tool.py`

They can proceed in parallel after Phase 1.

---

## Implementation Strategy

### MVP First (US1/US2)

1. Complete Phase 1: baseline verification
2. Complete Phase 2: `load_graph_node_ids()`
3. Complete Phase 3: entity merge dedup + DB rebuild + I-004 verification
4. **STOP and VALIDATE**: stc is a single record with fan_in=640, is_contract_seed=true
5. Contract seed discovery and graph traversal workflows are now correct

### Incremental Delivery

1. Phase 1 + 2 → Foundation ready
2. Phase 3 → US1/US2 complete → rebuild DB, verify stc (MVP!)
3. Phase 4 → US3 complete → search noise eliminated
4. Phase 5 → Full regression + lint/type checks pass

---

## Notes

- `_SCORE_THRESHOLD = 0.2` is an empirical starting value (T013). Adjust based on SC-003/SC-004 validation.
- The dedup key attribute name (`entity.location.file` or similar) must be confirmed from `DoxygenEntity` type in `packages/legacy_common/` before implementing T004.
- Each DB rebuild (T007) is a full drop-and-repopulate. No partial patching.
- After Phase 3, the entity count in the database will be lower than the pre-fix count — this is expected and correct (SC-001).
