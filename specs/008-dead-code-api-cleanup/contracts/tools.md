# Tool Contract Changes: 008 Dead Code Purge & API Cleanup

**Phase 1 output** | **Date**: 2026-03-19

This document describes changes to the tool contract relative to `specs/v1/contracts/tools.md`. After this spec, the canonical contract should be updated in-place.

## Tool Count

**Before**: 19 tools  
**After**: 15 tools

## Removed Tools

### get_hotspots (was: Behavior Analysis)

**Removed**. The `underdocumented` metric depended on removed `doc_quality`. Other metrics (`fan_in`, `fan_out`, `bridge`) are achievable via `search` with appropriate filters. Not part of any established agent workflow.

### get_related_files (was: Graph Exploration)

**Removed**. Only returned outgoing INCLUDES edges (1,656 total). Returned empty for most files. Agents navigate entity-first.

### get_file_summary (was: Entity Lookup)

**Removed**. Per-file entity counts; no clear agent use case.

### list_file_entities (was: Entity Lookup)

**Removed**. File-centric entity list; equivalent via `search`.

---

## Modified Tools

### search

**Parameter change**: `limit` → `top_k`, default `20` → `10`

```diff
- limit?: number = 20    // Maximum results
+ top_k?: number = 10    // Number of results
```

**Response change**: `provenance` field removed from `SearchResult`.

### get_class_hierarchy

**New parameter**: `direction`

```diff
  {
    entity_id: string,
+   direction?: "ancestors" | "descendants" | "both" = "both",
  }
```

When `direction="ancestors"`: `derived_classes` array is empty.  
When `direction="descendants"`: `base_classes` array is empty.  
When `direction="both"` (default): both arrays populated (same as current behavior).

### get_dependencies

**Default change**: `direction` default `"both"` → `"outgoing"`

```diff
- direction?: "incoming" | "outgoing" | "both" = "both"
+ direction?: "incoming" | "outgoing" | "both" = "outgoing"
```

### get_related_entities

**Parameter change**: `limit` → `limit_per_type`, default `100` → `20`

```diff
- limit?: number = 100     // Maximum results (global)
+ limit_per_type?: number = 20  // Maximum results per relationship group
```

Truncation semantics change: truncation is per-group, not global. Response `truncation` reflects whether any group was capped.

### list_entry_points

**Removed parameter**: `capability`

```diff
  {
-   capability?: string,
    name_pattern?: string,
    limit?: number = 100
  }
```

Agents must use `get_capability_detail` to find entry points routing into a capability.

### get_capability_detail

**Semantic change**: `entry_points` field now returns entry points that **route into** the capability (via transitive call cone), not entry points **classified as** the capability.

Query changes from `Entity.capability == capability` to `EntryPoint.capabilities` JSONB containment (enriched at build time with transitive capability data).

---

## Response Model Changes (all tools)

The `provenance` field is removed from all response models:
- `EntitySummary`
- `EntityNeighbor`
- `EntityDetail`
- `SearchResult`
- `CapabilityTouch`
- `GlobalTouch`
- `BehaviorSlice`
- `CapabilitySummary`
- `CapabilityDetail`

The `side_effect_markers` field is removed from `EntityDetail`.

The `side_effects` dict is removed from `BehaviorSlice`.

The `direct_side_effects` and `transitive_side_effects` lists are removed from `StateTouchesResponse`.

---

## Surviving Tool Inventory (15 tools)

### Entity Lookup (2 tools)
1. `get_entity`
2. `get_source_code`

### Search (1 tool)
3. `search` (param: `top_k`, default 10)

### Graph Exploration (4 tools)
4. `get_callers`
5. `get_callees`
6. `get_dependencies` (default direction: `"outgoing"`)
7. `get_class_hierarchy` (new param: `direction`)
8. `get_related_entities` (param: `limit_per_type`, default 20)

### Behavior Analysis (2 tools)
9. `get_behavior_slice`
10. `get_state_touches`

### Capability System (5 tools)
11. `list_capabilities`
12. `get_capability_detail`
13. `compare_capabilities`
14. `list_entry_points` (no `capability` param)
15. `get_entry_point_info`
