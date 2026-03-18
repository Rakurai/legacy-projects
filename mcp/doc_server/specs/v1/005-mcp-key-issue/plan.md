# Implementation Plan: Deterministic Entity IDs & Documentation Merge Fix

**Branch**: `005-mcp-key-issue` | **Date**: 2026-03-17 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/005-mcp-key-issue/spec.md`
**Design Document**: `mcp/doc_server/specs/design.005.md`

## Summary

Replace opaque, non-deterministic Doxygen entity IDs with stable, type-prefixed content-hashed IDs (`{prefix}:{7 hex}`). Ensure `signature_map.json` is regenerated from current artifacts before each build, recovering documentation for ~5,293 entities (up from ~330). Remove `resolve_entity` tool and signature-based lookup across all tools. Drop `doc_quality`, `doc_state`, `compound_id`, `member_id` from schema and models.

## Technical Context

**Language/Version**: Python 3.14+ (lazy annotations native)
**Primary Dependencies**: FastMCP, SQLModel, AsyncPG, Pydantic v2, pgvector, FastEmbed, NetworkX
**Storage**: PostgreSQL 18 + pgvector (Docker or local); pre-computed artifacts in `artifacts/`
**Testing**: pytest + pytest-randomly via `uv run pytest` (~100 total tests, including 20 tool-level contract tests; no DB needed)
**Target Platform**: macOS/Linux development; Docker for PostgreSQL
**Project Type**: MCP server + offline build script
**Performance Goals**: Build pipeline completes in <5 min; server query latency <100ms
**Constraints**: ~5,305 entities, ~25K edges; 7-hex-char IDs (28-bit); zero collisions
**Scale/Scope**: Single codebase (~90 KLOC C++), 30 capability groups, 20 MCP tools

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| Fail-Fast, No Fallbacks | ✅ PASS | Build halts on collision; no signature fallbacks; errors propagate |
| Types Are Contracts | ✅ PASS | Pydantic v2 models updated; mypy --strict; strict entity_id typing |
| Source Reflects Current Truth | ✅ PASS | Dead fields removed (doc_quality, doc_state, compound_id, member_id); resolve_entity retired; no compatibility shims |
| uv-Only Toolchain | ✅ PASS | All execution via uv run; ruff + mypy for verification |
| Notebook Discipline | ✅ N/A | No notebook changes in this feature |

**Gate result**: PASS — no violations. Proceeding to Phase 0.

## Project Structure

### Documentation (this feature)

```text
specs/005-mcp-key-issue/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── tools.md         # Updated tool interface contracts
├── checklists/
│   └── requirements.md  # Specification quality checklist
└── tasks.md             # Phase 2 output (NOT created by /speckit.plan)
```

### Source Code (existing structure — changes in-place)

```text
mcp/doc_server/
├── build_mcp_db.py              # Build orchestrator (reorder merge steps)
├── build_helpers/
│   ├── entity_ids.py            # ADD: deterministic ID generation
│   ├── entity_processor.py      # MODIFY: merge logic, remove doc_quality
│   ├── loaders.py               # MODIFY: loader adjustments
│   ├── graph_loader.py          # MODIFY: ID translation for edges
│   ├── embeddings_loader.py     # MODIFY: keyed by new IDs
│   └── artifact_models.py       # No changes expected
├── server/
│   ├── db_models.py             # MODIFY: drop columns
│   ├── models.py                # MODIFY: drop fields from API models
│   ├── enums.py                 # MODIFY: remove DocQuality, DocState enums
│   ├── converters.py            # MODIFY: drop removed fields
│   ├── util.py                  # MODIFY: remove resolve_entity_id helper
│   ├── resolver.py              # MODIFY: retain pipeline for search use
│   ├── search.py                # MODIFY: remove min_doc_quality
│   ├── resources.py             # MODIFY: drop doc_quality_dist from resources
│   ├── prompts.py               # MODIFY: update resolve_entity references
│   └── tools/
│       ├── entity.py            # MODIFY: remove resolve_entity, signature param
│       ├── search.py            # MODIFY: remove min_doc_quality param
│       ├── graph.py             # MODIFY: remove signature param from all tools
│       ├── behavior.py          # MODIFY: remove signature param, remove DocQuality import
│       └── capability.py        # MODIFY: remove doc_quality_dist from responses; remove signature param from get_entry_point_info
└── tests/
    ├── test_entity_tools.py     # MODIFY: remove resolve_entity tests, signature tests
    ├── test_graph_tools.py      # MODIFY: update fixtures (new ID format)
    ├── test_behavior_tools.py   # MODIFY: update fixtures
    ├── test_capability_tools.py # MODIFY: remove doc_quality_dist assertions
    ├── test_search_tool.py      # MODIFY: remove min_doc_quality test
    ├── test_resolution.py       # REMOVE or gut: resolve_entity pipeline tests
    ├── test_resolver_stages.py  # MODIFY: update for search-internal resolution changes
    ├── test_search.py           # MODIFY: remove doc_quality filter test
    ├── test_converters.py       # MODIFY: remove doc_quality/doc_state tests
    ├── test_server.py           # MODIFY: update tool count (20→19)
    ├── test_load_graph.py       # REVIEW: update if Doxygen-format IDs referenced
    ├── test_graph.py            # REVIEW: update if Doxygen-format IDs referenced
    └── test_util.py             # MODIFY: remove resolve_entity_id tests
```

**Structure Decision**: All changes are within the existing `mcp/doc_server/` subtree. No new packages or top-level directories. The `entity_ids.py` module gains the deterministic ID computation function; all other changes are modifications or removals within existing files.
