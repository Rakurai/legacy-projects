# Directive: revise search design toward hybrid candidate generation + reranking

## Motivating issue: search score calibration

Per-query normalization in `server/search.py` makes the top result of every query score 1.0, regardless of actual match quality. A nonsense query returns results indistinguishable from a perfect exact-name match.

**Root cause.** Both `hybrid_search` and `hybrid_search_usages` normalize by dividing all scores by the maximum score in the result set:

```python
max_score = ranked[0][1] if ranked else 1.0
normalizer = max_score if max_score > 0 else 1.0
# ...
score=min(score / normalizer, 1.0)
```

This produces a [0, 1] range relative to the best result in *this query*, not an absolute quality signal.

**Why this matters.** The requesting agent doesn't need a meaningful score number — it can read entity names, signatures, and briefs and reason about relevance on its own. What the agent needs is for the server to not waste its context window on noise. The current system returns garbage results with confident-looking scores, forcing the agent to evaluate and discard irrelevant entities.

**Additional factor: unbounded keyword scores.** PostgreSQL `ts_rank()` returns unbounded floats (typically [0, 0.1] but can exceed 1.0 for short documents with high term density). This makes naive fixed-ceiling normalization invalid — the keyword component must be normalized before combining with semantic scores.

**Reviewed approaches (see `issues-feedback.summary.md`):**
- Fixed-ceiling normalization (divide by 11.0): invalid without keyword normalization
- Component scores (exact, semantic, keyword): rejected — adds response bloat without agent decision value
- Reciprocal Rank Fusion: rejected — ranking order is already fine, the problem is filtering
- Sigmoid / nonlinear transforms: considered, rejected — threshold achieves same goal with less complexity
- Quality labels/bins: rejected — arbitrary without natural score breakpoints

**Conclusion.** The scoring problem is not fundamentally about calibrating a single number. It's about the search system's responsibility to filter noise before returning results. This motivates the reranking pipeline below: treat the current hybrid scoring as candidate generation, apply filtering to remove junk, and let a reranker handle final ordering.

---

Adopt the search pipeline below as the new design direction.

## Goal

Treat the current hybrid scoring system primarily as a **candidate generation and filtering stage**, not as the final relevance model. Final ordering should be handled by a **reranker** over a bounded candidate set.

## Proposed pipeline

1. **Vector retrieval**
   - Retrieve top **N** candidates from embedding / pgvector semantic search.

2. **Keyword retrieval**
   - Retrieve top **M** candidates from keyword / full-text search.

3. **Union + dedupe**
   - Union the two candidate sets.
   - Deduplicate by canonical entity identity.
   - Do not assume the two sets are highly overlapping; partial disjointness is expected and acceptable.
   - The purpose of hybrid retrieval here is recall.

4. **Cheap intermediate scoring / filtering**
   - For the merged candidate set, compute a small number of bounded relevance signals.
   - Signals should focus on:
     - **semantic similarity**
     - **keyword similarity**
     - **name/signature overlap** (if useful)
   - Do **not** treat “exact match” as a separate conceptual pillar if it is already captured by the lexical/overlap features.
   - Prefer a **nonlinear shaping / filtering approach** over a misleading normalized final scalar if that gives better separation between plausible and implausible candidates.
   - This stage exists to remove obvious junk before reranking, not to produce a user-facing or agent-facing “confidence score.”

5. **Filtering logic**
   - Apply filtering using either:
     - a combined nonlinear score, or
     - explicit per-signal thresholds / tuple thresholds, or
     - slightly more complex deterministic logic if justified.
   - The key requirement is that weak/noisy candidates should be removed before reranking.
   - Do not optimize for score interpretability; optimize for retaining good candidates and excluding garbage.

6. **Reranking**
   - Apply a reranker to the surviving candidate set.
   - The reranker is responsible for final relevance ordering.
   - The pre-rerank stage should be designed to keep the candidate set small enough that reranking remains practical.

7. **Return top-K**
   - Return the top **K** reranked results.

## Design guidance

- The main reason for the hybrid first stage is **recall**, not just cost.
- A reranker cannot recover entities that never entered the candidate pool.
- Therefore, vector-only top-20 retrieval should **not** be assumed sufficient unless verified empirically.
- Keyword and semantic retrieval should both contribute to candidate generation.
- The current homegrown search logic should be retained only insofar as it is useful for:
  - candidate generation
  - deduped candidate scoring
  - pre-rerank filtering

## Non-goals

- Do not spend effort making the intermediate score “interpretable” for the requesting agent.
- Do not add component scores to the response unless there is a concrete downstream need.
- Do not assume linear weighted averaging is the only valid intermediate filter.
- Do not introduce a trained classifier unless later evaluation shows the deterministic nonlinear filter is insufficient.

## Deferred issues

### I-003: Low-quality usage descriptions

**Originally**: proposed as a build-time negative-evidence pattern filter in `populate_entity_usages()` — skip rows whose description matches patterns like "not used", "not directly used", "not referenced", etc.

**Why deferred**: The pattern-matching approach is fragile and not well-bounded. It risks over-filtering mixed descriptions (e.g., "not used for X, but used for Y") and under-filtering novel phrasings the pattern list doesn't anticipate. The underlying problem — that low-quality usage descriptions surface in results and waste agent context — is better addressed by the reranking pipeline's pre-rerank filtering stage, which can demote or exclude weak-evidence candidates without a brittle keyword list.

**What to resolve here**: During reranking design, determine whether low-quality usage descriptions are handled by:
- a score floor on semantic similarity (rows with very low cosine similarity to any real query are never retrieved), or
- a field-quality signal in the intermediate scoring stage (e.g., description length, presence of behavioral verbs), or
- a corpus cleanup pass driven by better criteria than substring pattern matching.

## Expected follow-up work

Have the planning/spec agent fill in:
- exact definitions of N, M, and K
- precise dedupe identity rules
- which overlap feature(s) are worth computing
- the nonlinear/filtering rule to use before reranking
- where this logic belongs in the current codebase
- how I-003 (low-quality usage descriptions) is handled within the pre-rerank filtering stage