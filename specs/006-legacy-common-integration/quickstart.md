# Quickstart: Legacy Common Integration

## Prerequisites

- uv installed and working
- PostgreSQL 18 + pgvector running (for end-to-end build validation)
- `artifacts/` directory with: `code_graph.json`, `code_graph.gml`, `capability_defs.json`, `capability_graph.json`, `generated_docs/` directory
- Working `mcp/doc_server/.env` with database credentials

## Implementation Order

Single atomic integration — all changes land together. Implementation sequence within the branch:

1. **legacy_common modifications** (unblock everything else)
   - Add `docs_dir` param to `DocumentDB`
   - Remove unused `jinja2.is_undefined` import from `doxygen_graph.py`

2. **Dependency wiring**
   - Add `legacy-common` to `mcp/doc_server/pyproject.toml` dependencies
   - Run `uv sync`

3. **Entity model swap** (Story 1)
   - Replace `artifact_models.py` entity imports with `legacy_common.doxygen_parse`
   - Update `loaders.py`, `entity_processor.py`, `build_mcp_db.py`
   - Adapt for `EntityDatabase.entities` flat access and `EntityID` key type

4. **Document model + data source swap** (Story 2)
   - Replace document imports with `legacy_common.doc_db`
   - Point `DocumentDB` at configured `generated_docs/` path
   - Replace `build_embed_text()` with `Document.to_doxygen()` in embeddings_loader
   - Delete `build_helpers/embed_text.py`
   - Delete `tests/test_embed_text.py`

5. **Graph loader swap** (Story 3)
   - Replace `load_gml_graph()` with `legacy_common.doxygen_graph.load_graph` in graph_loader

6. **Signature map computation** (Story 4)
   - Create `SignatureMap` class in appropriate location
   - Remove `signature_map.json` from validation and loading

7. **Artifact cleanup**
   - Delete `build_helpers/artifact_models.py` and `build_helpers/__init__.py`
   - Update artifact validation list (remove `doc_db.json`, `signature_map.json`)
   - Remove `build_helpers` from pyproject.toml wheel packages
   - Add `generated_docs/` to artifact validation

8. **ResolutionResult conversion** (Story 5)
   - Convert `@dataclass` → `BaseModel` in `server/resolver.py`

9. **Validation**
   - Run `uv run pytest tests/ -v` — all tests pass
   - Run `uv run ruff check .` and `uv run ruff format .`
   - Run `uv run mypy server/`
   - Full pipeline run: `uv run python -m build_script.build_mcp_db`
   - Verify entity count (~5,300), brief coverage (≥90%), entity ID determinism

## Key Technical Decisions

- `entity_ids.py` is **kept** — `compute_entity_id()` and `kind_to_prefix()` have no equivalent in legacy_common
- `build_helpers/` directory is **kept** (still has entity_ids, entity_processor, embeddings_loader, graph_loader, loaders)
- `DocumentDB` gets an explicit `docs_dir` constructor param — minimal change, backward compatible
- Entity access via `EntityDatabase.entities` property — returns flat dict of all compounds + members
- Test modification: `test_embed_text.py` deleted (tests a removed function); all other tests unchanged

## Verification Commands

```bash
cd mcp/doc_server

# Sync after dependency changes
uv sync

# Run all tests
uv run pytest tests/ -v

# Lint and format
uv run ruff check .
uv run ruff format .

# Type check
uv run mypy server/

# Full pipeline build (requires PostgreSQL)
uv run python -m build_script.build_mcp_db
```
