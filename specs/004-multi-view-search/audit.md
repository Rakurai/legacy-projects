# Implementation Audit: Multi-View Search Pipeline (Re-Audit)

**Date**: 2025-07-16
**Branch**: `004-multi-view-search`
**Base**: `master`
**Files audited**: 31 (16 core, 15 test/config)
**Prior audit**: 2026-03-21 — 20 findings, all remediated via T031–T050. This re-audit verifies those fixes and scans for remaining issues.

---

## Findings

| ID | Category | Severity | Location | Description | Quoted Evidence |
|----|----------|----------|----------|-------------|-----------------|
| SD-001 | Spec Drift | HIGH | `server/search.py:443-445` | `query_coverage` computed on name+signature tokens; FR-035 requires doc text tokens. Makes it redundant with `token_jaccard` (both operate on same token set). | `entity_tokens = _tokenize(f"{row.name or ''} {row.signature or ''}")` — used for both `c.token_jaccard` and `c.query_coverage` |
| WC-001 | Wiring | HIGH | `build_helpers/embeddings_loader.py:175`, `tests/test_embeddings.py:131` | `sync_embeddings_cache` now reads `provider.max_batch_size` for batching; tests use `MagicMock()` without configuring this attribute. `MagicMock.__int__()` returns 1 → 2 texts split into 2 batches → each returns full 2-vector mock → 4 vectors for 2 keys → `zip(strict=True)` raises `ValueError`. | `batch_size = provider.max_batch_size` where mock has no `max_batch_size` configured; `mock_provider.embed_batch.return_value = [[0.1] * 3, [0.2] * 3]` returns 2 vectors regardless of batch size |
| SD-002 | Spec Drift | LOW | `server/search.py:399` | Per-channel candidate counts logged at DEBUG; FR-065 says "MUST log" channels queried and candidates per channel. Data is present but requires DEBUG level to observe. INFO log at line 576 covers totals only. | `log.debug("Channel counts", name_exact=len(name_exact_ids), ... merged=len(all_ids))` |
| DD-001 | Design Drift | HIGH | `server/search.py:533-573` | Tier-based sorting (scope=2, exact=1, normal=0) overrides cross-encoder ranking. Design D-01: "The cross-encoder alone determines order." Tier system is functionally a structured boost hack. | `scored_results.sort(key=lambda item: (item[0].sort_tier, item[1], item[2], item[0].score), reverse=True)` |
| DD-002 | Design Drift | MEDIUM | `server/search.py:174-207,553-554` | `kind_priority` heuristic guesses entity relevance by query shape (constant-like→variables, type-like→classes). Not in design. Overrides CE ordering within tiers. | `kind_priority = _exact_match_kind_priority(entity.kind, search_query)` |
| DD-003 | Design Drift | MEDIUM | `server/search.py:63,461` | `signature_exact` filter bypass not in design. Internal review: "We do not need exact signature match or exact qualified name match as separate features." | `c.signature_exact = eid in sig_exact_ids` ... `if c.name_exact or c.signature_exact:` |
| DD-004 | Design Drift | LOW | `server/search.py:370-391` | Stage 1 channels executed sequentially. Design: "five parallel retrieval channels." | Five sequential `await` calls instead of `asyncio.gather()` |
| DD-005 | Design Drift | LOW | `server/config.py:48` | Embedding model default is `BAAI/bge-base-en-v1.5` (prose). Design E-01 preferred `jinaai/jina-embeddings-v2-base-code`. No evaluation performed. | `embedding_local_model: str = "BAAI/bge-base-en-v1.5"` |
| CQ-001 | Code Quality | LOW | `server/search.py:141` | `import re as _re` inside function body, re-evaluated every call. | `def _tokenize(text: str) -> set[str]: import re as _re` |

---

## Prior Audit Remediation Verification

All 20 findings from the 2026-03-21 audit (T031–T050) have been verified as resolved:

- **SD-001–SD-005** (5 HIGH): `EmbeddingProvider` non-optional, conditional guards removed, `score==winning_score`, `token_jaccard`/`query_coverage` implemented, `_shape_tsrank` clamped — all fixed
- **SD-006–SD-012** (5 MEDIUM, 2 LOW): Floor thresholds configurable via `RetrievalView`, `params` in tsvector weight C, optional typing removed from usage search and resolver, `symbol_searchable` punctuation narrowed, observability logs added — all fixed
- **CV-001–CV-002** (2 MEDIUM): `from __future__ import annotations` removed from `embedding.py`, `lc.get()` changed to `lc[]` — both fixed
- **SF-001, PH-001** (2 MEDIUM): Dead `embedding_available` logic removed, `RetrievalView.floor_thresholds` populated and consumed — both fixed
- **TQ-001–TQ-003** (1 HIGH, 2 MEDIUM): Clamping test corrected, `symbol_searchable` populated in fixtures, `params` added to test SQL — all fixed
- **WC-001** (1 MEDIUM): `get_stats_resource` `embedding_available` parameter removed — fixed

---

## Requirement Traceability

| Requirement | Status | Implementing Code | Notes |
|-------------|--------|-------------------|-------|
| FR-001 | IMPLEMENTED | `server/db_models.py:85-86` | `doc_embedding`, `symbol_embedding` Vector columns |
| FR-002 | IMPLEMENTED | `server/db_models.py:87-88` | `doc_search_vector`, `symbol_search_vector` TSVECTOR columns |
| FR-003 | IMPLEMENTED | `server/db_models.py:89` | `symbol_searchable` TEXT column |
| FR-004 | IMPLEMENTED | `server/db_models.py:90` | `qualified_name` TEXT column |
| FR-005 | IMPLEMENTED | `server/db_models.py:108-121` | Dual HNSW indexes (vector_cosine_ops, m=16, ef_construction=64) |
| FR-006 | IMPLEMENTED | `server/db_models.py:122-129` | GIN indexes on both tsvector columns |
| FR-007 | IMPLEMENTED | `server/db_models.py:130-136` | GiST trigram index on `symbol_searchable` |
| FR-008 | IMPLEMENTED | `build_mcp_db.py:60` | `CREATE EXTENSION IF NOT EXISTS pg_trgm` |
| FR-010 | IMPLEMENTED | `build_mcp_db.py:257-276` | Parameterized tsvector with english dict; name='A', brief+details='B', notes+rationale+params+returns='C' |
| FR-011 | IMPLEMENTED | `build_mcp_db.py:257-276` | No source_text or definition_text in doc tsvector |
| FR-012 | IMPLEMENTED | `build_mcp_db.py:279-298` | Simple dict tsvector: name='A', qualified_name+signature='B', definition_text='C' |
| FR-013 | IMPLEMENTED | `build_mcp_db.py:279-298` | No prose fields in symbol tsvector |
| FR-014 | IMPLEMENTED | `build_helpers/entity_processor.py:695-737` | Strips `*&(),;`, concatenates name+qualified_name+signature |
| FR-015 | IMPLEMENTED | `server/search.py:308-322` | `symbol_searchable` used only in trigram query |
| FR-016 | IMPLEMENTED | `build_helpers/entity_processor.py:600-663` | Walks `contained_by` edges |
| FR-017 | IMPLEMENTED | `build_helpers/entity_processor.py:640-660` | Falls back to `definition_text` parsing for `::` |
| FR-018 | IMPLEMENTED | `server/db_models.py:90` | Stored as explicit column |
| FR-020 | IMPLEMENTED | `build_helpers/entity_processor.py:665-690` | Labeled prose fields, bare name fallback |
| FR-021 | IMPLEMENTED | `build_helpers/entity_processor.py:545-598` | Qualified scoped signature in C++ form |
| FR-022 | IMPLEMENTED | `build_helpers/entity_processor.py:545-598` | Return type, qualified scope, bare name, parameter types |
| FR-023 | IMPLEMENTED | `build_helpers/entity_processor.py:545-598` | No parameter names or prose |
| FR-024 | IMPLEMENTED | `build_helpers/entity_processor.py:590-598` | Non-function entities use `qualified_name` alone |
| FR-025 | IMPLEMENTED | `build_mcp_db.py:170-190` | Separate `_doc.pkl` and `_symbol.pkl` caches |
| FR-026 | IMPLEMENTED | `build_mcp_db.py:170-190` | Uses `sync_embeddings_cache` with `"doc"` and `"symbol"` |
| FR-027 | IMPLEMENTED | `server/retrieval_view.py` | `RetrievalView` parameterizable per view |
| FR-030 | IMPLEMENTED | `server/search.py:370-391` | Five parallel channels: doc semantic, symbol semantic, doc keyword, symbol keyword, trigram |
| FR-031 | IMPLEMENTED | `server/search.py:394-396` | Merged by `entity_id` via set union |
| FR-032 | IMPLEMENTED | `server/search.py:410-445` | 8 signals computed per candidate |
| FR-033 | IMPLEMENTED | `server/search.py:113-128` | `_shape_tsrank` with log shaping and `min(shaped, 1.0)` clamping |
| FR-034 | IMPLEMENTED | `server/search.py:147-155` | `_compute_token_jaccard` on name+signature tokens |
| FR-035 | DEVIATED | `server/search.py:443-445` | Uses name+signature tokens instead of doc text tokens — see SD-001 |
| FR-036 | IMPLEMENTED | `server/search.py:448-470` | Per-signal floor threshold check |
| FR-037 | IMPLEMENTED | `server/search.py:472-476` | `name_exact` bypass preserves candidate |
| FR-038 | IMPLEMENTED | `server/search.py:493-538` | Cross-encoder scores from both views |
| FR-039 | IMPLEMENTED | `server/search.py:540-545` | `winning_score = max(doc_score, sym_score)` |
| FR-040 | IMPLEMENTED | `server/search.py:547-555` | `winning_view`, `winning_score`, `losing_score` in result |
| FR-041 | IMPLEMENTED | `server/search.py` (full pipeline) | No per-query normalization |
| FR-042 | IMPLEMENTED | `build_mcp_db.py:135-165`, `server/lifespan.py:100-115` | Ceilings computed at build, stored in `SearchConfig`, loaded at startup |
| FR-043 | IMPLEMENTED | `server/config.py:35-40`, `server/lifespan.py:120-145` | Floor thresholds in `ServerConfig` with env var overrides, stored in `RetrievalView.floor_thresholds` |
| FR-044 | IMPLEMENTED | `server/search.py:540-545` | No weighted combination; cross-encoder determines rank |
| FR-045 | IMPLEMENTED | `server/retrieval_view.py:20` | `cross_encoder` field on `RetrievalView` |
| FR-046 | IMPLEMENTED | `server/lifespan.py:25-45` | `_assemble_doc_embed_text` produces labeled fields |
| FR-047 | IMPLEMENTED | `server/lifespan.py:48-60` | `_assemble_symbol_embed_text` uses qualified signature |
| FR-048 | IMPLEMENTED | `server/retrieval_view.py`, `server/lifespan.py` | Cross-encoder configurable, both views share same model |
| FR-049 | IMPLEMENTED | `server/lifespan.py:75-85` | Fail-fast startup; no fallback for missing embedding/CE |
| FR-050 | IMPLEMENTED | `server/retrieval_view.py` | `RetrievalView` frozen dataclass with all specified fields |
| FR-051 | IMPLEMENTED | `server/lifespan.py:120-150` | `symbol_view` and `doc_view` instantiated |
| FR-052 | IMPLEMENTED | `server/retrieval_view.py` | Parameterized — new views addable without pipeline changes |
| FR-053 | N/A | — | Out of scope (deferred) |
| FR-055 | IMPLEMENTED | `build_helpers/entity_processor.py:545-598,665-690` | `build_doc_embed_texts` and `build_symbol_embed_texts` |
| FR-056 | IMPLEMENTED | `build_mcp_db.py:100-110` | `derive_qualified_names` before `build_symbol_embed_texts` |
| FR-057 | IMPLEMENTED | `build_mcp_db.py:257-298` | UPDATE statements after entity insertion |
| FR-058 | IMPLEMENTED | `build_mcp_db.py:100-115` | `symbol_searchable` populated after `qualified_name` derived |
| FR-060 | IMPLEMENTED | `server/tools/search.py:15-30` | Same parameters: `query`, `kind`, `capability`, `top_k`, `source` |
| FR-061 | IMPLEMENTED | `server/models.py:50-65` | `winning_view`, `winning_score`, `losing_score` added; `score==winning_score`; `search_mode` removed |
| FR-062 | IMPLEMENTED | `server/search.py:590-735` | `hybrid_search_usages` unchanged |
| FR-063 | IMPLEMENTED | `server/db_models.py` | Old `embedding`/`search_vector` columns absent |
| FR-065 | PARTIAL | `server/search.py:399,576` | Per-channel counts at DEBUG; totals+rerank_ms at INFO. FR requires logging all 6 metrics — all present but per-channel at DEBUG level. |
| FR-066 | IMPLEMENTED | `build_mcp_db.py:155-165,130-140` | Ceiling values and qualified_name derivation stats logged |
| FR-070 | IMPLEMENTED | `server/enums.py` | `SearchMode` enum removed |
| FR-071 | IMPLEMENTED | `server/config.py`, `server/lifespan.py`, `server/search.py`, `server/resolver.py` | No `embedding_enabled` or conditional branches |
| FR-072 | IMPLEMENTED | `server/lifespan.py:70`, `server/config.py:25` | `EmbeddingProvider` non-optional throughout |
| FR-073 | IMPLEMENTED | `server/config.py:25` | `embedding_provider` required, no `None` default |
| FR-074 | IMPLEMENTED | `server/search.py`, `server/resolver.py` | No `if embedding_provider:` guards |
| FR-075 | IMPLEMENTED | — | V1 degradation requirements superseded |

---

## Metrics

- **Files audited**: 31
- **Findings**: 0 critical, 3 high, 2 medium, 4 low
- **Spec coverage**: 57 / 58 requirements implemented (1 deviated: FR-035)
- **Design alignment**: 5 design drift findings (1 high, 2 medium, 2 low) + 1 code quality
- **Constitution compliance**: 0 violations across 6 principles checked (fail-fast, types-as-contracts, source-reflects-truth, uv-only, no-defensive-programming, comment-discipline)

---

## Remediation Decisions

### 1. [SD-001] `query_coverage` computed on name+signature tokens instead of doc text (HIGH)

**Location**: `server/search.py:443-445`
**Spec says (FR-035)**: Query coverage MUST measure the fraction of query non-stopword terms found in the candidate's **doc text**
**Code does**: Tokenizes `f"{row.name or ''} {row.signature or ''}"` and uses that set for both `token_jaccard` and `query_coverage`. This makes `query_coverage` a different formula (coverage vs. Jaccard) over the identical token set — the two signals are algebraically related rather than independent. The spec and design doc explicitly split them: jaccard → compact symbol tokens; coverage → doc prose tokens.

Action: **fix** → T051

### 2. [WC-001] Test failure from batching refactor in `sync_embeddings_cache` (HIGH)

**Location**: `build_helpers/embeddings_loader.py:175`, `tests/test_embeddings.py:131`
**What changed**: `sync_embeddings_cache` now reads `provider.max_batch_size` to batch embedding generation via tqdm
**What broke**: `test_cold_cache_generates_all_embeddings` uses `MagicMock()` without configuring `max_batch_size`. `MagicMock.__int__()` returns 1, so `batch_size=1` splits 2 texts into 2 single-item batches; each batch call returns the full 2-vector mocked result → 4 vectors for 2 keys. `zip(missing_keys_list, all_vectors, strict=True)` raises `ValueError`. Test `assert_called_once()` would also fail since `embed_batch` is called twice.

Action: **fix** → T052

### 3. [DD-001] Tier-based sorting overrides cross-encoder ranking (HIGH)

**Location**: `server/search.py:533-573`
**Design says (D-01)**: "The cross-encoder alone determines order." Exact match is a filter bypass, not a ranking signal.
**Code does**: Sorts by `(sort_tier, kind_priority, fan_in, score)` — tier-2 scope matches and tier-1 exact matches outrank any tier-0 result regardless of CE score. `kind_priority` further reorders within tiers by guessing query intent from shape (constant-like, type-like).

Action: **fix** → T053

### MEDIUM / LOW Summary

- **DD-002** (MEDIUM): `kind_priority` query-shape heuristic overrides CE ordering. → **fix** → T053 (same task)
- **DD-003** (MEDIUM): `signature_exact` filter bypass not in design. → **fix** → T053 (same task)
- **DD-004** (LOW): Sequential channel queries; design says parallel. → **fix** → T054
- **DD-005** (LOW): Embedding model default not evaluated per design E-01/E-02. → **fix** → T057
- **CQ-001** (LOW): `import re` in function body. → **fix** → T055
- **SD-002** (LOW): Per-channel log level. → **skipped** (data is logged at DEBUG)

---

## Proposed Spec Changes

*No spec-change proposals.*

---

## Remediation Tasks

**Audit Remediation (Re-Audit):**
- [ ] T051 [AR] Fix `query_coverage` to tokenize doc text per FR-035 (SD-001)
- [ ] T052 [AR] Fix embedding test mock for `max_batch_size` (WC-001)

**Design Alignment:**
- [ ] T053 [DA] Remove tier-based sorting, `kind_priority`, `fan_in` tiebreaker, `signature_exact` bypass — CE score alone determines order (DD-001, DD-002, DD-003)
- [ ] T054 [DA] Parallelize Stage 1 channel queries with `asyncio.gather()` (DD-004)
- [ ] T055 [DA] Move `import re` to module level (CQ-001)
- [ ] T056 [DA] Optimize token overlap — defer to post-entity-fetch (enables T051)
- [ ] T057 [DA] Evaluate embedding and cross-encoder models per design E-01/E-02 — **prerequisite before finalizing spec** (DD-005)
