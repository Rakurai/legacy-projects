# Data Model: MCP Documentation Server

<!-- Canonical V1 data model. Incorporates changes from 003-fix-mcp-db-build, 004-local-fastembed-provider, 005-mcp-key-issue, 006-legacy-common-integration, 007-data-completeness, and 008-dead-code-api-cleanup. -->
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
    entity_id       TEXT PRIMARY KEY,          -- Deterministic content-hashed ID: {prefix}:{sha256(canonical_key)[:7]}
                                               -- Prefix: fn (function/define), var (variable), cls (class/struct), file (file), sym (other)
                                               -- Canonical key: signature_map tuple (compound_id, signature_or_name)
                                               -- Stable across rebuilds from same artifacts. See spec 005.
    -- <!-- spec 005: compound_id and member_id columns removed; identity is now the deterministic entity_id -->

    -- Identity (user-facing)
    name            TEXT NOT NULL,             -- Bare name: "do_look", "race_type"
    signature       TEXT NOT NULL,             -- Full signature: "void do_look(Character *ch, String argument)" (NOT unique — 521 signatures collide across compounds)
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
    -- <!-- spec 005: doc_state and doc_quality columns removed -->

    -- Classification
    capability      TEXT,                      -- Capability group name (NULL if ungrouped)
    is_entry_point  BOOLEAN DEFAULT FALSE,

    -- Precomputed metrics (from build script)
    fan_in          INTEGER DEFAULT 0,         -- Incoming CALLS edges
    fan_out         INTEGER DEFAULT 0,         -- Outgoing CALLS edges
    is_bridge       BOOLEAN DEFAULT FALSE,     -- Callers/callees span different capabilities
    -- <!-- spec 008: side_effect_markers JSONB column removed -->

    -- Embedding
    embedding       vector(N),                 -- pgvector column; N = EMBEDDING_DIMENSION env var (default 768 for BAAI/bge-base-en-v1.5)
                                               -- <!-- spec 004: was hardcoded vector(4096); now configurable -->

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
-- Note: HNSW index may be used instead of ivfflat depending on data size
```

**Derived Fields Computation (Build Script):**
<!-- spec 003: capability assignment from cap_graph members, not doc.system -->
- `capability`: Assigned from `capability_graph.json` → `capabilities[name].members[].name` mapping (~848 of ~5,305 entities receive a capability). Not from `doc.system` (which is always null).
- <!-- spec 005: doc_quality derivation removed; doc_quality and doc_state columns dropped from schema -->
- `fan_in`: COUNT(edges WHERE target_id = entity_id AND edge_type = 'CALLS')
- `fan_out`: COUNT(edges WHERE source_id = entity_id AND edge_type = 'CALLS')
- `is_bridge`: EXISTS(edge e1 JOIN edge e2 WHERE e1.source_cap != e2.target_cap AND e1.entity = e2.entity). Requires capability assignment to be completed first (pipeline ordering). <!-- spec 003: depends on capability assignment -->
- `is_entry_point`: name LIKE 'do_%' OR name LIKE 'spell_%' OR name LIKE 'spec_%'
- <!-- spec 008: side_effect_markers derivation removed (curated function list was unvalidated) -->

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

<!-- spec 003: description sourced from cap_defs "desc" key; function_count from cap_graph; doc_quality_dist aggregated from entity data -->

```sql
CREATE TABLE capabilities (
    name TEXT PRIMARY KEY,                     -- e.g., "combat", "magic", "persistence"
    type TEXT NOT NULL,                        -- domain, policy, projection, infrastructure, utility
    description TEXT NOT NULL,                 -- sourced from capability_defs.json "desc" key
    function_count INTEGER NOT NULL,           -- sourced from capability_graph.json capabilities[name].function_count
    stability TEXT                             -- stable, evolving, experimental (if defined)
    -- <!-- spec 005: doc_quality_dist column removed -->
);
```

### 1.4 Capability Edges Table

Typed dependencies between capability groups.

```sql
CREATE TABLE capability_edges (
    source_cap TEXT NOT NULL,                  -- FK to capabilities(name)
    target_cap TEXT NOT NULL,                  -- FK to capabilities(name)
    edge_type TEXT NOT NULL,                   -- uses_utility, requires_core, requires_policy, requires_projection, requires_infrastructure
                                               -- <!-- spec 003: key in source artifact is "edge_type", parsed from nested dict dependencies[source][target] -->
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
    entity_id: str = Field(primary_key=True)  # <!-- spec 005: deterministic {prefix}:{7hex} format; compound_id and member_id removed -->

    # Identity (user-facing)
    name: str
    signature: str  # NOT unique — 521 signatures collide across compounds (e.g. variables named "level" in different files)
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
    params: dict | None = Field(default=None, sa_column=Column(JSONB(none_as_null=True)))  # <!-- spec 007: none_as_null=True; build normalizes {} → NULL -->
    returns: str | None = None
    notes: str | None = None
    rationale: str | None = None
    usages: dict | None = Field(default=None, sa_column=Column(JSONB))
    # <!-- spec 005: doc_state and doc_quality fields removed -->

    # Classification
    capability: str | None = None
    is_entry_point: bool = False

    # Metrics
    fan_in: int = 0
    fan_out: int = 0
    is_bridge: bool = False
    # <!-- spec 008: side_effect_markers field removed -->

    # Embedding + search
    # <!-- spec 004: dimension is configurable via EMBEDDING_DIMENSION env var, default 768 -->
    embedding: list[float] | None = Field(default=None, sa_column=Column(Vector(_EMBEDDING_DIM)))
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
    # <!-- spec 005: doc_quality_dist field removed -->


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

> **Note**: JSONB columns use `sa_column=Column(JSONB)` for proper PostgreSQL dialect. `Vector(_EMBEDDING_DIM)` comes from `pgvector.sqlalchemy`, where `_EMBEDDING_DIM = int(os.environ.get("EMBEDDING_DIMENSION", "768"))` is read at module import time. <!-- spec 004: was Vector(4096) --> `TSVECTOR` from `sqlalchemy.dialects.postgresql`. Indexes are created via `CREATE INDEX IF NOT EXISTS` statements during schema initialization (see build script), not in the ORM model, because some indexes require PostgreSQL-specific syntax (GIN, HNSW/ivfflat). <!-- spec 003: IF NOT EXISTS for idempotent index creation -->

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
    entity_id: str = Field(description="Deterministic entity ID ({prefix}:{7hex})")  # <!-- spec 005: deterministic format -->
    signature: str = Field(description="Full human-readable signature (C++ function sig or name)")
    name: str = Field(description="Bare name")
    kind: Literal["function", "variable", "class", "struct", "file", "enum", "define", "typedef", "namespace", "dir", "group"]
    file_path: str | None = Field(None, description="Source file path")
    capability: str | None = Field(None, description="Capability group")
    brief: str | None = Field(None, description="One-line summary")
    # <!-- spec 005: doc_state and doc_quality fields removed from EntitySummary -->
    fan_in: int = Field(ge=0, description="Incoming CALLS edges")
    fan_out: int = Field(ge=0, description="Outgoing CALLS edges")
```

### 3.2 EntityDetail

Full entity record (returned by `get_entity`).

```python
class EntityDetail(BaseModel):
    """Complete entity documentation and metadata."""
    # Identity
    entity_id: str  # <!-- spec 005: deterministic {prefix}:{7hex}; compound_id and member_id removed -->
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
    source_text: str | None  # Optional (include_code=true), BUT auto-included for enum and group kinds (flag values visible without explicit request)

    # Capability & metrics
    capability: str | None
    # <!-- spec 005: doc_state and doc_quality removed from EntityDetail -->
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

    # <!-- spec 008: side_effect_markers field removed from EntityDetail -->

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

<!-- spec 005: ResolutionEnvelope removed from all tool responses. Resolution logic is internal to search; tools accept only entity_id. -->

### 3.4 SearchResult

Discriminated union for search results (V1: entity only; V2: entity + subsystem docs).

```python
class SearchResult(BaseModel):
    """Search result with discriminated type."""
    result_type: Literal["entity", "subsystem_doc"]  # V2: subsystem_doc not used in V1
    score: float = Field(ge=0, le=1, description="Normalized combined score")
    search_mode: Literal["hybrid", "semantic_only", "keyword_fallback"] = Field(description="Which search mode was used")
    # <!-- spec 008: provenance field removed -->
    entity_summary: EntitySummary | SubsystemDocSummary | dict  # EntitySummary in V1; V2 adds SubsystemDocSummary
    # <!-- spec 005: field renamed from "summary" to "entity_summary" in implementation -->
```

### 3.5 BehaviorSlice

Result from behavior analysis (call cone computation).

```python
class BehaviorSlice(BaseModel):
    """Transitive call cone with behavioral metadata."""
    entry_point: EntitySummary  # Full summary of seed entity

    # Call structure
    direct_callees: list[EntitySummary]
    transitive_cone: list[EntitySummary]
    max_depth: int
    truncated: bool

    # Capabilities touched
    capabilities_touched: dict[str, CapabilityTouch]  # cap_name → touch metadata

    # Globals used
    globals_used: list[GlobalTouch]

    # <!-- spec 008: side_effects dict and SideEffectMarker model removed -->

class CapabilityTouch(BaseModel):
    capability: str
    direct_count: int  # Functions in this cap called directly
    transitive_count: int  # Functions in this cap in full cone
    functions: list[EntitySummary]  # Sample (truncated if >10)
    # <!-- spec 008: provenance field removed -->

class GlobalTouch(BaseModel):
    entity_id: str
    name: str
    kind: Literal["variable"]
    access_type: Literal["direct", "transitive"]
    # <!-- spec 008: provenance field removed -->

# <!-- spec 008: SideEffectMarker model removed; SideEffectCategory, Confidence, Provenance enums removed -->
```

### 3.6 Truncation Metadata

Embedded in all list-returning responses.

```python
class TruncationMetadata(BaseModel):
    """Metadata about result truncation."""
    truncated: bool
    total_available: int
    node_count: int  # Actual result count returned
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

<!-- Updated per specs 003/004/005/006: pipeline reordered for capability assignment before bridge detection; sig_map merge; embedding generation; deterministic IDs; legacy_common integration -->
```
1.  Parse code_graph.json → DoxygenEntity objects (imported from legacy_common.doxygen_parse)  <!-- spec 006: models from legacy_common -->
2.  Load documents from generated_docs/*.json → Document objects via legacy_common.doc_db.DocumentDB  <!-- spec 006: replaces doc_db.json flat file -->
3.  Compute signature map on-the-fly from EntityDatabase + DocumentDB (no longer loaded from signature_map.json)  <!-- spec 006: signature_map computed at build time -->
4.  Compute deterministic entity IDs: {prefix}:{sha256(canonical_key)[:7]} from signature_map tuples  <!-- spec 005 -->
5.  Merge entities ↔ docs using computed signature_map bridge; halt on any ID collision  <!-- spec 005 --> <!-- spec 006: sig_map is computed, not loaded -->
6.  Extract source_text from disk using (file_path, start_line, end_line); BuildError on zero extraction or invalid line ranges  <!-- spec 007: fail-fast; narrows exceptions to OSError/UnicodeDecodeError -->
7.  Load capability_graph.json → build name→capability mapping from members lists
8.  Assign capabilities to merged entities (~848 assignments)
9.  Load graph edges (translate to deterministic IDs), compute fan_in/fan_out, bridge flags (requires capabilities)  <!-- spec 005: edge ID translation --> <!-- spec 008: side_effect_markers computation removed -->
10. Compute is_entry_point  <!-- spec 005: doc_quality computation removed -->
11. Generate search_vector = setweight(to_tsvector(name), 'A') || setweight(...brief/details..., 'B') || setweight(...definition_text..., 'C') || setweight(...source_text..., 'D')
12. Load or generate embeddings:  <!-- spec 006: build_embed_text() replaced by Document.to_doxygen() --> <!-- spec 007: doc-less entities get minimal embeddings -->
    - Doc-rich entities: embed text via Document.to_doxygen() from legacy_common.doc_db
    - Doc-less entities: embed via build_minimal_embed_text() using kind + name + signature + file_path (Doxygen-formatted)
    - Entities with no name, signature, or kind: skip (null embedding)
    - If matching artifact exists (embed_cache_{model}_{dim}.pkl) → load it
    - Else if embedding provider configured → generate via provider, save artifact
    - Else → skip (null embeddings), log warning
13. Drop/recreate schema (tables + indexes via same engine, CREATE INDEX IF NOT EXISTS)
14. INSERT INTO entities (batch, ~5000 rows)
15. Parse code_graph.gml → NetworkX graph → extract edges (translate to deterministic IDs)  <!-- spec 005 -->
16. INSERT INTO edges (batch, ~25000 rows)
17. Parse capability_defs.json ("desc" key), capability_graph.json → capabilities + capability_edges (from "dependencies" nested dict, 200 rows)
18. ANALYZE entities; ANALYZE edges; (update planner statistics)
```

<!-- spec 005: step 16 (compute doc_quality_dist per capability) removed; step numbering adjusted -->

### Runtime (Server Queries)

```
1. Tool invocation (e.g., search, get_entity)  <!-- spec 005: resolve_entity removed; search is the sole entry point for text-to-ID resolution -->
2. For search: resolution pipeline (exact signature → exact name → prefix → keyword → semantic) runs internally
3. For all other tools: direct entity_id lookup (no resolution)  <!-- spec 005: tools accept only entity_id -->
4. Database query (SELECT ... WHERE ... ORDER BY score LIMIT N)
5. Map rows → Pydantic models (EntitySummary, EntityDetail, etc.)
6. Attach truncation metadata
7. Return JSON response to MCP client
```

---

## 5. Validation Rules

### Entity Identity

- `entity_id` UNIQUE (primary key), format `{prefix}:{7 hex chars}` where prefix ∈ {fn, var, cls, file, sym}  <!-- spec 005 -->
- `signature` NOT NULL (display-only, **not unique** — 521 signatures collide across compounds; not a lookup key)  <!-- spec 005: no longer accepted as lookup key -->
- <!-- spec 005: compound_id, member_id validation rules removed -->
- `kind` IN (function, variable, class, struct, file, enum, define, typedef, namespace, dir, group)
- `entity_type` IN (compound, member)

### Documentation

<!-- spec 005: doc_state and doc_quality validation rules removed -->
- `brief` max length: 200 characters
- `details` max length: 10,000 characters

### Metrics

- `fan_in >= 0`, `fan_out >= 0`
- `is_bridge` TRUE only if fan_in > 0 AND fan_out > 0 AND entity has non-null capability <!-- spec 003: bridge detection requires capability assignment -->
- `is_entry_point` TRUE only if kind = 'function'

### Embeddings

<!-- spec 004: dimension is configurable, not hardcoded -->
- `embedding` dimensions = `EMBEDDING_DIMENSION` env var (default 768, enforced by pgvector column definition)
- `embedding` can be NULL (entity has no embedding or no documentable content; semantic search excludes it)
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

# <!-- spec 005: signature-based lookup retained for search-internal resolution only;
#      no public tool accepts signature as a parameter -->

# Exact name (ranked)
async def get_by_name(session: AsyncSession, name: str, limit: int = 20) -> list[Entity]:
    result = await session.execute(
        select(Entity).where(Entity.name == name)
        .order_by(Entity.fan_in.desc())  # <!-- spec 008: doc_quality removed from ORDER BY -->
        .limit(limit)
    )
    return list(result.scalars().all())

# Prefix match
async def get_by_prefix(session: AsyncSession, prefix: str, limit: int = 20) -> list[Entity]:
    result = await session.execute(
        select(Entity).where(Entity.name.startswith(prefix))
        .order_by(func.length(Entity.name), Entity.fan_in.desc())  # <!-- spec 008: doc_quality removed from ORDER BY -->
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
- **Entity Identity**: Deterministic `{prefix}:{7hex}` IDs computed from signature_map keys; stable across rebuilds from same artifacts <!-- spec 005 -->
- **ORM Layer**: SQLModel `table=True` table definitions with SQLAlchemy async engine (asyncpg driver)
- **Query Style**: SQLModel `select()` for CRUD/filtered queries; `text()` for hybrid search CTE and pgvector/tsvector operations
- **In-memory**: NetworkX MultiDiGraph (~5300 nodes, ~25K edges) for BFS/traversal
- **API Models**: Pydantic v2 (EntitySummary, EntityDetail, SearchResult, BehaviorSlice, etc.); ResolutionEnvelope removed <!-- spec 005 -->
- **Embedding**: Configurable provider (local FastEmbed ONNX or hosted OpenAI-compatible); vector dimension configurable (default 768) <!-- Added per spec 004 -->
- **Build Script**: Offline ETL (artifact parsing → on-the-fly sig_map computation → deterministic ID generation → source extraction with fail-fast → capability assignment → metric computation → embedding load/generate with minimal-embed fallback for doc-less entities → params normalization → DB population via SQLModel session) <!-- Updated per specs 003/004/005/006/007 -->
- **Server Runtime**: Async queries (SQLModel + SQLAlchemy async session) + in-memory graph algorithms (NetworkX) + async embedding (via `to_thread` for local) <!-- Updated per spec 004 -->

All validation rules enforced at database constraints + Pydantic model validation. No runtime LLM inference; all data pre-computed.

---

## Appendix A: Artifact Data Contracts

<!-- Added per spec 003: documents the actual JSON key names and structures in source artifacts -->

These contracts define the actual JSON formats in the source artifacts that the build script must correctly read.

### capability_defs.json

```json
{
  "<capability_name>": {
    "type": "domain | policy | projection | infrastructure | utility",
    "desc": "Human-readable description",
    "stability": "stable | evolving | experimental",
    "avoid": ["..."],
    "migration_role": "...",
    "target_surfaces": "...",
    "locked": true
  }
}
```

Key notes: description is under `"desc"` (not `"description"`). No `"functions"` or `"name"` key exists.

### capability_graph.json

```json
{
  "metadata": { ... },
  "capabilities": {
    "<capability_name>": {
      "type": "...",
      "description": "...",
      "function_count": 89,
      "members": [
        {"name": "function_name", "brief": "...", "min_depth": 1}
      ],
      "entry_points_using": [ ... ]
    }
  },
  "dependencies": {
    "<source_cap>": {
      "<target_cap>": {
        "edge_type": "uses_utility | requires_core | ...",
        "call_count": 3,
        "in_dag": false
      }
    }
  }
}
```

Key notes: Entity-to-capability mapping from `capabilities[name].members[].name`. Dependency edges from `"dependencies"` nested dict (not `"edges"` flat list). Edge type key is `"edge_type"`.

### signature_map.json

~~Loaded from artifact file.~~ As of spec 006, the signature map is **computed on-the-fly** at build time from `EntityDatabase` + `DocumentDB`. The `signature_map.json` artifact is no longer required by the build pipeline. The format below documents the historical artifact for reference.

```json
{
  "<entity_id>": {
    "compound_id": "<compound_id>",
    "signature": "<signature>"
  }
}
```

Bridges entity IDs from `code_graph.json` to documentation keys in `doc_db.json`. The value is the `(compound_id, signature)` tuple that serves as the doc_db key. This file was a **derived** artifact — regenerated from `code_graph.json` + `doc_db.json` via `projects/doc_gen/build_signature_map.py`. <!-- spec 006: no longer loaded; computed on-the-fly from EntityDatabase + DocumentDB -->

<!-- spec 005: The signature_map tuple (compound_id, signature_or_name) is also the canonical key
     used to compute deterministic entity IDs: {prefix}:{sha256(str(tuple))[:7]} -->

**Regeneration lifecycle**: ~~`signature_map.json` must be regenerated any time `code_graph.json` is refreshed from new Doxygen output, because Doxygen member hashes (the `member` part of entity IDs) change across runs.~~ The signature map is now computed at build time — no separate regeneration step. The doc_db key `(compound_id, signature)` is stable because `compound_id` derives from C++ qualified names and `signature` is the entity's definition text or name. See `artifacts/artifacts.md` §4-5 for full details. <!-- spec 006: computed on-the-fly; no regeneration step needed -->

**Phantom references**: `code_graph.json` contains ~506 entity IDs in `detailed_refs` and `codeline_refs` that don't appear as entities in the `id` fields. These are `enumvalue` IDs (~479, individual enum constants) and `friend` memberdefs (~27, filtered out during parsing). They are expected and should be silently skipped when translating edge endpoints during the build.

---

## Appendix B: Embedding Provider

<!-- Added per spec 004 -->

### Configuration (ServerConfig extensions)

| Field | Type | Default | Env Var | Notes |
|---|---|---|---|---|
| `embedding_provider` | `"local" \| "hosted" \| null` | `null` | `EMBEDDING_PROVIDER` | null = keyword-only |
| `embedding_local_model` | `str` | `"BAAI/bge-base-en-v1.5"` | `EMBEDDING_LOCAL_MODEL` | Only when provider = "local" |
| `embedding_dimension` | `int` | `768` | `EMBEDDING_DIMENSION` | Must match provider output |
| `embedding_base_url` | `str \| null` | `null` | `EMBEDDING_BASE_URL` | Required when provider = "hosted" |
| `embedding_api_key` | `str \| null` | `null` | `EMBEDDING_API_KEY` | — |
| `embedding_model` | `str \| null` | `null` | `EMBEDDING_MODEL` | Required when provider = "hosted" |

Derived: `embed_cache_filename` = `embed_cache_{model_slug}_{dim}.pkl` where model_slug has `/` → `-`.

### EmbeddingProvider Protocol

```python
class EmbeddingProvider(Protocol):
    @property
    def dimension(self) -> int: ...
    async def embed_query(self, text: str) -> list[float]: ...
    async def embed_documents(self, texts: list[str]) -> list[list[float]]: ...
    def embed_query_sync(self, text: str) -> list[float]: ...
    def embed_documents_sync(self, texts: list[str]) -> list[list[float]]: ...
```

**Variants:**
- `LocalEmbeddingProvider`: Wraps `fastembed.TextEmbedding`. Async methods use `asyncio.to_thread()`.
- `HostedEmbeddingProvider`: Wraps `openai.OpenAI` (sync) and `openai.AsyncOpenAI` (async).

**Factory:** `create_provider(config) → EmbeddingProvider | None` — returns appropriate variant or None.

**Invariant:** `provider.dimension == config.embedding_dimension` (validated by factory, fails fast on mismatch).

### Embedding Artifact Lifecycle

1. Build checks if artifact exists at `{artifacts_dir}/{embed_cache_filename}`
2. If exists → load pickle and attach to entities
3. If missing and provider configured → generate via `provider.embed_documents_sync()`, save as pickle, attach
4. If missing and no provider → skip embeddings (null columns), log warning
5. Invalidation is manual — developer deletes the file
