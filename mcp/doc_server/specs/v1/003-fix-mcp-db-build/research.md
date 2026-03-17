# Research: Fix MCP Database Build Script

**Feature**: 003-fix-mcp-db-build
**Phase**: 0 (Outline & Research)
**Date**: 2026-03-14

## Research Tasks

### R1: Index Creation Failure Mechanism

**Question**: Why do 14 secondary indexes silently fail during `drop_and_create_schema()`?

**Finding**: The function receives a `session: AsyncSession` bound to `db_manager.engine` (Engine A). Inside the function, it creates a *second* engine via `build_engine(config)` (Engine B) and calls `SQLModel.metadata.create_all()` on Engine B. This commits the DDL (tables) on Engine B's connection. The original session (Engine A) then tries to CREATE INDEX — but the session's transaction state is stale because the tables were committed by a different connection pool. The `try/except` around each index creation swallows the resulting errors.

**Decision**: Refactor `drop_and_create_schema()` to accept the engine from `db_manager` and use it for both `create_all()` and index creation. Use `engine.begin()` for DDL (tables + indexes) in a single connection context, not the data-loading session.

**Rationale**: Using a single engine eliminates the split-transaction issue. DDL and indexes should use `engine.begin()` (autocommit DDL), while data loading uses the session.

**Alternatives considered**:
- Pass `db_manager.engine` to the function → chosen, simplest
- Create session from same engine inside function → adds complexity
- Use raw SQL for table creation → loses SQLModel schema sync benefit

---

### R2: Entity-to-Capability Mapping Source

**Question**: Where does the entity-to-capability assignment come from if `doc.system` is always None?

**Finding**: `capability_graph.json` → `capabilities` section contains 30 entries, each with a `members` list. Each member is `{"name": "function_name", "brief": "...", "min_depth": N}`. Total of 848 member entries across all capabilities. The `name` field matches entity names (e.g., `"do_kill"`, `"Logging::bug"`).

**Decision**: Build a `name → capability` dict from `capability_graph.json` during merge phase. After `merge_entities()`, iterate and assign `merged.capability` from this map. Add a `_capability_override` attribute or modify the `capability` property to check an explicit assignment first, then fall back to `doc.system`.

**Rationale**: The capability_graph.json is the authoritative source for function-to-capability mapping. The `doc.system` field was intended to hold this but was never populated by the doc generation pipeline.

**Alternatives considered**:
- Fix the doc generation pipeline to populate `doc.system` → out of scope, would require upstream changes
- Store mapping in a separate lookup table → over-engineering for a build script fix
- Add `_capability` instance variable to MergedEntity → chosen, minimal change

---

### R3: Capability Definition JSON Key Names

**Question**: What are the actual key names in `capability_defs.json`?

**Finding**: Each capability definition in `capability_defs.json` has these keys:
```
type, desc, avoid (optional), stability, migration_role, target_surfaces, locked
```

The build code reads `cap_def.get("description", "")` but the actual key is `"desc"`.
The build code reads `cap_def.get("functions", [])` but there is no functions list — function counts are in `capability_graph.json` → `capabilities[name].function_count`.

**Decision**: Fix `populate_capabilities()` to:
1. Read description from `cap_def.get("desc", "")`
2. Read function_count from `cap_graph["capabilities"][name]["function_count"]`
3. Compute `doc_quality_dist` by aggregating from entities in that capability

**Rationale**: Direct fix for field name mismatch. Using cap_graph for function_count is authoritative since it's generated from the same analysis that assigns members.

**Alternatives considered**: None — this is a straightforward key name fix.

---

### R4: Capability Graph Dependencies Structure

**Question**: What is the actual format of inter-capability dependency edges in `capability_graph.json`?

**Finding**: The code expects `cap_graph["edges"]` (flat list of `{source, target, type, call_count, in_dag}`). The actual structure is:
```json
{
  "dependencies": {
    "admin": {
      "arg_parsing": {"edge_type": "uses_utility", "call_count": 3, "in_dag": false},
      "attributes": {"edge_type": "...", "call_count": N, "in_dag": bool},
      ...
    },
    "affects": { ... },
    ...
  }
}
```
This is a nested dict: `source_cap → target_cap → {edge_type, call_count, in_dag}`. Total of 200 edges across 25 source capabilities.

**Decision**: Fix `populate_capabilities()` to iterate the nested dict:
```python
for source_cap, targets in cap_graph.get("dependencies", {}).items():
    for target_cap, edge_data in targets.items():
        # edge_data has: edge_type, call_count, in_dag
```

**Rationale**: Matches the actual artifact format. The edge data keys also differ slightly: `"edge_type"` in the data vs `"type"` in the code's assumption.

**Alternatives considered**: None — this is a straightforward format fix.

---

### R5: Bridge Detection Correctness Post-Fix

**Question**: Will the existing `compute_bridge_flags` logic produce correct results once capabilities are assigned?

**Finding**: The logic builds caller/callee adjacency from CALLS edges, collects capabilities of each neighbor, discards None and the entity's own capability, then flags as bridge if both `caller_caps` and `callee_caps` are non-empty. With 848 entities having capabilities and 9,875 CALLS edges, a significant number of cross-capability calls should exist.

The condition `caller_caps != callee_caps or len(caller_caps) > 0` is slightly redundant (if `caller_caps` is non-empty it always has `len > 0`), but the logic is correct: it detects entities called by at least one external-capability entity AND calling at least one external-capability entity. This matches the spec's definition of a bridge function.

**Decision**: No algorithmic changes needed. The bridge detection logic is correct — it just needed non-null capability input data.

**Rationale**: The logic was verified by tracing through the code with the assumption of populated capabilities. The redundant condition doesn't cause incorrect results.

**Alternatives considered**: Simplify the condition to just `if caller_caps and callee_caps:` → could be done but is cosmetic, not a bug.

---

### R6: Index Creation Best Practices with SQLAlchemy Async

**Question**: What is the proper way to create indexes with SQLAlchemy async after `create_all()`?

**Finding**: SQLAlchemy's `create_all()` can be extended with `Index` objects in the model metadata, which would be created automatically. However, the current code uses raw SQL for indexes (including GIN and HNSW which need custom syntax). The best approach is:
1. Use `engine.begin()` → `conn.run_sync(SQLModel.metadata.create_all)` for tables
2. Use the same connection or a new `engine.begin()` for index DDL
3. Use `CREATE INDEX IF NOT EXISTS` for idempotent re-runs

**Decision**: After `create_all()`, create indexes in a fresh `engine.begin()` block using `IF NOT EXISTS`. This avoids transaction state issues and is idempotent.

**Rationale**: DDL (CREATE TABLE, CREATE INDEX) in PostgreSQL auto-commits or should be in its own transaction. Using `IF NOT EXISTS` prevents failures on re-runs.

**Alternatives considered**:
- Define indexes in SQLModel metadata → doesn't support GIN/HNSW custom index types easily
- Create all in one `begin()` block → tables + indexes together works fine too

---

## Summary of All Fixes

| Issue | File | Function | Fix |
|-------|------|----------|-----|
| Missing indexes | `build_mcp_db.py` | `drop_and_create_schema()` | Use `db_manager.engine` for `create_all()` + index DDL; add `IF NOT EXISTS` |
| Null capabilities | `build_mcp_db.py` + `entity_processor.py` | `main()` + `MergedEntity` | Build name→cap dict from `cap_graph["capabilities"]`, assign after merge |
| Bridge = 0 | (cascading fix) | `compute_bridge_flags()` | No code change needed — fixed by capability assignment |
| function_count = 0 | `build_mcp_db.py` | `populate_capabilities()` | Read `cap_graph["capabilities"][name]["function_count"]` |
| description empty | `build_mcp_db.py` | `populate_capabilities()` | Read `cap_def.get("desc", "")` instead of `"description"` |
| cap_edges = 0 | `build_mcp_db.py` | `populate_capabilities()` | Parse `cap_graph["dependencies"]` nested dict instead of `"edges"` list |
| doc_quality_dist zeros | `build_mcp_db.py` | `populate_capabilities()` | Aggregate doc_quality from entities per capability |
