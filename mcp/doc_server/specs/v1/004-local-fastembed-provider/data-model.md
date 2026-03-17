# Data Model: Local FastEmbed Provider

**Feature**: 004-local-fastembed-provider  
**Date**: 2026-03-15

## Entities

### Configuration (ServerConfig)

Extended environment-based settings for embedding provider selection.

| Field | Type | Default | Source | Validation |
|---|---|---|---|---|
| embedding_provider | "local" \| "hosted" \| null | null | `EMBEDDING_PROVIDER` env var | Must be one of the three values; null means no provider |
| embedding_local_model | string | "BAAI/bge-base-en-v1.5" | `EMBEDDING_LOCAL_MODEL` env var | Non-empty when provider = "local" |
| embedding_dimension | integer | 768 | `EMBEDDING_DIMENSION` env var | Positive integer, must match provider output (validated at startup) |
| embedding_base_url | string \| null | null | `EMBEDDING_BASE_URL` env var | Required when provider = "hosted" |
| embedding_api_key | string \| null | null | `EMBEDDING_API_KEY` env var | — |
| embedding_model | string \| null | null | `EMBEDDING_MODEL` env var | Required when provider = "hosted" |

**Derived properties:**
- `embedding_enabled`: true when `embedding_provider` is not null
- `embed_cache_filename`: `embed_cache_{model_slug}_{dimension}.pkl` where model_slug is the model name with `/` → `-`

### Embedding Provider

Runtime abstraction for generating embedding vectors.

| Attribute | Type | Description |
|---|---|---|
| dimension | integer (read-only) | Vector dimension of the model output |

| Method | Signature | Description |
|---|---|---|
| embed_query | async (text: str) → list[float] | Embed a single query string |
| embed_documents | async (texts: list[str]) → list[list[float]] | Batch-embed multiple texts |
| embed_query_sync | (text: str) → list[float] | Synchronous single-text embedding (for build) |
| embed_documents_sync | (texts: list[str]) → list[list[float]] | Synchronous batch embedding (for build) |

**Variants:**
- `LocalEmbeddingProvider`: Wraps `fastembed.TextEmbedding`. Sync methods call ONNX directly. Async methods delegate to `asyncio.to_thread()`.
- `HostedEmbeddingProvider`: Wraps `openai.OpenAI` (sync) and `openai.AsyncOpenAI` (async). Passes model name and encoding format through.

### Embedding Artifact

Serialized file mapping entity IDs to embedding vectors.

| Attribute | Type | Description |
|---|---|---|
| filename | string | `embed_cache_{model_slug}_{dim}.pkl` |
| content | dict[str, list[float]] | entity_id → embedding vector |
| format | pickle | Standard Python pickle serialization |

**Lifecycle:**
1. Build checks if artifact file exists at `{artifacts_dir}/{embed_cache_filename}`
2. If exists → load and attach to entities
3. If missing and provider configured → generate, save, then attach
4. If missing and no provider → skip embeddings (null columns), log warning
5. Invalidation is manual — developer deletes the file

### Entity (db_models.Entity — modified)

| Changed Field | Before | After |
|---|---|---|
| embedding | `Column(Vector(4096))` | `Column(Vector(EMBEDDING_DIMENSION))` where `EMBEDDING_DIMENSION` is read from environment at import time, default 768 |

All other Entity fields unchanged.

### Entity Embed Text

Not a persisted entity. An intermediate text representation computed at build time from `MergedEntity` fields.

**Construction rule** (from `build_embed_text(merged)`):**

```
/**
 * @{tag} {signature_or_name}
 *
 * @brief {doc.brief}
 *
 * @details {doc.details}
 *
 * @note {doc.notes}
 *
 * @rationale {doc.rationale}
 *
 * @param {name} {description}    (for each param)
 * @return {doc.returns}
 */
```

Where `tag` is derived from `entity.kind`: function→`@fn`, variable→`@var`, class→`@class`, struct→`@struct`, enum→`@enum`, define→`@def`, namespace→`@namespace`, group→`@defgroup`.

**Skip rule**: If `doc` is None or all of (`brief`, `details`, `params`, `returns`, `notes`, `rationale`) are None, the entity is skipped (receives null embedding).

### Lifespan Context (modified)

| Changed Field | Before | After |
|---|---|---|
| embedding_client | `AsyncOpenAI \| None` | removed |
| embedding_model | `str` | removed |
| embedding_provider | — | `EmbeddingProvider \| None` (new) |

## State Transitions

### Build Pipeline — Stage 9 (Embeddings)

```
START
  ├─ provider configured? ──NO──→ artifact exists? ──YES──→ load artifact → attach
  │                                                  │
  │                                                  └──NO──→ log warning → skip (nulls) → END
  │
  └─YES──→ artifact exists? ──YES──→ load artifact → attach → END
                              │
                              └──NO──→ generate via provider → save artifact → attach → END
```

### Server Startup — Embedding Initialization

```
START
  ├─ embedding_provider config set? ──NO──→ log "semantic search disabled" → provider = None → END
  │
  └─YES──→ instantiate provider (local or hosted)
            ├─ success? ──YES──→ validate dimension matches config → provider ready → END
            │                                                          │
            │                                         (mismatch) → FAIL FAST with error
            └─ failure? → log warning → provider = None → END
```

### Runtime Query — Embedding Path

```
hybrid_search(query, provider)
  ├─ provider is None? → keyword_fallback mode → END
  │
  └─ provider exists → try embed_query(query)
                          ├─ success → use vector for semantic search → hybrid mode → END
                          └─ exception → log warning → keyword_fallback mode → END
```
