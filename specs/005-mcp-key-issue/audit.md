# Implementation Audit: Deterministic Entity IDs & Documentation Merge Fix

**Date**: 2026-03-17
**Branch**: `005-mcp-key-issue`
**Base**: `master`
**Files audited**: 28 (source + test files changed on branch)

---

## Findings

| ID | Category | Severity | Location | Description | Quoted Evidence |
|----|----------|----------|----------|-------------|-----------------|
| SD-001 | Spec Drift | HIGH | `server/models.py:30` | `EntitySummary.entity_id` field description still says "Internal Doxygen ID" — should reflect the new deterministic `{prefix}:{7 hex}` format. Agent-visible metadata is stale. | `entity_id: str = Field(description="Internal Doxygen ID (for passing to get_entity)")` |
| OE-001 | Over-Engineering | MEDIUM | `build_helpers/entity_ids.py:50-95` | `build_id_map()` is dead code — never called in the build pipeline. The actual pipeline uses `assign_deterministic_ids()` from `entity_processor.py`. Both compute IDs via `compute_entity_id()`, but `build_id_map` takes raw dicts while the pipeline uses `MergedEntity` objects. Only test code calls `build_id_map`. | `def build_id_map(signature_map_data: dict[str, str], code_graph_entities: dict[str, dict]) -> dict[str, str]:` |
| SF-001 | Silent Failure | MEDIUM | `build_mcp_db.py:108-113` | Index creation failures are silently swallowed with `log.warning`. If a critical index (e.g., the embedding HNSW index or GIN search_vector index) fails, the build succeeds but runtime queries will be orders of magnitude slower or broken. | `except Exception as e: log.warning("Index creation failed", sql=idx_sql[:60], error=str(e))` |
| SF-002 | Silent Failure | MEDIUM | `server/resolver.py:283-284` | Semantic search stage catches all exceptions and logs a warning, silently falling through to "not found". Any bug in the semantic search query logic (bad SQL, type error) is masked. | `except Exception as e: log.warning("Semantic search failed", error=str(e), query=query[:50])` |
| SF-003 | Silent Failure | MEDIUM | `server/search.py:155-157` | Embedding generation failure is caught with broad `except Exception` and silently degrades to keyword-only mode. Agent never knows the search quality was degraded due to an unrelated bug. | `except Exception as e: log.warning("Embedding generation failed; falling back to keyword-only", error=str(e))` |
| CV-001 | Constitution Violation | LOW | `server/resolver.py:17` | `from __future__ import annotations` present in changed file. Constitution says "Python 3.14+ lazy annotation evaluation is native; no `from __future__ import annotations`". Pre-existing but not cleaned up during this feature's changes. | `from __future__ import annotations` |
| CV-002 | Constitution Violation | LOW | `server/search.py:19` | Same — `from __future__ import annotations` in a changed file. | `from __future__ import annotations` |
| CQ-001 | Code Quality | MEDIUM | `build_mcp_db.py:154` | Uses `hasattr(merged, 'embedding')` defensive check instead of trusting the object contract. `MergedEntity` never declares `embedding` as an attribute — it's monkey-patched by `attach_embeddings()`. This is a type-safety gap. | `embedding=merged.embedding if hasattr(merged, 'embedding') else None,` |
| CQ-002 | Code Quality | LOW | `build_helpers/loaders.py:7` | Module docstring still references removed `entity_ids.SignatureMap` class. | `- signature_map.json (entity_id ↔ doc_db key mapping — loaded via entity_ids.SignatureMap)` |
| CQ-003 | Code Quality | LOW | `build_helpers/entity_processor.py:57` | Comment referencing `assign_deterministic_ids` uses parentheses style that looks like an incomplete sentence. Minor, but the comment documents runtime behavior. | `# Deterministic ID (assigned by assign_deterministic_ids)` |

---

## Requirement Traceability

| Requirement | Status | Implementing Code | Notes |
|-------------|--------|-------------------|-------|
| FR-001 | IMPLEMENTED | `build_helpers/entity_ids.py:37-47`, `build_helpers/entity_processor.py:148-178` | `compute_entity_id` uses `repr((compound_id, second_element))` → sha256[:7] with prefix. `assign_deterministic_ids` wires it into the pipeline. |
| FR-002 | IMPLEMENTED | `build_helpers/entity_ids.py:19-29` | Prefix mapping: function/define→fn, variable→var, class/struct→cls, file→file, else→sym |
| FR-003 | IMPLEMENTED | `build_helpers/loaders.py:127-134`, `build_helpers/entity_processor.py:100-125`, `build_mcp_db.py:296-308` | Signature map loaded as raw dict, used in `merge_entities()`, three artifacts are pre-built inputs |
| FR-004 | IMPLEMENTED | `build_helpers/entity_processor.py:163-169` | Collision check with `RuntimeError` on duplicate new_id |
| FR-005 | IMPLEMENTED | `build_mcp_db.py:129-153` | `populate_entities` carries brief, details, params, returns, notes, rationale, usages from merged doc |
| FR-006 | IMPLEMENTED | `build_helpers/entity_ids.py:1-95`, `build_helpers/artifact_models.py:44-51` | Old `split_entity_id` import removed; `SignatureMap` class removed; new `compute_entity_id` + `kind_to_prefix` replace them. `EntityID.from_str` inlined the split logic. |
| FR-007 | IMPLEMENTED | `server/db_models.py:1-78` | Entity table has no `compound_id`, `member_id`, `doc_state`, `doc_quality` columns |
| FR-008 | IMPLEMENTED | `server/db_models.py:101-110` | Capability table has no `doc_quality_dist` column |
| FR-009 | IMPLEMENTED | `server/db_models.py:28` | `entity_id: str = Field(primary_key=True, description="Deterministic {prefix}:{7 hex} ID")` |
| FR-010 | IMPLEMENTED | `server/db_models.py:32` | `signature` column present, no UNIQUE constraint, description says "not unique, indexed" |
| FR-011 | IMPLEMENTED | `server/tools/entity.py` | `resolve_entity` tool function fully removed; `EXPECTED_TOOLS` in test_server.py excludes it |
| FR-012 | IMPLEMENTED | `server/tools/entity.py:61-65`, `server/tools/graph.py:78-80`, `server/tools/behavior.py:109-111`, `server/tools/capability.py:268-270` | All tools take only `entity_id: str` as required param, no `signature` |
| FR-013 | IMPLEMENTED | `server/models.py` diff | `ResolutionEnvelope` class fully removed |
| FR-014 | IMPLEMENTED | `server/tools/search.py:30-38`, `server/search.py` diff | `min_doc_quality` parameter removed from search tool and all internal functions |
| FR-015 | IMPLEMENTED | `server/models.py:191-196` | `CapabilitySummary` and `CapabilityDetail` no longer have `doc_quality_dist` |
| FR-016 | IMPLEMENTED | `server/enums.py` diff, `server/tools/behavior.py:1-22` | `DocQuality` and `DocState` enums removed; behavior.py no longer imports them |
| FR-017 | IMPLEMENTED | `server/prompts.py:1-178` | Prompts reference search → entity_id pattern; no mention of `resolve_entity` |
| FR-018 | IMPLEMENTED | `server/models.py:27-44` | `EntitySummary` has no `doc_state` or `doc_quality` fields |
| FR-019 | IMPLEMENTED | `server/models.py:60-106` | `EntityDetail` has no `compound_id`, `member_id`, `doc_state`, `doc_quality` fields |
| FR-020 | IMPLEMENTED | `server/tools/search.py`, `server/search.py` | Search is the sole path; resolver still exists internally but no tool exposes it |

---

## Metrics

- **Files audited**: 28
- **Findings**: 0 critical, 1 high, 5 medium, 4 low
- **Spec coverage**: 20 / 20 requirements implemented
- **Constitution compliance**: 2 violations (LOW — pre-existing `__future__` imports) across 5 principles checked

---

## Remediation Decisions

For each item below, choose an action:
- **fix**: Create a remediation task to fix the implementation
- **spec**: Update the spec to match the implementation (if the implementation is actually correct)
- **skip**: Accept the finding and take no action
- **split**: Fix part in implementation, update part in spec (explain which)

### 1. [SD-001] EntitySummary.entity_id description says "Internal Doxygen ID"
**Location**: `server/models.py:30`
**Spec says**: Entity IDs are deterministic `{prefix}:{7 hex}` format (FR-009)
**Code does**: Field description still references Doxygen IDs — agent-visible metadata is stale

Action: **fix** → T038

---

### MEDIUM / LOW — All Promoted

- **OE-001** (MEDIUM): `build_id_map()` in `entity_ids.py:50-95` is dead code → **fix** → T039
- **SF-001** (MEDIUM): `build_mcp_db.py:108-113` swallows index creation failures → **fix** → T040
- **SF-002** (MEDIUM): `resolver.py:283` broad `except Exception` silently degrades → **fix** → T041
- **SF-003** (MEDIUM): `search.py:155-157` broad `except Exception` silently degrades → **fix** → T042
- **CQ-001** (MEDIUM): `build_mcp_db.py:154` `hasattr` defensive check → **fix** → T043
- **CV-001** (LOW): `resolver.py:17` pre-existing `from __future__ import annotations` → **fix** → T044
- **CV-002** (LOW): `search.py:19` pre-existing `from __future__ import annotations` → **fix** → T045
- **CQ-002** (LOW): `loaders.py:7` stale module docstring → **fix** → T046
- **CQ-003** (LOW): `entity_processor.py:57` minor comment phrasing → **fix** → T047

---

## Spec Amendments

_(None)_

---

## Remediation Tasks

10 remediation tasks created (T038–T047) in `tasks.md` under **Audit Remediation**.

- 0 spec updates applied
- 0 findings skipped

Run `/speckit.implement` to execute remediation tasks.
