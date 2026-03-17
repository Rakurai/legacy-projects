# Tool Contracts: MCP Documentation Server

**Feature**: 001-mcp-doc-server
**Phase**: 1 (Design & Contracts)
**Date**: 2026-03-14

## Overview

This document defines the MCP tool interface contracts for the Legacy Documentation Server. All tools follow these conventions:
- **Input**: JSON object with tool-specific parameters (Pydantic-validated)
- **Output**: JSON object with consistent response shapes (EntitySummary base, resolution envelopes, truncation metadata)
- **Errors**: MCP errors for hard failures (DB down, invalid params); successful responses with status indicators for degraded states

**Total Tools**: 20 (grouped by category)

---

## Entity Resolution & Lookup (5 tools)

### resolve_entity

Resolve entity name to ranked candidate list with match metadata.

**Parameters:**
```typescript
{
  query: string,              // Entity name or signature
  kind?: string,              // Filter by kind (function, class, etc.)
  limit?: number = 10,        // Max candidates to return (DESIGN.md §8.1)
  verbose?: boolean = false   // Include per-stage pipeline details for each candidate
}
```

**Response:**
```typescript
{
  resolution_status: "exact" | "ambiguous" | "not_found",
  resolved_from: string,
  match_type: "signature_exact" | "name_exact" | "name_prefix" | "keyword" | "semantic",
  candidates: EntitySummary[],
  truncation: TruncationMetadata
}
```

**Match Metadata (per candidate):**
- `match_score`: float (0-1)
- `match_reason`: string (why this candidate matched)

**Example:**
```bash
Input: {query: "damage", kind: "function"}
Output: {
  resolution_status: "ambiguous",
  resolved_from: "damage",
  match_type: "name_exact",
  candidates: [
    {entity_id: "fight_8cc_1a...", signature: "void damage(Character *ch, ...)", name: "damage", kind: "function", ...},
    {entity_id: "magic_8cc_2b...", signature: "int damage(Spell *sp)", name: "damage", kind: "function", ...}
  ],
  truncation: {truncated: false, total_available: 2, node_count: 2}
}
```

---

### get_entity

Fetch full entity details by entity_id or signature (exact match required).

**Parameters:**
```typescript
{
  entity_id?: string,         // Internal ID (from resolve_entity)
  signature?: string,         // Or full signature (fallback to resolution if ambiguous)
  include_code?: boolean = false,      // Include source_text field
  include_neighbors?: boolean = false  // Include direct graph neighbors
}
```

**Response:**
```typescript
{
  entity: EntityDetail,
  resolution?: ResolutionEnvelope  // Present if signature was used
}
```

**Example:**
```bash
Input: {entity_id: "fight_8cc_1a2b3c...", include_code: true}
Output: {
  entity: {
    entity_id: "fight_8cc_1a2b3c...",
    signature: "void damage(Character *ch, Character *victim, int dam)",
    name: "damage",
    kind: "function",
    file_path: "src/fight.cc",
    body_start_line: 142,
    body_end_line: 203,
    definition_text: "void damage(Character *ch, Character *victim, int dam)",
    source_text: "void damage(Character *ch, ...) {\n  ...\n}",
    capability: "combat",
    doc_quality: "high",
    brief: "Apply damage to a character, handling death, corpse creation, and position updates.",
    details: "...",
    params: {"ch": "Attacker", "victim": "Target", "dam": "Damage amount"},
    returns: null,
    ...
  }
}
```

---

### get_source_code

Retrieve source code for an entity with optional context lines.

**Parameters:**
```typescript
{
  entity_id?: string,
  signature?: string,         // Resolve if needed
  context_lines?: number = 0  // Lines of context before/after body
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
  context_after?: string,
  resolution?: ResolutionEnvelope
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
  doc_quality_distribution: Record<string, number>, // {high: 25, medium: 15, low: 2}
  top_entities_by_fan_in: EntitySummary[],          // Top 10
  include_graph: string[],                          // Files this file includes
  included_by_graph: string[]                       // Files that include this file
}
```

---

---

## Search (1 tool)

### search

Hybrid semantic + keyword search with exact match boost.

**Parameters:**
```typescript
{
  query: string,              // Natural language query
  top_k?: number = 10,        // Number of results (DESIGN.md §8.2)
  kind?: string,              // Filter by kind
  capability?: string,        // Filter by capability
  min_doc_quality?: "high" | "medium" | "low",
  source?: "entity" = "entity" // V2: support "subsystem_doc" (unused in V1)
}
```

**Response:**
```typescript
{
  search_mode: "hybrid" | "semantic_only" | "keyword_fallback",  // Includes semantic_only per DESIGN.md §4.5
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
  provenance: "doxygen_extracted" | "llm_generated" | "subsystem_narrative",  // Doc source provenance (DESIGN.md §4.5)
  summary: EntitySummary  // V1 always EntitySummary; V2 may be SubsystemDocSummary
}
```

---

## Graph Exploration (6 tools)

### get_callers

Get functions that call this entity (reverse CALLS edges).

**Parameters:**
```typescript
{
  entity_id?: string,
  signature?: string,
  depth?: number = 1,         // 1-3 (transitive levels)
  limit?: number = 50
}
```

**Response:**
```typescript
{
  entity_id: string,
  signature: string,
  callers_by_depth: Record<number, EntitySummary[]>,  // {1: [...], 2: [...]}
  truncation: TruncationMetadata,
  resolution?: ResolutionEnvelope
}
```

---

### get_callees

Get functions this entity calls (forward CALLS edges).

**Parameters:**
```typescript
{
  entity_id?: string,
  signature?: string,
  depth?: number = 1,
  limit?: number = 50
}
```

**Response:**
```typescript
{
  entity_id: string,
  signature: string,
  callees_by_depth: Record<number, EntitySummary[]>,
  truncation: TruncationMetadata,
  resolution?: ResolutionEnvelope
}
```

---

### get_dependencies

Get entities this entity depends on (filtered by relationship type and direction).

**Parameters:**
```typescript
{
  entity_id?: string,
  signature?: string,
  relationship?: "calls" | "uses" | "inherits" | "includes" | "contained_by",  // NULL = all
  direction?: "incoming" | "outgoing" | "both" = "outgoing",
  limit?: number = 50
}
```

**Response:**
```typescript
{
  entity_id: string,
  signature: string,
  dependencies: Array<{
    entity: EntitySummary,
    relationship: string,
    direction: "incoming" | "outgoing"
  }>,
  truncation: TruncationMetadata,
  resolution?: ResolutionEnvelope
}
```

---

### get_class_hierarchy

Get inheritance tree (base classes and derived classes).

**Parameters:**
```typescript
{
  entity_id?: string,
  signature?: string,
  direction?: "ancestors" | "descendants" | "both" = "both",
  limit?: number = 50
}
```

**Response:**
```typescript
{
  entity_id: string,
  signature: string,
  base_classes: EntitySummary[],     // Parents
  derived_classes: EntitySummary[],  // Children
  truncation: TruncationMetadata,
  resolution?: ResolutionEnvelope
}
```

---

### get_related_entities

Get all direct neighbors grouped by relationship type.

**Parameters:**
```typescript
{
  entity_id?: string,
  signature?: string,
  limit_per_type?: number = 20
}
```

**Response:**
```typescript
{
  entity_id: string,
  signature: string,
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
  relationship?: "includes" | "included_by" | "co_dependent",  // NULL = all (matches DESIGN.md §8.3)
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

Compute transitive call cone with capabilities touched, globals used, side effects.

**Parameters:**
```typescript
{
  entity_id?: string,
  signature?: string,
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
  confidence: string,         // Overall confidence based on doc_quality distribution in cone
  resolution?: ResolutionEnvelope
}
```

---

### get_state_touches

Analyze which global variables an entity uses (direct and transitive).

**Parameters:**
```typescript
{
  entity_id?: string,
  signature?: string
  // Note: transitive reach is fixed at 2 hops (CALLS → USES) per DESIGN.md §8.4
}
```

**Response:**
```typescript
{
  entity_id: string,
  signature: string,
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
  }>,
  resolution?: ResolutionEnvelope
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
  limit?: number = 20   // DESIGN.md §8.4 default
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
    stability: string,
    doc_quality_dist: Record<string, number>
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
  doc_quality_dist: Record<string, number>,
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

Analyze which capabilities an entry point exercises.

**Parameters:**
```typescript
{
  entity_id?: string,
  signature?: string
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
  }>,
  resolution?: ResolutionEnvelope
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
- `resolution_status: "not_found"` — Entity not found (includes nearest matches)
- `resolution_status: "ambiguous"` — Multiple candidates (top one used, candidates list provided)
- `search_mode: "keyword_fallback"` — Embedding service unavailable
- `truncated: true` — Result set truncated (total_available > node_count)

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
