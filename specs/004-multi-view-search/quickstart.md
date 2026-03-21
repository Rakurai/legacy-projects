# Quickstart: Multi-View Search Pipeline Implementation

**Phase 1 output** | **Date**: 2026-03-21

This document provides the recommended implementation order and key decisions for building the multi-view search pipeline.

---

## Prerequisites

- PostgreSQL 18 with pgvector running (see [INSTALL.md](../../mcp/doc_server/INSTALL.md))
- `pg_trgm` extension available (standard contrib, included in pgvector Docker image)
- `.env` file with `EMBEDDING_PROVIDER=local` (or `hosted`) — **required, not optional**
- uv workspace synced: `uv sync`

---

## Implementation Order

The implementation has four layers with strict ordering constraints.

### Layer 1: Foundation (no search changes yet)

**Goal**: New columns exist, old fallback code removed, server still starts.

1. **Remove fallback system** (FR-070–FR-075)
   - Delete `SearchMode` enum from `enums.py`
   - Make `embedding_provider` required in `config.py` (no `None` default)
   - Delete `embedding_enabled` property from `config.py`
   - Make `EmbeddingProvider` non-optional in `lifespan.py`, `search.py`, `resolver.py`
   - Make `create_provider` return `EmbeddingProvider` (not `| None`)
   - Remove `search_mode` from `SearchResult` and `SearchResponse`
   - Update all `if embedding_provider:` guards

2. **Add cross-encoder provider** (FR-045–FR-048)
   - Create `server/cross_encoder.py` wrapping `TextCrossEncoder`
   - Add `CROSS_ENCODER_MODEL` to `ServerConfig`
   - Initialize in lifespan, fail fast if model can't load

3. **Schema changes** (FR-001–FR-008)
   - Add 6 new columns to Entity model in `db_models.py`
   - Remove 2 old columns (`embedding`, `search_vector`)
   - Add new indexes (HNSW × 2, GIN × 2, GiST × 1)
   - Add `pg_trgm` extension to `drop_and_create_schema()`

4. **RetrievalView abstraction** (FR-050–FR-053)
   - Create `server/retrieval_view.py` with frozen dataclass
   - Instantiate `doc_view` and `symbol_view` in lifespan

**Checkpoint**: Server starts, creates correct schema, but search is broken (old search code references removed columns). This is expected — Layer 2 fixes it.

### Layer 2: Build Pipeline

**Goal**: `build_mcp_db.py` populates all new columns correctly.

5. **Qualified name derivation** (FR-016–FR-018)
   - Add `derive_qualified_names()` to `entity_processor.py`
   - Walk `contained_by` edges in the GML graph
   - Secondary: parse `definition_text` for `::` separators
   - Must run before embed text assembly (FR-056)

6. **Embed text assembly** (FR-020–FR-024, FR-055)
   - Replace `build_entity_embed_texts()` with two functions:
     - `build_doc_embed_texts()` — labeled prose fields
     - `build_symbol_embed_texts()` — qualified scoped signatures
   - Update `main()` pipeline ordering

7. **Dual embedding caches** (FR-025–FR-026)
   - Call `sync_embeddings_cache` twice: `embedding_type="doc"` and `embedding_type="symbol"`
   - Assign `merged.doc_embedding` and `merged.symbol_embedding`

8. **Dual tsvectors + symbol_searchable** (FR-010–FR-015, FR-057–FR-058)
   - Generate `doc_search_vector` via SQL (english dict, A/B/C weights)
   - Generate `symbol_search_vector` via SQL (simple dict, A/B/C weights)
   - Populate `symbol_searchable` column

9. **ts_rank ceiling computation** (FR-042)
   - After entity population, compute p99 ts_rank per tsvector column
   - Store results in a metadata table (e.g., `search_config`) at build time
   - Server loads these values from the metadata table at startup — does not recompute

**Checkpoint**: `uv run python build_mcp_db.py` completes, all columns populated. Verify:
```sql
SELECT count(*) FROM entities WHERE doc_embedding IS NOT NULL;
SELECT count(*) FROM entities WHERE symbol_embedding IS NOT NULL;
SELECT count(*) FROM entities WHERE doc_search_vector IS NOT NULL;
SELECT count(*) FROM entities WHERE qualified_name IS NOT NULL;
```

### Layer 3: Search Pipeline

**Goal**: New 7-stage search pipeline replaces old hybrid_search.

10. **Rewrite search.py** (FR-030–FR-044)
    - Five parallel channel queries (doc semantic, symbol semantic, doc keyword, symbol keyword, trigram)
    - Merge by entity_id
    - Compute intermediate signal vector (8 signals)
    - Per-signal floor filtering with name_exact bypass
    - Cross-encoder reranking (both views per candidate)
    - Return top-k with winning_view metadata

11. **Update search tool** (FR-060–FR-061)
    - Remove `search_mode` from `SearchResponse`
    - Pass `RetrievalView` instances from lifespan context
    - Ensure `hybrid_search_usages` still works (unchanged, uses old single-embedding path on EntityUsage table)

**Checkpoint**: Search works end-to-end. Run manual queries:
```bash
cd mcp/doc_server && uv run python -c "
# Quick smoke test via direct function call
"
```

### Layer 4: Observability & Tests

12. **Logging** (FR-065–FR-066)
    - Per-search: channel counts, merge count, filter count, CE count, latency
    - Build: ceiling values, qualified_name stats, embedding counts

13. **Contract tests** (update existing)
    - Verify SearchResult has `winning_view`, `winning_score`, `losing_score`
    - Verify no `search_mode` field
    - Verify server refuses to start without `EMBEDDING_PROVIDER`

---

## Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Cross-encoder model | `Xenova/ms-marco-MiniLM-L-6-v2` (80MB) | Fast, Apache-2.0, good quality for passage ranking |
| Embedding model(s) | One shared model for both views (e.g., existing configured model); benchmark `BAAI/bge-small-en-v1.5` vs a code-aware model before finalizing (A-004/A-005). `RetrievalView` supports different models per view if evaluation shows benefit. | Avoids doubling embedding compute/cache size unless quality improvement justifies it |
| ts_rank shaping | `log(1 + score) / log(1 + ceiling)` | Corpus-calibrated, good resolution in typical range |
| Trigram index type | GiST | Supports KNN ordered retrieval (`<->` operator) |
| Trigram threshold | 0.2 | Low bar for short C++ identifiers |
| RetrievalView type | Frozen dataclass | Holds non-serializable runtime references |
| Qualified name algorithm | Walk `contained_by` edges → parse `definition_text` → bare name | Uses existing graph data |
| Migration strategy | Clean rebuild (drop all, rebuild from artifacts) | No incremental migration needed (A-008) |
| SearchMode enum | Delete entirely | Only one mode exists (FR-070) |

---

## Dependencies to Add

```bash
# fastembed already includes cross-encoder support — no new packages needed
# pg_trgm is a PostgreSQL extension, not a Python package
```

Verify fastembed cross-encoder availability:
```bash
cd mcp/doc_server && uv run python -c "from fastembed.rerank.cross_encoder import TextCrossEncoder; print('OK')"
```

---

## Config Changes

Add to `.env`:
```env
# Required (was previously optional)
EMBEDDING_PROVIDER=local

# New
CROSS_ENCODER_MODEL=Xenova/ms-marco-MiniLM-L-6-v2
```

Add to `ServerConfig`:
```python
cross_encoder_model: str = Field(
    default="Xenova/ms-marco-MiniLM-L-6-v2",
    description="fastembed cross-encoder model name",
)
```
