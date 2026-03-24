# Legacy MUD Documentation Server

Read-only [MCP](https://modelcontextprotocol.io/) server that exposes a legacy
DikuMUD/ROM-style C++ MUD codebase (~90 KLOC) as a searchable, analysis-capable
knowledge store. AI agents use it to research legacy features during migration
planning and spec creation — without loading raw artifacts into context or
parsing source files directly.

All data is pre-computed and deterministic. No LLM inference at runtime.

## What It Provides

The server organizes codebase knowledge in additive layers:

| Layer | Version | Question Answered |
|-------|---------|-------------------|
| **Implementation** | V1 (live) | *What is this code object and how does it work?* |
| **Conceptual** | V2 (designed) | *What larger system narrative helps interpret it?* |
| **User-Facing** | V3 (planned) | *What does the player see and expect?* |
| **Specification** | V4 (planned) | *What are the content authoring rules?* |

### V1 Data (Current)

- ~5,300 entities parsed from Doxygen XML (functions, classes, structs, files, variables)
- ~25,000 dependency edges (calls, uses, inherits, includes, contained_by)
- LLM-generated documentation per source file (briefs, details, params, rationale, usages)
- 30 capability group definitions with typed inter-capability dependencies
- Source code extracted at build time
- Multi-view search: dual embeddings (doc + symbol), dual tsvectors (english + simple), trigram fuzzy matching, cross-encoder reranking, qualified-name scoped disambiguation

## Architecture

```
┌──────────────┐    stdio/JSON-RPC    ┌──────────────────────┐
│  MCP Client  │◄────────────────────►│  FastMCP Server      │
│  (VS Code,   │                      │                      │
│   Claude,    │                      │  ┌────────────────┐  │
│   Inspector) │                      │  │ NetworkX Graph │  │
│              │                      │  │ (in-memory,    │  │
│              │                      │  │  read-only)    │  │
└──────────────┘                      │  └────────────────┘  │
                                      │  ┌────────────────┐  │
                                      │  │ PostgreSQL +   │  │
                                      │  │ pgvector       │  │
                                      │  └────────────────┘  │
                                      │  ┌────────────────┐  │
                                      │  │ Embedding +    │  │
                                      │  │ Cross-Encoder  │  │
                                      │  └────────────────┘  │
                                      └──────────────────────┘
```

- **FastMCP** framework over stdio transport
- **PostgreSQL 17+ with pgvector and pg_trgm** for entity storage, full-text search, vector similarity, and trigram fuzzy matching
- **NetworkX** in-memory directed multigraph for graph traversal (loaded from DB at startup)
- **FastEmbed** local ONNX embeddings (required) and cross-encoder reranking

## Quick Start

```bash
# 1. Set up PostgreSQL and build the database (see INSTALL.md)
cd mcp/doc_server/
cp .env.example .env        # edit with your DB credentials and paths
docker-compose up -d
uv sync
uv run python -m build_mcp_db

# 2. Run the server
uv run python -m server.server

# 3. Or inspect interactively
npx @modelcontextprotocol/inspector -- \
  uv run --directory mcp/doc_server python -m server.server
```

For full setup instructions, see [INSTALL.md](INSTALL.md).

## Tools (15)

### Entity Lookup

| Tool | Purpose |
|------|---------|
| `get_entity` | Full entity record by ID — docs, source location, metrics, optional source code and graph neighbors |
| `get_source_code` | Source code with configurable context lines |

### Search

| Tool | Purpose |
|------|---------|
| `search` | Multi-view search: 5-channel retrieval (doc/symbol semantic + keyword + trigram), floor filtering, cross-encoder reranking, qualified-name scoped disambiguation |

### Graph Navigation

| Tool | Purpose |
|------|---------|
| `get_callers` | Backward call graph traversal, depth 1–3 |
| `get_callees` | Forward call graph traversal, depth 1–3 |
| `get_dependencies` | Filtered dependencies by relationship type and direction |
| `get_class_hierarchy` | Base classes and derived classes for a class entity |
| `get_related_entities` | All direct neighbors grouped by relationship type |

### Behavioral Analysis

| Tool | Purpose |
|------|---------|
| `get_behavior_slice` | Transitive call cone with capabilities touched, globals used, and categorized side effects |
| `get_state_touches` | Direct + transitive global variable usage and side effects |
| `explain_interface` | Five-part behavioral contract: signature, mechanism, caller-derived contract, preconditions, calling patterns |

### Capabilities

| Tool | Purpose |
|------|---------|
| `list_capabilities` | All 30 capability groups with type, description, function count, stability |
| `get_capability_detail` | Group definition, typed dependency edges, entry points, optional function list |
| `compare_capabilities` | Shared/unique dependencies and bridge entities between 2+ capabilities |
| `list_entry_points` | `do_*`, `spell_*`, `spec_*` functions with optional capability/name filter |
| `get_entry_point_info` | Which capabilities an entry point exercises, with direct/transitive counts |

### Resources (5)

| URI | Description |
|-----|-------------|
| `legacy://capabilities` | All capability groups |
| `legacy://capability/{name}` | Capability detail |
| `legacy://entity/{entity_id}` | Full entity record |
| `legacy://file/{path}` | Entities in a source file |
| `legacy://stats` | Server statistics |

### Prompts (4)

| Prompt | Purpose |
|--------|---------|
| `explain_entity` | Entity explanation workflow |
| `analyze_behavior` | Behavioral analysis with call cone and side effects |
| `compare_entry_points` | Compare entry points for shared dependencies |
| `explore_capability` | Explore a capability group's architecture |

## Entity IDs

Entities use deterministic IDs in `{prefix}:{7hex}` format (e.g. `fn:a1b2c3d`).
Prefixes: `fn` (function/define), `cls` (class/struct), `var` (variable),
`file` (file), `sym` (other). IDs are stable across database rebuilds from the
same artifacts. The `search` tool is the sole path from human-readable text to
entity IDs.

## Development

```bash
# Run tests (contract tests, no live DB needed)
cd mcp/doc_server/
uv run pytest tests/test_tools.py -v

# Lint & format
uv run ruff check .
uv run ruff format .

# Type check
uv run mypy server/
```

## Specs

- [V1 Spec](specs/v1/spec.md) — implemented
- [V1 Tool Contracts](specs/v1/contracts/tools.md)
- [V1 Data Model](specs/v1/MODEL.md)
- [V2 Design](specs/v2/DESIGN_v2.md) — designed, Stage 0 complete
