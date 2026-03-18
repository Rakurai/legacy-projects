# Quickstart: MCP Documentation Server

**Feature**: 001-mcp-doc-server
**Phase**: 1 (Design & Contracts)
**Date**: 2026-03-14

## Overview

This guide covers setting up and running the Legacy MCP Documentation Server from scratch: environment setup, database initialization, artifact processing, server launch, and MCP client configuration.

**Prerequisites:**
- Python 3.11+
- Docker (for PostgreSQL + pgvector)
- `uv` Python package manager
- Pre-computed artifacts in `artifacts/`

**Time to First Query**: ~10 minutes (5 min build + instant server startup)

---

## 1. Environment Setup

### 1.1 Install Dependencies

```bash
# Navigate to project directory
cd mcp/doc_server/

# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment and install dependencies
uv sync
```

**Dependencies Installed:**
- FastMCP (MCP server framework)
- Pydantic v2 (validation)
- SQLModel (ORM + table definitions)
- SQLAlchemy[asyncio] (async engine, session — asyncpg driver transitive)
- NetworkX (graph algorithms)
- loguru (logging)
- OpenAI SDK (embeddings)
- pytest + pytest-asyncio (testing)

### 1.2 Start PostgreSQL

```bash
# Start PostgreSQL 17 with pgvector extension
docker-compose up -d

# Verify container is running
docker ps | grep postgres
```

**Container Specs:**
- Image: `pgvector/pgvector:pg17`
- Port: `5432`
- Database: `legacy_docs`
- User: `postgres`
- Password: `postgres` (change in production)

### 1.3 Configure Environment

```bash
# Copy example config
cp .env.example .env

# Edit .env with your settings
nano .env
```

**Required Settings:**
```bash
# PostgreSQL
PGHOST=localhost
PGPORT=5432
PGDATABASE=legacy_docs
PGUSER=postgres
PGPASSWORD=postgres

# Project paths
PROJECT_ROOT=/Users/QTE2333/repos/legacy
ARTIFACTS_DIR=/Users/QTE2333/repos/legacy/artifacts

# Logging
LOG_LEVEL=INFO

# Optional: Embedding endpoint (degrades to keyword-only mode if unavailable)
# EMBEDDING_BASE_URL=http://localhost:4000/v1
# EMBEDDING_API_KEY=lm-studio
# EMBEDDING_MODEL=text-embedding-qwen3-embedding-8b
```

---

## 2. Build Database

### 2.1 Validate Artifacts

```bash
# Verify all required artifacts exist
ls -lh $PROJECT_ROOT/artifacts/

# Expected files:
# - code_graph.json      (~8 MB, 5305 entities)
# - code_graph.gml       (~12 MB, dependency graph)
# - doc_db.json          (~15 MB, 5293 documents)
# - embeddings_cache.pkl (~83 MB, 4096-dim embeddings)
# - capability_defs.json (~50 KB, 30 capability groups)
# - capability_graph.json (~100 KB, group dependencies)
```

### 2.2 Run Build Script

```bash
# Activate virtual environment (if not using uv run)
source .venv/bin/activate

# Run build script
uv run python build_mcp_db.py
```

**Build Pipeline (expected output):**
```
2026-03-14 10:15:23.142 | INFO | build_mcp_db:main:45 - Starting database build artifacts_dir="artifacts"
2026-03-14 10:15:23.156 | INFO | loaders:validate_artifacts:28 - Validating artifacts
2026-03-14 10:15:23.158 | INFO | loaders:validate_artifacts:35 - All artifacts present and valid
2026-03-14 10:15:24.892 | INFO | loaders:load_entities:52 - Loaded entity database entities=5305
2026-03-14 10:15:26.143 | INFO | loaders:load_documents:68 - Loaded document database documents=5293
2026-03-14 10:15:27.234 | INFO | entity_processor:merge_entities:95 - Merged entities and docs merged=5293
2026-03-14 10:15:28.456 | INFO | entity_processor:extract_source_code:112 - Extracted source code entities_with_code=5127
2026-03-14 10:15:30.678 | INFO | entity_processor:compute_metrics:145 - Computed derived metrics doc_quality=5293 fan_in=2365 fan_out=2365 bridges=342 entry_points=633
2026-03-14 10:15:32.901 | INFO | entity_processor:generate_tsvectors:178 - Generated full-text search vectors vectors=5293
2026-03-14 10:15:34.234 | INFO | embeddings_loader:load_embeddings:89 - Loaded embeddings embeddings=5293
2026-03-14 10:15:36.567 | INFO | database:populate_entities:203 - Populated entities table rows=5293
2026-03-14 10:15:41.890 | INFO | graph_loader:populate_edges:245 - Populated edges table rows=25142
2026-03-14 10:15:43.123 | INFO | loaders:populate_capabilities:267 - Populated capabilities tables capabilities=30 edges=89
2026-03-14 10:15:43.456 | INFO | database:analyze_tables:289 - Updated planner statistics
2026-03-14 10:15:43.457 | INFO | build_mcp_db:main:78 - Database build complete duration_seconds=20.3
```

**Performance**: ~20 seconds for full rebuild (5293 entities, 25K edges, embeddings).

### 2.3 Verify Database

```bash
# Connect to database
docker exec -it mcp-postgres psql -U postgres -d legacy_docs

# Check row counts
SELECT 'entities' AS table, COUNT(*) FROM entities
UNION ALL
SELECT 'edges', COUNT(*) FROM edges
UNION ALL
SELECT 'capabilities', COUNT(*) FROM capabilities;

# Expected output:
#    table     | count
# -------------+-------
#  entities    |  5293
#  edges       | 25142
#  capabilities|    30

# Test full-text search
SELECT signature, brief FROM entities
WHERE search_vector @@ plainto_tsquery('damage calculation')
LIMIT 5;

# Test vector search (if embeddings loaded)
SELECT COUNT(*) FROM entities WHERE embedding IS NOT NULL;
# Expected: 5293
```

---

## 3. Start Server

### 3.1 Launch MCP Server

```bash
# Start server (stdio transport)
uv run python -m server.server

# Or with explicit log level
LOG_LEVEL=DEBUG uv run python -m server.server
```

**Expected Output:**
```
2026-03-14 10:16:00.123 | INFO | server:main:45 - Starting Legacy Documentation Server version=1.0.0
2026-03-14 10:16:00.234 | INFO | database:connect:67 - Connecting to database host=localhost database=legacy_docs
2026-03-14 10:16:00.456 | INFO | database:connect:72 - Database connection established
2026-03-14 10:16:00.567 | INFO | graph:load_graph:89 - Loading dependency graph from edges table
2026-03-14 10:16:02.890 | INFO | graph:load_graph:95 - Graph loaded nodes=5300 edges=25142
2026-03-14 10:16:02.901 | INFO | server:main:78 - Checking embedding endpoint
2026-03-14 10:16:03.012 | INFO | server:main:82 - Embedding endpoint available semantic_search=enabled
2026-03-14 10:16:03.023 | INFO | server:main:89 - Server ready
[Server running on stdio transport, awaiting MCP requests...]
```

**Startup Time**: < 5 seconds (graph load is the bottleneck).

### 3.2 Verify Server Health

```bash
# In a separate terminal, send test request via MCP client or manual JSON-RPC
echo '{"jsonrpc":"2.0","method":"tools/list","id":1}' | uv run python -m server.server
```

**Expected Response** (sample):
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "tools": [
      {"name": "resolve_entity", "description": "Resolve entity name to ranked candidates", ...},
      {"name": "get_entity", "description": "Fetch full entity details", ...},
      {"name": "search", "description": "Hybrid semantic + keyword search", ...},
      ...
    ]
  }
}
```

---

## 4. MCP Client Configuration

### 4.1 VS Code (Continue Extension)

**Config File**: `~/.continue/config.json`

```json
{
  "mcpServers": {
    "legacy-docs": {
      "command": "uv",
      "args": ["run", "python", "-m", "server.server"],
      "cwd": "/Users/QTE2333/repos/legacy/mcp/doc_server",
      "env": {
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
```

**Usage in VS Code:**
1. Open Continue sidebar
2. Type: `@legacy-docs resolve_entity damage`
3. Server auto-starts and responds

### 4.2 Claude Desktop

**Config File**: `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS)

```json
{
  "mcpServers": {
    "legacy-documentation": {
      "command": "uv",
      "args": ["run", "python", "-m", "server.server"],
      "cwd": "/Users/QTE2333/repos/legacy/mcp/doc_server"
    }
  }
}
```

**Usage in Claude:**
1. Start new conversation
2. Tools available automatically
3. Use natural language: "What does the damage function do?"
4. Claude invokes `resolve_entity` → `get_entity` behind the scenes

### 4.3 Command-Line Testing (Manual)

```bash
# Using jq for JSON formatting
echo '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"resolve_entity","arguments":{"query":"damage","kind":"function"}},"id":1}' \
  | uv run python -m server.server \
  | jq '.'
```

---

## 5. Example Queries

### 5.1 Entity Resolution

**Query:**
```json
{"name": "resolve_entity", "arguments": {"query": "damage", "kind": "function"}}
```

**Response:**
```json
{
  "resolution_status": "ambiguous",
  "resolved_from": "damage",
  "match_type": "name_exact",
  "candidates": [
    {
      "entity_id": "fight_8cc_1a2b3c...",
      "signature": "void damage(Character *ch, Character *victim, int dam)",
      "name": "damage",
      "kind": "function",
      "file_path": "src/fight.cc",
      "capability": "combat",
      "brief": "Apply damage to a character...",
      "doc_quality": "high",
      "fan_in": 23,
      "fan_out": 8
    }
  ]
}
```

### 5.2 Hybrid Search

**Query:**
```json
{"name": "search", "arguments": {"query": "poison damage over time"}}
```

**Response:**
```json
{
  "search_mode": "hybrid",
  "results": [
    {
      "result_type": "entity",
      "score": 0.87,
      "search_mode": "hybrid",
      "provenance": "precomputed",
      "entity_summary": {
        "signature": "void poison_effect(Character *ch, int level)",
        "brief": "Apply periodic poison damage...",
        ...
      }
    }
  ]
}
```

### 5.3 Behavior Analysis

**Query:**
```json
{"name": "get_behavior_slice", "arguments": {"signature": "void do_kill(Character *ch, String argument)", "max_depth": 5}}
```

**Response:**
```json
{
  "seed": {...},
  "direct_callees": [12 functions],
  "transitive_cone": [87 functions],
  "capabilities_touched": {
    "combat": {"direct_count": 8, "transitive_count": 42},
    "character_state": {"direct_count": 3, "transitive_count": 18}
  },
  "side_effects": {
    "messaging": [...],
    "persistence": [...],
    "state_mutation": [...]
  }
}
```

---

## 6. Troubleshooting

### Database Connection Fails

**Error**: `sqlalchemy.exc.OperationalError: cannot connect to server`

**Fix**:
```bash
# Check PostgreSQL container
docker ps | grep postgres

# Check logs
docker logs mcp-postgres

# Restart container
docker-compose restart

# Verify connection
psql -h localhost -U postgres -d legacy_docs -c "SELECT 1;"
```

### Graph Load Timeout

**Error**: `Graph loading took > 10 seconds`

**Fix**:
- Check edges table row count: `SELECT COUNT(*) FROM edges;` (expected ~25K)
- If edges table is empty, re-run the build script: `uv run python build_mcp_db.py`
- If row count is correct but load is slow, check PostgreSQL connection performance

### Embedding Service Unavailable

**Warning**: `Embedding endpoint unavailable; semantic search disabled`

**Fix** (optional):
- If EMBEDDING_BASE_URL not set, semantic search degrades to keyword-only (this is expected and supported)
- To enable semantic search, configure OpenAI-compatible endpoint in `.env`
- Server continues working with keyword search

### Build Script Fails

**Error**: `FileNotFoundError: code_graph.json not found`

**Fix**:
```bash
# Verify artifacts directory path
echo $PROJECT_ROOT/artifacts/
ls -la $PROJECT_ROOT/artifacts/

# Check .env settings
cat .env | grep ARTIFACTS_DIR

# Regenerate artifacts (if missing)
cd $PROJECT_ROOT
# Run doxygen + docgen pipeline (see gen_docs/README.md)
```

---

## 7. Development Workflow

### 7.1 Run Tests

```bash
# Run all tests
uv run pytest tests/

# Run specific test module
uv run pytest tests/test_resolution.py -v

# Run with coverage
uv run pytest --cov=server --cov-report=html
```

### 7.2 Type Checking

```bash
# Run mypy strict type checking
uv run mypy server/ build_helpers/ --strict
```

### 7.3 Linting

```bash
# Run ruff linter
uv run ruff check server/ build_helpers/

# Auto-fix issues
uv run ruff check --fix server/ build_helpers/
```

### 7.4 Rebuild Database

```bash
# Quick rebuild (drops and recreates tables)
uv run python build_mcp_db.py

# Time: ~20 seconds for full rebuild
```

---

## 8. Production Considerations

**Not Covered in Quickstart** (PoC scope only):
- SSL/TLS for database connections
- Authentication/authorization
- Rate limiting
- Horizontal scaling
- Monitoring and alerting
- Backup and recovery

For production deployment, consult deployment guides and infrastructure documentation.

---

## Summary

**Setup Checklist:**
- [ ] Install Python 3.11+, Docker, uv
- [ ] Start PostgreSQL container (`docker-compose up -d`)
- [ ] Configure `.env` file
- [ ] Run build script (`uv run python build_mcp_db.py`)
- [ ] Verify database (`psql` queries)
- [ ] Start server (`uv run python -m server.server`)
- [ ] Configure MCP client (VS Code, Claude Desktop)
- [ ] Test queries

**Key Commands:**
```bash
# Setup
docker-compose up -d
cp .env.example .env
uv sync

# Build
uv run python build_mcp_db.py

# Run
uv run python -m server.server

# Test
uv run pytest tests/
```

**Expected Performance:**
- Database build: ~20 seconds (5293 entities)
- Server startup: < 5 seconds (graph load)
- Single-entity lookup: < 100ms
- Hybrid search: < 500ms
- Behavior slice: < 1 second

---

## Next Steps

After completing quickstart:
1. Review [contracts/tools.md](contracts/tools.md) for full tool API
2. Review [data-model.md](data-model.md) for database schema
3. Review [research.md](research.md) for technology decisions
4. Run `/speckit.tasks` to generate implementation tasks
5. Start implementing Phase 1 (Entity Resolution & Lookup)
