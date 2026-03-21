# Tasks: Multi-View Search Pipeline

**Input**: Design documents from `/specs/004-multi-view-search/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/search-response.md, quickstart.md

**Tests**: Include focused contract/integration-style search tests because the feature changes the public `search` tool contract and must remain independently testable per user story.

**Organization**: Tasks are grouped by user story so each story can be implemented and validated independently.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Add the new runtime scaffolding required by every story.

- [x] T001 Add required embedding/cross-encoder settings and fail-fast config validation in mcp/doc_server/server/config.py
- [x] T002 [P] Create `CrossEncoderProvider` in mcp/doc_server/server/cross_encoder.py
- [x] T003 [P] Create the `RetrievalView` dataclass in mcp/doc_server/server/retrieval_view.py

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Replace the old single-view search foundations and remove fallback infrastructure before story work begins.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [x] T004 Remove `SearchMode` and update shared search response models in mcp/doc_server/server/enums.py, mcp/doc_server/server/models.py, and mcp/doc_server/server/tools/search.py
- [x] T005 Make embedding runtime dependencies non-optional in mcp/doc_server/server/embedding.py, mcp/doc_server/server/lifespan.py, and mcp/doc_server/server/resolver.py
- [x] T006 Replace the single-view entity schema with dual embeddings/tsvectors and trigram-ready columns in mcp/doc_server/server/db_models.py; add `pg_trgm` extension creation to `drop_and_create_schema()` and define `SearchConfig` metadata table (FR-008, FR-042)
- [x] T007 Add complete `qualified_name` derivation (containment-graph traversal per FR-016 + `definition_text` fallback parsing per FR-017) and dual embed-text builders (`build_doc_embed_text`, `build_symbol_embed_text`) in mcp/doc_server/build_helpers/entity_processor.py
- [x] T008 Rework the ETL for pg_trgm, dual embedding caches, dual tsvectors, `symbol_searchable`, and ts_rank ceiling computation (compute p99 per tsvector column post-population, store in a metadata table for startup loading) in mcp/doc_server/build_mcp_db.py
- [x] T009 Wire lifespan startup to initialize the cross-encoder, load precomputed ts_rank ceilings from the metadata table, and instantiate `RetrievalView` objects in mcp/doc_server/server/lifespan.py

**Checkpoint**: Foundation ready — story implementation can begin.

---

## Phase 3: User Story 1 - Symbol-Precise Entity Lookup (Priority: P1) 🎯 MVP

**Goal**: Return exact, fuzzy, and signature-aware identifier matches with symbol-first ranking.

**Independent Test**: Search for `stc`, `do_look`, `PLR_COLOR2`, `Character`, and a misspelled identifier; verify correct entities appear in top results and fuzzy trigram matches surface plausible candidates.

### Tests for User Story 1

- [x] T010 [P] [US1] Add symbol lookup coverage in mcp/doc_server/tests/test_search_symbol_lookup.py

### Implementation for User Story 1

- [x] T011 [US1] Implement exact-name, signature-token, and symbol-keyword retrieval helpers in mcp/doc_server/server/search.py
- [x] T012 [US1] Add trigram similarity and symbol-first ranking for identifier queries in mcp/doc_server/server/search.py
- [x] T013 [US1] Return symbol lookup results through the updated search tool contract in mcp/doc_server/server/tools/search.py

**Checkpoint**: User Story 1 works independently for exact, partial, and fuzzy symbol lookup.

---

## Phase 4: User Story 2 - Behavioral / Conceptual Search (Priority: P1)

**Goal**: Return documentation-driven matches for natural-language behavioral queries.

**Independent Test**: Search for `functions that handle player death processing` and `poison spreading between characters`; verify relevant documented entities surface even when names do not contain the query terms.

### Tests for User Story 2

- [x] T014 [P] [US2] Add conceptual-search coverage in mcp/doc_server/tests/test_search_conceptual.py

### Implementation for User Story 2

- [x] T015 [US2] Implement doc-semantic and doc-keyword retrieval helpers in mcp/doc_server/server/search.py
- [x] T016 [US2] Merge doc and symbol candidates by `entity_id` while preserving per-view signal vectors in mcp/doc_server/server/search.py
- [x] T017 [US2] Update tool-level handling for doc-view queries and unchanged `source` semantics in mcp/doc_server/server/tools/search.py

**Checkpoint**: User Stories 1 and 2 both work independently for identifier and prose queries.

---

## Phase 5: User Story 3 - Noise Filtering and Reranking (Priority: P2)

**Goal**: Eliminate weak candidates and rank survivors with cross-encoder scores instead of weighted score fusion.

**Independent Test**: Search for `xyzzy foobar baz` and verify zero results. Search for a real mixed query and verify returned results include `winning_view`, `winning_score`, and `losing_score` with sensible ordering.

### Tests for User Story 3

- [x] T018 [P] [US3] Add filtering/reranking coverage in mcp/doc_server/tests/test_search_reranking.py

### Implementation for User Story 3

- [x] T019 [US3] Implement per-signal floor filtering and `name_exact` bypass in mcp/doc_server/server/search.py
- [x] T020 [US3] Add cross-encoder reranking and `winning_view`/`winning_score`/`losing_score` assignment in mcp/doc_server/server/search.py
- [x] T021 [US3] Add per-search/build observability logging in mcp/doc_server/server/search.py and mcp/doc_server/build_mcp_db.py

**Checkpoint**: User Stories 1–3 return filtered, reranked results with meaningful metadata.

---

## Phase 6: User Story 4 - Qualified Name Navigation (Priority: P3)

**Goal**: Disambiguate same-name entities by fully-qualified scope and containment-derived names.

**Independent Test**: Search for `Logging::stc` and `Character::position`; verify the correctly scoped entity ranks above unscoped or differently scoped matches and that database rows contain derived `qualified_name` values.

### Tests for User Story 4

- [x] T022 [P] [US4] Add qualified-name navigation coverage in mcp/doc_server/tests/test_search_qualified_name.py

### Implementation for User Story 4

- [x] T023 [US4] Implement scoped-query disambiguation in mcp/doc_server/server/search.py: detect `::` separators in the query, boost candidates whose `qualified_name` matches the requested scope, and apply scope-aware ranking adjustments (derivation is complete after T007)
- [x] T025 [US4] Surface `qualified_name`-driven symbol text and scoped ranking inputs in mcp/doc_server/server/tools/search.py (`build_mcp_db.py` qualified_name integration is complete after T008)

**Checkpoint**: All user stories are independently functional, including fully-qualified scope navigation.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Finalize docs, regressions, and validation across all stories.

- [x] T026 [P] Update required-runtime setup docs in mcp/doc_server/INSTALL.md and mcp/doc_server/README.md
- [x] T027 [P] Align feature docs with the final response contract in specs/004-multi-view-search/quickstart.md and specs/004-multi-view-search/contracts/search-response.md
- [x] T028 [P] Add `source="usages"` regression coverage in mcp/doc_server/tests/test_search_tool.py
- [x] T029 Benchmark embedding model candidates (per A-004/A-005), finalize `RetrievalView` model parameters; calibrate default per-signal floor thresholds and per-channel retrieval limits (N) against representative queries in mcp/doc_server/server/search.py and mcp/doc_server/server/config.py
- [x] T030 Run end-to-end validation against all search test files (test_search_symbol_lookup.py, test_search_conceptual.py, test_search_reranking.py, test_search_qualified_name.py, test_search_tool.py); 232 tests passing

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1: Setup** — no dependencies
- **Phase 2: Foundational** — depends on Phase 1 and blocks all user stories
- **Phase 3: US1** — depends on Phase 2
- **Phase 4: US2** — depends on Phase 2
- **Phase 5: US3** — depends on US1 and US2 because reranking/filtering wraps the merged candidate pipeline
- **Phase 6: US4** — depends on Phase 2 and benefits from US1 symbol ranking work
- **Phase 7: Polish** — depends on all desired user stories

### User Story Dependencies

- **US1 (P1)**: independent after Foundational
- **US2 (P1)**: independent after Foundational
- **US3 (P2)**: depends on US1 + US2 search channels being in place
- **US4 (P3)**: depends on Foundational build/schema work; can follow US1 for scoped symbol ranking refinements

### Within Each User Story

- Test task first
- Core retrieval/build logic before tool wiring
- Tool wiring before full validation
- Story checkpoint before moving to lower-priority work

---

## Parallel Opportunities

- **Setup**: T002 and T003 can run in parallel
- **US1**: T010 can be prepared while foundational work is finishing
- **US2**: T014 can be prepared independently of US1 implementation
- **US3**: T018 can be prepared independently while US1/US2 stabilize
- **US4**: T022 can be prepared independently while earlier stories stabilize
- **Polish**: T026, T027, and T028 can run in parallel

### Parallel Example: User Story 1

```text
- T010 [US1] Add symbol lookup coverage in mcp/doc_server/tests/test_search_symbol_lookup.py
- T012 [US1] Add trigram similarity and symbol-first ranking for identifier queries in mcp/doc_server/server/search.py
```

### Parallel Example: User Story 2

```text
- T014 [US2] Add conceptual-search coverage in mcp/doc_server/tests/test_search_conceptual.py
- T015 [US2] Implement doc-semantic and doc-keyword retrieval helpers in mcp/doc_server/server/search.py
```

### Parallel Example: Polish

```text
- T026 Update required-runtime setup docs in mcp/doc_server/INSTALL.md and mcp/doc_server/README.md
- T027 Align feature docs with the final response contract in specs/004-multi-view-search/quickstart.md and specs/004-multi-view-search/contracts/search-response.md
- T028 Add `source="usages"` regression coverage in mcp/doc_server/tests/test_tools.py
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1
4. Validate symbol lookup independently
5. Demo/search-check before expanding scope

### Incremental Delivery

1. Foundation → shared infra and schema ready
2. Add US1 → identifier search MVP
3. Add US2 → conceptual search
4. Add US3 → filtering and reranking quality improvements
5. Add US4 → scoped disambiguation and qualified-name navigation
6. Finish Polish → docs, regressions, calibration, end-to-end validation

### Parallel Team Strategy

After Foundational completes:
- Developer A: US1 symbol retrieval
- Developer B: US2 doc retrieval
- Developer C: US4 qualified-name test prep / build validation
- Integrate into US3 reranking once US1 and US2 are stable

---

## Notes

- `[P]` tasks touch different files and have no direct dependency on incomplete work
- The `entity_usages` pipeline remains unchanged except for regression coverage
- Use `uv run` for all Python execution, testing, linting, and validation
- No compatibility shims or fallback paths should be introduced while implementing these tasks
