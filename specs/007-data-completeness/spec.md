# Feature Specification: MCP Build Pipeline — Data Completeness Fixes

**Feature Branch**: `007-data-completeness`  
**Created**: 2026-03-18  
**Status**: Draft  
**Input**: User description: "Fix Phase B data completeness gaps: source code extraction, params normalization, and embedding coverage"

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Source Code Available in Entity Lookups (Priority: P1) 🎯 MVP

An AI assistant calls `get_entity(entity_id, include_code=true)` or `get_source_code(entity_id)` expecting to read the actual C++ implementation of a function or class. Today these fields return `null` for all 5,305 entities because `extract_source_code()` silently yields zero results when `PROJECT_ROOT` does not resolve to the legacy C++ source tree. After this fix, the build pipeline validates source extraction and populates `source_text` and `definition_text` for every entity that has body-location metadata in the code graph.

**Why this priority**: Source code retrieval is the most-used tool in the spec-creating agent's workflow (`get_source_code`, `get_entity(include_code=true)`). With zero source populated, these tools return nothing useful — the server's primary value proposition is undermined.

**Independent Test**: Run the build pipeline with a correctly configured `PROJECT_ROOT`. Query `SELECT COUNT(*) FROM entities WHERE source_text IS NOT NULL` and verify the count is non-zero and proportional to entities with body locations in the code graph. Attempt the build with an invalid `PROJECT_ROOT` and verify it exits with a clear error.

**Acceptance Scenarios**:

1. **Given** a correct `PROJECT_ROOT` pointing to the legacy C++ source tree, **When** the build pipeline runs `extract_source_code()`, **Then** `source_text` is populated for ≥90% of entities that have `body.fn`, `body.line`, and `body.end_line` in the code graph
2. **Given** a correct `PROJECT_ROOT`, **When** the build pipeline runs, **Then** `definition_text` is populated for ≥90% of entities that have `decl.fn` and `decl.line` in the code graph
3. **Given** an invalid or missing `PROJECT_ROOT`, **When** the build pipeline calls `extract_source_code()`, **Then** the build fails with a clear error message naming the configured path and the expected file structure
4. **Given** entities with body locations whose source files cannot be read (e.g., deleted file), **When** the build pipeline runs, **Then** those entities are logged as warnings but do not prevent the build from completing (only a global zero-extraction count is fatal)
5. **Given** the build completes successfully, **When** an AI assistant calls `get_source_code(entity_id)` for a function with body location, **Then** the response includes the actual C++ source text between `body.line` and `body.end_line`

---

### User Story 2 — Improved Embedding Coverage for Search (Priority: P2)

An AI assistant searches for a variable or function by semantic query (e.g., "global player list") but gets no results because the entity has no embedding. Currently, 789 of 5,305 entities lack embeddings because `generate_embeddings()` skips entities without a `Document` object. After this fix, doc-less entities receive a minimal embedding derived from their signature, name, and kind — making them discoverable via semantic search even without LLM-generated documentation.

**Why this priority**: Search is the sole discovery path from natural language to entity IDs (spec 005 retired `resolve_entity`). Missing embeddings mean missing search results. Switching to `generated_docs/` (spec 006) already closes most of the gap (~541 of 789), but ~248 structural compounds and remaining doc-less entities still need coverage.

**Independent Test**: After a full build, query `SELECT COUNT(*) FROM entities WHERE embedding IS NULL`. Verify the count is zero (or limited to entities with genuinely zero documentable content — no name, no signature, no kind). Run `search("player list global variable")` and verify that `player_list` (a global variable) appears in results.

**Acceptance Scenarios**:

1. **Given** an entity with a `Document` (brief, details, etc.), **When** the build generates embeddings, **Then** the embedding is derived from `doc.to_doxygen()` (unchanged from current behavior)
2. **Given** an entity without a `Document` but with a signature and name, **When** the build generates embeddings, **Then** a minimal embedding is generated from a structured text combining `kind`, `name`, and `signature`
3. **Given** a structural compound entity (file, dir, namespace) without documentation, **When** the build generates embeddings, **Then** a minimal embedding is generated from the entity's name, kind, and file path (these entities are search targets because higher-level documentation references them)
4. **Given** the build completes, **When** querying embedding coverage, **Then** ≥95% of all entities have non-null embeddings (up from the current ~85%)
5. **Given** a doc-less entity that received a minimal embedding, **When** an AI assistant searches semantically, **Then** the entity appears in results when the query is conceptually related to its name or signature

---

### User Story 3 — Accurate Params Filtering (Priority: P3)

A developer or AI assistant queries the database for entities that have meaningful parameter documentation (`WHERE params IS NOT NULL`). Today this returns 5,055 rows, but only ~1,799 have actual parameter content — the remaining ~3,256 are empty dicts (`{}`) stored because `MergedEntity.doc.params` defaults to `{}` for non-function entities or functions without documented params. After this fix, `params` is `NULL` when empty, making database queries semantically correct.

**Why this priority**: This is a data hygiene fix that makes queries meaningful. It does not affect end-user-visible tools directly but ensures that internal queries, statistics, and any future tooling that filters by `params IS NOT NULL` produce correct results.

**Independent Test**: After a rebuild, query `SELECT COUNT(*) FROM entities WHERE params IS NOT NULL` and compare with the count of entities that have at least one non-empty param key-value pair. The two counts should match.

**Acceptance Scenarios**:

1. **Given** an entity whose document has `params = {}`, **When** the build inserts into the database, **Then** `params` is stored as `NULL`
2. **Given** an entity whose document has `params = None`, **When** the build inserts into the database, **Then** `params` is stored as `NULL`
3. **Given** an entity whose document has `params = {"ch": "The character receiving damage"}`, **When** the build inserts into the database, **Then** `params` is stored as the JSON object
4. **Given** an entity with no document at all, **When** the build inserts into the database, **Then** `params` is stored as `NULL`
5. **Given** the build completes, **When** querying `SELECT COUNT(*) FROM entities WHERE params IS NOT NULL`, **Then** the count roughly matches the number of entities with meaningful param documentation (~1,800–2,100 based on `generated_docs/` data)

---

### Edge Cases

- What happens when a source file referenced in `body.fn` exists but the line range (`body.line` to `body.end_line`) exceeds the file length? The build MUST fail with a `BuildError` — this indicates the code graph is stale or corrupt relative to the source tree.
- What happens when `body.fn` uses a relative path that doesn't match the file layout under `PROJECT_ROOT`? The extraction should attempt the path as-is relative to `PROJECT_ROOT`; if it fails, log the mismatch.
- What happens when an entity has a signature but both name and kind are empty? The minimal embedding fallback should still produce an embedding from whatever text is available; only skip if all three fields (name, signature, kind) are empty/null.
- What happens when the embedding provider is not configured (keyword-only mode)? The build should skip embedding generation entirely (current behavior), and the params and source code fixes should still apply independently.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The build pipeline MUST fail with a non-zero exit code and a clear error message if `extract_source_code()` processes entities with body locations but extracts zero source texts. The threshold is zero-only; any non-zero extraction count passes. The ≥90% quality target (SC-001) is measured post-build, not enforced as a build gate
- **FR-002**: The error message from FR-001 MUST include the configured `PROJECT_ROOT` path and state that the expected source files were not found at that location
- **FR-003**: The build pipeline MUST populate `source_text` for entities that have `body.fn`, `body.line`, and `body.end_line` in the code graph, reading from `PROJECT_ROOT / body.fn`
- **FR-004**: The build pipeline MUST populate `definition_text` for entities that have `decl.fn` and `decl.line` in the code graph, reading the single declaration line from `PROJECT_ROOT / decl.fn`
- **FR-005**: The build pipeline MUST store `params` as `NULL` when the value is `None`, `{}`, or absent — not as an empty JSON object
- **FR-006**: The build pipeline MUST generate embeddings for entities without a `Document` by constructing a minimal text from `kind`, `name`, `signature`, and `file_path` — including structural compounds (file, dir, namespace) which are referenced by higher-level documentation
- **FR-007**: The minimal embedding text (FR-006) MUST follow a structured format (e.g., Doxygen-like tag + signature) consistent with the existing embedding text format so that semantic similarity comparisons remain meaningful
- **FR-008**: The build pipeline MUST log a summary after source extraction showing: entities with body locations, successful extractions, failures, and the extraction success rate
- **FR-009**: The build pipeline MUST log a summary after embedding generation showing: entities with doc embeddings, entities with minimal embeddings, entities with no embedding, and the total coverage rate
- **FR-010**: Individual source file read failures (file not found, encoding errors, line range issues) MUST be logged as warnings but MUST NOT fail the build — only a global zero-extraction count is a build failure

### Key Entities

- **MergedEntity**: The intermediate representation joining entity metadata (from `EntityDatabase`) with documentation (from `DocumentDB`). Extended with `source_text`, `definition_text`, and `embedding` during the build pipeline.
- **Entity (DB row)**: The final database record in the `entities` table. `source_text`, `definition_text`, `params`, and `embedding` columns are the targets of this spec.
- **Document**: The `legacy_common.doc_db.Document` object providing brief, details, params, notes, rationale, usages. `params` may be `{}` when empty.

## Clarifications

### Session 2026-03-18

- Q: Should the build validate that the source tree matches the artifact generation point (commit hash comparison)? → A: No validation — trust the developer to keep source and artifacts in sync.
- Q: Should structural compounds (file/dir/namespace) receive embeddings and appear in semantic search? → A: Yes, embed all. Higher-level documentation references these structural entities; callers filter by `kind` if needed.
- Q: What minimum extraction success rate should cause the build to fail? → A: Zero-only gate (any non-zero count passes). The ≥90% target (SC-001) is a post-build quality measurement, not a build-time gate.

## Assumptions

- `PROJECT_ROOT` in `.env` points to the root of the legacy C++ source tree (the directory containing `src/`, `include/`, etc.). This is an existing configuration field.
- The code graph's `body.fn` and `decl.fn` paths are relative to `PROJECT_ROOT`. This is how `extract_source_code()` currently resolves them.
- The source tree at `PROJECT_ROOT` is assumed to match the state from which `code_graph.json` was generated. The build pipeline does not validate this alignment — the developer is responsible for ensuring consistency. The C++ source is a legacy frozen codebase; if artifacts are regenerated, the source tree must correspond to the same revision.
- The `Document.to_doxygen()` method from `legacy_common` produces the canonical embedding text for entities with documentation. Minimal embeddings for doc-less entities should approximate this format.
- The embedding dimension is consistent between doc-based and minimal embeddings because they use the same provider/model.
- The `generated_docs/` switch (spec 006) is complete and merged before this work begins — this spec builds on that foundation.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: After a successful build, ≥90% of entities with body locations in the code graph have non-null `source_text` in the database
- **SC-002**: After a successful build, ≥95% of all entities have non-null `embedding` in the database
- **SC-003**: After a successful build, the count of entities with `params IS NOT NULL` is within 15% of the count of entities with at least one documented parameter (approximately 1,800–2,100)
- **SC-004**: An attempted build with an invalid `PROJECT_ROOT` exits with a non-zero code within the source extraction stage (does not silently continue)
- **SC-005**: A before/after comparison of the database shows: briefs ≥4,900 (from spec 006), `source_text` populated for entities with body locations, params correctly nullified, embedding coverage ≥95%
