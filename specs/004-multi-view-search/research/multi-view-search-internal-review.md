# Multi-view search: internal review

Addresses concerns raised in internal review of the round 2 response before it goes
back to the external reviewer.

---

## 1. How do exact match, jaccard, and cross-encoder actually interact?

The round 2 document handwaves "the combination of that boolean + jaccard +
cross-encoder reranking handles the rest." That isn't a mechanism description.

Here is how the pipeline actually works:

1. **Retrieval channels** produce candidate sets (stages 1-2). A candidate enters
   the pool because it scored above a retrieval threshold in at least one channel.

2. **Intermediate scoring** (stage 3) computes a signal vector per candidate. These
   signals — jaccard, shaped keyword scores, semantic scores, trigram, coverage —
   exist for **filtering**, not ranking.

3. **Filtering** (stage 4) removes candidates where no signal exceeds its floor.
   This kills noise. The cross-encoder never sees garbage.

4. **Cross-encoder** (stage 5) produces the **final ranking**. It scores each
   surviving `(query, entity_text)` pair. This is the only ranking that matters for
   the returned result order.

The intermediate signals (including jaccard, keyword, semantic) do NOT combine into
a weighted score. They're independent thresholds for the binary keep/discard
decision in stage 4. The cross-encoder alone determines order.

### Where does exact-match fit?

An exact bare-name match is not a *scoring* signal. It is a **filter bypass**: if
the query string exactly equals an entity's bare name, that entity survives
filtering regardless of its other signal values.

This is justified because: an entity whose name is literally the query string is
never noise. Even if its semantic and keyword scores are low (because it has sparse
documentation), it's what the agent asked for.

This is NOT the same as the +10.0 boost hack. The hack was:
- exact match → add 10 to a weighted score → the score determines rank

The new design is:
- exact match → survive filtering (guaranteed candidate for cross-encoder)
- cross-encoder → determines rank among all surviving candidates

The exact-match entity's final position depends on the cross-encoder scoring
`(query, entity_text)`, not on a numeric boost. If the agent searched for "name"
and there's an entity called `name` that is a struct field with no docs, it would
survive filtering but rank below a well-documented function called `set_name` that
the cross-encoder scores higher.

There is no weighted combination of exact-match + jaccard + cross-encoder. These
operate at different pipeline stages for different purposes.

### Is exact-match redundant with other signals?

Probably yes in most cases. An entity with exact name match will typically also
score high on jaccard, symbol_keyword, trigram, and symbol_semantic. It would
survive filtering even without a special rule.

The exception: an entity with exact name match but extremely sparse documentation
(no brief, no details, no params) might have low keyword and semantic scores if
there's little text to match. The filter bypass ensures these sparse-but-exact
entities are not lost.

This is a defensive mechanism, not a ranking mechanism.

---

## 2. Where does "merging cross-encoder outputs" happen?

It doesn't, under the current architecture.

The round 2 document accepted the reviewer's concern about "a harder merge
downstream" when justifying a single cross-encoder. But that concern applies to a
design where two cross-encoders each produce a score and those scores are combined.
That's not what we're doing.

Within a single search call:
- One candidate pool (from multi-channel retrieval)
- One filtering pass
- One cross-encoder pass over survivors
- One ranked result list

There is no merge of two cross-encoder outputs at any point.

The question is: what text does the cross-encoder see? Two options:

**Option A: One cross-encoder, assembled text.**
The cross-encoder scores `(query, assembled_entity_text)` where the assembled text
includes symbol identity and doc prose. One score per candidate. One model handles
everything.

**Option B: Two cross-encoders, per-view text.**
A code cross-encoder scores `(query, symbol_text)`. A prose cross-encoder scores
`(query, doc_text)`. For each candidate, we have two scores. We need a rule to
produce a single ranking — max, weighted sum, or some other combination.

Option B has the merge problem: two incomparable scores from different models that
must be combined into one ranking. This IS the calibration issue the reviewer warned
about.

Option A avoids the merge by having one model see the complete picture. But it bets
on one model being adequate for both symbol-heavy and prose-heavy queries.

### Revised position

The user is right that "start with one, add another later" is forbidden. We should
design for the architecture we want.

The DI-based `RetrievalView` architecture already supports per-view cross-encoders
at no additional design cost. The question is purely about **ranking quality**.

**Design:** Each view carries its own cross-encoder as a configurable parameter.
For the initial implementation, both the symbol view and the doc view use the same
cross-encoder model (e.g., `BAAI/bge-reranker-base`) but the text assembly differs:
- Symbol view passes `(query, symbol_text)` to its cross-encoder
- Doc view passes `(query, doc_text)` to its cross-encoder

The per-view cross-encoder produces a score. The final ranking uses the **maximum
cross-encoder score across views** for each candidate. This is a simple,
calibration-free merge rule: a candidate that scores 0.9 on the symbol view and
0.3 on the doc view ranks by 0.9. No weighted combination, no normalization.

If evaluation shows that one cross-encoder model underperforms on one view's text
format, swapping in a different model for that view is a config change, not a
rearchitecture. The design supports heterogeneous models from day one; whether we
use that capability depends on evaluation results.

---

## 3. symbol_text construction: what belongs, what doesn't

### Parameter names

Parameter names are optional in C++ declarations and not part of the symbol's
identity. `void stc(const String&, Character*)` and `void stc(const String& txt,
Character* ch)` are the same function. Parameter names should be in `doc_text`
(they help explain what the params do) but not in `symbol_text`.

### Constness and type qualification

Constness IS part of a C++ unique signature. `void foo(const int&)` and
`void foo(int&)` are different overloads. Dropping constness from symbol_text would
make overloads indistinguishable. Type qualification is likewise critical:
`affect::type` and `skill::type` are completely different symbols.

`symbol_text` should preserve:
- kind
- bare name
- const/volatile qualifiers
- type qualifications (namespace::class prefixes)
- return type
- parameter types (with const and qualification)
- parameter order (positionally meaningful)
- containing scope (namespace, class, file)

`symbol_text` should **not** include:
- parameter names
- documentation prose
- source code

### What about embedding the signature directly?

The user raises a good point: if we use a code-aware embedding model like
`jina-embeddings-v2-base-code`, it already knows how to embed `void stc(const
String&, Character*)`. Why construct a decomposed symbol_text at all? Why not
just embed the actual signature?

Because the signature alone lacks scoping context. `void type()` means nothing
without `affect::type` vs `skill::type`. The signature as written in C++ doesn't
always include the namespace/class prefix (it may be in the function's definition
but not its declaration).

So `symbol_text` = **scoped signature** — the signature with full qualification
prepended, in a format the code model can embed well. Not a decomposed bag of
tokens. More like:

```
Logging::stc void stc(const String&, Character*)
```

or for the code model:

```
void Logging::stc(const String&, Character*)
```

This is almost the `definition_text` we already store, just with the qualification
ensured. The code model embeds this naturally — it's a C++ function declaration.

### Redundancy in symbol search channels

The concern: we're embedding the signature (symbol_semantic), tokenizing it
(symbol_keyword), trigramming it (trigram_sim), Jaccarding it (token_jaccard),
AND coverage-checking it. Five ways of saying "does this symbol match?"

But these serve different retrieval needs:
- **symbol_semantic** (embedding): finds conceptually similar symbols even when
  tokens don't match. `send_to_char` and `stc` are semantically related in code
  embedding space even though they share no tokens.
- **symbol_keyword** (simple tsvector): finds exact token matches. `stc` matches
  documents containing the stem `stc`. Fast, precise, no false positives.
- **trigram** (pg_trgm): finds partial and fuzzy matches. `stc` matches `stc_color`.
  `char` matches `Character`. Neither embedding nor tsvector catches these.
- **jaccard** and **coverage**: computed on candidates already retrieved. Not
  retrieval channels — intermediate filtering/scoring signals.

The first three are *retrieval* channels (produce candidates from the database).
The last two are *scoring* signals (computed on candidates already in memory).
The redundancy in "this candidate matches" is fine — the point of multi-channel
retrieval is recall. Multiple channels confirming a match means high confidence
that candidate belongs in the pool.

---

## 4. The hybrid doc field problem and model choice

The user suggests preferring the code-aware model as long as it handles natural
language adequately. This is the right instinct.

`jinaai/jina-embeddings-v2-base-code` describes itself as "Multilingual (English,
30 programming languages)." If it handles both English prose and C++ symbols in
one embedding space, it might be the right choice for BOTH `doc_text` and
`symbol_text` embeddings.

This would mean:
- One embedding model instead of two
- One query embedding per search (shared across both views)
- Still two separate pgvector columns (doc_embedding and symbol_embedding contain
  different text, even if the model is the same)
- Still two separate tsvectors (different dictionaries)

Whether this works depends on whether jina-code embeds English prose as well as
bge-base-en-v1.5 does. If the code model's prose embedding quality is 90% of a
dedicated prose model, that's probably fine — the tsvector channel handles the
lexical gap. If it's 70%, we need two models.

**This is an evaluation question.** Before committing to one vs. two models, we
should run representative queries against both models and compare recall@K on our
actual corpus. The architecture supports either configuration — the `RetrievalView`
carries its model as a parameter.

**What the spec should say:** The architecture uses `RetrievalView` instances with
configurable embedding models. The initial evaluation will compare:
- jina-code for both views
- jina-code for symbol + bge-base for doc
- bge-base for both (baseline)

The decision follows from evaluation on representative queries, not from
architectural assumption.

---

## 5. ts_rank vs. pgvector: what value does each add?

These are fundamentally different retrieval mechanisms.

### tsvector + ts_rank (keyword/lexical search)

- **How it works:** Text is tokenized into stems using a dictionary (english or
  simple). Stems are stored in a GIN inverted index. At query time, the query is
  tokenized the same way, and the index finds documents containing those stems.
  `ts_rank` scores matches by term frequency, position, document length, and
  weight labels (A/B/C/D).
- **What it's good for:** Exact term matching. If the query contains `stc`, it
  finds every document containing the token `stc`. No ambiguity, no hallucination.
  Rare terms, code identifiers, domain jargon — if the token exists in the
  document, it matches.
- **What it's bad for:** Synonyms, paraphrases, conceptual similarity. "send text
  to buffer" will NOT match a document about "output message to character" because
  the stems are different. It also can't handle semantics at all — it's purely
  lexical.

### pgvector cosine similarity (semantic/embedding search)

- **How it works:** Text is compressed into a dense 768-dim vector by a neural
  model. At query time, the query is also embedded, and cosine similarity finds
  the nearest vectors in an HNSW index. The similarity reflects what the model
  learned about semantic relationships during training.
- **What it's good for:** Semantic matching. "send text" and "output message" are
  nearby in embedding space because the model learned they mean similar things.
  Conceptual queries work: "functions that handle player combat" surfaces combat
  functions even if their docs don't use the word "combat."
- **What it's bad for:** Exact term matching of rare tokens. The model may not
  have seen `stc` or `PLR_COLOR2` during training, so their embeddings are
  meaningless. Short queries (1-2 tokens) often embed poorly. The model can
  "hallucinate" similarity between unrelated concepts if they share distributional
  context.

### Why both?

| Query type | tsvector finds it | pgvector finds it |
|---|---|---|
| `stc` (exact identifier) | YES | Maybe not |
| `void stc(const String&, Character*)` | Partially (tokenized) | Maybe (if code model) |
| "send formatted text to character" | Only if exact stems match | YES |
| "output buffering functions" | Only if docs say "output" and "buffer" | YES |
| `PLR_COLOR2` (rare macro) | YES | Unlikely |
| "functions related to colored text display" | Partial | YES |

Every row has at least one "partial" or "no." Neither channel alone covers all
query types. Their blind spots are complementary. This is the fundamental argument
for hybrid search — it's not redundancy, it's recall coverage.

---

## Decisions to carry forward

1. **Exact match = filter bypass, not scoring signal.** No numeric boost. No
   weighted combination. The cross-encoder decides rank.

2. **Per-view cross-encoders, max-score merge rule.** Architecture supports
   heterogeneous models from day one. Initial deployment may use the same model
   on both views, but the infrastructure doesn't assume it.

3. **symbol_text = qualified scoped signature.** Not a decomposed token bag. The
   code model embeds the signature in its natural form. Constness, type
   qualification, parameter order preserved. Parameter names excluded.

4. **Embedding model choice is an evaluation question.** Architecture is
   model-agnostic via `RetrievalView`. Evaluate jina-code on prose before assuming
   two models are needed — one model for both views is preferable if quality is
   sufficient.

5. **ts_rank and pgvector are complementary, not redundant.** Keyword catches
   exact tokens that semantic misses. Semantic catches meaning that keyword misses.
   Both stay.
