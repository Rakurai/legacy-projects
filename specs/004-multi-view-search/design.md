# Multi-view search: design

Locked design for the multi-view search pipeline. Supersedes `reranking.md` and
the reviewer discussion documents (`multi-view-search-review.md`,
`multi-view-search-round2.md`, `multi-view-search-internal-review.md`).

This document is the input to the implementation spec.

---

## 1. Schema changes

### 1.1 Entity table — columns

| Column | Type | Status | Description |
|--------|------|--------|-------------|
| `doc_embedding` | Vector(768) | **New** (replaces `embedding`) | Dense embedding of doc prose fields |
| `symbol_embedding` | Vector(768) | **New** | Dense embedding of qualified scoped signature |
| `doc_search_vector` | TSVECTOR | **New** (replaces `search_vector`) | Weighted english-dict tsvector over prose fields |
| `symbol_search_vector` | TSVECTOR | **New** | Simple-dict tsvector over symbol fields |
| `symbol_searchable` | TEXT | **New** | Lowercased, punctuation-stripped text for trigram index |
| `qualified_name` | TEXT | **New** | Fully-qualified name (e.g., `Logging::stc`) derived from containment graph |
| `embedding` | Vector(768) | **Drop** | Replaced by `doc_embedding` |
| `search_vector` | TSVECTOR | **Drop** | Replaced by `doc_search_vector` |

### 1.2 Indexes

| Index | Type | Column(s) | Notes |
|-------|------|-----------|-------|
| `ix_entities_doc_embedding` | HNSW | `doc_embedding` | `vector_cosine_ops`, m=16, ef_construction=64 |
| `ix_entities_symbol_embedding` | HNSW | `symbol_embedding` | Same params |
| `ix_entities_doc_search_vector` | GIN | `doc_search_vector` | |
| `ix_entities_symbol_search_vector` | GIN | `symbol_search_vector` | |
| `ix_entities_symbol_searchable_trgm` | GiST | `symbol_searchable` | `gist_trgm_ops` (requires `pg_trgm` extension) |

### 1.3 Field construction

**`doc_search_vector`** — english dictionary, weighted:

```sql
setweight(to_tsvector('english', COALESCE(name, '')), 'A') ||
setweight(to_tsvector('english', COALESCE(brief, '') || ' ' || COALESCE(details, '')), 'B') ||
setweight(to_tsvector('english', COALESCE(notes, '') || ' ' || COALESCE(rationale, '')), 'C') ||
setweight(to_tsvector('english', COALESCE(
    (SELECT string_agg(value, ' ') FROM jsonb_each_text(params)), ''
)), 'C') ||
setweight(to_tsvector('english', COALESCE(returns, '')), 'C')
```

**`symbol_search_vector`** — simple dictionary, weighted:

```sql
setweight(to_tsvector('simple', COALESCE(name, '')), 'A') ||
setweight(to_tsvector('simple', COALESCE(qualified_name, '')), 'B') ||
setweight(to_tsvector('simple', COALESCE(signature, '')), 'B') ||
setweight(to_tsvector('simple', COALESCE(definition_text, '')), 'C')
```

**`symbol_searchable`** — derived at build time:

```
lower(name || ' ' || qualified_name || ' ' || signature)
```

With punctuation stripped (remove `*`, `&`, `(`, `)`, `,`, `;`). Lowercase.
Used only for `pg_trgm` similarity queries.

**`qualified_name`** — derived at build time from the containment graph.
Walk `contained_by` edges to reconstruct `Namespace::Class::name`. For entities
whose containment graph path is incomplete, fall back to parsing `definition_text`
for `::` scoping. Store explicitly — do not reconstruct at query time.

---

## 2. Embedding surfaces

Two text surfaces, each embedded independently.

### 2.1 `doc_embed_text`

Prose fields assembled with shallow field labels for the cross-encoder (and as
embedding input):

```
BRIEF: Sends formatted text to a Character's output buffer
DETAILS: Formats the text using the Character's color preferences and writes
it to the output buffer for later flushing.
PARAMS: txt: The String containing the formatted text; ch: Target Character pointer
RETURNS: void
NOTES: Called from nearly every output path in the game engine.
RATIONALE: Centralized output formatting ensures consistent color handling.
```

Field labels are short, stable, and regular. Fields with no content are omitted
(no `NOTES:` line if notes is null).

### 2.2 `symbol_embed_text`

Qualified scoped signature in natural C++ form:

```
void Logging::stc(const String&, Character*)
```

Construction rules:
- Return type + qualified scope + bare name + parameter type list
- **Include:** constness, type qualification, parameter order, containing scope
- **Exclude:** parameter names (not part of identity), documentation prose
- Qualified scope derived from `qualified_name` (containment graph at build time)
- For non-function entities (classes, structs, variables, etc.), use
  `qualified_name` alone (e.g., `Logging::log_level`)

### 2.3 Embedding model

Architecture supports one or two embedding models via `RetrievalView`
parameterization:

- **Preferred:** One code-aware model for both views
  (`jinaai/jina-embeddings-v2-base-code`, 768-dim). Handles mixed
  code+prose content natively. Simpler operationally.
- **Fallback:** Code model for symbol view, prose model
  (`BAAI/bge-base-en-v1.5`, 768-dim) for doc view. Only if evaluation
  shows the code model's prose quality is insufficient.

**Resolution:** Empirical evaluation against representative queries on
our corpus before implementation. The schema and pipeline are identical
either way.

---

## 3. Search pipeline

Seven stages. No weighted score combination. No per-query normalization.

### Stage 1: Candidate generation

Five parallel retrieval channels, each producing a set of `(entity_id, raw_score)`
pairs:

| # | Channel | Source | Method | Dict |
|---|---------|--------|--------|------|
| 1 | doc_semantic | `doc_embedding` | pgvector cosine similarity | — |
| 2 | symbol_semantic | `symbol_embedding` | pgvector cosine similarity | — |
| 3 | doc_keyword | `doc_search_vector` | `ts_rank` | english |
| 4 | symbol_keyword | `symbol_search_vector` | `ts_rank` | simple |
| 5 | trigram | `symbol_searchable` | `pg_trgm` similarity | — |

Each channel retrieves up to N candidates (N determined empirically; channels
are independent and can have different N values). The query is embedded
by the appropriate model for semantic channels.

### Stage 2: Union + dedupe

Merge all candidate sets by `entity_id`. Each entity appears once regardless
of how many channels produced it.

### Stage 3: Intermediate scoring

For each candidate in the merged set, compute the following signal vector.
These signals are for filtering only — they do not determine final ranking.

| Signal | Type | Range | Description |
|--------|------|-------|-------------|
| `doc_semantic` | float | [0, 1] | Cosine similarity from doc embedding |
| `symbol_semantic` | float | [0, 1] | Cosine similarity from symbol embedding |
| `doc_keyword` | float | [0, 1] | Log-shaped ts_rank from doc tsvector |
| `symbol_keyword` | float | [0, 1] | Log-shaped ts_rank from symbol tsvector |
| `trigram_sim` | float | [0, 1] | pg_trgm similarity score |
| `name_exact` | bool | — | Bare name exact match (case-sensitive) |
| `token_jaccard` | float | [0, 1] | Jaccard over query tokens vs name+sig tokens |
| `query_coverage` | float | [0, 1] | Fraction of query non-stopword terms found in entity doc text |

**ts_rank shaping:** Raw ts_rank values are transformed via
`log(1 + score) / log(1 + ceiling)` where `ceiling` is the 99th percentile
ts_rank across all entities for that tsvector (computed once at build time
or server startup and cached). Clamped to [0, 1]. Each tsvector channel has
its own ceiling — doc and symbol distributions differ.

**Jaccard** operates on compact symbol token sets (query tokens vs
name + signature tokens). Appropriate for symbol-bearing queries.

**Query coverage** operates on doc prose fields (fraction of query
non-stopword tokens appearing in the entity's searchable doc text).
Appropriate for multi-term prose queries. The split between jaccard and
query coverage is justified by the different token distributions — symbol
strings are compact and high-signal; doc text is long and asymmetric.

### Stage 4: Filtering

Per-signal floor thresholds. A candidate is **discarded** if no signal
exceeds its respective floor.

**Exception:** `name_exact=true` bypasses filtering — the candidate survives
regardless of other signal values.

`name_exact` bypass serves its purpose because in a 5,300-entity corpus,
bare-name exact matches are almost always what the agent wanted. Common English
words that happen to be identifiers (`name`, `count`) will produce a handful
of extra candidates that the cross-encoder handles naturally. The cost
(a few extra cross-encoder evaluations) does not justify adding a query-shape
classifier.

Floor thresholds are determined empirically and configured per-channel.

### Stage 5: Cross-encoder reranking

Each `RetrievalView` carries its own cross-encoder as a configurable parameter.
For each surviving candidate:

1. **Symbol view** scores `(query, symbol_embed_text)` via its cross-encoder
2. **Doc view** scores `(query, doc_embed_text)` via its cross-encoder

Per-candidate ranking score = `max(symbol_ce_score, doc_ce_score)`.

This is a calibration-free merge. No weighted combination, no normalization
across views.

**Metadata preserved per candidate:**
- `winning_view`: which view produced the max score (`"symbol"` or `"doc"`)
- `winning_score`: the max cross-encoder score
- `losing_score`: the other view's cross-encoder score

The ranking uses `winning_score` only. The losing score and winning view
label are carried as metadata — available to the agent or for future
refinements if cross-view corroboration proves useful. This costs nothing
since both scores are already computed.

**Cross-encoder text format:** The doc view uses **lightly structured text**
with stable field labels (as shown in §2.1). Not flat prose concatenation.
The structure helps the cross-encoder distinguish "what the function does"
from "what parameter `ch` means." The symbol view uses `symbol_embed_text`
as-is (the natural qualified signature).

**Cross-encoder model selection:** Both views may share the same model (config
decision). Candidates for benchmarking:
- `BAAI/bge-reranker-base` (278M params) — natural first candidate
- `Xenova/ms-marco-MiniLM-L-6-v2` (22M params) — fast alternative
- `jinaai/jina-reranker-v1-turbo-en` — fast, 8K context

Resolution by benchmarking representative queries before implementation.

### Stage 6: Top-K

Return the top K reranked results with metadata:
- `search_mode` (hybrid, keyword_fallback)
- `winning_view` per result
- `winning_score` and `losing_score` per result

---

## 4. Build pipeline changes

### 4.1 New build functions

| Function | Input | Output | Description |
|----------|-------|--------|-------------|
| `build_doc_embed_text(entity)` | Entity fields | str | Assembles labeled prose text (§2.1) |
| `build_symbol_embed_text(entity)` | Entity fields + qualified_name | str | Assembles qualified scoped signature (§2.2) |
| `derive_qualified_name(entity, containment_graph)` | Entity + graph | str | Walks containment edges to build qualified name |
| `build_symbol_searchable(entity)` | name, qualified_name, signature | str | Lowercased, punctuation-stripped text for trigrams |

### 4.2 Embedding generation

- One or two embedding passes depending on model evaluation outcome
- Entity cache files: `embed_cache_{model}_{dim}_doc.pkl` and
  `embed_cache_{model}_{dim}_symbol.pkl`
- Uses existing `save_embedding_cache` / `load_embedding_cache` with
  `embedding_type="doc"` and `embedding_type="symbol"`

### 4.3 Tsvector generation

Two UPDATE statements after entity insertion:
1. `doc_search_vector` — english dict, weighted (§1.3)
2. `symbol_search_vector` — simple dict, weighted (§1.3)

### 4.4 Symbol searchable + qualified name

- `qualified_name` derived from containment graph at build time, stored as column
- `symbol_searchable` derived from name + qualified_name + signature, stored as column
- GiST trigram index created after population

### 4.5 ts_rank ceiling computation

At build time (or server startup), compute 99th percentile ts_rank for each
tsvector across the full entity set. Store as server config / cached values.
Used for log-shaping in stage 3.

---

## 5. DI / extensibility

### 5.1 RetrievalView abstraction

Each `RetrievalView` encapsulates:
- Embedding model reference
- Embedding column name
- Tsvector column name and dictionary
- Cross-encoder model reference
- Scoring parameters (ts_rank ceiling, floor thresholds)
- Text assembly function (doc vs symbol)

The V1 entity layer has two views: `symbol_view` and `doc_view`.

### 5.2 Future doc layers

Each future doc layer (subsystem docs, help entries, builder guide) is a new
view instance with appropriate model selection. Views can share models.

Cross-layer search (when `source=all` is needed) merges per-layer results by
max-score across views, not score fusion. Results carry their source layer as
metadata. The agent interprets cross-layer relevance. No intent classifier
or layer budget allocator on the server.

Per-layer search tools remain the primary interface. Agents use typed tools
(`search`, `search_subsystem_docs`, `search_help_docs`, `search_builder_guide`),
not a universal search box.

---

## 6. What this replaces

### Current search.py (to be rewritten)

| Current | New |
|---------|-----|
| `_exact_match_ids` → +10.0 boost | `name_exact` boolean → filter bypass |
| `_keyword_scores` → single english tsvector | Two tsvectors (doc + symbol) + trigram channel |
| `_semantic_scores` → single embedding | Two embeddings (doc + symbol) |
| `_merge_scores` → weighted sum with per-query normalization | No weighted sum, no normalization. Cross-encoder determines rank. |
| `_SCORE_THRESHOLD = 0.2` on combined score | Per-signal floor thresholds in filtering stage |

### Current db_models.py Entity

| Current column | Disposition |
|----------------|-------------|
| `embedding` (Vector 768) | Drop. Replaced by `doc_embedding` + `symbol_embedding` |
| `search_vector` (TSVECTOR) | Drop. Replaced by `doc_search_vector` + `symbol_search_vector` |

### Current embeddings_loader.py

| Current | Disposition |
|---------|-------------|
| `build_minimal_embed_text` | Splits into `build_doc_embed_text` + `build_symbol_embed_text` |
| `generate_embeddings` (single pass) | One or two passes with type="doc" / type="symbol" |
| Single `embed_cache_{model}_{dim}_entity.pkl` | Two caches: `_doc.pkl` and `_symbol.pkl` |

---

## 7. Decisions log

Positions locked through three reviewer rounds.

| # | Decision | Rationale |
|---|----------|-----------|
| D-01 | Exact bare-name match = filter bypass, not scoring signal | Cross-encoder alone determines rank. No +10.0 hack. |
| D-02 | No query-shape gating on name_exact bypass | 5,300 entities — extra candidates from common-word names are negligible |
| D-03 | ts_rank log-shaped with empirical ceiling per channel | Unbounded ts_rank needs monotone nonlinear shaping before thresholding |
| D-04 | Per-view cross-encoders with max-score merge | Calibration-free. Avoids weighted combination of cross-scale scores. |
| D-05 | Preserve both view scores as metadata | winning_view + winning_score + losing_score carried per result. Free since both are computed. |
| D-06 | symbol_text = qualified scoped signature in natural C++ form | Code-aware model embeds this directly. Preserves constness, type qualification, parameter order. |
| D-07 | Structured fields remain as Entity columns | symbol_text is derived, not a replacement. Jaccard and exact-match operate on structured fields. |
| D-08 | Store `qualified_name` as explicit column | Fundamental identity data, frequently useful. Derived from containment graph at build time. |
| D-09 | Prefer one code-aware model for both views | jina-code handles mixed code+prose. Resolve by evaluation. Schema identical either way. |
| D-10 | Keep both trigram and simple-dict FTS for symbols | Complementary blind spots: FTS for token identity, trigrams for partials/fuzzy. |
| D-11 | Jaccard for symbol tokens, query-term-recall for doc tokens | Different token distributions warrant split metrics. |
| D-12 | Cross-encoder sees lightly structured text (doc view) | Shallow field labels reduce ambiguity in heterogeneous source text. |
| D-13 | Per-layer typed tools, no server-side intent routing | Agent is the intent interpreter. Per-layer RetrievalView for future layers. |
| D-14 | No per-query normalization | Root cause of the original scoring problem. Eliminated entirely. |

---

## 8. Open evaluation items

These require empirical testing before implementation can finalize parameter values.
The architecture is not blocked by them — they affect config, not structure.

| Item | What to evaluate | Resolution |
|------|------------------|------------|
| E-01 | jina-code prose quality on our corpus | Determines 1 vs 2 embedding models |
| E-02 | Cross-encoder model selection | Benchmark bge-reranker-base, ms-marco-MiniLM, jina-reranker on representative queries |
| E-03 | Per-channel N (retrieval limits) | How many candidates each channel needs to not miss relevant entities |
| E-04 | Per-signal floor thresholds | Empirical: what floors separate signal from noise per channel |
| E-05 | ts_rank ceiling values | 99th percentile ts_rank per tsvector across full entity set |
| E-06 | Top-K value | How many results agents actually consume (likely 10-20) |

---

## 9. Out of scope

- `hybrid_search_usages` — separate pipeline design, deferred
- I-003 (low-quality usage descriptions) — addressed by usage pipeline design
- Cross-layer `source=all` search — future, per-layer tools are the V1 interface
- Trained classifier for filtering — only if deterministic floors prove insufficient
- Intent classification / layer budget allocation — agent handles intent
