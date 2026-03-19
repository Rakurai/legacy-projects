# Implementation Plan: Dead Code Purge & API Cleanup

**Branch**: `008-dead-code-api-cleanup` | **Date**: 2026-03-19 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/008-dead-code-api-cleanup/spec.md`

## Summary

Remove six families of dead/vestigial fields from the MCP doc server (doc_quality, doc_state, side_effect_markers, provenance, compound_id, member_id), drop four low-value tools (get_hotspots, get_related_files, get_file_summary, list_file_entities), fix entry point / capability semantics, and align tool parameters with the published contract. Pure subtraction + contract alignment — no new features.

## Technical Context

**Language/Version**: Python 3.14+ (uv workspace)
**Primary Dependencies**: FastMCP, SQLModel, Pydantic v2, AsyncPG, pgvector, NetworkX
**Storage**: PostgreSQL 18 + pgvector (Docker or local)
**Testing**: pytest + pytest-randomly; contract tests (no DB needed)
**Target Platform**: MCP server (local or remote)
**Project Type**: MCP tool server (web-service-like)
**Performance Goals**: N/A (pure subtraction, no performance change expected)
**Constraints**: All changes must be backward-compatible with existing `capability_graph.json` and `code_graph.gml` artifacts
**Scale/Scope**: ~5,300 entities, ~25K edges, 30 capabilities, 19→15 tools

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| Fail-Fast, No Fallbacks | PASS | Pure deletion — no new fallback paths introduced |
| Types Are Contracts | PASS | Removing unused typed fields; remaining types become more accurate. Pydantic v2 models slimmed. mypy --strict compliance maintained |
| Source Reflects Current Truth | PASS | This spec IS about enforcing this principle — removing dead code, dead enums, dead fields. Exactly aligned |
| uv-Only Toolchain | PASS | No changes to toolchain |
| Notebook Discipline | N/A | No notebook changes |

**Gate result**: ALL PASS — proceed to Phase 0.

## Project Structure

### Documentation (this feature)

```text
specs/008-dead-code-api-cleanup/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── tools.md         # Updated tool contracts (diff from v1)
└── tasks.md             # Phase 2 output (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
mcp/doc_server/
├── server/
│   ├── enums.py           # Remove DocState, DocQuality, SideEffectCategory, Provenance, HotspotMetric
│   ├── db_models.py       # Remove Entity.side_effect_markers, Capability.doc_quality_dist (if present)
│   ├── models.py          # Remove provenance from all models, SideEffectMarker, side_effects on BehaviorSlice
│   ├── converters.py      # Remove provenance assignments, side_effect_markers pass-through
│   ├── search.py          # Remove Provenance import, provenance= assignments
│   ├── resolver.py        # No changes needed (already uses fan_in)
│   ├── resources.py       # Remove side_effect_markers from entity resource
│   ├── util.py            # No changes expected
│   └── tools/
│       ├── behavior.py    # Remove get_hotspots, _extract_side_effects_for_entities, side-effect imports
│       ├── capability.py  # Remove capability param from list_entry_points, fix get_capability_detail EP query
│       ├── entity.py      # Remove get_file_summary, list_file_entities
│       ├── graph.py       # Remove get_related_files, add direction to get_class_hierarchy, fix defaults
│       └── search.py      # Rename limit→top_k (default 10)
├── build_helpers/
│   ├── entity_processor.py  # Remove SIDE_EFFECT_FUNCTIONS, MergedEntity.side_effect_markers
│   └── graph_loader.py      # Remove compute_side_effect_markers(), _SIDE_EFFECT_BFS_DEPTH
├── build_mcp_db.py          # Remove compute_side_effect_markers import/call, side_effect_markers= assignment
└── tests/
    ├── conftest.py            # Update fixtures
    ├── test_behavior_tools.py # Remove hotspot tests, side-effect tests
    ├── test_capability_tools.py
    ├── test_converters.py     # Remove provenance tests
    ├── test_entity_tools.py   # Remove file_summary/list_file_entities tests
    ├── test_graph_tools.py    # Remove get_related_files tests, add direction tests
    ├── test_search.py         # Update provenance assertions
    ├── test_search_units.py   # Remove _provenance_for tests
    ├── test_search_tool.py    # Rename limit→top_k in test calls
    └── test_resources.py      # Remove dead field assertions
```

**Structure Decision**: Existing monorepo structure under `mcp/doc_server/`. All changes are within this sub-project. No new files created (only deletions and modifications).

## Complexity Tracking

No constitution violations. Table intentionally left empty.
