# Data Model: Multi-View Search Pipeline

**Phase 1 output** | **Date**: 2026-03-21

---

## Database Entities

### Entity Table — Schema Changes

The `Entity` SQLModel table (`server/db_models.py`) gains 6 new columns and loses 2.

#### Columns Removed

| Column | Type | Reason |
|--------|------|--------|
| `embedding` | `Vector(N)` | Replaced by `doc_embedding` + `symbol_embedding` |
| `search_vector` | `TSVECTOR` | Replaced by `doc_search_vector` + `symbol_search_vector` |

#### Columns Added

| Column | Type | Nullable | Default | Description | FR |
|--------|------|----------|---------|-------------|-----|
| `doc_embedding` | `Vector(N)` | Yes | `None` | Embedding of labeled prose fields (brief, details, params, returns, notes, rationale) | FR-001 |
| `symbol_embedding` | `Vector(N)` | Yes | `None` | Embedding of qualified scoped signature in natural C++ form | FR-001 |
| `doc_search_vector` | `TSVECTOR` | Yes | `None` | Weighted tsvector: name=A, brief+details=B, notes+rationale+params+returns=C. English dictionary (stemming). | FR-002 |
| `symbol_search_vector` | `TSVECTOR` | Yes | `None` | Weighted tsvector: name=A, qualified_name+signature=B, definition_text=C. Simple dictionary (no stemming). | FR-002 |
| `symbol_searchable` | `TEXT` | Yes | `None` | Lowercased, punctuation-stripped `name + qualified_name + signature`. For pg_trgm similarity. | FR-003 |
| `qualified_name` | `TEXT` | Yes | `None` | Fully-qualified C++ name derived from containment graph (e.g., `Logging::stc`). | FR-004 |

#### Indexes Added

| Index Name | Type | Column(s) | Options | FR |
|------------|------|-----------|---------|-----|
| `ix_entities_doc_embedding` | HNSW | `doc_embedding` | `vector_cosine_ops, m=16, ef_construction=64` | FR-005 |
| `ix_entities_symbol_embedding` | HNSW | `symbol_embedding` | `vector_cosine_ops, m=16, ef_construction=64` | FR-005 |
| `ix_entities_doc_search_vector` | GIN | `doc_search_vector` | — | FR-006 |
| `ix_entities_symbol_search_vector` | GIN | `symbol_search_vector` | — | FR-006 |
| `ix_entities_symbol_searchable` | GiST | `symbol_searchable` | `gist_trgm_ops` | FR-007 |

#### Indexes Removed

| Index Name | Type | Column(s) | Reason |
|------------|------|-----------|--------|
| `idx_entities_search` | GIN | `search_vector` | Column dropped |
| `idx_entities_embedding` | ivfflat | `embedding` | Column dropped |

#### Entity Model Definition (target state)

```python
class Entity(SQLModel, table=True):
    __tablename__ = "entities"

    # ... existing identity, source location, documentation, classification fields unchanged ...

    # Embedding (dual views)
    doc_embedding: list[float] | None = Field(
        default=None,
        sa_column=Column(Vector(_EMBEDDING_DIM)),
        description=f"{_EMBEDDING_DIM}-dim embedding of labeled prose fields",
    )
    symbol_embedding: list[float] | None = Field(
        default=None,
        sa_column=Column(Vector(_EMBEDDING_DIM)),
        description=f"{_EMBEDDING_DIM}-dim embedding of qualified scoped signature",
    )

    # Full-text search (dual views)
    doc_search_vector: str | None = Field(
        default=None,
        sa_column=Column(TSVECTOR),
        description="Weighted tsvector: name=A, brief+details=B, notes+rationale+params+returns=C (english)",
    )
    symbol_search_vector: str | None = Field(
        default=None,
        sa_column=Column(TSVECTOR),
        description="Weighted tsvector: name=A, qualified_name+signature=B, definition_text=C (simple)",
    )

    # Trigram similarity
    symbol_searchable: str | None = Field(
        default=None,
        description="Lowercased punctuation-stripped name+qualified_name+signature for pg_trgm",
    )

    # Qualified name
    qualified_name: str | None = Field(
        default=None,
        description="Fully-qualified C++ name (e.g., Logging::stc, Character::position)",
    )
```

### SearchConfig Table — New (FR-042)

Stores precomputed search calibration values produced by the build pipeline. The server loads these at startup and caches them for its lifetime.

```python
class SearchConfig(SQLModel, table=True):
    __tablename__ = "search_config"

    key: str = Field(primary_key=True, description="Config key (e.g., 'doc_tsrank_ceiling')")
    value: float = Field(description="Numeric config value")
```

**Known keys** (populated by build pipeline, consumed by server):

| Key | Description | Source |
|-----|-------------|--------|
| `doc_tsrank_ceiling` | 99th percentile ts_rank for `doc_search_vector` | FR-042 |
| `symbol_tsrank_ceiling` | 99th percentile ts_rank for `symbol_search_vector` | FR-042 |

### EntityUsage Table — No Changes

The `entity_usages` table is explicitly out of scope (FR-062, A-009). Its `embedding` and `search_vector` columns remain unchanged.

---

## Runtime Models

### SearchResult — Modified Response Shape

```python
class SearchResult(BaseModel):
    result_type: str                        # "entity" in V1; V2 adds "subsystem_doc"
    score: float                            # Cross-encoder score (winning view); raw logit may be negative
    entity_summary: EntitySummary | None    # Present when result_type="entity"
    matching_usages: list[MatchingUsage] | None  # Present when source="usages"
    # NEW fields
    winning_view: str                       # "symbol" or "doc"
    winning_score: float                    # Cross-encoder score from winning view; raw logit may be negative
    losing_score: float                     # Cross-encoder score from losing view; raw logit may be negative
    # REMOVED fields
    # search_mode: SearchMode  ← FR-070: removed entirely
```

### RetrievalView — New Runtime Abstraction

Not a database entity. Encapsulates per-view search configuration for the pipeline.

```python
@dataclass(frozen=True)
class RetrievalView:
    name: str                                    # "doc" or "symbol"
    embedding_column: str                        # SA column name for cosine query
    tsvector_column: str                         # SA column name for ts_rank query
    tsvector_dictionary: str                     # "english" or "simple"
    cross_encoder: TextCrossEncoder              # fastembed reranker instance
    ts_rank_ceiling: float                       # p99 ts_rank loaded from metadata table at startup
    floor_thresholds: dict[str, float]           # {signal_name: minimum_value}
    assemble_embed_text: Callable[[Entity], str] # Reconstructs CE input text from entity fields at query time
```

`assemble_embed_text` is a pure function called at reranking time — it is **not** a database column. `doc_embed_text` and `symbol_embed_text` are **not** stored in the Entity table; they are reconstructed from fields already present in the Entity row (`brief`, `details`, `params`, `returns`, `notes`, `rationale`, `qualified_name`, `signature`, etc.) using the same assembly functions defined in `entity_processor.py`.

**Instances created at startup** (in lifespan):

| View | embedding_column | tsvector_column | dictionary | assemble_embed_text |
|------|-----------------|-----------------|------------|---------------------|
| `doc_view` | `doc_embedding` | `doc_search_vector` | `english` | `build_doc_embed_text` |
| `symbol_view` | `symbol_embedding` | `symbol_search_vector` | `simple` | `build_symbol_embed_text` |

### CrossEncoderProvider — New Runtime Abstraction

Wraps `TextCrossEncoder` with async support and the project's provider pattern.

```python
class CrossEncoderProvider:
    def __init__(self, model_name: str) -> None:
        self._reranker = TextCrossEncoder(model_name=model_name)

    def rerank(self, query: str, documents: list[str], batch_size: int = 64) -> list[float]:
        return list(self._reranker.rerank(query, documents, batch_size=batch_size))

    async def arerank(self, query: str, documents: list[str], batch_size: int = 64) -> list[float]:
        return await asyncio.to_thread(self.rerank, query, documents, batch_size)
```

---

## Removed Entities

### SearchMode Enum — Deleted (FR-070)

The `SearchMode` enum (`HYBRID`, `SEMANTIC_ONLY`, `KEYWORD_FALLBACK`) is removed entirely. There is only one search mode: all channels + cross-encoder reranking.

### EmbeddingProvider Optional Typing — Removed (FR-072)

`EmbeddingProvider` is non-optional everywhere. The `| None` union type and all `if embedding_provider:` guards are removed from:
- `config.py` (`embedding_provider` field)
- `lifespan.py` (`LifespanContext["embedding_provider"]`)
- `search.py` (function parameters)
- `resolver.py` (function parameters)
- `embedding.py` (`create_provider` return type)

### `embedding_enabled` Property — Deleted (FR-071)

The `ServerConfig.embedding_enabled` property is removed. Embedding is always enabled because `embedding_provider` is required.

---

## Build Pipeline Text Assembly

### doc_embed_text Construction (FR-020)

```python
def build_doc_embed_text(entity: MergedEntity) -> str:
    """Assemble labeled prose fields for doc embedding."""
    parts: list[str] = []
    if entity.doc:
        if entity.doc.brief:
            parts.append(f"BRIEF: {entity.doc.brief}")
        if entity.doc.details:
            parts.append(f"DETAILS: {entity.doc.details}")
        if entity.doc.params:
            params_text = " ".join(f"{k}: {v}" for k, v in entity.doc.params.items())
            parts.append(f"PARAMS: {params_text}")
        if entity.doc.returns:
            parts.append(f"RETURNS: {entity.doc.returns}")
        if entity.doc.notes:
            parts.append(f"NOTES: {entity.doc.notes}")
        if entity.doc.rationale:
            parts.append(f"RATIONALE: {entity.doc.rationale}")
    # Fallback: entities with no doc prose fields use bare name as doc embedding text.
    # This ensures every entity gets a doc_embedding (never null due to missing prose).
    return "\n".join(parts) if parts else entity.entity.name
```

### symbol_embed_text Construction (FR-021–FR-024)

```python
def build_symbol_embed_text(entity: MergedEntity) -> str:
    """Assemble qualified signature for symbol embedding."""
    if entity.entity.kind == "function":
        # Use qualified_name in natural C++ signature form
        # e.g., "void Logging::stc(const String&, Character*)"
        return entity.qualified_name_signature or entity.signature
    # Non-function: qualified name only
    return entity.qualified_name or entity.entity.name
```

---

## State Transitions

No state machines in this feature. The build pipeline is a linear ETL with ordering constraints (FR-056):

```
load artifacts
  → merge entities
  → assign deterministic IDs
  → extract source code
  → assign capabilities
  → load graph edges
  → compute fan metrics + bridge flags
  → compute entry points + enriched fields
  → derive qualified_name (NEW — uses containment graph)         ← must run before embed text
  → build doc_embed_text + symbol_embed_text (NEW — replaces build_entity_embed_texts)
  → sync dual embedding caches (NEW — doc + symbol)
  → create schema (NEW — pg_trgm extension, new columns, new indexes)
  → populate entities (NEW — dual embeddings, dual tsvectors, symbol_searchable, qualified_name)
  → compute ts_rank ceilings (NEW — post-population)
  → populate entity_usages (unchanged)
  → populate edges, capabilities, entry_points (unchanged)
  → analyze tables
```

---

## Validation Rules

| Field | Rule | Source |
|-------|------|--------|
| `doc_embedding` | Dimension must match `EMBEDDING_DIMENSION` env var | Enforced by pgvector Vector(N) |
| `symbol_embedding` | Dimension must match `EMBEDDING_DIMENSION` env var | Enforced by pgvector Vector(N) |
| `qualified_name` | May be null (scope chain unavailable) but ≥90% of functions should have one | SC-009 |
| `symbol_searchable` | Must be lowercase, punctuation-stripped | FR-014, enforced at build time |
| `ts_rank_ceiling` | Must be > 0 | Enforced in shaping function (log1p denominator) |
| `EMBEDDING_PROVIDER` | Required at startup, must be `"local"` or `"hosted"` | FR-073 |
| Cross-encoder model | Must load successfully at startup | FR-049 |
