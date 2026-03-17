# Implementation Plan: Fix MCP Database Build Script

**Branch**: `003-fix-mcp-db-build` | **Date**: 2026-03-14 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/003-fix-mcp-db-build/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

Fix 4 bugs in the MCP documentation server's offline build script (`build_mcp_db.py`) that prevent correct database population: (1) secondary indexes silently fail due to a split-engine transaction issue, (2) entity-to-capability mapping is null because the code reads from an empty `doc.system` field instead of `capability_graph.json`, (3) capability function_count and description use wrong JSON keys, and (4) capability_edges are empty because the code reads a non-existent `"edges"` key instead of the actual `"dependencies"` nested dict. All fixes are confined to the build pipeline (`build_mcp_db.py`, `build_helpers/loaders.py`, `build_helpers/entity_processor.py`); no changes to the MCP server runtime or database schema.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: SQLModel + SQLAlchemy[asyncio] (ORM, async engine), asyncpg (PostgreSQL driver), pgvector (vector column type), loguru (logging). Build reuses parsers from `.ai/gen_docs/clustering/` (doxygen_parse, doc_db, doxygen_graph).
**Storage**: PostgreSQL 17 + pgvector extension (existing database, schema unchanged)
**Testing**: Manual validation via `test_database.py` (row counts, index checks, sample queries). Run with `uv run python test_database.py`.
**Target Platform**: macOS/Linux developer workstations
**Project Type**: Offline ETL build script (bugfix, no new features)
**Performance Goals**: Build completes in < 60 seconds (~20-30s current baseline)
**Constraints**: Schema (`server/db_models.py`) is unchanged. All fixes are in build pipeline only.
**Scale/Scope**: 5,305 entities, ~34,800 edges, 30 capabilities, 200 capability dependency edges, 848 entity-capability assignments

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

The Legacy MUD Server Constitution (v1.0.0) applies to the **MUD source code in `src/`**, not this MCP documentation server which lives in `.ai/mcp/doc_server/`. This is a separate Python project serving the documentation layer. The constitution's principles are noted here for context but do not create gates for this feature.

### Informational Review (Not Blocking)

**I. Documentation-First** — ✅ Aligned
- This is a bugfix to documentation infrastructure itself
- Root causes documented in spec with diagnostic evidence

**II. Backward Compatibility** — ✅ Not Applicable
- No changes to MUD source, player data, area files, or save formats
- Database schema (db_models.py) is unchanged; only build pipeline data flow is fixed

**III. Pragmatic Testing** — ✅ Aligned
- Validation via `test_database.py` (row counts, index existence, sample queries, data quality checks)
- Success criteria are all verifiable via SQL queries post-build

**IV. Performance & Stability** — ✅ Aligned
- Build time target: < 60 seconds (current ~20-30s baseline)
- Fixes enable query indexes that are *required* for runtime performance targets

**V. Incremental Modernization** — ✅ Not Applicable
- Greenfield Python project; bugfix to existing code, no refactoring

### Gate Result: ✅ **PASS** (No violations; constitution not binding for this feature)

---

### Post-Design Re-check (Phase 1 Complete)

**Gate Status**: ✅ **PASS** (No new violations)

**Design Review**:
- **Documentation**: All planning artifacts generated (research.md, data-model.md, quickstart.md)
- **Backward Compatibility**: No schema changes; only build pipeline data flow fixes
- **Testing Strategy**: Validation via `test_database.py` with SQL-verifiable success criteria
- **Performance**: Build-time only changes; index creation *improves* query performance
- **Complexity**: Pure bugfixes — field name corrections, data source changes, transaction fix. No new abstractions.

**No violations introduced during design phase.** Ready for implementation (Phase 2: Task Generation via `/speckit.tasks`).

## Project Structure

### Documentation (this feature)

```text
specs/003-fix-mcp-db-build/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── tasks.md             # Phase 2 output (NOT created by /speckit.plan)
```

### Source Code (files to modify)

```text
.ai/mcp/doc_server/
├── build_mcp_db.py              # Fix: index creation engine, capability population, capability edges parsing
├── build_helpers/
│   ├── loaders.py               # Fix: docstring for load_capability_graph (wrong format documented)
│   └── entity_processor.py      # Fix: add capability assignment from cap_graph, remove reliance on doc.system
└── test_database.py             # Optional: enhance assertions for new success criteria
```

**Structure Decision**: No new files. All changes are targeted fixes to existing build pipeline files. The schema (`server/db_models.py`) and server runtime code are untouched.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

*No violations — constitution not applicable to this MCP server project.*
