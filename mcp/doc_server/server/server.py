"""
MCP Documentation Server - FastMCP Server Entry Point.

Long-lived async server handling multiple sequential MCP tool invocations.
Uses stdio transport for communication with MCP clients.
"""

import sys
from contextlib import asynccontextmanager
from typing import Any
import networkx as nx

from fastmcp import FastMCP
from openai import AsyncOpenAI

from server.config import ServerConfig
from server.db import DatabaseManager
from server.graph import load_graph
from server.logging_config import configure_logging, log
from server.tools.entity import (
    ResolveEntityParams,
    GetEntityParams,
    GetSourceCodeParams,
    ListFileEntitiesParams,
    GetFileSummaryParams,
    resolve_entity_tool,
    get_entity_tool,
    get_source_code_tool,
    list_file_entities_tool,
    get_file_summary_tool,
)
from server.tools.search import SearchParams, search_tool
from server.tools.graph import (
    GetCallersParams,
    GetCalleesParams,
    GetDependenciesParams,
    GetClassHierarchyParams,
    GetRelatedEntitiesParams,
    GetRelatedFilesParams,
    get_callers_tool,
    get_callees_tool,
    get_dependencies_tool,
    get_class_hierarchy_tool,
    get_related_entities_tool,
    get_related_files_tool,
)


# Lifespan context for server initialization
class ServerContext:
    """Server context holding database and graph instances."""

    def __init__(self):
        self.config: ServerConfig | None = None
        self.db_manager: DatabaseManager | None = None
        self.graph: nx.MultiDiGraph | None = None
        self.embedding_client: AsyncOpenAI | None = None


server_context = ServerContext()


@asynccontextmanager
async def lifespan(app: FastMCP):
    """
    Server lifespan manager.

    Initializes database connection and loads dependency graph at startup.
    Cleans up resources at shutdown.
    """
    # Startup
    log.info("Starting Legacy Documentation Server")

    # Load configuration
    config = ServerConfig()
    configure_logging(config.log_level)
    server_context.config = config

    log.info(
        "Configuration loaded",
        db_host=config.db_host,
        db_name=config.db_name,
        project_root=str(config.project_root),
    )

    # Initialize database manager
    db_manager = DatabaseManager(config)
    server_context.db_manager = db_manager

    log.info("Database connection established")

    # Load dependency graph
    log.info("Loading dependency graph from database")
    async with db_manager.session() as session:
        graph = await load_graph(session)
        server_context.graph = graph

    log.info(
        "Dependency graph loaded",
        nodes=graph.number_of_nodes(),
        edges=graph.number_of_edges(),
    )

    # Initialize embedding client (optional)
    if config.embedding_enabled:
        try:
            embedding_client = AsyncOpenAI(
                base_url=config.embedding_base_url,
                api_key=config.embedding_api_key or "default",
            )
            server_context.embedding_client = embedding_client
            log.info("Embedding client initialized", base_url=config.embedding_base_url)
        except Exception as e:
            log.warning("Embedding client initialization failed", error=str(e))
            server_context.embedding_client = None
    else:
        log.info("Embedding endpoint not configured; semantic search disabled")

    log.info("Server ready")

    yield

    # Shutdown
    log.info("Shutting down server")
    await db_manager.dispose()
    log.info("Server shutdown complete")


# Create FastMCP app
mcp = FastMCP(
    "Legacy Documentation Server",
    lifespan=lifespan,
)


# Tool: resolve_entity
@mcp.tool()
async def resolve_entity(query: str, kind: str | None = None) -> dict[str, Any]:
    """
    Resolve entity name to ranked candidates.

    Multi-stage resolution pipeline:
    1. Exact entity_id (if query looks like ID)
    2. Exact signature match
    3. Exact name match (ranked by doc_quality, fan_in)
    4. Prefix match (ranked by length, doc_quality)
    5. Keyword search (full-text via tsvector)
    6. Semantic search (pgvector, if embedding endpoint available)

    Args:
        query: Entity name, signature, or ID to resolve
        kind: Optional kind filter (function, class, variable, etc.)

    Returns:
        Resolution envelope with status, match_type, and ranked candidates
    """
    params = ResolveEntityParams(query=query, kind=kind)

    async with server_context.db_manager.session() as session:  # type: ignore
        result = await resolve_entity_tool(
            session=session,
            params=params,
            embedding_client=server_context.embedding_client,
        )

    return result.model_dump()


@mcp.tool()
async def get_entity(
    entity_id: str | None = None,
    signature: str | None = None,
    include_code: bool = False,
    include_neighbors: bool = False,
) -> dict[str, Any]:
    """
    Fetch full entity details by ID or signature.

    Provides complete documentation including:
    - Identity (name, signature, kind)
    - Source location (file, line range)
    - Documentation (brief, details, params, returns, rationale, usage notes)
    - Metrics (fan_in, fan_out, doc_quality, is_bridge)
    - Optional: source code (if include_code=true)
    - Optional: direct neighbors in dependency graph (if include_neighbors=true)

    Args:
        entity_id: Entity ID (from resolve_entity)
        signature: Entity signature (alternative to entity_id)
        include_code: Include source code in response
        include_neighbors: Include direct neighbors in dependency graph

    Returns:
        EntityDetail with complete documentation
    """
    params = GetEntityParams(
        entity_id=entity_id,
        signature=signature,
        include_code=include_code,
        include_neighbors=include_neighbors,
    )

    async with server_context.db_manager.session() as session:  # type: ignore
        result = await get_entity_tool(session=session, params=params)

    return result.model_dump()


@mcp.tool()
async def get_source_code(entity_id: str, context_lines: int = 5) -> dict[str, Any]:
    """
    Retrieve source code for an entity with optional context lines.

    Args:
        entity_id: Entity ID
        context_lines: Number of context lines before/after (0-50)

    Returns:
        Source code with file path and line range
    """
    params = GetSourceCodeParams(entity_id=entity_id, context_lines=context_lines)

    async with server_context.db_manager.session() as session:  # type: ignore
        result = await get_source_code_tool(session=session, params=params)

    return result


@mcp.tool()
async def list_file_entities(
    file_path: str,
    kind: str | None = None,
    limit: int = 100,
) -> dict[str, Any]:
    """
    List all entities defined in a source file.

    Args:
        file_path: Source file path (e.g., src/fight.cc)
        kind: Optional kind filter (function, class, variable, etc.)
        limit: Maximum results (1-500)

    Returns:
        List of entity summaries with truncation metadata
    """
    params = ListFileEntitiesParams(file_path=file_path, kind=kind, limit=limit)

    async with server_context.db_manager.session() as session:  # type: ignore
        result = await list_file_entities_tool(session=session, params=params)

    return result


@mcp.tool()
async def get_file_summary(file_path: str) -> dict[str, Any]:
    """
    Get file-level statistics and top entities.

    Provides:
    - Entity count total and by kind
    - Capability distribution
    - Documentation quality distribution
    - Top 10 entities by fan_in (most called)

    Args:
        file_path: Source file path

    Returns:
        File summary with aggregated statistics
    """
    params = GetFileSummaryParams(file_path=file_path)

    async with server_context.db_manager.session() as session:  # type: ignore
        result = await get_file_summary_tool(session=session, params=params)

    return result.model_dump()


@mcp.tool()
async def search(
    query: str,
    source: str = "entity",
    kind: str | None = None,
    capability: str | None = None,
    min_doc_quality: str | None = None,
    limit: int = 20,
) -> dict[str, Any]:
    """
    Perform hybrid semantic + keyword search.

    Combines three search strategies with weighted scoring:
    1. Exact match (signature or name) - 10x boost
    2. Semantic similarity (embeddings via pgvector) - 0.6 weight
    3. Keyword relevance (full-text via tsvector) - 0.4 weight

    Degrades gracefully to keyword-only mode if embedding service unavailable.
    Explicit mode reporting via search_mode field.

    Args:
        query: Search query (natural language or keywords)
        source: Search source ('entity' only in V1; V2-reserved parameter)
        kind: Optional kind filter (function, class, variable, etc.)
        capability: Optional capability filter
        min_doc_quality: Minimum documentation quality (high, medium, low)
        limit: Maximum results (1-100)

    Returns:
        Search results with mode indicator and ranked entities
    """
    params = SearchParams(
        query=query,
        source=source,  # type: ignore
        kind=kind,
        capability=capability,
        min_doc_quality=min_doc_quality,  # type: ignore
        limit=limit,
    )

    async with server_context.db_manager.session() as session:  # type: ignore
        result = await search_tool(
            session=session,
            params=params,
            embedding_client=server_context.embedding_client,
        )

    return result.model_dump()


@mcp.tool()
async def get_callers(entity_id: str, depth: int = 1, limit: int = 50) -> dict[str, Any]:
    """
    Get callers (functions that call this entity).

    Backward traversal in dependency graph up to specified depth.
    Each entity appears once at shortest path distance.

    Args:
        entity_id: Entity ID
        depth: Traversal depth (1-3)
        limit: Max results per depth level (1-200)

    Returns:
        Callers grouped by depth with truncation metadata
    """
    params = GetCallersParams(entity_id=entity_id, depth=depth, limit=limit)

    async with server_context.db_manager.session() as session:  # type: ignore
        result = await get_callers_tool(
            session=session,
            params=params,
            graph=server_context.graph,  # type: ignore
        )

    return result.model_dump()


@mcp.tool()
async def get_callees(entity_id: str, depth: int = 1, limit: int = 50) -> dict[str, Any]:
    """
    Get callees (functions called by this entity).

    Forward traversal in dependency graph up to specified depth.
    Each entity appears once at shortest path distance.

    Args:
        entity_id: Entity ID
        depth: Traversal depth (1-3)
        limit: Max results per depth level (1-200)

    Returns:
        Callees grouped by depth with truncation metadata
    """
    params = GetCalleesParams(entity_id=entity_id, depth=depth, limit=limit)

    async with server_context.db_manager.session() as session:  # type: ignore
        result = await get_callees_tool(
            session=session,
            params=params,
            graph=server_context.graph,  # type: ignore
        )

    return result.model_dump()


@mcp.tool()
async def get_dependencies(
    entity_id: str,
    relationship: str | None = None,
    direction: str = "both",
    limit: int = 100,
) -> dict[str, Any]:
    """
    Get filtered dependencies by relationship type and direction.

    Relationship types:
    - calls: Function calls
    - uses: Variable/type usage
    - inherits: Class inheritance
    - includes: File includes
    - contained_by: Member containment

    Args:
        entity_id: Entity ID
        relationship: Filter by type (calls, uses, inherits, includes, contained_by)
        direction: Edge direction (incoming, outgoing, both)
        limit: Maximum results (1-500)

    Returns:
        Dependencies with relationship and direction metadata
    """
    params = GetDependenciesParams(
        entity_id=entity_id,
        relationship=relationship,  # type: ignore
        direction=direction,  # type: ignore
        limit=limit,
    )

    async with server_context.db_manager.session() as session:  # type: ignore
        result = await get_dependencies_tool(
            session=session,
            params=params,
            graph=server_context.graph,  # type: ignore
        )

    return result.model_dump()


@mcp.tool()
async def get_class_hierarchy(entity_id: str) -> dict[str, Any]:
    """
    Get class hierarchy (base classes and derived classes).

    Traverses INHERITS edges in both directions.

    Args:
        entity_id: Class entity ID

    Returns:
        Base classes (ancestors) and derived classes (descendants)
    """
    params = GetClassHierarchyParams(entity_id=entity_id)

    async with server_context.db_manager.session() as session:  # type: ignore
        result = await get_class_hierarchy_tool(
            session=session,
            params=params,
            graph=server_context.graph,  # type: ignore
        )

    return result.model_dump()


@mcp.tool()
async def get_related_entities(entity_id: str, limit: int = 100) -> dict[str, Any]:
    """
    Get all direct neighbors grouped by relationship type.

    Provides complete local neighborhood of an entity.

    Args:
        entity_id: Entity ID
        limit: Maximum results (1-500)

    Returns:
        Neighbors grouped by relationship type and direction
    """
    params = GetRelatedEntitiesParams(entity_id=entity_id, limit=limit)

    async with server_context.db_manager.session() as session:  # type: ignore
        result = await get_related_entities_tool(
            session=session,
            params=params,
            graph=server_context.graph,  # type: ignore
        )

    return result.model_dump()


@mcp.tool()
async def get_related_files(file_path: str, limit: int = 50) -> dict[str, Any]:
    """
    Find related files via include relationships.

    Args:
        file_path: Source file path
        limit: Maximum results (1-200)

    Returns:
        Related files with relationship metadata
    """
    params = GetRelatedFilesParams(file_path=file_path, limit=limit)

    async with server_context.db_manager.session() as session:  # type: ignore
        result = await get_related_files_tool(
            session=session,
            params=params,
            graph=server_context.graph,  # type: ignore
        )

    return result.model_dump()


def main():
    """Main entry point."""
    mcp.run(
        transport="stdio",
    )


if __name__ == "__main__":
    main()
