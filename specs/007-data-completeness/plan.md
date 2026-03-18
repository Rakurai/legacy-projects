# Implementation Plan: MCP Build Pipeline — Data Completeness Fixes

**Branch**: `007-data-completeness` | **Date**: 2026-03-18 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/007-data-completeness/spec.md`

## Summary

Fix three data completeness gaps in the MCP doc_server build pipeline: (1) make `extract_source_code()` fail-fast on invalid `PROJECT_ROOT` instead of silently yielding zero results, with extraction summary logging; (2) normalize empty `params` dicts to `NULL` in the database; (3) generate minimal embeddings for doc-less entities from `kind + name + signature + file_path` so all entities are semantically searchable.

## Technical Context

**Language/Version**: Python 3.14+ (uv workspace)
**Primary Dependencies**: legacy_common (doc_db, entity_db), SQLModel, AsyncPG, pgvector, FastEmbed, loguru
**Storage**: PostgreSQL 18 + pgvector (Docker or local)
**Testing**: pytest + pytest-randomly (contract tests, no live DB)
**Target Platform**: macOS/Linux (developer workstation, build script)
**Project Type**: Offline build script (populates DB consumed by MCP server)
**Performance Goals**: Build completes in <5 min for ~5,300 entities; embedding generation ~1–3 min
**Constraints**: Build is offline (no network required for local embeddings); must not regress existing entity population
**Scale/Scope**: ~5,305 entities, ~25K edges, ~4,900 docs, 30 capability groups

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| **Fail-Fast, No Fallbacks** | PASS | This spec *adds* fail-fast behavior (FR-001: build fails on zero source extraction). Current silent-skip is the violation; this spec fixes it. |
| **Types Are Contracts** | PASS | No new public interfaces. `MergedEntity` fields already typed. Params normalization is `dict → None`, preserving existing types. |
| **Source Reflects Current Truth** | PASS | No compatibility shims. Changes are in-place modifications to existing functions. |
| **uv-Only Toolchain** | PASS | All execution via `uv run`. No direct `python` calls. |
| **Notebook Discipline** | N/A | No notebook changes. |

No violations. No Complexity Tracking entries needed.

## Project Structure

### Documentation (this feature)

```text
specs/007-data-completeness/
├── plan.md              # This file
├── research.md          # Phase 0: resolved questions
├── data-model.md        # Phase 1: entity field changes
├── quickstart.md        # Phase 1: build & verify guide
├── contracts/           # Phase 1: no external contracts (build-only changes)
└── tasks.md             # Phase 2: task breakdown
```

### Source Code (files to modify)

```text
mcp/doc_server/
├── build_helpers/
│   ├── entity_processor.py     # extract_source_code() — add validation + logging
│   └── embeddings_loader.py    # generate_embeddings() — add minimal embedding coverage
├── build_mcp_db.py             # populate_entities() — params normalization
└── tests/
    ├── test_entity_processor.py  # New: source extraction validation tests
    └── test_embeddings.py        # New: minimal embedding text tests
```

**Structure Decision**: All changes are within the existing `mcp/doc_server/` package. No new packages, modules, or structural changes. Two new test files for the new behavior.

## Phase 2: Implementation Tasks

### Task 1 — Source extraction: fail-fast validation (US-1, FR-001, FR-002, FR-008, FR-010)

**File**: `mcp/doc_server/build_helpers/entity_processor.py`

**Changes to `extract_source_code()`**:
1. Count `body_located` entities (those with `entity.body` and `entity.body.fn` and `entity.body.line` and `entity.body.end_line`)
2. Change `.exists()` silent skips to `log.warning()` calls for missing files
3. Track `extracted_count`, `failed_count`, `skipped_count` (missing file)
4. After the loop, log a structured summary: `body_located`, `extracted`, `failed`, `skipped`, success rate
5. If `body_located > 0 and extracted_count == 0`: raise `BuildError` (defined in `entity_processor.py`) including the `project_root` path (FR-001, FR-002)
6. Same pattern for definition extraction (track separately or combined)

**Exception type**: `BuildError(Exception)` — new exception class in `entity_processor.py`. Inherits from `Exception` (not `RuntimeError`) for clear intent.

**Acceptance**: SC-004 — build with invalid `PROJECT_ROOT` raises `BuildError`.

---

### Task 2 — Source extraction: tests (US-1)

**File**: `mcp/doc_server/tests/test_entity_processor.py` (new)

**Tests**:
1. `test_extract_source_code_happy_path` — create a tmp source tree, build mock `MergedEntity` list with body locations pointing into it, call `extract_source_code()`, assert `source_text` and `definition_text` are populated
2. `test_extract_source_code_zero_extraction_raises` — mock entities with body locations, point at empty tmp dir, assert raises `BuildError`
3. `test_extract_source_code_partial_extraction_warns` — some files exist, some don't; assert extraction succeeds for present files and logs warnings for missing

**Dependencies**: Task 1

---

### Task 3 — Params normalization (US-3, FR-005)

**File**: `mcp/doc_server/build_mcp_db.py`

**Change**: In `populate_entities()`, line ~134:
```python
# Before:
params=merged.doc.params if merged.doc else None,
# After:
params=merged.doc.params if merged.doc and merged.doc.params else None,
```

One line change. `{}` is falsy in Python, so `merged.doc.params` evaluates to `False` when it's an empty dict.

**Acceptance**: SC-003 — `params IS NOT NULL` count matches meaningful param content (~1,800–2,100).

---

### Task 4 — Minimal embedding text builder (US-2, FR-006, FR-007)

**File**: `mcp/doc_server/build_helpers/embeddings_loader.py`

**New function**: `build_minimal_embed_text(merged: MergedEntity) -> str | None`

Implementation:
1. Determine tag from `merged.entity.kind` using the Doxygen tag mapping (same as `Document.to_doxygen()`)
2. Get display name: `merged.signature` or `merged.entity.name` or `""`
3. Get file path: `merged.entity.body.fn` or `merged.entity.decl.fn` or `None`
4. If all of `name`, `signature`, `kind` are empty/null → return `None`
5. Build Doxygen-like text block and return

---

### Task 5 — Extend `generate_embeddings()` for doc-less entities (US-2, FR-006, FR-009)

**File**: `mcp/doc_server/build_helpers/embeddings_loader.py`

**Changes to `generate_embeddings()`**:
1. After building `docs_to_embed` list (doc-rich), build a second list for doc-less entities:
   ```python
   minimal_to_embed = [
       (m.entity_id, build_minimal_embed_text(m))
       for m in merged_entities
       if m.doc is None
   ]
   minimal_to_embed = [(eid, text) for eid, text in minimal_to_embed if text is not None]
   ```
2. Concatenate both text lists, embed in a single batch
3. Log summary: `doc_embeds=N, minimal_embeds=N, no_embed=N, coverage=X%` (FR-009)

**Dependencies**: Task 4

---

### Task 6 — Embedding tests (US-2)

**File**: `mcp/doc_server/tests/test_embeddings.py` (new)

**Tests**:
1. `test_build_minimal_embed_text_function` — function entity → `@fn` tag + signature
2. `test_build_minimal_embed_text_file` — file compound → `@file` tag + path
3. `test_build_minimal_embed_text_empty_skips` — entity with no name/sig/kind → returns `None`
4. `test_generate_embeddings_includes_doc_less` — mock provider, verify doc-less entities appear in the embed call

**Dependencies**: Task 4, Task 5

---

### Task 7 — Verify `.env` configuration and full build (US-1, US-2, US-3, SC-001–SC-005)

**Manual / integration**:
1. Ensure `PROJECT_ROOT` in `mcp/doc_server/.env` points to the C++ source tree
2. Run full build: `cd mcp/doc_server && uv run python -m build_mcp_db`
3. Run verification queries from [quickstart.md](quickstart.md)
4. Confirm SC-001 through SC-005

**Dependencies**: Tasks 1–6

---

### Task Dependency Graph

```
Task 1 (source extraction validation)
  └── Task 2 (source extraction tests)

Task 3 (params normalization) — independent

Task 4 (minimal embed text builder)
  ├── Task 5 (extend generate_embeddings)
  │     └── Task 6 (embedding tests)
  └── Task 6 (embedding tests)

Tasks 1-6 ──► Task 7 (full build verification)
```

**Parallelism**: Tasks 1, 3, and 4 can be implemented in parallel. Tasks 2, 5, 6 follow their dependencies. Task 7 is the final integration gate.

## Post-Design Constitution Re-check

| Principle | Status | Notes |
|-----------|--------|-------|
| Fail-Fast, No Fallbacks | PASS | `BuildError` on zero extraction. Minimal embedding is an intended code path, not a fallback. |
| Types Are Contracts | PASS | `build_minimal_embed_text()` → `str \| None`. No `Any`. |
| Source Reflects Current Truth | PASS | No shims. Dead code removed if found. |
| uv-Only Toolchain | PASS | All execution via `uv run`. |
| Notebook Discipline | N/A | |

No violations. No Complexity Tracking entries needed.