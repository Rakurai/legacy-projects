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
CREATE EXTENSION IF NOT EXISTS pg_trgm;

CREATE TABLE entities (
    -- Identity (internal)
    entity_id       TEXT PRIMARY KEY,          -- Deterministic content-hashed ID: {prefix}:{sha256(canonical_key)[:7]}
                                               -- Prefix: fn (function/define), var (variable), cls (class/struct), file (file), sym (other)
                                               -- Canonical key: signature_map tuple (compound_id, signature_or_name)
                                               -- Stable across rebuilds from same artifacts. See spec 005.

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

    -- Classification
    capability      TEXT,                      -- Capability group name (NULL if ungrouped)
    is_entry_point  BOOLEAN DEFAULT FALSE,

    -- Precomputed metrics (from build script)
    fan_in          INTEGER DEFAULT 0,         -- Incoming CALLS edges
    fan_out         INTEGER DEFAULT 0,         -- Outgoing CALLS edges
    is_bridge       BOOLEAN DEFAULT FALSE,     -- Callers/callees span different capabilities

    -- Qualified name
    qualified_name  TEXT,                      -- Fully-qualified C++ name from containment graph (e.g., "Logging::stc", "conn::GetSexState")
                                               -- Scoping containers: namespace, class, struct, group only (no file/dir paths)

    -- Embedding (dual views)
    doc_embedding       vector(N),             -- pgvector; N = EMBEDDING_DIMENSION env var (default 768)
                                               -- Labeled prose fields (brief, details, params, returns, notes, rationale)
    symbol_embedding    vector(N),             -- pgvector; same dimension
                                               -- Qualified scoped signature in natural C++ form

    -- Full-text search (dual views)
    doc_search_vector    tsvector,             -- Weighted: name=A, brief+details=B, notes+rationale+params+returns=C. English dictionary (stemming).
    symbol_search_vector tsvector,             -- Weighted: name=A, qualified_name+signature=B, definition_text=C. Simple dictionary (no stemming).

    -- Trigram similarity
    symbol_searchable    TEXT                  -- Lowercased, punctuation-stripped name+qualified_name+signature. For pg_trgm similarity.
);

-- Indexes
CREATE INDEX idx_entities_name ON entities(name);
CREATE INDEX idx_entities_kind ON entities(kind);
CREATE INDEX idx_entities_file ON entities(file_path);
CREATE INDEX idx_entities_capability ON entities(capability);
CREATE INDEX idx_entities_entry ON entities(is_entry_point) WHERE is_entry_point;
CREATE INDEX idx_entities_bridge ON entities(is_bridge) WHERE is_bridge;
CREATE INDEX ix_entities_doc_embedding ON entities USING hnsw (doc_embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);
CREATE INDEX ix_entities_symbol_embedding ON entities USING hnsw (symbol_embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);
CREATE INDEX ix_entities_doc_search_vector ON entities USING GIN(doc_search_vector);
CREATE INDEX ix_entities_symbol_search_vector ON entities USING GIN(symbol_search_vector);
CREATE INDEX ix_entities_symbol_searchable ON entities USING GiST(symbol_searchable gist_trgm_ops);
```

**Derived Fields Computation (Build Script):**

- `capability`: Assigned from `capability_graph.json` → `capabilities[name].members[].name` mapping (~848 of ~5,305 entities receive a capability). Not from `doc.system` (which is always null).
- `fan_in`: COUNT(edges WHERE target_id = entity_id AND edge_type = 'CALLS')
- `fan_out`: COUNT(edges WHERE source_id = entity_id AND edge_type = 'CALLS')
- `is_bridge`: EXISTS(edge e1 JOIN edge e2 WHERE e1.source_cap != e2.target_cap AND e1.entity = e2.entity). Requires capability assignment to be completed first (pipeline ordering).
- `is_entry_point`: name LIKE 'do_%' OR name LIKE 'spell_%' OR name LIKE 'spec_%'
- `qualified_name`: Derived from containment graph. Walks `CONTAINED_BY` edges upward, collecting only C++ scoping containers (namespace, class, struct, group). File and directory parents are excluded. Result: `conn::GetSexState`, not `src/include/conn::State.hh::conn::GetSexState`.
- **Entity Deduplication**: Build pipeline groups entities by `entity.id.member` (Doxygen member hash) to deduplicate declaration/definition splits. For each group, the definition fragment (where `entity.body is not None`) is selected as the survivor, and documentation from declaration fragments is merged onto it. Entities without a member hash (pure compounds) pass through unchanged. This ensures one database record per logical entity.

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
    description TEXT NOT NULL,                 -- sourced from capability_defs.json "desc" key
    function_count INTEGER NOT NULL,           -- sourced from capability_graph.json capabilities[name].function_count
    stability TEXT                             -- stable, evolving, experimental (if defined)
);
```

### 1.4 Capability Edges Table

Typed dependencies between capability groups.

```sql
CREATE TABLE capability_edges (
    source_cap TEXT NOT NULL,                  -- FK to capabilities(name)
    target_cap TEXT NOT NULL,                  -- FK to capabilities(name)
    edge_type TEXT NOT NULL,                   -- uses_utility, requires_core, requires_policy, requires_projection, requires_infrastructure

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

### 1.6 Search Config Table

Stores precomputed search calibration values produced by the build pipeline. The server loads these at startup and caches them for its lifetime.

```sql
CREATE TABLE search_config (
    key   TEXT PRIMARY KEY,                    -- Config key (e.g., 'doc_tsrank_ceiling')
    value DOUBLE PRECISION NOT NULL            -- Numeric config value
);
```

**Known keys** (populated by build pipeline, consumed by server):

| Key | Description |
|-----|-------------|
| `doc_tsrank_ceiling` | 99th percentile ts_rank for `doc_search_vector` |
| `symbol_tsrank_ceiling` | 99th percentile ts_rank for `symbol_search_vector` |

### 1.7 SQLModel Table Definitions

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
    params: dict | None = Field(default=None, sa_column=Column(JSONB(none_as_null=True)))
    returns: str | None = None
    notes: str | None = None
    rationale: str | None = None
    usages: dict | None = Field(default=None, sa_column=Column(JSONB))

    # Classification
    capability: str | None = None
    is_entry_point: bool = False

    # Metrics
    fan_in: int = 0
    fan_out: int = 0
    is_bridge: bool = False

    # Qualified name
    qualified_name: str | None = Field(
        default=None,
        description="Fully-qualified C++ name (e.g., Logging::stc, conn::GetSexState)",
    )

    # Embedding (dual views)
    doc_embedding: list[float] | None = Field(
        default=None,
        sa_column=Column(Vector(_EMBEDDING_DIM)),
        description=f"{_EMBEDDING_DIM}-dim embedding of labeled prose fields",
    )
    symbol_embedding: list[float] | None = Field(
        default=None,
        sa_column=Column(Vector(_EMBEDDING_DIM)),
        description=f"{_EMBEDDING_DIM}-dim embedding of qualified scoped signature",
    )

    # Full-text search (dual views)
    doc_search_vector: str | None = Field(
        default=None,
        sa_column=Column(TSVECTOR),
        description="Weighted tsvector: name=A, brief+details=B, notes+rationale+params+returns=C (english)",
    )
    symbol_search_vector: str | None = Field(
        default=None,
        sa_column=Column(TSVECTOR),
        description="Weighted tsvector: name=A, qualified_name+signature=B, definition_text=C (simple)",
    )

    # Trigram similarity
    symbol_searchable: str | None = Field(
        default=None,
        description="Lowercased punctuation-stripped name+qualified_name+signature for pg_trgm",
    )


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


class SearchConfig(SQLModel, table=True):
    __tablename__ = "search_config"

    key: str = Field(primary_key=True, description="Config key (e.g., 'doc_tsrank_ceiling')")
    value: float = Field(description="Numeric config value")
```

> **Note**: JSONB columns use `sa_column=Column(JSONB)` for proper PostgreSQL dialect. `Vector(_EMBEDDING_DIM)` comes from `pgvector.sqlalchemy`, where `_EMBEDDING_DIM = int(os.environ.get("EMBEDDING_DIMENSION", "768"))` is read at module import time. `TSVECTOR` from `sqlalchemy.dialects.postgresql`. Indexes are created via `CREATE INDEX IF NOT EXISTS` statements during schema initialization (see build script), not in the ORM model, because some indexes require PostgreSQL-specific syntax (GIN, HNSW, GiST). The `pg_trgm` extension is created alongside `vector` during schema setup.

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
    entity_id: str = Field(description="Deterministic entity ID ({prefix}:{7hex})")
    signature: str = Field(description="Full human-readable signature (C++ function sig or name)")
    name: str = Field(description="Bare name")
    kind: Literal["function", "variable", "class", "struct", "file", "enum", "define", "typedef", "namespace", "dir", "group"]
    file_path: str | None = Field(None, description="Source file path")
    capability: str | None = Field(None, description="Capability group")
    brief: str | None = Field(None, description="One-line summary")

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



### 3.4 SearchResult

Result from multi-view search pipeline. Each result carries metadata about which view won.

```python
class SearchResult(BaseModel):
    """Search result with multi-view ranking metadata."""
    result_type: Literal["entity", "subsystem_doc"]  # V2: subsystem_doc not used in V1
    score: float = Field(description="Cross-encoder score from winning view; raw logit, may be negative")

    entity_summary: EntitySummary | SubsystemDocSummary | dict  # EntitySummary in V1; V2 adds SubsystemDocSummary

    # Multi-view ranking metadata
    winning_view: str = Field(description='"symbol" or "doc" — the view that produced the higher cross-encoder score')
    winning_score: float = Field(description="Cross-encoder score from winning view")
    losing_score: float = Field(description="Cross-encoder score from losing view")
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


class CapabilityTouch(BaseModel):
    capability: str
    direct_count: int  # Functions in this cap called directly
    transitive_count: int  # Functions in this cap in full cone
    functions: list[EntitySummary]  # Sample (truncated if >10)


class GlobalTouch(BaseModel):
    entity_id: str
    name: str
    kind: Literal["variable"]
    access_type: Literal["direct", "transitive"]
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

```
1.  Parse code_graph.json → DoxygenEntity objects (imported from legacy_common.doxygen_parse)
2.  Load documents from generated_docs/*.json → Document objects via legacy_common.doc_db.DocumentDB
3.  Compute signature map on-the-fly from EntityDatabase + DocumentDB (no longer loaded from signature_map.json)
4.  Compute deterministic entity IDs: {prefix}:{sha256(canonical_key)[:7]} from signature_map tuples
5.  Merge entities ↔ docs using computed signature_map bridge; halt on any ID collision
6.  Extract source_text from disk using (file_path, start_line, end_line); BuildError on zero extraction or invalid line ranges
7.  Load capability_graph.json → build name→capability mapping from members lists
8.  Assign capabilities to merged entities (~848 assignments)
9.  Load graph edges (translate to deterministic IDs), compute fan_in/fan_out, bridge flags (requires capabilities)
10. Compute is_entry_point
11. Derive qualified_name from containment graph — walks CONTAINED_BY edges upward,
    using only C++ scoping containers (namespace, class, struct, group); excludes file/dir parents
12. Build doc_search_vector (english dictionary):
    setweight(to_tsvector('english', name), 'A') ||
    setweight(to_tsvector('english', brief || details), 'B') ||
    setweight(to_tsvector('english', notes || rationale || params || returns), 'C')
13. Build symbol_search_vector (simple dictionary):
    setweight(to_tsvector('simple', name), 'A') ||
    setweight(to_tsvector('simple', qualified_name || signature), 'B') ||
    setweight(to_tsvector('simple', definition_text), 'C')
14. Compute symbol_searchable: lowercased, punctuation-stripped concatenation of
    name + qualified_name + signature (for pg_trgm similarity)
15. Build doc_embed_text: labeled prose fields (BRIEF/DETAILS/PARAMS/RETURNS/NOTES/RATIONALE);
    fallback to bare name for doc-less entities
16. Build symbol_embed_text: qualified_name_signature for functions;
    qualified_name or bare name for non-functions
17. Load or generate dual embeddings (provider is required):
    - Doc embeddings: embed doc_embed_text via doc embedding provider (BAAI/bge-base-en-v1.5)
    - Symbol embeddings: embed symbol_embed_text via symbol embedding provider (jinaai/jina-embeddings-v2-base-code)
    - Each type has an independent cache file: embed_cache_{model_slug}_{dim}_{type}.pkl
    - Cache synchronization: load existing → compute missing → prune stale → save if changed
18. Drop/recreate schema (tables + indexes, CREATE INDEX IF NOT EXISTS; CREATE EXTENSION IF NOT EXISTS for vector + pg_trgm)
19. INSERT INTO entities (batch, ~5000 rows — includes dual embeddings, dual tsvectors, symbol_searchable, qualified_name)
20. Compute ts_rank ceilings (99th percentile ts_rank for each tsvector column → INSERT INTO search_config)
21. Parse code_graph.gml → NetworkX graph → extract edges (translate to deterministic IDs)
22. INSERT INTO edges (batch, ~25000 rows)
23. Parse capability_defs.json ("desc" key), capability_graph.json → capabilities + capability_edges (from "dependencies" nested dict, 200 rows)
24. ANALYZE entities; ANALYZE edges; (update planner statistics)
```

### Runtime (Server Queries)

```
1. Tool invocation (e.g., search, get_entity)
2. For search: multi-view pipeline runs internally
   a. Query classification (symbol-like vs. conceptual)
   b. Per-view retrieval (5 channels: doc semantic, symbol semantic, doc keyword, symbol keyword, trigram)
   c. Cross-encoder reranking per view
   d. View competition (max score per entity across views)
   e. Deduplication + score floor + exact-name priority tier
3. For all other tools: direct entity_id lookup (no resolution)
4. Database query (SELECT ... WHERE ... ORDER BY score LIMIT N)
5. Map rows → Pydantic models (EntitySummary, EntityDetail, etc.)
6. Attach truncation metadata
7. Return JSON response to MCP client
```

---

## 5. Validation Rules

### Entity Identity

- `entity_id` UNIQUE (primary key), format `{prefix}:{7 hex chars}` where prefix ∈ {fn, var, cls, file, sym}
- `signature` NOT NULL (display-only, **not unique** — 521 signatures collide across compounds; not a lookup key)
- `kind` IN (function, variable, class, struct, file, enum, define, typedef, namespace, dir, group)
- `entity_type` IN (compound, member)

### Documentation

- `brief` max length: 200 characters
- `details` max length: 10,000 characters

### Metrics

- `fan_in >= 0`, `fan_out >= 0`
- `is_bridge` TRUE only if fan_in > 0 AND fan_out > 0 AND entity has non-null capability
- `is_entry_point` TRUE only if kind = 'function'

### Embeddings

- `doc_embedding` dimensions = `EMBEDDING_DIMENSION` env var (default 768, enforced by pgvector column definition)
- `symbol_embedding` dimensions = `EMBEDDING_DIMENSION` env var (default 768, enforced by pgvector column definition)
- `doc_embedding` can be NULL only if entity has no documentable content; otherwise populated from labeled prose fields
- `symbol_embedding` can be NULL only if entity has no documentable content; otherwise populated from qualified signature
- `doc_search_vector` generated using English dictionary (stemming): name=A, brief+details=B, notes+rationale+params+returns=C
- `symbol_search_vector` generated using Simple dictionary (no stemming): name=A, qualified_name+signature=B, definition_text=C
- `symbol_searchable` must be lowercase, punctuation-stripped (for pg_trgm similarity)
- `qualified_name` may be NULL (scope chain unavailable) but ≥90% of functions should have one; uses only namespace/class/struct/group as scoping containers

### Edges

- `source_id` and `target_id` MUST reference valid entity_id
- `relationship` IN (calls, uses, inherits, includes, contained_by)
- No self-loops for CALLS edges (source_id != target_id when relationship = 'CALLS')

---

## 6. Query Patterns

> **Convention**: Simple CRUD and filtered queries use SQLModel `select()`. Complex queries (per-view retrieval, cosine similarity, tsvector ranking, trigram matching) use `session.execute(text(...))` with bound parameters.

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
        .order_by(Entity.fan_in.desc())
        .limit(limit)
    )
    return list(result.scalars().all())

# Prefix match
async def get_by_prefix(session: AsyncSession, prefix: str, limit: int = 20) -> list[Entity]:
    result = await session.execute(
        select(Entity).where(Entity.name.startswith(prefix))
        .order_by(func.length(Entity.name), Entity.fan_in.desc())
        .limit(limit)
    )
    return list(result.scalars().all())
```

### Multi-View Search Pipeline

Search uses a multi-view pipeline with cross-encoder reranking. Per-view SQL retrieval is followed by in-Python cross-encoder scoring. See spec.md FR-007–FR-012 for the full pipeline description.

Per-view retrieval queries (5 channels total):

```python
# Doc semantic: cosine similarity on doc_embedding
# Symbol semantic: cosine similarity on symbol_embedding
# Doc keyword: ts_rank on doc_search_vector (english dictionary)
# Symbol keyword: ts_rank on symbol_search_vector (simple dictionary)
# Trigram: pg_trgm similarity on symbol_searchable
```

All ranking is done by the cross-encoder (Xenova/ms-marco-MiniLM-L-12-v2) after retrieval. There is no weighted-sum hybrid CTE — the cross-encoder is the sole authority on result ordering.

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

- **Database**: PostgreSQL 18 + pgvector + pg_trgm, 6 tables (entities, edges, capabilities, capability_edges, entry_points, search_config)
- **Entity Identity**: Deterministic `{prefix}:{7hex}` IDs computed from signature_map keys; stable across rebuilds from same artifacts
- **ORM Layer**: SQLModel `table=True` table definitions with SQLAlchemy async engine (asyncpg driver)
- **Query Style**: SQLModel `select()` for CRUD/filtered queries; `text()` for per-view retrieval (cosine, ts_rank, trigram)
- **In-memory**: NetworkX MultiDiGraph (~5300 nodes, ~25K edges) for BFS/traversal
- **API Models**: Pydantic v2 (EntitySummary, EntityDetail, SearchResult, BehaviorSlice, etc.); ResolutionEnvelope removed; SearchMode enum removed
- **Embedding**: Dual embedding architecture (required, no keyword-only fallback):
  - Doc embedding: BAAI/bge-base-en-v1.5 (labeled prose fields) — model locked
  - Symbol embedding: jinaai/jina-embeddings-v2-base-code (qualified scoped signature) — model locked
  - Cross-encoder: Xenova/ms-marco-MiniLM-L-12-v2 (reranking) — model locked
  - Provider: local FastEmbed ONNX or hosted OpenAI-compatible; vector dimension configurable (default 768)
- **Build Script**: Offline ETL (artifact parsing → on-the-fly sig_map computation → deterministic ID generation → source extraction with fail-fast → capability assignment → metric computation → qualified_name derivation → dual embed text assembly → incremental embedding cache sync per type (doc, symbol, usages) → dual tsvector generation → symbol_searchable computation → ts_rank ceiling calibration → DB population via SQLModel session)
- **Server Runtime**: Async queries (SQLModel + SQLAlchemy async session) + in-memory graph algorithms (NetworkX) + multi-view search pipeline (5-channel retrieval → cross-encoder reranking → view competition → deduplication → score floor + exact-name priority) + async embedding (via `to_thread` for local)

All validation rules enforced at database constraints + Pydantic model validation. No runtime LLM inference; all data pre-computed.

---

## Appendix A: Artifact Data Contracts

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

Bridges entity IDs from `code_graph.json` to documentation keys in `doc_db.json`. The value is the `(compound_id, signature)` tuple that serves as the doc_db key. This file was a **derived** artifact — regenerated from `code_graph.json` + `doc_db.json` via `projects/doc_gen/build_signature_map.py`.

<!-- spec 005: The signature_map tuple (compound_id, signature_or_name) is also the canonical key
     used to compute deterministic entity IDs: {prefix}:{sha256(str(tuple))[:7]} -->

**Regeneration lifecycle**: ~~`signature_map.json` must be regenerated any time `code_graph.json` is refreshed from new Doxygen output, because Doxygen member hashes (the `member` part of entity IDs) change across runs.~~ The signature map is now computed at build time — no separate regeneration step. The doc_db key `(compound_id, signature)` is stable because `compound_id` derives from C++ qualified names and `signature` is the entity's definition text or name. See `artifacts/artifacts.md` §4-5 for full details.

**Phantom references**: `code_graph.json` contains ~506 entity IDs in `detailed_refs` and `codeline_refs` that don't appear as entities in the `id` fields. These are `enumvalue` IDs (~479, individual enum constants) and `friend` memberdefs (~27, filtered out during parsing). They are expected and should be silently skipped when translating edge endpoints during the build.

---

## Appendix B: Embedding Provider

### Configuration (ServerConfig extensions)

| Field | Type | Default | Env Var | Notes |
|---|---|---|---|---|
| `embedding_provider` | `"local" \| "hosted"` | `"local"` | `EMBEDDING_PROVIDER` | Required; no `null` option (no keyword-only mode) |
| `embedding_local_model` | `str` | `"BAAI/bge-base-en-v1.5"` | `EMBEDDING_LOCAL_MODEL` | Doc embedding model (local mode) — locked |
| `symbol_local_model` | `str` | `"jinaai/jina-embeddings-v2-base-code"` | `SYMBOL_LOCAL_MODEL` | Symbol embedding model (local mode) — locked |
| `cross_encoder_model` | `str` | `"Xenova/ms-marco-MiniLM-L-12-v2"` | `CROSS_ENCODER_MODEL` | Cross-encoder reranker — locked |
| `embedding_dimension` | `int` | `768` | `EMBEDDING_DIMENSION` | Must match both doc and symbol provider output |
| `embedding_base_url` | `str \| null` | `null` | `EMBEDDING_BASE_URL` | Required when provider = "hosted" |
| `embedding_api_key` | `str \| null` | `null` | `EMBEDDING_API_KEY` | — |
| `embedding_model` | `str \| null` | `null` | `EMBEDDING_MODEL` | Required when provider = "hosted" |

Cache file naming: `embed_cache_{model_slug}_{dim}_{type}.pkl` where model_slug has `/` → `-` and `{type}` is the embedding package identifier (e.g., "doc", "symbol", "usages").

### EmbeddingProvider Protocol

```python
class EmbeddingProvider(Protocol):
    @property
    def dimension(self) -> int: ...
    @property
    def max_batch_size(self) -> int: ...
    def embed(self, text: str) -> list[float]: ...
    def embed_batch(self, texts: list[str]) -> list[list[float]]: ...
```

The protocol exposes both sync (`embed`, `embed_batch`) and async (`aembed`, `aembed_batch`) surfaces. The provider owns the async strategy — local uses `asyncio.to_thread()`, hosted uses native `AsyncOpenAI`. Server runtime calls `await provider.aembed(query)`; build pipeline calls `provider.embed_batch(texts)`.

**Variants:**
- `LocalEmbeddingProvider`: Wraps `fastembed.TextEmbedding`. `max_batch_size=256`. Async via `asyncio.to_thread()`.
- `HostedEmbeddingProvider`: Wraps `openai.OpenAI` (sync) + `openai.AsyncOpenAI` (async). `max_batch_size=256`.

**Factory:** `create_provider(config) → EmbeddingProvider` — returns appropriate variant. No `None` return; embedding is required.

**Invariant:** `provider.dimension == config.embedding_dimension` (validated by factory, fails fast on mismatch).

### CrossEncoderProvider

Wraps `fastembed.TextCrossEncoder` with async support.

```python
class CrossEncoderProvider:
    def __init__(self, model_name: str) -> None:
        self._reranker = TextCrossEncoder(model_name=model_name)

    def rerank(self, query: str, documents: list[str], batch_size: int = 64) -> list[float]:
        return list(self._reranker.rerank(query, documents, batch_size=batch_size))

    async def arerank(self, query: str, documents: list[str], batch_size: int = 64) -> list[float]:
        return await asyncio.to_thread(self.rerank, query, documents, batch_size)
```

### Embedding Artifact Lifecycle

Cache files are named `embed_cache_{model_slug}_{dim}_{type}.pkl` (e.g., `embed_cache_bge-base-en-v1-5_768_doc.pkl`, `embed_cache_jina-embeddings-v2-base-code_768_symbol.pkl`). Each embedding type has an independent file.

Per-type synchronization (provider is always configured):
1. Load existing cache file for that type if it exists
2. Compute missing keys (in current build but not in cache) and stale keys (in cache but not in current build)
3. Generate embeddings only for missing keys via `provider.embed_batch()`
4. Prune stale keys from cache dict
5. Save updated cache file if any changes occurred; skip save if cache was already current
6. Invalidation is manual — developer deletes the type-specific file to force full regeneration
