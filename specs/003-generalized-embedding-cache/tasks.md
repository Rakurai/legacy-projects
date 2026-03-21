# Tasks: Generalized Embedding Cache

**Input**: Design documents from `/specs/003-generalized-embedding-cache/`
**Branch**: `003-generalized-embedding-cache`

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on in-progress tasks)
- **[Story]**: User story this task belongs to (US1=Entity Cache, US2=Usage Cache, US3=Extensibility)
- Note: US1 preserves existing entity cache with new naming; US2 adds usage cache; US3 demonstrates extensibility

---

## Phase 1: Setup

**Purpose**: Confirm existing project structure (no changes needed)

- [X] T001 Verify existing build infrastructure at `mcp/doc_server/build_helpers/embeddings.py` and `mcp/doc_server/build_script/build_mcp_db.py`

---

## Phase 2: Foundational (Blocking Prerequisite)

**Purpose**: Generalize cache persistence functions to accept type identifier parameter. This is required by all user stories.

**⚠️ CRITICAL**: No user story implementation can begin until this phase is complete.

- [X] T002 Add type identifier validation function `_validate_type_identifier()` in `mcp/doc_server/build_helpers/embeddings_loader.py` — validates alphanumeric + underscores + hyphens only; raises `ValueError` if invalid
- [X] T003 Refactor `save_embedding_cache()` in `mcp/doc_server/build_helpers/embeddings_loader.py` to accept `embedding_type: str` parameter and incorporate it into filename: `embed_cache_{model_slug}_{dimension}_{type}.pkl`
- [X] T004 Refactor `load_embedding_cache()` in `mcp/doc_server/build_helpers/embeddings_loader.py` to accept `embedding_type: str` parameter and locate type-specific cache file
- [X] T005 Add legacy file detection logic to `load_embedding_cache()` for entity type: if `embedding_type == "entity"` and new file not found, check for legacy file without suffix and log warning message
- [X] T006 Update logging in both functions to include `type=embedding_type` parameter in all log statements for cache hit/miss/corruption

**Checkpoint**: Foundation ready — user story implementation can begin

---

## Phase 3: User Story 1 — Entity Embedding Cache Persistence (Priority: P1) 🎯 MVP

**Goal**: Preserve existing entity embedding cache functionality with new consistent naming (`_entity` suffix). Entity embeddings continue to be cached and reused across builds.

**Independent Test**: Run two consecutive builds with same embedding configuration; verify second build reuses entity cache in under 10 seconds and cache file has `_entity` suffix.

### Implementation for User Story 1

- [X] T007 [US1] Update entity embedding cache save call in `mcp/doc_server/build_helpers/embeddings_loader.py` `generate_embeddings()` to pass `embedding_type="entity"` parameter
- [X] T008 [US1] Update entity embedding cache load call in `mcp/doc_server/build_helpers/embeddings_loader.py` `load_embeddings()` to pass `embedding_type="entity"` parameter
- [X] T009 [US1] Run build script and verify `embed_cache_{model}_{dim}_entity.pkl` file is created in artifacts directory
- [X] T010 [US1] Run build script again (without clearing cache) and verify entity embeddings are loaded from cache with log message "Loaded N embeddings from cache for type 'entity'"
- [X] T011 [US1] Verify entity embedding phase completes in under 10 seconds on cache hit

**Checkpoint**: US1 fully functional — entity embeddings cached with new naming, backward compatibility addressed via clear warning message for legacy files

---

## Phase 4: User Story 2 — Usage Embedding Cache Persistence (Priority: P2)

**Goal**: Add separate cache file for usage embeddings (`_usages` suffix) so entity and usage caches can be invalidated independently.

**Independent Test**: Modify entity data but not usage data, rebuild, verify usage cache is reused while entity cache is regenerated.

### Implementation for User Story 2

- [X] T012 [P] [US2] Update usage embedding cache save call in `mcp/doc_server/build_mcp_db.py` `populate_entity_usages()` to pass `embedding_type="usages"` parameter
- [X] T013 [P] [US2] Update usage embedding cache load call in `mcp/doc_server/build_mcp_db.py` `populate_entity_usages()` to pass `embedding_type="usages"` parameter
- [X] T014 [US2] Run build script and verify both `embed_cache_{model}_{dim}_entity.pkl` and `embed_cache_{model}_{dim}_usages.pkl` files are created in artifacts directory
- [X] T015 [US2] Delete entity cache file only, rebuild, and verify usage cache is reused (log: "Loaded N embeddings from cache for type 'usages'") while entity cache is regenerated
- [ ] T016 [US2] Delete usage cache file only, rebuild, and verify entity cache is reused (log: "Loaded N embeddings from cache for type 'entity'") while usage cache is regenerated (SKIPPED per user request)

**Checkpoint**: US2 fully functional — entity and usage embeddings cached independently in separate files

---

## Phase 5: User Story 3 — Extensible Cache Mechanism for Future Types (Priority: P3)

**Goal**: Demonstrate that the cache mechanism supports arbitrary new embedding types without code changes to save/load functions.

**Independent Test**: Add a hypothetical new embedding type ("subsystem") and verify cache mechanism handles it without modifying save/load logic.

### Implementation for User Story 3

- [X] T017 [P] [US3] Add unit test `test_save_load_with_custom_type` in `mcp/doc_server/tests/test_embeddings.py` — saves embeddings with `embedding_type="subsystem"`, verifies file created with correct name, loads and verifies data matches
- [X] T018 [P] [US3] Add unit test `test_multiple_types_independent` in `mcp/doc_server/tests/test_embeddings.py` — saves three types (entity, usages, subsystem), deletes one cache file, verifies other two still loadable
- [X] T019 [P] [US3] Add unit test `test_invalid_type_identifier_raises` in `mcp/doc_server/tests/test_embeddings.py` — attempts to save with invalid type identifier (e.g., "entity/usages", "type.invalid") and verifies `ValueError` is raised
- [X] T020 [US3] Add unit test `test_corrupted_cache_returns_none` in `mcp/doc_server/tests/test_embeddings.py` — creates a corrupted pickle file, attempts to load, verifies `None` returned and warning logged
- [X] T021 [US3] Run all unit tests: `cd mcp/doc_server && uv run pytest tests/test_embeddings.py -v` — verify all tests pass

**Checkpoint**: US3 demonstrated — cache mechanism is extensible without code changes; unit tests prove contract compliance

---

## Phase 6: Polish & Cross-Cutting Concerns

- [X] T022 [P] Run full build integration test: `cd mcp/doc_server && uv run python -m build_script.build_mcp_db` — verify both entity and usage cache files created, build completes successfully
- [X] T023 [P] Run build again without clearing cache and verify both cache files reused (embedding phase completes in under 10 seconds total)
- [X] T024 [P] Update quickstart.md if any API changes occurred during implementation (verify against contracts/cache-persistence.md)
- [X] T025 [P] Run `uv run mypy build_helpers/` to verify type checking passes with strict mode
- [X] T026 [P] Run `uv run ruff check mcp/doc_server/` and `uv run ruff format mcp/doc_server/` — verify zero violations

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — complete
- **Phase 2 (Foundational)**: Depends on Phase 1
- **Phase 3 (US1)**: Depends on Phase 2 (T002-T006 must be complete)
- **Phase 4 (US2)**: Depends on Phase 2; can run in parallel with Phase 3 if team capacity allows, but US1 should complete first for stability
- **Phase 5 (US3)**: Depends on Phase 2; can run in parallel with Phase 3/4
- **Phase 6 (Polish)**: Depends on Phases 3, 4, 5 complete

### User Story Dependencies

- **US1 (Phase 3)**: Requires foundational refactor (T002-T006) — No dependencies on other stories
- **US2 (Phase 4)**: Requires foundational refactor (T002-T006) — Independent of US1 but benefits from US1 validation
- **US3 (Phase 5)**: Requires foundational refactor (T002-T006) — Independent of US1/US2; primarily unit tests demonstrating extensibility

### Within Phase 2 (Foundational)

```
T002 (validation) → T003 (save refactor) → parallel with T004 (load refactor)
                                       ↘         ↗
                                        T005 (legacy detection)
                                             ↓
                                        T006 (logging)
```

### Within Phase 3 (US1)

```
T007 (save call update) → parallel with T008 (load call update)
                    ↘              ↗
                     T009 (verify file created)
                            ↓
                     T010 (verify cache reuse)
                            ↓
                     T011 (verify performance)
```

### Within Phase 4 (US2)

```
T012 (save call) → parallel with T013 (load call)
              ↘           ↗
               T014 (verify both files)
                       ↓
          T015 (test entity invalidation)
                       ↓
          T016 (test usage invalidation)
```

### Within Phase 5 (US3)

```
T017 [P] (custom type test)
T018 [P] (multiple types test)
T019 [P] (invalid type test)
T020 [P] (corruption test)
    ↘    ↓    ↓    ↙
      T021 (run all tests)
```

---

## Parallel Opportunities

### Phase 2 parallelism

```bash
# After T002 completes, T003 and T004 can run in parallel:
Task T003: "Refactor save_embedding_cache() in embeddings.py"
Task T004: "Refactor load_embedding_cache() in embeddings.py"
# Then T005, then T006
```

### Phase 3 parallelism

```bash
# T007 and T008 can run in parallel (different call sites in same file, but distinct operations):
Task T007: "Update entity save call in build_mcp_db.py"
Task T008: "Update entity load call in build_mcp_db.py"
```

### Phase 4 parallelism

```bash
# T012 and T013 can run in parallel:
Task T012: "Update usage save call in build_mcp_db.py"
Task T013: "Update usage load call in build_mcp_db.py"
```

### Phase 5 parallelism

```bash
# All test tasks T017-T020 can run in parallel (different test functions):
Task T017: "test_save_load_with_custom_type in test_embeddings.py"
Task T018: "test_multiple_types_independent in test_embeddings.py"
Task T019: "test_invalid_type_identifier_raises in test_embeddings.py"
Task T020: "test_corrupted_cache_returns_none in test_embeddings.py"
# All tests run together with T021
```

### Phase 6 parallelism

```bash
# All polish tasks can run in parallel:
Task T022: "Run full build integration test"
Task T023: "Run build with cache"
Task T024: "Update quickstart.md"
Task T025: "Run mypy type checking"
Task T026: "Run ruff linting"
```

---

## Implementation Strategy

### MVP First (US1 Only)

1. Complete Phase 1: Setup (already done)
2. Complete Phase 2: Foundational (T002-T006) — CRITICAL blocking work
3. Complete Phase 3: User Story 1 (T007-T011)
4. **STOP and VALIDATE**: Run build twice, verify entity cache with `_entity` suffix works
5. User Story 1 is the MVP — entity embeddings cached with new consistent naming

### Incremental Delivery

1. Phase 1 + 2 → Foundation ready (generalized cache mechanism exists)
2. Phase 3 (US1) → Entity embeddings work with new naming (MVP!)
3. Phase 4 (US2) → Usage embeddings cached independently
4. Phase 5 (US3) → Extensibility demonstrated via unit tests
5. Phase 6 → Full validation and polish

### Parallel Team Strategy

With multiple developers after Phase 2 completes:

1. Team completes Phase 1 + 2 together (foundational work)
2. Once Phase 2 done:
   - Developer A: Phase 3 (US1 — entity cache)
   - Developer B: Phase 4 (US2 — usage cache)
   - Developer C: Phase 5 (US3 — unit tests)
3. Phase 6: Any team member can run final validation

---

## Audit Remediation

> Generated by `/speckit.audit` on 2026-03-20. Address before merging to main.

- [X] T027 [AR] Fix stale docstring in `load_embeddings()` at `mcp/doc_server/build_helpers/embeddings_loader.py:190-193` — remove "Raises: RuntimeError" claim; function returns None on corruption per FR-008
- [X] T028 [AR] Move `from typing import cast` import to module level in `mcp/doc_server/build_helpers/embeddings_loader.py:274` — relocate to top imports section with other typing imports
- [X] T029 [AR] Implement incremental cache synchronization in `populate_entity_usages()` at `mcp/doc_server/build_mcp_db.py:228-265` — after loading cache, compute missing keys (need embeddings) and stale keys (in cache but not needed), generate embeddings for missing keys only, merge with cached embeddings, prune stale keys, save updated cache with logging of sync actions per FR-012

---

## Schema-Agnostic Generalization (FR-013)

> Refactor to complete the original spec requirement: "don't create a new code path, let's generalize and reuse"
> Architecture: Layer 1 (cache ops), Layer 2 (entity domain logic), Layer 3 (orchestration), Layer 4 (provider abstraction)

### Phase 1: Create Generic Cache Sync Function (Layer 1)

- [X] T030 Create `sync_embeddings_cache()` function in `mcp/doc_server/build_helpers/embeddings_loader.py` with signature: `sync_embeddings_cache(artifacts_path: Path, model_slug: str, dimension: int, embedding_type: str, current_keys: list[str | tuple[str, ...]], texts_by_key: dict[str | tuple[str, ...], str], provider: EmbeddingProvider) -> dict[str | tuple[str, ...], list[float]]`. Implementation: call `load_embedding_cache()`, compute `missing_keys = set(current_keys) - set(cached.keys())` and `stale_keys = set(cached.keys()) - set(current_keys)`, generate embeddings for missing keys only via `provider.embed_documents_sync()`, merge with cached, prune stale, call `save_embedding_cache()`, return complete dict. Log sync actions. Fully schema-agnostic per FR-013.

### Phase 2: Move Entity Text Generation to Domain Layer (Layer 2)

- [X] T031 Move `build_minimal_embed_text()` from `mcp/doc_server/build_helpers/embeddings_loader.py` to `mcp/doc_server/build_helpers/entity_processor.py` (no signature changes, just relocation)
- [X] T032 Create `build_entity_embed_texts(merged_entities: list[MergedEntity]) -> dict[str, str]` in `mcp/doc_server/build_helpers/entity_processor.py` that iterates merged_entities, calls `.to_doxygen()` for doc-rich entities, calls `build_minimal_embed_text()` for doc-less entities, returns `{entity_id: text}` mapping. This consolidates all entity text generation logic in the domain layer.

### Phase 3: Remove Entity-Specific Wrappers from Cache Layer

- [X] T033 Remove entity-specific wrapper functions from `mcp/doc_server/build_helpers/embeddings_loader.py`: `load_embeddings()`, `generate_embeddings()`, `attach_embeddings()`, `get_embed_cache_path()`. Keep only: `_validate_type_identifier()`, `save_embedding_cache()`, `load_embedding_cache()`, `sync_embeddings_cache()`. The cache layer is now purely generic.

### Phase 4: Update Entity Embedding Call Site (Layer 3 Orchestration)

- [X] T034 Refactor entity embedding logic in `mcp/doc_server/build_mcp_db.py` `main()` function (lines 463-473) to orchestrate layers: import `build_entity_embed_texts` from `entity_processor`, build `entity_keys = [m.entity_id for m in merged_entities]`, call `texts_by_key = build_entity_embed_texts(merged_entities)`, call `embeddings = sync_embeddings_cache(artifacts_path, model_slug, dimension, "entity", entity_keys, texts_by_key, provider)`, inline attach loop `for m in merged_entities: m.embedding = embeddings.get(m.entity_id)`. Remove old `load_embeddings()`, `generate_embeddings()`, `attach_embeddings()` calls.

### Phase 5: Update Usage Embedding Call Site (Layer 3 Orchestration)

- [X] T035 Refactor usage embedding logic in `mcp/doc_server/build_mcp_db.py` `populate_entity_usages()` (lines 226-289) to use generic `sync_embeddings_cache()`: build `usage_keys` list and `texts_by_key = {key: row.description for key, row in ...}`, call `embeddings = sync_embeddings_cache(...)`, apply results `for idx, key in enumerate(usage_keys): rows[idx].embedding = embeddings[key]`. Remove duplicated inline sync logic.

### Phase 6: Update Tests

- [X] T036 Update `mcp/doc_server/tests/test_embeddings.py`: move entity-specific tests (TestBuildMinimalEmbedTextFunction, TestBuildMinimalEmbedTextFile, TestBuildMinimalEmbedTextEmptySkips, TestGenerateEmbeddingsIncludesDocLess) to new file `tests/test_entity_processor.py` since `build_minimal_embed_text` and entity text logic now live in `entity_processor.py`. Update imports and test the new `build_entity_embed_texts()` function.
- [X] T037 Add test coverage for generic `sync_embeddings_cache()` in `tests/test_embeddings.py`: test with string keys (entity-like), tuple keys (usage-like), verify incremental sync behavior (cache miss → generate all, partial cache → generate missing only, stale keys → prune), verify logging of sync actions.

### Phase 7: Validation

- [ ] T038 Run full build script twice and verify entity embeddings use incremental sync: first build should log "Cache synchronized" with added count matching entity count, second build (no data changes) should log "Cache up to date", third build after adding/removing entities should log added/pruned counts. No more "Generating embeddings from merged entities" on warm builds.
- [X] T039 Run full test suite: `uv run pytest tests/ -v` — verify all tests pass including moved entity_processor tests
- [X] T040 Run linting and type checking: `uv run ruff check .` and `uv run mypy build_helpers/ build_mcp_db.py tests/` — verify zero violations

---

## Notes

- Entity embeddings transition from no suffix to `_entity` suffix (manual migration required for legacy files)
- Usage embeddings added as new `_usages` cache (no migration needed)
- Extensibility is design property, not runtime feature — demonstrated via US3 tests
- Each cache file is independent: deleting one does not affect others
- Cache invalidation is manual (delete file) or automatic (model config changes)
- No concurrent build support: assume sequential builds per artifacts directory
