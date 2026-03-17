# Tasks: Deterministic Entity IDs & Documentation Merge Fix

**Feature**: `005-mcp-key-issue`
**Generated**: 2026-03-17
**Source**: [plan.md](plan.md) + [spec.md](spec.md)

---

## Phase 1 — Setup

> Project initialization and shared infrastructure. Must complete before any user story work.

- [X] T001 Create deterministic ID generator in `mcp/doc_server/build_helpers/entity_ids.py`
  - Replace existing Doxygen-format helpers (`split_entity_id`, `SignatureMap`) with new deterministic ID functions (FR-006)
  - Implement `compute_entity_id(kind, compound_id, second_element) -> str` producing `{prefix}:{sha256(canonical_key)[:7]}`
  - Prefix mapping: function/define → `fn`, variable → `var`, class/struct → `cls`, file → `file`, everything else → `sym`
  - Implement `build_id_map(signature_map, code_graph) -> dict[str, str]` computing all IDs and halting on collision (FR-001, FR-002, FR-004)

- [X] T002 Add unit tests for entity ID generation in `mcp/doc_server/tests/test_entity_ids.py`
  - Test prefix mapping for each entity kind
  - Test determinism: same input → same output across calls
  - Test collision detection: synthetic collision raises error
  - Test format: output matches `{prefix}:{7 hex}` regex

---

## Phase 2 — Foundational (blocking prerequisites)

> Schema and model changes that all user stories depend on. Must complete before Phases 3–5.

- [X] T003 Remove `DocQuality` and `DocState` enums from `mcp/doc_server/server/enums.py` (FR-007)

- [X] T004 Update DB model in `mcp/doc_server/server/db_models.py`
  - Drop columns: `compound_id`, `member_id`, `doc_state`, `doc_quality` from Entity table (FR-007)
  - Drop column: `doc_quality_dist` from Capability table (FR-008)
  - Ensure `entity_id` PK stores `{prefix}:{7 hex}` format (FR-009)
  - Ensure `signature` column has no UNIQUE constraint (FR-010)

- [X] T005 [P] Update API response models in `mcp/doc_server/server/models.py`
  - Remove `doc_state`, `doc_quality` from `EntitySummary` (FR-018)
  - Remove `compound_id`, `member_id`, `doc_state`, `doc_quality` from `EntityDetail` (FR-019)
  - Remove `doc_quality_dist` from capability response models (FR-015)
  - Remove `ResolutionEnvelope` wrapper class entirely (FR-013)

- [X] T006 [P] Update converters in `mcp/doc_server/server/converters.py`
  - Remove mapping logic for dropped fields (`doc_quality`, `doc_state`, `compound_id`, `member_id`)
  - Remove `ResolutionEnvelope` construction from all converter paths

- [X] T007 [P] Remove `resolve_entity_id` helper from `mcp/doc_server/server/util.py` (FR-011)

---

## Phase 3 — User Story 1: Reliable Entity References Across Tool Calls (P1)

> **Goal**: Every entity has a short, deterministic, type-prefixed ID (`{prefix}:{7 hex}`) that is stable across rebuilds and unambiguous. Agents search → receive IDs → use IDs in all follow-up calls with zero collision or mismatch.
>
> **Independent Test**: Rebuild the database from the same source artifacts twice and confirm every entity receives the same ID in both builds. Then issue a `search` call, take the returned `entity_id`, and pass it to `get_entity`, `get_callers`, `get_behavior_slice` — all must return correct results.

- [X] T008 [US1] Integrate deterministic IDs into entity processing in `mcp/doc_server/build_helpers/entity_processor.py`
  - After merge, compute deterministic ID for each entity using `entity_ids.compute_entity_id(kind, compound_id, signature)`
  - Halt build on any collision (FR-004)
  - `signature_map.json`, `code_graph.json`, and `doc_db.json` are pre-built input artifacts — the build pipeline loads them, it does not regenerate them
  - Note: T017 also modifies this file for doc-field carry-through — T008 owns ID assignment, T017 owns doc-merge verification

- [X] T009 [US1] Update graph loader for ID translation in `mcp/doc_server/build_helpers/graph_loader.py`
  - Build ID translation map (old Doxygen ID → new deterministic ID) from the merge step
  - Translate edge source/target from Doxygen IDs to deterministic IDs
  - Silently skip edges where either endpoint has no entity mapping (~506 IDs in `code_graph.json` are enumvalue or friend references, not entities — see `artifacts/artifacts.md` §5)

- [X] T010 [US1] Update embeddings loader for new IDs in `mcp/doc_server/build_helpers/embeddings_loader.py`
  - Re-key embedding entries by new deterministic IDs instead of old Doxygen IDs

- [X] T011 [US1] Update build orchestrator in `mcp/doc_server/build_mcp_db.py`
  - Pipeline order: load artifacts (code_graph.json, doc_db.json, signature_map.json) → merge entities + docs → compute deterministic IDs → extract source → capabilities → graph (with ID translation) → embeddings (with ID translation)
  - Wire new functions into the build sequence
  - Remove any doc_quality/doc_state population logic

- [X] T013 [US1] Update test fixtures for new ID format in `mcp/doc_server/tests/conftest.py`
  - Change all fixture entity IDs from Doxygen format to `{prefix}:{7 hex}` format
  - Remove any fixture fields for `compound_id`, `member_id`, `doc_state`, `doc_quality`

- [X] T014 [US1] Update entity tool tests in `mcp/doc_server/tests/test_entity_tools.py`
  - Remove `resolve_entity` test cases
  - Remove tests that pass `signature` parameter
  - Update remaining tests to use new ID format

- [X] T015 [US1] Update graph tool tests in `mcp/doc_server/tests/test_graph_tools.py`
  - Update fixtures to use `{prefix}:{7 hex}` IDs
  - Remove tests that pass `signature` parameter

- [X] T016 [P] [US1] Update behavior tool tests in `mcp/doc_server/tests/test_behavior_tools.py`
  - Update fixtures to use `{prefix}:{7 hex}` IDs
  - Remove tests that pass `signature` parameter

---

## Phase 4 — User Story 2: Complete Documentation After Build (P2)

> **Goal**: At least 95% of ~5,293 documented entities retain their documentation after build (up from ~6% today). The build regenerates `signature_map.json` from current artifacts before merging.
>
> **Independent Test**: After a build, query a sample of 50 entities that have non-null briefs in `doc_db.json` and confirm each entity's `brief` field in the database matches the artifact. Count total entities with non-null `brief` and compare against artifact count.

- [X] T017 [US2] Ensure documentation field carry-through in `mcp/doc_server/build_helpers/entity_processor.py`
  - The merge logic (`merge_entities()`) is already correct — it iterates code_graph entities and looks up docs via signature_map. With a fresh `signature_map.json` (pre-built), ~85% of doc_db entries match.
  - Verify all doc fields are carried through: brief, details, params, returns, notes, rationale, usages (FR-005)
  - Remove `compute_doc_quality()` and any `doc_state` assignment logic
  - Note: T008 also modifies this file for ID assignment — T017 owns doc-merge verification, T008 owns ID assignment

- [X] T018 [US2] Update converter tests in `mcp/doc_server/tests/test_converters.py`
  - Remove assertions for `doc_quality` and `doc_state` fields
  - Verify documentation fields are carried through conversion

- [X] T019 [P] [US2] Update search tests in `mcp/doc_server/tests/test_search.py`
  - Remove `doc_quality` filter tests
  - Update any fixtures referencing removed fields

- [X] T020 [P] [US2] Update resolution tests in `mcp/doc_server/tests/test_resolution.py` and `mcp/doc_server/tests/test_resolver_stages.py`
  - Remove or gut `resolve_entity` pipeline tests in `test_resolution.py`
  - Update `test_resolver_stages.py` for search-internal resolution changes
  - Retain only tests relevant to search's internal resolution pipeline

---

## Phase 5 — User Story 3: Simplified Tool Interface (P3)

> **Goal**: Retire `resolve_entity` tool. All tools accept only `entity_id` (not `signature`). Remove `ResolutionEnvelope` from all responses. Streamlined two-step agent pattern: search → use entity_id.
>
> **Independent Test**: Confirm `resolve_entity` is absent from tool catalog. Confirm `get_entity` with valid `entity_id` works, and with `signature` string is rejected. Confirm no response contains `resolution` field.

- [X] T021 [US3] Remove `resolve_entity` tool from `mcp/doc_server/server/tools/entity.py` (FR-011)
  - Delete the resolve_entity function registration
  - Remove signature parameter from `get_entity` (FR-012)
  - Note: `get_source_code` already accepts only `entity_id` — no change needed

- [X] T022 [P] [US3] Remove signature parameter from graph tools in `mcp/doc_server/server/tools/graph.py` (FR-012)
  - Update `get_callers`, `get_callees`, `get_dependencies`, `get_class_hierarchy`, `get_related_entities` to accept only `entity_id`

- [X] T023 [P] [US3] Remove signature parameter from behavior tools in `mcp/doc_server/server/tools/behavior.py` (FR-012, FR-016)
  - Update `get_behavior_slice`, `get_state_touches` to accept only `entity_id`
  - Remove `DocQuality` import (broken after T003 removes the enum)

- [X] T024 [P] [US3] Remove `min_doc_quality` parameter from search tool in `mcp/doc_server/server/tools/search.py` (FR-014)

- [X] T025 [P] [US3] Remove `doc_quality_dist` from capability tools in `mcp/doc_server/server/tools/capability.py` (FR-012, FR-015)
  - Update `list_capabilities` and `get_capability_detail` responses to remove `doc_quality_dist`
  - Remove signature parameter from `get_entry_point_info` (lives in capability.py, not behavior.py)

- [X] T026 [US3] Update search implementation in `mcp/doc_server/server/search.py`
  - Remove `min_doc_quality` filtering logic
  - Preserve multi-stage resolution pipeline (name_exact → prefix → keyword → semantic) as internal search implementation (FR-020)

- [X] T027 [US3] Update resolver in `mcp/doc_server/server/resolver.py`
  - Retain resolution pipeline for search's internal use
  - Remove any signature-based entity lookup paths

- [X] T028 [US3] Update resources in `mcp/doc_server/server/resources.py`
  - Remove `doc_quality_dist` from resource responses

- [X] T029 [US3] Update prompts in `mcp/doc_server/server/prompts.py` (FR-017)
  - Update workflow descriptions in `explain_entity_prompt` and `compare_entry_points_prompt` that reference entity resolution
  - Replace "entity resolution" workflow guidance with search → entity_id pattern

- [X] T030 [US3] Update search tool test in `mcp/doc_server/tests/test_search_tool.py`
  - Remove `min_doc_quality` parameter test
  - Update test expectations

- [X] T031 [P] [US3] Update capability tool tests in `mcp/doc_server/tests/test_capability_tools.py`
  - Remove `doc_quality_dist` assertions from responses

- [X] T032 [P] [US3] Update resource tests in `mcp/doc_server/tests/test_resources.py`
  - Remove `doc_quality_dist` from expected resource output

---

## Phase 6 — Polish & Cross-Cutting Concerns

> Final validation, cleanup, and overall consistency checks.

- [X] T033 Update util tests in `mcp/doc_server/tests/test_util.py`
  - Remove `resolve_entity_id` helper tests

- [X] T033a Review `mcp/doc_server/tests/test_load_graph.py` and `mcp/doc_server/tests/test_graph.py`
  - Update any references to Doxygen-format entity IDs if present
  - No changes needed if these tests only use graph structure (not entity ID format)

- [X] T034 Update server test in `mcp/doc_server/tests/test_server.py`
  - Update expected tool count (resolve_entity removed; verify actual count dynamically or adjust constant)

- [X] T035 Run full test suite and fix any regressions
  - Execute `cd mcp/doc_server && uv run pytest tests/ -v --color=never`
  - All tests must pass

- [X] T036 Run linting and type checking
  - Execute `cd mcp/doc_server && uv run ruff check .`
  - Execute `cd mcp/doc_server && uv run mypy server/`
  - Fix any violations

- [X] T037 Validate build pipeline end-to-end
  - Run `cd mcp/doc_server && uv run python -m build_mcp_db`
  - Verify ≥95% of ~5,293 doc_db entries have non-null brief in DB (SC-001)
  - Verify deterministic IDs (SC-002)
  - Verify zero collisions

---

## Dependencies

```text
Phase 1 (Setup) ──────────────► Phase 2 (Foundational)
                                       │
                    ┌──────────────────┤──────────────────┐
                    ▼                  ▼                  ▼
             Phase 3 (US1) ───► Phase 4 (US2)      Phase 5 (US3)
                    │                  │                  │
                    └──────────────────┤──────────────────┘
                                       ▼
                                Phase 6 (Polish)
```

**Key constraints**:
- Phase 1 → Phase 2: ID generation must exist before schema changes reference the format
- Phase 2 → Phases 3/4/5: Schema/model changes are prerequisites for all user stories
- Phases 3, 4, 5: Largely independent after Phase 2; can be worked in parallel with caution on shared test fixtures (T013)
- Phase 3 (US1) should complete before Phase 4 (US2): deterministic ID computation (T008) is needed before doc merge verification
- All phases → Phase 6: Polish runs last

## Parallel Execution Opportunities

**Within Phase 2** (after T003, T004):
- T005 + T006 + T007 can run in parallel (different files, no interdependency)

**Within Phase 3** (US1):
- T009 + T010 can run in parallel (graph_loader.py vs embeddings_loader.py), both after T008
- T013 + T014 + T015 can run in parallel (separate test files)

**Within Phase 5** (US3):
- T021 → then T022 + T023 + T024 + T025 can run in parallel (separate tool files)
- T030 + T031 + T032 can run in parallel (separate test files)

**Cross-phase parallelism** (after Phase 2):
- Phase 4 tasks (T017–T020) can run alongside Phase 5 tasks (T021–T032)
  provided Phase 3's T008 (deterministic ID integration) is complete

## Implementation Strategy

**MVP scope**: Phase 1 + Phase 2 + Phase 3 (User Story 1)
- Delivers deterministic entity IDs — the single prerequisite for trustworthy agent interactions
- All tools accept and return the new ID format
- Agent can search → get IDs → use IDs reliably

**Increment 2**: Phase 4 (User Story 2)
- Delivers complete documentation recovery (95%+ coverage)
- Completes the server's primary value proposition

**Increment 3**: Phase 5 (User Story 3)
- Simplifies tool interface (removes resolve_entity, signature params, ResolutionEnvelope)
- Reduces agent confusion and context consumption

**Final**: Phase 6 (Polish)
- Cross-cutting validation, cleanup, CI green
