# Research: Dead Code Purge & API Cleanup

**Phase 0 output** | **Date**: 2026-03-19

## 1. Dead Fields — Current State Inventory

### Already absent (no action needed)

| Field | Expected in | Finding |
|-------|------------|---------|
| `compound_id` | `Entity` (db_models) | Does not exist. Already removed or never added |
| `member_id` | `Entity` (db_models) | Does not exist. Already removed or never added |
| `doc_quality_dist` | `Capability` (db_models) | Does not exist |
| `doc_quality` | `Entity` (db_models) | Does not exist |
| `doc_state` | `Entity` (db_models) | Does not exist |
| `DocQuality` | enums.py | Does not exist |
| `DocState` | enums.py | Does not exist |

**Decision**: FR-001, FR-002, FR-005 are already satisfied at the DB/model layer. Only API models and converters need cleanup for any remaining references.  
**Rationale**: Previous spec (005) already removed these from the DB schema. Remaining references are in response models and build helpers.

### Still present (action required)

| Field / Symbol | Files | Lines |
|---------------|-------|-------|
| `side_effect_markers` (JSONB) | `db_models.py` Entity | L73-78 |
| `side_effect_markers` on `EntityDetail` | `models.py` | L103 |
| `side_effect_markers` pass-through | `converters.py` | L62 |
| `side_effect_markers` in resource | `resources.py` | L187 |
| `SideEffectCategory` enum | `enums.py` | L57-62 |
| `Confidence` enum | `enums.py` | L71-75 |
| `Provenance` enum | `enums.py` | L82-89 |
| `HotspotMetric` enum | `enums.py` | L153-158 |
| `SideEffectMarker` model | `models.py` | L152-158 |
| `provenance` field | `models.py` on 10+ models | Throughout |
| `side_effects` dict on `BehaviorSlice` | `models.py` | L185 |
| `SIDE_EFFECT_FUNCTIONS` dict | `entity_processor.py` | L27 |
| `MergedEntity.side_effect_markers` | `entity_processor.py` | L101 |
| `compute_side_effect_markers()` | `graph_loader.py` | L175-248 |
| `_SIDE_EFFECT_BFS_DEPTH` constant | `graph_loader.py` | L22 |
| `compute_side_effect_markers` import + call | `build_mcp_db.py` | L39, L309 |
| `side_effect_markers=` assignment | `build_mcp_db.py` | L149 |

## 2. Confidence Enum — Corrected Finding

**Original assumption** (from clarification session): `Confidence` is used by `GlobalTouch` and must be preserved.

**Actual finding**: `Confidence` is used **only** by `SideEffectMarker` (models.py L157) and `_extract_side_effects_for_entities` (behavior.py L88). `GlobalTouch` has `access_type: AccessType` but **no** `confidence` field.

**Decision**: Remove `Confidence` along with `SideEffectMarker`.  
**Rationale**: No retained model or tool uses `Confidence`. Removing it is safe.

## 3. Tool Removal — Impact Analysis

### get_hotspots

- **File**: `server/tools/behavior.py` L313-367
- **Response model**: `HotspotsResponse` (behavior.py L62-65)
- **Enum dependency**: `HotspotMetric` — only used by this tool; remove with it
- **Tests**: `test_behavior_tools.py` L136-196 (6 tests)
- **Risk**: None. `search` with `kind`/`capability` filters + DB ordering provides equivalent functionality

### get_related_files

- **File**: `server/tools/graph.py` L349-398
- **Response model**: `RelatedFilesResponse` (graph.py L71-75)
- **Tests**: `test_graph_tools.py` L145-163 (2 tests)
- **Risk**: None. Only returns outgoing INCLUDES edges; minimal utility

### get_file_summary

- **File**: `server/tools/entity.py` L210-253
- **Response model**: `FileSummaryResponse` (entity.py L35-40)
- **Tests**: `test_entity_tools.py` L118-136 (2 tests)
- **Risk**: None. File-centric workflow not used by agents

### list_file_entities

- **File**: `server/tools/entity.py` L168-208
- **Response model**: `ListFileEntitiesResponse` (entity.py L44-48)
- **Tests**: `test_entity_tools.py` L90-117 (3 tests)
- **Risk**: None. `search` with semantic queries serves entity-first workflows better

## 4. Entry Point / Capability Semantics

### Current behavior (broken)

`get_capability_detail` at capability.py L111-116 queries:
```python
select(EntryPoint)
    .join(Entity, Entity.entity_id == EntryPoint.entity_id)
    .where(Entity.capability == capability)
```

Most entry points have `capability=NULL` (or a different capability like "commands"), so this returns **empty or wrong results** for most capabilities.

### Available data sources

1. **`EntryPoint.capabilities` JSONB**: Build pipeline populates with `[merged.capability]` — only the direct capability. Does NOT include transitive capabilities exercised via call cone.

2. **`capability_graph.json` → `entry_points_using`**: This field is an **integer count** (e.g., `148` for combat), NOT a list of entry point names. Cannot be used directly.

3. **`get_entry_point_info` tool**: Already computes transitive capabilities correctly at runtime using `compute_call_cone()`. But this is per-entry-point, not per-capability.

### Recommended approach

**Decision**: Enrich `EntryPoint.capabilities` JSONB at build time with transitive capability data (from call cone analysis), then query `WHERE capability_name = ANY(capabilities)` in `get_capability_detail`.

**Rationale**: The build pipeline already has call cone computation available. Moving the computation to build time avoids expensive runtime graph traversal per-capability-detail request. The `EntryPoint` table already has the JSONB column — it just needs richer data.

**Alternative considered**: Runtime call cone computation per-capability. Rejected because it's O(entry_points × capability) at query time.

## 5. Contract Alignment — Parameter Trace

### search: `limit` → `top_k`

Rename scope:
- `tools/search.py` L38: parameter signature `limit: int = 20` → `top_k: int = 10`
- `tools/search.py` L49: log call `limit=limit` → `top_k=top_k`
- `tools/search.py` L67: pass-through `limit=limit` → `limit=top_k`
- `server/search.py`: internal functions keep `limit` parameter name (internal API)

**Decision**: Rename only at the tool surface (tools/search.py). Internal search functions retain `limit` parameter name — it's an internal implementation detail.

### get_class_hierarchy: add `direction` parameter

- Graph helper (`server/graph.py` L231-264) already separates base_classes (outgoing INHERITS) and derived_classes (incoming INHERITS) into distinct collection loops
- Add `direction: "ancestors" | "descendants" | "both" = "both"` parameter to both tool and graph helper
- Gate each collection loop on direction value
- ~5 lines changed in graph helper, ~3 lines in tool

### get_dependencies: change default `direction`

- Current: `direction = "both"` (tools/graph.py L181)
- Contract: `direction = "outgoing"`
- Change: update default in parameter annotation only (1 line)

### get_related_entities: `limit` → `limit_per_type`

- Current: global `limit=100` applied before grouping (loses rare relationship types)
- Needed: remove early truncation, group first, then truncate per group to `limit_per_type=20`
- ~15 lines restructured in tools/graph.py

## 6. Test Impact Summary

| Test file | Tests to remove | Tests to modify | Tests to add |
|-----------|----------------|-----------------|-------------|
| `test_behavior_tools.py` | 6 hotspot tests, 2 side-effect tests | `test_behavior_slice` (remove side_effects assertions) | None |
| `test_entity_tools.py` | 5 tests (file_summary + list_file_entities) | None | None |
| `test_graph_tools.py` | 2 related_files tests | None | direction tests for get_class_hierarchy |
| `test_search.py` | 1 provenance test | Remove provenance assertions | None |
| `test_search_tool.py` | None | Rename `limit` → `top_k` in calls | None |
| `test_converters.py` | Provenance-specific tests | Remove provenance assertions | None |
| `test_search_units.py` | `_provenance_for` tests | Remove provenance imports/assertions | None |
| `test_resources.py` | None | Remove side_effect_markers assertions | None |
| `conftest.py` | None | Remove `side_effect_markers` from fixtures | None |

**Net change**: ~13 tests removed, ~8 tests modified, ~1-2 tests added (direction filtering).
