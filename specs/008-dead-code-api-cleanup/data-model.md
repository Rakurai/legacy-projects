# Data Model: Dead Code Purge & API Cleanup

**Phase 1 output** | **Date**: 2026-03-19

This document describes the **target state** of the data model after the cleanup. It captures only the changes — fields/entities being removed or modified.

## Entity Changes

### Entity (db_models.py)

**Removed fields**:

| Field | Type | Reason |
|-------|------|--------|
| `side_effect_markers` | `JSONB` | Unvalidated heuristic data (gaps §2) |

**Preserved fields** (no change): `entity_id`, `name`, `signature`, `kind`, `entity_type`, `file_path`, `body_start_line`, `body_end_line`, `decl_file_path`, `decl_line`, `definition_text`, `source_text`, `brief`, `details`, `params`, `returns`, `notes`, `rationale`, `usages`, `capability`, `is_entry_point`, `fan_in`, `fan_out`, `is_bridge`, `embedding`, `search_vector`

### EntityDetail (models.py)

**Removed fields**:

| Field | Reason |
|-------|--------|
| `side_effect_markers` | Removed from Entity |
| `provenance` | Never consumed by agents (gaps §3) |

### EntitySummary (models.py)

**Removed fields**:

| Field | Reason |
|-------|--------|
| `provenance` | Never consumed by agents |

### EntityNeighbor (models.py)

**Removed fields**:

| Field | Reason |
|-------|--------|
| `provenance` | Never consumed by agents |

## Capability Changes

### Capability (db_models.py)

No changes. `doc_quality_dist` was already absent.

### CapabilitySummary (models.py)

**Removed fields**: `provenance`

### CapabilityDetail (models.py)

**Removed fields**: `provenance`

## Behavior Model Changes

### BehaviorSlice (models.py)

**Removed fields**:

| Field | Reason |
|-------|--------|
| `side_effects` | `dict[str, list[SideEffectMarker]]` — entire side-effect system removed |
| `provenance` | Never consumed |

### GlobalTouch (models.py)

**Removed fields**: `provenance`

### CapabilityTouch (models.py)

**Removed fields**: `provenance`

### StateTouchesResponse (behavior.py)

**Removed fields**:

| Field | Reason |
|-------|--------|
| `direct_side_effects` | `list[SideEffectMarker]` — side-effect system removed |
| `transitive_side_effects` | `list[SideEffectMarker]` — side-effect system removed |

### SearchResult (models.py)

**Removed fields**: `provenance`

## Deleted Models

| Model | File | Reason |
|-------|------|--------|
| `SideEffectMarker` | models.py | Side-effect system removed |
| `HotspotsResponse` | tools/behavior.py | `get_hotspots` tool removed |
| `RelatedFilesResponse` | tools/graph.py | `get_related_files` tool removed |
| `FileSummaryResponse` | tools/entity.py | `get_file_summary` tool removed |
| `ListFileEntitiesResponse` | tools/entity.py | `list_file_entities` tool removed |

## Deleted Enums

| Enum | File | Reason |
|------|------|--------|
| `SideEffectCategory` | enums.py | Only consumer was `SideEffectMarker` |
| `Confidence` | enums.py | Only consumer was `SideEffectMarker` |
| `Provenance` | enums.py | Removed from all models |
| `HotspotMetric` | enums.py | Only consumer was `get_hotspots` tool |

## EntryPoint Table Changes

### EntryPoint (db_models.py)

**Modified fields**:

| Field | Change | Reason |
|-------|--------|--------|
| `capabilities` | JSONB enriched at build time | Must contain **transitive** capabilities (from call cone), not just direct |

The build pipeline must compute the call cone for each entry point and populate `capabilities` with all capability names touched transitively, enabling `get_capability_detail` to query entry points that route into a given capability.

## State Transitions

No state machines affected. The changes are purely subtractive (field removal) with one build-time enrichment (EntryPoint.capabilities).

## Validation Rules

No new validation rules. Existing validators on `EntitySummary` (non-empty `signature` and `name`) are preserved.
