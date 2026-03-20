My take: the **ranking idea is mostly sound**, but the **reported score is not a trustworthy absolute quality signal**, and there are a couple of structural mismatches that matter specifically for C++/Doxygen corpora.

## Bottom line

Your current approach is conceptually reasonable for this corpus:

* exact symbol match gets a large boost,
* semantic similarity helps with intent-style queries,
* keyword/full-text catches lexical overlap and domain terms. 

That is a valid hybrid design for Doxygen-derived function docs. The main problem is **not** “hybrid search is wrong.” The main problem is:

1. **per-query normalization destroys score meaning**, so weak queries still produce a top score of 1.0, and
2. **the keyword component is not bounded**, so the proposed “divide by 11” fix is not mathematically valid as stated.  

So I would say: **the ranking recipe is broadly correct; the score calibration is not**.

## Is the current scoring algorithm conceptually correct?

For entity search, yes, mostly.

The implementation is:

* exact match: `+10.0`
* semantic: cosine similarity × `0.6`
* keyword: `ts_rank` × `0.4`  

That is a classic additive hybrid. For C++ functional entities with Doxygen text, this makes sense because users usually fall into one of three modes:

* they know the symbol exactly,
* they know approximate terminology,
* they know behavioral intent but not the name.

Your design covers all three.

Where it goes off the rails is that after ranking, you normalize by the **best result for that query**, so the best result is always 1.0 even when the query is garbage. That is exactly the issue documented in I-002.  

So:

* **Ranking order**: often fine.
* **Displayed score meaning**: currently misleading.

That distinction matters.

## Why this is especially tricky for Doxygen on C++ functions

Doxygen function docs are not ordinary prose documents. They have a peculiar structure:

* symbol name and signature,
* brief/details,
* params/returns,
* notes/rationale,
* sometimes caller-usage text.  

That means retrieval quality depends on **which field carries the useful evidence** for a given query.

Examples:

* “damage” or exact function lookup should be dominated by **name/signature**.
* “apply poison over time” may live in **details** or **rationale**.
* “used to send text to a character” may live mainly in **usages**, not the entity’s own brief.  

So a single flat score over one big reconstructed docstring is serviceable, but it is not ideal. The conceptual issue is not hybrid retrieval itself; it is that your corpus is **fielded** and your current score is only weakly field-aware.

## What I think the real problem is

I think you actually have **three distinct problems**, not one.

### 1. Score calibration problem

This is the explicit bug.

Per-query normalization makes the score relative, not absolute. A nonsense query still gets a top score of 1.0. 

That means agents cannot tell:

* “this is a genuinely strong match”
  from
* “this is simply the least bad result.”

That is a real defect.

### 2. Data quality / corpus pollution problem

Your usage search issue is not fundamentally a retrieval problem. It is also a **bad corpus rows** problem.

Rows like “not used directly” and “not referenced” are semantically valid but behaviorally useless, and they pollute usage retrieval. The issue writeup is right about that. 

So even with better scoring, garbage evidence rows will still dilute top-k behavior.

### 3. Entity identity problem

The split declaration/definition rows are likely hurting search more than the scoring discussion suggests.

If one entity has the graph metrics and the other has the useful text, then ranking, downstream traversal, and result interpretation all become unstable. That is I-001, and it is probably the highest-value fix. 

In other words: some of what looks like “search quality trouble” is actually **indexing/merge corruption**.

## Where I agree with the feedback, and where I’d refine it

The feedback file is basically right:

* the hybrid design is fundamentally sound,
* I-001 should be fixed first,
* the proposed fixed-ceiling normalization is flawed if `ts_rank` is left unbounded.  

I agree with that.

I would add one refinement:

### I would not over-optimize for a single `[0,1]` scalar

A single normalized score is attractive, but for an MCP documentation server it may be more useful to expose **component scores**:

* `exact_match: bool`
* `semantic_score`
* `keyword_score`
* `combined_score`

That is often more agent-friendly than trying to cram everything into one “perfectly calibrated” number.

Why? Because exact symbol match is qualitatively different from semantic proximity. A combined scalar hides that distinction.

An agent can do better reasoning with:

* “exact=true, semantic modest, keyword strong”
  than with
* “score=0.83”.

## Alternatives I would seriously consider

## Option A: Keep the current additive hybrid, but fix calibration

This is the lowest-risk path.

Use the existing architecture, but:

* normalize the keyword component before combining,
* stop per-query max normalization,
* optionally expose raw component scores. 

Why this is good:

* minimal code change,
* preserves current ranking behavior,
* makes scores usable,
* aligns with the current spec and implementation shape. 

This is the path I would choose first.

## Option B: Reciprocal Rank Fusion instead of weighted score addition

For your use case, RRF is a very strong alternative.

Instead of trying to combine incomparable numeric scales from:

* exact lookup,
* semantic similarity,
* full-text rank,

you fuse their **ranks** rather than their raw scores.

Why it may be better here:

* avoids the `ts_rank` calibration headache entirely,
* robust when the different retrieval channels have different score distributions,
* often works better in practice for heterogeneous corpora like code docs.

Why it may be worse:

* you lose an intuitive absolute score unless you add a separate confidence estimate,
* less transparent if you want threshold-based filtering.

My view: **RRF is probably the cleanest conceptual alternative** if you care primarily about ranking quality, not score semantics.

## Option C: Two-stage retrieval

This is the best medium-term design.

Stage 1:

* retrieve candidates using exact + keyword + semantic.

Stage 2:

* rerank top 20–50 using a more field-aware scorer.

The reranker could be simple and symbolic, not necessarily a heavy ML model:

* boost exact name match,
* boost signature token overlap,
* boost matches in `brief` and `rationale`,
* demote docs with only weak usage evidence,
* reward entities with richer evidence fields.

Why this fits C++/Doxygen well:

* function docs are structured,
* users often search by intent plus symbol clues,
* field-aware reranking exploits that structure better than a single flat embedding pass.

## Option D: Separate retrieval by source/field and fuse later

You already started moving this direction with `source="entity"` vs `source="usages"`.  

I would push that idea further:

* `name/signature` retrieval
* `entity doc` retrieval
* `usage description` retrieval
* maybe `source_text/definition_text` retrieval

Then combine at the entity level.

Why this is attractive:

* different evidence channels answer different user intents,
* avoids forcing one embedding and one score to do everything.

For Doxygen-heavy docs, this is often better than pretending the reconstructed docstring is the whole truth.

## Option E: Learned calibration or reranking

This is only worth it if you can build a judged query set.

If you have enough examples of:

* query
* relevant entities
* irrelevant entities

then a lightweight learned reranker or calibration model could outperform hand-tuned weights.

But absent evaluation data, I would not jump here yet. Hand-tuned hybrids usually get you far enough for doc servers.

## What I would not do

I would not rely on “one embedding over one reconstructed Doxygen blob” as the final design.

It is okay as a baseline, but it conflates:

* API identity,
* internal mechanism,
* caller-observed behavior,
* source-code lexical evidence.

Those are different retrieval targets.

## My recommended diagnosis

If your question is “why are results feeling wrong?”, my answer is:

### The core algorithm is not the main villain

The current hybrid is conceptually okay.

### The main issues are:

* **bad score semantics** from per-query normalization, 
* **unmerged split entities** causing evidence fragmentation, 
* **low-value usage rows** polluting retrieval, 
* **field mixing** in a corpus where different fields answer different kinds of questions. 

So I would not conclude “the scoring algorithm is fundamentally wrong for Doxygen docstrings.” I would conclude:

> The hybrid retrieval idea is correct, but the system currently mixes ranking, calibration, and corpus-quality problems together, which makes the score look worse than the ranking strategy really is.

## Practical recommendation order

1. **Fix split entities first.**
   This is a data integrity problem, not a tuning problem, and it affects search, graph traversal, and contract-seed logic. 

2. **Fix score calibration next.**
   Either:

* normalize keyword scores before weighting and then use a fixed ceiling, or
* stop pretending the combined scalar is a calibrated probability and expose raw/component scores. 

3. **Filter negative-evidence usage rows at build time.**
   That is cheap and likely high impact. 

4. **Then evaluate whether the remaining ranking quality is actually insufficient.**
   Only after those fixes would I decide whether to move to RRF or two-stage reranking.

## My preferred design

If I were tuning this server, I would do:

* exact-match channel,
* BM25/FTS channel,
* embedding channel,
* usage channel separated from entity-doc channel,
* RRF or field-aware reranking at the entity level,
* expose component evidence instead of over-trusting one scalar.

That gives you better robustness for C++/Doxygen retrieval without making the system much more complicated.

## Final answer

So, to your direct question:

* **Is your current scoring algorithm conceptually correct?**
  **Yes, in broad strokes.** The hybrid additive design is a reasonable fit for Doxygen docstrings on C++ functions.

* **Is the current implementation producing a useful search score?**
  **No, not as an absolute quality signal.** Per-query normalization makes it misleading, and fixed-ceiling normalization is invalid unless keyword scores are bounded first.  

* **What alternatives would I consider?**
  First, calibrated additive hybrid with component scores.
  Second, RRF.
  Third, two-stage field-aware reranking.
  Long term, separate evidence channels for entity docs vs usage docs.

* **What is my take on the real problem?**
  The biggest issue is probably **not the hybrid idea**. It is **evidence fragmentation, score calibration, and corpus hygiene**.
