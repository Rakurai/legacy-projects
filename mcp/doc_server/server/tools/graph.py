"""
Graph Navigation Tools - Dependency graph traversal and exploration.

Tools:
- get_callers: Find functions that call this entity (backward traversal)
- get_callees: Find functions called by this entity (forward traversal)
- get_dependencies: Get filtered dependencies by relationship type
- get_class_hierarchy: Get base and derived classes
- get_related_entities: Get all direct neighbors grouped by relationship
- get_related_files: Find related files via includes/co-dependency
"""

from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Literal
import networkx as nx

from server.db_models import Entity
from server.models import EntitySummary, TruncationMetadata
from server.resolver import entity_to_summary
from server.graph import get_callers as get_callers_fn, get_callees as get_callees_fn, get_class_hierarchy as get_class_hierarchy_fn
from server.logging_config import log
from server.util import fetch_entity_summaries, fetch_entity_map, resolve_entity_id


# Tool Parameter Models

class GetCallersParams(BaseModel):
    """Parameters for get_callers tool."""
    entity_id: str | None = Field(default=None, description="Entity ID")
    signature: str | None = Field(default=None, description="Entity signature (alternative to entity_id)")
    depth: int = Field(default=1, ge=1, le=3, description="Traversal depth (1-3)")
    limit: int = Field(default=50, ge=1, le=200, description="Max results per depth level")


class GetCalleesParams(BaseModel):
    """Parameters for get_callees tool."""
    entity_id: str | None = Field(default=None, description="Entity ID")
    signature: str | None = Field(default=None, description="Entity signature (alternative to entity_id)")
    depth: int = Field(default=1, ge=1, le=3, description="Traversal depth (1-3)")
    limit: int = Field(default=50, ge=1, le=200, description="Max results per depth level")


class GetDependenciesParams(BaseModel):
    """Parameters for get_dependencies tool."""
    entity_id: str | None = Field(default=None, description="Entity ID")
    signature: str | None = Field(default=None, description="Entity signature (alternative to entity_id)")
    relationship: Literal["calls", "uses", "inherits", "includes", "contained_by"] | None = Field(
        default=None,
        description="Filter by relationship type"
    )
    direction: Literal["incoming", "outgoing", "both"] = Field(
        default="both",
        description="Edge direction"
    )
    limit: int = Field(default=100, ge=1, le=500, description="Maximum results")


class GetClassHierarchyParams(BaseModel):
    """Parameters for get_class_hierarchy tool."""
    entity_id: str | None = Field(default=None, description="Class entity ID")
    signature: str | None = Field(default=None, description="Entity signature (alternative to entity_id)")


class GetRelatedEntitiesParams(BaseModel):
    """Parameters for get_related_entities tool."""
    entity_id: str | None = Field(default=None, description="Entity ID")
    signature: str | None = Field(default=None, description="Entity signature (alternative to entity_id)")
    limit: int = Field(default=100, ge=1, le=500, description="Maximum results")


class GetRelatedFilesParams(BaseModel):
    """Parameters for get_related_files tool."""
    file_path: str = Field(description="Source file path")
    limit: int = Field(default=50, ge=1, le=200, description="Maximum results")


# Tool Response Models

class CallersResponse(BaseModel):
    """Response from get_callers tool."""
    entity_id: str
    callers_by_depth: dict[int, list[EntitySummary]]
    truncation: TruncationMetadata


class CalleesResponse(BaseModel):
    """Response from get_callees tool."""
    entity_id: str
    callees_by_depth: dict[int, list[EntitySummary]]
    truncation: TruncationMetadata


class DependenciesResponse(BaseModel):
    """Response from get_dependencies tool."""
    entity_id: str
    dependencies: list[dict]  # List of {entity: EntitySummary, relationship: str, direction: str}
    truncation: TruncationMetadata


class ClassHierarchyResponse(BaseModel):
    """Response from get_class_hierarchy tool."""
    entity_id: str
    base_classes: list[EntitySummary]
    derived_classes: list[EntitySummary]


class RelatedEntitiesResponse(BaseModel):
    """Response from get_related_entities tool."""
    entity_id: str
    neighbors_by_relationship: dict[str, list[EntitySummary]]
    truncation: TruncationMetadata


class RelatedFilesResponse(BaseModel):
    """Response from get_related_files tool."""
    file_path: str
    related_files: list[dict]  # List of {file_path: str, relationship: str, entity_count: int}
    truncation: TruncationMetadata


# Tool Implementations

async def get_callers_tool(
    session: AsyncSession,
    params: GetCallersParams,
    graph: nx.MultiDiGraph,
) -> CallersResponse:
    """
    Get callers (entities with CALLS edges to this entity).

    Backward traversal in dependency graph up to specified depth.

    Args:
        session: Database session
        params: Tool parameters
        graph: Dependency graph

    Returns:
        Callers grouped by depth with truncation metadata
    """
    log.info("get_callers tool invoked", entity_id=params.entity_id, depth=params.depth)

    entity_id = await resolve_entity_id(session, params.entity_id, params.signature)
    callers_by_depth_ids = get_callers_fn(graph, entity_id, params.depth, params.limit)

    # Batch-fetch all entity IDs across all depths
    all_ids = [eid for ids in callers_by_depth_ids.values() for eid in ids]
    entity_map = await fetch_entity_map(session, all_ids)

    # Build summaries per depth
    callers_by_depth: dict[int, list[EntitySummary]] = {}
    total_callers = 0

    for depth, entity_ids in callers_by_depth_ids.items():
        summaries = [
            entity_to_summary(entity_map[eid])
            for eid in entity_ids
            if eid in entity_map
        ]
        callers_by_depth[depth] = summaries
        total_callers += len(summaries)

    max_depth_reached = max(callers_by_depth.keys()) if callers_by_depth else 0

    return CallersResponse(
        entity_id=entity_id,
        callers_by_depth=callers_by_depth,
        truncation=TruncationMetadata(
            truncated=any(len(ids) >= params.limit for ids in callers_by_depth_ids.values()),
            total_available=total_callers,  # Approximation
            node_count=total_callers,
            max_depth_requested=params.depth,
            max_depth_reached=max_depth_reached,
        ),
    )


async def get_callees_tool(
    session: AsyncSession,
    params: GetCalleesParams,
    graph: nx.MultiDiGraph,
) -> CalleesResponse:
    """
    Get callees (entities called by this entity).

    Forward traversal in dependency graph up to specified depth.

    Args:
        session: Database session
        params: Tool parameters
        graph: Dependency graph

    Returns:
        Callees grouped by depth with truncation metadata
    """
    log.info("get_callees tool invoked", entity_id=params.entity_id, depth=params.depth)

    entity_id = await resolve_entity_id(session, params.entity_id, params.signature)
    callees_by_depth_ids = get_callees_fn(graph, entity_id, params.depth, params.limit)

    # Batch-fetch all entity IDs across all depths
    all_ids = [eid for ids in callees_by_depth_ids.values() for eid in ids]
    entity_map = await fetch_entity_map(session, all_ids)

    # Build summaries per depth
    callees_by_depth: dict[int, list[EntitySummary]] = {}
    total_callees = 0

    for depth, entity_ids in callees_by_depth_ids.items():
        summaries = [
            entity_to_summary(entity_map[eid])
            for eid in entity_ids
            if eid in entity_map
        ]
        callees_by_depth[depth] = summaries
        total_callees += len(summaries)

    max_depth_reached = max(callees_by_depth.keys()) if callees_by_depth else 0

    return CalleesResponse(
        entity_id=entity_id,
        callees_by_depth=callees_by_depth,
        truncation=TruncationMetadata(
            truncated=any(len(ids) >= params.limit for ids in callees_by_depth_ids.values()),
            total_available=total_callees,
            node_count=total_callees,
            max_depth_requested=params.depth,
            max_depth_reached=max_depth_reached,
        ),
    )


async def get_dependencies_tool(
    session: AsyncSession,
    params: GetDependenciesParams,
    graph: nx.MultiDiGraph,
) -> DependenciesResponse:
    """
    Get filtered dependencies by relationship type and direction.

    Args:
        session: Database session
        params: Tool parameters
        graph: Dependency graph

    Returns:
        Dependencies with relationship and direction
    """
    log.info(
        "get_dependencies tool invoked",
        entity_id=params.entity_id,
        relationship=params.relationship,
        direction=params.direction,
    )

    entity_id = await resolve_entity_id(session, params.entity_id, params.signature)
    dependencies = []

    if entity_id not in graph:
        return DependenciesResponse(
            entity_id=entity_id,
            dependencies=[],
            truncation=TruncationMetadata(
                truncated=False,
                total_available=0,
                node_count=0,
            ),
        )

    # Collect all neighbor IDs with their edge metadata
    dep_records: list[tuple[str, str, str]] = []  # (entity_id, edge_type, direction)

    if params.direction in ("outgoing", "both"):
        for _, target, data in graph.out_edges(entity_id, data=True):
            edge_type = data.get("type", "")
            if params.relationship and edge_type != params.relationship:
                continue
            dep_records.append((target, edge_type, "outgoing"))

    if params.direction in ("incoming", "both"):
        for source, _, data in graph.in_edges(entity_id, data=True):
            edge_type = data.get("type", "")
            if params.relationship and edge_type != params.relationship:
                continue
            dep_records.append((source, edge_type, "incoming"))

    # Truncate before fetching
    truncated = len(dep_records) > params.limit
    dep_records = dep_records[:params.limit]

    # Batch-fetch all entities
    all_ids = list({r[0] for r in dep_records})
    entity_map = await fetch_entity_map(session, all_ids)

    for eid, edge_type, direction in dep_records:
        if eid in entity_map:
            dependencies.append({
                "entity": entity_to_summary(entity_map[eid]).model_dump(),
                "relationship": edge_type,
                "direction": direction,
            })

    return DependenciesResponse(
        entity_id=entity_id,
        dependencies=dependencies,
        truncation=TruncationMetadata(
            truncated=len(dependencies) >= params.limit,
            total_available=len(dependencies),
            node_count=len(dependencies),
        ),
    )


async def get_class_hierarchy_tool(
    session: AsyncSession,
    params: GetClassHierarchyParams,
    graph: nx.MultiDiGraph,
) -> ClassHierarchyResponse:
    """
    Get class hierarchy (base classes and derived classes).

    Args:
        session: Database session
        params: Tool parameters
        graph: Dependency graph

    Returns:
        Base and derived classes
    """
    log.info("get_class_hierarchy tool invoked", entity_id=params.entity_id)

    entity_id = await resolve_entity_id(session, params.entity_id, params.signature)
    hierarchy = get_class_hierarchy_fn(graph, entity_id)

    # Batch-fetch all entities
    all_ids = hierarchy["base_classes"] + hierarchy["derived_classes"]
    entity_map = await fetch_entity_map(session, all_ids)

    base_classes = [
        entity_to_summary(entity_map[eid])
        for eid in hierarchy["base_classes"]
        if eid in entity_map
    ]
    derived_classes = [
        entity_to_summary(entity_map[eid])
        for eid in hierarchy["derived_classes"]
        if eid in entity_map
    ]

    return ClassHierarchyResponse(
        entity_id=entity_id,
        base_classes=base_classes,
        derived_classes=derived_classes,
    )


async def get_related_entities_tool(
    session: AsyncSession,
    params: GetRelatedEntitiesParams,
    graph: nx.MultiDiGraph,
) -> RelatedEntitiesResponse:
    """
    Get all direct neighbors grouped by relationship type.

    Args:
        session: Database session
        params: Tool parameters
        graph: Dependency graph

    Returns:
        Neighbors grouped by relationship type
    """
    log.info("get_related_entities tool invoked", entity_id=params.entity_id)

    entity_id = await resolve_entity_id(session, params.entity_id, params.signature)

    if entity_id not in graph:
        return RelatedEntitiesResponse(
            entity_id=entity_id,
            neighbors_by_relationship={},
            truncation=TruncationMetadata(
                truncated=False,
                total_available=0,
                node_count=0,
            ),
        )

    neighbors_by_relationship: dict[str, list[EntitySummary]] = {}
    total_neighbors = 0

    # Collect all neighbor records
    all_neighbors: list[tuple[str, str, str]] = []  # (id, rel_type, direction)
    seen = set()

    for _, target, data in graph.out_edges(entity_id, data=True):
        key = (target, data.get("type", "unknown"), "outgoing")
        if key not in seen:
            seen.add(key)
            all_neighbors.append(key)

    for source, _, data in graph.in_edges(entity_id, data=True):
        key = (source, data.get("type", "unknown"), "incoming")
        if key not in seen:
            seen.add(key)
            all_neighbors.append(key)

    # Truncate before fetching
    all_neighbors = all_neighbors[:params.limit]

    # Batch-fetch all entities
    all_ids = list({n[0] for n in all_neighbors})
    entity_map = await fetch_entity_map(session, all_ids)

    for neighbor_id, rel_type, direction in all_neighbors:
        if neighbor_id in entity_map:
            key = f"{rel_type}_{direction}"
            if key not in neighbors_by_relationship:
                neighbors_by_relationship[key] = []
            neighbors_by_relationship[key].append(entity_to_summary(entity_map[neighbor_id]))
            total_neighbors += 1

    return RelatedEntitiesResponse(
        entity_id=entity_id,
        neighbors_by_relationship=neighbors_by_relationship,
        truncation=TruncationMetadata(
            truncated=total_neighbors >= params.limit,
            total_available=total_neighbors,
            node_count=total_neighbors,
        ),
    )


async def get_related_files_tool(
    session: AsyncSession,
    params: GetRelatedFilesParams,
    graph: nx.MultiDiGraph,
) -> RelatedFilesResponse:
    """
    Find related files via include relationships.

    Args:
        session: Database session
        params: Tool parameters
        graph: Dependency graph

    Returns:
        Related files with relationship metadata
    """
    log.info("get_related_files tool invoked", file_path=params.file_path)

    # Find file entities in this file
    from sqlmodel import select as sqlselect

    result = await session.execute(
        sqlselect(Entity).where(Entity.file_path == params.file_path).where(Entity.kind == "file")
    )
    file_entities = list(result.scalars().all())

    related_files_map: dict[str, dict] = {}

    # Collect all target IDs from INCLUDES edges
    target_ids: list[str] = []
    for file_entity in file_entities:
        entity_id = file_entity.entity_id
        if entity_id not in graph:
            continue
        for _, target, data in graph.out_edges(entity_id, data=True):
            if data.get("type") == "includes":
                target_ids.append(target)

    # Batch-fetch all target entities
    entity_map = await fetch_entity_map(session, target_ids)

    for target_id in target_ids:
        target_entity = entity_map.get(target_id)
        if target_entity and target_entity.file_path:
            if target_entity.file_path not in related_files_map:
                related_files_map[target_entity.file_path] = {
                    "file_path": target_entity.file_path,
                    "relationship": "includes",
                    "entity_count": 0,
                }
            related_files_map[target_entity.file_path]["entity_count"] += 1

    related_files = list(related_files_map.values())[:params.limit]

    return RelatedFilesResponse(
        file_path=params.file_path,
        related_files=related_files,
        truncation=TruncationMetadata(
            truncated=len(related_files_map) > params.limit,
            total_available=len(related_files_map),
            node_count=len(related_files),
        ),
    )
