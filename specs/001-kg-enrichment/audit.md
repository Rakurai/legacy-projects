# Implementation Audit: Knowledge Graph Enrichment (V1)

**Date**: 2026-03-19
**Branch**: `001-kg-enrichment`
**Base**: `master`
**Files audited**: 25 (source files only, excluding spec/docs)

---

## Findings

| ID | Category | Severity | Location | Description | Quoted Evidence |
|----|----------|----------|----------|-------------|-----------------|
| SF-001 | Silent Failure | CRITICAL | `server/tools/search.py:53-60` | Invalid `source` parameter returns empty results with a warning instead of raising an error | `log.warning("Unsupported search source", source=source)` → `return SearchResponse(search_mode=SearchMode.KEYWORD_FALLBACK, results=[], ...)` |
| CV-001 | Constitution Violation | CRITICAL | `server/search.py:143-147` | Embedding failure caught and silently degraded to keyword-only; constitution forbids log-and-continue | `except (OSError, RuntimeError, TimeoutError) as e: log.warning("Embedding generation failed; falling back to keyword-only", error=str(e))` |
| CV-002 | Constitution Violation | CRITICAL | `server/search.py:219-223` | Same silent fallback pattern in `hybrid_search_usages` | `except (OSError, RuntimeError, TimeoutError) as e: log.warning("Embedding generation failed; using keyword-only for usages search", ...)` |
| CQ-001 | Code Quality | MEDIUM | `server/tools/explain.py:59-82` and `server/tools/entity.py:101-125` | Duplicated fan_in ranking query (25 lines) between `explain_interface` and `get_entity` — identical subquery, outerjoin, ordering, and limit | Both files contain identical: `fanin_sq = (sa_select(Entity.signature, func.max(Entity.fan_in).label("fan_in")).group_by(Entity.signature).subquery())` + `outerjoin(EntityUsage, fanin_sq, ...)` |
| CQ-002 | Code Quality | MEDIUM | `server/tools/explain.py:63` and `server/tools/entity.py:106` | `from sqlalchemy import outerjoin` imported inside function body instead of at module level | `from sqlalchemy import outerjoin` |
| SD-001 | Spec Drift | MEDIUM | `server/enums.py` | T017 says to add `"usages"` to `SearchSource` enum in `server/enums.py`, but no `SearchSource` enum exists — source validation is done via inline string comparison | `if source not in ("entity", "usages"):` in `server/tools/search.py:53` |
| CV-003 | Constitution Violation | MEDIUM | `server/tools/entity.py:173-174` | `get_source_code` catches `OSError`/`UnicodeDecodeError` and logs a warning instead of propagating — silent failure on disk read for context lines | `except (OSError, UnicodeDecodeError) as e: log.warning("Could not read context from disk", ...)` |

---

## Requirement Traceability

| Requirement | Status | Implementing Code | Notes |
|-------------|--------|-------------------|-------|
| FR-001 (doc_state) | IMPLEMENTED | `build_helpers/entity_processor.py:444-452`, `build_mcp_db.py:152` | Carried from `doc.state`, fail-fast on missing |
| FR-002 (notes_length) | IMPLEMENTED | `build_helpers/entity_processor.py:454-457`, `build_mcp_db.py:153` | Character count of notes field |
| FR-003 (is_contract_seed) | IMPLEMENTED | `build_helpers/entity_processor.py:459-462`, `build_mcp_db.py:154` | Threshold=10, configurable constant |
| FR-004 (rationale_specificity) | IMPLEMENTED | `build_helpers/entity_processor.py:465-474`, `build_mcp_db.py:155` | Length × domain-term density heuristic |
| FR-005 (entity_usages table) | IMPLEMENTED | `server/db_models.py:104-161`, `build_mcp_db.py:180-244` | Drop+recreate, key parsing, tsvector |
| FR-006 (usage embeddings) | IMPLEMENTED | `build_mcp_db.py:225-231` | Inline batch generation via provider |
| FR-007 (explain_interface) | IMPLEMENTED | `server/tools/explain.py:29-116` | Five-part contract, top 5 by fan_in |
| FR-008 (search source=usages) | IMPLEMENTED | `server/search.py:193-344`, `server/tools/search.py:63-71` | Hybrid search, grouped by callee |
| FR-009 (get_entity enrichment fields) | IMPLEMENTED | `server/converters.py:58-61`, `server/models.py:133-136` | All four fields in EntityDetail |
| FR-010 (include_usages) | IMPLEMENTED | `server/tools/entity.py:52,100-134` | Top 5 by fan_in ranking |
| FR-012 (query by callee/caller) | IMPLEMENTED | `server/db_models.py:115-116` | Indexes on callee_id and (caller_compound, caller_sig) |
| FR-013 (fail-fast on malformed) | IMPLEMENTED | `build_helpers/entity_processor.py:445-449` | BuildError on missing state field |

---

## Metrics

- **Files audited**: 25
- **Findings**: 3 critical, 0 high, 4 medium, 0 low
- **Spec coverage**: 12 / 12 requirements implemented
- **Constitution compliance**: 3 violations across 5 principles checked

---

## Remediation Decisions

For each item below, choose an action:
- **fix**: Create a remediation task to fix the implementation
- **spec**: Update the spec to match the implementation (if the implementation is actually correct)
- **skip**: Accept the finding and take no action
- **split**: Fix part in implementation, update part in spec

### 1. [SF-001] Invalid `source` parameter returns empty results instead of raising
**Location**: `server/tools/search.py:53-60`
**Constitution says**: Fail-fast, no fallbacks. Silent failure is prohibited.
**Code does**: Returns empty SearchResponse with `KEYWORD_FALLBACK` mode and a log warning when `source` is not `"entity"` or `"usages"`.

This should raise a `ValueError` — an invalid `source` value is a caller bug, not a degraded-service condition.

Action: fix / spec / skip / split

### 2. [CV-001] Embedding failure silently degrades to keyword-only in `hybrid_search`
**Location**: `server/search.py:143-147`
**Constitution says**: Silent failure, log-and-continue, and broad `except Exception` without immediate re-raise are prohibited.
**Code does**: Catches `(OSError, RuntimeError, TimeoutError)`, logs a warning, and silently continues with keyword-only search.

**Context**: This is a pre-existing V1 pattern (not introduced by this branch). The embedding provider is an external dependency that may be unavailable at runtime. The fallback provides degraded but functional search.

Action: fix / spec / skip / split

### 3. [CV-002] Same embedding fallback pattern in `hybrid_search_usages`
**Location**: `server/search.py:219-223`
**Constitution says**: Same as CV-001.
**Code does**: Same silent degradation pattern, copied from V1 `hybrid_search` into the new `hybrid_search_usages`.

Action: fix / spec / skip / split

### MEDIUM / LOW Summary

- **CQ-001** (MEDIUM): Duplicated fan_in ranking query (~25 lines identical) between `explain.py:59-82` and `entity.py:101-125`. Should be extracted to a shared helper.
- **CQ-002** (MEDIUM): `from sqlalchemy import outerjoin` imported inside function body in two files. Move to module-level imports.
- **SD-001** (MEDIUM): No `SearchSource` enum was created despite T017 mentioning it; source validation uses inline string comparison. The enum would enforce type-safe source values per the "Types Are Contracts" principle.
- **CV-003** (MEDIUM): `get_source_code` silently catches disk read errors for context lines. This is a pre-existing V1 pattern — context lines are optional supplementary data, so propagating might be too aggressive. But the constitution is clear about log-and-continue being prohibited.

Would you like to promote any MEDIUM findings to remediation tasks?

---

## Spec Amendments

None.

---

## Remediation Tasks

Appended to `tasks.md` under **Audit Remediation**:

- T029 [AR] Raise `ValueError` for invalid `source` in search tool (SF-001)
- T030 [AR] Remove embedding fallback in `hybrid_search` (CV-001)
- T031 [AR] Remove embedding fallback in `hybrid_search_usages` (CV-002)
- T032 [P] [AR] Extract duplicated fan_in ranking query to shared helper (CQ-001, CQ-002)
- T033 [P] [AR] Add `SearchSource` enum, type the `source` parameter (SD-001)
- T034 [P] [AR] Remove silent catch in `get_source_code` context reads (CV-003)
- T035 [AR] Remove embedding fallback in `resolver.py` (CV-001 pre-existing)
- T036 Run lint, typecheck, and test suite after all remediations

**8 remediation tasks created, 0 spec updates, 0 skipped.**
Run `/speckit.implement` to execute remediation tasks.
