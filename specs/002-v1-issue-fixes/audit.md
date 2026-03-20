# Implementation Audit: V1 Known Issue Fixes

**Date**: 2026-03-20
**Branch**: master (002-v1-issue-fixes work)
**Base**: master (pre-implementation)
**Files audited**: 7 source + 3 test files

---

## Findings

| ID | Category | Severity | Location | Description | Quoted Evidence |
|----|----------|----------|----------|-------------|-----------------|
| SD-001 | Spec Drift | HIGH | `entity_processor.py:229` | Dedup key `(name, kind, decl.fn)` incorrectly groups unrelated entities sharing name/kind/file — confirmed in real data: 11 distinct struct `name` fields (all in merc.hh) collapsed into one group, with 10 silently discarded. This is data loss, not imprecision. | `dedup_key = (entity.name, entity.kind, file_key)` |
| SD-002 | Spec Drift | HIGH | `entity_processor.py:257-260` | Survivor selection uses `.cc/.cpp` file-extension heuristic with insertion-order fallback (`cc_candidates[0] if cc_candidates else in_graph[0]`). For falsely grouped entities (SD-001), the `.cc` tiebreaker has no candidates and the fallback picks an arbitrary fragment. Even for true split pairs, `entity.body is not None` is the deterministic Doxygen signal and should replace the extension check entirely. | `cc_candidates[0] if cc_candidates else in_graph[0]` |
| CV-001 | Constitution Violation | MEDIUM | `entity_processor.py:220` | `from collections import defaultdict` imported inside function body; module-level imports are required by clean module structure under "Source Reflects Current Truth" | `from collections import defaultdict` (inside `merge_entities()`) |
| OE-001 | Over-Engineering | LOW | `entity_processor.py:192-194` | `_node_id()` private helper is called from exactly one site (line 248 only) | `def _node_id(entity: DoxygenEntity) -> str:` |
| CQ-001 | Code Quality | LOW | `tests/test_entity_processor.py:140` | `DoxygenLocation` for a file location constructed with `type="decl"` — semantically incorrect; type value should be "file" if the field means anything | `file_loc = DoxygenLocation(fn=file_fn, line=1, type="decl")` |
| TQ-001 | Test Quality | LOW | `tests/test_search_tool.py:136-144` | `test_nonsense_query_returns_no_results` is functionally identical to the pre-existing `test_search_tool_empty_results`; both assert 0 results for a no-match query with different strings | `query="xyzzy_nonexistent_9f3k"` vs pre-existing `query="zzz_nonexistent_xyz_999"` |

---

## Requirement Traceability

| Requirement | Status | Implementing Code | Notes |
|-------------|--------|-------------------|-------|
| FR-001: At most one record per logical entity (name, sig, source path) | DEVIATED | `entity_processor.py:224-232` | Key uses `(name, kind, decl.fn)` not `(name, sig, source path)`; diverges from spec text AND causes data loss — 11 distinct entities confirmed incorrectly merged in real corpus; correct key is `entity.id.member` (T022) |
| FR-002: Each record carries graph metrics AND documentation | IMPLEMENTED | `entity_processor.py:264-285` | Doc copied from sibling if survivor has none; graph metrics assigned downstream per existing pipeline |
| FR-003: Knowledge store entity ID = code graph node ID | IMPLEMENTED | `entity_processor.py:248` | Survivor is selected by `_node_id(e) in graph_node_ids`; survivor's compound ID becomes the record's canonical ID |
| FR-004: Contract seed flag computed from unified record | IMPLEMENTED | `build_mcp_db.py:389-391` | `compute_enriched_fields` (which sets `is_contract_seed`) runs after `merge_entities` on the deduplicated list |
| FR-005: Build logs count of unified declaration/definition pairs | IMPLEMENTED | `entity_processor.py:277-292` | Per-merge `log.info("Split entity merged", ...)` + final `split_pairs_unified=merged_pair_count` in summary log |
| FR-006: Keyword scores normalized within result set before combining | IMPLEMENTED | `search.py:114-120` (entity), `search.py:251-256` (usages) | Intra-query normalization added to both `_merge_scores()` and inline in `hybrid_search_usages()` |
| FR-007: No per-query score normalization | IMPLEMENTED | `search.py:174-185`, `search.py:326-344` | Normalization blocks removed from both `hybrid_search()` and `hybrid_search_usages()` |
| FR-008: Results below threshold excluded; entity exact-name always returned; usage threshold uniform | IMPLEMENTED | `search.py:176-177`, `search.py:329-330` | Threshold filter `score < _SCORE_THRESHOLD` applied; exact-name scores ≥ 10.0 always exceed threshold; usage search applies threshold uniformly with no carve-out |
| FR-009: Raw combined score returned | IMPLEMENTED | `search.py:183`, `search.py:340` | `score=score` (raw) replaces `min(score/normalizer, 1.0)` |
| FR-010: stc has is_contract_seed=true, non-null rationale, non-empty calling_patterns after rebuild | NOT VERIFIED | — | Requires DB rebuild + live server verification (T007/T008); cannot be verified from code alone |

---

## Metrics

- **Files audited**: 10 (7 source, 3 test)
- **Findings**: 0 critical, 2 high, 1 medium, 3 low (SD-001/SD-002 upgraded from MEDIUM to HIGH after real-data analysis confirmed data loss)
- **Spec coverage**: 9 / 10 requirements implemented (FR-010 requires live verification)
- **Constitution compliance**: 1 violation across 5 principles checked

---

## Remediation Decisions

### HIGH Findings (Resolved via T022)

- **SD-001** (HIGH): Dedup key `(name, kind, decl.fn)` causes confirmed data loss in the real corpus. The `name` field appears in 11 different structs in merc.hh; all 11 share the same `(name, variable, merc.hh)` key and are collapsed into a single group — 10 entities discarded. `RoomID` and `act` show similar patterns (4-fragment false groups). Decision: **fix** via T022 — group by `entity.id.member` instead.

- **SD-002** (HIGH): `.cc/.cpp` file-extension tiebreaker is a heuristic that fails for falsely grouped entities (no definition file exists) and falls to non-deterministic `in_graph[0]`. Even for true split pairs, `entity.body is not None` is the correct deterministic test — Doxygen sets `body` only on definition fragments. Decision: **fix** via T022 — replace extension check with `entity.body is not None`.

### MEDIUM / LOW Summary

- **CV-001** (MEDIUM): `from collections import defaultdict` at `entity_processor.py:220` should be at module level. Recommend **fix** — trivial one-line move.

- **OE-001** (LOW): `_node_id()` called from one site. Inline is fine; the extraction adds no abstraction value. Recommend **skip** (readability argument is sufficient).

- **CQ-001** (LOW): `type="decl"` on file location in test helper. Recommend **skip** (`.type` is never accessed in the production path being tested).

- **TQ-001** (LOW): Duplicate nonsense-query test. Recommend **skip** (redundant but harmless; both run fast).

---

## SD-001 / SD-002 Research

**Question**: Is there a graph structure that unambiguously links declaration and definition compounds?

**Finding**: No edge type in the GML links declaration to definition compounds. However, `entity.id.member` (the Doxygen member hash) **is shared** between all fragments of the same logical function — declaration and definition compounds both carry the same member hash. `EntityDatabase.member_groups[member_hash]` groups them explicitly, and `get_body_eid()` in `packages/legacy_common/legacy_common/doxygen_graph.py` already uses this pattern to resolve which fragment owns the body.

**Real-data analysis**: Simulating the current dedup key against the actual artifact corpus revealed 108 multi-entity groups (flagged as "split pairs") under the current key, including at minimum:
- `name` (variable): 11 distinct struct fields from merc.hh collapsed into one group — all have `body=True` and `.hh` file paths, so the `.cc/.cpp` tiebreaker finds no candidates and `in_graph[0]` picks an arbitrary survivor. 10 entities silently discarded.
- `RoomID`: 4 fragments from the same compound over-grouped.
- `act`: 4 fragments incorrectly merged.
- Multiple other groups where the `.cc/.cpp` fallback has no candidates and resolution is insertion-order dependent.

**Body-presence signal**: `entity.body is not None` is Doxygen's authoritative signal that a fragment contains the function definition (not just a declaration). It is deterministic, requires no file-extension inference, and eliminates all fallback paths. The 94 body-less member nodes in the graph are confirmed singletons in `member_groups` (compiler-generated `operator=` and implicit constructors) — they pass through as single-entity groups; no edge case exists.

**Decision**: **fix** — T022 rewrites grouping to use `entity.id.member` and survivor selection to use `entity.body is not None`.

---

## Remediation Tasks (T018–T022)

Appended to `tasks.md`:

- **T018** [AR] CV-001: Move `defaultdict` import to module level in `entity_processor.py:220`
- **T019** [AR] OE-001: Inline `_node_id()` into its single call site at `entity_processor.py:248`
- **T020** [AR] CQ-001: Fix `type="decl"` → `type="file"` in test `_make_entity()` at `test_entity_processor.py:140`
- **T021** [AR] TQ-001: Remove duplicate `test_nonsense_query_returns_no_results` from `test_search_tool.py`
- **T022** [AR] SD-001/SD-002: Rewrite dedup key to `entity.id.member` grouping; replace `.cc/.cpp` tiebreaker with `entity.body is not None`; update `TestMergeEntitiesDedup` tests; run full test suite
