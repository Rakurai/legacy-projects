# Quickstart: Fix MCP Database Build Script

**Feature**: 003-fix-mcp-db-build
**Date**: 2026-03-14

## Prerequisites

- PostgreSQL 17+ with pgvector extension running (Docker: `docker compose up -d` from `mcp/doc_server/`)
- Python 3.11+ via `uv` (dependency manager)
- Pre-computed artifacts in `artifacts/` (code_graph.json, code_graph.gml, doc_db.json, embeddings_cache.pkl, capability_defs.json, capability_graph.json)
- `.env` file configured in `mcp/doc_server/`

## Files to Modify

1. `mcp/doc_server/build_mcp_db.py` — Main build script (index creation, capability population, pipeline ordering)
2. `mcp/doc_server/build_helpers/entity_processor.py` — Add capability assignment from cap_graph
3. `mcp/doc_server/build_helpers/loaders.py` — Fix docstring for load_capability_graph

## Build & Validate

```bash
cd mcp/doc_server

# Run the build
uv run python build_mcp_db.py

# Validate all fixes
uv run python test_database.py
```

## Expected Validation Output (After Fix)

```
entities: 5305 rows
edges: 34797 rows
capabilities: 30 rows
capability_edges: 200 rows        # Was: 0
entry_points: 637 rows

Sample bridge functions: N rows    # Was: 0
Indexes: 19+ total                 # Was: 5

Top capabilities by function count:
  combat (domain): 89 functions    # Was: 0
  ...

Doc quality distribution:
  low: ~5300
  medium: ~5
```

## Success Criteria Checks (SQL)

```sql
-- SC-001: At least 19 indexes
SELECT COUNT(*) FROM pg_indexes WHERE schemaname = 'public';  -- >= 19

-- SC-002: ~848 entities with capability
SELECT COUNT(*) FROM entities WHERE capability IS NOT NULL;  -- ~848

-- SC-003: Bridge functions detected
SELECT COUNT(*) FROM entities WHERE is_bridge = true;  -- > 10

-- SC-004: All capabilities have function_count > 0
SELECT COUNT(*) FROM capabilities WHERE function_count = 0;  -- = 0

-- SC-005: 200 capability edges
SELECT COUNT(*) FROM capability_edges;  -- = 200

-- SC-006: All capabilities have description
SELECT COUNT(*) FROM capabilities WHERE description = '' OR description IS NULL;  -- = 0
```

## Key Design Decisions

- **No schema changes**: All fixes are in the build pipeline data flow, not the database schema
- **Capability source**: Use `capability_graph.json` members, not `doc.system` (which is always null)
- **Pipeline reorder**: Load capability_graph earlier so entity capabilities are set before bridge detection
- **Single engine**: Use `db_manager.engine` for both table creation and index creation
