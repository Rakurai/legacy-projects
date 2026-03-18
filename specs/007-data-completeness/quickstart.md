# Quickstart: MCP Build Pipeline — Data Completeness Fixes

**Feature**: 007-data-completeness
**Date**: 2026-03-18

## Prerequisites

1. PostgreSQL 18 + pgvector running (Docker or local)
2. `.env` configured in `mcp/doc_server/` with:
   - `PROJECT_ROOT` pointing to the legacy C++ source tree root (the directory containing `src/`, `include/`, etc.)
   - Database credentials (`DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`)
   - `EMBEDDING_PROVIDER=local` (or `hosted` with endpoint config, or omit for keyword-only)
3. `uv sync` completed at repo root

## Verify Source Tree Configuration

```bash
# Check that PROJECT_ROOT resolves to the C++ source directory
cd mcp/doc_server
grep PROJECT_ROOT .env

# Verify source files are accessible (example check)
ls "$(grep PROJECT_ROOT .env | cut -d= -f2)/src/fight.cc"
```

## Run Build

```bash
cd mcp/doc_server
uv run python -m build_mcp_db
```

Expected log output includes:
- Source extraction summary: `extracted=N, failed=N, skipped=N, body_located=N`
- Embedding summary: `doc_embeds=N, minimal_embeds=N, no_embed=N, coverage=X%`

## Verify Results

```bash
# Connect to the database and run verification queries
cd mcp/doc_server
uv run python -c "
from server.config import ServerConfig
config = ServerConfig()
print(f'PROJECT_ROOT: {config.project_root}')
print(f'Artifacts: {config.artifacts_path}')
"
```

After build, verify in PostgreSQL:

```sql
-- Source code population (SC-001: ≥90% of body-located)
SELECT
  COUNT(*) FILTER (WHERE source_text IS NOT NULL) AS has_source,
  COUNT(*) FILTER (WHERE body_start_line IS NOT NULL) AS has_body_loc,
  ROUND(100.0 * COUNT(*) FILTER (WHERE source_text IS NOT NULL) /
    NULLIF(COUNT(*) FILTER (WHERE body_start_line IS NOT NULL), 0), 1) AS pct
FROM entities;

-- Embedding coverage (SC-002: ≥95%)
SELECT
  COUNT(*) AS total,
  COUNT(*) FILTER (WHERE embedding IS NOT NULL) AS has_embed,
  ROUND(100.0 * COUNT(*) FILTER (WHERE embedding IS NOT NULL) / COUNT(*), 1) AS pct
FROM entities;

-- Params normalization (SC-003: only meaningful content)
SELECT
  COUNT(*) FILTER (WHERE params IS NOT NULL) AS has_params,
  COUNT(*) AS total
FROM entities;
-- Expected: ~1,800–2,100 has_params (not ~5,055)
```

## Run Tests

```bash
cd mcp/doc_server
uv run pytest tests/ -v
```

## Test Invalid PROJECT_ROOT (SC-004)

```bash
# Temporarily set a bad PROJECT_ROOT to verify fail-fast
cd mcp/doc_server
PROJECT_ROOT=/nonexistent uv run python -m build_mcp_db
# Expected: build fails with error naming /nonexistent
```
