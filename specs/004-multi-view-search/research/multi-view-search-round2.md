# Multi-view search: reviewer round 2

Incorporates reviewer's second-round feedback plus our own analysis of what matters
for the actual agent use cases (spec-creating agents and system planning agents).

---

## Point-by-point

### 1. Exact match vs. jaccard

**Reviewer says:** Don't replace exact match with jaccard. Exactness is qualitatively
different from overlap.

**Our position:** We agree that exact bare-name match is a strong signal that should
survive as a distinct feature — not because the agent needs a label that says "exact
match", but because of the degenerate jaccard case the reviewer identifies: `foo(A,
B, C, D)` and `bar(A, B, C, D)` have high jaccard on the full signature despite
being completely different functions. The bare name is the one token where exact
equality is categorically stronger than high overlap.

However, we do not need exact *signature* match or exact *qualified name* match as
separate features. Once the name matches exactly, signature and qualified name
differences are fine-grained disambiguation signals the reranker handles naturally.
Four "exact match" features is over-engineering for our use case — agents iterate
results and read briefs to disambiguate.

**Decision:** Keep **exact bare-name match** as a boolean feature alongside jaccard.
Drop the +10.0 boost hack. Do not add exact-signature or exact-qualified-name as
separate features.

To be precise about how this works in the pipeline: exact bare-name match is a
**filter bypass**, not a scoring signal. The pipeline stages are:

1. **Retrieval** channels produce candidate sets.
2. **Intermediate scoring** computes signal vectors (jaccard, keyword, semantic, etc.)
   for filtering — not for ranking.
3. **Filtering** removes candidates where no signal exceeds its floor.
   `name_exact=true` is a bypass: the candidate survives filtering regardless of
   other signal values.
4. **Cross-encoder** produces the final ranking. It scores each surviving
   `(query, entity_text)` pair. This is the only ranking that matters.

There is no weighted combination of exact-match + jaccard + cross-encoder. These
operate at different pipeline stages for different purposes. Exact-match guarantees
candidacy; jaccard and other signals determine the keep/discard threshold; the
cross-encoder alone determines order.

This differs from the current +10.0 boost hack because the hack was `exact match →
add 10 to a weighted score → the score determines rank`. In the new design, an
exact-match entity's final position depends entirely on the cross-encoder scoring
`(query, entity_text)`, not on a numeric boost. If the agent searched for "name"
and there's a sparsely-documented struct field called `name`, it would survive
filtering but could rank below a well-documented `set_name` function that the
cross-encoder scores higher.

### 2. ts_rank shaping

**Reviewer says:** ts_rank is not bounded. Need per-channel shaping before
thresholding or combining.

**Agreed.** This was already identified in our earlier discussions. `ts_rank` returns
unbounded floats — the PostgreSQL docs describe it as proportional to term frequency
and document length, with typical values in [0, 0.1] but no ceiling.

For context on what ts_rank actually represents: it is a TF-IDF-like relevance score
that computes a weighted sum of term matches against the tsvector, where weights come
from the A/B/C/D label assignments. It accounts for document length and term position
but does not normalize to any fixed range.

**Decision:** Each keyword channel produces a raw ts_rank value. Before any
cross-channel comparison or filtering:

1. Apply monotone nonlinear shaping (log transform: `log(1 + score) / log(1 + ceiling)`)
   where `ceiling` is determined empirically from the corpus (99th percentile ts_rank
   across all entities for that tsvector).
2. Clamp to [0, 1].
3. Per-channel floor filtering: if the shaped score is below the channel's threshold,
   the candidate is not contributed by this channel.

No raw ts_rank values ever participate in cross-channel arithmetic. The shaped
values are still not directly comparable across channels (symbol tsvector vs doc
tsvector have different distributions), but they are individually thresholdable.

### 3. Cross-encoder reranking: per-view architecture

**Reviewer says:** Two cross-encoders may create a harder merge problem. A
code-aware cross-encoder might already be good on both symbol and prose. Question
whether dual rerankers improve ordering on their slices without creating a harder
merge downstream.

**The reviewer's concern applies to a specific design:** one where two cross-encoders
each produce a score and those scores are combined via weighted sum or similar. That
would recreate the calibration problem we're escaping.

But the concern does not apply if the merge rule avoids cross-scale comparison.

**Design:** Each `RetrievalView` carries its own cross-encoder as a configurable
parameter. For each surviving candidate, each view's cross-encoder scores
`(query, view_text)` — the symbol view passes `(query, symbol_text)`, the doc view
passes `(query, doc_text)`. The final ranking uses the **maximum cross-encoder score
across views** for each candidate.

This is a calibration-free merge: a candidate scoring 0.9 on the symbol view and 0.3
on the doc view ranks by 0.9. No weighted combination, no normalization across views.
A candidate that is strong in one view is ranked by that strength regardless of how
it scores in the other.

Whether the two views use the same model or different models is a configuration
choice, not an architecture choice. The DI-based `RetrievalView` supports
heterogeneous models from day one. If the same cross-encoder model handles both
symbol and prose text adequately, both views share that model. If evaluation shows
one view needs a specialized model, it's a config swap.

fastembed supports several cross-encoder models via `TextCrossEncoder` (in
`fastembed.rerank.cross_encoder`):
- `Xenova/ms-marco-MiniLM-L-6-v2` (22M params, fast)
- `Xenova/ms-marco-MiniLM-L-12-v2` (33M params)
- `BAAI/bge-reranker-base` (278M params, higher quality)
- `jinaai/jina-reranker-v1-tiny-en` (fast, 8K context)
- `jinaai/jina-reranker-v1-turbo-en` (fast, 8K context)
- `jinaai/jina-reranker-v2-base-multilingual`

We should benchmark 2-3 of these against representative queries before committing.
`BAAI/bge-reranker-base` is the natural first candidate since we already use the
BAAI/bge family for embeddings.

**Note on cross-layer search:** This same per-view max-score merge applies to future
doc layers (subsystem docs, help entries, builder guide). Each layer's view has its
own cross-encoder; cross-layer search uses max-score across views. No scores are
combined across views at any point. Results carry their source layer as metadata, and
the agent interprets cross-layer relevance.

### 4. symbol_text construction

**Reviewer says:** Keep symbol fields separable. Don't let symbol_text become a
baggy pseudo-doc. `Character` as a type is not the same as in a namespace.

**Agreed.** `symbol_text` is a derived search surface for embedding, not a
replacement for structured field storage.

A code-aware embedding model (e.g., `jina-embeddings-v2-base-code`) already knows
how to embed a C++ function signature. So `symbol_text` should be a **qualified
scoped signature** — the signature with full namespace/class qualification — not a
decomposed bag of tokens. The code model embeds this in its natural form.

Example for `void stc(const String&, Character*)` in namespace `Logging`:

```
void Logging::stc(const String&, Character*)
```

This preserves:
- **Constness** — `const int&` vs `int&` are different overloads in C++, and
  constness is part of a unique signature
- **Type qualification** — `affect::type` and `skill::type` are completely different
  symbols
- **Parameter order** — positionally meaningful in C++ signatures
- **Containing scope** — namespace and class prefixes derived from the containment
  graph at build time

This does **not** include:
- **Parameter names** — technically optional in C++ declarations and not part of
  symbol identity. `void stc(const String& txt, Character* ch)` and
  `void stc(const String&, Character*)` are the same function. Parameter names
  belong in `doc_text` where they help explain what the params do.
- **Documentation prose** — that's the doc view's job

**For storage:** The individual fields (bare name, qualified name, signature,
parameter types, return type, containing namespace/class/file) remain as structured
columns in the Entity table. `symbol_text` is derived at build time from these
fields and stored alongside them — not instead of them. The jaccard overlap and
exact-name-match features operate on the structured fields, not on `symbol_text`.

**On symbol search channel redundancy:** We have symbol_semantic (embedding),
symbol_keyword (simple tsvector), and trigram (pg_trgm) as retrieval channels, plus
jaccard and coverage as intermediate scoring signals. The retrieval channels are not
redundant — they have non-overlapping blind spots:

- **symbol_semantic** finds conceptually similar symbols even when tokens don't
  match (`send_to_char` and `stc` may be nearby in code embedding space despite
  sharing no tokens)
- **symbol_keyword** finds exact token matches (`stc` finds documents containing
  the stem `stc` — precise, no false positives)
- **trigram** finds partial and fuzzy matches (`stc` matches `stc_color`, `char`
  matches `Character` — neither embedding nor tsvector catches these)

Jaccard and coverage are computed on candidates already in memory — they're scoring
signals for the keep/discard decision, not retrieval channels.

**Open question for spec:** Do we need a stored `qualified_name` column on Entity?
Currently the Doxygen XML `qualifiedname` element is parsed but dropped (not on the
`DoxygenEntity` model). The containment graph has ~6,500 `contained_by` edges that
encode the same information, and `definition_text` carries `::` scoped names for
functions. We can derive qualified scope from the containment graph at build time
without adding a new artifact dependency.

### 5. Cross-layer intent gating

**Reviewer says:** Broad search across layers needs intent gating / layer budget
allocation, not just merging independent result sets.

**Our position:** The reviewer is thinking about a human-facing search system where
ambiguous natural language queries need to be routed. Our system is different in two
ways:

1. **Agents use typed tools, not a universal search box.** The tool surface in
   `speculative_agent_reqs.md` has per-layer search tools: `search` (entities),
   `search_subsystem_docs`, `search_help_docs`, `search_builder_guide`. Agents call
   the tool corresponding to what they're looking for. The MCP prompts guide agents
   through specific workflows: research_feature, orient_to_system, trace_behavior.
   Agents don't make ambiguous "how does the combat system work" queries — they make
   targeted calls to specific tools.

2. **The server exposes prompts, not intelligence.** The MCP server is explicitly
   not an intelligent router (per `speculative_agent_reqs.md` §1). It doesn't
   interpret intent — it returns what's asked for. The agent handles intent.

That said: a `source=all` cross-layer search mode is planned for V2+. The reviewer
is right that simply interleaving independently-ranked results will produce noisy
cross-layer results. But the solution is not intent classification on the server —
it's per-layer retrieval views with typed results that the agent can distinguish.

**Decision:** Per-layer search tools are the primary interface. If/when `source=all`
cross-layer search is added:
- Results carry their source layer as metadata (entity / subsystem_doc / help / guide)
- Each layer's candidates are scored and filtered within their own view
- The merge is by interleaving ranked results per-layer, not by combining scores
- The agent decides how to weight layers based on its task context

No intent classifier or layer budget allocator on the server. The agent is the
intent interpreter.

### 6. Non-FTS symbol lexical matching (trigrams, substrings, prefixes)

**Reviewer says:** Symbol retrieval needs trigram/substring/prefix matching beyond
tsvector for partial identifiers, glued names, casing variants, namespace fragments.

**This is a real gap.** PostgreSQL's `pg_trgm` extension provides trigram similarity
and `LIKE`/`ILIKE` index support. For our corpus:

- Partial identifier searches (`stc` matching `stc_color`, `stc_buf`)
- CamelCase/snake_case variant matching (`CharacterData` vs `character_data`)
- Namespace fragment matching (`Logging::` prefix)
- Type fragment matching (`Character*` finding all functions taking Character params)

These are common patterns for spec-creating agents looking up entities they've seen
referenced in call graphs or source code.

**Decision:** Add `pg_trgm`-based trigram similarity as a fifth retrieval channel on
the symbol search path. This operates on a stored `symbol_searchable` column (bare
name + qualified name + signature, lowercased, punctuation-stripped) with a GiST
trigram index. This channel contributes candidates just like the other four channels.

This is a meaningful addition to recall that the other channels miss entirely — an
embedding of "stc" and an embedding of "stc_color" are not necessarily close in
vector space, and `simple` tsvector tokenization splits on punctuation boundaries
so `stc_color` becomes two tokens `stc` and `color`.

### 7. Model-per-view vs. model-per-language-register

**Reviewer says:** Don't assume every layer needs its own embedding model. The real
split is code-centric vs. prose-centric.

**Agreed.** At most two embedding models:
- **Code model** (e.g., `jinaai/jina-embeddings-v2-base-code`, 768-dim): for
  `symbol_text` embeddings across all layers that have symbol content
- **Prose model** (`BAAI/bge-base-en-v1.5`, 768-dim): for `doc_text` embeddings
  across all layers that have natural language prose

Subsystem docs, migration guides, and help entries would all use the prose model
since they are natural language. Only the code entity layer has a symbol-text surface
that warrants the code model.

The `RetrievalView` abstraction carries its embedding model as a parameter, so views
can share models without coupling.

**However:** the doc fields (brief, details, params, returns) contain a mix of
natural language and C++ symbols (see "Hybrid doc field problem" below). If the code
model (e.g., jina-code, which describes itself as "Multilingual: English +
30 programming languages") handles English prose adequately, it could serve as the
*sole* embedding model for both views. This is preferable if quality is sufficient —
one model for both views is simpler operationally and avoids any temptation to
compare embeddings across different spaces.

Whether one model suffices or two are needed is an evaluation question to be resolved
by running representative queries against our corpus before committing. The
architecture supports either configuration via `RetrievalView` parameterization.

### 8. Query coverage

**Reviewer says:** Add explicit query coverage — a candidate matching all query terms
moderately is often better than one matching one term very strongly.

**Our position asked:** Isn't coverage modeled by jaccard?

On reflection: partially, but not sufficiently. Jaccard measures set overlap, which
is a coverage proxy for symbol tokens. But for multi-term prose queries like "damage
calculation with armor reduction", jaccard over the full entity text is noisy (too
many tokens in the entity). What matters is whether the entity's searchable text
covers the *query* terms, not the other way around.

A better formulation: **query term recall** — what fraction of the query's
non-stopword tokens appear somewhere in the candidate's searchable fields? This is
cheap to compute on the candidate set (tokenize query, check membership against
candidate's token set) and is arguably more useful than jaccard for multi-term
queries.

**Decision:** Add query term recall as an intermediate scoring signal alongside
jaccard, semantic scores, and shaped keyword scores. For the symbol channel, jaccard
on name+signature tokens is the right metric. For the doc channel, query term recall
over doc fields is the right metric. These are complementary, not redundant.

---

## The hybrid doc field problem

The `brief`, `details`, `params`, and `returns` fields contain a mix of natural
language and C++ symbols. Example from a real entity:

> **brief:** "Sends formatted text to a Character's output buffer"
> **params:** `{txt: "The String containing the formatted text", ch: "Target Character pointer"}`

`Character` here is a C++ class name, but the english tsvector stemmer will treat it
as a common English word. A purely prose-focused embedding model will embed it in
natural-language-concept space, not code-symbol space.

This is the same "one muddled representation" problem, but at the field level rather
than the entity level.

**Options:**

1. **Use a code-aware embedding model for doc_text too.** If the code model (e.g.,
   jina-code) handles English prose adequately, it naturally handles C++ symbols
   appearing in English sentences — it was trained on exactly this mixed content.
   This would mean one embedding model for both views, which avoids the problem
   entirely at the embedding layer.

2. **Accept the blurring with a prose model.** The doc_text embedding is for
   prose/behavioral retrieval. If someone searches for "Character" meaning the
   class, the symbol channel handles it. The doc channel finding "character" in
   prose surfaces entities that *talk about* characters — arguably a feature.

3. **Symbol extraction from doc fields.** At build time, identify C++ symbol tokens
   in doc fields (by cross-referencing entity names, type names, and known
   identifiers) and add them to the symbol_text/symbol_search_vector. This way
   "Character" appears in both channels.

4. **Dual tsvector for doc fields.** Build the doc_search_vector twice: once with
   `english` dict (for prose queries) and once with `simple` dict (for
   symbol-in-prose queries). This doubles the GIN index cost for marginal gain.

**Decision:** The preferred approach is option 1 — use the code-aware model for
both views if evaluation shows it handles prose adequately. As noted in §7, jina-code
describes itself as supporting English alongside 30 programming languages, so it is
designed for exactly this mixed-register content. Falling back to option 2 (accept
blurring) if the code model's prose quality is insufficient. Options 3 and 4 are
targeted fixes to hold in reserve if evaluation reveals a systematic gap.

---

## Why both tsvector keyword search and pgvector semantic search?

These are fundamentally different retrieval mechanisms with complementary blind spots.

**tsvector + ts_rank** is lexical/keyword search. Text is tokenized into stems via a
dictionary, stored in a GIN inverted index, and matched on exact token presence.
`ts_rank` scores by term frequency, position weight (A/B/C/D labels), and document
length. If the query contains `stc`, it finds every document containing the stem
`stc` — no ambiguity. But "send text to buffer" will NOT match a document about
"output message to character" because the stems are different. It is purely lexical.

**pgvector cosine similarity** is semantic search. Text is compressed into a dense
768-dim vector by a neural model, and similarity is computed in that space. "send
text" and "output message" are nearby because the model learned they're semantically
related. But it may miss exact identifiers — `stc` as a query embedding may not be
close to `stc` in a document embedding if the model treats 3-letter tokens as noise.

| Query type | tsvector finds it | pgvector finds it |
|---|---|---|
| `stc` (exact identifier) | YES | Maybe not |
| `void stc(const String&, Character*)` | Partially (tokenized) | Maybe (if code model) |
| "send formatted text to character" | Only if exact stems match | YES |
| "output buffering functions" | Only if docs say "output" and "buffer" | YES |
| `PLR_COLOR2` (rare macro) | YES | Unlikely |
| "functions related to colored text display" | Partial | YES |

Neither channel alone covers all query types. Their blind spots are complementary.
This is the fundamental argument for hybrid search — it's not redundancy, it's
recall coverage.

---

## Revised architecture summary

### Schema changes (Entity table)

| Current | Proposed |
|---------|----------|
| `embedding` (Vector 768) | `doc_embedding` (Vector 768) |
| — | `symbol_embedding` (Vector 768) |
| `search_vector` (TSVECTOR, english) | `doc_search_vector` (TSVECTOR, english dict: brief, details, notes, rationale, params, returns) |
| — | `symbol_search_vector` (TSVECTOR, simple dict: name, qualified scope, signature, definition, param types) |
| — | `symbol_searchable` (TEXT: lowercased, punctuation-stripped name+qualified+sig for trigram index) |

Old `embedding` and `search_vector` columns are dropped. Embedding model choice
(one code-aware model for both views, or code + prose models) is resolved by
evaluation; the schema is the same either way.

### Build pipeline changes

- **New:** `build_doc_embed_text(entity)` — assembles prose fields for doc embedding
- **New:** `build_symbol_embed_text(entity)` — assembles qualified scoped signature
  for code embedding (no parameter names; preserves constness and type qualification)
- **New:** One or two embed passes depending on model evaluation
- **New:** Two tsvector UPDATE statements (english and simple dictionaries)
- **New:** `symbol_searchable` column population + GiST trigram index
- **New:** Derive qualified scope from containment graph at build time
- **Changed:** `build_minimal_embed_text` splits into doc and symbol variants

### Search pipeline (7 stages, expanded)

1. **Candidate generation** — 5 parallel channels:
   - Semantic over doc_embedding (cosine, query embedded by doc model)
   - Semantic over symbol_embedding (cosine, query embedded by symbol model)
   - Keyword over doc_search_vector (ts_rank, english dict, shaped)
   - Keyword over symbol_search_vector (ts_rank, simple dict, shaped)
   - Trigram over symbol_searchable (pg_trgm similarity)

2. **Union + dedupe** — merge by entity_id

3. **Intermediate scoring** — per-candidate signal vector:
   - `doc_semantic`: cosine similarity from doc embedding [0, 1]
   - `symbol_semantic`: cosine similarity from symbol embedding [0, 1]
   - `doc_keyword`: log-shaped ts_rank from doc tsvector [0, 1]
   - `symbol_keyword`: log-shaped ts_rank from symbol tsvector [0, 1]
   - `trigram_sim`: pg_trgm similarity [0, 1]
   - `name_exact`: boolean, bare name exact match
   - `token_jaccard`: jaccard over query tokens vs name+sig tokens [0, 1]
   - `query_coverage`: fraction of query terms found in entity text [0, 1]

4. **Filtering** — per-signal floors, discard candidates where no signal exceeds
   its floor. name_exact=true bypasses filtering (always survives).

5. **Reranking** — per-view cross-encoders:
   - Symbol view scores `(query, symbol_text)` via its cross-encoder
   - Doc view scores `(query, doc_text)` via its cross-encoder
   - Per-candidate final score = `max(symbol_view_score, doc_view_score)`
   - Views may share the same cross-encoder model (config decision)

6. **Top-K** — return reranked results with search_mode metadata.

### DI / extensibility

The `RetrievalView` abstraction encapsulates: embedding model, tsvector config,
cross-encoder, scoring parameters, and filtering thresholds. Each doc layer in
future versions (subsystem docs, help entries, builder guide) is a new view instance
with appropriate model selection. Views can share models.

Cross-layer search (when `source=all` is needed) merges per-layer results by
max-score across views, not score fusion. Results carry their source layer as
metadata. The agent interprets cross-layer relevance. No intent classifier or layer
budget allocator on the server.

---

## Questions for the reviewer

1. **Trigram channel vs. FTS overlap:** For symbol retrieval, we'll have both
   `simple`-dict tsvector and `pg_trgm` trigram similarity. The tsvector handles
   exact token matching; trigrams handle partial/fuzzy matching. Is there a case
   where these two are redundant and one should be dropped, or should both stay?

2. **Cross-encoder text assembly:** Each view's cross-encoder sees its respective
   text (symbol_text or doc_text). For the doc view, should this be structured
   (e.g., `BRIEF: ...\nDETAILS: ...\nPARAMS: ...`) or flat prose? Structured
   format may help the cross-encoder attend to the right fields, but ms-marco
   models were trained on flat text pairs.

3. **Coverage vs. jaccard nuance:** We're proposing jaccard for symbol tokens and
   query-term-recall for doc tokens. Is there a case where a unified coverage
   metric works better, or is the split justified by the different token
   distributions?

4. **symbol_text as qualified signature:** We propose using the qualified scoped
   signature in its natural C++ form (e.g., `void Logging::stc(const String&,
   Character*)`) rather than a decomposed token list. The code-aware embedding model
   is trained on code and can embed this directly. Does this seem right, or do you
   see cases where the natural signature form hurts retrieval compared to a
   normalized decomposition?
