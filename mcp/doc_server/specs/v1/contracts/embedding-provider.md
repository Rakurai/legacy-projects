# Contract: Embedding Provider

<!-- Canonical V1 contract. Added per spec 004-local-fastembed-provider. -->
**Feature**: 004-local-fastembed-provider
**Phase**: 1 (Design & Contracts)
**Date**: 2026-03-15

## Overview

Internal interface contract for the embedding provider abstraction. This is not an MCP-facing contract — it defines the server's internal embedding interface used by the search/resolver layer at query time and by the build pipeline for artifact generation.

---

## Interface: EmbeddingProvider

### Properties

| Property | Type | Description |
|---|---|---|
| `dimension` | `int` (read-only) | Vector dimension of the model output. Constant for a given provider instance. |

### Methods

#### `embed_query` (async)

Embed a single text string (typically a user search query).

- **Input**: `text: str` — non-empty text to embed
- **Output**: `list[float]` — vector of length `dimension`
- **Errors**: May raise on network failure (hosted) or model loading failure (local). Caller must handle gracefully (fall back to keyword search).
- **Thread safety**: Must not block the async event loop. Local provider offloads to background thread via `asyncio.to_thread()`.

#### `embed_documents` (async)

Batch-embed multiple text strings (typically entity documentation).

- **Input**: `texts: list[str]` — list of non-empty texts
- **Output**: `list[list[float]]` — one vector per input text, each of length `dimension`, in same order as input
- **Errors**: Same as `embed_query`

#### `embed_query_sync`

Synchronous variant of `embed_query` for use in the build pipeline.

- **Input/Output**: Same as `embed_query`
- **Thread safety**: Blocking call. Only for use in synchronous contexts (build script).

#### `embed_documents_sync`

Synchronous variant of `embed_documents` for use in the build pipeline.

- **Input/Output**: Same as `embed_documents`
- **Batch behavior**: Processes in batches of 32 internally (configurable per implementation).

---

## Implementations

### LocalEmbeddingProvider

Wraps `fastembed.TextEmbedding` with ONNX-based local inference.

- **Default model**: BAAI/bge-base-en-v1.5 (768-dim, ~130 MB ONNX)
- **Sync methods**: Call ONNX directly
- **Async methods**: Delegate to `asyncio.to_thread()`
- **Dimension**: Probed from model on init (embed a test string, check output length)
- **Performance**: ~5-20ms per single query, ~1-3 min for full entity set (~5,300)

### HostedEmbeddingProvider

Wraps `openai.OpenAI` (sync) and `openai.AsyncOpenAI` (async).

- **Config requires**: `EMBEDDING_BASE_URL`, `EMBEDDING_MODEL`, optionally `EMBEDDING_API_KEY`
- **Sync methods**: Use `openai.OpenAI` client
- **Async methods**: Use `openai.AsyncOpenAI` client
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
- When provider is present: calls `await provider.embed_query(query)` and blends semantic scores
- On provider error: logs warning, degrades to keyword fallback for that request

### `resolve_entity(session, query, ..., embedding_provider=None, ...)`

- Same pattern as `hybrid_search`
- Calls `await provider.embed_query(query)` in the semantic resolution stage

### `build_mcp_db.py` Stage 10

- Calls `create_provider(config)` to get a provider (may be None)
- If provider exists and no artifact cached: calls `provider.embed_documents_sync(texts)` for batch generation
- Saves result to artifact file for future builds

---

## Environment Configuration Contract

```env
# Provider selection (required for embeddings)
EMBEDDING_PROVIDER=local|hosted    # omit for keyword-only mode

# Dimension (must match provider output)
EMBEDDING_DIMENSION=768            # default 768

# Local provider config
EMBEDDING_LOCAL_MODEL=BAAI/bge-base-en-v1.5
EMBEDDING_ONNX_PROVIDER=CPUExecutionProvider  # ONNX Runtime execution provider (e.g. CoreMLExecutionProvider, CUDAExecutionProvider) <!-- spec 006 -->

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

**Skip rule**: Entities with no documentable content (all of brief, details, params, returns, notes, rationale are null) receive null embeddings.
