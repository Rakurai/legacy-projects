# Tasks: Local FastEmbed Provider

**Input**: Design documents from `specs/004-local-fastembed-provider/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/embedding-provider.md, quickstart.md

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3, US4)
- All paths relative to `.ai/mcp/doc_server/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Add dependency, extend configuration, update build validation

- [X] T001 Add `fastembed>=0.4.0` to dependencies in `pyproject.toml` and run `uv lock`
- [X] T002 [P] Add embedding provider fields to `server/config.py`: `embedding_provider` (Literal["local", "hosted"] | None), `embedding_local_model` (str, default "BAAI/bge-base-en-v1.5"), `embedding_dimension` (int, default 768); add `embed_cache_filename` property; update `embedding_enabled` property to check `embedding_provider is not None`
- [X] T003 [P] Update `.env.example` with new config vars: `EMBEDDING_PROVIDER`, `EMBEDDING_DIMENSION`, `EMBEDDING_LOCAL_MODEL`; comment out old-style standalone `EMBEDDING_BASE_URL`/`EMBEDDING_API_KEY`/`EMBEDDING_MODEL` with notes on when they apply

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core abstractions that all user stories depend on — provider protocol, text construction, dynamic schema

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Create `server/embedding.py` with `EmbeddingProvider` Protocol defining: `dimension` property, `embed_query(text)` async, `embed_documents(texts)` async, `embed_query_sync(text)`, `embed_documents_sync(texts)`
- [X] T005 [P] Implement `LocalEmbeddingProvider` class in `server/embedding.py`: wraps `fastembed.TextEmbedding`, sync methods call ONNX directly, async methods use `asyncio.to_thread()`, `dimension` probed from model on init
- [X] T006 [P] Implement `HostedEmbeddingProvider` class in `server/embedding.py`: wraps `openai.OpenAI` (sync) and `openai.AsyncOpenAI` (async), passes model/encoding_format through, `dimension` from config
- [X] T007 Implement `create_provider(config)` factory in `server/embedding.py`: returns Local/Hosted/None based on `config.embedding_provider`; validates `provider.dimension == config.embedding_dimension` and raises on mismatch
- [X] T008 [P] Create `build_helpers/embed_text.py` with `build_embed_text(doc: dict[str, Any]) -> str`: reconstruct Doxygen-formatted docstring from raw doc_db entry fields (kind, name, definition, brief, details, params, returns, notes, rationale); always returns text (every doc_db entry is embeddable)
- [X] T009 [P] Change `server/db_models.py` Entity embedding column from `Vector(4096)` to `Vector(_EMBEDDING_DIM)` where `_EMBEDDING_DIM = int(os.environ.get("EMBEDDING_DIMENSION", "768"))`; update description string

**Checkpoint**: Provider abstraction, text builder, and dynamic schema are ready. All downstream tasks can now proceed.

---

## Phase 3: User Story 1 — Zero-Dependency Database Build (Priority: P1) 🎯 MVP

**Goal**: Build script generates embeddings locally when no artifact exists, saves artifact for reuse, loads into DB. No external service needed.

**Independent Test**: Run `build_mcp_db.py` with `EMBEDDING_PROVIDER=local` and no artifact file. Verify artifact created, entities get embeddings, DB populated.

### Implementation for User Story 1

- [X] T010 [US1] Rewrite `build_helpers/embeddings_loader.py`: add `get_embed_cache_path(artifacts_dir, config)` returning `artifacts_dir / config.embed_cache_filename`; rewrite `load_embeddings(artifacts_dir, config)` to load from config-derived filename (return None if file missing; catch `pickle.UnpicklingError`/`EOFError` and raise with clear "corrupt artifact" message per edge case EC-002); keep `attach_embeddings()` unchanged
- [X] T011 [US1] Add `generate_embeddings(artifacts_dir, provider, config)` to `build_helpers/embeddings_loader.py`: reads `doc_db.json` directly, calls `build_embed_text()` for each entry (using `mid` as entity_id key), calls `provider.embed_documents_sync(texts)`, writes pickle to temp file then renames (atomic save per concurrent-build edge case), returns dict[str, list[float]]
- [X] T012 [US1] Remove `embeddings_cache.pkl` from the `required_files` list in `build_helpers/loaders.py` `validate_artifacts()` function (FR-010)
- [X] T013 [US1] Update Stage 9 in `build_mcp_db.py`: instantiate provider via `create_provider(config)`; try `load_embeddings()`; if None and provider exists → `generate_embeddings()`; if None and no provider → log warning, use empty dict; pass result to `attach_embeddings()`

**Checkpoint**: `build_mcp_db.py` works end-to-end with `EMBEDDING_PROVIDER=local`. Artifact is generated on first run, loaded on subsequent runs. No hosted service or pre-built artifact required.

---

## Phase 4: User Story 2 — Semantic Search with Local Embeddings (Priority: P1)

**Goal**: Server uses local provider for query-time embedding, enabling hybrid semantic+keyword search.

**Independent Test**: Start server with `EMBEDDING_PROVIDER=local`, issue search query, verify `search_mode: "hybrid"` (not `"keyword_fallback"`).

### Implementation for User Story 2

- [X] T014 [US2] Update `server/lifespan.py`: replace `AsyncOpenAI` client setup with `create_provider(config)` call; change `LifespanContext` TypedDict to use `embedding_provider: EmbeddingProvider | None` instead of `embedding_client`/`embedding_model`; remove `from openai import AsyncOpenAI` import; add dimension validation log on success
- [X] T015 [US2] Update `server/search.py` `hybrid_search()`: change signature from `(embedding_client=None, embedding_model="")` to `(embedding_provider=None)`; replace `embedding_client.embeddings.create()` call with `await embedding_provider.embed_query(query)`; keep fallback logic unchanged
- [X] T016 [P] [US2] Update `server/resolver.py` `resolve_entity()` and `_resolve_by_semantic()`: change signature from `(embedding_client, embedding_model)` to `(embedding_provider)`; replace OpenAI API call with `await embedding_provider.embed_query(query)`
- [X] T017 [P] [US2] Update `server/tools/search.py`: change `lc["embedding_client"]`/`lc["embedding_model"]` to `lc["embedding_provider"]` in `hybrid_search()` call
- [X] T018 [P] [US2] Update `server/tools/entity.py`: change `lc["embedding_client"]`/`lc["embedding_model"]` to `lc["embedding_provider"]` in `resolve_entity()` call
- [X] T019 [US2] Update `server/server.py`: change `lc["embedding_client"] is not None` to `lc["embedding_provider"] is not None` for the `embedding_available` flag

**Checkpoint**: Server runs with `EMBEDDING_PROVIDER=local`. Semantic search returns hybrid results. Keyword fallback still works when provider is None or errors occur.

---

## Phase 5: User Story 3 — Hosted Provider Remains Available (Priority: P2)

**Goal**: Existing hosted embedding workflow still works — both build-time generation and runtime query embedding.

**Independent Test**: Configure `EMBEDDING_PROVIDER=hosted` with a running OpenAI-compatible endpoint, build database, start server, verify hybrid search.

### Implementation for User Story 3

- [X] T020 [US3] Verify `HostedEmbeddingProvider` (T006) works end-to-end: confirm `embed_query` async path uses `AsyncOpenAI`, `embed_documents_sync` uses sync `OpenAI` client, model name and encoding_format pass through correctly
- [X] T021 [US3] Verify build pipeline generates artifact via hosted provider when `EMBEDDING_PROVIDER=hosted` and no artifact exists — confirm artifact filename uses hosted model slug and dimension
- [X] T022 [US3] Verify server startup with `EMBEDDING_PROVIDER=hosted` creates `HostedEmbeddingProvider` and semantic search returns hybrid results

**Checkpoint**: Hosted path works identically to before but through the new `EmbeddingProvider` abstraction. Config is backward-compatible.

---

## Phase 6: User Story 4 — Switching Between Providers (Priority: P3)

**Goal**: Developer can change provider config and rebuild cleanly. Different artifacts coexist.

**Independent Test**: Build with hosted, switch to local, rebuild. Verify new artifact generated, schema dimension correct, search works.

### Implementation for User Story 4

- [X] T023 [US4] Verify that changing `EMBEDDING_PROVIDER` from "hosted" to "local" (and updating dimension/model) causes build to generate a new artifact (different filename) while preserving the old one
- [X] T024 [US4] Verify that `db_models.py` `Vector(dim)` reads the updated `EMBEDDING_DIMENSION` env var correctly when the schema is dropped and recreated

**Checkpoint**: Provider switching works cleanly with config-only changes.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Tests, documentation, cleanup

- [X] T025 [P] Create `tests/test_embed_text.py`: test `build_embed_text()` with function entity (full doc), entity with no doc (skip rule), entity with partial fields; verify Doxygen tag format matches original `to_doxygen()` output shape
- [X] T026 [P] Create `tests/test_embedding_provider.py`: test `LocalEmbeddingProvider` dimension property + `embed_query_sync` returns correct-length vector; test `create_provider()` factory with local/hosted/None configs; test dimension mismatch raises error
- [X] T027 [P] Remove `openai` import from `server/lifespan.py` if no longer used; verify `openai` remains in `pyproject.toml` dependencies (still needed by `HostedEmbeddingProvider`)
- [ ] T028 Run `quickstart.md` validation: follow the local setup steps end-to-end on a clean environment, verify all commands succeed and search returns hybrid results

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on T001 (fastembed installed) and T002 (config fields) — BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Foundational phase (T004-T009)
- **US2 (Phase 4)**: Depends on Foundational phase (T004-T009); code changes can be authored in parallel with US1 (different files), but US2 validation requires a built database with embeddings (US1 output)
- **US3 (Phase 5)**: Depends on US2 completion (lifespan/search refactored to use provider)
- **US4 (Phase 6)**: Depends on US1 + US2 completion
- **Polish (Phase 7)**: Depends on all user stories complete

### Within-Phase Parallel Opportunities

**Phase 1**: T002 and T003 can run in parallel (different files)

**Phase 2**: After T004 (Protocol definition):
- T005, T006, T008, T009 can all run in parallel (different files)
- T007 depends on T005, T006 (needs both implementations to validate)

**Phase 3**: T010, T011 are sequential (same file); T012 is parallel (different file); T013 depends on T010+T011

**Phase 4**: T015, T016, T017, T018 can run in parallel after T014 (different files, but all consume the new LifespanContext shape)

### Parallel Example: Foundational Phase

```
T004 (Protocol) ──→ T005 (LocalProvider)  ──→ T007 (Factory + validation)
                ──→ T006 (HostedProvider) ──→
                ──→ T008 (embed_text.py)       [independent]
                ──→ T009 (db_models.py)        [independent]
```

### Parallel Example: US2 (after T014 lands)

```
T014 (lifespan) ──→ T015 (search.py)
                ──→ T016 (resolver.py)    [parallel, different files]
                ──→ T017 (tools/search)   [parallel, different files]
                ──→ T018 (tools/entity)   [parallel, different files]
                ──→ T019 (server.py)
```

---

## Implementation Strategy

### MVP First (US1 + US2)

1. Complete Phase 1: Setup (T001-T003)
2. Complete Phase 2: Foundational (T004-T009)
3. Complete Phase 3: US1 — Build pipeline works locally (T010-T013)
4. Complete Phase 4: US2 — Server search works locally (T014-T019)
5. **STOP and VALIDATE**: Build with `EMBEDDING_PROVIDER=local`, start server, run search queries
6. This delivers SC-001 (zero external dependencies) and SC-002 (relevant search results)

### Incremental Delivery

1. Setup + Foundational → Provider abstraction ready
2. US1 → Build pipeline self-contained → **Validate**
3. US2 → Server search works → **Validate** (MVP complete!)
4. US3 → Hosted path verified → **Validate** (backward compat confirmed)
5. US4 → Switching verified → **Validate** (flexibility confirmed)
6. Polish → Tests + cleanup → **Done**
