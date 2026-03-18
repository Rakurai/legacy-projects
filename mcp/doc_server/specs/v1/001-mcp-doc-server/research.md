# Research: MCP Documentation Server

**Feature**: 001-mcp-doc-server
**Phase**: 0 (Research & Technology Selection)
**Date**: 2026-03-14

## Overview

This document captures research findings and technology selection decisions for the MCP Documentation Server. All "NEEDS CLARIFICATION" items from Technical Context were pre-resolved; this research validates those choices and documents best practices.

---

## 1. FastMCP Framework

### Decision

Use **FastMCP** (latest version) as the MCP server framework.

### Rationale

FastMCP is the official Python framework for building MCP servers. It provides:
- Declarative tool/resource/prompt registration via decorators
- Async/await support (critical for I/O-bound operations)
- Automatic JSON-RPC protocol handling over stdio
- Built-in validation via Pydantic models
- Type-safe tool parameter definitions

### Best Practices

**Tool Definition Pattern:**
```python
from fastmcp import FastMCP
from pydantic import BaseModel

mcp = FastMCP("Legacy Documentation Server")

class ResolveEntityParams(BaseModel):
    query: str
    kind: str | None = None

@mcp.tool()
async def resolve_entity(params: ResolveEntityParams) -> dict:
    """Resolve entity name to ranked candidates."""
    # Implementation with async database queries
    return result
```

**Resource Pattern:**
```python
@mcp.resource("legacy://entity/{entity_id}")
async def get_entity_resource(uri: str) -> str:
    entity_id = uri.split("/")[-1]
    # Fetch and return JSON
    return json.dumps(entity_data)
```

**Prompt Pattern:**
```python
@mcp.prompt()
async def explain_entity(entity_name: str) -> list[dict]:
    """Generate canned prompt for entity explanation workflow."""
    return [
        {"role": "user", "content": f"Explain {entity_name}..."},
        {"role": "assistant", "content": "I'll look that up..."}
    ]
```

**Server Execution:**
```python
if __name__ == "__main__":
    mcp.run(transport="stdio")  # Long-lived async event loop
```

### Alternatives Considered

- **Raw JSON-RPC implementation** — rejected because FastMCP provides battle-tested protocol handling and reduces boilerplate
- **mcp-server-python (anthropic)** — rejected because FastMCP is more actively maintained and has better async support

---

## 2. PostgreSQL + pgvector

### Decision

Use **PostgreSQL 17** with **pgvector** extension for entity storage, full-text search, and semantic search.

### Rationale

PostgreSQL provides:
- **Mature full-text search** with `tsvector`, `ts_rank`, weighted indexing (name=A, details=B, etc.)
- **pgvector extension** for cosine similarity search on 4,096-dim embeddings
- **Async query support** via SQLModel + SQLAlchemy async (asyncpg driver under the hood)
- **Single data store** for entities, edges, embeddings (no polyglot persistence)
- **ACID guarantees** for build script idempotency

pgvector specifically enables:
- `vector(4096)` column type for embeddings
- `<=>` operator for L2 distance, `<#>` for cosine distance
- Indexing strategies (IVFFlat, HNSW) for fast approximate nearest neighbor search

### Schema Design Principles

**Entities Table:**
```sql
CREATE TABLE entities (
    entity_id TEXT PRIMARY KEY,           -- Doxygen ID (compound_member)
    compound_id TEXT NOT NULL,
    member_id TEXT,
    signature TEXT UNIQUE NOT NULL,       -- User-facing key
    name TEXT NOT NULL,
    kind TEXT NOT NULL,                    -- function, class, variable, etc.
    entity_type TEXT NOT NULL,             -- compound or member
    file_path TEXT,
    body_start_line INTEGER,
    body_end_line INTEGER,
    decl_file_path TEXT,
    decl_line INTEGER,
    definition_text TEXT,
    source_text TEXT,                      -- Extracted at build time
    capability TEXT,
    doc_state TEXT,
    doc_quality TEXT,                      -- high, medium, low
    brief TEXT,
    details TEXT,
    params JSONB,
    returns TEXT,
    notes TEXT,
    rationale TEXT,
    usages JSONB,
    fan_in INTEGER DEFAULT 0,
    fan_out INTEGER DEFAULT 0,
    is_bridge BOOLEAN DEFAULT FALSE,
    is_entry_point BOOLEAN DEFAULT FALSE,
    side_effect_markers JSONB,             -- {messaging: [], persistence: [], ...}
    embedding vector(4096),                -- pgvector column
    search_vector tsvector                 -- Full-text search
);

CREATE INDEX idx_entities_name ON entities(name);
CREATE INDEX idx_entities_kind ON entities(kind);
CREATE INDEX idx_entities_file ON entities(file_path);
CREATE INDEX idx_entities_capability ON entities(capability);
CREATE INDEX idx_entities_entry ON entities(is_entry_point) WHERE is_entry_point;
CREATE INDEX idx_entities_bridge ON entities(is_bridge) WHERE is_bridge;
CREATE INDEX idx_entities_search ON entities USING GIN(search_vector);
CREATE INDEX idx_entities_embedding ON entities USING ivfflat (embedding vector_cosine_ops) WITH (lists = 50);
```

**Edges Table:**
```sql
CREATE TABLE edges (
    source_id TEXT NOT NULL REFERENCES entities(entity_id),
    target_id TEXT NOT NULL REFERENCES entities(entity_id),
    relationship TEXT NOT NULL,             -- calls, uses, inherits, includes, contained_by
    PRIMARY KEY (source_id, target_id, relationship)
);

CREATE INDEX idx_edges_source ON edges(source_id);
CREATE INDEX idx_edges_target ON edges(target_id);
CREATE INDEX idx_edges_rel ON edges(relationship);
```

**Capabilities Table:**
```sql
CREATE TABLE capabilities (
    name TEXT PRIMARY KEY,
    type TEXT NOT NULL,                    -- domain, policy, projection, infrastructure, utility
    description TEXT,
    function_count INTEGER,
    stability TEXT,
    doc_quality_dist JSONB
);

CREATE TABLE capability_edges (
    source_cap TEXT NOT NULL REFERENCES capabilities(name),
    target_cap TEXT NOT NULL REFERENCES capabilities(name),
    edge_type TEXT NOT NULL,               -- requires_core, requires_policy, uses_utility, etc.
    call_count INTEGER,
    PRIMARY KEY (source_cap, target_cap, edge_type)
);
```

### Best Practices

**Async Engine & Session Factory (via SQLAlchemy):**
```python
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

def build_engine(config: ServerConfig) -> AsyncEngine:
    return create_async_engine(
        f"postgresql+asyncpg://{config.pguser}:{config.pgpassword}"
        f"@{config.pghost}:{config.pgport}/{config.pgdatabase}",
        pool_size=10,
        max_overflow=0,
    )

def build_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
```

> **Note**: asyncpg is still the underlying driver (fastest Python PostgreSQL driver), but all application code interacts through SQLModel/SQLAlchemy — never importing asyncpg directly.

**Hybrid Search Query (via `text()`):**
```sql
WITH semantic AS (
    SELECT entity_id, 1 - (embedding <=> $1) AS score
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
SELECT e.*, COALESCE(ex.score, 0) * 10 + COALESCE(s.score, 0) * 0.6 + COALESCE(k.score, 0) * 0.4 AS combined_score
FROM entities e
LEFT JOIN exact ex USING (entity_id)
LEFT JOIN semantic s USING (entity_id)
LEFT JOIN keyword k USING (entity_id)
WHERE ex.entity_id IS NOT NULL OR s.entity_id IS NOT NULL OR k.entity_id IS NOT NULL
ORDER BY combined_score DESC
LIMIT $4;
```

### SQLModel Data Access Layer

**Decision**: Use **SQLModel** (`table=True` models) with **SQLAlchemy async engine** for all database operations. asyncpg is the underlying driver but never imported directly by application code.

**Rationale**:
- Single model definition serves both Pydantic validation and SQLAlchemy persistence
- `table=True` models enforce strict typing at the database boundary (mypy --strict compliant)
- Repository pattern (per SQLMODEL.md) encapsulates query logic; services own transactions
- Compatible with pgvector via `pgvector.sqlalchemy` package (`Vector` column type)
- Compatible with PostgreSQL full-text search via `sqlalchemy.dialects.postgresql.TSVECTOR`

**Table Model Pattern:**
```python
from sqlmodel import SQLModel, Field
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import TSVECTOR, JSONB
from pgvector.sqlalchemy import Vector

class Entity(SQLModel, table=True):
    __tablename__ = "entities"

    entity_id: str = Field(primary_key=True)
    compound_id: str
    member_id: str | None = None
    signature: str = Field(unique=True)
    name: str
    kind: str
    entity_type: str
    file_path: str | None = None
    body_start_line: int | None = None
    body_end_line: int | None = None
    # ... remaining fields per data-model.md §1.1
    embedding: list[float] | None = Field(default=None, sa_column=Column(Vector(4096)))
    search_vector: str | None = Field(default=None, sa_column=Column(TSVECTOR))
```

**Repository Pattern:**
```python
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession

class EntityRepository:
    """Encapsulates entity DB access. Never commits — caller owns session."""

    async def get_by_id(self, session: AsyncSession, entity_id: str) -> Entity | None:
        return await session.get(Entity, entity_id)

    async def get_by_signature(self, session: AsyncSession, signature: str) -> Entity | None:
        result = await session.execute(select(Entity).where(Entity.signature == signature))
        return result.scalar_one_or_none()

    async def search_by_name(self, session: AsyncSession, name: str, limit: int = 20) -> list[Entity]:
        result = await session.execute(
            select(Entity).where(Entity.name == name).order_by(Entity.fan_in.desc()).limit(limit)
        )
        return list(result.scalars().all())
```

**Complex Queries (raw SQL via `text()`):**
Hybrid search, tsvector ranking, and pgvector cosine similarity queries use `session.execute(text(...))` with bound parameters. SQLModel `select()` is used for simple CRUD and filtered queries.

### Alternatives Considered

- **SQLite** — rejected because pgvector is PostgreSQL-only and semantic search is a hard requirement
- **Separate vector DB (Pinecone, Weaviate)** — rejected to avoid polyglot persistence; pgvector is sufficient for 5K entities
- **Elasticsearch** — rejected as overkill for this scale; PostgreSQL full-text search is adequate
- **Raw asyncpg** — rejected because SQLModel provides type-safe table definitions, Pydantic validation at the DB boundary, and repository pattern support without sacrificing async performance

---

## 3. NetworkX In-Memory Graph

### Decision

Load dependency graph from the `edges` table into **NetworkX MultiDiGraph** at server startup; keep in memory (read-only).

### Rationale

- **Small enough for memory**: ~5,300 nodes + 25,000 edges ≈ 100-200 MB
- **Fast graph algorithms**: BFS for call cone, shortest path, cycle detection
- **No concurrency issues**: Read-only after load; Python GIL safe for concurrent reads
- **No artifact files at runtime**: Server reads only from the database; build script handles GML parsing

### Best Practices

**Graph Loading:**
```python
import networkx as nx
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

async def load_graph(session: AsyncSession) -> nx.MultiDiGraph:
    """Load dependency graph from edges table."""
    log.info("Loading dependency graph from database")
    g = nx.MultiDiGraph()
    result = await session.execute(text("SELECT source_id, target_id, relationship FROM edges"))
    for row in result.all():
        g.add_edge(row.source_id, row.target_id, type=row.relationship)
    log.info("Graph loaded", nodes=g.number_of_nodes(), edges=g.number_of_edges())
    return g
```

**BFS Call Cone:**
```python
def compute_call_cone(
    graph: nx.MultiDiGraph,
    seed_id: str,
    max_depth: int = 5,
    max_size: int = 200
) -> dict[str, list[str]]:
    """Compute transitive call cone via BFS."""
    direct_callees = []
    transitive_cone = []
    visited = {seed_id}
    queue = [(seed_id, 0)]

    while queue and len(transitive_cone) < max_size:
        node_id, depth = queue.pop(0)
        if depth >= max_depth:
            continue

        for _, target, data in graph.out_edges(node_id, data=True):
            if data.get("type") != "CALLS":
                continue
            if target in visited:
                continue

            visited.add(target)
            if depth == 0:
                direct_callees.append(target)
            else:
                transitive_cone.append(target)

            queue.append((target, depth + 1))

    return {
        "direct": direct_callees,
        "transitive": transitive_cone,
        "truncated": len(transitive_cone) >= max_size
    }
```

### Alternatives Considered

- **Store edges in PostgreSQL only (no in-memory graph)** — rejected because graph traversal performance degrades with SQL recursion; in-memory NetworkX is 10-100x faster for BFS
- **Load GML file at runtime** — rejected because the server should not depend on artifact files at runtime; the edges table is the source of truth after build
- **Neo4j graph database** — rejected as overkill for this scale; deployment complexity not justified

---

## 4. Pydantic v2 for Schemas

### Decision

Use **Pydantic v2** for all request/response models and configuration validation.

### Rationale

- **Strict type validation** at API boundaries (MCP tool parameters, SQLModel rows → Pydantic API models)
- **JSON schema generation** for MCP tool contracts
- **Settings management** via `pydantic-settings` for environment config
- **Fast** (Pydantic v2 is Rust-backed)
- **Required by FastMCP** (Pydantic is the schema layer)
- **SQLModel integration** — SQLModel extends Pydantic BaseModel; `table=True` models share the same validation engine

### Best Practices

**Model Definition:**
```python
from pydantic import BaseModel, Field, field_validator
from typing import Literal

class EntitySummary(BaseModel):
    entity_id: str
    signature: str
    name: str
    kind: Literal["function", "variable", "class", "struct", "file", "enum", "define", "typedef", "namespace", "dir", "group"]
    file_path: str | None = None
    capability: str | None = None
    brief: str | None = None
    doc_state: str
    doc_quality: Literal["high", "medium", "low"]
    fan_in: int = Field(ge=0)
    fan_out: int = Field(ge=0)

    @field_validator("signature")
    @classmethod
    def signature_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("signature cannot be empty")
        return v.strip()
```

**Config Management:**
```python
from pydantic_settings import BaseSettings, SettingsConfigDict

class ServerConfig(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    pghost: str = "localhost"
    pgport: int = 5432
    pgdatabase: str = "legacy_docs"
    pguser: str = "postgres"
    pgpassword: str

    embedding_base_url: str | None = None  # Optional; degrades gracefully
    embedding_api_key: str | None = None
    embedding_model: str | None = None
    project_root: str
    artifacts_dir: str = "artifacts"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
```

### Alternatives Considered

- **Dataclasses** — rejected because no runtime validation or JSON schema generation
- **TypedDict** — rejected because no validation and less ergonomic

---

## 5. Loguru for Structured Logging

### Decision

Use **loguru** for all server and build script logging.

### Rationale

- **Structured logging** with context fields (operation, entity_id, duration, etc.)
- **Simple API** (`log.info`, `log.error`, `log.bind`)
- **Automatic context** (timestamp, level, module, line number)
- **Configurable sinks** (stderr for server, files for build script)
- **Performance** (lazy formatting)

### Best Practices

**Configuration:**
```python
from loguru import logger as log
import sys

def configure_logging(level: str):
    log.remove()  # Remove default handler
    log.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level> {extra}",
        level=level,
        serialize=False  # Human-readable by default; can switch to JSON for production
    )
```

**Usage Patterns:**
```python
# Start of operation
log.info("Resolving entity", query="damage", kind="function")

# Success
log.info("Entity resolved", entity_id="fight_8cc_1a2b3c...", match_type="signature_exact", duration_ms=42)

# Error
log.error("Database query failed", query="SELECT ...", error=str(e))

# Context binding
with log.contextualize(tool="search", query_id="abc123"):
    log.info("Executing hybrid search")
    # All logs in this context include tool="search", query_id="abc123"
```

**Log Levels:**
- **DEBUG**: Resolution pipeline stages, SQL queries, graph traversal steps
- **INFO**: Tool invocations, database events, performance metrics
- **WARNING**: Degraded states (embedding service down, truncated results)
- **ERROR**: Database failures, invalid parameters, internal errors

### Alternatives Considered

- **Standard library `logging`** — rejected because less ergonomic and requires more boilerplate for structured logging
- **structlog** — rejected because loguru is simpler and sufficient for this use case

---

## 6. OpenAI SDK for Embeddings

### Decision

Use **OpenAI Python SDK** for embedding queries via an OpenAI-compatible endpoint (Qwen3-Embedding-8B, 4096 dimensions, served locally via LM Studio).

### Rationale

- **Existing embeddings** in `embeddings_cache.pkl` were generated with Qwen3-Embedding-8B (4096 dims)
- **Same model required** for cosine similarity to be meaningful against cached embeddings
- **OpenAI-compatible API** — the SDK works with any endpoint that implements the OpenAI embeddings API
- **Async support** (`openai.AsyncOpenAI`)
- **Explicit mode switching** (embedding endpoint optional; search switches to keyword-only mode)

### Best Practices

**Client Setup:**
```python
from openai import AsyncOpenAI

async def get_embedding_client() -> AsyncOpenAI | None:
    if not config.embedding_base_url:
        log.warning("No embedding endpoint configured; semantic search disabled")
        return None
    return AsyncOpenAI(base_url=config.embedding_base_url, api_key=config.embedding_api_key or "lm-studio")
```

**Query Embedding:**
```python
async def embed_query(client: AsyncOpenAI | None, query: str) -> list[float] | None:
    if client is None:
        return None
    try:
        response = await client.embeddings.create(
            model=config.embedding_model,  # e.g., "text-embedding-qwen3-embedding-8b"
            input=query,
            encoding_format="float"
        )
        return response.data[0].embedding
    except Exception as e:
        log.warning("Embedding query failed", error=str(e), query=query[:50])
        return None  # Degrade gracefully
```

### Alternatives Considered

- **Local embedding model (sentence-transformers)** — rejected to avoid model download/inference overhead at startup; OpenAI-compatible endpoint matches existing artifacts
- **Different embedding model** — rejected because changing model would invalidate existing 5,293 cached embeddings (generated with Qwen3-Embedding-8B)

---

## 7. Build Script Architecture

### Decision

Offline ETL pipeline (`build_mcp_db.py`) that runs separately before server startup.

### Rationale

- **Separation of concerns**: Build = batch ETL, Server = online queries
- **Idempotency**: Re-running build produces identical database state
- **Validation at build time**: Source code extraction, derived metric computation, tsvector generation
- **No runtime overhead**: Server doesn't parse artifacts or compute metrics

### Pipeline Stages

1. **Validate artifacts** — Check all 6 required files exist and parse without errors
2. **Load entities** — Parse `code_graph.json` with `doxygen_parse.load_db()`
3. **Load documentation** — Parse `doc_db.json` with `doc_db` module
4. **Merge entity + doc** — 1:1 join on (compound_id, signature)
5. **Extract source code** — Read from disk using `body.fn`, `body.line`, `body.end_line`
6. **Compute derived metrics**:
   - `doc_quality` from doc_state + field presence
   - `fan_in`/`fan_out` from CALLS edges
   - `is_bridge` from cross-capability CALLS neighbors
   - `side_effect_markers` from curated function list
   - `is_entry_point` from name pattern (do_*, spell_*, spec_*)
7. **Generate tsvector** — Weighted composition: `setweight(to_tsvector(name), 'A') || setweight(to_tsvector(brief || details), 'B') || setweight(to_tsvector(definition), 'C') || setweight(to_tsvector(source_text), 'D')`
8. **Load embeddings** — Unpickle `embeddings_cache.pkl`, map to entity_id
9. **Populate database** — Bulk insert entities, edges, capabilities, capability_edges
10. **Validate population** — Row counts, sample queries

### Best Practices

**Build Script Entry Point:**
```python
import asyncio
from pathlib import Path

async def main():
    config = load_config()
    artifacts_dir = Path(config.artifacts_dir)

    log.info("Starting database build", artifacts_dir=str(artifacts_dir))

    # Stage 1: Validate
    validate_artifacts(artifacts_dir)

    # Stage 2-4: Load and merge
    entities = load_and_merge_entities(artifacts_dir)

    # Stage 5-7: Enrich
    enrich_entities(entities, artifacts_dir)

    # Stage 8-9: Populate
    engine = build_engine(config)
    session_factory = build_session_factory(engine)
    async with session_factory() as session:
        await populate_database(session, entities)
        await session.commit()
    await engine.dispose()

    log.info("Database build complete")

if __name__ == "__main__":
    asyncio.run(main())
```

**Idempotency Pattern:**
```sql
BEGIN;

DROP TABLE IF EXISTS entities CASCADE;
DROP TABLE IF EXISTS edges CASCADE;
DROP TABLE IF EXISTS capabilities CASCADE;
DROP TABLE IF EXISTS capability_edges CASCADE;

-- CREATE TABLE statements...
-- INSERT statements...

COMMIT;
```

### Alternatives Considered

- **Online artifact parsing at server startup** — rejected because startup time would exceed 5s target and complicate server logic
- **Incremental updates** — rejected because full rebuild is fast enough (<5 min) and avoids sync issues

---

## 8. Strict Typing Strategy

### Decision

**mypy --strict** enforcement, no `Any` in production paths, explicit type annotations everywhere.

### Rationale

- **Fail-fast validation** catches type errors at static analysis time
- **Self-documenting** code (signatures are contracts)
- **IDE support** (autocomplete, refactoring)
- **Aligns with PATTERNS.md** ("Type Safety as Contract")

### Best Practices

**Type Annotation Patterns:**
```python
from typing import TYPE_CHECKING
from collections.abc import Awaitable, Callable

if TYPE_CHECKING:
    from networkx import MultiDiGraph

# Function signatures — use SQLModel types, not raw driver types
async def resolve_entity(
    session: AsyncSession,
    query: str,
    kind: str | None = None,
    limit: int = 20
) -> list[EntitySummary]:
    """Resolve entity name to ranked candidates."""
    ...

# Callable types
ToolHandler = Callable[[dict[str, str]], Awaitable[dict[str, str]]]

# Protocol for duck typing
from typing import Protocol

class Resolvable(Protocol):
    async def resolve(self, query: str) -> list[EntitySummary]: ...
```

**Avoiding `Any`:**
```python
# BAD — raw driver types leak through
def process_row(row: Any) -> dict:
    return {"id": row["entity_id"]}

# GOOD — SQLModel table model provides typed access
def entity_to_summary(entity: Entity) -> EntitySummary:
    return EntitySummary(
        entity_id=entity.entity_id,
        signature=entity.signature,
        name=entity.name,
        kind=entity.kind,
        # ... fully typed, no Any
    )
```

### Tools

- **mypy** for static checking
- **ruff** for linting (replaces flake8, isort, black)
- **pyright** (optional, for editor integration)

---

## Summary

All technology choices validated. Key decisions:
1. **FastMCP** for MCP server framework (async, declarative tools)
2. **PostgreSQL 17 + pgvector** for unified storage (entities, embeddings, full-text)
3. **SQLModel + SQLAlchemy async** for type-safe data access (repository pattern, asyncpg driver)
4. **NetworkX** for in-memory graph algorithms (BFS, call cone)
5. **Pydantic v2** for strict validation and schemas
6. **Loguru** for structured logging
7. **OpenAI SDK** for embedding queries (with explicit degradation handling)
8. **Offline build script** for ETL (idempotent, validates artifacts)
9. **Strict typing** (`mypy --strict`, no `Any` in production)

No open research questions. Ready for Phase 1 (data model and contracts).
