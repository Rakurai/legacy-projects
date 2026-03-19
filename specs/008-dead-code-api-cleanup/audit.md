# Implementation Audit: Dead Code Purge & API Cleanup

**Date**: 2026-03-19
**Branch**: `008-dead-code-api-cleanup`
**Base**: `master` (all changes uncommitted)
**Files audited**: 28

---

## Findings

| ID | Category | Severity | Location | Description | Quoted Evidence |
|----|----------|----------|----------|-------------|-----------------|
| CV-001 | Constitution Violation | CRITICAL | `build_helpers/entity_processor.py:336` | Dead comment references removed `side_effect_markers` — violates "Source Reflects Current Truth" | `# Note: fan_in, fan_out, is_bridge, and side_effect_markers` |
| CV-002 | Constitution Violation | CRITICAL | `tests/test_behavior_tools.py:7` | Module docstring lists removed tool `get_hotspots` — violates "Source Reflects Current Truth" | `- get_hotspots` |
| CV-003 | Constitution Violation | CRITICAL | `server/tools/capability.py:66` | `list_capabilities` docstring references removed "doc quality distribution" — violates "Source Reflects Current Truth" | `function count, stability, and doc quality distribution.` |
| CV-004 | Constitution Violation | HIGH | `server/tools/graph.py:237-239` | Newly added `direction` parameter on `get_class_hierarchy` typed as `str` instead of `Literal["ancestors", "descendants", "both"]` — violates "Types Are Contracts" (narrow types aggressively; use Literal) | `direction: Annotated[str, Field(description="Which direction: ancestors, descendants, or both")]` |
| SF-001 | Silent Failure | HIGH | `server/tools/graph.py:255-256` | Invalid `direction` value (e.g., `"foo"`) silently returns empty base_classes AND derived_classes — no validation, no error raised | `base_ids = hierarchy["base_classes"] if direction in ("ancestors", "both") else []` |
| PH-001 | Phantom Implementation | MEDIUM | `server/tools/graph.py:345-348` | `TruncationMetadata.total_available` set to post-truncation count, identical to `node_count`. When groups are capped, `total_available` should reflect the pre-truncation total so agents know data was lost | `truncation=TruncationMetadata(truncated=truncated, total_available=total, node_count=total,)` |

---

## Requirement Traceability

| Requirement | Status | Implementing Code | Notes |
|-------------|--------|-------------------|-------|
| FR-001 | IMPLEMENTED | N/A (pre-satisfied) | `doc_quality`/`doc_state` already absent |
| FR-002 | IMPLEMENTED | N/A (pre-satisfied) | `doc_quality_dist` already absent |
| FR-003 | IMPLEMENTED | `db_models.py`, `models.py`, `converters.py`, `resources.py`, `conftest.py` | `side_effect_markers` removed from all layers |
| FR-004 | IMPLEMENTED | `models.py`, `converters.py`, `search.py`, `behavior.py`, `capability.py` | `provenance` field removed from all response models |
| FR-005 | IMPLEMENTED | N/A (pre-satisfied) | `compound_id`/`member_id` already absent |
| FR-006 | IMPLEMENTED | `enums.py` | `SideEffectCategory`, `Confidence`, `Provenance`, `HotspotMetric` removed. `DocState`/`DocQuality` pre-absent |
| FR-007 | IMPLEMENTED | `entity_processor.py`, `graph_loader.py`, `build_mcp_db.py` | Build no longer computes or persists removed fields |
| FR-008 | IMPLEMENTED | N/A (pre-satisfied) | Resolver already uses `fan_in` |
| FR-009 | IMPLEMENTED | `behavior.py` | `get_hotspots` and `HotspotsResponse` removed |
| FR-010 | IMPLEMENTED | `graph.py` | `get_related_files` and `RelatedFilesResponse` removed |
| FR-011 | IMPLEMENTED | `entity.py` | `get_file_summary` and `FileSummaryResponse` removed |
| FR-012 | IMPLEMENTED | `entity.py` | `list_file_entities` and `ListFileEntitiesResponse` removed |
| FR-013 | IMPLEMENTED | `behavior.py`, `entity.py`, `graph.py` | All removed-tool response models deleted |
| FR-014 | IMPLEMENTED | `capability.py:110-115`, `build_mcp_db.py:272-290` | JSONB containment query + BFS capability enrichment at build time |
| FR-015 | IMPLEMENTED | `capability.py:239` | `capability` parameter removed from `list_entry_points` |
| FR-015a | IMPLEMENTED | `capability.py` docstrings | Docstrings direct agents to `get_capability_detail` |
| FR-016 | IMPLEMENTED | `capability.py:248-252`, `capability.py:92-97` | Docstrings explain `capability=NULL` design |
| FR-017 | IMPLEMENTED | `search.py:38` | `top_k` parameter with default 10 |
| FR-018 | PARTIAL | `graph.py:234-241` | `direction` parameter added to `get_class_hierarchy` with correct values and default — but typed as `str`, not `Literal`. Invalid values silently accepted (CV-004, SF-001) |
| FR-019 | IMPLEMENTED | `graph.py:168` | Default changed to `"outgoing"` |
| FR-020 | IMPLEMENTED | `graph.py:278` | `limit_per_type` with default 20, per-group truncation |

---

## Metrics

- **Files audited**: 28
- **Findings**: 3 critical, 2 high, 1 medium, 0 low
- **Spec coverage**: 20 / 20 requirements implemented (1 partial — FR-018)
- **Constitution compliance**: 4 violations across 5 principles checked

---

## Remediation Decisions

For each item below, choose an action:
- **fix**: Create a remediation task to fix the implementation
- **spec**: Update the spec to match the implementation (if the implementation is actually correct)
- **skip**: Accept the finding and take no action
- **split**: Fix part in implementation, update part in spec (explain which)

### 1. [CV-001] Dead comment references `side_effect_markers`
**Location**: `build_helpers/entity_processor.py:336`
**Constitution says**: Source reflects current truth — no stale commentary
**Code does**: `# Note: fan_in, fan_out, is_bridge, and side_effect_markers`

Action: fix / spec / skip / split

### 2. [CV-002] Module docstring lists removed `get_hotspots`
**Location**: `tests/test_behavior_tools.py:7`
**Constitution says**: Source reflects current truth — no stale commentary
**Code does**: Module docstring lists `get_hotspots` as a tested tool

Action: fix / spec / skip / split

### 3. [CV-003] Docstring references removed "doc quality distribution"
**Location**: `server/tools/capability.py:66`
**Constitution says**: Source reflects current truth — no stale commentary
**Code does**: `function count, stability, and doc quality distribution.`

Action: fix / spec / skip / split

### 4. [CV-004 + SF-001] `direction` param on `get_class_hierarchy` is `str`, not `Literal`
**Location**: `server/tools/graph.py:237-239`
**Constitution says**: Types Are Contracts — narrow types aggressively, use Literal
**Code does**: `direction: Annotated[str, ...]` — accepts any string, invalid values silently return empty results
**Spec says**: FR-018 requires values `"ancestors"`, `"descendants"`, `"both"`

Action: fix / spec / skip / split

### 5. [PH-001] `total_available` in `get_related_entities` shows post-truncation count
**Location**: `server/tools/graph.py:345-348`
**Spec says**: FR-020 — per-group truncation replacing global limit
**Code does**: `total_available=total` where `total` is the sum after truncation. Agents cannot distinguish "5 results available, 5 returned" from "50 available, 5 returned after capping"

Action: fix / spec / skip / split

### MEDIUM / LOW Summary

No additional medium/low findings beyond PH-001 (listed above as a decision item due to functional impact).

All six findings are actionable. Would you like to promote or demote any?
