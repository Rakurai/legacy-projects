# V1 Issues Feedback

**Date**: 2026-03-19
**Reviewer**: Claude Code (Sonnet 4.5)
**Source**: `specs/v1/issues.md` validation request

---

## Executive Summary

Three of four proposed solutions are sound. One (I-002) has a significant flaw in the proposed fix that would not achieve the stated goal. Search scoring fundamentals are solid but implementation has two fixable issues: per-query normalization (obscures absolute quality) and unbounded keyword scores (prevents reliable fixed-ceiling normalization).

**Priority**: Fix I-001 (split entities) first—this is data corruption affecting contract seeds, graph traversal, and usage search. Then address I-002 and I-003 together since I-003 depends on I-002 for score-based filtering.

---

## Issue-by-Issue Validation

### I-001: Split Entities — APPROVED ✅

**Problem statement**: Accurate. Two Doxygen compounds (declaration in `.hh`, definition in `.cc`) generate two database rows with different entity_ids. Metrics on one, documentation on the other. This systematically breaks `is_contract_seed`, creates empty `calling_patterns` on graph-reachable entities, and inflates entity counts.

**Root cause analysis**: Correct. Entity ID formula `{prefix}:{sha256(compound_id, signature)[:7]}` at `packages/legacy_common/legacy_common/entity_ids.py:30-39` is deterministic per compound. Two compounds produce two distinct but stable IDs.

**Proposed fix**: Sound. Merge at build time in `build_helpers/entity_processor.py::merge_entities()` before deterministic ID assignment (line 237). The critical insight—keep the compound_id that the code graph references—is correct. Graph edges (`code_graph.gml` loaded at `build_helpers/graph_loader.py`) reference specific compound IDs as node identifiers. The surviving entity must use the graph-referenced compound for runtime traversal to work.

**Implementation notes**:

Current flow at `entity_processor.py:192-234`:
```python
def merge_entities(entity_db, doc_db) -> list[MergedEntity]:
    merged: list[MergedEntity] = []
    for entity in entity_db.entities.values():
        doc = doc_db.get_doc(compound_id, entity.signature)
        merged.append(MergedEntity(entity, doc, sig_key))  # One per Doxygen entity, no dedup
    return merged
```

Needs deduplication by `(name, signature, file_path)` triple before returning. Grouping logic:

1. Build dict: `(name, sig, path) -> list[MergedEntity]`
2. For each group with len > 1:
   - Load graph at this stage or pass graph node IDs into merge
   - Select entity whose `compound_id` appears as a graph node
   - Merge doc fields from non-selected entities onto selected entity
3. Emit one MergedEntity per logical entity

**Where to fix**: `build_helpers/entity_processor.py::merge_entities()` only. No changes to graph loader, server runtime, or schema.

**Test verification**: After fix, `fn:4b7e3b7` (stc) should have both `fan_in=640` AND non-null rationale, causing `is_contract_seed=true`. `explain_interface` for high-fan_in entities should return populated `calling_patterns`.

---

### I-002: Search Score Normalization — APPROVED WITH REVISIONS ⚠️

**Problem statement**: Accurate. Per-query normalization at `server/search.py:168-179` makes all top scores 1.0, obscuring absolute match quality. A nonsense query and a perfect match both return `score=1.0`.

**Root cause analysis**: Correct. Lines 168-169:
```python
max_score = ranked[0][1] if ranked else 1.0
normalizer = max_score if max_score > 0 else 1.0
```

This divides all scores by the best score in the current result set, producing relative [0,1] range per query.

**Proposed fix**: **FLAWED**. Document suggests dividing by 11.0 (sum of weights: 10.0 + 0.6 + 0.4) to produce [0,1] absolute range. This assumption is incorrect.

**Why the proposed fix fails**:

The scoring formula at `search.py:104-122` (`_merge_scores`):
```python
score = 0.0
if eid in exact_ids: score += 10.0
if eid in semantic_scores: score += semantic_scores[eid] * 0.6  # cosine_sim ∈ [0,1] → [0, 0.6]
if eid in keyword_scores: score += keyword_scores[eid] * 0.4    # ts_rank is UNBOUNDED
```

PostgreSQL `ts_rank()` (line 75) does not have a fixed ceiling. It returns values typically in [0, 0.1] but can exceed 1.0 for short documents with high term density. The range varies by document length, term frequency, and query term count. Therefore:

- Theoretical max: 10.0 + 0.6 + (unbounded keyword)
- Dividing by 11.0 does NOT guarantee [0,1] output
- A highly relevant short document could score 10.0 + 0.6 + 2.0 = 12.6, producing 12.6/11 = 1.145 > 1.0

**Correct fix options**:

**Option A (recommended): Normalize components before weighting**
```python
# In _merge_scores() or caller:
max_kw = max(keyword_scores.values()) if keyword_scores else 1.0
normalized_kw = {eid: s / max_kw for eid, s in keyword_scores.items()}

score = 0.0
if eid in exact_ids: score += 10.0
if eid in semantic_scores: score += semantic_scores[eid] * 0.6  # already [0,1]
if eid in normalized_kw: score += normalized_kw[eid] * 0.4     # now [0,0.4]

# Now theoretical max is 11.0, divide by 11.0 → [0,1]
normalized = min(score / 11.0, 1.0)
```

This ensures:
- Exact match + perfect semantic + perfect keyword = 1.0
- Weak match across all dimensions = ~0.02
- Scores comparable across queries

**Option B: Return raw scores, document scale**

Remove normalization entirely:
- Exact match: ~10.0+ (indicates exact name/sig match)
- Good semantic: 0.4–0.6 (cosine similarity 0.6–1.0)
- Weak match: <0.2

Agents learn to interpret: `score > 10` = exact, `score > 0.4` = relevant, `score < 0.2` = noise.

**Option C: Expose both raw and normalized**

Extend `SearchResult` model at `server/models.py`:
```python
class SearchResult(BaseModel):
    score: float  # Normalized [0,1] for backward compat
    raw_score: float | None = None  # Absolute quality signal
    ...
```

Agents use `raw_score` for filtering, `score` for relative ranking within results.

**Recommendation**: Implement Option A. It achieves the stated goal (absolute [0,1] scores) correctly and requires minimal client changes.

**Where to fix**:
1. `server/search.py::_merge_scores()` — normalize keyword scores before weighting
2. `server/search.py::hybrid_search()` and `hybrid_search_usages()` — divide by 11.0 instead of per-query max
3. Remove lines 168-169 (current per-query normalization)

**Test verification**: After fix, a nonsense query should return `score < 0.1`, while an exact match returns `score > 0.9`.

---

### I-003: Usage Search Quality — APPROVED ✅

**Problem statement**: Accurate. Nonsense queries return non-empty results with normalized score=1.0. Negative-evidence usage descriptions ("not used directly") pollute results because they score equally poorly with everything else when query is far from corpus.

**Analysis**: Correct distinction between Issue A (usage search purpose—valid) and Issue B (low-quality descriptions—fixable).

**Proposed fix**: Sound. Two-part approach:

1. **Build-time filter**: Skip entity_usages rows matching negative-evidence patterns
2. **Score floor** (via I-002): Low-quality results get low absolute scores, agents filter by threshold

**Implementation for part 1**:

Location: `mcp/doc_server/build_mcp_db.py::populate_entity_usages()` line 180-240

Current code (approximate line 220):
```python
for merged in merged_entities:
    if not merged.doc or not merged.doc.usages:
        continue
    for key, description in merged.doc.usages.items():
        # Parse key, create EntityUsage...
```

Add filter:
```python
NEGATIVE_PATTERNS = [
    "not used",
    "not directly used",
    "not referenced",
    "not directly referenced",
    "only checked for",
    "only present in signature",
]

for key, description in merged.doc.usages.items():
    desc_lower = description.lower()
    if any(pattern in desc_lower for pattern in NEGATIVE_PATTERNS):
        continue  # Skip this usage row
    # Continue with EntityUsage creation...
```

Log filtered count for observability:
```python
log.info("Entity usages populated",
         total_rows=len(usage_rows),
         filtered_negatives=filtered_count)
```

**Implementation for part 2**: Depends on I-002 being fixed correctly per Option A above. After that, agents can use `if score < 0.2: log.warning("weak matches only")`.

**Where to fix**:
1. `mcp/doc_server/build_mcp_db.py::populate_entity_usages()` — add negative-evidence filter
2. I-002 must be fixed first for score-based filtering to work

**Test verification**: After build, search `source="usages"` for "nonexistent_xyz" should return either zero results or very low-score results (<0.1). Usage entries like "not used directly" should not appear in `entity_usages` table.

---

### I-004: `stc` Contract Seed Flag — APPROVED ✅

**Validation**: Correct identification as I-001 manifestation. No independent fix needed.

**Test case value**: High. This is the most egregious case (fan_in=640, highest in codebase). After I-001 fix, verify:
- `fn:4b7e3b7` (stc) has `is_contract_seed=true`
- `explain_interface(fn:4b7e3b7)` returns populated `calling_patterns` (not empty)
- Search `source="usages"` for "send text to character" returns stc with `fan_in=640`

Retain as named regression test.

---

## General Search Scoring Assessment

**Question**: "Is our search scoring problematic in general?"

**Answer**: Fundamentals are sound. Implementation has two fixable issues.

### Issue 1: Per-query normalization obscures absolute quality

**Current behavior**: Every query's top result gets score=1.0, regardless of match quality.

**Impact**:
- Agents can't detect "no good matches found" vs "perfect match"
- Score-based filtering impossible (e.g., "only show results with score > 0.5")
- Agent workflows must inspect content (brief, signature) to judge relevance

**Severity**: Medium. Agents work around this, but it's a footgun. Fixing this unlocks score-based filtering and reduces agent token usage (can skip low-score results early).

**Fix**: I-002 Option A (normalize keyword before weighting, divide by fixed ceiling).

---

### Issue 2: Unbounded ts_rank prevents naive fixed-ceiling normalization

**Current behavior**: `ts_rank()` at `search.py:75` returns unbounded float. Typical range [0, 0.1] but can exceed 1.0.

**Impact**: Can't divide by 11.0 without first normalizing keyword scores. Doing so produces scores > 1.0 for some queries, breaking the [0,1] assumption.

**Severity**: Low. Only affects I-002 implementation, doesn't impact current functionality.

**Fix**: Include keyword normalization in I-002 Option A.

---

### What's working well

**Exact match boost (10x)**: Appropriate. Entities have unique names/signatures. An exact match is definitionally the correct result.

**Semantic (0.6) + keyword (0.4) weighting**: Reasonable balance. Embeddings capture semantic similarity, full-text search catches lexical matches. 60/40 split favors semantics appropriately for documentation search.

**Hybrid fallback**: Clean degradation when embedding provider unavailable. `search_mode: keyword_fallback` explicitly signals degraded state. No silent failures.

**Component independence**: Exact, semantic, and keyword searches run in parallel (lines 148-153 in `search.py`). Additive scoring allows independent tuning of weights.

**Usage search design**: Grouping by callee entity (one result per entity, `matching_usages` as evidence) is the right abstraction. Returning individual usage rows would flood results.

---

## Recommendations

### Priority 1: Fix I-001 (split entities)

**Why first**: Data corruption. Breaks core features:
- Contract seed identification (highest-value entities invisible to Wave 1 planning)
- Graph traversal → explain_interface workflow (empty calling patterns)
- Usage search → get_callers workflow (fan_in=0 on wrong entity)

**Impact**: ~50% of high-fan_in entities likely affected (declaration/definition split is common in C++).

**Effort**: Medium. Requires deduplication logic in merge pipeline, graph node lookup to determine surviving compound.

**Risk**: Low. Build-time only, no runtime changes. Fully testable with I-004 (stc) as regression test.

---

### Priority 2: Fix I-002 (search scoring) correctly

**Why second**: Moderate impact, enables I-003 score-based filtering. Current agents work around it.

**Implementation**: Option A (normalize keyword scores, divide by 11.0). Do NOT divide by 11.0 without normalizing keyword first.

**Effort**: Low. 10-15 line change in `_merge_scores()` and `hybrid_search()`.

**Risk**: Low. Additive change (scores shift but relative ranking mostly unchanged). Agents currently ignore scores, so breaking score semantics is safe.

**Test**: Add contract test verifying nonsense query returns `score < 0.1`, exact match returns `score > 0.9`.

---

### Priority 3: Fix I-003 (usage search quality)

**Why third**: Low effort, high data quality impact. Depends on I-002 for full value.

**Implementation**: Add 5-line negative-evidence filter in `populate_entity_usages()`.

**Effort**: Trivial. One-liner plus pattern list.

**Risk**: None. Build-time only, removes garbage data.

**Test**: Query entity_usages table after build, verify zero rows matching negative patterns. Usage search for nonsense query returns zero or very low-score results.

---

### Priority 4: Monitor I-004

No action. Regression test for I-001.

---

## Implementation Sequence

```
1. Implement I-001 (entity merge deduplication)
   - Update merge_entities() with grouping logic
   - Add graph node lookup to determine survivor
   - Test with I-004 (stc) verification

2. Implement I-002 Option A (keyword normalization + fixed ceiling)
   - Normalize keyword scores in _merge_scores()
   - Replace per-query normalization with /11.0
   - Add contract tests for score ranges

3. Implement I-003 (negative-evidence filter)
   - Add pattern filter in populate_entity_usages()
   - Verify filtered count in logs
   - Confirm low/zero results for nonsense queries

4. Run full test suite (specs/001-kg-enrichment/full-test.md)
   - All 37 tests should still pass
   - I-004 (stc) should now pass contract seed check
   - Search score tests should pass new absolute thresholds
```

---

## Additional Observations

### Graph loader timing

Current build flow (from `build_mcp_db.py`):
1. Load entities + docs → merge (line ~36)
2. Assign deterministic IDs (line ~38)
3. Load graph and compute metrics (line ~40)

I-001 fix requires graph node IDs during merge (step 1) to determine which compound survives. Options:

**A: Load graph early**
```python
# In build_mcp_db.py main():
graph = load_code_graph(...)  # Before merge
merged = merge_entities(entity_db, doc_db, graph_node_ids=graph.nodes())
```

**B: Two-pass merge**
```python
# Pass 1: merge without dedup
merged = merge_entities(entity_db, doc_db)
# Pass 2: dedup using graph after it's loaded
merged = deduplicate_entities(merged, graph)
```

Recommend Option A (early graph load) for cleaner single-pass merge.

### Capability assignment dependency

Current code at `entity_processor.py` has FR-059: "Build script MUST assign entity capabilities before computing bridge flags (pipeline ordering dependency)."

I-001 entity merge must happen BEFORE capability assignment (which is before bridge computation). Current order:
```
merge → assign IDs → extract source → compute enrichments → assign capabilities → compute metrics (bridge)
```

New order:
```
merge+dedup → assign IDs → extract source → compute enrichments → assign capabilities → compute metrics
```

Deduplication in merge step maintains all downstream ordering.

### Embedding generation for merged entities

After merge deduplication, each surviving entity should get exactly one embedding. Current flow at `build_mcp_db.py::main()` calls `generate_embeddings(merged_entities)` after merge. This is correct—deduplication happens before embedding generation, so no duplicate embeddings.

Entity_usages embeddings (001-kg-enrichment) are generated in `populate_entity_usages()` and already group by callee. I-001 fix ensures each callee_id maps to exactly one logical entity, so usage embedding grouping is correct.

---

## Conclusion

All four issues are real. Three proposed fixes are sound. One (I-002) requires correction to achieve stated goal. Search scoring is fundamentally well-designed but needs two implementation fixes: proper keyword normalization and fixed-ceiling division.

Fix I-001 first—it's the most impactful. I-002 and I-003 can be done together since I-003 depends on I-002 for score-based filtering. Total effort: ~1-2 days for all three fixes plus testing.
