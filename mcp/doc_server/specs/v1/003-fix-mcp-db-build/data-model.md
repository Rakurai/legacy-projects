# Data Model: Fix MCP Database Build Script

**Feature**: 003-fix-mcp-db-build
**Phase**: 1 (Design & Contracts)
**Date**: 2026-03-14

## Overview

This is a bugfix feature — no new database tables or columns are introduced. The database schema defined in `server/db_models.py` is unchanged. This document specifies the **artifact data contracts** (the actual JSON formats in the source artifacts) that the build script must correctly read, and the **derived field computation** rules that were broken.

---

## 1. Artifact Data Contracts (Read-Only Inputs)

### 1.1 capability_defs.json

```json
{
  "<capability_name>": {
    "type": "domain | policy | projection | infrastructure | utility",
    "desc": "Human-readable description of the capability",
    "stability": "stable | evolving | experimental",
    "avoid": ["list", "of", "entity", "names"],  // optional
    "migration_role": "...",
    "target_surfaces": "...",
    "locked": true | false
  }
}
```

**Key corrections**:
- Description field: `"desc"` (NOT `"description"`)
- No `"functions"` key exists in this file
- No `"name"` key exists (capability name is the dict key)

### 1.2 capability_graph.json

```json
{
  "metadata": { ... },
  "capabilities": {
    "<capability_name>": {
      "type": "domain | ...",
      "description": "...",
      "stability": "...",
      "migration_role": "...",
      "target_surfaces": "...",
      "wave": 1,
      "entry_points_using": [ ... ],
      "function_count": 89,
      "locked_count": 5,
      "members": [
        {
          "name": "function_name",
          "brief": "One-line summary or null",
          "min_depth": 1
        }
      ]
    }
  },
  "dependencies": {
    "<source_cap>": {
      "<target_cap>": {
        "edge_type": "uses_utility | requires_core | requires_policy | ...",
        "call_count": 3,
        "in_dag": false
      }
    }
  },
  "waves": [ ... ],
  "entry_points": { ... },
  "uncategorized_callees": { ... }
}
```

**Key corrections**:
- Function-to-capability mapping: `capabilities[name].members[].name`
- Function count: `capabilities[name].function_count`
- Dependency edges: `dependencies` (NOT `edges`), nested dict (NOT flat list)
- Edge type key: `"edge_type"` (NOT `"type"`)

### 1.3 Unchanged Artifacts

These artifacts are correctly read by the current code:
- `code_graph.json` — entity database (via doxygen_parse)
- `code_graph.gml` — dependency graph (via doxygen_graph)
- `doc_db.json` — documentation database (via doc_db)
- `embeddings_cache.pkl` — embeddings (via pickle)

---

## 2. Derived Field Computation Rules

### 2.1 Entity.capability (BROKEN → FIXED)

**Before**: `MergedEntity.capability` returns `self.doc.system` → always `None`

**After**: Build a name→capability dict from `capability_graph.json`:
```python
name_to_cap: dict[str, str] = {}
for cap_name, cap_data in cap_graph["capabilities"].items():
    for member in cap_data["members"]:
        name_to_cap[member["name"]] = cap_name
```
Assign to each entity via `merged._capability = name_to_cap.get(merged.entity.name)`.

**Cardinality**: ~848 entities receive a capability assignment out of ~5,305 total.

### 2.2 Entity.is_bridge (BROKEN → FIXED by 2.1)

**Before**: `compute_bridge_flags()` skips all entities because `entity_cap` is always `None`.

**After**: No code change. Once `capability` is populated per 2.1, the existing logic works:
- Build caller/callee adjacency from CALLS edges
- For each entity with a capability, collect neighbor capabilities
- Flag as bridge if both callers and callees include external capabilities

**Expected outcome**: At least 10 bridge entities detected.

### 2.3 Capability.function_count (BROKEN → FIXED)

**Before**: `len(cap_def.get("functions", []))` → always 0 (no `"functions"` key)

**After**: `cap_graph["capabilities"][cap_name]["function_count"]`

### 2.4 Capability.description (BROKEN → FIXED)

**Before**: `cap_def.get("description", "")` → always `""` (key is `"desc"`)

**After**: `cap_def.get("desc", "")`

### 2.5 Capability.doc_quality_dist (BROKEN → FIXED)

**Before**: Hard-coded `{"high": 0, "medium": 0, "low": 0}`

**After**: Aggregate from entities:
```python
for merged in merged_entities:
    if merged.capability == cap_name:
        dist[merged.doc_quality] += 1
```

### 2.6 CapabilityEdge population (BROKEN → FIXED)

**Before**: Iterates `cap_graph.get("edges", [])` → empty list (key doesn't exist)

**After**: Iterates `cap_graph.get("dependencies", {})` as nested dict:
```python
for source_cap, targets in cap_graph.get("dependencies", {}).items():
    for target_cap, edge_data in targets.items():
        CapabilityEdge(
            source_cap=source_cap,
            target_cap=target_cap,
            edge_type=edge_data["edge_type"],
            call_count=edge_data["call_count"],
            in_dag=edge_data.get("in_dag", False),
        )
```

**Expected rows**: 200 capability edges.

---

## 3. Database Schema (UNCHANGED)

No modifications to `server/db_models.py`. All 5 tables remain as-is:
- `entities` — 31 columns, PK on `entity_id`
- `edges` — 3 columns, composite PK `(source_id, target_id, relationship)`
- `capabilities` — 6 columns, PK on `name`
- `capability_edges` — 5 columns, composite PK `(source_cap, target_cap)`
- `entry_points` — 4 columns, PK on `entity_id`

### 3.1 Index Specification (14 secondary indexes)

These indexes are defined in the build script and must be created successfully:

| Index Name | Table | Type | Definition |
|------------|-------|------|------------|
| `idx_entities_signature` | entities | B-tree | `(signature)` |
| `idx_entities_name` | entities | B-tree | `(name)` |
| `idx_entities_kind` | entities | B-tree | `(kind)` |
| `idx_entities_file` | entities | B-tree | `(file_path)` |
| `idx_entities_capability` | entities | B-tree | `(capability)` |
| `idx_entities_entry` | entities | Partial B-tree | `(is_entry_point) WHERE is_entry_point` |
| `idx_entities_bridge` | entities | Partial B-tree | `(is_bridge) WHERE is_bridge` |
| `idx_entities_search` | entities | GIN | `(search_vector)` |
| `idx_entities_embedding` | entities | HNSW | `(embedding vector_cosine_ops)` |
| `idx_edges_source` | edges | B-tree | `(source_id)` |
| `idx_edges_target` | edges | B-tree | `(target_id)` |
| `idx_edges_rel` | edges | B-tree | `(relationship)` |
| `idx_cap_edges_source` | capability_edges | B-tree | `(source_cap)` |
| `idx_cap_edges_target` | capability_edges | B-tree | `(target_cap)` |

---

## 4. State Transitions

### Build Pipeline Data Flow (corrected)

```
Stage 1: Validate artifacts
Stage 2: Load entities (code_graph.json) + docs (doc_db.json)
Stage 3: Merge entities ↔ docs
Stage 4: Extract source code from disk
Stage 5: Load capability graph → build name→cap mapping  [NEW ORDER]
Stage 6: Assign capabilities to merged entities            [NEW]
Stage 7: Load graph edges, compute fan metrics, bridge flags, side effects
Stage 8: Compute doc_quality, is_entry_point, tsvector text
Stage 9: Load embeddings, attach to entities
Stage 10: Drop/recreate schema (tables + indexes via same engine)
Stage 11: Populate entities, edges, capabilities, capability_edges, entry_points
Stage 12: ANALYZE tables
```

**Key change**: Capability assignment (Stages 5-6) must happen BEFORE bridge detection (Stage 7), which is before database population. The capability_graph is loaded earlier in the pipeline.
