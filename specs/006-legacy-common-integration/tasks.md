# Tasks: Legacy Common Integration

**Input**: Design documents from `/specs/006-legacy-common-integration/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, quickstart.md

**Tests**: Not explicitly requested. Existing tests must pass; `test_embed_text.py` must be deleted (tests removed function).

**Organization**: Tasks grouped by user story. Single atomic integration — intermediate states may break the pipeline; only the final state must work.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup

**Purpose**: Dependency wiring and environment preparation

- [x] T001 Add `legacy-common` as workspace dependency in `mcp/doc_server/pyproject.toml`
- [x] T002 Run `uv sync` in `mcp/doc_server/` and verify `legacy_common` imports succeed

**Checkpoint**: `from legacy_common.doxygen_parse import DoxygenEntity` works in the doc_server environment

---

## Phase 2: Foundational (legacy_common Modifications)

**Purpose**: Unblock all downstream stories by making necessary changes to the shared library

**Warning**: No user story work can begin until this phase is complete

- [x] T003 [P] Add `docs_dir: Path | None = None` parameter to `DocumentDB` in `packages/legacy_common/legacy_common/doc_db.py` — modify `load()` to use `self.docs_dir or GENERATED_DOCS_DIR`; preserve backward compatibility for existing singleton and callers
- [x] T004 [P] Remove unused `from jinja2 import is_undefined` import from `packages/legacy_common/legacy_common/doxygen_graph.py`

**Checkpoint**: `legacy_common` modifications complete; existing legacy_common consumers unaffected

---

## Phase 3: User Story 1 — Entity Model Consolidation (Priority: P1) MVP

**Goal**: Replace reimplemented entity dataclasses in `build_helpers/artifact_models.py` with canonical imports from `legacy_common.doxygen_parse`

**Independent Test**: Run `uv run python -m build_script.build_mcp_db` — all ~5,300 entities load and process with identical entity IDs

### Implementation for User Story 1

- [x] T005 [US1] Update `mcp/doc_server/build_helpers/loaders.py` — replace `from build_helpers.artifact_models import EntityDatabase, load_entity_db` with `from legacy_common.doxygen_parse import EntityDatabase, DoxygenEntity`; update `load_entities()` to use `EntityDatabase.from_json()` and return the `.entities` flat dict view; keep `validate_artifacts()` unchanged for now
- [x] T006 [US1] Update `mcp/doc_server/build_helpers/entity_processor.py` — replace entity model imports (`EntityID`, `DoxygenEntity`, `DoxygenLocation`) from `build_helpers.artifact_models` with imports from `legacy_common.doxygen_parse`; leave `Document` import from `artifact_models` in place (replaced in T009/US2); adapt to `EntityID` objects as dict keys (use `str(entity_id)` where string keys are needed); update `assign_deterministic_ids()`, `extract_source_code()`, and other functions that handle entity fields
- [x] T007 [US1] Update `mcp/doc_server/build_script/build_mcp_db.py` — replace entity model imports with `legacy_common` equivalents; adapt entity loading call to use updated `loaders.load_entities()` return type

**Checkpoint**: Entity loading works with legacy_common models; entity IDs are deterministic and match previous output

---

## Phase 4: User Story 2 — Document Model and Data Source Switch (Priority: P2)

**Goal**: Switch from flat `doc_db.json` to per-compound `generated_docs/` via `legacy_common.doc_db.DocumentDB`, replace `build_embed_text()` with `Document.to_doxygen()`

**Independent Test**: Rebuild database and verify brief coverage ≥90% (up from ~43%); verify embedding text format matches Doxygen tag structure

### Implementation for User Story 2

- [x] T008 [US2] Update `mcp/doc_server/build_helpers/loaders.py` — replace `from build_helpers.artifact_models import DocumentDB, Document` with `from legacy_common.doc_db import DocumentDB, Document`; update `load_documents()` to construct `DocumentDB(docs_dir=config.artifacts_path / "generated_docs")` with explicit path; remove `doc_db.json` from `validate_artifacts()` required files list; add `generated_docs/` directory validation
- [x] T009 [US2] Update `mcp/doc_server/build_helpers/entity_processor.py` — replace `Document` import from `build_helpers.artifact_models` with `from legacy_common.doc_db import Document`; adapt `merge_entities()` to work with legacy_common `DocumentDB` two-level key structure (`compound_id → signature → Document`) instead of repr-tuple keys
- [x] T010 [US2] Update `mcp/doc_server/build_helpers/embeddings_loader.py` — replace `from build_helpers.embed_text import build_embed_text` with usage of `Document.to_doxygen()` method; update `generate_embeddings()` to call `doc.to_doxygen()` on `Document` instances instead of passing raw dicts to `build_embed_text()`
- [x] T011 [US2] Update `mcp/doc_server/build_script/build_mcp_db.py` — replace document model imports; adapt document loading and merging calls to use updated loaders; remove any direct references to `doc_db.json`
- [x] T012 [P] [US2] Delete `mcp/doc_server/build_helpers/embed_text.py`
- [x] T013 [P] [US2] Delete `mcp/doc_server/tests/test_embed_text.py`

**Checkpoint**: Documents load from `generated_docs/`; brief coverage ≥90%; embedding text uses `Document.to_doxygen()`

---

## Phase 5: User Story 3 — Graph Loader Deduplication (Priority: P3)

**Goal**: Replace local `load_gml_graph()` with `legacy_common.doxygen_graph.load_graph`

**Independent Test**: Load `code_graph.gml` — verify same node count, edge count, and attributes

### Implementation for User Story 3

- [x] T014 [US3] Update `mcp/doc_server/build_helpers/graph_loader.py` — replace `from build_helpers.artifact_models import load_gml_graph` with `from legacy_common.doxygen_graph import load_graph`; update `load_graph_edges()` to call `load_graph(gml_path)` instead of `load_gml_graph(gml_path)`

**Checkpoint**: Graph loading works with legacy_common loader; metrics computation unchanged

---

## Phase 6: User Story 4 — SignatureMap Computed On-the-Fly (Priority: P4)

**Goal**: Compute signature map from `EntityDatabase` and `DocumentDB` at build time instead of loading `signature_map.json`

**Independent Test**: Computed map produces identical entity IDs as current pipeline for all ~5,300 entities

### Implementation for User Story 4

- [x] T015 [US4] Create `SignatureMap` class in `mcp/doc_server/build_helpers/entity_processor.py` — accepts `EntityDatabase` and `DocumentDB`; iterates `DocumentDB.docs` entries and correlates with `EntityDatabase` to build `repr((compound_id, second_element))` → old Doxygen entity ID mapping; provides dict-like lookup matching current `signature_map[key]` usage pattern
- [x] T016 [US4] Update `mcp/doc_server/build_helpers/loaders.py` — remove `load_signature_map()` function; remove `signature_map.json` from `validate_artifacts()` required files list
- [x] T017 [US4] Update `mcp/doc_server/build_script/build_mcp_db.py` — replace `load_signature_map()` call with `SignatureMap` construction from loaded `EntityDatabase` and `DocumentDB`; verify all downstream consumers (`merge_entities`, `assign_deterministic_ids`) work with computed map

**Checkpoint**: Pipeline runs without `signature_map.json`; all entity IDs match previous output

---

## Phase 7: User Story 5 — ResolutionResult Pydantic Conversion (Priority: P5)

**Goal**: Convert `ResolutionResult` from `@dataclass` to Pydantic `BaseModel`

**Independent Test**: All resolution-related tests pass (`test_resolution.py`, `test_resolver_stages.py`)

### Implementation for User Story 5

- [x] T018 [US5] Convert `ResolutionResult` in `mcp/doc_server/server/resolver.py` — change from `@dataclass` to Pydantic `BaseModel`; keep all fields (`status`, `match_type`, `candidates`, `resolved_from`) and `to_entity_summaries()` method; remove `dataclasses` import if no longer needed

**Checkpoint**: Resolution pipeline works identically; existing tests pass

---

## Phase 8: Polish & Cleanup

**Purpose**: Delete obsolete files, update packaging, final validation

- [x] T019 Delete `mcp/doc_server/build_helpers/artifact_models.py`
- [x] T020 Check `mcp/doc_server/build_helpers/__init__.py` — if empty (no re-exports or relative imports used by remaining modules), delete it; if it contains imports needed by `entity_ids.py`, `entity_processor.py`, `embeddings_loader.py`, `graph_loader.py`, or `loaders.py`, keep it
- [x] T021 Update `mcp/doc_server/pyproject.toml` — remove `build_helpers` from `[tool.hatch.build.targets.wheel] packages` list (keep `server` only)
- [x] T022 Run full validation: `cd mcp/doc_server && uv run ruff check . && uv run ruff format . && uv run mypy server/ && uv run pytest tests/ -v` — also verify no `from legacy_common import ARTIFACTS_DIR` exists in doc_server code (FR-013)
- [x] T023 Run end-to-end pipeline build: `cd mcp/doc_server && uv run python -m build_script.build_mcp_db` — verify ~5,300 entities, ≥90% brief coverage, identical entity IDs, all capabilities and graph metrics populated

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Setup; BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Foundational
- **US2 (Phase 4)**: Depends on US1 (entity models must be swapped first)
- **US3 (Phase 5)**: Depends on Foundational only (independent of US1/US2)
- **US4 (Phase 6)**: Depends on US1 + US2 (needs both EntityDatabase and DocumentDB from legacy_common)
- **US5 (Phase 7)**: Depends on Foundational only (independent of all other stories)
- **Polish (Phase 8)**: Depends on US1 + US2 + US3 + US4 (artifact_models.py can only be deleted after all consumers are rewired)

### User Story Dependency Graph

```text
Setup → Foundational ─┬─→ US1 ──→ US2 ──→ US4 ──┐
                       ├─→ US3 ───────────────────┤→ Polish
                       └─→ US5 ───────────────────┘
```

### Within Each User Story

- Update loaders/imports first
- Update processors/consumers second
- Update orchestrator (build_mcp_db.py) last
- Delete files only after all consumers are rewired

### Parallel Opportunities

- T003 and T004 (Foundational) can run in parallel
- US3 and US5 can run in parallel with US1→US2→US4 chain
- T012 and T013 (file deletions in US2) can run in parallel with each other

---

## Parallel Example: Foundational Phase

```text
# These modify different files in legacy_common — run in parallel:
Task T003: "Add docs_dir param to DocumentDB in legacy_common/doc_db.py"
Task T004: "Remove jinja2 import from legacy_common/doxygen_graph.py"
```

## Parallel Example: After Foundational

```text
# US3 and US5 are independent of US1/US2 — can run in parallel:
Track A: US1 → US2 → US4 (sequential dependency chain)
Track B: US3 (independent)
Track C: US5 (independent)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001–T002)
2. Complete Phase 2: Foundational (T003–T004)
3. Complete Phase 3: US1 — Entity Model Consolidation (T005–T007)
4. **STOP and VALIDATE**: Entity loading works with legacy_common models

### Incremental Delivery

1. Setup + Foundational → Environment ready
2. US1 → Entity models consolidated (MVP foundation)
3. US2 → Document source upgraded, ~2x brief coverage improvement
4. US3 → Graph loader deduplicated
5. US4 → Signature map computed on-the-fly, 2 artifacts removed
6. US5 → ResolutionResult consistency cleanup
7. Polish → Delete obsolete files, full validation

### Single-Developer Strategy (Recommended)

This is an atomic integration best done sequentially:

1. Setup + Foundational (T001–T004)
2. US1 → US2 → US4 (main dependency chain: T005–T017)
3. US3 (T014) — slot in anywhere after Foundational
4. US5 (T018) — slot in anywhere after Foundational
5. Polish (T019–T023)

---

## Audit Remediation

> Generated by `/speckit.audit` on 2026-03-18. Address before next `/speckit.implement` run.

- [x] T024 [AR] Fix `ruff.toml` config conflict — `ruff.toml` has no `line-length` (defaults to 88) and sets `magic-trailing-comma = "ignore"`, while `pyproject.toml` specifies `line-length = 120`. `ruff.toml` takes precedence, causing all the formatting churn. Add `line-length = 120` to `mcp/doc_server/ruff.toml` top-level; change `[format] magic-trailing-comma` to `"respect"`; reconcile `[lint.isort]` `force-wrap-length` and `known-first-party` with `pyproject.toml` values.
- [x] T025 [AR] Revert pure-formatting changes in all files where the only diff is ruff reformatting (no behavioral changes). Use `git diff HEAD` to identify files with formatting-only changes and `git checkout HEAD -- <file>` to restore them. Then re-run `uv run ruff check --fix .` and `uv run ruff format .` with the corrected config from T024, so only intentional changes remain in the diff.

---

## Notes

- Single atomic integration: intermediate states may break the pipeline
- `entity_ids.py` is KEPT — `compute_entity_id()` has no legacy_common equivalent
- `build_helpers/` directory is KEPT (still has entity_ids, entity_processor, embeddings_loader, graph_loader, loaders)
- `test_embed_text.py` is the only test file deleted; all other tests must pass without modification
- Verify `EntityID.split()` equivalence with old `EntityID.from_str()` for all ~5,300 entities during US1
