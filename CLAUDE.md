# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Auxiliary Python tooling for analyzing and migrating a legacy DikuMUD/ROM-style C++ MUD codebase (~90 KLOC). The legacy C++ source and the newer Evennia-based reimagining live in separate repositories but share a VS Code workspace with this one.

## Monorepo Layout (uv workspace)

- `packages/legacy_common/` — Shared library: Doxygen parsing, graph construction, semantic/structural clustering, LLM refinement, subsystem identification
- `projects/classify_fns/` — Jupyter notebooks for game subsystem classification and capability mapping
- `projects/doc_gen/` — Doxygen graph mining and LLM-based documentation generation
- `mcp/doc_server/` — FastMCP server exposing the codebase as a searchable knowledge store (PostgreSQL + pgvector, NetworkX graph, hybrid search)

## Build & Dev Commands

All commands use **uv** — never run `python`, `pip`, `pytest`, or `ruff` directly.

```bash
# Install/sync dependencies
uv sync

# Run tests (MCP server — contract tests, no DB needed)
cd mcp/doc_server && uv run pytest tests/test_tools.py -v

# Run a single test
uv run pytest tests/test_tools.py::test_name -v

# Lint & format
uv run ruff check .
uv run ruff format .

# Type checking (MCP server)
cd mcp/doc_server && uv run mypy server/

# Run MCP server (requires PostgreSQL with pgvector)
cd mcp/doc_server && uv run python -m server.server

# Build MCP database from artifacts
cd mcp/doc_server && uv run python -m build_script.build_mcp_db
```

## MCP Server Infrastructure

- PostgreSQL 18 + pgvector via Docker (`mcp/doc_server/docker-compose.yml`) or local install
- Database credentials in `mcp/doc_server/.env` (DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD)
- AsyncPG for async access, SQLModel ORM, FastMCP framework, FastEmbed for embeddings
- `artifacts/` directory contains pre-computed data: code graph (~5,300 entities), dependency graph (~25K edges), LLM-generated docs, embeddings cache, 30 capability group definitions

## Code Discipline

- **Fail-fast**: No defensive programming, no fallback logic, no legacy compatibility paths. Let errors raise.
- **Refactoring**: Update interfaces everywhere, remove dead code, no compatibility shims. Source reflects current truth; history lives in git.
- **Comments**: Explain intent or invariants only. No narration, no restating symbol names, no historical commentary.
- **Ruff**: E, W, F, I, N, UP, B, C4, SIM rules enabled. Line length 120. Target py314.
- **mypy**: Strict mode on MCP server code.

## Scratch Files

Use `.scratch/` directory for temporary scripts (gitignored). Never write temp scripts to `/tmp` or system directories.

## Jupyter Notebooks

Never edit `.ipynb` files as raw JSON. Use VS Code notebook editing tools only. One responsibility per cell, no ceremonial output, no fallback logic.
