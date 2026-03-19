# Tasks: Knowledge Graph Enrichment (V1)

**Input**: Design documents from `/specs/001-kg-enrichment/`
**Prerequisites**: plan.md (required), spec.md (required), data-model.md, contracts/tools.md, research.md, quickstart.md

**Tests**: Included — the existing V1 server uses contract tests as the primary validation strategy. Tests follow the established async mock-context pattern (no real DB).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

All paths relative to `mcp/doc_server/` within the repository root.

---

## Phase 1: Setup

**Purpose**: No new project initialization needed — this feature extends the existing MCP doc server. Setup phase verifies assumptions from research.md.

- [ ] T001 Verify usages dict key format by inspecting artifacts — run a scratch script in `.scratch/verify_usages_format.py` that loads 3+ generated_docs JSON files, parses usages keys by splitting on `", "`, and asserts the format matches `"{compound_id}, {caller_signature}"` → description string (research.md R1)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Schema changes, build pipeline enrichment, and test fixture updates that ALL user stories depend on.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

### Schema & Models

- [ ] T002 [P] Add four new columns to Entity model in `server/db_models.py`: `doc_state: str | None`, `notes_length: int | None`, `is_contract_seed: bool` (default False), `rationale_specificity: float | None`. Follow existing column patterns (nullable types, Field definitions).

- [ ] T003 Add EntityUsage SQLModel in `server/db_models.py` with `table=True`: composite PK `(callee_id, caller_compound, caller_sig)`, `description: str`, `embedding: list[float] | None` (Vector(768)), `search_vector: str | None` (TSVECTOR). Add FK on `callee_id` → `entities.entity_id`. Add indexes per data-model.md: callee, caller compound, HNSW on embedding, GIN on search_vector.

- [ ] T004 [P] Add new Pydantic response models in `server/models.py`: `CallingPattern(caller_compound, caller_sig, description)`, `UsageEntry(caller_compound, caller_sig, description)`, `MatchingUsage(caller_compound, caller_sig, description, score)`, `ContractMetadata(doc_state, is_contract_seed, rationale_specificity, fan_in, fan_out, capability)`. Add `doc_state`, `notes_length`, `is_contract_seed`, `rationale_specificity` fields to `EntityDetail`. Add optional `top_usages: list[UsageEntry] | None` to `EntityDetail`.

- [ ] T005 Update `EntitySummary` and `EntityDetail` converter functions in `server/converters.py` to populate the new `doc_state`, `notes_length`, `is_contract_seed`, `rationale_specificity` fields from the Entity ORM object.

### Build Pipeline — Entity Enrichment (FR-001 through FR-004)

- [ ] T006 Extend entity processing in `build_helpers/entity_processor.py` to compute derived fields during entity merge: carry `doc.state` → `doc_state`, compute `notes_length` from `len(doc.notes)` when non-null, compute `is_contract_seed` from `fan_in > threshold AND rationale is not None` (threshold as a configurable constant, start with 10), compute `rationale_specificity` heuristic (length * domain-term ratio — define a small set of domain terms from the codebase vocabulary). Validate that required source fields (`state`, `brief`) are present on each generated_docs entry; raise with a clear error identifying the malformed entry if missing (FR-013).

- [ ] T007 Update `populate_entities()` in `build_mcp_db.py` to pass the four new fields (`doc_state`, `notes_length`, `is_contract_seed`, `rationale_specificity`) through to the Entity model during database insertion.

### Build Pipeline — Entity Usages Table (FR-005, FR-006, FR-012)

- [ ] T008 Add `populate_entity_usages()` function in `build_mcp_db.py` that: (a) drops and recreates the `entity_usages` table, (b) iterates over all merged entities with non-null `usages` dicts, (c) parses each usages key by splitting on first `", "` into `(caller_compound, caller_sig)`, (d) creates EntityUsage rows with `callee_id` = entity's deterministic ID, (e) generates tsvector search vectors for each description using PostgreSQL `to_tsvector('english', description)` via raw SQL after insertion. Reference the key parsing format from research.md R1.

- [ ] T009 Extend usage embeddings generation in `build_helpers/embeddings_loader.py`: add a function `generate_usage_embeddings()` that collects all usage descriptions as a flat list, calls `provider.embed_documents_sync()` in a single batch, and returns a mapping of `(callee_id, caller_compound, caller_sig)` → embedding vector. Call this from `populate_entity_usages()` and attach embeddings to EntityUsage rows before insertion.

- [ ] T010 Wire `populate_entity_usages()` into the `main()` build pipeline in `build_mcp_db.py` — call it after `populate_entities()` and `populate_edges()`, passing the merged entities and embedding provider. Add schema creation for the `entity_usages` table alongside the existing table creation block.

### Test Fixtures

- [ ] T011 Update test fixtures in `tests/conftest.py`: (a) add `doc_state`, `notes_length`, `is_contract_seed`, `rationale_specificity` fields to all 7 `sample_entities` — give `damage` (index 0) `doc_state="refined_summary"`, `notes_length=150`, `is_contract_seed=True`, `rationale_specificity=0.85`; give others varying values including some nulls. (b) Add `sample_entity_usages` fixture creating 5 EntityUsage rows for the `damage` entity with distinct caller compounds, signatures, and descriptions. Populate embeddings as None (tests don't need real vectors). (c) Add tsvector population for entity_usages descriptions via raw SQL, matching the pattern used for entities.

**Checkpoint**: Foundation ready — enriched entities and entity_usages table are built and populated. All user story implementation can begin.

---

## Phase 3: User Story 1 — Spec Agent Retrieves Behavioral Contract (Priority: P1) 🎯 MVP

**Goal**: `explain_interface` tool returns a five-part behavioral contract composed from entity fields + top 5 usage patterns.

**Independent Test**: Query `explain_interface` for the `damage` sample entity and verify all five sections are populated.

### Tests for User Story 1

- [ ] T012 [P] [US1] Write contract tests in `tests/test_explain_interface.py`: (a) test full contract — call `explain_interface(entity_id=damage_id)` and assert all 5 sections present: `signature_block` non-null, `mechanism.brief` and `mechanism.details` populated, `contract.rationale` populated, `preconditions.notes` populated, `calling_patterns` has ≤5 entries from sample_entity_usages. (b) test partial contract — call for an entity with null rationale and assert `contract` section is None. (c) test entity not found — assert appropriate error. (d) test metadata fields — assert `doc_state`, `is_contract_seed`, `rationale_specificity`, `fan_in`, `fan_out`, `capability` are present and correct.

### Implementation for User Story 1

- [ ] T013 [US1] Add `ExplainInterfaceResponse` model in `server/models.py` with sections: `signature_block: str | None`, `mechanism: MechanismSection`, `contract: ContractSection | None`, `preconditions: PreconditionsSection | None`, `calling_patterns: list[CallingPattern]`, `metadata: ContractMetadata`. Define `MechanismSection(brief, details)`, `ContractSection(rationale)`, `PreconditionsSection(notes)` as nested Pydantic models.

- [ ] T014 [US1] Implement `explain_interface` tool in `server/tools/explain.py`: (a) register with `@mcp.tool()`, accept `entity_id: str` parameter, (b) fetch entity by PK via `session.get(Entity, entity_id)`, (c) query `entity_usages` for this callee_id, join against `entities` table on `(caller_compound, caller_sig)` matching `(entities.file_path-derived compound, entities.signature)` to get caller fan_in — or use a simpler approach: subquery matching `caller_sig` against `entities.signature` to look up fan_in, default to 0 for unmatched callers, ORDER BY fan_in DESC LIMIT 5, (d) compose the five-part response, (e) return `ExplainInterfaceResponse`.

- [ ] T015 [US1] Register `explain_interface` tool module in `server/server.py` by adding `import server.tools.explain` alongside existing tool imports.

**Checkpoint**: `explain_interface` returns structured behavioral contracts. US1 independently testable.

---

## Phase 4: User Story 2 — Spec Agent Searches by Usage Intent (Priority: P1)

**Goal**: `search` tool with `source="usages"` performs hybrid search over usage descriptions, grouped by callee entity.

**Independent Test**: Search with `source="usages"` and a domain query; verify results include expected entities with matching usage descriptions inlined.

### Tests for User Story 2

- [ ] T016 [P] [US2] Write contract tests in `tests/test_search_tool.py` (additions to existing file): (a) test `source="usages"` returns results with `matching_usages` field populated — use a keyword that appears in sample_entity_usages descriptions. (b) test `source="usages"` groups by callee — verify no duplicate entity_ids in results. (c) test `source="usages"` with `kind` filter — verify filter applies to callee entity, not usage row. (d) test `source="entity"` (default) behavior unchanged — existing tests should still pass.

### Implementation for User Story 2

- [ ] T017 [US2] Add `"usages"` to the `source` parameter validation in `server/tools/search.py`. Update the source parameter's allowed values (and add to `SearchSource` enum in `server/enums.py` if the enum exists) and route `source="usages"` to a new search path.

- [ ] T018 [US2] Implement `hybrid_search_usages()` function in `server/search.py`: (a) semantic search: embed query via provider, cosine distance against `entity_usages.embedding`, return top N rows with scores, (b) keyword search: `plainto_tsquery` against `entity_usages.search_vector`, `ts_rank` for scoring, (c) combine scores with semantic 0.6 + keyword 0.4 weighting (no exact-match boost), (d) group results by `callee_id` — for each callee, collect top-matching usage descriptions with scores, (e) fetch callee `EntitySummary` for each group, (f) apply `kind` and `capability` filters to the callee entity, (g) return `SearchResponse` with `matching_usages` populated on each `SearchResult`.

- [ ] T019 [US2] Add `matching_usages: list[MatchingUsage] | None` field to `SearchResult` model in `server/models.py`. Default to None. Populate only when `source="usages"`.

**Checkpoint**: Usage-based semantic search operational. Agents can search by behavioral intent. US2 independently testable.

---

## Phase 5: User Story 3 — Planning Agent Assesses Documentation Quality (Priority: P2)

**Goal**: `get_entity` returns enriched metadata (`doc_state`, `notes_length`, `is_contract_seed`, `rationale_specificity`) and supports `include_usages` for inline top-5 patterns.

**Independent Test**: Fetch an entity and verify new metadata fields are present and correctly valued.

### Tests for User Story 3

- [ ] T020 [P] [US3] Write contract tests in `tests/test_entity_tools.py` (additions to existing file): (a) test new fields present — call `get_entity(entity_id=damage_id)` and assert `doc_state`, `notes_length`, `is_contract_seed`, `rationale_specificity` are in the response with expected values from fixtures. (b) test `include_usages=True` — assert `top_usages` is a list of ≤5 `UsageEntry` items. (c) test `include_usages=False` (default) — assert `top_usages` is None. (d) test entity with null doc fields — assert null fields are correctly represented.

### Implementation for User Story 3

- [ ] T021 [US3] Add `include_usages: bool = False` parameter to the `get_entity` tool function in `server/tools/entity.py`. When true, query `entity_usages` for the entity's callee_id, rank by caller fan_in (same ranking approach as `explain_interface`), take top 5, and populate `top_usages` on the `EntityDetail` response.

- [ ] T022 [US3] Verify that the foundational converter changes (T005) correctly surface `doc_state`, `notes_length`, `is_contract_seed`, `rationale_specificity` in the `EntityDetail` response for all existing tool paths (get_entity, get_entity with neighbors, etc.).

**Checkpoint**: Planning agents can triage entities by documentation quality. US3 independently testable.

---

## Phase 6: User Story 4 — Auditor Agent Verifies Spec Claims (Priority: P2)

**Goal**: Auditor workflow is enabled by US1 + US2 working together — no additional tools needed.

**Independent Test**: Use `explain_interface` on a well-documented entity and verify the contract evidence is sufficient for cross-referencing against a spec claim.

### Implementation for User Story 4

- [ ] T023 [US4] Validate end-to-end auditor workflow with a test in `tests/test_explain_interface.py` (addition): given a sample entity with known behavioral contract, call `explain_interface` and verify that the combined evidence (rationale + calling patterns + doc_state) is sufficient for an auditor to assess a behavioral claim. Assert that `metadata.doc_state` is present for trust assessment and `calling_patterns` contains evidence from diverse callers.

**Checkpoint**: Auditor workflow validated. All four user stories independently functional.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Validation, cleanup, and cross-story integration.

- [ ] T024 [P] Run `uv run ruff check .` and `uv run ruff format .` from `mcp/doc_server/` to ensure all new code passes linting.
- [ ] T025 [P] Run `uv run mypy server/` from `mcp/doc_server/` to verify strict type checking passes on all modified and new files.
- [ ] T026 Run full test suite: `uv run pytest tests/ -v` from `mcp/doc_server/` — verify all existing tests still pass alongside new tests.
- [ ] T027 Run quickstart.md validation: execute `uv run python -m build_script.build_mcp_db` against a real PostgreSQL instance and verify (a) entity_usages table has ~24,803 rows, (b) all 5,295 documented entities have `doc_state` populated, (c) `is_contract_seed` entities are a reasonable subset of high-fan-in entities.
- [ ] T028 Clean up `.scratch/verify_usages_format.py` from T001.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Setup (T001 validates assumptions) — BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Foundational (Phase 2) — no dependencies on other stories
- **US2 (Phase 4)**: Depends on Foundational (Phase 2) — no dependencies on other stories
- **US3 (Phase 5)**: Depends on Foundational (Phase 2) — no dependencies on other stories
- **US4 (Phase 6)**: Depends on US1 (Phase 3) and US2 (Phase 4) — validates auditor workflow
- **Polish (Phase 7)**: Depends on all desired user stories being complete

### User Story Dependencies

- **US1 (P1)**: Can start after Phase 2. Independent.
- **US2 (P1)**: Can start after Phase 2. Independent of US1.
- **US3 (P2)**: Can start after Phase 2. Independent of US1/US2.
- **US4 (P2)**: Depends on US1 and US2 completion (uses `explain_interface` + usage search evidence).

### Within Each User Story

- Tests written first (TDD: verify they fail before implementation)
- Models/response types before tool implementation
- Tool implementation before registration
- Registration before integration testing

### Parallel Opportunities

- **Phase 2**: T002 and T004 can run in parallel (different files). T003 must follow T002 (same file: `db_models.py`). T006 + T007 are sequential (entity_processor → build_mcp_db). T008, T009 are sequential (usages population → embedding generation). T011 depends on T002 + T003 (needs model classes).
- **Phase 3–5**: US1, US2, US3 can all start in parallel after Phase 2 completes. Each story modifies different files.
- **Within US1**: T012 (tests) and T013 (response models) can run in parallel.
- **Within US2**: T016 (tests) and T017 + T018 (implementation) — tests first in TDD, but T17 and T19 can be parallel.

---

## Parallel Example: Foundational Phase

```bash
# Launch schema + model changes in parallel (different files):
Task T002: "Add Entity columns in server/db_models.py"
Task T003: "Add EntityUsage model in server/db_models.py"  # Same file as T002 — run sequentially
Task T004: "Add response models in server/models.py"       # Different file — parallel with T002

# After schema tasks complete, launch build pipeline tasks:
Task T006: "Entity enrichment in build_helpers/entity_processor.py"
Task T008: "Usages population in build_mcp_db.py"          # Can parallel with T006 (different file)
```

## Parallel Example: User Stories (after Phase 2)

```bash
# All three stories can start simultaneously:
# Developer/Agent A: US1 (explain_interface)
Task T012: "Tests in tests/test_explain_interface.py"
Task T013: "Response models in server/models.py"
Task T014: "Tool in server/tools/explain.py"

# Developer/Agent B: US2 (usage search)
Task T016: "Tests in tests/test_search_tool.py"
Task T017: "Search routing in server/tools/search.py"
Task T018: "Hybrid search in server/search.py"

# Developer/Agent C: US3 (get_entity enrichment)
Task T020: "Tests in tests/test_entity_tools.py"
Task T021: "include_usages in server/tools/entity.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001)
2. Complete Phase 2: Foundational (T002–T011)
3. Complete Phase 3: User Story 1 — `explain_interface` (T012–T015)
4. **STOP and VALIDATE**: Test `explain_interface` with real data via quickstart build
5. This alone delivers the core value: structured behavioral contracts for spec agents

### Incremental Delivery

1. Setup + Foundational → Foundation ready (enriched entities + usages table)
2. Add US1 → `explain_interface` operational → **MVP!**
3. Add US2 → Usage-based search operational → Agents can search by intent
4. Add US3 → `get_entity` enriched → Planning agents have quality signals
5. Add US4 → Auditor workflow validated → Full feature complete
6. Each story adds value without breaking previous stories

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- T002 and T003 modify the same file (`db_models.py`) — T003 must follow T002
- T013 (US1) and T019 (US2) both modify `server/models.py` — must follow T004 (Phase 2) completion
- All tests use the async mock-context pattern from existing `conftest.py` — no real DB needed
- The `explain_interface` caller fan-in ranking requires a join or subquery against `entities` — the exact SQL approach should be determined during T014 implementation
- `rationale_specificity` formula in T006 is deliberately approximate (v1 heuristic) — domain terms can be extracted from capability_defs.json vocabulary
