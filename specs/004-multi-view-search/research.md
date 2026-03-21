# Research: Multi-View Search Pipeline

**Phase 0 output** | **Date**: 2026-03-21

---

## R-001: Cross-Encoder Reranking via fastembed

**Decision**: Use `fastembed.rerank.cross_encoder.TextCrossEncoder` for cross-encoder reranking.

**Rationale**: fastembed is already a project dependency (used for embedding via `TextEmbedding`). The `TextCrossEncoder` class provides a compatible sync API (`rerank()`, `rerank_pairs()`) with ONNX inference. No additional heavy dependencies needed.

**Key findings**:

- **Import**: `from fastembed.rerank.cross_encoder import TextCrossEncoder` (not re-exported from top-level)
- **API**: `reranker.rerank(query, documents, batch_size=64)` → `Iterable[float]` (lazy — must `list()`)
- **Scores**: Raw logits (not 0–1 probabilities). Use for relative ranking only, not absolute thresholds.
- **Async**: Sync-only. Wrap in `asyncio.to_thread()` for async server code.
- **Coexistence**: TextEmbedding + TextCrossEncoder work in same process without conflict (separate ONNX sessions).
- **First call downloads model** to `~/.cache/fastembed/`.

**Model recommendation**:

| Model | Size | License | Notes |
|-------|------|---------|-------|
| `Xenova/ms-marco-MiniLM-L-6-v2` | 80 MB | Apache-2.0 | Default — fast, good quality |
| `BAAI/bge-reranker-base` | 1.04 GB | MIT | Higher quality, larger |
| `jinaai/jina-reranker-v1-turbo-en` | 150 MB | Apache-2.0 | 8K context, fast |

Start with `Xenova/ms-marco-MiniLM-L-6-v2`. Switch to `BAAI/bge-reranker-base` if quality is insufficient. Avoid `jinaai/jina-reranker-v2-base-multilingual` (CC-BY-NC license).

**Usage pattern**:

```python
from fastembed.rerank.cross_encoder import TextCrossEncoder

reranker = TextCrossEncoder(model_name="Xenova/ms-marco-MiniLM-L-6-v2")

async def rerank_results(query: str, candidates: list[str]) -> list[float]:
    return await asyncio.to_thread(
        lambda: list(reranker.rerank(query, candidates, batch_size=64))
    )
```

**Alternatives considered**:

- sentence-transformers `CrossEncoder`: heavier dependency (torch), not ONNX-optimized. Rejected — fastembed already handles this.
- Raw ONNX Runtime: lower-level, would need tokenizer management. Rejected — fastembed wraps this.

---

## R-002: pg_trgm Trigram Similarity via SQLAlchemy

**Decision**: Use GiST index with `gist_trgm_ops`, query via `func.similarity()` and the `<->` distance operator.

**Rationale**: GiST supports KNN-ordered scans (`ORDER BY col <-> query LIMIT k`), which GIN does not. The search pipeline needs top-k most similar entities by trigram, not boolean matching.

**Key findings**:

- **Function**: `func.similarity(col, query)` returns `real` in [0.0, 1.0]
- **KNN operator**: `col.op("<->")(query)` for GiST-accelerated ordered retrieval
- **Threshold**: Default `pg_trgm.similarity_threshold = 0.3`. For short identifiers, use 0.2.
- **Index type**: GiST with `gist_trgm_ops` — supports ordered retrieval. GIN only supports boolean `%` operator.

**Query pattern**:

```python
distance = Entity.symbol_searchable.op("<->")(query)
similarity = func.similarity(Entity.symbol_searchable, query).label("trgm_score")

stmt = (
    select(Entity.entity_id, similarity)
    .where(func.similarity(Entity.symbol_searchable, query) > 0.2)
    .order_by(distance)
    .limit(limit)
)
```

**Alternatives considered**:

- GIN index: cannot do ordered retrieval (only boolean `%` match). Rejected for ranking use case.
- `LIKE`/`ILIKE` with B-tree: no fuzzy matching capability. Rejected.

---

## R-003: ts_rank Score Shaping

**Decision**: Use `log(1 + score) / log(1 + ceiling)` with per-column 99th percentile ceilings, computed at build time.

**Rationale**: Raw ts_rank is unbounded and the distribution differs between doc vectors (long text, low density → 0.01–0.15 typical) and symbol vectors (short text, high density → 0.06–0.60 typical). Log-ceiling shaping preserves resolution in the typical range and gracefully compresses outliers.

**Key findings**:

- **Per-column ceilings needed**: Doc and symbol tsvectors have different score distributions. A single ceiling distorts one or the other.
- **Computation**: Use `ts_stat()` with top-50 lexemes cross-joined against entities, then `percentile_cont(0.99)`.
- **Recomputation frequency**: Build time only. Corpus is static between builds; p99 is stable.
- **PostgreSQL built-in normalization** (flag 32, `score/(1+score)`): Poor resolution — entire typical range compresses into [0, 0.13]. Rejected.

**Python expression**:

```python
import math

def shape_ts_rank(raw: float, ceiling: float) -> float:
    if raw <= 0.0:
        return 0.0
    return min(1.0, math.log1p(raw) / math.log1p(ceiling))
```

**Ceiling computation SQL** (build time):

```sql
WITH top_lexemes AS (
  SELECT word FROM ts_stat('SELECT doc_search_vector FROM entities')
  ORDER BY nentry DESC LIMIT 50
),
scores AS (
  SELECT ts_rank(e.doc_search_vector, plainto_tsquery('simple', l.word)) AS score
  FROM entities e CROSS JOIN top_lexemes l
  WHERE e.doc_search_vector @@ plainto_tsquery('simple', l.word)
)
SELECT percentile_cont(0.99) WITHIN GROUP (ORDER BY score) AS ceiling FROM scores;
```

**Expected p99 values**: ~0.3–0.5 for doc, ~0.5–0.8 for symbol (to be confirmed empirically during build).

**Alternatives considered**:

- Sigmoid shaping: needs manual k/midpoint tuning per corpus. Rejected — log-ceiling self-calibrates via p99.
- Min-max normalization: outlier-sensitive, no log compression. Rejected.
- PostgreSQL normalization flag 32: poor resolution. Rejected.

---

## R-004: Qualified Name Derivation from Containment Graph

**Decision**: Walk outgoing `contained_by` edges from member entities to reconstruct scope chains (e.g., `Logging::stc`). Secondary source: parse `definition_text` for `::` separators.

**Rationale**: The dependency graph already has ~6,567 `contained_by` edges linking members to their containing scopes (classes, namespaces, files). Walking these edges produces correct qualified names without parsing source code.

**Key findings**:

- **Edge direction**: `contained_by` edges go member → container (outgoing from the member node).
- **Graph IDs**: At build time, the GML graph uses old Doxygen IDs (member hashes, compound IDs). The `load_graph_edges()` function maps these to deterministic IDs via `node_to_entity`.
- **Node attributes**: `name` (bare name or signature), `kind` (function, class, etc.), `type` (compound/member).
- **No existing qualified_name helper** — must be written.
- **Build-time derivation**: The raw GML graph is loaded in `build_mcp_db.py` for edge extraction. The containment edges are available at this point but not currently used for name derivation.

**Algorithm**:

```python
def derive_qualified_name(entity_id: str, graph: nx.MultiDiGraph, entity_names: dict[str, str]) -> str:
    """Walk contained_by edges to build scope chain."""
    parts = [entity_names[entity_id]]
    current = entity_id
    while True:
        containers = [
            target for _, target, data in graph.out_edges(current, data=True)
            if data.get("type") == "contained_by"
        ]
        if not containers:
            break
        current = containers[0]  # take first container (should be unique)
        node_name = entity_names.get(current, "")
        if not node_name or graph.nodes[current].get("kind") in ("file", "dir"):
            break  # stop at file/dir scope — not meaningful for C++ qualified names
        parts.append(node_name)
    parts.reverse()
    return "::".join(parts)
```

**Secondary source**: When no `contained_by` edges exist for an entity, parse `definition_text` for `::`:

```python
if "::" in (definition_text or ""):
    # Extract "Scope::name" from "ReturnType Scope::name(args)"
    match = re.search(r'(\w+(?:::\w+)+)', definition_text)
    if match:
        qualified_name = match.group(1)
```

**Alternatives considered**:

- Parse source code for namespace/class declarations: fragile, requires full C++ parsing. Rejected.
- Use `file_path` as scope proxy: lossy, many entities in same file with different scopes. Rejected.

---

## R-005: RetrievalView Abstraction Design

**Decision**: `RetrievalView` is a frozen `dataclass` (not Pydantic — it holds runtime references to models and functions, not serializable data) encapsulating per-view configuration.

**Rationale**: Each view (doc, symbol) carries its own embedding model, embedding column, tsvector column/dictionary, cross-encoder, scoring parameters, and text assembly function. This must be a runtime abstraction, not a database model.

**Key findings**:

- Two views in V1: `doc_view` and `symbol_view`
- Future views (V2 subsystem docs, etc.) are new instances — no pipeline changes needed
- Cross-encoder scores are per-view; final rank is `max(symbol_ce_score, doc_ce_score)`
- The view needs: embedding model reference, column name (string for SA Column lookup), tsvector column name, dictionary name, cross-encoder reference, ts_rank ceiling, floor thresholds, text assembly function

**Design**:

```python
@dataclass(frozen=True)
class RetrievalView:
    name: str                           # "doc" or "symbol"
    embedding_column: str               # "doc_embedding" or "symbol_embedding"
    tsvector_column: str                # "doc_search_vector" or "symbol_search_vector"
    tsvector_dictionary: str            # "english" or "simple"
    cross_encoder: TextCrossEncoder     # fastembed reranker instance
    ts_rank_ceiling: float              # p99 ts_rank for this column
    floor_thresholds: dict[str, float]  # per-signal floor values
    embed_text_key: str                 # key into entity embed texts for CE input
```

**Alternatives considered**:

- Pydantic model: cannot hold non-serializable references (TextCrossEncoder, SA Column). Rejected.
- Protocol: over-engineered for two known instances. Rejected — use simple dataclass.
- Dict/NamedTuple: loses type safety and documentation. Rejected.

---

## R-006: Embedding Provider & Cross-Encoder as Hard Requirements

**Decision**: `EMBEDDING_PROVIDER` config field is required (no `None` default). Server crashes at startup if not set. Cross-encoder model initializes during lifespan startup; failure is fatal.

**Rationale**: Per PATTERNS.md and the constitution's "Fail-Fast, No Fallbacks" principle, partially configured systems are not allowed. The current optional embedding design predates the constitution ratification (2026-03-17).

**Key findings (current codebase)**:

| File | What to change |
|------|---------------|
| `config.py` | `embedding_provider: Literal["local", "hosted"] \| None` → `Literal["local", "hosted"]`, remove `None` default |
| `config.py` | Delete `embedding_enabled` property |
| `lifespan.py` | `embedding_provider: EmbeddingProvider \| None` → `EmbeddingProvider`, remove conditional init |
| `embedding.py` | `create_provider() -> EmbeddingProvider \| None` → `-> EmbeddingProvider`, remove `None` return |
| `search.py` | Remove all `if embedding_provider:` / `if query_embedding:` branches |
| `resolver.py` | `embedding_provider: EmbeddingProvider \| None` → `EmbeddingProvider` |
| `enums.py` | Remove `SearchMode` enum entirely (only `HYBRID` would remain, making it redundant) |
| `models.py` | Remove `search_mode: SearchMode` from `SearchResult` |

**Alternatives considered**:

- Keep optional but log a warning: violates constitution. Rejected.
- Make it optional with a startup validation check: still requires `None` types everywhere. Rejected.
