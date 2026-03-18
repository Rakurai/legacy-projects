# Resource Contracts: MCP Documentation Server

<!-- Canonical V1 resource contracts. Updated per spec 004: legacy://stats embedding field reflects provider system. Updated per spec 005: doc_quality_dist removed from capability responses; entity_id format updated. -->
**Feature**: 001-mcp-doc-server
**Phase**: 1 (Design & Contracts)
**Date**: 2026-03-14

## Overview

MCP resources provide read-only access to documentation artifacts via URIs. All resources return JSON (text/plain MIME type) and support standard MCP resource patterns (list, get by URI).

**URI Scheme**: `legacy://` (custom scheme for Legacy MUD Documentation Server)

**Total Resources**: 5 resource types

---

## 1. Capabilities Resource

### URI: `legacy://capabilities`

**Description**: List all capability groups with metadata.

**Response:**
```json
{
  "uri": "legacy://capabilities",
  "mimeType": "application/json",
  "text": "{\"capabilities\": [{\"name\": \"combat\", \"type\": \"domain\", ...}, ...]}"
}
```

**Response Schema:**
```typescript
{
  capabilities: Array<{
    name: string,
    type: "domain" | "policy" | "projection" | "infrastructure" | "utility",
    description: string,
    function_count: number,
    stability: string
    // <!-- spec 005: doc_quality_dist removed -->
  }>
}
```

**Example:**
```bash
URI: legacy://capabilities
Response: {
  "capabilities": [
    {
      "name": "combat",
      "type": "domain",
      "description": "Combat mechanics including damage, death, corpses, and positioning",
      "function_count": 127,
      "stability": "stable"
    },
    ...
  ]
}
```

---

## 2. Capability Detail Resource

### URI: `legacy://capability/{name}`

**Description**: Get detailed information for a specific capability group.

**Parameters:**
- `{name}`: Capability name (e.g., `combat`, `magic`, `persistence`)

**Response Schema:**
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
    edge_type: string,
    call_count: number
  }>,
  entry_points: Array<{
    entity_id: string,
    signature: string,
    name: string
  }>,
  sample_functions: EntitySummary[]  // Top 10 by fan_in
}
```

**Example:**
```bash
URI: legacy://capability/combat
Response: {
  "name": "combat",
  "type": "domain",
  "description": "Combat mechanics...",
  "dependencies": [
    {"target_capability": "character_state", "edge_type": "requires_core", "call_count": 342},
    {"target_capability": "output", "edge_type": "requires_projection", "call_count": 156}
  ],
  "entry_points": [
    {"entity_id": "fn:x1y2z3w", "signature": "void do_kill(...)", "name": "do_kill"},  <!-- spec 005: deterministic entity_id -->
    ...
  ],
  "sample_functions": [...]
}
```

---

## 3. Entity Resource

### URI: `legacy://entity/{entity_id}`

**Description**: Get full entity details by internal entity_id.

**Parameters:**
- `{entity_id}`: Deterministic entity ID (e.g., `fn:a1b2c3d`) <!-- spec 005: deterministic format replaces Doxygen-format IDs -->

**Response Schema:**
```typescript
EntityDetail  // Full entity record (see data-model.md)
```

**Example:**
```bash
URI: legacy://entity/fn:a1b2c3d
Response: {
  "entity_id": "fn:a1b2c3d",
  "signature": "void damage(Character *ch, Character *victim, int dam)",
  "name": "damage",
  "kind": "function",
  "file_path": "src/fight.cc",
  "brief": "Apply damage to a character...",
  "details": "...",
  ...
}
```

---

## 4. File Entities Resource

### URI: `legacy://file/{path}`

**Description**: List all entities defined in a source file.

**Parameters:**
- `{path}`: Relative file path (e.g., `src/fight.cc`)
  - URL-encoded (e.g., `src%2Ffight.cc`)

**Response Schema:**
```typescript
{
  file_path: string,
  entity_count: number,
  entities: EntitySummary[]
}
```

**Example:**
```bash
URI: legacy://file/src%2Ffight.cc
Response: {
  "file_path": "src/fight.cc",
  "entity_count": 42,
  "entities": [
    {"entity_id": "fn:a1b2c3d", "signature": "void damage(...)", "name": "damage", "kind": "function", ...},
    {"entity_id": "fn:e4f5a6b", "signature": "void update_pos(...)", "name": "update_pos", "kind": "function", ...},
    ...
  ]
}
```

---

## 5. Server Statistics Resource

### URI: `legacy://stats`

**Description**: Get aggregate server statistics (entity counts, graph size, capability counts).

**Response Schema:**
```typescript
{
  entity_stats: {
    total_entities: number,
    entities_by_kind: Record<string, number>,
    // <!-- spec 005: entities_by_doc_quality removed -->
    entities_with_embeddings: number
  },
  graph_stats: {
    total_nodes: number,
    total_edges: number,
    edges_by_type: Record<string, number>
  },
  capability_stats: {
    total_capabilities: number,
    capabilities_by_type: Record<string, number>,
    total_entry_points: number
  },
  server_info: {
    version: string,
    embedding_provider: "local" | "hosted" | null,  // Active provider mode (null = keyword-only)
    embedding_available: boolean                       // Whether embedding-based search is operational
    database_connection_status: "connected" | "degraded"
  }
}
```

**Example:**
```bash
URI: legacy://stats
Response: {
  "entity_stats": {
    "total_entities": 5305,
    "entities_by_kind": {"function": 2365, "variable": 2369, "class": 56, ...},
    <!-- spec 005: entities_by_doc_quality removed -->
    "entities_with_embeddings": 5293
  },
  "graph_stats": {
    "total_nodes": 5300,
    "total_edges": 25142,
    "edges_by_type": {"CALLS": 18456, "USES": 4231, "INHERITS": 127, ...}
  },
  "capability_stats": {
    "total_capabilities": 30,
    "capabilities_by_type": {"domain": 12, "policy": 5, "projection": 8, "infrastructure": 3, "utility": 2},
    "total_entry_points": 633
  },
  "server_info": {
    "version": "1.0.0",
    "embedding_provider": "local",
    "embedding_available": true,
    "database_connection_status": "connected"
  }
}
```

---

## Resource Discovery

### List Resources

MCP clients can list all available resources via the standard `resources/list` method.

**Response:**
```json
{
  "resources": [
    {"uri": "legacy://capabilities", "name": "Capability Groups", "description": "List all capability groups", "mimeType": "application/json"},
    {"uri": "legacy://capability/{name}", "name": "Capability Detail", "description": "Get detailed capability information", "mimeType": "application/json"},
    {"uri": "legacy://entity/{entity_id}", "name": "Entity Detail", "description": "Get full entity documentation", "mimeType": "application/json"},
    {"uri": "legacy://file/{path}", "name": "File Entities", "description": "List entities in a file", "mimeType": "application/json"},
    {"uri": "legacy://stats", "name": "Server Statistics", "description": "Get aggregate server stats", "mimeType": "application/json"}
  ]
}
```

---

## Error Handling

**Not Found (404-equivalent):**
```json
{
  "error": {
    "code": -32002,
    "message": "Resource not found",
    "data": {"uri": "legacy://capability/nonexistent"}
  }
}
```

**Invalid URI Format:**
```json
{
  "error": {
    "code": -32602,
    "message": "Invalid URI format",
    "data": {"uri": "legacy://entity/", "reason": "entity_id required"}
  }
}
```

**Database Error:**
```json
{
  "error": {
    "code": -32603,
    "message": "Internal error: database query failed",
    "data": {"uri": "legacy://entity/abc123"}
  }
}
```

---

## Caching Considerations

All resources are **read-only** and **deterministic** (database contents don't change at runtime). MCP clients can safely cache resource responses for the duration of a session.

**Cache Invalidation**: Only required when database is rebuilt (offline, before server restart).

---

## URI Encoding

- **File paths**: URL-encode slashes and special characters
  - `src/fight.cc` → `legacy://file/src%2Ffight.cc`
- **Entity IDs**: Use as-is (type prefix + colon + hex)
  - `fn:a1b2c3d` → `legacy://entity/fn:a1b2c3d`  <!-- spec 005: deterministic format -->
- **Capability names**: Use as-is (lowercase, underscores)
  - `character_state` → `legacy://capability/character_state`

---

## Resource vs. Tool Trade-offs

**Use Resources When:**
- Data is static/read-only
- Direct URI access is valuable (bookmarkable, cacheable)
- No complex filtering or parameters needed

**Use Tools When:**
- Complex query parameters required
- Resolution/disambiguation logic needed
- Result aggregation or computation required

**Example**: `legacy://entity/{entity_id}` is a resource (static lookup). Search via `search` tool discovers entity IDs. <!-- spec 005: resolve_entity retired; search is the discovery tool -->
