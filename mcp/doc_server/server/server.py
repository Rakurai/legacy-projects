"""
MCP Documentation Server - FastMCP Server Entry Point.

Long-lived async server handling multiple sequential MCP tool invocations.
Uses stdio transport for communication with MCP clients.
"""

import json
from typing import Any

from fastmcp import FastMCP

from server.errors import CapabilityNotFoundError, EntityNotFoundError, not_found_response
from server.lifespan import lifespan, server_context
from server.logging_config import log
from server.prompts import (
    analyze_behavior_prompt,
    compare_entry_points_prompt,
    explain_entity_prompt,
    explore_capability_prompt,
)
from server.resources import (
    get_capabilities_resource,
    get_capability_detail_resource,
    get_entity_resource,
    get_file_entities_resource,
    get_stats_resource,
)
from server.tools.behavior import (
    GetBehaviorSliceParams,
    GetHotspotsParams,
    GetStateTouchesParams,
    get_behavior_slice_tool,
    get_hotspots_tool,
    get_state_touches_tool,
)
from server.tools.capability import (
    CompareCapabilitiesParams,
    GetCapabilityDetailParams,
    GetEntryPointInfoParams,
    ListCapabilitiesParams,
    ListEntryPointsParams,
    compare_capabilities_tool,
    get_capability_detail_tool,
    get_entry_point_info_tool,
    list_capabilities_tool,
    list_entry_points_tool,
)
from server.tools.entity import (
    GetEntityParams,
    GetFileSummaryParams,
    GetSourceCodeParams,
    ListFileEntitiesParams,
    ResolveEntityParams,
    get_entity_tool,
    get_file_summary_tool,
    get_source_code_tool,
    list_file_entities_tool,
    resolve_entity_tool,
)
from server.tools.graph import (
    GetCalleesParams,
    GetCallersParams,
    GetClassHierarchyParams,
    GetDependenciesParams,
    GetRelatedEntitiesParams,
    GetRelatedFilesParams,
    get_callees_tool,
    get_callers_tool,
    get_class_hierarchy_tool,
    get_dependencies_tool,
    get_related_entities_tool,
    get_related_files_tool,
)
from server.tools.search import SearchParams, search_tool


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
            embedding_model=server_context.embedding_model,
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
        try:
            result = await get_entity_tool(
                session=session,
                params=params,
                graph=server_context.graph,
            )
        except EntityNotFoundError as e:
            return not_found_response(e.identifier, e.kind)

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
        try:
            result = await get_source_code_tool(
                session=session,
                params=params,
                project_root=server_context.config.project_root if server_context.config else None,
            )
        except EntityNotFoundError as e:
            return not_found_response(e.identifier, e.kind)

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
        try:
            result = await get_file_summary_tool(session=session, params=params)
        except EntityNotFoundError as e:
            return not_found_response(e.identifier, e.kind)

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
            embedding_model=server_context.embedding_model,
        )

    return result.model_dump()


@mcp.tool()
async def get_callers(
    entity_id: str | None = None,
    signature: str | None = None,
    depth: int = 1,
    limit: int = 50,
) -> dict[str, Any]:
    """
    Get callers (functions that call this entity).

    Backward traversal in dependency graph up to specified depth.
    Each entity appears once at shortest path distance.

    Args:
        entity_id: Entity ID
        signature: Entity signature (alternative to entity_id)
        depth: Traversal depth (1-3)
        limit: Max results per depth level (1-200)

    Returns:
        Callers grouped by depth with truncation metadata
    """
    params = GetCallersParams(entity_id=entity_id, signature=signature, depth=depth, limit=limit)

    async with server_context.db_manager.session() as session:  # type: ignore
        result = await get_callers_tool(
            session=session,
            params=params,
            graph=server_context.graph,  # type: ignore
        )

    return result.model_dump()


@mcp.tool()
async def get_callees(
    entity_id: str | None = None,
    signature: str | None = None,
    depth: int = 1,
    limit: int = 50,
) -> dict[str, Any]:
    """
    Get callees (functions called by this entity).

    Forward traversal in dependency graph up to specified depth.
    Each entity appears once at shortest path distance.

    Args:
        entity_id: Entity ID
        signature: Entity signature (alternative to entity_id)
        depth: Traversal depth (1-3)
        limit: Max results per depth level (1-200)

    Returns:
        Callees grouped by depth with truncation metadata
    """
    params = GetCalleesParams(entity_id=entity_id, signature=signature, depth=depth, limit=limit)

    async with server_context.db_manager.session() as session:  # type: ignore
        result = await get_callees_tool(
            session=session,
            params=params,
            graph=server_context.graph,  # type: ignore
        )

    return result.model_dump()


@mcp.tool()
async def get_dependencies(
    entity_id: str | None = None,
    signature: str | None = None,
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
        signature: Entity signature (alternative to entity_id)
        relationship: Filter by type (calls, uses, inherits, includes, contained_by)
        direction: Edge direction (incoming, outgoing, both)
        limit: Maximum results (1-500)

    Returns:
        Dependencies with relationship and direction metadata
    """
    params = GetDependenciesParams(
        entity_id=entity_id,
        signature=signature,
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
async def get_class_hierarchy(
    entity_id: str | None = None,
    signature: str | None = None,
) -> dict[str, Any]:
    """
    Get class hierarchy (base classes and derived classes).

    Traverses INHERITS edges in both directions.

    Args:
        entity_id: Class entity ID
        signature: Entity signature (alternative to entity_id)

    Returns:
        Base classes (ancestors) and derived classes (descendants)
    """
    params = GetClassHierarchyParams(entity_id=entity_id, signature=signature)

    async with server_context.db_manager.session() as session:  # type: ignore
        result = await get_class_hierarchy_tool(
            session=session,
            params=params,
            graph=server_context.graph,  # type: ignore
        )

    return result.model_dump()


@mcp.tool()
async def get_related_entities(
    entity_id: str | None = None,
    signature: str | None = None,
    limit: int = 100,
) -> dict[str, Any]:
    """
    Get all direct neighbors grouped by relationship type.

    Provides complete local neighborhood of an entity.

    Args:
        entity_id: Entity ID
        signature: Entity signature (alternative to entity_id)
        limit: Maximum results (1-500)

    Returns:
        Neighbors grouped by relationship type and direction
    """
    params = GetRelatedEntitiesParams(entity_id=entity_id, signature=signature, limit=limit)

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


# ---- Phase 6: Behavioral Analysis Tools (US4) ----


@mcp.tool()
async def get_behavior_slice(
    entity_id: str | None = None,
    signature: str | None = None,
    max_depth: int = 5,
    max_cone_size: int = 200,
) -> dict[str, Any]:
    """
    Compute transitive call cone with behavioral analysis.

    Analyzes:
    - Direct and transitive callees (BFS through CALLS edges)
    - Capabilities touched (which capability groups the cone spans)
    - Global variables used (direct and transitive USES edges)
    - Side effects (messaging, persistence, state_mutation, scheduling)

    Args:
        entity_id: Seed entity ID
        signature: Entity signature (alternative to entity_id)
        max_depth: Maximum traversal depth (1-10, default 5)
        max_cone_size: Maximum cone size before truncation (1-1000, default 200)

    Returns:
        BehaviorSlice with full analysis and truncation metadata
    """
    params = GetBehaviorSliceParams(
        entity_id=entity_id,
        signature=signature,
        max_depth=max_depth,
        max_cone_size=max_cone_size,
    )

    async with server_context.db_manager.session() as session:  # type: ignore
        try:
            result = await get_behavior_slice_tool(
                session=session,
                params=params,
                graph=server_context.graph,  # type: ignore
            )
        except EntityNotFoundError as e:
            return not_found_response(e.identifier, e.kind)

    return result.model_dump()


@mcp.tool()
async def get_state_touches(
    entity_id: str | None = None,
    signature: str | None = None,
) -> dict[str, Any]:
    """
    Analyze global variable usage and side effects (direct + transitive).

    Direct: Variables this entity uses directly (USES edges, depth=1)
    Transitive: Variables reachable via CALLS→USES (depth=2 hops)
    Side effects: Categorized markers from entity's call chain

    Args:
        entity_id: Entity ID
        signature: Entity signature (alternative to entity_id)

    Returns:
        Direct and transitive state touches with side effect markers
    """
    params = GetStateTouchesParams(entity_id=entity_id, signature=signature)

    async with server_context.db_manager.session() as session:  # type: ignore
        try:
            result = await get_state_touches_tool(
                session=session,
                params=params,
                graph=server_context.graph,  # type: ignore
            )
        except EntityNotFoundError as e:
            return not_found_response(e.identifier, e.kind)

    return result.model_dump()


@mcp.tool()
async def get_hotspots(
    metric: str,
    kind: str | None = None,
    capability: str | None = None,
    limit: int = 20,
) -> dict[str, Any]:
    """
    Find architectural hotspots ranked by metric.

    Metrics:
    - fan_in: Most called functions (highest incoming edges)
    - fan_out: Functions calling the most things (highest outgoing edges)
    - bridge: Functions spanning multiple capabilities
    - underdocumented: Important functions with low documentation quality

    Args:
        metric: Ranking metric (fan_in, fan_out, bridge, underdocumented)
        kind: Optional kind filter (function, class, variable, etc.)
        capability: Optional capability filter
        limit: Maximum results (1-100, default 20)

    Returns:
        Ranked hotspot entities with truncation metadata
    """
    params = GetHotspotsParams(
        metric=metric,  # type: ignore
        kind=kind,
        capability=capability,
        limit=limit,
    )

    async with server_context.db_manager.session() as session:  # type: ignore
        result = await get_hotspots_tool(session=session, params=params)

    return result.model_dump()


# ---- Phase 7: Capability System Tools (US5) ----


@mcp.tool()
async def list_capabilities() -> dict[str, Any]:
    """
    List all capability groups with metadata.

    Returns all 30 capability groups with their type, description,
    function count, stability, and documentation quality distribution.

    Returns:
        List of capability summaries
    """
    params = ListCapabilitiesParams()

    async with server_context.db_manager.session() as session:  # type: ignore
        result = await list_capabilities_tool(session=session, params=params)

    return result.model_dump()


@mcp.tool()
async def get_capability_detail(
    capability: str,
    include_functions: bool = False,
) -> dict[str, Any]:
    """
    Get detailed capability information.

    Includes dependencies on other capabilities, entry points exercising
    this capability, and optionally the full function list.

    Args:
        capability: Capability name (e.g., combat, magic, persistence)
        include_functions: Include full function list (may be large)

    Returns:
        Detailed capability information with dependencies and entry points
    """
    params = GetCapabilityDetailParams(
        capability=capability,
        include_functions=include_functions,
    )

    async with server_context.db_manager.session() as session:  # type: ignore
        try:
            result = await get_capability_detail_tool(session=session, params=params)
        except CapabilityNotFoundError as e:
            return not_found_response(e.name, "capability")

    return result.model_dump()


@mcp.tool()
async def compare_capabilities(
    capabilities: list[str],
    limit: int = 50,
) -> dict[str, Any]:
    """
    Compare multiple capabilities showing shared/unique dependencies and bridges.

    Analyzes which functions are shared between capabilities, which are unique
    to each, and which serve as bridge functions connecting them.

    Args:
        capabilities: 2+ capability names to compare
        limit: Maximum results per section (1-200, default 50)

    Returns:
        Comparison with shared/unique dependencies and bridge entities
    """
    params = CompareCapabilitiesParams(
        capabilities=capabilities,
        limit=limit,
    )

    async with server_context.db_manager.session() as session:  # type: ignore
        result = await compare_capabilities_tool(
            session=session,
            params=params,
            graph=server_context.graph,  # type: ignore
        )

    return result.model_dump()


@mcp.tool()
async def list_entry_points(
    capability: str | None = None,
    name_pattern: str | None = None,
    limit: int = 100,
) -> dict[str, Any]:
    """
    List entry points (do_*, spell_*, spec_* functions).

    Entry points are the primary user-facing functions in the MUD server.
    Filterable by capability group and name pattern.

    Args:
        capability: Optional capability filter
        name_pattern: Optional SQL LIKE pattern (e.g., 'do_look%')
        limit: Maximum results (1-500, default 100)

    Returns:
        Entry point entity summaries with truncation metadata
    """
    params = ListEntryPointsParams(
        capability=capability,
        name_pattern=name_pattern,
        limit=limit,
    )

    async with server_context.db_manager.session() as session:  # type: ignore
        result = await list_entry_points_tool(session=session, params=params)

    return result.model_dump()


@mcp.tool()
async def get_entry_point_info(
    entity_id: str | None = None,
    signature: str | None = None,
) -> dict[str, Any]:
    """
    Analyze which capabilities an entry point exercises.

    Computes the call cone and maps each callee to its capability group,
    showing direct vs transitive capability exercise counts.

    Args:
        entity_id: Entry point entity ID
        signature: Entity signature (alternative to entity_id)

    Returns:
        Entry point summary with capabilities exercised (direct/transitive counts)
    """
    params = GetEntryPointInfoParams(entity_id=entity_id, signature=signature)

    async with server_context.db_manager.session() as session:  # type: ignore
        try:
            result = await get_entry_point_info_tool(
                session=session,
                params=params,
                graph=server_context.graph,  # type: ignore
            )
        except EntityNotFoundError as e:
            return not_found_response(e.identifier, e.kind)

    return result.model_dump()


# ---- Phase 8: MCP Resources ----


@mcp.resource("legacy://capabilities")
async def capabilities_resource() -> str:
    """List all capability groups with metadata."""
    async with server_context.db_manager.session() as session:  # type: ignore
        data = await get_capabilities_resource(session)
    return json.dumps(data, default=str)


@mcp.resource("legacy://capability/{name}")
async def capability_detail_resource(name: str) -> str:
    """Get detailed capability information."""
    async with server_context.db_manager.session() as session:  # type: ignore
        data = await get_capability_detail_resource(session, name)
    return json.dumps(data, default=str)


@mcp.resource("legacy://entity/{entity_id}")
async def entity_resource(entity_id: str) -> str:
    """Get full entity details by entity_id."""
    async with server_context.db_manager.session() as session:  # type: ignore
        data = await get_entity_resource(session, entity_id)
    return json.dumps(data, default=str)


@mcp.resource("legacy://file/{path}")
async def file_entities_resource(path: str) -> str:
    """List all entities defined in a source file."""
    # URL-decode the path (e.g., src%2Ffight.cc → src/fight.cc)
    from urllib.parse import unquote
    file_path = unquote(path)
    async with server_context.db_manager.session() as session:  # type: ignore
        data = await get_file_entities_resource(session, file_path)
    return json.dumps(data, default=str)


@mcp.resource("legacy://stats")
async def stats_resource() -> str:
    """Get aggregate server statistics."""
    async with server_context.db_manager.session() as session:  # type: ignore
        data = await get_stats_resource(
            session,
            graph=server_context.graph,
            embedding_available=server_context.embedding_client is not None,
        )
    return json.dumps(data, default=str)


# ---- Phase 8: MCP Prompts ----


@mcp.prompt()
def explain_entity(entity_name: str) -> list[dict[str, str]]:
    """
    Comprehensive entity explanation workflow.

    Guides the AI through resolving an entity, gathering its documentation,
    callers, callees, and architectural context.
    """
    return explain_entity_prompt(entity_name)


@mcp.prompt()
def analyze_behavior(entity_name: str, max_depth: int = 5) -> list[dict[str, str]]:
    """
    Behavioral analysis workflow for a function.

    Guides the AI through computing the call cone, analyzing capabilities
    touched, global state interactions, and side effects.
    """
    return analyze_behavior_prompt(entity_name, max_depth)


@mcp.prompt()
def compare_entry_points(entry_point_names: list[str]) -> list[dict[str, str]]:
    """
    Entry point comparison workflow.

    Guides the AI through comparing multiple entry points to identify
    shared dependencies, unique functionality, and refactoring opportunities.
    """
    return compare_entry_points_prompt(entry_point_names)


@mcp.prompt()
def explore_capability(capability_name: str) -> list[dict[str, str]]:
    """
    Capability exploration workflow.

    Guides the AI through exploring a capability group's structure,
    dependencies, entry points, hotspots, and architectural role.
    """
    return explore_capability_prompt(capability_name)


def main():
    """Main entry point."""
    mcp.run(
        transport="stdio",
    )


if __name__ == "__main__":
    main()
