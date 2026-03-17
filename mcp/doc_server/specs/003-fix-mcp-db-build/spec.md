# Feature Specification: Fix MCP Database Build Script

**Feature Branch**: `003-fix-mcp-db-build`  
**Created**: 2026-03-14  
**Status**: Draft  
**Input**: User description: "Fix build_mcp_db.py: missing indexes, bridge detection, capability function_count, and capability_edges"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Database Indexes Created Successfully (Priority: P1) 🎯 MVP

After running `build_mcp_db.py`, all 14 intended secondary database indexes must exist on the `entities`, `edges`, and `capability_edges` tables. Currently only 5 primary key indexes exist; the 14 additional indexes defined in the build script silently fail during creation because `SQLModel.metadata.create_all()` runs on a separate engine instance, leaving the original session in an inconsistent transaction state for subsequent index DDL.

**Why this priority**: Without indexes, every query performs full table scans. This breaks the < 100ms entity lookup and < 500ms search performance targets from the original spec.

**Independent Test**: Run `build_mcp_db.py` then query `pg_indexes WHERE schemaname = 'public'`. Verify at least 19 indexes exist (5 PKs + 14 secondary).

**Acceptance Scenarios**:

1. **Given** a freshly built database, **When** querying `pg_indexes`, **Then** all 14 secondary indexes exist alongside the 5 primary key indexes (19 total)
2. **Given** the build script encounters a duplicate index, **When** index creation runs, **Then** the existing index is retained and no error is raised
3. **Given** the build script runs, **When** the GIN index on `search_vector` is created, **Then** full-text search queries use the index (verified via EXPLAIN)

**Root Cause**: `drop_and_create_schema()` creates a second engine via `build_engine(config)` for `SQLModel.metadata.create_all()`, which commits tables on that engine. The original `session` parameter's transaction state becomes stale. When index DDL runs on the original session, errors are caught and silently swallowed by the `try/except` block.

---

### User Story 2 - Entity-to-Capability Mapping Populated (Priority: P1) 🎯 MVP

Each entity must be assigned its correct capability group name. Currently all 5,305 entities have `capability = NULL` because the code relies on `doc.system` (from `doc_db.json`), which is `None` for all 5,293 documents. The capability mapping must instead be derived from `capability_graph.json` → `capabilities[cap_name].members[].name`, which contains 848 entity-to-capability assignments.

**Why this priority**: Capability assignment is a prerequisite for bridge detection (Story 3), capability function_count (Story 4), capability-filtered search, and behavioral analysis. Without it, the entire capability system is non-functional.

**Independent Test**: Run `build_mcp_db.py` then query `SELECT COUNT(*) FROM entities WHERE capability IS NOT NULL`. Must be approximately 848.

**Acceptance Scenarios**:

1. **Given** a built database, **When** querying entities with non-null capability, **Then** approximately 848 entities have their capability set
2. **Given** a function named `do_kill` in `combat` capability members, **When** querying, **Then** `do_kill` has `capability = 'combat'`
3. **Given** an entity not in any capability's members list, **When** querying, **Then** `capability IS NULL`

**Root Cause**: `MergedEntity.capability` returns `self.doc.system`, but `Document.system` is `None` for all docs. The actual mapping lives in `capability_graph.json` under `capabilities[name].members` — a list of `{name, brief, min_depth}` dicts — but is never loaded or used during entity processing.

---

### User Story 3 - Bridge Functions Detected (Priority: P2)

Functions whose callers and callees span different capability groups must have `is_bridge = true`. Currently 0 entities are flagged because capability assignment was broken (Story 2). Once capabilities are populated, the existing `compute_bridge_flags` logic should produce non-zero results.

**Why this priority**: Bridge detection depends on Story 2. Once capabilities are assigned, architectural analysis tools can identify cross-cutting functions. This is a follow-on benefit that requires no additional logic changes — just correct input data.

**Independent Test**: Run `build_mcp_db.py` then query `SELECT COUNT(*) FROM entities WHERE is_bridge = true`. Must be > 0.

**Acceptance Scenarios**:

1. **Given** a built database with capabilities populated, **When** querying bridge entities, **Then** at least 10 entities have `is_bridge = true`
2. **Given** a function called by entities in one capability and calling entities in a different capability, **When** checking `is_bridge`, **Then** it is `true`
3. **Given** a function whose callers and callees are all in the same capability, **When** checking `is_bridge`, **Then** it is `false`

**Root Cause**: `compute_bridge_flags` skips entities with `capability = None` (`if not entity_cap: continue`). Since all entities had null capabilities, every entity was skipped.

---

### User Story 4 - Capability Function Counts and Descriptions Correct (Priority: P2)

Each capability record must have correct `function_count` and `description`. Currently all have `function_count = 0` and `description = ""` because:
- `function_count` reads `cap_def.get("functions", [])` but `capability_defs.json` has no `"functions"` key
- `description` reads `cap_def.get("description", "")` but the actual key is `"desc"`

The fixes must source `function_count` from `capability_graph.json` → `capabilities[name].function_count` (or `len(members)`) and `description` from `capability_defs.json` → `"desc"`.

**Why this priority**: Showing `function_count = 0` and empty descriptions for all 30 capabilities breaks trust in the data and makes the capability listing tool useless.

**Independent Test**: Run `build_mcp_db.py` then query `SELECT name, function_count, description FROM capabilities`. Verify counts match source data and descriptions are non-empty.

**Acceptance Scenarios**:

1. **Given** a built database, **When** querying capabilities, **Then** every capability has `function_count > 0`
2. **Given** the `combat` capability, **When** querying its description, **Then** it matches the `desc` field from `capability_defs.json` (non-empty)
3. **Given** capability_defs.json and capability_graph.json, **When** building, **Then** `doc_quality_dist` is computed from actual entity doc_quality counts per capability (not all zeros)

**Root Cause**: Field name mismatch between code expectations and actual artifact JSON keys. Code assumes `"functions"` and `"description"` keys; actual data has neither — function lists are in `capability_graph.json` and descriptions use key `"desc"`.

---

### User Story 5 - Capability Edges Populated (Priority: P2)

The `capability_edges` table must contain inter-capability dependency records. Currently 0 rows exist because the code reads `cap_graph.get("edges", [])` but the actual key in `capability_graph.json` is `"dependencies"`. The data is a nested dict (`source_cap → target_cap → {edge_type, call_count, in_dag}`) not a flat list of edge objects.

**Why this priority**: Capability edges enable architectural navigation (which capabilities depend on which others). Without them, capability detail and comparison tools return empty dependency data.

**Independent Test**: Run `build_mcp_db.py` then query `SELECT COUNT(*) FROM capability_edges`. Must be 200.

**Acceptance Scenarios**:

1. **Given** a built database, **When** querying `capability_edges`, **Then** exactly 200 rows exist
2. **Given** the dependency `admin → arg_parsing` with `edge_type = "uses_utility"`, **When** querying, **Then** this edge exists with correct `call_count` and `in_dag` values
3. **Given** all capability edges, **When** checking foreign keys, **Then** every `source_cap` and `target_cap` exists in the `capabilities` table

**Root Cause**: Code looks for `cap_graph["edges"]` (flat list format) but actual data uses `cap_graph["dependencies"]` (nested dict: `{source: {target: {edge_type, call_count, in_dag}}}`).

---

### Edge Cases

- **Entity name appears in multiple capability member lists**: First match wins; log a warning for duplicates
- **Member name uses qualified format** (e.g., `Logging::bug`): Match against entity name field which contains the same qualified name
- **capability_graph.json member references entity not in entity database**: Skip silently (entity may have been filtered during graph construction)
- **Dependency edge references a capability not in capability_defs.json**: Skip edge and log warning
- **Index creation fails due to insufficient data for HNSW**: Log warning and continue; server operates without vector index (slower but functional)
- **Transaction rollback during index creation**: Use `IF NOT EXISTS` to prevent cascading failures

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Build script MUST create all 14 secondary indexes using the same engine/connection that created the tables, not a separate engine instance
- **FR-002**: Build script MUST assign capability group names to entities by building a name-to-capability mapping from `capability_graph.json` → `capabilities[name].members[].name`
- **FR-003**: Build script MUST compute `is_bridge` flags after entity capabilities are assigned (existing logic, correct input data)
- **FR-004**: Build script MUST read capability descriptions from the `"desc"` key in `capability_defs.json`
- **FR-005**: Build script MUST compute `function_count` using `capability_graph.json` → `capabilities[name].function_count` or `len(members)`
- **FR-006**: Build script MUST parse capability edges from `capability_graph.json` → `"dependencies"` (nested dict: `source → target → {edge_type, call_count, in_dag}`)
- **FR-007**: Build script MUST compute `doc_quality_dist` for each capability by aggregating doc_quality from entities in that capability group
- **FR-008**: Build script MUST use `CREATE INDEX IF NOT EXISTS` or equivalent for idempotent re-runs

### Key Entities

- **Entity**: Code entity with `capability` field mapping to a capability group name
- **Capability**: Group definition with correct `function_count`, `description`, and `doc_quality_dist`
- **CapabilityEdge**: Cross-capability dependency with `edge_type`, `call_count`, and `in_dag`

## Assumptions

- The `capability_graph.json` member names (e.g., `Logging::bug`, `do_kill`) match entity names in the entity database exactly
- The `doc.system` field will remain unused for now; capability assignment is fully driven by `capability_graph.json`
- The existing `compute_bridge_flags` logic is correct once given non-null capability data — no algorithmic changes needed
- The existing `compute_side_effect_markers` logic is unaffected by these changes

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: After a full build, at least 19 database indexes exist (5 PKs + 14 secondary) — verifiable via `pg_indexes`
- **SC-002**: After a full build, approximately 848 entities have `capability IS NOT NULL`
- **SC-003**: After a full build, at least 10 entities have `is_bridge = true`
- **SC-004**: After a full build, every capability has `function_count > 0`
- **SC-005**: After a full build, `capability_edges` contains exactly 200 rows
- **SC-006**: After a full build, every capability has a non-empty `description`
- **SC-007**: Full build completes in under 60 seconds (baseline ~20-30s should not regress significantly)
