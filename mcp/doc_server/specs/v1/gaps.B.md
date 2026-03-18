# Phase B — Data Completeness

> Ensure every field the DB schema declares actually gets populated from the richest available source.
> Depends on Phase A (legacy_common imports in place).
>
> **Phase A dependency resolved** — spec 006-legacy-common-integration completed.
> **Phase B RESOLVED** — spec 007-data-completeness completed. Source extraction fail-fast, params normalization, and minimal embeddings for doc-less entities all implemented.
>
> Items: gaps.md §15, §12, §9, §13, §14

---

## 1. `doc_db.json` Is a Stale Snapshot — Switch to `generated_docs/` (gaps §15)

> **Status: RESOLVED** by spec 006-legacy-common-integration. Build pipeline now reads from `generated_docs/*.json` via `legacy_common.doc_db.DocumentDB`. `doc_db.json` removed from required artifacts.

**The single most impactful data issue** — half the documentation is being dropped.

### The problem

`artifacts/doc_db.json` is a flat serialization of the per-compound `generated_docs/` files. It was serialized at an **early pipeline stage** — after `extracted_summary` and `generated_summary` passes, but **before** the `refined_summary` and `refined_usage` passes that added briefs, notes, and rationale to most entities. It was never regenerated.

The MCP build pipeline reads `doc_db.json`. The actual source of truth is `generated_docs/` (now at `projects/doc_gen/context/internal/generated_docs/`).

### Data audit comparison

| Field | `generated_docs/` (475 files, 5,295 docs) | `doc_db.json` (5,307 entries) | Loss |
|-------|-------------------------------------------|-------------------------------|------|
| **brief** | **4,946 (93.4%)** | 2,272 (42.8%) | **2,674 briefs dropped** |
| **details** | **4,953 (93.5%)** | ~2,381 (44.9%) | ~2,572 dropped |
| **notes** | **4,407 (83.2%)** | 0 (field absent) | **all dropped** |
| **rationale** | **4,387 (82.9%)** | 0 (field absent) | **all dropped** |
| **usages** | **2,889 (54.6%)** | 0 (field absent) | **all dropped** |
| **state** | **5,295 (100%)** | 0 (field absent) | **all dropped** |
| throws | 676 (12.8%) | 0 (field absent) | all dropped |
| tparams | 20 (0.4%) | 0 (field absent) | all dropped |
| params | 2,062 (38.9%) | 1,799 | ~263 dropped |
| returns | 2,346 (44.3%) | 1,967 | ~379 dropped |

### State distribution in generated_docs

| State | Count | Notes |
|-------|-------|-------|
| `refined_summary` | 4,447 | Bulk of docs — these have briefs, notes, rationale |
| `extracted_summary` | 732 | Doxygen-extracted only |
| `generated_summary` | 94 | LLM-generated, not yet refined |
| `refined_usage` | 22 | Refined with usage context |

### Key overlap analysis

doc_db.json uses `"('compound_id', 'signature')"` tuple-string keys; generated_docs uses `compound_id` file → `member_key` dict keys.

| Set | Count |
|-----|-------|
| Overlapping keys | 4,528 |
| In doc_db.json only | 779 |
| In generated_docs only | 767 |

Among the 4,528 overlapping entries:
- Both have brief: **2,165**
- Only generated_docs has brief: **2,359** (state: `refined_summary`) — added during refinement passes after doc_db.json was serialized
- Only doc_db.json has brief: **0**
- Neither: **4**

### Action

1. **Configure `generated_docs/` path**: Add `GENERATED_DOCS_DIR` to `mcp/doc_server/.env` / `config.py`, pointing to `projects/doc_gen/context/internal/generated_docs/`
2. **Update the build pipeline** to load documents via `legacy_common.doc_db.DocumentDB` (per-compound files) instead of the flat `doc_db.json`
3. **Remove `doc_db.json`** from the required artifacts list in spec, build validation, and `loaders.py`
4. **Update `embeddings_loader.py`**: use `Document.to_doxygen()` instead of `build_embed_text()` on raw dicts
5. **Update `entity_processor.py`**: use `legacy_common.doc_db.Document` fields (which include notes, rationale, usages, state)
6. **Verify signature matching**: the 779 doc_db-only and 767 generated_docs-only keys suggest a key-format mismatch. After switching loaders, confirm the join between entity IDs and doc keys produces ≥95% match rate
7. **Delete `artifacts/doc_db.json`** once the build pipeline no longer references it

### File inventory

| File | Change |
|------|--------|
| `server/config.py` | Add `GENERATED_DOCS_DIR` setting |
| `build_helpers/loaders.py` | Replace `load_documents()` — use `legacy_common.doc_db.DocumentDB` pointed at configured dir |
| `build_helpers/entity_processor.py` | Accept `legacy_common.doc_db.Document`, map new fields (notes, rationale, usages, state) |
| `build_helpers/embeddings_loader.py` | Use `Document.to_doxygen()` instead of raw-dict `build_embed_text()` |
| `build_mcp_db.py` | Update `load_documents()` call; pass generated_docs path from config |
| `mcp/doc_server/.env` | Add `GENERATED_DOCS_DIR=...` |

---

## 2. `notes`, `rationale`, `usages` — Fix Data Source (gaps §12)

> **Status: RESOLVED** by spec 006-legacy-common-integration. Data source switched to `generated_docs/`; these fields are now populated from `legacy_common.doc_db.Document`.

**Upgraded from P2 to P0** — core documentation fields exist in source but were dropped during serialization.

| Column | MCP DB state | `doc_db.json` state | `generated_docs/` state | Root cause |
|--------|----------|---------------------|------------------------|------------|
| `notes` | 0/5,305 | 0 (field absent) | **4,407 / 5,295 (83.2%)** | doc_db.json is stale; doesn't include this field |
| `rationale` | 0/5,305 | 0 (field absent) | **4,387 / 5,295 (82.9%)** | Same |
| `usages` | 0/5,305 | 0 (field absent) | **2,889 / 5,295 (54.6%)** | Same |

**Decision:** Keep these columns. Resolves automatically when §1 switches the data source.

**Action:**
- Verify after §1 that entity_processor properly maps these fields to DB columns
- Check `Document.to_doxygen()`: notes and rationale should contribute to embeddings (they already do in the legacy_common version)

---

## 3. Source Code Extraction — Broken Pipeline (gaps §9)

> **Status: RESOLVED** by spec 007-data-completeness. `extract_source_code()` now raises `BuildError` on zero extraction (PROJECT_ROOT misconfigured), logs warnings for individual missing files, logs a structured extraction summary, raises `BuildError` on invalid line ranges (stale code graph), and narrows exception handling to `(OSError, UnicodeDecodeError)`. `.env` `PROJECT_ROOT` now points to the C++ source tree.

`source_text` and `definition_text` are 0/5,305 populated. The build pipeline calls `extract_source_code(merged_entities, config.project_root)` but fails silently when the C++ source tree isn't at the configured `project_root`. Since the spec-creating agent's primary workflow involves reading source code (`get_source_code` tool, `get_entity(include_code=true)`), this is a critical gap.

**Action:**
- ~~Ensure `PROJECT_ROOT` in `.env` points to the legacy C++ source tree~~ Done
- ~~Make `extract_source_code()` fail the build (not silently skip) if the source tree is missing or if extraction yields zero results~~ Done — `BuildError` raised
- ~~The build should log a clear error: "PROJECT_ROOT={path} does not contain expected source files"~~ Done
- ~~Verify that entity body locations (`body.fn`, `body.line`, `body.end_line`) from `code_graph.json` resolve correctly against the source tree~~ Done

---

## 4. `params` — Normalize Empty Dicts to NULL (gaps §13)

> **Status: RESOLVED** by spec 007-data-completeness. Params normalization applied in `build_mcp_db.py` (`params=merged.doc.params if merged.doc and merged.doc.params else None`) and `db_models.py` (`JSONB(none_as_null=True)`).

`params` shows 5,055 "non-empty" in the DB, but `doc_db.json` has only 1,799 docs with actual param content. The remaining 3,256 are either `{}` (947 in doc_db) or non-function entities where the build pipeline inserts `{}` because `merged.doc.params` defaults to empty dict.

**Action:**
- ~~In the build pipeline, write `NULL` for `params` when the value is `None` or `{}`~~ Done
- ~~This makes queries like `WHERE params IS NOT NULL` actually meaningful~~ Done

---

## 5. Embedding Coverage (gaps §14)

> **Status: RESOLVED** by spec 007-data-completeness. Doc-less entities now receive minimal Doxygen-formatted embeddings from `build_minimal_embed_text()` using `kind + name + signature + file_path`. Structural compounds (file/dir/namespace) are included — higher-level documentation references them. Embedding generation summary is logged. Coverage target ≥95%.

789/5,305 entities have no embedding. Current breakdown:

| Kind | Missing | Total | Cause |
|------|---------|-------|-------|
| file | 217 | 217 | Structural compounds — no doc_db entry |
| dir | 20 | 20 | Same |
| namespace | 11 | 11 | Same |
| function | 390 | 2,365 | Not in doc_db (no LLM-generated docs) |
| variable | 139 | 2,369 | Same |
| define | 7 | 82 | Same |
| group | 5 | 85 | Same |

**Update (data audit 2025-07):** The generated_docs source has **4,946 briefs (93.4%)** vs doc_db.json's 2,272 (42.8%). Once §1 switches the build to generated_docs, most of the 390+139 missing entities will gain embeddings. The remaining gap will be ~248 structural compounds (file/dir/namespace) which never have doc entries.

**Action:**
- ~~**Primary fix**: §1 (switch to generated_docs) provides embeddings for the vast majority of entities~~ Done (spec 006)
- ~~For functions/variables still without doc entries after §1: generate a minimal embedding from `signature + kind + name` so they're at least discoverable via semantic search~~ Done — `build_minimal_embed_text()` in `embeddings_loader.py`
- ~~For file/dir/namespace: consider whether these need embeddings at all~~ Decision: embed all. Structural compounds are searchable; callers filter by `kind` if needed.

---

## Deliverable

> **Status: RESOLVED.** All items below achieved by specs 006 + 007.

After a rebuild:
- Briefs jump from ~2,165 to ~4,900+ (spec 006)
- notes, rationale, usages are populated (83%, 83%, 55%) (spec 006)
- `source_text` / `definition_text` are populated for entities with body locations (spec 007)
- `params` NULL when empty (not `{}`) (spec 007)
- Embedding coverage ≥95% (spec 007 — doc-less entities get minimal embeddings)
- Build fails fast on misconfigured `PROJECT_ROOT` or stale code graph line ranges (spec 007)
