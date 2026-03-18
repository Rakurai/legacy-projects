# Implementation Plan: Legacy Common Integration

**Branch**: `006-legacy-common-integration` | **Date**: 2026-03-18 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/006-legacy-common-integration/spec.md`

## Summary

Replace reimplemented dataclasses and loaders in `mcp/doc_server/build_helpers/` with canonical imports from `legacy_common`, switch the documentation source from flat `doc_db.json` to per-compound `generated_docs/`, compute the signature map on-the-fly, and convert `ResolutionResult` to Pydantic. This eliminates ~350 lines of duplicated code and nearly doubles documentation brief coverage.

## Technical Context

**Language/Version**: Python 3.14+ (lazy annotations native)
**Primary Dependencies**: legacy_common (workspace), Pydantic v2, NetworkX, SQLModel, FastMCP, loguru
**Storage**: PostgreSQL 18 + pgvector (build pipeline target); JSON artifacts (build pipeline source)
**Testing**: pytest + pytest-asyncio; 20 test modules in `mcp/doc_server/tests/`
**Target Platform**: macOS/Linux development (offline build pipeline + MCP server)
**Project Type**: Build pipeline (offline) + MCP server (runtime)
**Performance Goals**: None — offline build pipeline, no latency constraints
**Constraints**: Single atomic integration; intermediate states may break the pipeline
**Scale/Scope**: ~5,300 entities, ~25K edges, ~4,946 documents

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| Fail-Fast, No Fallbacks | ✅ Pass | Pipeline already uses assertions and fail-fast. No fallback logic introduced. |
| Types Are Contracts | ✅ Pass | Moving from stdlib dataclasses to Pydantic v2 BaseModel strengthens type contracts. |
| Source Reflects Current Truth | ✅ Pass | Core goal: remove duplicated code, delete stale files, eliminate pre-computed artifacts. |
| uv-Only Toolchain | ✅ Pass | All commands via uv. `legacy-common` added as workspace dependency. |
| Notebook Discipline | N/A | No notebook changes in scope. |

No violations — no Complexity Tracking entries needed.

## Project Structure

### Documentation (this feature)

```text
specs/006-legacy-common-integration/
├── plan.md              # This file
├── research.md          # Phase 0: resolved unknowns
├── data-model.md        # Phase 1: entity/model mapping
├── quickstart.md        # Phase 1: implementation quickstart
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
packages/legacy_common/legacy_common/
├── __init__.py              # REPO_ROOT, ARTIFACTS_DIR constants
├── doxygen_parse.py         # EntityID, DoxygenEntity, EntityDatabase [MODIFY: no changes needed]
├── doc_db.py                # Document, DocumentDB [MODIFY: add explicit path param to DocumentDB]
└── doxygen_graph.py         # load_graph() [MODIFY: remove unused jinja2 import]

mcp/doc_server/
├── pyproject.toml           # [MODIFY: add legacy-common dependency, remove build_helpers from packages]
├── build_script/
│   └── build_mcp_db.py      # [MODIFY: rewire imports, new loading logic, on-the-fly signature map]
├── build_helpers/
│   ├── __init__.py           # [DELETE]
│   ├── artifact_models.py    # [DELETE]
│   ├── embed_text.py         # [DELETE]
│   ├── entity_ids.py         # [KEEP: compute_entity_id(), kind_to_prefix() — not duplicated in legacy_common]
│   ├── entity_processor.py   # [MODIFY: update imports to use legacy_common types]
│   ├── embeddings_loader.py  # [MODIFY: replace build_embed_text with Document.to_doxygen()]
│   ├── graph_loader.py       # [MODIFY: replace load_gml_graph with legacy_common.load_graph]
│   └── loaders.py            # [MODIFY: rewire artifact loading, remove doc_db.json/signature_map.json validation]
├── server/
│   └── resolver.py           # [MODIFY: ResolutionResult dataclass → Pydantic BaseModel]
└── tests/
    ├── test_entity_ids.py    # [KEEP: imports from build_helpers.entity_ids, no changes needed]
    ├── test_embed_text.py    # [MODIFY or DELETE: build_embed_text() is being removed]
    └── ... (18 other test modules — no changes expected)
```

**Structure Decision**: Existing uv workspace monorepo structure. Changes span two workspace members: `packages/legacy_common` (minor modifications) and `mcp/doc_server` (primary refactoring target). No new packages or structural changes.

## Complexity Tracking

> No constitution violations to justify.
