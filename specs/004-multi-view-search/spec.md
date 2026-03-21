# Feature Specification: Multi-View Search Pipeline

**Feature Branch**: `004-multi-view-search`
**Created**: 2026-03-21
**Status**: Draft
**Input**: User description: "Implement multi-view search pipeline for MCP doc server: dual embeddings (doc + symbol), dual tsvectors (english + simple), trigram index, 7-stage search pipeline with cross-encoder reranking, RetrievalView DI abstraction"

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Symbol-Precise Entity Lookup (Priority: P1) 🎯 MVP

An AI agent has seen a function name in a call graph or source excerpt — `stc`, `do_look`, `PLR_COLOR2` — and needs to find the matching entity. The agent searches for the identifier and receives results where the exact-name match and structurally similar symbols rank highest, regardless of how sparse their documentation is. Fuzzy and partial matches (`stc` finding `stc_color`, `char` finding `Character`) also surface when the exact name has no hit.

**Why this priority**: Symbol lookup is the most frequent search operation. Agents iterate search → `get_entity` → graph traversal hundreds of times per research session. If symbol retrieval fails to surface the right entity, the entire downstream workflow breaks. The current system's English stemmer mangles C++ identifiers (`Character` stemmed as a common English word) and the +10.0 exact-match hack produces unreliable rankings.

**Independent Test**: Search for known identifiers (`stc`, `do_look`, `damage`, `PLR_COLOR2`, `Character`) and verify the correct entity appears in top-3 results. Search for partial identifiers (`stc` matching `stc_color`) and verify fuzzy matches appear. Search for a misspelled identifier and verify trigram similarity surfaces plausible candidates.

**Acceptance Scenarios**:

1. **Given** a query matching an entity's bare name exactly, **When** the agent searches, **Then** that entity appears in results regardless of how sparse its documentation is
2. **Given** a query like `stc` with no exact name match, **When** the agent searches, **Then** entities with names like `stc_color`, `stc_buf` appear via trigram similarity
3. **Given** a C++ type name like `Character`, **When** the agent searches, **Then** the symbol search channel treats it as an identifier (simple dictionary, no stemming), not an English word
4. **Given** a qualified name query like `Logging::stc`, **When** the agent searches, **Then** results include the entity whose qualified scope matches, ranked above unscoped `stc` occurrences
5. **Given** a complete signature `void damage(Character *ch, Character *victim, int dam)`, **When** the agent searches, **Then** the exact entity ranks first via symbol token overlap

---

### User Story 2 — Behavioral / Conceptual Search (Priority: P1)

An AI agent researching a migration topic needs to find entities by what they *do*, not what they're *named*. The agent searches with natural language queries like "send formatted text to character output buffer" or "poison spreading between characters" and receives results ranked by semantic and keyword relevance across documentation prose (brief, details, rationale, notes, params).

**Why this priority**: Equally critical as symbol lookup — spec-creating agents need to discover entities they don't yet know the names of. The current system's single embedding conflates code identifiers with prose, degrading both. Separating doc-prose retrieval into its own view with an English-stemmed tsvector and a dedicated embedding surface fixes this.

**Independent Test**: Search for "functions that handle player death processing" and verify results include `do_kill`, `raw_kill`, `death_cry` and similar entities with relevant documentation. Search for "poison spreading between characters" and verify results surface poison-related entities even if their names don't contain "poison".

**Acceptance Scenarios**:

1. **Given** a natural language query like "send formatted text to character", **When** the agent searches, **Then** results include entities whose documentation describes text output functions, ranked by semantic similarity
2. **Given** a multi-term prose query, **When** the agent searches, **Then** entities matching more query terms rank higher than those matching only one term strongly (query coverage signal)
3. **Given** a query matching documentation prose but not any entity name, **When** the agent searches, **Then** results include those entities (the doc view surfaces them even though the symbol view doesn't)

---

### User Story 3 — Noise Filtering and Reranking (Priority: P2)

An AI agent issues a search query and receives only relevant results — no garbage with confident-looking scores. Weak candidates are eliminated before they consume agent context window. The final ranking is produced by cross-encoder reranking, not by a combined numeric score that the agent needs to interpret.

**Why this priority**: The root cause of the current search problem is per-query normalization making the top result always score 1.0, plus unbounded `ts_rank` values producing unreliable combinations. This story addresses the quality problem directly: agents stop wasting context on noise, and the score becomes meaningful (cross-encoder relevance, not a homegrown weighted sum).

**Independent Test**: Search for a nonsense query ("xyzzy foobar baz") and verify zero results are returned (no garbage with high scores). Search for a real query and verify all returned results are plausibly relevant — no entities that have nothing to do with the query.

**Acceptance Scenarios**:

1. **Given** a nonsense query with no relevant entities, **When** the agent searches, **Then** zero results are returned (filtering eliminates all candidates)
2. **Given** a real query producing candidates, **When** results are returned, **Then** each result carries `winning_view` (`"symbol"` or `"doc"`), `winning_score`, and `losing_score` metadata
3. **Given** multiple candidates survive filtering, **When** the cross-encoder ranks them, **Then** a well-documented entity that semantically matches the query ranks above a sparsely-documented entity that merely shares a name token
4. **Given** a query that matches entities across both views, **When** results are returned, **Then** the ranking uses the maximum cross-encoder score across views (not a weighted combination)

---

### User Story 4 — Qualified Name Navigation (Priority: P3)

An AI agent examining a class hierarchy or namespace structure needs to find entities by their fully-qualified C++ scope. The agent searches for `Logging::stc` or `Character::position` and receives results scoped to the correct namespace/class, disambiguating entities with the same bare name but different containing scopes.

**Why this priority**: Qualified names are essential for disambiguation in a codebase where many entities share bare names (e.g., `type` in multiple classes). The current system has no qualified name column — all scoping is through `file_path`, which is lossy. This story depends on the containment graph traversal added in the build pipeline.

**Independent Test**: Search for `Logging::stc` and verify the entity inside the `Logging` scope ranks above any unscoped `stc`. Verify that the `qualified_name` column in the database contains correct scoped names derived from the containment graph.

**Acceptance Scenarios**:

1. **Given** a query containing `::` scope separators, **When** the agent searches, **Then** entities whose `qualified_name` matches the query scope rank highest
2. **Given** two entities with the same bare name in different scopes, **When** the agent searches for `Scope::name`, **Then** the correctly-scoped entity appears above the other
3. **Given** a containment graph with nested scopes, **When** the build pipeline derives `qualified_name`, **Then** it produces `Namespace::Class::member` by walking `contained_by` edges

---

### Edge Cases

- **Empty query string**: Return zero results, not an error
- **Query is a single character** (e.g., `a`): Trigram similarity may produce many low-quality matches; per-signal floor filtering should eliminate them
- **Entity with no documentation and no meaningful name** (e.g., anonymous structs): May not survive filtering — this is acceptable; these entities are not useful search targets
- **Embedding provider or cross-encoder model unavailable at startup**: The system MUST fail fast with a clear error — these are hard requirements, not optional
- **Entity appears in multiple retrieval channels**: Deduplication ensures it appears only once in the merged candidate set; a candidate survives filtering if at least one signal exceeds its respective floor threshold (FR-036)
- **ts_rank returns extreme values for short documents with high term density**: Log-shaping with empirical ceiling prevents unbounded scores from distorting filtering
- **Containment graph has incomplete paths** (entity's scope chain is broken): Parse `definition_text` for `::` scoping as the secondary source; if neither yields a scope, `qualified_name` = bare name
- **Query contains both identifier tokens and prose** ("damage function that handles player death"): Both symbol and doc channels contribute candidates; the cross-encoder ranks based on the best-matching view

## Clarifications

### Session 2026-03-21

- Q: How should the system behave when no embedding provider is configured — keyword-only mode, error, or startup refusal? → A: No fallbacks allowed (PATTERNS.md). Embedding provider and cross-encoder are hard requirements. Server must fail fast at startup. All existing fallback infrastructure (SearchMode.KEYWORD_FALLBACK, embedding_enabled, optional EmbeddingProvider) must be removed.

## Requirements *(mandatory)*

### Functional Requirements

#### Schema Changes

- **FR-001**: Entity table MUST replace `embedding` column with two new vector columns: `doc_embedding` (Vector) and `symbol_embedding` (Vector), both using the dimension from `EMBEDDING_DIMENSION` env var
- **FR-002**: Entity table MUST replace `search_vector` column with two new tsvector columns: `doc_search_vector` (english dictionary, weighted) and `symbol_search_vector` (simple dictionary, weighted)
- **FR-003**: Entity table MUST add `symbol_searchable` TEXT column containing lowercased, punctuation-stripped text (name + qualified_name + signature) for trigram indexing
- **FR-004**: Entity table MUST add `qualified_name` TEXT column storing fully-qualified names derived from the containment graph at build time (e.g., `Logging::stc`, `Character::position`)
- **FR-005**: Database MUST have HNSW indexes on both `doc_embedding` and `symbol_embedding` (vector_cosine_ops, m=16, ef_construction=64)
- **FR-006**: Database MUST have GIN indexes on both `doc_search_vector` and `symbol_search_vector`
- **FR-007**: Database MUST have a GiST trigram index on `symbol_searchable` using `gist_trgm_ops` (requires `pg_trgm` extension)
- **FR-008**: Build script MUST enable the `pg_trgm` extension (`CREATE EXTENSION IF NOT EXISTS pg_trgm`)

#### Doc Search Vector Construction

- **FR-010**: `doc_search_vector` MUST be built using the `english` dictionary with weights: name='A', brief+details='B', notes+rationale+params(values concatenated)+returns='C'
- **FR-011**: `doc_search_vector` MUST NOT include source_text or definition_text (these are code, not prose)

#### Symbol Search Vector Construction

- **FR-012**: `symbol_search_vector` MUST be built using the `simple` dictionary (no stemming, no stop words) with weights: name='A', qualified_name+signature='B', definition_text='C'
- **FR-013**: `symbol_search_vector` MUST NOT include documentation prose fields

#### Symbol Searchable Text Construction

- **FR-014**: `symbol_searchable` MUST be derived at build time as `lower(name || ' ' || qualified_name || ' ' || signature)` with punctuation characters (`*`, `&`, `(`, `)`, `,`, `;`) stripped
- **FR-015**: `symbol_searchable` MUST be used only for `pg_trgm` similarity queries, not for embedding or tsvector search

#### Qualified Name Derivation

- **FR-016**: Build pipeline MUST derive `qualified_name` by walking `contained_by` edges in the dependency graph to reconstruct the scope chain (e.g., `Namespace::Class::name`)
- **FR-017**: When the containment graph path is incomplete, build pipeline MUST derive scope from parsing `definition_text` for `::` separators
- **FR-018**: `qualified_name` MUST be stored as an explicit column — not reconstructed at query time

#### Embedding Text Surfaces

- **FR-020**: Build pipeline MUST construct `doc_embed_text` per entity using labeled prose fields: `BRIEF: ...`, `DETAILS: ...`, `PARAMS: ...`, `RETURNS: ...`, `NOTES: ...`, `RATIONALE: ...` — omitting labels for null/empty fields. When all prose fields are null/empty, `doc_embed_text` MUST fall back to the entity's bare name (every entity gets a `doc_embedding`).
- **FR-021**: Build pipeline MUST construct `symbol_embed_text` per entity as the qualified scoped signature in natural C++ form (e.g., `void Logging::stc(const String&, Character*)`)
- **FR-022**: `symbol_embed_text` MUST include return type, qualified scope, bare name, and parameter types with const/volatile qualifiers
- **FR-023**: `symbol_embed_text` MUST NOT include parameter names or documentation prose
- **FR-024**: For non-function entities (classes, structs, variables), `symbol_embed_text` MUST use `qualified_name` alone (e.g., `Logging::log_level`)

#### Embedding Generation

- **FR-025**: Build pipeline MUST generate two separate embedding caches: `embed_cache_{model}_{dim}_doc.pkl` and `embed_cache_{model}_{dim}_symbol.pkl`
- **FR-026**: Both caches MUST use the existing `sync_embeddings_cache` infrastructure with `embedding_type="doc"` and `embedding_type="symbol"`
- **FR-027**: Architecture MUST support one or two embedding models via `RetrievalView` parameterization — determined by evaluation, not hard-coded

#### Search Pipeline

- **FR-030**: Search MUST use five parallel candidate retrieval channels: doc semantic (pgvector cosine on `doc_embedding`), symbol semantic (pgvector cosine on `symbol_embedding`), doc keyword (`ts_rank` on `doc_search_vector`), symbol keyword (`ts_rank` on `symbol_search_vector`), trigram (`pg_trgm` similarity on `symbol_searchable`). Entities with null values in a channel's column are excluded from that channel's query.
- **FR-031**: Candidate sets from all five channels MUST be merged by `entity_id` — each entity appears at most once in the merged set
- **FR-032**: For each candidate, the system MUST compute an intermediate signal vector with the following 8 signals: `doc_semantic`, `symbol_semantic`, `doc_keyword`, `symbol_keyword`, `trigram_sim`, `name_exact`, `token_jaccard`, `query_coverage`
- **FR-033**: Raw `ts_rank` values MUST be shaped via `log(1 + score) / log(1 + ceiling)` where `ceiling` is the 99th percentile ts_rank for that tsvector, computed at build time and loaded by the server at startup (see FR-042). Shaped values MUST be clamped to [0, 1].
- **FR-034**: Token jaccard MUST operate on compact symbol token sets (query tokens vs name + signature tokens)
- **FR-035**: Query coverage MUST measure the fraction of query non-stopword terms found in the candidate's doc text
- **FR-036**: Filtering MUST use per-signal floor thresholds — a candidate is discarded if no signal exceeds its respective floor
- **FR-037**: `name_exact=true` MUST bypass filtering — the candidate survives regardless of other signal values
- **FR-038**: Cross-encoder reranking MUST score each surviving candidate from both views: symbol view scores `(query, symbol_embed_text)`, doc view scores `(query, doc_embed_text)`
- **FR-039**: Per-candidate ranking score MUST equal `max(symbol_ce_score, doc_ce_score)` — no weighted combination, no normalization across views
- **FR-040**: Each result MUST carry metadata: `winning_view` (`"symbol"` or `"doc"`), `winning_score`, `losing_score`
- **FR-041**: The search tool MUST NOT apply per-query score normalization

#### Scoring and Thresholds

- **FR-042**: ts_rank ceiling values (99th percentile per tsvector) MUST be computed at build time (during ETL) and stored durably (e.g., in a metadata table). The server MUST load the precomputed values at startup and cache them for its lifetime. Ceilings MUST NOT be recomputed at server startup.
- **FR-043**: Per-signal floor thresholds MUST be configurable via `ServerConfig` fields with environment variable overrides (not hard-coded). Initial values determined empirically. Thresholds are stored in `RetrievalView.floor_thresholds` at startup.
- **FR-044**: There MUST be no weighted combination of scores from different channels. Intermediate signals exist for filtering only. The cross-encoder determines final rank.

#### Cross-Encoder

- **FR-045**: Each `RetrievalView` MUST carry its own cross-encoder as a configurable parameter
- **FR-046**: The doc view cross-encoder MUST receive lightly structured text with field labels (as specified in `doc_embed_text` construction), not flat prose concatenation
- **FR-047**: The symbol view cross-encoder MUST receive the `symbol_embed_text` (natural qualified signature)
- **FR-048**: Cross-encoder model selection MUST be configurable. Both views MAY share the same model.
- **FR-049**: Embedding provider and cross-encoder model MUST be configured and available. Server MUST fail fast at startup if either is missing or cannot be initialized. There is no keyword-only degraded mode.

#### RetrievalView Abstraction

- **FR-050**: The system MUST define a `RetrievalView` abstraction encapsulating: embedding model reference, embedding column name, tsvector column name and dictionary, cross-encoder model reference, scoring parameters (ts_rank ceiling, floor thresholds), and text assembly function
- **FR-051**: The V1 entity search layer MUST have two views: `symbol_view` and `doc_view`
- **FR-052**: Future doc layers (subsystem docs, help entries, builder guide) MUST be addable as new `RetrievalView` instances without modifying core pipeline logic
- **FR-053**: *(Out of scope for this feature — deferred to a future implementation.)* Cross-layer search (`source=all`), when implemented, SHOULD merge per-layer results by max-score across views — not score fusion. Results SHOULD carry their source layer as metadata.

#### Build Pipeline Changes

- **FR-055**: Build pipeline MUST produce `doc_embed_text` and `symbol_embed_text` as separate text assembly functions replacing the current `build_entity_embed_texts` / `build_minimal_embed_text`
- **FR-056**: Build pipeline MUST populate `qualified_name` before generating `symbol_embed_text` (pipeline ordering dependency)
- **FR-057**: Build pipeline MUST populate both tsvector columns after entity insertion via UPDATE statements
- **FR-058**: Build pipeline MUST populate `symbol_searchable` after `qualified_name` is derived

#### Backward Compatibility

- **FR-060**: The `search` tool's external interface (parameters: `query`, `kind`, `capability`, `top_k`, `source`) MUST remain compatible. The `source` parameter semantics are unchanged.
- **FR-061**: `SearchResult` response shape MUST be extended with `winning_view`, `winning_score`, and `losing_score` fields. Existing fields (`result_type`, `score`, `entity_summary`) MUST be preserved. `score` MUST always equal `winning_score` (preserved for backward compatibility). The `search_mode` field MUST be removed (there is only one mode: hybrid with cross-encoder reranking).
- **FR-062**: `hybrid_search_usages` is out of scope — its pipeline is unchanged by this feature
- **FR-063**: The old `embedding` and `search_vector` columns MUST be dropped. Migration is a clean rebuild (drop all tables, rebuild from artifacts).

#### Observability

- **FR-065**: Server MUST log per-search: channels queried, candidates per channel, candidates after merge, candidates after filtering, candidates sent to cross-encoder, and reranking latency
- **FR-066**: Build pipeline MUST log: ts_rank ceiling values computed, qualified_name derivation stats (from containment graph vs definition_text parse vs bare name), doc/symbol embedding counts

#### Remove Fallback System

- **FR-070**: The `SearchMode` enum MUST be removed. There is only one search mode (all channels + cross-encoder reranking). The `search_mode` field MUST be removed from `SearchResult` and all tool responses.
- **FR-071**: The `embedding_enabled` property and all conditional branches guarding "no embedding provider" MUST be removed from `config.py`, `lifespan.py`, `search.py`, and `resolver.py`.
- **FR-072**: `EmbeddingProvider` MUST NOT be typed as `Optional`. The `embedding_provider` field in `LifespanContext` MUST be `EmbeddingProvider` (non-optional). `create_provider` MUST return `EmbeddingProvider` (not `EmbeddingProvider | None`).
- **FR-073**: The `EMBEDDING_PROVIDER` config field MUST be required (no `None` default). Server MUST fail fast at startup if it is not set to `"local"` or `"hosted"`.
- **FR-074**: All `if embedding_provider:` / `if query_embedding:` conditional branches in search and resolver code MUST be removed. Embedding is always available.
- **FR-075**: The V1 spec's FR-008 ("degrade gracefully to keyword-only search"), FR-063 ("no provider mode"), and any other requirements describing keyword-only degradation are superseded by this spec. These requirements no longer apply.

### Key Entities

- **Entity (modified)**: Gains `doc_embedding`, `symbol_embedding`, `doc_search_vector`, `symbol_search_vector`, `symbol_searchable`, `qualified_name`. Loses `embedding`, `search_vector`.
- **RetrievalView (new, runtime)**: Encapsulates a retrieval surface — embedding model, embedding column, tsvector column/dictionary, cross-encoder, scoring parameters, text assembly. Not a database entity.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Searching for a known entity bare name (e.g., `damage`, `stc`, `do_look`) returns that entity in the top-3 results
- **SC-002**: Searching for a C++ identifier (`Character`, `PLR_COLOR2`) returns the correct entity, not entities whose documentation happens to contain the word in prose context
- **SC-003**: Searching for a natural language query ("send formatted text to character output buffer") returns relevant entities, with documentation-rich entities ranked above documentation-sparse ones
- **SC-004**: A nonsense query ("xyzzy foobar baz") returns zero results, not garbage with high scores
- **SC-005**: No returned result has a score produced by per-query normalization — all scores come from cross-encoder reranking
- **SC-006**: Partial identifier searches (`stc` matching `stc_color`) return relevant fuzzy matches via trigram similarity
- **SC-007**: After a full build, all entities have non-null `doc_search_vector` and `symbol_search_vector`
- **SC-008**: After a full build, ≥95% of entities have non-null `doc_embedding` and `symbol_embedding` (same coverage threshold as V1)
- **SC-009**: After a full build, ≥90% of function entities have a non-empty `qualified_name` derived from the containment graph or definition_text
- **SC-010**: Search latency (end-to-end including cross-encoder reranking) remains under 2 seconds for typical queries on a development machine
- **SC-011**: Build pipeline completes (including dual embedding generation) within 5 minutes for ~5,300 entities
- **SC-012**: Server refuses to start when `EMBEDDING_PROVIDER` is not configured, with a clear error message

### Assumptions

- **A-001**: The `pg_trgm` extension is available in the PostgreSQL installation (standard contrib module, included in pgvector Docker image)
- **A-002**: Cross-encoder model files are cached locally by fastembed after initial download, similar to embedding models
- **A-003**: The cross-encoder reranking step processes at most ~100-200 candidates per query — small enough that inference time is acceptable on CPU
- **A-004**: Embedding model choice (one code-aware model for both views vs. separate code + prose models) will be resolved by empirical evaluation before implementation finalizes parameter values. The architecture supports either configuration. Regardless of model choice, an embedding provider is always required — there is no unconfigured/keyword-only mode.
- **A-005**: Cross-encoder model selection will be resolved by benchmarking 2-3 candidates (e.g., `BAAI/bge-reranker-base`, `Xenova/ms-marco-MiniLM-L-6-v2`, `jinaai/jina-reranker-v1-turbo-en`) against representative queries
- **A-006**: Per-signal floor thresholds, per-channel retrieval limits (N), and ts_rank ceilings are empirical parameters determined during implementation — they affect config, not architecture
- **A-007**: The containment graph (~6,500 `contained_by` edges) is available from the dependency graph loaded at build time. No new artifact is required.
- **A-008**: Migration path is a clean rebuild — no incremental schema migration from the V1 `embedding`/`search_vector` columns
- **A-009**: `hybrid_search_usages` is unaffected by this change and will be addressed in a separate pipeline design
- **A-010**: The removal of keyword-only degradation mode is a policy decision per PATTERNS.md ("No fallbacks: the word and practice are forbidden"). All prior V1 spec requirements describing graceful degradation to keyword-only search are superseded.
