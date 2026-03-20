# Research: V1 Known Issue Fixes

**Branch**: `002-v1-issue-fixes` | **Date**: 2026-03-20

---

## I-001: Split Entity Merge — Pipeline Reordering

### Problem

`merge_entities()` (`build_helpers/entity_processor.py:192`) currently has no deduplication. It iterates `entity_db.entities` and appends one `MergedEntity` per Doxygen compound without detecting when two compounds represent the same logical entity.

`load_graph_edges()` (`build_helpers/graph_loader.py:20`) is called after `merge_entities()` and receives `merged_entities` as input — it needs the already-computed `entity_id`s to build its `node_to_entity` mapping (lines 41–47). So the current design deliberately loads the graph late.

### Key finding: two-phase graph loading

The fix cannot move `load_graph_edges()` earlier because it depends on assigned entity IDs. Instead, introduce a new earlier-stage function that reads **only the raw GML node IDs** — a frozenset of strings — without the entity→ID mapping:

```
load_graph_node_ids(artifacts_path) → frozenset[str]   # new, before merge
```

Then `load_graph_edges(artifacts_path, merged_entities)` remains unchanged and runs after ID assignment.

**Decision**: Two-phase graph access. `load_graph_node_ids()` added to `graph_loader.py`; `load_graph_edges()` untouched.

**Rationale**: Minimal blast radius. No changes to downstream metric computation (fan_in, fan_out, bridge) or the NetworkX graph used at server runtime.

### Key finding: deduplication key

From `build_helpers/entity_processor.py:209–214`, the `sig_key` per entity is `(compound_id, second_element)` — unique per compound. The dedup key must be different: **`(entity.name, entity.signature, entity.location.file)`** (need to verify exact `DoxygenEntity` attribute for file — likely `entity.location` or `entity.location.file`; confirm from legacy_common type stubs during implementation).

**Decision**: Dedup by `(name, signature, file_path)`. Two entities that share this triple are a declaration/definition split pair.

### Key finding: surviving compound selection

The GML node IDs are either:
- `entity.id.member` (for class members)
- `entity.id.compound` (for standalone entities)

This matches the lookup in `graph_loader.py:41–47`. To determine which compound wins: check whether `entity.id.member or entity.id.compound` is in the `frozenset` returned by `load_graph_node_ids()`.

**Decision**: The compound whose node ID appears in the GML wins. The other compound's `doc` field is copied onto the survivor if the survivor's `doc` is `None`.

### Key finding: error cases

- **Neither compound in GML**: `BuildError` — the logical entity is not reachable from the graph at all. Raise, don't skip.
- **Both compounds in GML**: deterministically keep the one whose file path ends in `.cc` / `.cpp` (the definition). If file path is unavailable or ambiguous, keep the compound with non-null `doc` (rationale: documentation was generated against the definition compound).
- **More than two fragments**: same logic extended — pick the GML-present compound; merge all others' docs onto it.

### Merge doc field strategy

`MergedEntity.__init__` accepts `doc: Document | None`. After grouping by dedup key:

1. All fragments in the group are instantiated as `MergedEntity` instances (with individual `doc` lookups against `doc_db`).
2. The survivor is the fragment whose node ID is in the GML.
3. If the survivor's `doc` is `None` and any sibling's `doc` is not `None`, copy the sibling's `doc` onto the survivor by direct field assignment (the `doc` field must be mutable, or the merge must happen before `MergedEntity` instantiation).
4. Log the merge: `log.info("merged split entity", name=..., count=...)`.

**Decision**: Collect fragments as pre-`MergedEntity` data, resolve survivor, then construct a single `MergedEntity`. Alternatively, make `MergedEntity.doc` mutable (it's a dataclass field — it's already mutable). Either approach is valid; prefer resolving before instantiation to keep the constructor clean.

---

## I-002: Score Threshold Filtering

### Key finding: `_merge_scores()` and normalization locations

`_merge_scores()` (`server/search.py:104`) computes:
```
score = exact_weight (10.0) + semantic * 0.6 + keyword * 0.4
```

Per-query normalization happens in `hybrid_search()` at lines 167–169 and in `hybrid_search_usages()` at lines 313–314:
```python
max_score = ranked[0][1] if ranked else 1.0
normalizer = max_score if max_score > 0 else 1.0
score = min(score / normalizer, 1.0)
```

### Key finding: keyword score bounds

`ts_rank()` is unbounded. The keyword contribution (`keyword_scores[eid] * 0.4`) can exceed 0.4 when `ts_rank` returns > 1.0. Normalize within the query's keyword result set first:

```python
if keyword_scores:
    max_kw = max(keyword_scores.values())
    keyword_scores = {eid: s / max_kw for eid, s in keyword_scores.items()}
```

After normalization, keyword contribution is bounded to `[0, 0.4]` and the combined score for a non-exact match is bounded to `[0, 1.0]`.

**Decision**: Normalize keyword scores in `_merge_scores()` before the weight application. Normalization is query-relative (within the result set), which is acceptable since keyword scores are only used for ranking and threshold filtering — not as an absolute signal.

### Key finding: threshold value

With normalization applied, genuine semantic matches have cosine similarity ≥ 0.4, giving a semantic contribution of ≥ 0.24. A threshold of **0.2** excludes results where semantic similarity is < 0.33 AND keyword contribution is negligible. Exact matches (score 10.0+) are always above threshold.

This threshold must be empirically validated against SC-003 (nonsense query → zero results) and SC-004 (exact-name query → target entity first) before commit.

**Decision**: Threshold = 0.2 (approximate; validated before commit). Applied in `hybrid_search()` and `hybrid_search_usages()` after computing combined scores, replacing the per-query normalization block.

**Alternatives considered**:
- Fixed-ceiling normalization (divide by 11.0): invalid without keyword normalization; still pursued by Claude Sonnet 4.5 as "Option A" in feedback — rejected because the threshold approach achieves the same filtering goal with less complexity.
- Sigmoid compression: requires tuning two parameters; threshold is simpler and sufficient.
- RRF: solves a ranking problem, not a filtering problem — rejected.

### Key finding: exact match unconditional return

Exact matches (via name/signature exact lookup) always score ≥ 10.0, well above any threshold. No special-casing needed; the threshold naturally preserves them.

---

## I-004: stc Regression Verification

Not a code change. After I-001 is implemented and the database is rebuilt:

- Query entity for `stc` → expect single record with `fan_in=640`, `is_contract_seed=true`, non-null `rationale`
- Call `explain_interface` on the returned entity_id → expect non-empty `calling_patterns`
- Search `source="usages"` for "send text to character" → expect `stc` entity in results with `fan_in=640`

These three checks cover FR-010 (SC-002).

---

## Pipeline ordering after all changes

```
load_graph_node_ids()            ← NEW: before merge, reads raw GML node IDs
load_entities() + load_documents()
merge_entities(graph_node_ids)   ← MODIFIED: dedup + graph-compound selection
assign_deterministic_ids()
extract_source_code()
load_capability_defs() + load_capability_graph()
assign_capabilities()
load_graph_edges(merged_entities) ← UNCHANGED: still after ID assignment
compute_fan_metrics()
compute_bridge_flags()
populate_entities() → populate_entity_usages() → populate_edges() → ...
```

All downstream ordering dependencies (FR-059: capabilities before bridge) are preserved.
