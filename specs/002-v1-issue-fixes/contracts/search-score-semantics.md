# Contract: Search Score Semantics

**Tool**: `search` and `search_usages` MCP tools
**Changed by**: 002-v1-issue-fixes (I-002)

The response schema is unchanged. This contract documents the behavioral change to the `score` field.

---

## `score` field semantics (after this fix)

| Query type | Expected score | Expected result count |
|---|---|---|
| Exact name/signature match | ≥ 10.0 (exact boost dominates) | ≥ 1 |
| Strong semantic match (cosine ≥ 0.7) | ~0.4–0.6 | ≥ 1 |
| Weak semantic match (cosine < 0.3) | ~0.1–0.2 | 0 (filtered) |
| No plausible match (nonsense query) | N/A | 0 |

## Filtering rule

Results with combined score < 0.2 are excluded before returning. Exact-name matches (score ≥ 10.0) are always returned regardless of combined score.

## What changed

**Before**: `score` was normalized per-query. Top result always = 1.0 regardless of actual match quality. A nonsense query returned results indistinguishable from a perfect match.

**After**: `score` is the raw combined score. No per-query normalization. Score ordering is preserved; score value signals absolute match strength.

## Contract tests

```python
# test_search_tool.py

def test_nonsense_query_returns_no_results():
    results = search(query="xyzzy_nonexistent_9f3k", limit=10)
    assert results == []

def test_exact_name_match_returned():
    results = search(query="stc", limit=5)
    assert any(r.name == "stc" for r in results)
    assert results[0].score > 1.0  # exact match dominates
```
