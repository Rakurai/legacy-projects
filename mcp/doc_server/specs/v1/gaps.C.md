# Phase C — Dead Code Purge & API Cleanup

> Remove everything the server declares but doesn't use, then fix remaining API contract gaps.
> Depends on Phases A and B (model layer stable, data pipeline correct).
>
> Items: gaps.md §1, §7, §8, §10, §11, §2, §3

---

## 1. `doc_quality` / `doc_state` Dead Code Removal (gaps §1)

Spec 005 dropped `doc_state` and `doc_quality` from the `entities` table and `doc_quality_dist` from `capabilities`. The SQLModel classes still define these fields, and code throughout the server still reads/writes them. `compute_doc_quality()` is dead code.

**Action:** Remove all `doc_quality`, `doc_state`, `DocQuality`, `DocState`, and `doc_quality_dist` references from the codebase.

### File inventory

| File | What to remove |
|------|----------------|
| `server/db_models.py` | `Entity.doc_state`, `Entity.doc_quality` fields; `Capability.doc_quality_dist` field |
| `server/enums.py` | `DocState` enum, `DocQuality` enum |
| `server/models.py` | `doc_state`, `doc_quality` on `EntitySummary`; `doc_state`, `doc_quality` on `EntityDetail`; `doc_quality_dist` on `CapabilitySummary` and `CapabilityDetail` |
| `server/converters.py` | `doc_state`/`doc_quality` assignments in `entity_to_summary()` and `entity_to_detail()`; `doc_quality_dist` in `capability_to_summary()`; `DocState`/`DocQuality` imports; provenance derivation currently uses `doc_state` — replace with `entity.details is not None` check |
| `server/util.py` | `doc_quality_sort_key()` function and `DocQuality` import; usage in `resolve_entity_id()` — replace ORDER BY with `Entity.fan_in.desc()` |
| `server/resolver.py` | `doc_quality_sort_key` import; three usages in `_resolve_by_signature`, `_resolve_by_name`, `_resolve_by_prefix` — replace with `Entity.fan_in.desc()` |
| `server/tools/entity.py` | `doc_quality_sort_key` import and usage in `get_entity`; `doc_quality_distribution` field on `FileSummaryResponse` and its computation in `get_file_summary` |
| `server/tools/behavior.py` | `DocQuality` import; `HotspotMetric.UNDERDOCUMENTED` filter uses `Entity.doc_quality` — replace with `Entity.brief.is_(None)` |
| `server/resources.py` | `doc_quality_dist` on capability resources; `doc_state`, `doc_quality` on entity resource; `entities_by_doc_quality` stats query |
| `build_helpers/entity_processor.py` | `compute_doc_quality()` function; `self.doc_quality` on `MergedEntity`; `DocQuality`/`DocState` imports; docstring mentions |
| `build_mcp_db.py` | `compute_doc_quality` import and call; `doc_state=` and `doc_quality=` assignments in `populate_entities()`; `cap_quality_dist` computation block in `populate_capabilities()` |
| Tests | `doc_quality`, `doc_state`, `doc_quality_dist` in fixtures and assertions across `conftest.py`, `test_behavior_tools.py`, `test_search_units.py`, `test_converters.py`, `test_resolution.py`, `test_search.py`, `test_capability_tools.py` |

---

## 2. Side-Effect Markers — Remove (gaps §7)

<!-- spec 008: RESOLVED — side_effect_markers JSONB column, SideEffectCategory/Confidence enums, SideEffectMarker model, SIDE_EFFECT_FUNCTIONS dict, compute_side_effect_markers(), and all related code removed -->

### File inventory

| File | What to remove |
|------|----------------|
| `server/db_models.py` | `Entity.side_effect_markers` JSONB field |
| `server/enums.py` | `SideEffectCategory` enum, `Confidence` enum (keep `AccessType` — used by `GlobalTouch`) |
| `server/models.py` | `SideEffectMarker` model; `side_effect_markers` on `EntityDetail`; `side_effects` dict on `BehaviorSlice`; `Confidence`/`SideEffectCategory` imports |
| `server/converters.py` | `side_effect_markers=entity.side_effect_markers` in `entity_to_detail()` |
| `server/tools/behavior.py` | `_extract_side_effects_for_entities()` function; `SideEffectCategory`/`Confidence` imports; `direct_side_effects`/`transitive_side_effects` on `StateTouchesResponse`; `side_effects` construction in `get_behavior_slice`; side-effect extraction calls in `get_state_touches`; indirect callee fetch block (only purpose was side-effect extraction) |
| `server/resources.py` | `side_effect_markers` on entity resource dict |
| `build_helpers/entity_processor.py` | `SIDE_EFFECT_FUNCTIONS` dict (~20 lines); `self.side_effect_markers` on `MergedEntity`; docstring mentions |
| `build_helpers/graph_loader.py` | `compute_side_effect_markers()` function (~70 lines); `SIDE_EFFECT_FUNCTIONS` import; `_SIDE_EFFECT_BFS_DEPTH` constant |
| `build_mcp_db.py` | `compute_side_effect_markers` import and call; `side_effect_markers=` assignment in `populate_entities()` |
| Tests | `side_effect_markers` in fixtures and assertions across `conftest.py`, `test_behavior_tools.py` |

---

## 3. Provenance Labels — Remove (gaps §8)

<!-- spec 008: RESOLVED — Provenance enum (7 members), provenance field on all response models, _provenance_for() helper, and all provenance derivation logic removed -->

### File inventory

| File | What to remove |
|------|----------------|
| `server/enums.py` | `Provenance` enum (7 members) |
| `server/models.py` | `provenance` field on `EntitySummary`, `EntityNeighbor`, `EntityDetail`, `SearchResult`, `CapabilityTouch`, `GlobalTouch`, `SideEffectMarker` (removed in §2), `BehaviorSlice`, `CapabilitySummary`, `CapabilityDetail`; `Provenance` import; FR-044 docstring reference |
| `server/converters.py` | `provenance=Provenance.PRECOMPUTED` in `entity_to_summary()`; `provenance=Provenance.DOXYGEN_EXTRACTED if ...` in `entity_to_detail()` (also removes doc_state dependency); `provenance=Provenance.PRECOMPUTED` in `capability_to_summary()`; `Provenance` import |
| `server/search.py` | `_provenance_for()` helper function; `provenance=_provenance_for(entity)` in search result construction; `Provenance` import |
| `server/tools/behavior.py` | `provenance=Provenance.INFERRED` on BehaviorSlice construction; `provenance=Provenance.HEURISTIC` on side-effect markers (removed in §2); `Provenance` import |
| `server/tools/capability.py` | `provenance="precomputed"` in capability detail construction |
| Tests | `TestProvenanceFor` class and 3 provenance-specific tests in `test_converters.py`; `_provenance_for` import and tests in `test_search_units.py`; provenance assertions in `test_search.py` and `test_converters.py` |

---

## 4. `compound_id` / `member_id` — Remove from Schema and API (gaps §10)

The live database has already dropped `compound_id` and `member_id` columns (confirmed: `UndefinedColumnError: column "compound_id" does not exist`). These are Doxygen internal identifiers used during the build pipeline to join entities with their doc_db entries. They should not propagate past the build stage.

However, `db_models.py` still declares `Entity.compound_id` and `Entity.member_id`, and `EntityDetail` in `models.py` exposes them in the API response. The build pipeline in `populate_entities()` still writes them. This causes a schema mismatch on rebuild.

**Action:**
- Remove `compound_id` and `member_id` from `Entity` in `db_models.py`
- Remove from `EntityDetail` in `models.py`
- Remove from `entity_to_detail()` in `converters.py`
- Remove from `populate_entities()` in `build_mcp_db.py`
- Remove from entity resource in `resources.py`
- The build pipeline uses these only to join artifacts — conversion to `entity_id` (e.g., `fn:a494a29`) happens before DB insertion

---

## 5. Remove Low-Value Tools (gaps §11)

<!-- spec 008: RESOLVED — get_hotspots, get_related_files, get_file_summary, list_file_entities removed (19 → 15 tools). Response models HotspotsResponse, FileSummaryResponse, ListFileEntitiesResponse also removed. -->

---

## 6. Entry Point / Capability Language Cleanup (gaps §2)

<!-- spec 008: RESOLVED — capability param removed from list_entry_points; entry points have capability=NULL by design; get_capability_detail.entry_points uses JSONB containment for transitive call cone lookup; MODEL.md and contracts/tools.md updated -->

---

## 7. Contract Compliance — Tool Parameter Gaps (gaps §3)

<!-- spec 008: RESOLVED — search: limit → top_k (default 10); get_class_hierarchy: direction param added (Literal["ancestors","descendants","both"]); get_related_entities: limit → limit_per_type (default 20, per-group truncation); get_dependencies: default direction "both" → "outgoing"; get_related_files removed (§5) -->

---

## Deliverable

- Enums, models, converters, and tests shed ~30% of their fields
- Tool count drops from 19 to 15 <!-- spec 008: confirmed -->
- Remaining tools match their contract specs <!-- spec 008: confirmed -->
- No `doc_quality`, `doc_state`, `side_effect_markers`, `provenance`, `compound_id`, or `member_id` anywhere in the codebase <!-- spec 008: confirmed -->
- Clean rebuild + full test suite passes <!-- spec 008: confirmed (170 tests pass) -->
