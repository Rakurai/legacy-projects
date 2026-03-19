# Quickstart: Knowledge Graph Enrichment (V1)

**Branch**: `001-kg-enrichment`

## Prerequisites

- PostgreSQL 18 + pgvector running (Docker or local)
- `mcp/doc_server/.env` configured with DB credentials
- `uv sync` run from repo root
- Artifacts present: `artifacts/generated_docs/`, `artifacts/code_graph.json`, `artifacts/code_graph.gml`, `artifacts/capability_defs.json`, `artifacts/capability_graph.json`

## Build

```bash
cd mcp/doc_server && uv run python -m build_script.build_mcp_db
```

Build pipeline additions (this feature):
1. Carries `doc_state` from generated_docs `state` field → `entities.doc_state`
2. Computes `notes_length`, `is_contract_seed`, `rationale_specificity` at entity load time
3. Explodes `usages` dicts into `entity_usages` table (~24,803 rows)
4. Generates embeddings for usage descriptions via FastEmbed
5. Creates tsvector search column on `entity_usages` for keyword search

## Test

```bash
cd mcp/doc_server && uv run pytest tests/ -v
```

New/modified test files:
- `tests/test_entity_tools.py` — enhanced `get_entity` with new fields + `include_usages`
- `tests/test_search_tool.py` — `source="usages"` search mode
- `tests/test_explain_interface.py` — new `explain_interface` tool
- `tests/conftest.py` — new `sample_entity_usages` fixture, updated `sample_entities` with new columns

## Run

```bash
cd mcp/doc_server && uv run python -m server.server
```

## Key Files Modified

### Build Pipeline
- `mcp/doc_server/build_mcp_db.py` — entity enrichment + usages table population
- `mcp/doc_server/build_helpers/entity_processor.py` — compute derived fields

### Schema
- `mcp/doc_server/server/db_models.py` — new columns on Entity, new EntityUsage model

### Tools
- `mcp/doc_server/server/tools/entity.py` — `include_usages` parameter, new response fields
- `mcp/doc_server/server/tools/search.py` — `source="usages"` mode
- `mcp/doc_server/server/tools/explain.py` — new `explain_interface` tool

### Models
- `mcp/doc_server/server/models.py` — new response models

### Server Registration
- `mcp/doc_server/server/server.py` — import new tool modules

## Verification Checklist

- [ ] `uv run python -m build_script.build_mcp_db` completes without error
- [ ] `entity_usages` table has ~24,803 rows
- [ ] `entities` table has `doc_state` populated for all 5,295 documented entities
- [ ] `uv run pytest tests/ -v` passes
- [ ] `explain_interface` returns 5-part contract for a well-documented entity
- [ ] `search` with `source="usages"` returns grouped results
