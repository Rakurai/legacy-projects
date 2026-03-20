# Quickstart: V1 Known Issue Fixes

**Branch**: `002-v1-issue-fixes`

---

## After implementing I-001 (entity merge) — verify with stc

Rebuild the database, then spot-check:

```bash
cd mcp/doc_server

# Rebuild (drops and repopulates all tables)
uv run python -m build_script.build_mcp_db

# Check the build log for merge count
# Expected: "split entity merged" log entries for known split pairs (stc, damage, interpret)
```

Then start the server and verify via MCP tools:

1. `search(query="stc", limit=3)` — expect exactly one result with `fan_in=640` and `is_contract_seed=true`
2. `explain_interface(entity_id=<stc entity_id>)` — expect `calling_patterns` non-empty
3. `search(query="damage", limit=3)` — expect one result (not two near-identical results)

## After implementing I-002 (score threshold) — verify search behavior

Run contract tests (no DB needed):

```bash
cd mcp/doc_server
uv run pytest tests/test_search_tool.py -v
```

Then manually verify score semantics via the running server:

1. Nonsense query: `search(query="xyzzy_nonexistent_9f3k")` — expect zero results
2. Exact match: `search(query="stc")` — expect stc as first result with score > 1.0

## Full regression suite

```bash
cd mcp/doc_server
uv run pytest tests/test_tools.py -v
uv run pytest tests/test_entity_processor.py -v
uv run pytest tests/test_search_tool.py -v
```

All 37 existing tests must pass. New tests for entity dedup and search threshold should also pass.

## Type check

```bash
cd mcp/doc_server
uv run mypy server/
```

## Lint

```bash
uv run ruff check .
uv run ruff format .
```
