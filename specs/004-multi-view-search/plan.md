# Implementation Plan: Multi-View Search Pipeline

**Branch**: `004-multi-view-search` | **Date**: 2026-03-21 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/004-multi-view-search/spec.md`

## Summary

Replace the MCP doc server's single-channel hybrid search (one embedding + one tsvector + exact match with weighted score fusion) with a multi-view search pipeline. The new pipeline uses five parallel retrieval channels (doc semantic, symbol semantic, doc keyword, symbol keyword, trigram), per-signal floor filtering, and cross-encoder reranking through a `RetrievalView` DI abstraction. It also removes the entire keyword-only degradation system — embedding and cross-encoder are hard startup requirements.

## Technical Context

**Language/Version**: Python 3.14+ (lazy annotation evaluation native)
**Primary Dependencies**: FastMCP, AsyncPG, SQLModel, fastembed (ONNX embeddings + cross-encoder reranking), pgvector, NetworkX, Pydantic v2, loguru
**Storage**: PostgreSQL 18 with pgvector extension + pg_trgm extension (Docker via docker-compose.yml)
**Testing**: pytest + pytest-randomly (contract tests, no DB needed for existing tests)
**Target Platform**: macOS development machine (stdio MCP transport)
**Project Type**: MCP server (library exposed via FastMCP stdio transport)
**Performance Goals**: Search latency <2s end-to-end including cross-encoder; build pipeline <5min for ~5,300 entities
**Constraints**: CPU-only inference (ONNX local provider); cross-encoder processes ~100-200 candidates per query
**Scale/Scope**: ~5,300 entities, ~25K dependency edges, ~6,500 containment edges, ~20K usage rows

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| # | Principle | Status | Notes |
|---|-----------|--------|-------|
| 1 | **Fail-Fast, No Fallbacks** | ✅ PASS | Spec explicitly removes `SearchMode.KEYWORD_FALLBACK`, `embedding_enabled`, and all optional `EmbeddingProvider` typing. Server crashes at startup if embedding or cross-encoder unavailable (FR-049, FR-070–FR-075). |
| 2 | **Types Are Contracts** | ✅ PASS | `EmbeddingProvider` becomes non-optional everywhere (FR-072). `RetrievalView` is a typed abstraction. `SearchResult` gains typed `winning_view`/`winning_score`/`losing_score` fields. `SearchMode` enum removed entirely. mypy --strict enforced. |
| 3 | **Source Reflects Current Truth** | ✅ PASS | Old `embedding`/`search_vector` columns dropped (FR-063). `SearchMode` enum removed (FR-070). No compatibility shims — clean rebuild migration (A-008). |
| 4 | **uv-Only Toolchain** | ✅ PASS | All execution via `uv run`. No direct python/pip/pytest. |
| 5 | **Notebook Discipline** | N/A | No notebook changes in this feature. |
| 6 | **Pydantic v2** | ✅ PASS | All models use v2 patterns. `SearchResult` uses `BaseModel` + `Field`. No v1 imports. |
| 7 | **SQLModel** | ✅ PASS | Entity model uses `SQLModel` with `table=True`. New columns follow explicit typing rules. No business logic in models. |
| 8 | **PATTERNS.md** | ✅ PASS | No fallbacks (word and practice forbidden). Fail-fast on config. Schema-first. No defensive programming. loguru logging. |

**Gate result**: PASS — no violations. Proceed to Phase 0.

## Project Structure

### Documentation (this feature)

```text
specs/004-multi-view-search/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Phase 0: technology research
├── data-model.md        # Phase 1: entity & schema design
├── quickstart.md        # Phase 1: implementation quickstart
├── contracts/           # Phase 1: search tool response contracts
│   └── search-response.md
├── checklists/
│   └── requirements.md  # Quality checklist
└── tasks.md             # Phase 2: implementation tasks (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
mcp/doc_server/
├── server/
│   ├── db_models.py          # Entity table: +6 columns, -2 columns (FR-001–FR-008)
│   ├── config.py             # EMBEDDING_PROVIDER required, remove embedding_enabled (FR-071, FR-073)
│   ├── lifespan.py           # EmbeddingProvider non-optional, cross-encoder init (FR-072)
│   ├── embedding.py          # create_provider returns non-optional; cross-encoder provider added
│   ├── enums.py              # Remove SearchMode enum (FR-070)
│   ├── models.py             # SearchResult: +winning_view/scores, -search_mode (FR-061)
│   ├── search.py             # NEW: 7-stage multi-view pipeline (FR-030–FR-044)
│   ├── tools/
│   │   └── search.py         # Tool wiring layer — modified (FR-060, FR-061)
│   ├── resolver.py           # EmbeddingProvider non-optional (FR-072, FR-074)
│   ├── retrieval_view.py     # NEW: RetrievalView abstraction (FR-050–FR-053)
│   └── cross_encoder.py      # NEW: Cross-encoder provider (FR-045–FR-048)
├── build_mcp_db.py            # Dual embed texts, dual embeddings, dual tsvectors, pg_trgm (FR-055–FR-058)
├── build_helpers/
│   ├── entity_processor.py   # qualified_name derivation, doc/symbol embed text assembly (FR-016–FR-024)
│   └── embeddings_loader.py  # Dual cache files (doc/symbol) (FR-025–FR-026)
└── tests/
    └── test_tools.py          # Contract tests for search tool response shape
```

**Structure Decision**: Existing `mcp/doc_server/` project. New files: `retrieval_view.py`, `cross_encoder.py`. All other changes are modifications to existing files.

## Complexity Tracking

No constitution violations — table intentionally empty.

## Post-Design Constitution Re-Check

*Re-evaluated after Phase 1 design artifacts (data-model.md, contracts/, quickstart.md).*

| # | Principle | Status | Notes |
|---|-----------|--------|-------|
| 1 | **Fail-Fast, No Fallbacks** | ✅ PASS | data-model.md removes all optional typing. quickstart.md Layer 1 step 1 is "remove fallback system." |
| 2 | **Types Are Contracts** | ✅ PASS | RetrievalView frozen dataclass, SearchResult contract fully typed, EmbeddingProvider non-optional. |
| 3 | **Source Reflects Current Truth** | ✅ PASS | Clean rebuild migration. Old columns dropped. SearchMode deleted. No compatibility shims. |
| 4 | **uv-Only Toolchain** | ✅ PASS | All examples use `uv run`. |
| 5 | **Notebook Discipline** | N/A | No notebook changes. |
| 6 | **Pydantic v2** | ✅ PASS | SearchResult uses BaseModel + Field. No v1 patterns. |
| 7 | **SQLModel** | ✅ PASS | Entity model: `table=True`, explicit types, no business logic in model. |
| 8 | **PATTERNS.md** | ✅ PASS | No fallbacks in any design artifact. Fail-fast on config. loguru logging. |

**Gate result**: PASS — design is constitution-compliant.
