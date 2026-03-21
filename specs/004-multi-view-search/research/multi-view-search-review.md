# Multi-view search architecture — reviewer discussion

Response to reviewer feedback on search representation, embeddings, and scoring layers.

## What we're adopting

### 1. Two embedding models over two derived text views

We'll embed two distinct text surfaces per entity:

- **`doc_text`** (brief, details, rationale, notes, param descriptions, return description) — embedded with **BAAI/bge-base-en-v1.5** (our current model). This is the prose/behavioral retrieval surface.
- **`symbol_text`** (a normalized symbol-centric string: kind, name, qualified scope, signature tokens, parameter types, return type, file/class/namespace context) — embedded with a **code-oriented model** (likely **BAAI/bge-code-v1** or similar from fastembed's catalog). This is the identifier/structural retrieval surface.

These two views are never conflated into one embedding space. Retrieval from each produces candidates scored within its own model, and the reranker operates over assembled entity text using its own cross-encoder — so there's no need for the embedding spaces to be comparable.

We will **not** embed a `full_text` combined view. The two-view retrieval already covers the recall concern: symbol queries surface through `symbol_text`, behavioral queries through `doc_text`, and mixed queries will produce candidates from both channels. A third "catch-all" embedding that blends both surfaces re-introduces the dilution problem you identified.

### 2. Two separate tsvectors with appropriate tokenizers

- **`symbol_search_vector`** — tsvector over name, qualified name, signature, definition text, parameter names/types. Built with PostgreSQL's **`simple` dictionary** (no stemming, no stop words). This means searching for `String`, `Character`, `stc`, `PLR_COLOR2` works as direct token matching without English stemming mangling identifier tokens.
- **`doc_search_vector`** — tsvector over brief, details, notes, rationale, param descriptions, return description. Built with **`english` dictionary** (stemming, stop word removal). This is the right config for prose queries like "send text to a character buffer."

The current single weighted tsvector (name=A, brief+details=B, definition=C, source_text=D) with english stemming everywhere is exactly the "one muddled representation" problem you described. Splitting it solves the concrete issue where `Character` gets treated as an English word rather than a C++ type name.

### 3. Multi-view candidate generation in the reranking pipeline

The revised pipeline has four retrieval channels:

1. Semantic over `doc_embedding` (cosine similarity)
2. Semantic over `symbol_embedding` (cosine similarity)
3. Keyword over `doc_search_vector` (ts_rank, english)
4. Keyword over `symbol_search_vector` (ts_rank, simple)

These are parallel candidate generators. Their union forms the candidate pool. Each retriever contributes a bounded signal per candidate that the scoring/filtering stage can use independently — no linear combination into a single fused score.

### 4. Token overlap (jaccard) replaces exact match

For symbol-layer retrieval, we'll compute token-set jaccard between the query and the entity's name + signature + qualified scope. This replaces the current binary exact-match (+10.0 boost) with a continuous, bounded [0,1] signal. Exact match is just jaccard = 1.0.

### 5. Dual cross-encoders for reranking

Since the two embedding spaces are separate, the reranker needs to work across both. We'll use:

- A **prose cross-encoder** (e.g., `cross-encoder/ms-marco-MiniLM-L-6-v2`) scoring `(query, doc_text)` pairs
- A **code-aware cross-encoder** scoring `(query, symbol_text)` pairs

The final ranking combines both cross-encoder scores. This avoids forcing one cross-encoder to handle both "send text to character" and `void stc(const String&, Character*)` query types.

The embedding providers, cross-encoders, and their scoring logic will be encapsulated behind dependency-injected abstractions — a `RetrievalView` or similar, so each view carries its own embedding model + cross-encoder + scoring parameters. This also makes adding a new retrieval surface (see doc layers below) a new instance configuration, not a code redesign.

## Scoping: what we have, what we'll surface

You recommended "qualified name, file / namespace / class context" as part of symbol identity. We agree — relying solely on file_path for scoping is naive. Here's what we actually have available from Doxygen:

- **Containment graph edges** (~6,500 `contained_by` edges): member → file, member → class/struct, member → namespace, member → group. These give us the structural scope hierarchy.
- **`definition_text`** on functions: carries C++ qualified names like `bool RoomID::is_valid(...)`, `void Logging::bug(...)`.
- **`qualified_name`** from Doxygen XML: currently parsed but dropped (not stored on the entity model). We can surface this.
- **Compound hierarchy**: every member knows its parent compound ID (file, class, namespace), and compounds know their containment parents.

For the `symbol_text` view, we'll derive a structural scope string from the containment graph at build time — something like `namespace::class::name(params)` — rather than relying on file path as the sole context signal. This scope string also becomes part of the `symbol_search_vector` tsvector (using `simple` dictionary).

## What we're deferring to a separate spec

**Similarity links** (symbol-family, behavioral-doc, role/capability, field-specific topical links): These are graph enrichment features, not search features. They add navigational value ("show me functions behaviorally similar to this one") but don't improve the search-retrieve-rerank pipeline. We'll address them in a dedicated graph enrichment spec — they're a real feature, not discarded.

## A concern we want your input on: doc layers

The current system indexes C++ source code documentation (Doxygen-extracted + LLM-enriched). Future versions will add:

- **v2**: Curated subsystem documentation (architectural overviews, design rationale written by humans/LLMs about the system as a whole)
- **v3**: Migration/building guides (how-to guides for reimplementing subsystems in the target framework)
- **v4**: User-facing help content (in-game help text, player documentation)

These live at different semantic scales — subsystem docs are closer to code docs, building guides are closer to subsystem docs, and user help is the most distant. Searching across all of them with one embedding/metric model seems likely to degrade precision on all layers.

Our current plan: the DI-based view architecture naturally supports adding new `RetrievalView` instances per doc layer. Each layer gets its own embedding model, tsvector config, cross-encoder, and filtering thresholds — same pipeline structure, different parameterization. The tool layer decides which views to query based on the tool being called (a code-search tool queries code views; a system-doc-search tool queries doc views; a broad search could query across views and merge).

**Question for you**: Does this "view-per-layer" architecture seem sound, or do you see cases where cross-layer retrieval needs more than just merging independently-scored candidate sets? Our concern is that a query like "how does the combat system work" might need to surface both code entities and subsystem docs, and simply interleaving two independent result sets might not rank well across the boundary.
