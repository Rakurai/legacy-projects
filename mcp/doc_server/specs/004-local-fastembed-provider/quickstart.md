# Quickstart: Local FastEmbed Provider

**Feature**: 004-local-fastembed-provider

## Prerequisites

- Python 3.11+
- PostgreSQL with pgvector extension
- uv package manager
- The `.ai/artifacts/` directory with `code_graph.json`, `code_graph.gml`, `doc_db.json`, `capability_defs.json`, `capability_graph.json`

## Setup (Local Embedding — Default)

### 1. Install dependencies

```bash
cd .ai/mcp/doc_server
uv sync
```

This installs `fastembed` along with all other dependencies. The ONNX model (~130 MB) is downloaded automatically on first use and cached at `~/.cache/fastembed/`.

### 2. Configure environment

```bash
cp .env.example .env
```

Edit `.env`:

```env
DB_HOST=localhost
DB_PORT=4010
DB_NAME=legacy_og_docs
DB_USER=postgres
DB_PASSWORD=postgres

PROJECT_ROOT=/path/to/legacy/repo
ARTIFACTS_DIR=/path/to/legacy/repo/.ai/artifacts

EMBEDDING_PROVIDER=local
EMBEDDING_DIMENSION=768
EMBEDDING_LOCAL_MODEL=BAAI/bge-base-en-v1.5
```

### 3. Build the database

```bash
uv run python build_mcp_db.py
```

On first run (no cached artifact):
- Generates embeddings for ~5,300 entities locally (~1-3 minutes)
- Saves artifact to `{ARTIFACTS_DIR}/embed_cache_BAAI-bge-base-en-v1.5_768.pkl`
- Loads embeddings into PostgreSQL

On subsequent runs:
- Loads cached artifact directly (~2 seconds)

### 4. Start the server

```bash
uv run python -m server
```

Semantic search is now fully operational with no external service dependencies.

## Setup (Hosted Embedding — Alternative)

Edit `.env`:

```env
EMBEDDING_PROVIDER=hosted
EMBEDDING_DIMENSION=4096
EMBEDDING_BASE_URL=http://localhost:4000/v1
EMBEDDING_API_KEY=lm-studio
EMBEDDING_MODEL=text-embedding-qwen3-embedding-8b
```

The build and server will use the hosted endpoint for all embedding operations.

## Setup (No Embedding — Keyword Only)

Omit `EMBEDDING_PROVIDER` from `.env` (or leave it commented out). Search degrades to keyword-only mode. The build completes without generating or loading embeddings.

## Switching Providers

1. Update `EMBEDDING_PROVIDER`, `EMBEDDING_DIMENSION`, and model-specific fields in `.env`
2. Re-run `uv run python build_mcp_db.py`
3. Restart the server

The build will detect that no artifact exists for the new configuration and generate one. Old artifacts for other model configs are not deleted and can be reused if you switch back.

## Regenerating Embeddings

If source documentation has changed and you want fresh embeddings:

```bash
rm .ai/artifacts/embed_cache_BAAI-bge-base-en-v1.5_768.pkl
uv run python build_mcp_db.py
```

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| "Embedding endpoint not configured; semantic search disabled" at startup | `EMBEDDING_PROVIDER` not set in `.env` | Add `EMBEDDING_PROVIDER=local` to `.env` |
| "Dimension mismatch" error at startup | `EMBEDDING_DIMENSION` doesn't match the model's actual output | Set `EMBEDDING_DIMENSION=768` for bge-base-en-v1.5 |
| Search returns only keyword results (`keyword_fallback` mode) | No embedding provider or embedding error | Check server logs; ensure provider config is correct |
| Build takes several minutes on first run | Model download + embedding generation | Normal for first run. Subsequent builds use cached artifact. |
