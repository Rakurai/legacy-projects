# Implementation Plan: Knowledge Graph Enrichment (V1)

**Branch**: `001-kg-enrichment` | **Date**: 2026-03-19 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-kg-enrichment/spec.md`

## Summary

Enrich the MCP doc server's V1 entity model by carrying through discarded doc fields (`doc_state`, computed `notes_length`, `is_contract_seed`, `rationale_specificity`), materializing the ~24,803 `usages` dict entries into a dedicated `entity_usages` table with embeddings and full-text search, and exposing this enriched data through a new `explain_interface` tool and enhancements to existing tools (`get_entity`, `search`).

All enrichments are aggregation and indexing over existing artifacts — no new LLM inference required.

## Technical Context

**Language/Version**: Python 3.14+
**Primary Dependencies**: FastMCP, AsyncPG, SQLModel, Pydantic v2, FastEmbed, NetworkX, pgvector
**Storage**: PostgreSQL 18 + pgvector (Docker or local)
**Testing**: pytest + pytest-randomly; async contract tests with mock context (no real DB)
**Target Platform**: macOS (dev), Linux (deploy)
**Project Type**: MCP server (tool-based API for AI agents)
**Performance Goals**: Build completes in reasonable time for ~24,803 embedding generations; query latency comparable to existing tools
**Constraints**: No new LLM inference (SC-006); additive schema changes only (SC-007); full rebuild on each build (no incremental)
**Scale/Scope**: 5,305 entities, ~24,803 usage entries, 768-dim embeddings

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| **Fail-Fast, No Fallbacks** | PASS | Build pipeline fails on malformed input (FR-013). Tools return null sections for missing evidence, no fabrication. |
| **Types Are Contracts** | PASS | All new models use Pydantic v2 + SQLModel. mypy --strict on server code. New columns fully typed. |
| **Source Reflects Current Truth** | PASS | No legacy compatibility code. Existing `usages` JSONB column remains (still used by `get_entity`); `entity_usages` table is additive, not a migration bridge. |
| **uv-Only Toolchain** | PASS | All commands via `uv run`. No direct python/pip/pytest. |
| **Notebook Discipline** | N/A | No notebook changes in this feature. |

**Post-Phase 1 re-check**: All principles remain satisfied. No violations introduced by the design.

## Project Structure

### Documentation (this feature)

```text
specs/001-kg-enrichment/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Phase 0: resolved unknowns
├── data-model.md        # Phase 1: schema additions
├── quickstart.md        # Phase 1: build/test/run guide
├── contracts/
│   └── tools.md         # Phase 1: tool interface contracts
├── checklists/
│   └── requirements.md  # Spec quality checklist
└── tasks.md             # Phase 2 output (created by /speckit.tasks)
```

### Source Code (repository root)

```text
mcp/doc_server/
├── build_mcp_db.py                    # MODIFY: entity enrichment + usages population
├── build_helpers/
│   ├── entity_processor.py            # MODIFY: compute derived fields (doc_state, notes_length, etc.)
│   └── embeddings_loader.py           # MODIFY: generate usage embeddings
├── server/
│   ├── db_models.py                   # MODIFY: new Entity columns + new EntityUsage model
│   ├── models.py                      # MODIFY: new response models
│   ├── search.py                      # MODIFY: usages search path in hybrid_search
│   ├── enums.py                       # MODIFY: add SearchSource enum value
│   ├── server.py                      # MODIFY: import new tool modules
│   ├── tools/
│   │   ├── entity.py                  # MODIFY: include_usages param, new fields
│   │   ├── search.py                  # MODIFY: source="usages" routing
│   │   └── explain.py                 # NEW: explain_interface tool
│   └── converters.py                  # MODIFY: EntitySummary/Detail gains new fields
└── tests/
    ├── conftest.py                    # MODIFY: new fixtures, updated sample entities
    ├── test_entity_tools.py           # MODIFY: test new fields + include_usages
    ├── test_search_tool.py            # MODIFY: test source="usages"
    └── test_explain_interface.py      # NEW: explain_interface tests
```

**Structure Decision**: All changes are within the existing `mcp/doc_server/` project. No new packages or top-level directories. New tools follow the established pattern of one file per tool module in `server/tools/`. This is an enrichment of the existing V1 server, not a new project.

## Complexity Tracking

No constitution violations. No complexity justifications needed.
