# Implementation Audit: Multi-View Search Pipeline

**Date**: 2026-03-21
**Branch**: `004-multi-view-search`
**Base**: `master`
**Files audited**: 28 (14 core, 14 test/config)

---

## Findings

| ID | Category | Severity | Location | Description | Quoted Evidence |
|----|----------|----------|----------|-------------|-----------------|
| SD-001 | Spec Drift | HIGH | `mcp/doc_server/server/search.py:215` | `hybrid_search` types `embedding_provider` as `EmbeddingProvider \| None` — FR-072 requires non-optional | `embedding_provider: EmbeddingProvider \| None = None,` |
| SD-002 | Spec Drift | HIGH | `mcp/doc_server/server/search.py:252-261` | Conditional `if embedding_provider:` / `if query_embedding:` guards remain — FR-074 requires removal | `if embedding_provider:` / `if query_embedding:` |
| SD-003 | Spec Drift | HIGH | `mcp/doc_server/server/search.py:327-336` | `score` ≠ `winning_score` when exact/scope boosted to 10.0/20.0 — FR-061 requires `score` MUST always equal `winning_score` | `final_score = max(final_score, 10.0)` … `score=final_score, winning_score=winning_score` |
| SD-004 | Spec Drift | HIGH | `mcp/doc_server/server/search.py:55-65` | `Candidate` dataclass missing `token_jaccard` and `query_coverage` signals — FR-032 requires 8 intermediate signals | Candidate fields: `doc_semantic`, `symbol_semantic`, `doc_keyword`, `symbol_keyword`, `trigram`, `name_exact` — missing `token_jaccard`, `query_coverage` |
| SD-005 | Spec Drift | HIGH | `mcp/doc_server/server/search.py:67-71` | `_shape_tsrank` does not clamp to [0, 1] — FR-033 requires clamped values | `return math.log1p(raw) / math.log1p(ceiling)` |
| SD-006 | Spec Drift | MEDIUM | `mcp/doc_server/server/search.py:288-294` | Floor thresholds hardcoded, not configurable via `ServerConfig` fields with env var overrides — FR-043 requires configurable via ServerConfig | `floor_thresholds = {"doc_semantic": 0.3, "symbol_semantic": 0.3, …}` |
| SD-007 | Spec Drift | MEDIUM | `mcp/doc_server/build_mcp_db.py:188-189` | `doc_search_vector` weight C missing `params` values — FR-010 requires params(values concatenated) in weight C | `setweight(to_tsvector('english', COALESCE(notes, '') \|\| ' ' \|\| COALESCE(rationale, '') \|\| ' ' \|\| COALESCE(returns, '')), 'C')` |
| SD-008 | Spec Drift | MEDIUM | `mcp/doc_server/server/search.py:409` | `hybrid_search_usages` still types `embedding_provider: EmbeddingProvider \| None = None` — FR-072 applies to all search paths | `embedding_provider: EmbeddingProvider \| None = None,` |
| SD-009 | Spec Drift | MEDIUM | `mcp/doc_server/server/resolver.py:56` | `resolve_entity` still types `embedding_provider: EmbeddingProvider \| None = None` — FR-072 applies to resolver | `embedding_provider: EmbeddingProvider \| None = None,` |
| SD-010 | Spec Drift | MEDIUM | `mcp/doc_server/server/search.py:213-219` | `hybrid_search` takes `doc_view` and `symbol_view` as optional kwargs defaulting to `None` — views are required runtime components | `doc_view: RetrievalView \| None = None, symbol_view: RetrievalView \| None = None,` |
| SD-011 | Spec Drift | LOW | `mcp/doc_server/build_helpers/entity_processor.py:682` | `symbol_searchable` strips ALL non-alphanumeric chars — FR-014 specifies only `*&(),;` | `re.sub(r"[^a-z0-9_ ]", "", raw.lower())` |
| SD-012 | Spec Drift | LOW | `mcp/doc_server/server/search.py:219` | Missing per-search observability for channels queried, candidates per channel, reranking latency — FR-065 requires 6 logged metrics | Only logs `pre_filter`, `post_filter`, `result_count` |
| CV-001 | Constitution | MEDIUM | `mcp/doc_server/server/embedding.py:12` | `from __future__ import annotations` present in changed file — constitution mandates Python 3.14+ native lazy annotations, no `__future__` import | `from __future__ import annotations` |
| CV-002 | Constitution | MEDIUM | `mcp/doc_server/server/tools/search.py:72-73` | `lc.get("doc_view")` / `lc.get("symbol_view")` uses None-tolerant access — constitution requires fail-fast, these are required runtime components | `doc_view=lc.get("doc_view"), symbol_view=lc.get("symbol_view"),` |
| SF-001 | Silent Failure | MEDIUM | `mcp/doc_server/server/server.py:77` | `embedding_available=lc["embedding_provider"] is not None` — embedding is now mandatory, this check is dead logic preserving the appearance of optional embedding | `embedding_available=lc["embedding_provider"] is not None,` |
| PH-001 | Phantom | MEDIUM | `mcp/doc_server/server/lifespan.py:124,134` | `RetrievalView.floor_thresholds` passed as `{}` empty dict — field is declared but never read by search pipeline; actual thresholds are hardcoded in search.py | `floor_thresholds={},` |
| TQ-001 | Test Quality | HIGH | `mcp/doc_server/tests/test_search_units.py:28-30` | `test_raw_above_ceiling_exceeds_one` asserts shaped value > 1.0 — contradicts FR-033 requirement that shaped values be clamped to [0,1]; test encodes the wrong behavior | `assert result > 1.0` |
| TQ-002 | Test Quality | MEDIUM | `mcp/doc_server/tests/conftest.py:87-258` | Test fixtures do not populate `symbol_searchable` column — trigram channel tests cannot actually exercise pg_trgm queries; all trigram tests pass vacuously | `symbol_searchable` absent from all Entity fixtures |
| TQ-003 | Test Quality | MEDIUM | `mcp/doc_server/tests/conftest.py:264-278` | Test tsvector fixture SQL omits `params` from weight C — mirrors the production bug in SD-007, cannot catch it | Missing `params` in doc_search_vector test fixture SQL |
| WC-001 | Wiring | MEDIUM | `mcp/doc_server/server/resources.py:209` | `get_stats_resource` parameter `embedding_available: bool = False` — default is `False` (defensive), should be removed or hardcoded to `True` since embedding is mandatory | `embedding_available: bool = False,` |

---

## Requirement Traceability

| Requirement | Status | Implementing Code | Notes |
|-------------|--------|-------------------|-------|
| FR-001 | IMPLEMENTED | `db_models.py:91-100` | `doc_embedding` and `symbol_embedding` Vector columns present |
| FR-002 | IMPLEMENTED | `db_models.py:103-114` | `doc_search_vector` and `symbol_search_vector` TSVECTOR columns present |
| FR-003 | IMPLEMENTED | `db_models.py:117-120` | `symbol_searchable` TEXT column present |
| FR-004 | IMPLEMENTED | `db_models.py:123-126` | `qualified_name` TEXT column present |
| FR-005 | IMPLEMENTED | `build_mcp_db.py:107-115` | HNSW indexes on both embedding columns |
| FR-006 | IMPLEMENTED | `build_mcp_db.py:117-118` | GIN indexes on both tsvector columns |
| FR-007 | IMPLEMENTED | `build_mcp_db.py:120` | GiST trigram index on `symbol_searchable` |
| FR-008 | IMPLEMENTED | `build_mcp_db.py:91` | `CREATE EXTENSION IF NOT EXISTS pg_trgm` |
| FR-010 | PARTIAL | `build_mcp_db.py:182-189` | Weight C missing `params` values concatenation |
| FR-011 | IMPLEMENTED | `build_mcp_db.py:182-189` | `source_text` and `definition_text` excluded |
| FR-012 | IMPLEMENTED | `build_mcp_db.py:191-196` | Simple dictionary, correct weights |
| FR-013 | IMPLEMENTED | `build_mcp_db.py:191-196` | No documentation prose fields in symbol tsvector |
| FR-014 | DEVIATED | `entity_processor.py:682` | Strips all non-alphanumeric instead of specific punctuation |
| FR-015 | IMPLEMENTED | `search.py:174-185` | `symbol_searchable` used only for trigram queries |
| FR-016 | IMPLEMENTED | `entity_processor.py:632-669` | Containment graph traversal for qualified_name |
| FR-017 | IMPLEMENTED | `entity_processor.py:671-676` | Definition text fallback for `::`  |
| FR-018 | IMPLEMENTED | `db_models.py:123-126` | `qualified_name` stored as explicit column |
| FR-020 | IMPLEMENTED | `entity_processor.py:690-714` | Labeled prose fields, bare name fallback |
| FR-021 | IMPLEMENTED | `entity_processor.py:717-738` | Qualified scoped signature for functions |
| FR-022 | IMPLEMENTED | `entity_processor.py:726-731` | Return type, qualified scope, bare name, param types |
| FR-023 | IMPLEMENTED | `entity_processor.py:717-738` | No parameter names or prose in symbol text |
| FR-024 | IMPLEMENTED | `entity_processor.py:737-738` | Non-functions use `qualified_name` alone |
| FR-025 | IMPLEMENTED | `build_mcp_db.py:456-478` | Dual cache files with `embedding_type` parameter |
| FR-026 | IMPLEMENTED | `build_mcp_db.py:456-478` | Uses `sync_embeddings_cache` with `doc` and `symbol` |
| FR-027 | IMPLEMENTED | `retrieval_view.py:17-28` | `RetrievalView` parameterization allows one or two models |
| FR-030 | PARTIAL | `search.py:100-185` | Five channels present but `token_jaccard` and `query_coverage` missing from signal vector |
| FR-031 | IMPLEMENTED | `search.py:264-271` | Entity ID union merge |
| FR-032 | PARTIAL | `search.py:55-65` | Only 6 of 8 specified signals implemented — missing `token_jaccard` and `query_coverage` |
| FR-033 | DEVIATED | `search.py:67-71` | Log-shaping implemented but values NOT clamped to [0, 1] |
| FR-034 | MISSING | — | `token_jaccard` not implemented anywhere |
| FR-035 | MISSING | — | `query_coverage` not implemented anywhere |
| FR-036 | IMPLEMENTED | `search.py:288-306` | Per-signal floor filtering with threshold checks |
| FR-037 | IMPLEMENTED | `search.py:297-298` | `name_exact` bypass |
| FR-038 | IMPLEMENTED | `search.py:309-319` | Cross-encoder scores both views per candidate |
| FR-039 | IMPLEMENTED | `search.py:323-328` | `max(symbol_ce_score, doc_ce_score)` determines score |
| FR-040 | IMPLEMENTED | `search.py:323-336` | `winning_view`, `winning_score`, `losing_score` assigned |
| FR-041 | IMPLEMENTED | `search.py` | No per-query normalization in entity search pipeline |
| FR-042 | IMPLEMENTED | `build_mcp_db.py:200-227`, `db_models.py:257-265` | Ceilings computed at build, stored in `search_config` table |
| FR-043 | DEVIATED | `search.py:288-294` | Thresholds hardcoded, not in `ServerConfig` with env var overrides; `RetrievalView.floor_thresholds` unused |
| FR-044 | IMPLEMENTED | `search.py:323-328` | No weighted combination; cross-encoder determines rank |
| FR-045 | IMPLEMENTED | `retrieval_view.py:24` | Each view carries its own cross-encoder reference |
| FR-046 | IMPLEMENTED | `lifespan.py:27-39` | Doc view cross-encoder receives labeled text |
| FR-047 | IMPLEMENTED | `lifespan.py:42-51` | Symbol view cross-encoder receives `symbol_embed_text` |
| FR-048 | IMPLEMENTED | `config.py:63-66` | Cross-encoder model configurable via `ServerConfig` |
| FR-049 | IMPLEMENTED | `lifespan.py:107-111` | Server fails fast without provider; cross-encoder initialized at startup |
| FR-050 | IMPLEMENTED | `retrieval_view.py:17-28` | `RetrievalView` dataclass with all specified fields |
| FR-051 | IMPLEMENTED | `lifespan.py:114-143` | `doc_view` and `symbol_view` instantiated |
| FR-052 | IMPLEMENTED | `retrieval_view.py:17-28` | New views addable without modifying core pipeline |
| FR-053 | N/A | — | Out of scope for this feature (deferred) |
| FR-055 | IMPLEMENTED | `entity_processor.py:690-738` | `build_doc_embed_texts` and `build_symbol_embed_texts` replace old function |
| FR-056 | IMPLEMENTED | `build_mcp_db.py:445-453` | `derive_qualified_names` called before `build_symbol_embed_texts` |
| FR-057 | IMPLEMENTED | `build_mcp_db.py:182-196` | Dual tsvectors via UPDATE after entity insertion |
| FR-058 | IMPLEMENTED | `build_mcp_db.py:453` | `build_symbol_searchable` called after `derive_qualified_names` |
| FR-060 | IMPLEMENTED | `tools/search.py:31-46` | Same parameters: `query`, `kind`, `capability`, `top_k`, `source` |
| FR-061 | DEVIATED | `search.py:327-343` | `score` ≠ `winning_score` when boosted for exact/scope matches |
| FR-062 | IMPLEMENTED | `search.py:391-556` | `hybrid_search_usages` unchanged |
| FR-063 | IMPLEMENTED | `db_models.py` | Old `embedding` and `search_vector` columns removed |
| FR-065 | PARTIAL | `search.py:219,296,349` | Only logs 3 of 6 required metrics (missing per-channel counts, channels queried, reranking latency) |
| FR-066 | IMPLEMENTED | `entity_processor.py:662-669` | Derivation stats logged |
| FR-070 | IMPLEMENTED | `enums.py` diff | `SearchMode` enum removed; `search_mode` removed from `SearchResult` |
| FR-071 | PARTIAL | `config.py` diff, `server.py:77` | `embedding_enabled` removed from config; but `embedding_available=…is not None` check remains in server.py |
| FR-072 | DEVIATED | `search.py:215`, `search.py:409`, `resolver.py:56` | `EmbeddingProvider` still typed as `Optional` in three function signatures |
| FR-073 | IMPLEMENTED | `config.py:38-40` | `embedding_provider` is required field (no `None` default) |
| FR-074 | DEVIATED | `search.py:252-261`, `resolver.py:94` | `if embedding_provider:` and `if query_embedding:` guards remain |
| FR-075 | IMPLEMENTED | `enums.py`, `config.py` | V1 degradation requirements superseded |

---

## Metrics

- **Files audited**: 28
- **Findings**: 0 critical, 5 high, 11 medium, 4 low
- **Spec coverage**: 55 / 62 requirements implemented (5 partial, 2 deviated, 2 missing)
- **Constitution compliance**: 2 violations across 5 principles checked

---

## Remediation Decisions

For each item below, choose an action:
- **fix**: Create a remediation task to fix the implementation
- **spec-proposal**: Propose a spec update (recorded in audit.md for user to review and apply separately)
- **skip**: Accept the finding and take no action
- **split**: Fix part in implementation, propose spec update for part (explain which)

### 1. [SD-001] `hybrid_search` types `embedding_provider` as `EmbeddingProvider | None`
**Location**: [search.py:215](mcp/doc_server/server/search.py#L215)
**Spec says**: FR-072 — `EmbeddingProvider` MUST NOT be typed as `Optional`
**Code does**: `embedding_provider: EmbeddingProvider | None = None`

Action: **fix** → T031

### 2. [SD-002] Conditional `if embedding_provider:` guards remain in search pipeline
**Location**: [search.py:252-261](mcp/doc_server/server/search.py#L252-L261)
**Spec says**: FR-074 — All `if embedding_provider:` / `if query_embedding:` branches MUST be removed
**Code does**: Retains both conditional guards, skipping semantic channels when provider is None

Action: **fix** → T032

### 3. [SD-003] `score` ≠ `winning_score` for exact/scope matches
**Location**: [search.py:327-336](mcp/doc_server/server/search.py#L327-L336)
**Spec says**: FR-061 — `score` MUST always equal `winning_score`
**Code does**: Boosts `score` to 10.0/20.0 for exact/scope matches while `winning_score` remains the cross-encoder score

Action: **fix** → T033

### 4. [SD-004] Missing `token_jaccard` and `query_coverage` signals
**Location**: [search.py:55-65](mcp/doc_server/server/search.py#L55-L65)
**Spec says**: FR-032 requires 8 intermediate signals including `token_jaccard` and `query_coverage`; FR-034 and FR-035 define their computation
**Code does**: Only 6 signals implemented. `token_jaccard` and `query_coverage` are absent from both the `Candidate` dataclass and the search pipeline.

Action: **fix** → T034

### 5. [SD-005] `_shape_tsrank` does not clamp to [0, 1]
**Location**: [search.py:67-71](mcp/doc_server/server/search.py#L67-L71)
**Spec says**: FR-033 — Shaped values MUST be clamped to [0, 1]
**Code does**: Returns unclamped `log(1+score)/log(1+ceiling)` which can exceed 1.0

Action: **fix** → T035

### 6. [TQ-001] Test asserts wrong behavior for tsrank clamping
**Location**: [test_search_units.py:28-30](mcp/doc_server/tests/test_search_units.py#L28-L30)
**Spec says**: FR-033 — shaped values clamped to [0, 1]
**Test asserts**: `assert result > 1.0` — encodes the spec violation as expected behavior

Action: **fix** → T035 (same task as SD-005)

---

### MEDIUM / LOW Summary

- **SD-006** (MEDIUM): Floor thresholds hardcoded in search.py, not configurable via `ServerConfig` with env var overrides per FR-043
- **SD-007** (MEDIUM): `doc_search_vector` weight C omits `params` values per FR-010
- **SD-008** (MEDIUM): `hybrid_search_usages` retains optional `EmbeddingProvider` typing
- **SD-009** (MEDIUM): `resolve_entity` retains optional `EmbeddingProvider` typing
- **SD-010** (MEDIUM): `hybrid_search` kwargs `doc_view`/`symbol_view` default to `None`
- **SD-011** (LOW): `symbol_searchable` strips all non-alphanumeric chars vs. FR-014 specific list
- **SD-012** (LOW): Per-search observability logs 3 of 6 required metrics per FR-065
- **CV-001** (MEDIUM): `from __future__ import annotations` in `embedding.py:12`
- **CV-002** (MEDIUM): `lc.get("doc_view")` uses None-tolerant access for required component
- **SF-001** (MEDIUM): `server.py:77` checks `embedding_provider is not None` — now dead logic
- **PH-001** (MEDIUM): `RetrievalView.floor_thresholds` passed as `{}`, never read
- **TQ-002** (MEDIUM): Test fixtures omit `symbol_searchable` — trigram tests pass vacuously
- **TQ-003** (MEDIUM): Test fixture tsvector SQL mirrors production bug (missing params)
- **WC-001** (MEDIUM): `get_stats_resource` defaults `embedding_available=False` — should be True or removed

All MEDIUM/LOW findings promoted to remediation tasks.

---

## Proposed Spec Changes

None — all findings resolved via implementation fixes.

---

## Remediation Tasks

Appended to `tasks.md` under **Audit Remediation** section:

- T031 [AR] Make `embedding_provider` non-optional in `hybrid_search`, `hybrid_search_usages`, and `resolve_entity` (SD-001, SD-008, SD-009)
- T032 [AR] Remove `if embedding_provider:` / `if query_embedding:` conditional guards (SD-002)
- T033 [AR] Fix `score` to always equal `winning_score` (SD-003)
- T034 [AR] Implement `token_jaccard` and `query_coverage` signals (SD-004)
- T035 [AR] Clamp `_shape_tsrank` to [0,1] and fix test (SD-005, TQ-001)
- T036 [AR] Move floor thresholds to `ServerConfig` with env var overrides (SD-006, PH-001)
- T037 [AR] Add `params` to `doc_search_vector` weight C in SQL and test fixtures (SD-007, TQ-003)
- T038 [AR] Make `doc_view`/`symbol_view` non-optional; use `lc[]` not `lc.get()` (SD-010, CV-002)
- T039 [AR] Remove `from __future__ import annotations` from embedding.py (CV-001)
- T040 [AR] Remove dead `embedding_available` check and parameter (SF-001, WC-001)
- T041 [AR] Populate `symbol_searchable` in test fixtures for trigram coverage (TQ-002)
- T042 [AR] Add per-search observability logging (SD-012)
- T043 [AR] Narrow `symbol_searchable` stripping to spec-defined punctuation (SD-011)
