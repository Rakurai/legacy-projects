# Tool Contracts: MCP Documentation Server

<!-- Canonical V1 tool contracts. Updated per spec 005: resolve_entity removed; signature param removed from all tools; ResolutionEnvelope removed; doc_quality fields removed; min_doc_quality param removed from search. -->
**Feature**: 001-mcp-doc-server
**Phase**: 1 (Design & Contracts)
**Date**: 2026-03-14

## Overview

This document defines the MCP tool interface contracts for the Legacy Documentation Server. All tools follow these conventions:
- **Input**: JSON object with tool-specific parameters (Pydantic-validated)
- **Output**: JSON object with consistent response shapes (EntitySummary base, resolution envelopes, truncation metadata)
- **Errors**: MCP errors for hard failures (DB down, invalid params); successful responses with status indicators for degraded states

**Total Tools**: 19 (grouped by category) <!-- spec 005: was 20; resolve_entity removed -->

---

## Entity Lookup (4 tools) <!-- spec 005: was 5; resolve_entity removed -->

<!-- spec 005: resolve_entity tool REMOVED. search is the sole path from text to entity IDs.
     The multi-stage resolution pipeline (name_exact → prefix → keyword → semantic) is preserved
     internally as the implementation of search. -->

### get_entity

Fetch full entity details by entity_id. <!-- spec 005: signature param removed; entity_id is required -->

**Parameters:**
```typescript
{
  entity_id: string,                           // Deterministic ID ({prefix}:{7hex})
  include_code?: boolean = false,              // Include source_text field
  include_neighbors?: boolean = false          // Include direct graph neighbors
}
```

**Response:**
```typescript
EntityDetail  // <!-- spec 005: ResolutionEnvelope removed -->
```

**Example:**
```bash
Input: {entity_id: "fn:a1b2c3d", include_code: true}
Output: {
  entity_id: "fn:a1b2c3d",
  signature: "void damage(Character *ch, Character *victim, int dam)",
  name: "damage",
  kind: "function",
  file_path: "src/fight.cc",
  body_start_line: 142,
  body_end_line: 203,
  definition_text: "void damage(Character *ch, Character *victim, int dam)",
  source_text: "void damage(Character *ch, ...) {\n  ...\n}",
  capability: "combat",
  brief: "Apply damage to a character, handling death, corpse creation, and position updates.",
  details: "...",
  params: {"ch": "Attacker", "victim": "Target", "dam": "Damage amount"},
  returns: null,
  ...
}
```

---

### get_source_code

Retrieve source code for an entity with optional context lines. <!-- spec 005: entity_id only -->

**Parameters:**
```typescript
{
  entity_id: string,                   // Deterministic ID
  context_lines?: number = 0           // Lines of context before/after body
}
```

**Response:**
```typescript
{
  entity_id: string,
  signature: string,
  file_path: string,
  start_line: number,
  end_line: number,
  source_text: string,        // From database (build-time extraction)
  context_before?: string,    // If context_lines > 0, read from disk
  context_after?: string
}
```

---

### list_file_entities

List all entities defined in a source file.

**Parameters:**
```typescript
{
  file_path: string,          // Relative path (e.g., "src/fight.cc")
  kind?: string               // Filter by kind
}
```

**Response:**
```typescript
{
  file_path: string,
  entities: EntitySummary[],
  truncation: TruncationMetadata
}
```

---

### get_file_summary

Get aggregate file-level statistics.

**Parameters:**
```typescript
{
  file_path: string
}
```

**Response:**
```typescript
{
  file_path: string,
  entity_count_by_kind: Record<string, number>,     // {function: 42, variable: 18, ...}
  capability_distribution: Record<string, number>,  // {combat: 30, utility: 12, ...}
  // <!-- spec 005: doc_quality_distribution removed -->
  top_entities_by_fan_in: EntitySummary[],          // Top 10
  include_graph: string[],                          // Files this file includes
  included_by_graph: string[]                       // Files that include this file
}
```

---

---

## Search (1 tool)

### search

Hybrid semantic + keyword search with exact match boost. <!-- spec 005: sole path from text to entity IDs -->

**Parameters:**
```typescript
{
  query: string,              // Natural language query
  top_k?: number = 10,        // Number of results
  kind?: string,              // Filter by kind
  capability?: string,        // Filter by capability
  // <!-- spec 005: min_doc_quality parameter removed -->
  source?: "entity" = "entity" // V2: support "subsystem_doc" (unused in V1)
}
```

**Response:**
```typescript
{
  search_mode: "hybrid" | "semantic_only" | "keyword_fallback",
  results: SearchResult[],
  truncation: TruncationMetadata
}
```

**Search Result:**
```typescript
{
  result_type: "entity",  // V2: "subsystem_doc"
  score: number,          // Combined score (exact * 10 + semantic * 0.6 + keyword * 0.4)
  search_mode: "hybrid" | "semantic_only" | "keyword_fallback",
  provenance: "doxygen_extracted" | "llm_generated" | "precomputed" | "subsystem_narrative",  // Doc source provenance <!-- spec 005: added "precomputed" -->
  entity_summary: EntitySummary  // <!-- spec 005: field renamed from "summary" -->
}
```

---

## Graph Exploration (6 tools)

### get_callers

Get functions that call this entity (reverse CALLS edges). <!-- spec 005: entity_id only -->

**Parameters:**
```typescript
{
  entity_id: string,                   // Deterministic ID
  depth?: number = 1,                  // 1-3 (transitive levels)
  limit?: number = 50
}
```

**Response:**
```typescript
{
  entity_id: string,
  callers_by_depth: Record<number, EntitySummary[]>,  // {1: [...], 2: [...]}
  truncation: TruncationMetadata
}
```

---

### get_callees

Get functions this entity calls (forward CALLS edges). <!-- spec 005: entity_id only -->

**Parameters:**
```typescript
{
  entity_id: string,
  depth?: number = 1,
  limit?: number = 50
}
```

**Response:**
```typescript
{
  entity_id: string,
  callees_by_depth: Record<number, EntitySummary[]>,
  truncation: TruncationMetadata
}
```

---

### get_dependencies

Get entities this entity depends on (filtered by relationship type and direction). <!-- spec 005: entity_id only -->

**Parameters:**
```typescript
{
  entity_id: string,
  relationship?: "calls" | "uses" | "inherits" | "includes" | "contained_by",  // NULL = all
  direction?: "incoming" | "outgoing" | "both" = "outgoing",
  limit?: number = 50
}
```

**Response:**
```typescript
{
  entity_id: string,
  dependencies: Array<{
    entity: EntitySummary,
    relationship: string,
    direction: "incoming" | "outgoing"
  }>,
  truncation: TruncationMetadata
}
```

---

### get_class_hierarchy

Get inheritance tree (base classes and derived classes). <!-- spec 005: entity_id only -->

**Parameters:**
```typescript
{
  entity_id: string,
  direction?: "ancestors" | "descendants" | "both" = "both",
  limit?: number = 50
}
```

**Response:**
```typescript
{
  entity_id: string,
  base_classes: EntitySummary[],     // Parents
  derived_classes: EntitySummary[],  // Children
  truncation: TruncationMetadata
}
```

---

### get_related_entities

Get all direct neighbors grouped by relationship type. <!-- spec 005: entity_id only -->

**Parameters:**
```typescript
{
  entity_id: string,
  limit_per_type?: number = 20
}
```

**Response:**
```typescript
{
  entity_id: string,
  relationships: Record<string, Array<{
    entity: EntitySummary,
    direction: "incoming" | "outgoing"
  }>>,  // {CALLS: [...], USES: [...], INHERITS: [...]}
  truncation_by_type: Record<string, TruncationMetadata>
}
```

---

### get_related_files

Get files related via INCLUDES edges, co-dependency, or shared entities.

**Parameters:**
```typescript
{
  file_path: string,
  relationship?: "includes" | "included_by" | "co_dependent",  // NULL = all
  limit?: number = 50
}
```

**Response:**
```typescript
{
  file_path: string,
  related_files: Array<{
    file_path: string,
    relationship: string,
    shared_entity_count?: number  // For "shares_entities"
  }>,
  truncation: TruncationMetadata
}
```

---

## Behavior Analysis (3 tools)

### get_behavior_slice

Compute transitive call cone with capabilities touched, globals used, side effects. <!-- spec 005: entity_id only -->

**Parameters:**
```typescript
{
  entity_id: string,                   // Deterministic ID
  max_depth?: number = 5,
  max_cone_size?: number = 200
}
```

**Response:**
```typescript
{
  seed: EntitySummary,
  direct_callees: EntitySummary[],
  transitive_cone: EntitySummary[],
  max_depth: number,
  truncated: boolean,

  capabilities_touched: Record<string, {
    capability: string,
    direct_count: number,
    transitive_count: number,
    functions: EntitySummary[]  // Sample (max 10)
  }>,

  globals_used: Array<{
    entity: EntitySummary,
    access_type: "direct" | "transitive"
  }>,

  side_effects: Record<string, Array<{  // {messaging: [...], persistence: [...], ...}
    function: EntitySummary,
    category: "messaging" | "persistence" | "state_mutation" | "scheduling",
    access_type: "direct" | "transitive",
    confidence: "direct" | "heuristic" | "transitive",
    provenance: "side_effect_marker" | "graph_transitive"
  }>>,

  fan_in: number,             // Aggregate metrics for seed
  fan_out: number,
  confidence: string          // Overall confidence based on doc distribution in cone
  // <!-- spec 005: resolution field removed -->
}
```

---

### get_state_touches

Analyze which global variables an entity uses (direct and transitive). <!-- spec 005: entity_id only -->

**Parameters:**
```typescript
{
  entity_id: string
  // Note: transitive reach is fixed at 2 hops (CALLS → USES)
}
```

**Response:**
```typescript
{
  entity_id: string,
  direct_uses: EntitySummary[],           // Globals directly used (USES edges, depth=1)
  direct_side_effects: Array<{            // Side-effect markers from own CALLS (depth=1)
    function: EntitySummary,
    category: "messaging" | "persistence" | "state_mutation" | "scheduling",
    access_type: "direct",
    provenance: "side_effect_marker"
  }>,
  transitive_uses: EntitySummary[],       // Globals reachable within 2 hops of CALLS → USES
  transitive_side_effects: Array<{        // Side-effect markers from callees at depth 2+
    function: EntitySummary,
    category: "messaging" | "persistence" | "state_mutation" | "scheduling",
    access_type: "transitive",
    provenance: "graph_transitive"
  }>
}
```

---

### get_hotspots

Find architectural hotspots ranked by metric.

**Parameters:**
```typescript
{
  metric: "fan_in" | "fan_out" | "bridge" | "underdocumented",
  kind?: string,
  capability?: string,
  limit?: number = 20
}
```

**Response:**
```typescript
{
  metric: string,
  hotspots: EntitySummary[],  // Sorted by metric descending
  truncation: TruncationMetadata
}
```

---

## Capability System (5 tools)

### list_capabilities

List all capability groups with metadata.

**Parameters:**
```typescript
{}  // No parameters
```

**Response:**
```typescript
{
  capabilities: Array<{
    name: string,
    type: "domain" | "policy" | "projection" | "infrastructure" | "utility",
    description: string,
    function_count: number,
    stability: string
    // <!-- spec 005: doc_quality_dist removed from capability responses -->
  }>
}
```

---

### get_capability_detail

Get detailed capability information including dependencies and functions.

**Parameters:**
```typescript
{
  capability: string,
  include_functions?: boolean = false  // Include full function list (may be large)
}
```

**Response:**
```typescript
{
  name: string,
  type: string,
  description: string,
  function_count: number,
  stability: string,
  // <!-- spec 005: doc_quality_dist removed -->
  dependencies: Array<{
    target_capability: string,
    edge_type: string,  // requires_core, requires_policy, uses_utility, etc.
    call_count: number
  }>,
  entry_points: EntitySummary[],       // Entry points exercising this capability
  functions?: EntitySummary[]          // Full list (if include_functions=true)
}
```

---

### compare_capabilities

Compare multiple capabilities showing shared/unique dependencies and bridges.

**Parameters:**
```typescript
{
  capabilities: string[],  // 2+ capability names
  limit?: number = 50
}
```

**Response:**
```typescript
{
  capabilities: string[],
  shared_dependencies: EntitySummary[],           // Functions called by multiple capabilities
  unique_dependencies: Record<string, EntitySummary[]>,  // {cap_name: [unique funcs]}
  bridge_entities: EntitySummary[],              // Functions connecting these capabilities
  truncation: TruncationMetadata
}
```

---

### list_entry_points

List entry points (do_*, spell_*, spec_* functions) filterable by capability.

**Parameters:**
```typescript
{
  capability?: string,
  name_pattern?: string,  // SQL LIKE pattern (e.g., "do_look%")
  limit?: number = 100
}
```

**Response:**
```typescript
{
  entry_points: EntitySummary[],
  truncation: TruncationMetadata
}
```

---

### get_entry_point_info

Analyze which capabilities an entry point exercises. <!-- spec 005: entity_id only -->

**Parameters:**
```typescript
{
  entity_id: string
}
```

**Response:**
```typescript
{
  entry_point: EntitySummary,
  capabilities_exercised: Record<string, {
    capability: string,
    direct_count: number,
    transitive_count: number
  }>
}
```

---

## Error Handling

**MCP Errors (Hard Failures):**
- Database connection failure
- Invalid parameters (type validation failure, negative depth, etc.)
- Malformed requests
- Internal server errors

**Successful Responses with Status Indicators (Degraded States):**
- `search_mode: "keyword_fallback"` — Embedding service unavailable
- `truncated: true` — Result set truncated (total_available > node_count)
<!-- spec 005: resolution_status indicators removed (resolve_entity retired) -->

**Example Error Response (MCP Error):**
```json
{
  "error": {
    "code": -32602,
    "message": "Invalid parameter: depth must be between 1 and 3",
    "data": {"parameter": "depth", "value": -1}
  }
}
```

**Example Degraded Response (Success with Indicator):**
```json
{
  "search_mode": "keyword_fallback",
  "results": [...],
  "truncation": {"truncated": false, "total_available": 5, "node_count": 5}
}
```

---

## Tool Naming Convention

- **Verb + Noun**: `get_entity`, `list_capabilities`, `compare_capabilities`
- **Plural for lists**: `list_capabilities`, `get_callers`, `list_entry_points`
- **Singular for detail**: `get_entity`, `get_capability_detail`

---

## Response Size Limits

- **EntitySummary lists**: Default 20, max 100
- **Source code**: No limit (full file if needed)
- **Call cones**: Max 200 entities (configurable)
- **Graph depth**: Max 5 for behavior analysis, max 3 for general traversal

All truncations explicitly reported via `TruncationMetadata`.
