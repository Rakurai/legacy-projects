# Tasks: MCP Build Pipeline — Data Completeness Fixes

**Input**: Design documents from `/specs/007-data-completeness/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, quickstart.md

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup

**Purpose**: No new project structure needed — all changes are within the existing `mcp/doc_server/` package. This phase ensures the environment is ready.

- [x] T001 Verify `PROJECT_ROOT` in `mcp/doc_server/.env` points to the legacy C++ source tree root (not the Python repo root)
- [x] T002 Run `uv sync` at repo root to ensure all dependencies are current

---

## Phase 2: Foundational

**Purpose**: No blocking prerequisites — this feature modifies existing build pipeline functions. No schema changes, no new dependencies.

*(No tasks — user stories can begin immediately after setup)*

---

## Phase 3: User Story 1 — Source Code Available in Entity Lookups (Priority: P1) 🎯 MVP

**Goal**: Make `extract_source_code()` populate `source_text` and `definition_text` for all entities with body/decl locations, and fail-fast when `PROJECT_ROOT` is misconfigured.

**Independent Test**: Run the build with a valid `PROJECT_ROOT` → verify `SELECT COUNT(*) FROM entities WHERE source_text IS NOT NULL` is non-zero and proportional to body-located entities. Run with an invalid path → verify build exits with error.

### Implementation for User Story 1

- [x] T003 [US1] Add `BuildError` exception class and fail-fast validation to `extract_source_code()` — raise `BuildError` when `body_located > 0 and extracted == 0` with `PROJECT_ROOT` path in message, in `mcp/doc_server/build_helpers/entity_processor.py`
- [x] T004 [US1] Replace silent `.exists()` skips with `log.warning()` for missing source files in `mcp/doc_server/build_helpers/entity_processor.py`
- [x] T005 [US1] Add structured extraction summary log (body_located, extracted, failed, skipped, success rate) at end of `extract_source_code()` in `mcp/doc_server/build_helpers/entity_processor.py`

### Tests for User Story 1

- [x] T006 [US1] Create `test_extract_source_code_happy_path` using `tmp_path` fixture with mock source tree in `mcp/doc_server/tests/test_entity_processor.py`
- [x] T007 [US1] Create `test_extract_source_code_zero_extraction_raises` asserting `BuildError` (from `entity_processor`) on empty source tree in `mcp/doc_server/tests/test_entity_processor.py`
- [x] T008 [US1] Create `test_extract_source_code_partial_extraction_warns` verifying warnings for missing files but no error in `mcp/doc_server/tests/test_entity_processor.py`

**Checkpoint**: Source extraction works with valid `PROJECT_ROOT`, fails fast with invalid. Tests pass with `uv run pytest tests/test_entity_processor.py -v`.

---

## Phase 4: User Story 2 — Improved Embedding Coverage for Search (Priority: P2)

**Goal**: Generate minimal embeddings for doc-less entities (including structural compounds) so ≥95% of all entities have non-null embeddings and are discoverable via semantic search.

**Independent Test**: After build, `SELECT COUNT(*) FROM entities WHERE embedding IS NULL` returns near-zero. `search("player list global variable")` returns relevant results.

### Implementation for User Story 2

- [x] T009 [P] [US2] Implement `build_minimal_embed_text(merged: MergedEntity) -> str | None` with Doxygen tag mapping in `mcp/doc_server/build_helpers/embeddings_loader.py`
- [x] T010 [US2] Extend `generate_embeddings()` to build doc-less entity text list via `build_minimal_embed_text()`, concatenate with doc-rich list, embed in single batch in `mcp/doc_server/build_helpers/embeddings_loader.py`
- [x] T011 [US2] Add embedding generation summary log (doc_embeds, minimal_embeds, no_embed, coverage%) to `generate_embeddings()` in `mcp/doc_server/build_helpers/embeddings_loader.py`

### Tests for User Story 2

- [x] T012 [P] [US2] Create `test_build_minimal_embed_text_function` verifying `@fn` tag + signature output in `mcp/doc_server/tests/test_embeddings.py`
- [x] T013 [P] [US2] Create `test_build_minimal_embed_text_file` verifying `@file` tag + path output for file compounds in `mcp/doc_server/tests/test_embeddings.py`
- [x] T014 [P] [US2] Create `test_build_minimal_embed_text_empty_skips` verifying `None` return when name/sig/kind are all empty in `mcp/doc_server/tests/test_embeddings.py`
- [x] T015 [US2] Create `test_generate_embeddings_includes_doc_less` with mock provider verifying doc-less entities are in the embed batch in `mcp/doc_server/tests/test_embeddings.py`

**Checkpoint**: Minimal embeddings generated for doc-less entities. Tests pass with `uv run pytest tests/test_embeddings.py -v`.

---

## Phase 5: User Story 3 — Accurate Params Filtering (Priority: P3)

**Goal**: Store `params` as `NULL` when empty (`{}` or `None`) so `WHERE params IS NOT NULL` returns only entities with meaningful parameter documentation.

**Independent Test**: After build, `SELECT COUNT(*) FROM entities WHERE params IS NOT NULL` returns ~1,800–2,100 (not ~5,055).

### Implementation for User Story 3

- [x] T016 [P] [US3] Normalize empty params to `NULL` at DB insertion — change `params=merged.doc.params if merged.doc else None` to `params=merged.doc.params if merged.doc and merged.doc.params else None` in `mcp/doc_server/build_mcp_db.py`

**Checkpoint**: Params normalization complete. Verifiable after full build via SQL query.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Full build verification and validation of all success criteria.

- [x] T017 Delete embedding cache `.pkl` file from artifacts dir to force regeneration with new minimal embedding path
- [x] T018 Run full build with valid `PROJECT_ROOT` — `cd mcp/doc_server && uv run python -m build_mcp_db`
- [x] T019 Run all tests — `cd mcp/doc_server && uv run pytest tests/ -v`
- [x] T020 Execute SC-001 verification query: ≥90% of body-located entities have non-null `source_text`
- [x] T021 Execute SC-002 verification query: ≥95% of all entities have non-null `embedding`
- [x] T022 Execute SC-003 verification query: `params IS NOT NULL` count is ~1,800–2,100
- [x] T023 Execute SC-004 verification: build with `PROJECT_ROOT=/nonexistent` fails with `BuildError`
- [x] T024 Run quickstart.md validation steps from `specs/007-data-completeness/quickstart.md`

---

## Audit Remediation

> Generated by `/speckit.audit` on 2026-03-18. Address before next `/speckit.implement` run.

- [x] T025 [AR] Fix line range exceeding file length — raise `BuildError` instead of silent drop in `entity_processor.py:262` (SD-001, spec edge case updated)
- [x] T026 [AR] Narrow `except Exception` to `(OSError, UnicodeDecodeError)` in `entity_processor.py:246,265` (CV-001)
- [x] T027 [AR] Fix import sorting (ruff I001) in `entity_processor.py`, `test_entity_processor.py`, `test_embeddings.py` (CV-002)
- [x] T028 [AR] Add `Path` type annotation to `tmp_path` params in `test_embeddings.py:122,158` (CV-003)
- [x] T029 [AR] Fix misleading `_KIND_TAG_MAP` comment in `embeddings_loader.py:20` — clarify it extends the canonical map (CQ-001)
- [x] T030 [AR] Update stale `generate_embeddings()` docstring in `embeddings_loader.py:130` (CQ-002)
- [x] T031 [AR] Remove dead `sig_override` parameter from `_make_merged` helper in `test_embeddings.py` (TQ-001)
- [x] T032 [AR] Add `PLR2004` per-file-ignore for `tests/**` in `mcp/doc_server/ruff.toml`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Empty — no blocking prerequisites
- **US1 (Phase 3)**: Can start after Setup
- **US2 (Phase 4)**: Can start after Setup — independent of US1
- **US3 (Phase 5)**: Can start after Setup — independent of US1 and US2
- **Polish (Phase 6)**: Depends on all user stories complete

### User Story Dependencies

- **User Story 1 (P1)**: Self-contained in `entity_processor.py` + new test file
- **User Story 2 (P2)**: Self-contained in `embeddings_loader.py` + new test file
- **User Story 3 (P3)**: Self-contained in `build_mcp_db.py` — one-line change

No cross-story dependencies. All three user stories modify different files and can be implemented in any order or in parallel.

### Within Each User Story

- Implementation before tests (tests import the new functions/behavior)
- T003 → T004 → T005 (sequential within `extract_source_code()`)
- T009 → T010 → T011 (sequential: builder function → integration → logging)
- T016 is standalone

### Parallel Opportunities

**Across stories** (different files, no conflicts):
- T003–T005 (entity_processor.py) ‖ T009–T011 (embeddings_loader.py) ‖ T016 (build_mcp_db.py)

**Within US2 tests** (different test functions, same new file):
- T012 ‖ T013 ‖ T014 (all [P] marked — independent `build_minimal_embed_text` test cases)

---

## Parallel Example: All Three Stories

```
# Start all three stories in parallel (different files):
T003-T005: extract_source_code() validation in entity_processor.py
T009-T011: minimal embeddings in embeddings_loader.py
T016:      params normalization in build_mcp_db.py

# Then tests (after respective implementations):
T006-T008: source extraction tests
T012-T015: embedding tests

# Finally:
T017-T023: full build verification
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (verify `.env`)
2. Complete Phase 3: User Story 1 (source extraction fix)
3. **STOP and VALIDATE**: Run build, check `source_text` is populated, verify fail-fast on bad path
4. This alone delivers the highest-value fix — source code accessible to AI assistants

### Incremental Delivery

1. US1: Source extraction fix → build + verify → **source_text populated**
2. US3: Params normalization → build + verify → **params cleaned** (one-line change, quick win)
3. US2: Embedding coverage → build + verify → **≥95% embedding coverage**
4. Polish: Full verification against all SC criteria

### Full Parallel Strategy

1. Implement T003–T005, T009–T011, T016 simultaneously (3 different files)
2. Write tests T006–T008, T012–T015 simultaneously (2 new test files)
3. Run T017–T023 (full build + verification)

---

## Notes

- All changes are within `mcp/doc_server/` — no changes to `legacy_common` or other packages
- No schema changes — all DB columns already exist
- No new dependencies needed
- Embedding cache files will need to be regenerated (delete existing `.pkl` cache before rebuild)
- Total: 24 tasks, 3 modified files, 2 new test files
