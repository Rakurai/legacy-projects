# Implementation Plan: Local FastEmbed Provider

**Branch**: `004-local-fastembed-provider` | **Date**: 2026-03-15 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `specs/004-local-fastembed-provider/spec.md`

## Summary

Add FastEmbed (BAAI/bge-base-en-v1.5, 768-dim) as a bundled local embedding provider for the MCP doc server, with runtime provider selection via environment configuration. Introduces an `EmbeddingProvider` abstraction that supports both local (ONNX) and hosted (OpenAI-compatible) backends. The build pipeline gains an auto-generate-if-missing flow for embedding artifacts keyed by model+dimension. The existing hosted embedding path is preserved as an alternative.

## Technical Context

**Language/Version**: Python 3.11+  
**Primary Dependencies**: FastMCP, SQLModel/SQLAlchemy async, pgvector, openai SDK, fastembed (new), pydantic-settings  
**Storage**: PostgreSQL 18 + pgvector extension (vector column dimension now configurable)  
**Testing**: pytest + pytest-asyncio  
**Target Platform**: macOS/Linux development machines  
**Project Type**: MCP tool server + offline build pipeline  
**Performance Goals**: <100ms query-time embedding latency (local); <5min full artifact generation (~5,300 entities)  
**Constraints**: Must not block async event loop; must work fully offline after initial model download  
**Scale/Scope**: ~5,300 entities, single-developer usage, build runs infrequently

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Applicable? | Status | Notes |
|---|---|---|---|
| I. Documentation-First | Yes | ✅ PASS | Spec, plan, and inline docs all precede implementation |
| II. Backward Compatibility | Marginal | ✅ PASS | This is Python MCP server code, not the C++ game server. No player data, save files, area formats, or MobProg affected. The hosted embedding path is preserved as a config option. |
| III. Pragmatic Testing | Yes | ✅ PASS | Embedding is a critical search/query path. Tests required for: provider abstraction, build generate-or-load logic, dimension validation. |
| IV. Performance & Stability | Yes | ✅ PASS | FR-012 mandates background thread for local embed. SC-004 sets <100ms query latency target. |
| V. Incremental Modernization | Yes | ✅ PASS | Adds new `embedding.py` module + `embed_text.py` helper. Adapts existing interfaces incrementally (config → lifespan → search/resolver → tools). No wholesale rewrite. |

No gate violations. No complexity justification needed.

## Project Structure

### Documentation (this feature)

```text
specs/004-local-fastembed-provider/
├── plan.md              # This file
├── research.md          # Phase 0: technology research
├── data-model.md        # Phase 1: entity/config model
├── quickstart.md        # Phase 1: developer onboarding
├── contracts/           # Phase 1: interface contracts
│   └── embedding-provider.md
└── tasks.md             # Phase 2: implementation tasks (created by /speckit.tasks)
```

### Source Code (repository root)

```text
mcp/doc_server/
├── pyproject.toml                       # + fastembed dependency
├── .env.example                         # + new embedding config vars
├── build_mcp_db.py                      # Stage 9 load-or-generate flow
├── server/
│   ├── config.py                        # + provider type, local model, dimension fields
│   ├── embedding.py                     # NEW: EmbeddingProvider protocol + 2 implementations + factory
│   ├── db_models.py                     # Vector(4096) → Vector(configurable)
│   ├── lifespan.py                      # EmbeddingProvider replaces AsyncOpenAI client
│   ├── search.py                        # hybrid_search takes provider instead of client+model
│   ├── resolver.py                      # resolve_entity takes provider instead of client+model
│   └── tools/
│       ├── search.py                    # pass provider from context
│       └── entity.py                    # pass provider from context
├── build_helpers/
│   ├── embed_text.py                    # NEW: build_embed_text() — docstring reconstruction
│   ├── embeddings_loader.py             # rewritten: load/generate/save with config-aware naming
│   └── loaders.py                       # remove embeddings_cache.pkl from required list
└── tests/
    ├── test_embedding_provider.py       # NEW: unit tests for provider abstraction
    └── test_embed_text.py               # NEW: unit tests for text construction
```

**Structure Decision**: Existing flat layout within `mcp/doc_server/` is preserved. Two new files (`server/embedding.py`, `build_helpers/embed_text.py`) and two new test files are added. No directory restructuring needed.

## Constitution Check — Post-Design

*Re-evaluated after Phase 1 design is complete.*

| Principle | Status | Post-Design Notes |
|---|---|---|
| I. Documentation-First | ✅ PASS | research.md, data-model.md, contracts/, quickstart.md all produced. CLAUDE.md and agent context updated with new technology. |
| II. Backward Compatibility | ✅ PASS | No game server, player data, or area file impact. Hosted embedding path preserved — existing `.env` configs continue to work if `EMBEDDING_PROVIDER=hosted` is set. |
| III. Pragmatic Testing | ✅ PASS | Two test files planned: `test_embedding_provider.py` (provider abstraction, dimension validation, factory) and `test_embed_text.py` (text construction, skip rule). |
| IV. Performance & Stability | ✅ PASS | `asyncio.to_thread()` prevents event loop blocking (FR-012). Single-query latency ~5-20ms, well under 100ms budget (SC-004). |
| V. Incremental Modernization | ✅ PASS | Two new modules added. Existing interfaces adapted incrementally (6 files gain `embedding_provider` parameter replacing `embedding_client + embedding_model`). No rewrites. |

No gate violations. No complexity justification needed.
