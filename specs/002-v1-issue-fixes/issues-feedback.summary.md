# Issues Feedback Summary

**Date**: 2026-03-19
**Sources**: issues.md, issues-feedback.gpt.md (GPT), issues-feedback.claude.md (Claude Sonnet 4.5), user discussion

---

## Consensus

All parties agree on the following:

- Hybrid retrieval (exact + semantic + keyword) is conceptually sound for Doxygen-derived C++ docs
- Current ranking order is mostly correct — the problem is score presentation and filtering, not retrieval strategy
- I-001 (split entities) is the highest-priority fix — it's data corruption, not a tuning problem
- I-003 (negative-evidence usages) should be filtered at build time
- Per-query normalization (I-002) is the announced score bug
- `ts_rank` is unbounded, so the proposed "divide by 11.0" fix is invalid without normalizing keyword scores first

---

## Key insight: agent competence changes the design target

The requesting agent is itself a semantic and language matching machine. It knows the search query. It can read the returned signatures, briefs, and descriptions. It can reason about which results are relevant.

The score is not a quality signal for the agent to deliberate over — the agent already has better quality information from the content itself. The score serves two internal purposes:

1. **Ranking** — determines the order results appear. The agent reads top-down and stops when results stop looking useful. Any monotonic ordering works. The current ranking is already good.
2. **Filtering** — determines whether noise is included at all. The agent doesn't need to be told result #1 is great; it needs to not see result #47 which is garbage.

The goal is to present agents with a ranked and filtered group of results so they don't waste context window and attention. Not to give them a number to think about.

---

## Reviewer proposals evaluated

### GPT proposals

| Proposal | Verdict | Reasoning |
|----------|---------|-----------|
| Option A: Fix calibration, keep additive | **Partially adopted** | Keyword normalization is correct. Fixed-ceiling normalization is unnecessary if we threshold instead. |
| Component scores (exact_match, semantic_score, keyword_score) | **Rejected** | Gives the agent more numbers to not need. The agent can already see the entity name and judge exact match. Component scores add response bloat without decision value. |
| RRF (Reciprocal Rank Fusion) | **Rejected** | Ranking is already fine. The problem was never "wrong order" — it was "too many irrelevant results with misleading scores." RRF doesn't solve that. |
| Two-stage field-aware reranking | **Rejected** | Over-engineered for ~5K entities. A single retrieval pass with good filtering is sufficient. |
| Separate retrieval by source/field | **Deferred** | Interesting but not warranted by current evidence. Already partially captured via `source="entity"` vs `source="usages"`. |

### Claude proposals

| Proposal | Verdict | Reasoning |
|----------|---------|-----------|
| Option A: Normalize keyword before weighting, divide by 11.0 | **Partially adopted** | Keyword normalization is correct. Fixed-ceiling division is unnecessary — raw score with threshold achieves the actual goal (filtering) more directly. |
| Option B: Return raw scores, document scale | **Close to adopted** | Right direction. We go further: raw score + threshold + no normalization. |
| Option C: Expose both raw and normalized | **Rejected** | Two score fields for one concept. The raw score is sufficient. |
| Early graph load for I-001 | **Agreed** | Load graph before merge to determine surviving compound in a single pass. |

### Nonlinear scoring (user-raised)

**Considered, not adopted.** A sigmoid centered at a relevance threshold would create natural separation between relevant and noise results. But it requires empirically tuning two parameters ($t$ and $k$), and the agent doesn't need the score to be interpretable — it just needs noise filtered out. A threshold achieves the same effect with less complexity.

### Labels/bins ("good", "strong", "exact")

**Rejected.** Binning a linear score into quality labels is arbitrary unless the score has natural breakpoints. It adds a subjective layer the agent doesn't need. The agent reads content; the system filters noise.

---

## Decided approach

### I-001: Split entity merge (HIGH)

Fix in the build pipeline only. During `merge_entities()`, detect when two compounds resolve to the same `(name, signature, file_path)` triple. Keep the compound whose `compound_id` appears as a graph node (so entity_id remains graph-addressable). Copy doc fields from the other compound onto it.

Requires loading the graph before the merge phase (currently loaded after). Single-pass merge with graph node lookup.

**Where**: `build_helpers/entity_processor.py::merge_entities()`
**Verification**: I-004 (stc: fan_in=640, is_contract_seed should become true)

### I-002: Score calibration (LOW → threshold-based filtering)

Three changes:

1. **Normalize keyword scores** within each query's keyword result set before combining with semantic scores. This bounds the keyword contribution to [0, 0.4] and makes the combined score predictable.
2. **Apply a minimum score threshold** — don't emit results below it. Since semantic cosine similarity for genuinely relevant queries is typically 0.4+ and the semantic weight is 0.6, a combined floor of ~0.2 filters noise while preserving real results. Exact-match results are kept unconditionally (score ~10+, well above any threshold).
3. **Drop per-query normalization entirely** — return the raw combined score. The agent doesn't need [0, 1] — it needs a useful result set. The raw score provides ordering; the threshold provides filtering.

**Where**: `server/search.py::_merge_scores()`, `hybrid_search()`, `hybrid_search_usages()`
**Not doing**: Component scores, sigmoid compression, binning, labels, RRF, two-stage reranking

### I-003: Usage description quality (MEDIUM)

Two parts:

1. **Build-time filter**: Skip `entity_usages` rows whose description matches negative-evidence patterns ("not used," "not directly used," "not referenced," etc.). This is a data quality fix.
2. **Score floor from I-002**: After keyword normalization + threshold, garbage usage results simply don't appear. This comes free with I-002.

**Where**: `build_mcp_db.py::populate_entity_usages()` (filter), I-002 changes (score floor)

### I-004: stc contract seed (MEDIUM)

No independent fix. Retained as a named regression test for I-001. After entity merge, verify:
- `fn:4b7e3b7` has `is_contract_seed=true`
- `explain_interface` returns populated `calling_patterns`
- Usage search returns stc with `fan_in=640`

---

## Implementation order

```
1. I-001 — Split entity merge (build pipeline)
   Highest impact. Fixes data corruption that affects contract seeds,
   graph traversal, usage search, and entity count.

2. I-002 — Keyword normalization + score threshold + drop normalization
   Enables I-003. Small code change in search.py.

3. I-003 — Negative-evidence usage filter (build pipeline)
   Trivial. Pattern list + skip logic in populate_entity_usages().

4. I-004 — Verify stc as regression test for I-001

5. Full retest (specs/001-kg-enrichment/full-test.md)
```

---

## What we're explicitly not doing

- **RRF or rank fusion**: Ranking is not the problem. Filtering is.
- **Two-stage reranking**: ~5K entities don't need a retrieval pipeline designed for millions.
- **Component scores in response**: Agent reads content, not sub-scores.
- **Sigmoid or nonlinear transforms**: Threshold achieves the same goal with less complexity and no tuning.
- **Quality labels/bins**: Arbitrary without natural score breakpoints. Agent doesn't need them.
- **Separate per-field retrieval channels**: Already partially done via `source` parameter. Not warranted further now.
