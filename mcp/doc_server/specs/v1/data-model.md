# Data Model: MCP Documentation Server

**Feature**: 001-mcp-doc-server
**Phase**: 1 (Design & Contracts)
**Date**: 2026-03-14

## Overview

This document defines the complete data model for the MCP Documentation Server: database schema (PostgreSQL + pgvector), SQLModel table definitions (Python ORM layer), in-memory graph structure (NetworkX), and Pydantic models for API contracts. The model separates **source artifacts** (read-only inputs) from **derived database** (queryable storage) and **runtime graph** (in-memory BFS/traversal).

---

## 1. Database Schema

### 1.1 Entities Table

Primary storage for entity metadata, documentation, metrics, embeddings, and full-text search vectors.

```sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE entities (
    -- Identity (internal)
    entity_id       TEXT PRIMARY KEY,          -- Doxygen compound_member ID
    compound_id     TEXT NOT NULL,             -- Doxygen compound refid
    member_id       TEXT,                      -- Member hex hash (NULL for compounds)

    -- Identity (user-facing)
    name            TEXT NOT NULL,             -- Bare name: "do_look", "race_type"
    signature       TEXT NOT NULL UNIQUE,      -- Full signature: "void do_look(Character *ch, String argument)"
    kind            TEXT NOT NULL,             -- function, variable, class, struct, file, enum, define, typedef, namespace, dir, group
    entity_type     TEXT NOT NULL,             -- "compound" or "member"

    -- Source location
    file_path       TEXT,                      -- Relative path (e.g., "src/fight.cc")
    body_start_line INTEGER,                   -- Body start line (1-based)
    body_end_line   INTEGER,                   -- Body end line
    decl_file_path  TEXT,                      -- Declaration file path
    decl_line       INTEGER,                   -- Declaration line number

    -- Source code (extracted at build time from disk)
    definition_text TEXT,                      -- C++ definition line: "void do_look(Character *ch, String argument)"
    source_text     TEXT,                      -- Full body source code (~5 MB total for all entities)

    -- Documentation
    brief           TEXT,
    details         TEXT,
    params          JSONB,                     -- {param_name: description}
    returns         TEXT,
    notes           TEXT,
    rationale       TEXT,
    usages          JSONB,                     -- {caller_key: usage_description}
    doc_state       TEXT,                      -- extracted_summary, refined_summary, etc.
    doc_quality     TEXT,                      -- derived: high, medium, low

    -- Classification
    capability      TEXT,                      -- Capability group name (NULL if ungrouped)
    is_entry_point  BOOLEAN DEFAULT FALSE,

    -- Precomputed metrics (from build script)
    fan_in          INTEGER DEFAULT 0,         -- Incoming CALLS edges
    fan_out         INTEGER DEFAULT 0,         -- Outgoing CALLS edges
    is_bridge       BOOLEAN DEFAULT FALSE,     -- Callers/callees span different capabilities
    side_effect_markers JSONB,                 -- {messaging: [...], persistence: [...], state_mutation: [...], scheduling: [...]}

    -- Embedding
    embedding       vector(4096),              -- pgvector column (doc embedding)

    -- Full-text search
    search_vector   tsvector                   -- Weighted: name=A, brief/details=B, definition_text=C, source_text=D
);

-- Indexes
CREATE INDEX idx_entities_name ON entities(name);
CREATE INDEX idx_entities_kind ON entities(kind);
CREATE INDEX idx_entities_file ON entities(file_path);
CREATE INDEX idx_entities_capability ON entities(capability);
CREATE INDEX idx_entities_entry ON entities(is_entry_point) WHERE is_entry_point;
CREATE INDEX idx_entities_bridge ON entities(is_bridge) WHERE is_bridge;
CREATE INDEX idx_entities_search ON entities USING GIN(search_vector);
CREATE INDEX idx_entities_embedding ON entities USING ivfflat (embedding vector_cosine_ops) WITH (lists = 50);
```

**Derived Fields Computation (Build Script):**
- `doc_quality`:
  - `high`: doc_state IN (refined_summary, refined_usage) AND details IS NOT NULL AND (params IS NOT NULL OR kind != 'function')
  - `medium`: doc_state = generated_summary OR (brief IS NOT NULL AND details IS NULL)
  - `low`: doc_state = extracted_summary OR brief IS NULL
- `fan_in`: COUNT(edges WHERE target_id = entity_id AND edge_type = 'CALLS')
- `fan_out`: COUNT(edges WHERE source_id = entity_id AND edge_type = 'CALLS')
- `is_bridge`: EXISTS(edge e1 JOIN edge e2 WHERE e1.source_cap != e2.target_cap AND e1.entity = e2.entity)
- `is_entry_point`: name LIKE 'do_%' OR name LIKE 'spell_%' OR name LIKE 'spec_%'
- `side_effect_markers`: BFS from entity through CALLS edges, check callees against curated list, categorize by marker type

### 1.2 Edges Table

Dependency graph edges (subset of in-memory NetworkX graph, stored for query convenience).

```sql
CREATE TABLE edges (
    source_id       TEXT NOT NULL REFERENCES entities(entity_id),
    target_id       TEXT NOT NULL REFERENCES entities(entity_id),
    relationship    TEXT NOT NULL,             -- calls, uses, inherits, includes, contained_by
    PRIMARY KEY (source_id, target_id, relationship)
);

CREATE INDEX idx_edges_source ON edges(source_id);
CREATE INDEX idx_edges_target ON edges(target_id);
CREATE INDEX idx_edges_rel ON edges(relationship);
```

**Edge Types (from code_graph.gml):**
- `CALLS`: Function/define calls another function/define
- `USES`: Entity uses a variable, type, class, etc.
- `INHERITS`: Class/struct inheritance or function override
- `INCLUDES`: File includes another file
- `CONTAINED_BY`: Member belongs to compound (or nested class in outer class)

### 1.3 Capabilities Table

Capability group definitions (30 groups).

```sql
CREATE TABLE capabilities (
    name TEXT PRIMARY KEY,                     -- e.g., "combat", "magic", "persistence"
    type TEXT NOT NULL,                        -- domain, policy, projection, infrastructure, utility
    description TEXT NOT NULL,
    function_count INTEGER NOT NULL,
    stability TEXT,                            -- stable, evolving, experimental (if defined)
    doc_quality_dist JSONB NOT NULL            -- {high: N, medium: N, low: N}
);
```

### 1.4 Capability Edges Table

Typed dependencies between capability groups.

```sql
CREATE TABLE capability_edges (
    source_cap TEXT NOT NULL,                  -- FK to capabilities(name)
    target_cap TEXT NOT NULL,                  -- FK to capabilities(name)
    edge_type TEXT NOT NULL,                   -- requires_core, requires_policy, requires_projection, requires_infrastructure, uses_utility
    call_count INTEGER NOT NULL,               -- Number of cross-capability CALLS edges
    in_dag BOOLEAN DEFAULT FALSE,              -- Whether this edge is in the DAG overlay
    PRIMARY KEY (source_cap, target_cap)
);

-- Indexes
CREATE INDEX idx_capability_edges_source ON capability_edges(source_cap);
CREATE INDEX idx_capability_edges_target ON capability_edges(target_cap);

-- Foreign keys
ALTER TABLE capability_edges ADD CONSTRAINT fk_source_cap FOREIGN KEY (source_cap) REFERENCES capabilities(name);
ALTER TABLE capability_edges ADD CONSTRAINT fk_target_cap FOREIGN KEY (target_cap) REFERENCES capabilities(name);
```

### 1.5 Entry Points Table

```sql
CREATE TABLE entry_points (
    name            TEXT PRIMARY KEY,          -- do_kill, spell_fireball, etc.
    entity_id       TEXT REFERENCES entities(entity_id),
    capabilities    JSONB,                     -- list of capability names exercised
    entry_type      TEXT                       -- do_, spell_, spec_
);
```

### 1.6 SQLModel Table Definitions

All tables above are defined as SQLModel `table=True` classes in `server/db_models.py`. These are the authoritative Python representation; the SQL above documents the generated schema for reference.

```python
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import TSVECTOR, JSONB
from pgvector.sqlalchemy import Vector

class Entity(SQLModel, table=True):
    __tablename__ = "entities"

    # Identity (internal)
    entity_id: str = Field(primary_key=True)
    compound_id: str
    member_id: str | None = None

    # Identity (user-facing)
    name: str
    signature: str = Field(unique=True)
    kind: str
    entity_type: str

    # Source location
    file_path: str | None = None
    body_start_line: int | None = None
    body_end_line: int | None = None
    decl_file_path: str | None = None
    decl_line: int | None = None

    # Source code
    definition_text: str | None = None
    source_text: str | None = None

    # Documentation
    brief: str | None = None
    details: str | None = None
    params: dict | None = Field(default=None, sa_column=Column(JSONB))
    returns: str | None = None
    notes: str | None = None
    rationale: str | None = None
    usages: dict | None = Field(default=None, sa_column=Column(JSONB))
    doc_state: str | None = None
    doc_quality: str | None = None

    # Classification
    capability: str | None = None
    is_entry_point: bool = False

    # Metrics
    fan_in: int = 0
    fan_out: int = 0
    is_bridge: bool = False
    side_effect_markers: dict | None = Field(default=None, sa_column=Column(JSONB))

    # Embedding + search
    embedding: list[float] | None = Field(default=None, sa_column=Column(Vector(4096)))
    search_vector: str | None = Field(default=None, sa_column=Column(TSVECTOR))


class Edge(SQLModel, table=True):
    __tablename__ = "edges"

    source_id: str = Field(foreign_key="entities.entity_id", primary_key=True)
    target_id: str = Field(foreign_key="entities.entity_id", primary_key=True)
    relationship: str = Field(primary_key=True)


class Capability(SQLModel, table=True):
    __tablename__ = "capabilities"

    name: str = Field(primary_key=True)
    type: str
    description: str
    function_count: int
    stability: str | None = None
    doc_quality_dist: dict = Field(sa_column=Column(JSONB))


class CapabilityEdge(SQLModel, table=True):
    __tablename__ = "capability_edges"

    source_cap: str = Field(foreign_key="capabilities.name", primary_key=True)
    target_cap: str = Field(foreign_key="capabilities.name", primary_key=True)
    edge_type: str
    call_count: int
    in_dag: bool = False


class EntryPoint(SQLModel, table=True):
    __tablename__ = "entry_points"

    name: str = Field(primary_key=True)
    entity_id: str | None = Field(default=None, foreign_key="entities.entity_id")
    capabilities: list | None = Field(default=None, sa_column=Column(JSONB))
    entry_type: str | None = None
```

> **Note**: JSONB columns use `sa_column=Column(JSONB)` for proper PostgreSQL dialect. `Vector(4096)` comes from `pgvector.sqlalchemy`. `TSVECTOR` from `sqlalchemy.dialects.postgresql`. Indexes are created via `CREATE INDEX` statements during schema initialization (see build script), not in the ORM model, because some indexes require PostgreSQL-specific syntax (GIN, ivfflat).

---

## 2. In-Memory Graph (NetworkX)

### 2.1 Graph Structure

Constructed from the `edges` table at server startup (`SELECT source_id, target_id, relationship FROM edges`); kept in memory as `NetworkX.MultiDiGraph`. Not loaded from artifact files at runtime.

**Nodes:**
- **Entity nodes**: `entity_id` as node ID (string)
  - Attributes: `name` (str), `kind` (str), `type` ("compound" | "member")
- Note: Location nodes and `REPRESENTED_BY` edges exist only in the raw GML artifact. The runtime graph contains only entity-to-entity edges loaded from the `edges` table.

**Edges:**
- Key: `(source, target, edge_type)`
- Attributes: `type` (Relationship enum)

**Edge Types (lowercase in DB, uppercase in code constants):**
- `calls`: Function → function
- `uses`: Entity → variable/type/class
- `inherits`: Derived class → base class
- `includes`: File → file
- `contained_by`: Member → compound

**Access Patterns:**
```python
# Get all CALLS edges from entity
callees = [
    target
    for _, target, data in graph.out_edges(entity_id, data=True)
    if data.get("type") == "CALLS"
]

# Get all CALLS edges to entity
callers = [
    source
    for source, _, data in graph.in_edges(entity_id, data=True)
    if data.get("type") == "CALLS"
]

# BFS call cone (see research.md for implementation)
cone = compute_call_cone(graph, seed_id, max_depth=5, max_size=200)
```

---

## 3. Pydantic Models (API Contracts)

### 3.1 EntitySummary

Base model for all list-returning tools.

```python
from pydantic import BaseModel, Field
from typing import Literal

class EntitySummary(BaseModel):
    """Compact entity representation used in all list tools."""
    entity_id: str = Field(description="Internal Doxygen ID (for passing to get_entity)")
    signature: str = Field(description="Full human-readable signature (C++ function sig or name)")
    name: str = Field(description="Bare name")
    kind: Literal["function", "variable", "class", "struct", "file", "enum", "define", "typedef", "namespace", "dir", "group"]
    file_path: str | None = Field(None, description="Source file path")
    capability: str | None = Field(None, description="Capability group")
    brief: str | None = Field(None, description="One-line summary")
    doc_state: str = Field(description="Documentation pipeline state")
    doc_quality: Literal["high", "medium", "low"] = Field(description="Derived quality bucket")
    fan_in: int = Field(ge=0, description="Incoming CALLS edges")
    fan_out: int = Field(ge=0, description="Outgoing CALLS edges")
```

### 3.2 EntityDetail

Full entity record (returned by `get_entity`).

```python
class EntityDetail(BaseModel):
    """Complete entity documentation and metadata."""
    # Identity
    entity_id: str
    compound_id: str
    member_id: str | None
    signature: str
    name: str

    # Classification
    kind: str
    entity_type: Literal["compound", "member"]

    # Source location
    file_path: str | None
    body_start_line: int | None
    body_end_line: int | None
    decl_file_path: str | None
    decl_line: int | None
    definition_text: str | None
    source_text: str | None  # Optional (include_code=true)

    # Capability & metrics
    capability: str | None
    doc_state: str
    doc_quality: Literal["high", "medium", "low"]
    fan_in: int
    fan_out: int
    is_bridge: bool
    is_entry_point: bool

    # Documentation
    brief: str | None
    details: str | None
    params: dict[str, str] | None
    returns: str | None
    rationale: str | None
    usages: dict[str, str] | None
    notes: str | None

    # Side effects
    side_effect_markers: dict[str, list[str]] | None

    # Optional neighbors (include_neighbors=true)
    neighbors: list[EntityNeighbor] | None = None

class EntityNeighbor(BaseModel):
    entity_id: str
    name: str
    kind: str
    relationship: str  # CALLS, USES, INHERITS, etc.
    direction: Literal["incoming", "outgoing"]
```

### 3.3 Resolution Envelope

Wraps responses from tools accepting entity names.

```python
class ResolutionEnvelope(BaseModel):
    """Metadata about entity resolution."""
    resolution_status: Literal["exact", "ambiguous", "not_found"]
    resolved_from: str  # Original query string
    match_type: Literal["entity_id", "signature_exact", "name_exact", "name_prefix", "keyword", "semantic"]
    resolution_candidates: int  # Total matches found (1 for exact)
```

### 3.4 SearchResult

Discriminated union for search results (V1: entity only; V2: entity + subsystem docs).

```python
class SearchResult(BaseModel):
    """Search result with discriminated type."""
    result_type: Literal["entity", "subsystem_doc"]  # V2: subsystem_doc not used in V1
    score: float = Field(ge=0, le=1, description="Normalized combined score")
    search_mode: Literal["hybrid", "semantic_only", "keyword_fallback"] = Field(description="Which search mode was used")
    provenance: Literal["doxygen_extracted", "llm_generated", "subsystem_narrative"]  # Doc source provenance
    summary: EntitySummary | SubsystemDocSummary | dict  # EntitySummary in V1; V2 adds SubsystemDocSummary
    # In V1, result_type is always "entity" and summary is always EntitySummary
```

### 3.5 BehaviorSlice

Result from behavior analysis (call cone computation).

```python
class BehaviorSlice(BaseModel):
    """Transitive call cone with behavioral metadata."""
    entry_point: EntitySummary  # Full summary of seed entity (matches DESIGN.md §8.4)

    # Call structure
    direct_callees: list[EntitySummary]
    transitive_cone: list[EntitySummary]
    max_depth: int
    truncated: bool

    # Capabilities touched
    capabilities_touched: dict[str, CapabilityTouch]  # cap_name → touch metadata

    # Globals used
    globals_used: list[GlobalTouch]

    # Side effects (categorized)
    side_effects: dict[str, list[SideEffectMarker]]  # category → markers

class CapabilityTouch(BaseModel):
    capability: str
    direct_count: int  # Functions in this cap called directly
    transitive_count: int  # Functions in this cap in full cone
    functions: list[EntitySummary]  # Sample (truncated if >10)
    provenance: Literal["graph_calls", "graph_transitive", "capability_map"] = "capability_map"

class GlobalTouch(BaseModel):
    entity_id: str
    name: str
    kind: Literal["variable"]
    access_type: Literal["direct", "transitive"]
    provenance: Literal["graph_uses", "graph_transitive"] = "graph_uses"

class SideEffectMarker(BaseModel):
    function_id: str
    function_name: str
    category: Literal["messaging", "persistence", "state_mutation", "scheduling"]
    access_type: Literal["direct", "transitive"]
    confidence: Literal["direct", "heuristic", "transitive"]
    provenance: Literal["side_effect_marker", "graph_transitive"] = "side_effect_marker"
```

### 3.6 Truncation Metadata

Embedded in all list-returning responses.

```python
class TruncationMetadata(BaseModel):
    """Metadata about result truncation."""
    truncated: bool
    total_available: int
    node_count: int  # Actual result count returned (matches DESIGN.md §4.3)
    max_depth_requested: int | None = None
    max_depth_reached: int | None = None
    truncation_reason: Literal["depth_limit", "node_limit", "none"] | None = None
```

### 3.7 V2-Reserved Shapes

Defined now to prevent response-shape drift when V2 lands. Not used by V1 tools.

```python
class SubsystemSummary(BaseModel):
    """V2: Subsystem-level summary."""
    id: str
    name: str
    parent_id: str | None
    description: str
    source_file: str
    entity_count: int
    doc_section_count: int
    depends_on_count: int
    depended_on_by_count: int

class SubsystemDocSummary(BaseModel):
    """V2: Subsystem documentation section summary."""
    id: int
    subsystem_id: str
    subsystem_name: str
    section_path: str
    heading: str
    section_kind: str
    source_file: str
    line_range: tuple[int, int] | None
    excerpt: str

class ContextBundle(BaseModel):
    """V2: Mixed entity/system context assembly."""
    focus_type: Literal["entity", "subsystem", "capability", "entry_point"]
    focus: EntitySummary | SubsystemSummary | dict  # Primary object
    related_entities: list[EntitySummary]
    related_capabilities: list[dict]
    related_subsystems: list[SubsystemSummary]
    relevant_doc_sections: list[dict]
    confidence_notes: str | None = None
    truncated: bool = False
```

---

## 4. Entity Lifecycle

### Build Time (Offline ETL)

```
1. Parse code_graph.json → DoxygenEntity objects
2. Parse doc_db.json → Document objects
3. Merge on (compound_id, signature) → combined entity records
4. Extract source_text from disk using (file_path, start_line, end_line)
5. Compute derived metrics (doc_quality, fan_in, fan_out, is_bridge, side_effect_markers, is_entry_point)
6. Generate search_vector = setweight(to_tsvector(name), 'A') || setweight(to_tsvector(coalesce(brief, '') || ' ' || coalesce(details, '')), 'B') || setweight(to_tsvector(coalesce(definition_text, '')), 'C') || setweight(to_tsvector(coalesce(source_text, '')), 'D')
7. Load embeddings from embeddings_cache.pkl, map by member_id
8. INSERT INTO entities (batch, ~5000 rows)
9. Parse code_graph.gml → NetworkX graph → extract edges
10. INSERT INTO edges (batch, ~25000 rows)
11. Parse capability_defs.json, capability_graph.json → capabilities + capability_edges
12. ANALYZE entities; ANALYZE edges; (update planner statistics)
```

### Runtime (Server Queries)

```
1. Tool invocation (e.g., resolve_entity)
2. Resolution pipeline: exact signature → exact name → prefix → keyword → semantic
3. Database query (SELECT ... WHERE ... ORDER BY score LIMIT N)
4. Map rows → Pydantic models (EntitySummary, EntityDetail, etc.)
5. Attach resolution envelope, truncation metadata
6. Return JSON response to MCP client
```

---

## 5. Validation Rules

### Entity Identity

- `entity_id` UNIQUE (primary key)
- `signature` UNIQUE (user-facing key)
- `compound_id` NOT NULL
- `member_id` NULL only for compound entities
- `kind` IN (function, variable, class, struct, file, enum, define, typedef, namespace, dir, group)
- `entity_type` IN (compound, member)

### Documentation Quality

- `doc_state` NOT NULL, IN (extracted_summary, generated_summary, refined_summary, generated_usage, refined_usage)
- `doc_quality` NOT NULL, IN (high, medium, low)
- `doc_quality = high` → (details IS NOT NULL)
- `brief` max length: 200 characters
- `details` max length: 10,000 characters

### Metrics

- `fan_in >= 0`, `fan_out >= 0`
- `is_bridge` TRUE only if fan_in > 0 AND fan_out > 0
- `is_entry_point` TRUE only if kind = 'function'

### Embeddings

- `embedding` dimensions = 4096 (enforced by pgvector)
- `embedding` can be NULL (entity has no embedding; semantic search excludes it)
- `search_vector` NOT NULL (always generated, even for entities without docs)

### Edges

- `source_id` and `target_id` MUST reference valid entity_id
- `relationship` IN (calls, uses, inherits, includes, contained_by)
- No self-loops for CALLS edges (source_id != target_id when relationship = 'CALLS')

---

## 6. Query Patterns

> **Convention**: Simple CRUD and filtered queries use SQLModel `select()`. Complex queries (hybrid search CTE, tsvector ranking, pgvector cosine) use `session.execute(text(...))` with bound parameters.

### Entity Resolution (SQLModel `select()`)

```python
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession

# Exact signature
async def get_by_signature(session: AsyncSession, sig: str) -> Entity | None:
    result = await session.execute(select(Entity).where(Entity.signature == sig))
    return result.scalar_one_or_none()

# Exact name (ranked)
async def get_by_name(session: AsyncSession, name: str, limit: int = 20) -> list[Entity]:
    result = await session.execute(
        select(Entity).where(Entity.name == name)
        .order_by(Entity.doc_quality.desc(), Entity.fan_in.desc())
        .limit(limit)
    )
    return list(result.scalars().all())

# Prefix match
async def get_by_prefix(session: AsyncSession, prefix: str, limit: int = 20) -> list[Entity]:
    result = await session.execute(
        select(Entity).where(Entity.name.startswith(prefix))
        .order_by(func.length(Entity.name), Entity.doc_quality.desc())
        .limit(limit)
    )
    return list(result.scalars().all())
```

### Keyword & Semantic Search (raw SQL via `text()`)

```python
from sqlalchemy import text

# Keyword search
KEYWORD_QUERY = text(\"\"\"
    SELECT *, ts_rank(search_vector, plainto_tsquery(:query)) AS score
    FROM entities
    WHERE search_vector @@ plainto_tsquery(:query)
    ORDER BY score DESC
    LIMIT :limit
\"\"\")

# Semantic search
SEMANTIC_QUERY = text(\"\"\"
    SELECT *, 1 - (embedding <=> :embedding::vector) AS score
    FROM entities
    WHERE embedding IS NOT NULL
    ORDER BY score DESC
    LIMIT :limit
\"\"\")
```

### Hybrid Search (Combined — raw SQL via `text()`)

```sql
WITH semantic AS (
    SELECT entity_id, 1 - (embedding <=> $1::vector) AS score
    FROM entities
    WHERE embedding IS NOT NULL
    ORDER BY score DESC
    LIMIT 100
),
keyword AS (
    SELECT entity_id, ts_rank(search_vector, plainto_tsquery($2)) AS score
    FROM entities
    WHERE search_vector @@ plainto_tsquery($2)
    ORDER BY score DESC
    LIMIT 100
),
exact AS (
    SELECT entity_id, 1.0 AS score
    FROM entities
    WHERE signature = $3 OR name = $3
)
SELECT
    e.*,
    COALESCE(ex.score, 0) * 10 + COALESCE(s.score, 0) * 0.6 + COALESCE(k.score, 0) * 0.4 AS combined_score
FROM entities e
LEFT JOIN exact ex USING (entity_id)
LEFT JOIN semantic s USING (entity_id)
LEFT JOIN keyword k USING (entity_id)
WHERE ex.entity_id IS NOT NULL OR s.entity_id IS NOT NULL OR k.entity_id IS NOT NULL
ORDER BY combined_score DESC
LIMIT $4;
```

### Graph Traversal (SQLModel `select()` + NetworkX)

```python
# Direct callers (via SQLModel)
async def get_direct_callers(session: AsyncSession, entity_id: str, limit: int = 50) -> list[Entity]:
    result = await session.execute(
        select(Entity)
        .join(Edge, Edge.source_id == Entity.entity_id)
        .where(Edge.target_id == entity_id, Edge.relationship == "calls")
        .order_by(Entity.fan_out.desc())
        .limit(limit)
    )
    return list(result.scalars().all())

# Direct callees (via SQLModel)
async def get_direct_callees(session: AsyncSession, entity_id: str, limit: int = 50) -> list[Entity]:
    result = await session.execute(
        select(Entity)
        .join(Edge, Edge.target_id == Entity.entity_id)
        .where(Edge.source_id == entity_id, Edge.relationship == "calls")
        .order_by(Entity.fan_in.desc())
        .limit(limit)
    )
    return list(result.scalars().all())

# Transitive via NetworkX BFS (not SQL)
```

---

## Summary

- **Database**: PostgreSQL 17 + pgvector, 5 tables (entities, edges, capabilities, capability_edges, entry_points)
- **ORM Layer**: SQLModel `table=True` table definitions with SQLAlchemy async engine (asyncpg driver)
- **Query Style**: SQLModel `select()` for CRUD/filtered queries; `text()` for hybrid search CTE and pgvector/tsvector operations
- **In-memory**: NetworkX MultiDiGraph (~5300 nodes, ~25K edges) for BFS/traversal
- **API Models**: Pydantic v2 (EntitySummary, EntityDetail, SearchResult, BehaviorSlice, etc.)
- **Build Script**: Offline ETL (artifact parsing → merging → metric computation → DB population via SQLModel session)
- **Server Runtime**: Async queries (SQLModel + SQLAlchemy async session) + in-memory graph algorithms (NetworkX)

All validation rules enforced at database constraints + Pydantic model validation. No runtime LLM inference; all data pre-computed.
