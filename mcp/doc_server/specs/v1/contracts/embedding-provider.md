# Contract: Embedding Provider


**Feature**: 004-local-fastembed-provider
**Phase**: 1 (Design & Contracts)
**Date**: 2026-03-15

## Overview

Internal interface contract for the embedding provider abstraction. This is not an MCP-facing contract — it defines the server's internal embedding interface used by the search/resolver layer at query time and by the build pipeline for artifact generation.

The provider owns both sync and async surfaces. The optimal async strategy is implementation-specific: local (ONNX) is CPU-bound and uses `asyncio.to_thread()`; hosted (OpenAI) has native async HTTP via `AsyncOpenAI` and would waste a thread pool thread if forced to `asyncio.to_thread()`. The naming convention is the `a`-prefix pattern (LangChain, SQLAlchemy `AsyncSession`).

---

## Interface: EmbeddingProvider

```python
class EmbeddingProvider(Protocol):
    @property
    def dimension(self) -> int: ...

    @property
    def max_batch_size(self) -> int: ...

    def embed(self, text: str) -> list[float]: ...
    def embed_batch(self, texts: list[str]) -> list[list[float]]: ...

    async def aembed(self, text: str) -> list[float]: ...
    async def aembed_batch(self, texts: list[str]) -> list[list[float]]: ...
```

### Properties

| Property | Type | Description |
|---|---|---|
| `dimension` | `int` (read-only) | Vector dimension of the model output. Constant for a given provider instance. |
| `max_batch_size` | `int` (read-only) | Maximum recommended texts per batch call. Provider handles internal chunking so callers are not required to pre-chunk, but may do so for progress reporting. |

### Methods

#### `embed(text: str) -> list[float]`

Embed a single text string, sync.

- **Input**: `text: str` — non-empty text to embed
- **Output**: `list[float]` — vector of length `dimension`
- **Implemented as**: `return self.embed_batch([text])[0]`

#### `embed_batch(texts: list[str]) -> list[list[float]]`

Batch-embed multiple text strings, sync. Used by the build pipeline.

- **Output**: one vector per input text, in same order, each of length `dimension`
- **Chunking**: Provider handles internal chunking at `max_batch_size` boundaries

#### `aembed(text: str) -> list[float]` (async)

Async variant of `embed`. Used by server runtime (search.py, resolver.py).

- **Errors**: May raise on network failure (hosted) or model loading failure (local). Caller must handle gracefully (fall back to keyword search).

#### `aembed_batch(texts: list[str]) -> list[list[float]]` (async)

Async variant of `embed_batch`.

---

## Naming Migration

| Old name | New name |
|---|---|
| `embed_query_sync` | `embed` |
| `embed_documents_sync` | `embed_batch` |
| `embed_query` (async) | `aembed` |
| `embed_documents` (async) | `aembed_batch` |

---

## Implementations

### LocalEmbeddingProvider

Wraps `fastembed.TextEmbedding` with ONNX-based local inference.

- **Default model**: BAAI/bge-base-en-v1.5 (768-dim, ~130 MB ONNX)
- **`max_batch_size`**: 256 (matches fastembed's internal default; throughput plateaus here)
- **`embed_batch`**: Passes `batch_size=self.max_batch_size` to `fastembed.TextEmbedding.embed()`
- **`aembed` / `aembed_batch`**: Wrap sync methods via `asyncio.to_thread()` (ONNX is CPU-bound)
- **Dimension**: Probed from model on init (embed a test string, check output length)
- **Performance**: ~5-20ms per single query, ~1-3 min for full entity set (~5,300)

### HostedEmbeddingProvider

Wraps `openai.OpenAI` (sync) and `openai.AsyncOpenAI` (async) — two clients, one per surface.

- **Config requires**: `EMBEDDING_BASE_URL`, `EMBEDDING_MODEL`, optionally `EMBEDDING_API_KEY`
- **`max_batch_size`**: 256 (configurable via constructor)
- **`embed_batch`**: Uses sync `OpenAI` client, chunking at `max_batch_size`
- **`aembed` / `aembed_batch`**: Use `AsyncOpenAI` client (native non-blocking HTTP I/O)
- **Dimension**: From config (not probed)
- **Encoding format**: `"float"` passed through

---

## Factory

`create_provider(config: ServerConfig) -> EmbeddingProvider | None`

- Returns `LocalEmbeddingProvider` when `config.embedding_provider == "local"`
- Returns `HostedEmbeddingProvider` when `config.embedding_provider == "hosted"` and endpoint config is valid
- Returns `None` when `config.embedding_provider` is not set (keyword-only mode)
- **Validates**: `provider.dimension == config.embedding_dimension` — raises on mismatch (fail-fast)

---

## Invariants

1. `provider.dimension` must equal `config.embedding_dimension`. Factory validates this and raises on mismatch.
2. All vectors returned by a provider instance have exactly `dimension` elements.
3. The same provider type and model that generated stored vectors must be used for query-time embedding. This is ensured by configuration — build and server read the same `.env`.

---

## Consumer Contracts

### `hybrid_search(session, query, embedding_provider=None, ...)`

- Receives `EmbeddingProvider | None` from lifespan context
- When provider is `None`: returns results in `keyword_fallback` mode
- When provider is present: calls `await provider.aembed(query)` and blends semantic scores
- On provider error: logs warning, degrades to keyword fallback for that request

### `resolve_entity(session, query, ..., embedding_provider=None, ...)`

- Same pattern as `hybrid_search`
- Calls `await provider.aembed(query)` in the semantic resolution stage

### `build_mcp_db.py` Embedding Stages

The build pipeline uses a four-layer architecture for embeddings:

- **Layer 1 — Cache operations** (`build_helpers/embeddings_loader.py`): `save_embedding_cache()`, `load_embedding_cache()`, `sync_embeddings_cache()`. Fully schema-agnostic — operates on generic key → text → embedding mappings with no knowledge of entities, usages, or Doxygen. Calls `provider.embed_batch(missing_texts)` for generation.
- **Layer 2 — Domain logic** (`build_helpers/entity_processor.py`): `build_entity_embed_texts()` and `build_minimal_embed_text()`. Constructs embedding text for each entity from its doc fields or minimal Doxygen-formatted text.
- **Layer 3 — Orchestration** (`build_mcp_db.py`): Calls `build_entity_embed_texts()` to produce `{entity_id: text}` maps, calls `sync_embeddings_cache()` with the result, attaches returned vectors to merged entities. `populate_entity_usages()` builds `{usage_key: description}` maps and calls `sync_embeddings_cache()` with `embedding_type="usages"`.
- **Layer 4 — Provider** (`server/embedding.py`): `create_provider(config)` returns `EmbeddingProvider | None`. Called once in the orchestration layer before embedding stages begin.

Synchronization flow per type:
1. `build_entity_embed_texts(merged_entities)` → `dict[str, str]` (entity_id → embed text, doc-less entities with no name/sig/kind excluded)
2. `sync_embeddings_cache(artifacts_path, model_slug, dim, "entity", entity_keys, texts_by_key, provider)` → `dict[str, list[float]]`; `sync_embeddings_cache` calls `provider.embed_batch(missing_texts)` internally
3. `for merged in merged_entities: merged.embedding = embeddings.get(merged.entity_id)`

---

## Environment Configuration Contract

```env
# Provider selection (required for embeddings)
EMBEDDING_PROVIDER=local|hosted    # omit for keyword-only mode

# Dimension (must match provider output)
EMBEDDING_DIMENSION=768            # default 768

# Local provider config
EMBEDDING_LOCAL_MODEL=BAAI/bge-base-en-v1.5
EMBEDDING_ONNX_PROVIDER=CPUExecutionProvider  # ONNX Runtime execution provider (e.g. CoreMLExecutionProvider, CUDAExecutionProvider)

# Hosted provider config (only when EMBEDDING_PROVIDER=hosted)
EMBEDDING_BASE_URL=http://localhost:4000/v1
EMBEDDING_API_KEY=lm-studio
EMBEDDING_MODEL=text-embedding-qwen3-embedding-8b
```

---

## Embed Text Construction

The text used as input to the embedding model for each entity is a structured Doxygen-formatted docstring reconstructed from entity documentation fields:

```
/**
 * @{tag} {signature_or_name}
 *
 * @brief {brief}
 *
 * @details {details}
 *
 * @note {notes}
 *
 * @rationale {rationale}
 *
 * @param {name} {description}
 * @return {returns}
 */
```

Where `tag` is derived from entity kind: function→`@fn`, variable→`@var`, class→`@class`, struct→`@struct`, etc.

**Skip rule for doc-less entities**: Entities with no `Document` but with a non-empty name, signature, or kind receive a minimal embedding via `build_minimal_embed_text()`. Only entities where all three of name, signature, and kind are empty/null are excluded entirely (null embedding).
