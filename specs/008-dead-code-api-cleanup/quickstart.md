# Quickstart: Dead Code Purge & API Cleanup

**Phase 1 output** | **Date**: 2026-03-19

## Implementation Order

This spec is pure subtraction + contract alignment. No new features. Recommended implementation order follows dependency chains (remove leaves first, then update consumers).

### Step 1: Remove enums (no dependents after model cleanup)

Delete from `server/enums.py`:
- `SideEffectCategory`
- `Confidence`
- `Provenance`
- `HotspotMetric`

### Step 2: Remove dead models

Delete from `server/models.py`:
- `SideEffectMarker` class
- `provenance` field from all 10 models
- `side_effects` field from `BehaviorSlice`

### Step 3: Remove dead DB fields

Delete from `server/db_models.py`:
- `Entity.side_effect_markers` column

### Step 4: Update converters

In `server/converters.py`:
- Remove `provenance=` arguments from all three converter functions
- Remove `side_effect_markers=` from `entity_to_detail()`

### Step 5: Update search

In `server/search.py`:
- Remove `Provenance` import
- Remove `provenance=` from search result construction

In `server/tools/search.py`:
- Rename parameter `limit` → `top_k`, default `20` → `10`

### Step 6: Remove tools

In `server/tools/behavior.py`:
- Delete `get_hotspots` function and `HotspotsResponse`
- Delete `_extract_side_effects_for_entities()` function
- Remove side-effect extraction from `get_behavior_slice` and `get_state_touches`
- Remove `StateTouchesResponse.direct_side_effects` / `transitive_side_effects`
- Remove `SideEffectCategory`, `Confidence`, `Provenance`, `HotspotMetric` imports

In `server/tools/entity.py`:
- Delete `get_file_summary` function, `FileSummaryResponse`
- Delete `list_file_entities` function, `ListFileEntitiesResponse`

In `server/tools/graph.py`:
- Delete `get_related_files` function, `RelatedFilesResponse`
- Add `direction` parameter to `get_class_hierarchy`
- Change `get_dependencies` default direction to `"outgoing"`
- Restructure `get_related_entities` to use `limit_per_type`

### Step 7: Fix entry point semantics

In `server/tools/capability.py`:
- Remove `capability` parameter from `list_entry_points`
- Fix `get_capability_detail` entry_points query to use `EntryPoint.capabilities` JSONB

In `build_mcp_db.py`:
- Enrich `EntryPoint.capabilities` at build time with transitive capabilities from call cone

### Step 8: Remove build pipeline dead code

In `build_helpers/entity_processor.py`:
- Delete `SIDE_EFFECT_FUNCTIONS` dict
- Delete `MergedEntity.side_effect_markers` attribute

In `build_helpers/graph_loader.py`:
- Delete `compute_side_effect_markers()` function
- Delete `_SIDE_EFFECT_BFS_DEPTH` constant
- Delete `SIDE_EFFECT_FUNCTIONS` import

In `build_mcp_db.py`:
- Delete `compute_side_effect_markers` import and call
- Delete `side_effect_markers=` assignment in `populate_entities()`

### Step 9: Update resources

In `server/resources.py`:
- Remove `side_effect_markers` from entity resource dict

### Step 10: Update tests

- Remove tests for deleted tools (13 tests)
- Update fixtures in `conftest.py` (remove `side_effect_markers`)
- Update assertions that check `provenance` fields
- Rename `limit` → `top_k` in search test calls
- Add `direction` parameter tests for `get_class_hierarchy`

## Verification

```bash
# Run tests
cd mcp/doc_server && uv run pytest tests/ -v --color=never

# Type check
cd mcp/doc_server && uv run mypy server/

# Lint
cd mcp/doc_server && uv run ruff check .

# Verify no dead references remain
grep -rn "DocQuality\|DocState\|SideEffectCategory\|Provenance\|compute_doc_quality\|compute_side_effect_markers\|doc_quality_sort_key\|_provenance_for\|HotspotMetric" mcp/doc_server/server/ mcp/doc_server/build_helpers/ mcp/doc_server/build_mcp_db.py

# Verify tool count (should be 15)
cd mcp/doc_server && uv run python -c "from server.app import mcp; print(len(mcp._tool_manager._tools))"
```
