# Implementation Plan: MCP Documentation Server

**Branch**: `001-mcp-doc-server` | **Date**: 2026-03-14 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-mcp-doc-server/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

Build an MCP (Model Context Protocol) server that exposes the Legacy MUD codebase (~5,300 entities, 25,000 dependency edges, 30 capability groups) as a searchable, analysis-capable knowledge store for AI coding assistants. The server provides entity lookup with disambiguation, hybrid semantic+keyword search, dependency graph navigation, behavioral analysis (call cones, side effects, capability touches), and architectural views via capability groups. A separate build script transforms pre-computed artifacts (entity database, dependency graph, LLM-generated documentation, embeddings, capability definitions) into a queryable PostgreSQL database with pgvector for semantic search. The server runs as a long-lived async process over stdio, serving deterministic read-only queries with structured logging and explicit degradation handling (e.g., embedding service unavailable).

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: FastMCP (latest, async MCP framework), Pydantic v2 (strict validation), SQLModel (ORM, table definitions), SQLAlchemy[asyncio] (async engine, session), asyncpg (PostgreSQL driver, transitive via SQLAlchemy), pgvector (vector column type), NetworkX (in-memory graph algorithms), loguru (structured logging), OpenAI SDK (embedding queries)
**Storage**: PostgreSQL 17 + pgvector extension (entity metadata, full-text search, embeddings), NetworkX MultiDiGraph in-memory (loaded at startup, read-only)
**Testing**: pytest with async support (pytest-asyncio); focus on happy-path integration tests (contract validation, artifact loading, query execution)
**Target Platform**: macOS/Linux local development machines (developer workstations running MCP clients like VS Code, Claude Desktop)
**Project Type**: MCP server (long-lived stdio-based service) + offline ETL build script
**Performance Goals**: < 100ms single-entity lookup, < 500ms hybrid search (including embedding query), < 1s behavior slice computation (depth 5, <200 cone size), < 5s server startup with graph load
**Constraints**: No pagination (hard truncation with metadata), no write access (read-only queries), deterministic responses (no runtime LLM inference), async/await for I/O, strict typing (mypy --strict), fail-fast validation (no fallbacks or silent masking)
**Scale/Scope**: 5,293 documented entities, ~25,000 graph edges, 30 capability groups, 633 entry points; single-codebase server (Legacy MUD); database ~500 MB (entities + embeddings + full-text vectors)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Note**: The Legacy MUD Server Constitution (v1.0.0) applies to the **MUD source code in `src/`**, not this MCP documentation server which lives in `.ai/mcp/doc_server/`. This is a separate Python project serving the documentation layer. The constitution's principles are noted here for context but do not create gates for this feature.

### Informational Review (Not Blocking)

**I. Documentation-First** — ✅ Aligned
- This MCP server *is* documentation infrastructure; inline docs will explain design rationale
- Build script and server code will include docstrings for complex logic
- No breaking changes to MUD source code

**II. Backward Compatibility** — ✅ Not Applicable
- MCP server is new infrastructure; no backward compatibility concerns
- Reads pre-computed artifacts as input; does not modify MUD source or player data

**III. Pragmatic Testing** — ✅ Aligned
- Happy-path integration tests for artifact loading, query execution, resolution pipeline
- Critical paths: database population, graph construction, search accuracy
- No exhaustive edge-case matrices (PoC-level testing per PATTERNS.md)

**IV. Performance & Stability** — ✅ Aligned
- Performance targets explicit in spec (< 100ms lookups, < 500ms search, < 5s startup)
- Async I/O prevents blocking
- Read-only queries with no state mutation ensure stability

**V. Incremental Modernization** — ✅ Not Applicable
- Greenfield Python project; no legacy code to modernize

### Gate Result: ✅ **PASS** (No violations; constitution not binding for this feature)

---

### Post-Design Re-check (Phase 1 Complete)

**Gate Status**: ✅ **PASS** (No new violations)

**Design Review**:
- **Documentation**: All planning artifacts generated (research.md, data-model.md, contracts/, quickstart.md)
- **Testing Strategy**: Happy-path integration tests planned per PATTERNS.md (contract validation, artifact loading, query execution)
- **Performance**: Explicit targets in spec (< 100ms, < 500ms, < 1s); async I/O prevents blocking
- **Complexity**: No unnecessary abstraction; schema-first Pydantic models; fail-fast validation

**No violations introduced during design phase.** Ready for implementation (Phase 2: Task Generation via `/speckit.tasks`).

## Project Structure

### Documentation (this feature)

```text
specs/001-mcp-doc-server/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
│   ├── tools.md         # MCP tool schemas
│   ├── resources.md     # MCP resource URIs
│   └── prompts.md       # MCP canned prompts
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
.ai/mcp/doc_server/
├── server/
│   ├── __init__.py
│   ├── server.py          # FastMCP app entry point, tool handlers
│   ├── config.py          # Environment config validation (pydantic-settings)
│   ├── models.py          # Pydantic API models (EntitySummary, SearchResult, BehaviorSlice, etc.)
│   ├── db_models.py       # SQLModel table=True definitions (Entity, Edge, Capability, etc.) - CANONICAL LOCATION
│   ├── db.py              # SQLAlchemy async engine + session factory, repository classes
│   ├── graph.py           # NetworkX graph loading, BFS traversal, call cone computation
│   ├── resolver.py        # Entity resolution pipeline (exact → prefix → keyword → semantic)
│   ├── search.py          # Hybrid search (pgvector + full-text + exact match boost)
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── entity.py      # Entity lookup tools (resolve, get, get_source, list_file, etc.)
│   │   ├── search.py      # Search tool
│   │   ├── graph.py       # Graph navigation tools (callers, callees, dependencies, hierarchy)
│   │   ├── behavior.py    # Behavioral analysis tools (behavior_slice, state_touches, hotspots)
│   │   └── capability.py  # Capability tools (list, detail, compare, entry_points)
│   ├── resources.py       # MCP resource handlers (legacy://capabilities, legacy://entity/*, etc.)
│   └── prompts.py         # MCP canned prompts (explain_entity, analyze_behavior, etc.)
├── build_mcp_db.py        # Offline ETL: artifacts → PostgreSQL (at project root per DESIGN.md)
├── build_helpers/
│   ├── __init__.py
│   ├── loaders.py         # Artifact loaders (reuse .ai/gen_docs/clustering/ modules)
│   ├── entity_processor.py # Entity + doc merge, derived metrics computation (imports schema from server/db_models.py)
│   ├── graph_loader.py    # GML → edges table, side-effect marker computation (imports schema from server/db_models.py)
│   └── embeddings_loader.py # Pickle → pgvector insertion (imports schema from server/db_models.py)
├── tests/
│   ├── conftest.py        # pytest fixtures (test DB, mock artifacts)
│   ├── test_build.py      # Build script integration tests
│   ├── test_resolution.py # Resolution pipeline tests
│   ├── test_search.py     # Search tests (keyword, semantic, hybrid)
│   ├── test_graph.py      # Graph traversal tests
│   └── test_tools.py      # Tool contract tests (input/output schemas)
├── .env.example           # Example configuration
├── pyproject.toml         # uv project config (dependencies, dev tools)
├── README.md              # Quick setup instructions
└── docker-compose.yml     # PostgreSQL 17 + pgvector container
```

**Structure Decision**: Single Python project with two main entry points: `server/server.py` (long-lived MCP server) and `build_mcp_db.py` (offline ETL, at project root per DESIGN.md §12). The project lives in `.ai/mcp/doc_server/` to separate it from the C++ MUD source code. Uses `uv` for Python dependency management. Database schema is defined in `server/db_models.py` (SQLModel table=True classes) and imported by build_helpers modules—this ensures the server has no dependency on build_helpers. Database access uses SQLModel table models with SQLAlchemy async engine (asyncpg driver); repositories encapsulate queries, services own transactions. The server reuses existing artifact parsers from `.ai/gen_docs/clustering/` (doxygen_parse, doxygen_graph, doc_db modules) rather than reinventing parsing logic. PostgreSQL runs in Docker for local development; database is populated offline before server startup.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

*No violations — constitution not applicable to this MCP server project.*
