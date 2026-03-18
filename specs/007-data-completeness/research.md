# Research: MCP Build Pipeline — Data Completeness Fixes

**Feature**: 007-data-completeness
**Date**: 2026-03-18

## R1: Source Code Extraction — Current Failure Mode

**Question**: Why does `extract_source_code()` produce zero results, and what's the correct fix?

**Findings**:
- `extract_source_code()` at [entity_processor.py#L210-L257](../../../mcp/doc_server/build_helpers/entity_processor.py) resolves paths via `project_root / entity.body.fn`
- File-not-found is a **silent skip** — guarded by `.exists()` checks at L229, L239 with no warning
- Only actual read exceptions increment `failed_count` (L247); missing files are never counted
- The function logs an end summary (`extracted=N, failed=N`) but `failed` understates the problem because missing files aren't counted as failures
- `config.project_root` is a required `Path` field (no default) — set via `PROJECT_ROOT` env var in `.env`
- The root cause is that `PROJECT_ROOT` must point to the C++ source tree root, but the current `.env` likely points to the Python repo root (`legacy-projects/`) not the C++ repo

**Decision**: Add a post-extraction validation check. After the loop, count entities that have body locations but received no source text. If this count equals the total body-located entity count (zero successes), raise a `BuildError` with the configured path. Log individual missing files as warnings (not silently skip).

**Alternatives considered**:
- Pre-validate `PROJECT_ROOT` by checking for known sentinel files (e.g., `src/fight.cc`) — rejected because it couples the build to specific filenames
- Make every missing file a build error — rejected because some entities may reference generated or deleted files legitimately

---

## R2: Minimal Embedding Text Format

**Question**: What structured text format should doc-less entities use for embedding generation?

**Findings**:
- `Document.to_doxygen()` at [doc_db.py#L47-L100](../../../packages/legacy_common/legacy_common/doc_db.py) produces a Doxygen comment block:
  ```
  /**
   * @fn void damage(Character *ch, ...)
   * @brief Apply damage to a character...
   * @details ...
   * @note ...
   * @param ch The character
   * @return void
   */
  ```
- The embedding model (BAAI/bge-base-en-v1.5) is trained on general English + code documentation
- For doc-less entities, we have: `kind` (function/variable/class/file/dir/namespace), `name`, `signature` (may be same as name), `file_path`

**Decision**: Use a minimal Doxygen-like format matching the existing pattern:
```
/**
 * @{tag} {signature_or_name}
 *
 * @file {file_path}
 */
```
Where `tag` maps from `kind` using the same mapping as `Document.to_doxygen()`: function→`@fn`, variable→`@var`, class→`@class`, struct→`@struct`, file→`@file`, dir→`@dir`, namespace→`@namespace`, define→`@def`, group→`@defgroup`.

For structural compounds (file/dir/namespace), use:
```
/**
 * @file src/fight.cc
 */
```

**Rationale**: Matching the Doxygen format ensures the embedding space is consistent — doc-rich and doc-less entities are embedded in comparable textual structures, maximizing semantic similarity quality.

**Alternatives considered**:
- Plain text (`"function damage in src/fight.cc"`) — rejected because it diverges from the training-text distribution of the existing embeddings
- Including source code in the embedding text — rejected because source text is large and would dominate the embedding, losing the documentation-oriented signal

---

## R3: Params Normalization — Where to Apply

**Question**: Should params be normalized at the `Document` source level, at `MergedEntity` level, or at DB insertion?

**Findings**:
- `Document.params` is typed `Optional[Dict[str, str]]` with default `None` at [doc_db.py#L22](../../../packages/legacy_common/legacy_common/doc_db.py)
- In serialized `generated_docs/` JSON, some entries have `"params": {}` which deserializes to `{}` (not `None`)
- `build_mcp_db.py` writes: `params=merged.doc.params if merged.doc else None` at [L134](../../../mcp/doc_server/build_mcp_db.py)
- The `Entity` SQLModel column is `sa_column=Column(JSONB)` — accepts both `{}` and `None`

**Decision**: Normalize at DB insertion in `populate_entities()`. Change the params line to:
```python
params=merged.doc.params if merged.doc and merged.doc.params else None,
```
This catches both `None` and `{}` (falsy dict). Applied once at the single insertion point — no upstream changes needed.

**Rationale**: Normalizing at insertion is the narrowest possible change. It doesn't alter `Document` or `MergedEntity` semantics, only the DB representation. If `Document` later starts using `{}` vs `None` semantically, the normalization is localized.

**Alternatives considered**:
- Normalize in `Document.__init__` or a Pydantic validator — rejected because it changes `legacy_common` behavior for all consumers
- Normalize in `MergedEntity` construction — rejected because it adds a concern to merge logic that belongs to DB insertion

---

## R4: Embedding Generation — Batch Architecture

**Question**: How should doc-less entities be embedded alongside doc-rich entities?

**Findings**:
- `generate_embeddings()` at [embeddings_loader.py#L77-L126](../../../mcp/doc_server/build_helpers/embeddings_loader.py) currently builds a single list of `(entity_id, doc)` pairs filtered by `m.doc is not None`
- All texts are embedded in one call: `provider.embed_documents_sync(texts)` — no chunking
- The embedding cache is keyed by entity_id and persisted as a pickle artifact
- Adding ~248 more entities to the batch increases total from ~5,057 to ~5,305 — negligible performance impact

**Decision**: Extend `generate_embeddings()` to build two lists: (1) doc-rich entities using `doc.to_doxygen()` and (2) doc-less entities using a minimal text builder function. Concatenate both lists and embed in a single batch. Log counts for both categories.

**Rationale**: Single batch is simpler and fast enough. Separating into two categories allows accurate logging per FR-009.

**Alternatives considered**:
- Two separate embedding calls (doc-rich then doc-less) — rejected because it doubles provider invocations and complicates cache management
- A separate post-processing step — rejected because it would require a second cache file or special-casing in the main cache

---

## R5: Test Strategy

**Question**: What tests are needed for the new behavior?

**Findings**:
- Existing tests are contract tests that don't require a live DB (per CLAUDE.md)
- 22 test files in `mcp/doc_server/tests/`
- No existing tests for `extract_source_code()` or `generate_embeddings()` — these are build-time functions
- Test fixtures use mock entities built from Pydantic models

**Decision**: Add two test files:
1. `test_entity_processor.py` — Test `extract_source_code()` behavior:
   - Happy path: valid project_root with source files → extraction succeeds
   - Zero extraction: project_root with no matching files → raises `BuildError`
   - Partial extraction: some files present, some missing → warnings logged, build continues
2. `test_embeddings.py` — Test minimal embedding text generation:
   - Doc-rich entity → uses `doc.to_doxygen()` (existing behavior)
   - Doc-less function → minimal Doxygen format with `@fn` + signature
   - Doc-less file compound → minimal format with `@file` + path
   - All-empty entity (no name, no sig, no kind) → skipped

Use `tmp_path` fixture for source tree simulation. Mock the embedding provider for embedding tests.

**Rationale**: Happy-path contract tests per constitution. Focus on the new fail-fast behavior (the main bug being fixed) and the new minimal embedding format (new code path).
