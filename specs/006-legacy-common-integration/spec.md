# Feature Specification: Legacy Common Integration

**Feature Branch**: `006-legacy-common-integration`
**Created**: 2026-03-18
**Status**: Draft
**Input**: User description: "Replace build_helpers reimplementations with legacy_common imports — entity models, document models, graph loader, and signature map consolidation"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Entity Model Consolidation (Priority: P1) 🎯 MVP

The MCP doc_server build pipeline currently reimplements entity models (`EntityID`, `DoxygenLocation`, `DoxygenEntity`, `EntityDatabase`) as stdlib dataclasses in `build_helpers/artifact_models.py`. These are stripped-down copies of the canonical Pydantic models in `legacy_common/doxygen_parse.py`. A developer maintaining the MCP server must keep two parallel model definitions in sync — any schema change in `legacy_common` silently diverges from the build pipeline's copy, potentially producing incorrect data in the database.

After this change, the build pipeline imports entity models directly from `legacy_common.doxygen_parse`, eliminating the duplicated definitions. The `EntityID.from_str()` method in `artifact_models.py` is replaced by `EntityID.split()` from `legacy_common`.

**Why this priority**: Entity models are the foundation of the entire build pipeline. Every downstream stage (document merging, entity processing, graph loading, embedding generation) depends on these models. Consolidating them first ensures all subsequent changes build on correct, canonical types.

**Independent Test**: Can be fully tested by running the existing build pipeline (`build_mcp_db.py`) end-to-end against the artifacts directory and verifying that all entities are loaded, processed, and inserted into the database with identical results to the current pipeline. The contract tests (`tests/`) pass without modification.

**Acceptance Scenarios**:

1. **Given** the build pipeline using `legacy_common` entity models, **When** loading `code_graph.json`, **Then** all ~5,300 entities are parsed into `DoxygenEntity` instances with the same fields accessible (id, kind, name, body, decl, file, signature)
2. **Given** a `DoxygenEntity` from `legacy_common`, **When** the entity processor accesses `.signature`, **Then** functions return `definition + argsstring` and non-functions return `name`, matching current behavior
3. **Given** the `EntityID` from `legacy_common`, **When** calling `EntityID.split(entity_id_str)`, **Then** the result matches the current `EntityID.from_str()` behavior in `artifact_models.py` for both compound-only and compound+member IDs
4. **Given** `legacy-common` added as a workspace dependency, **When** running `uv sync` in the doc_server directory, **Then** the package resolves without conflicts and imports succeed

---

### User Story 2 - Document Model and Data Source Switch (Priority: P2)

The build pipeline reads documentation from the flat `artifacts/doc_db.json` file via a reimplemented `Document` dataclass and `DocumentDB` loader in `build_helpers/artifact_models.py`. This flat file is a stale snapshot with only 12 fields and 2,272 briefs. The canonical source is the per-compound `generated_docs/*.json` directory, loaded by `legacy_common/doc_db.py`'s `DocumentDB`, which has 20 fields, 4,946 briefs (93.4%), plus notes (83%), rationale (83%), and usages (55%) that the flat file entirely lacks.

After this change, the build pipeline imports `Document` and `DocumentDB` from `legacy_common.doc_db`, reads from `generated_docs/` instead of `doc_db.json`, and uses `Document.to_doxygen()` instead of the reimplemented `build_embed_text()` function for embedding text construction.

**Why this priority**: Switching the document source dramatically improves data quality — nearly doubling brief coverage and adding notes, rationale, and usages fields. This directly improves search quality, entity documentation completeness, and embedding accuracy. However, it depends on Story 1's entity model foundation being in place.

**Independent Test**: Can be tested by loading the `DocumentDB` from `generated_docs/` and comparing document counts, brief coverage, and field availability against the current `doc_db.json` loader. Verify that `Document.to_doxygen()` produces output identical to `build_embed_text()` for the same input data. The database should contain richer documentation after rebuild.

**Acceptance Scenarios**:

1. **Given** the build pipeline using `legacy_common.doc_db.DocumentDB`, **When** loading documents, **Then** documents are read from `generated_docs/*.json` files (not `doc_db.json`)
2. **Given** the new document source, **When** counting briefs after database rebuild, **Then** brief coverage is ≥90% of entities (up from ~43% with the flat file)
3. **Given** a `Document` instance from `legacy_common`, **When** calling `.to_doxygen()`, **Then** the output matches the format produced by the current `build_embed_text()` function (same Doxygen tag structure)
4. **Given** `doc_db.json` removed from the required artifacts list, **When** running artifact validation, **Then** validation passes without checking for `doc_db.json`
5. **Given** the `build_helpers/embed_text.py` module removed, **When** the embedding loader generates embed text, **Then** it calls `Document.to_doxygen()` instead

---

### User Story 3 - Graph Loader Deduplication (Priority: P3)

The build pipeline has its own `load_gml_graph()` in `build_helpers/artifact_models.py` that duplicates `load_graph()` from `legacy_common/doxygen_graph.py`. Both read a GML file into a NetworkX `MultiDiGraph` with identical logic.

After this change, the build pipeline imports `load_graph` from `legacy_common.doxygen_graph` and removes the local copy.

**Why this priority**: This is a straightforward deduplication with no behavioral change. It has no dependencies on Stories 1 or 2 and can be implemented independently, but is lower priority because the duplication has no data quality impact.

**Independent Test**: Can be tested by loading `code_graph.gml` with both the old and new loader and comparing the resulting graph (node count, edge count, edge attributes). The graphs should be identical.

**Acceptance Scenarios**:

1. **Given** the build pipeline using `legacy_common.doxygen_graph.load_graph`, **When** loading `code_graph.gml`, **Then** the resulting `MultiDiGraph` has the same nodes, edges, and attributes as the current loader produces
2. **Given** the `load_gml_graph()` function removed from `artifact_models.py`, **When** the build pipeline runs, **Then** it completes successfully using the imported loader

---

### User Story 4 - SignatureMap Computed On-the-Fly (Priority: P4)

The build pipeline loads a pre-computed `signature_map.json` artifact that maps `(compound_id, second_element)` tuples to old Doxygen entity IDs. This artifact is generated by a standalone script (`projects/doc_gen/build_signature_map.py`) that manually parses raw JSON and reimplements entity ID construction. The signature map is a derived artifact that can be computed at build time from the `EntityDatabase` and `DocumentDB`.

After this change, a `SignatureMap` class computes the mapping on-the-fly from the loaded databases, eliminating the need for the pre-computed JSON file. `signature_map.json` is removed from the required artifacts list.

**Why this priority**: Removing the pre-computed artifact simplifies the build process and eliminates a source of staleness. However, this requires Stories 1 and 2 to be complete (needs both `EntityDatabase` and `DocumentDB` from `legacy_common`).

**Independent Test**: Can be tested by computing the `SignatureMap` from databases and comparing against the current `signature_map.json` contents. All keys present in the JSON should be produced by the computed map. The deterministic entity ID generation (`compute_entity_id`) should produce the same IDs as before.

**Acceptance Scenarios**:

1. **Given** a `SignatureMap` constructed from `EntityDatabase` and `DocumentDB`, **When** looking up any key that exists in the current `signature_map.json`, **Then** the mapping produces the same old Doxygen entity ID
2. **Given** `signature_map.json` removed from the required artifacts list, **When** running artifact validation, **Then** validation passes without checking for `signature_map.json`
3. **Given** the computed `SignatureMap`, **When** the entity processor uses it to generate deterministic IDs, **Then** all entity IDs match those produced by the current pipeline

---

### User Story 5 - ResolutionResult Pydantic Conversion (Priority: P5)

The `ResolutionResult` in `server/resolver.py` is a stdlib `@dataclass` in a codebase that otherwise uses Pydantic `BaseModel` consistently. This inconsistency means `ResolutionResult` lacks Pydantic validation, serialization, and schema generation.

After this change, `ResolutionResult` is a Pydantic `BaseModel` with the same fields and behavior.

**Why this priority**: This is an isolated cleanup with no external dependencies. It improves internal consistency but does not change any user-facing behavior or data quality.

**Independent Test**: Can be tested by running the existing contract tests which exercise the resolution pipeline. The `ResolutionResult` fields and methods should behave identically.

**Acceptance Scenarios**:

1. **Given** `ResolutionResult` as a Pydantic `BaseModel`, **When** the resolution pipeline creates a result, **Then** all fields (status, match_type, candidates, resolved_from) are validated and accessible as before
2. **Given** the `to_entity_summaries()` method on the new model, **When** called with candidates, **Then** the output is identical to the current implementation

---

### Edge Cases

- What happens when `legacy_common.doc_db.DocumentDB` encounters a malformed `generated_docs/*.json` file? The current `legacy_common` implementation skips and logs an error — the build pipeline should log via loguru and continue, matching current resilience behavior.
- What happens when `legacy_common.doc_db.DocumentDB.__init__()` auto-loads from the hardcoded singleton path? The build pipeline must construct the `DocumentDB` pointed at an explicit path, not the global default. The `DocumentDB` constructor auto-loads from `GENERATED_DOCS_DIR` — the build pipeline should either pass the path explicitly or pre-set the directory before construction.
- What happens when `legacy_common.doxygen_graph.py` imports `jinja2.is_undefined` (an unused import)? This import should be removed from `legacy_common` to avoid pulling in an unnecessary dependency.
- What happens when entity processing encounters a `DoxygenEntity` from `legacy_common` that has additional fields not present in the old dataclass (e.g., `extern`, `doc`, `detailed_refs`)? The processor should access only the fields it needs; extra fields are harmless.
- What happens when `generated_docs/` has documents for entities not in `code_graph.json`? The build pipeline joins on entity IDs — unmatched documents are simply not included in the database, matching current behavior with `doc_db.json`.

## Clarifications

### Session 2026-03-18

- Q: Are modifications to `legacy_common` itself in-scope? → A: Yes — minor modifications (path params, removing unused imports) are in-scope for this feature.
- Q: Must each story be independently deployable? → A: No — single atomic integration; intermediate states may break the pipeline; only the final state must work.
- Q: Is there a build time budget for the pipeline? → A: No build time constraint — offline pipeline, speed is not a concern.
- Q: Should `build_helpers/artifact_models.py` be emptied or deleted? → A: Delete the file entirely.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Build pipeline MUST import `EntityID`, `DoxygenEntity`, `DoxygenLocation`, and `EntityDatabase` from `legacy_common.doxygen_parse` instead of `build_helpers/artifact_models.py`
- **FR-002**: Build pipeline MUST import `Document` and `DocumentDB` from `legacy_common.doc_db` instead of `build_helpers/artifact_models.py`
- **FR-003**: Build pipeline MUST read documentation from per-compound `generated_docs/*.json` files instead of the flat `doc_db.json`
- **FR-004**: Build pipeline MUST use `Document.to_doxygen()` from `legacy_common` for embedding text construction instead of `build_embed_text()`
- **FR-005**: Build pipeline MUST import `load_graph` from `legacy_common.doxygen_graph` instead of using `load_gml_graph()` from `artifact_models.py`
- **FR-006**: Build pipeline MUST compute the signature map on-the-fly from `EntityDatabase` and `DocumentDB` instead of loading `signature_map.json`
- **FR-007**: `doc_db.json` and `signature_map.json` MUST be removed from the required artifacts validation list
- **FR-008**: `build_helpers/artifact_models.py` MUST be deleted after consolidation
- **FR-009**: `build_helpers/embed_text.py` MUST be removed (replaced by `Document.to_doxygen()`)
- **FR-010**: `ResolutionResult` in `server/resolver.py` MUST be converted from `@dataclass` to Pydantic `BaseModel`
- **FR-011**: `legacy-common` MUST be added as a workspace dependency in `mcp/doc_server/pyproject.toml`
- **FR-012**: The `DocumentDB` in the build pipeline MUST NOT use the hardcoded singleton from `legacy_common` — it MUST accept an explicit path to the `generated_docs/` directory via configuration
- **FR-013**: The build pipeline MUST NOT import `ARTIFACTS_DIR` from `legacy_common` — it MUST continue using explicit paths from `server/config.py`
- **FR-014**: All existing contract tests for runtime server behavior (`tests/`) MUST pass without modification after the consolidation. Build helper tests for deleted modules (`tests/test_embed_text.py`) are removed alongside their implementation.

### Key Entities

- **EntityDatabase**: A flat mapping of entity ID string → `DoxygenEntity`, loaded from `code_graph.json`. Provides the structural backbone for all entities in the codebase (~5,300 entries).
- **DocumentDB**: A two-level mapping of `compound_id → signature → Document`, loaded from per-compound JSON files in `generated_docs/`. Provides documentation content (briefs, details, params, notes, rationale, usages) for entities.
- **SignatureMap**: A derived mapping from `(compound_id, second_element)` tuples to old Doxygen entity IDs. Used during entity processing to link documentation records to entity records and compute deterministic entity IDs.
- **Document**: A single documentation record with fields for brief, details, params, returns, notes, rationale, usages, and the `to_doxygen()` method for embedding text construction.
- **ResolutionResult**: An internal pipeline result carrying resolution status, match type, candidate entities, and the original query string. Used by the search layer, not exposed to MCP clients.

## Assumptions

- The `legacy_common` Pydantic `DoxygenEntity.from_dict()` parser handles the same JSON structure as the current dataclass parser in `artifact_models.py`. Both parse `code_graph.json` entries.
- The `legacy_common.doc_db.DocumentDB` will be modified (if needed) to accept an explicit directory path parameter rather than only the hardcoded `GENERATED_DOCS_DIR`. Minor `legacy_common` modifications are in-scope.
- The unused `jinja2.is_undefined` import in `legacy_common/doxygen_graph.py` will be removed as part of this feature (in-scope `legacy_common` modification).
- Fields present in `legacy_common` models but not used by the build pipeline (e.g., `DoxygenEntity.extern`, `DoxygenEntity.doc`, `DoxygenEntity.detailed_refs`) will not cause issues — the pipeline accesses only the subset it needs.
- The `generated_docs/` directory is present in the artifacts directory at build time. It is not a new artifact — it already exists and is the canonical documentation source used by other tools.
- The deterministic entity ID computation (`compute_entity_id` in `entity_ids.py`) remains unchanged — only the input models change, not the ID generation algorithm.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Zero reimplemented model classes remain in `build_helpers/` — all entity and document models are imported from `legacy_common`
- **SC-002**: Documentation brief coverage in the database increases from ~43% (2,272 of ~5,300 entities) to ≥90% after switching to `generated_docs/` as the data source
- **SC-003**: All existing contract tests for runtime server behavior pass without modification after the consolidation (build helper tests for deleted modules are removed)
- **SC-004**: The required artifacts list shrinks by 2 files (`doc_db.json` and `signature_map.json` no longer required)
- **SC-005**: `build_helpers/artifact_models.py` and `build_helpers/embed_text.py` are deleted, reducing codebase size by ~350 lines of duplicated code
- **SC-006**: The build pipeline completes successfully end-to-end, producing a database with identical entity IDs and richer documentation content
- **SC-007**: `ResolutionResult` passes Pydantic validation and serialization, consistent with all other models in the server
