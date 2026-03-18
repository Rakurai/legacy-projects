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

The `side_effect_markers` system is built on a hand-curated function list (`SIDE_EFFECT_FUNCTIONS` dict in `entity_processor.py`) that was not validated against actual call patterns. The categorization (messaging, persistence, state_mutation, scheduling) and the specific function names were hallucinated — they represent plausible-looking but unverified assumptions about what constitutes a side effect in the legacy codebase.

**Decision:** Remove entirely. If side-effect analysis is needed in V2, it should be derived from the dependency graph (e.g., functions that write to globals via USES edges), not from a prebuilt dictionary.

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

Every response model carries a `provenance: Provenance` field (FR-044) that the calling agent never reads or acts on. The 7-label `Provenance` enum (`doxygen_extracted`, `llm_generated`, `subsystem_narrative`, `precomputed`, `inferred`, `heuristic`, `measured`) adds complexity without providing signal — agents reason about the *content* of responses, not their data lineage.

The provenance derivation logic also depends on `doc_state` (being removed in §1), creating a coupling that makes both removals cleaner when done together.

**Decision:** Remove entirely.

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

Four tools provide minimal value to agents and should be removed to reduce the tool surface:

| Tool | File | Reason |
|------|------|--------|
| `get_hotspots` | `server/tools/behavior.py` | The `underdocumented` metric depends on `doc_quality` (being removed in §1). The `fan_in`/`fan_out`/`bridge` metrics are available via `search` with sorting. Not a natural part of any agent workflow |
| `get_related_files` | `server/tools/graph.py` | Only works for outgoing INCLUDES edges (1,656 total). Returns empty for most files. The spec-creating agent works entity-first, not file-first |
| `get_file_summary` | `server/tools/entity.py` | Returns per-file entity counts and distributions. No clear agent use case — agents navigate by entity or capability, not by source file |
| `list_file_entities` | `server/tools/entity.py` | File-centric entity list. Occasionally useful ("what else is in this file?") but not a core workflow and can be achieved via `search` with file_path filter |

Also remove the corresponding response models (`HotspotsResponse`, `FileSummaryResponse`, `ListFileEntitiesResponse`) and any related test code.

---

## 6. Entry Point / Capability Language Cleanup (gaps §2)

Entry points (`do_*`, `spell_*`, `spec_*`) are **routing functions** — they dispatch into capability-grouped implementation code but do not themselves belong to a single capability. All 637 entry points have `capability=NULL` and this is correct by design. The capability classification pipeline assigns capabilities to the *callees* of entry points, not the entry points themselves.

Multiple spec documents, tool contracts, and TODO items repeatedly describe this as a bug ("entry points should have capabilities", "list_entry_points with capability filter returns empty"). This is not a bug — it reflects the architectural distinction between dispatch and implementation.

**Action:**
- Update MODEL.md, SPEC.md, contracts/tools.md, and analysis.md to clarify that `Entity.capability` is NULL for entry points by design
- Redefine `list_entry_points(capability=...)` contract: the filter means "entry points whose call cone touches this capability" (requires graph traversal), not "entry points where `Entity.capability == X`" (always empty)
- Decide: implement the graph-traversal filter, or drop the capability parameter from `list_entry_points`
- Similarly clarify `get_capability_detail.entry_points`: this should list entry points that *route into* the capability (via `capability_graph.json`'s `entry_points_using` field), not entry points *classified as* the capability

---

## 7. Contract Compliance — Tool Parameter Gaps (gaps §3)

Remaining divergences between `contracts/tools.md` and the implementation:

| Tool | Contract | Implementation | Fix |
|------|----------|----------------|-----|
| `search` | `top_k` parameter | `limit` parameter | Rename param |
| `get_class_hierarchy` | `direction?: "ancestors"\|"descendants"\|"both"` | Always returns both | Add param + filter |
| `get_related_files` | `relationship?: "includes"\|"included_by"\|"co_dependent"` | Outgoing INCLUDES only — returns empty for most files | Add reverse edge traversal + filter |
| `get_related_entities` | `limit_per_type` (default 20) | `limit` global (default 100) | Restructure grouping |
| `get_dependencies` | `direction` default `"outgoing"` | Default `"both"` | Change default |

**Note:** If `get_related_files` is removed in §5, its contract row is moot.

---

## Deliverable

- Enums, models, converters, and tests shed ~30% of their fields
- Tool count drops from 19 to 15
- Remaining tools match their contract specs
- No `doc_quality`, `doc_state`, `side_effect_markers`, `provenance`, `compound_id`, or `member_id` anywhere in the codebase
- Clean rebuild + full test suite passes
