"""
Graph Navigation Tools - callers, callees, dependencies, hierarchy, related.

Tools are decorated at module level with @mcp.tool() and remain directly importable.
"""

from typing import Annotated

from fastmcp import Context
from pydantic import BaseModel, Field
from sqlmodel import select

from server.app import get_ctx, mcp
from server.converters import entity_to_summary
from server.db_models import Entity
from server.enums import Relationship
from server.graph import (
    INCLUDES,
)
from server.graph import (
    get_callees as get_callees_fn,
)
from server.graph import (
    get_callers as get_callers_fn,
)
from server.graph import (
    get_class_hierarchy as get_class_hierarchy_fn,
)
from server.logging_config import log
from server.models import EntitySummary, TruncationMetadata
from server.util import fetch_entity_map

# -- Response Models --

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
    dependencies: list[dict]
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
    related_files: list[dict]
    truncation: TruncationMetadata


@mcp.tool()
async def get_callers(
    ctx: Context,
    entity_id: Annotated[str, Field(description="Entity ID")],
    depth: Annotated[int, Field(ge=1, le=3, description="Traversal depth (1-3)")] = 1,
    limit: Annotated[int, Field(ge=1, le=200, description="Max results per depth level")] = 50,
) -> CallersResponse:
    """
    Get callers (functions that call this entity). Backward graph traversal.
    """
    lc = get_ctx(ctx)
    graph = lc["graph"]

    log.info("get_callers", entity_id=entity_id, depth=depth)

    async with lc["db_manager"].session() as session:
        callers_by_depth_ids = get_callers_fn(graph, entity_id, depth, limit)

        all_ids = [eid for ids in callers_by_depth_ids.values() for eid in ids]
        entity_map = await fetch_entity_map(session, all_ids)

    callers_by_depth: dict[int, list[EntitySummary]] = {}
    total = 0
    for d, entity_ids in callers_by_depth_ids.items():
        summaries = [
            entity_to_summary(entity_map[e])
            for e in entity_ids if e in entity_map
        ]
        callers_by_depth[d] = summaries
        total += len(summaries)

    max_depth_reached = max(callers_by_depth.keys()) if callers_by_depth else 0

    return CallersResponse(
        entity_id=entity_id,
        callers_by_depth=callers_by_depth,
        truncation=TruncationMetadata(
            truncated=any(len(ids) >= limit for ids in callers_by_depth_ids.values()),
            total_available=total,
            node_count=total,
            max_depth_requested=depth,
            max_depth_reached=max_depth_reached,
        ),
    )


@mcp.tool()
async def get_callees(
    ctx: Context,
    entity_id: Annotated[str, Field(description="Entity ID")],
    depth: Annotated[int, Field(ge=1, le=3, description="Traversal depth (1-3)")] = 1,
    limit: Annotated[int, Field(ge=1, le=200, description="Max results per depth level")] = 50,
) -> CalleesResponse:
    """
    Get callees (functions called by this entity). Forward graph traversal.
    """
    lc = get_ctx(ctx)
    graph = lc["graph"]

    log.info("get_callees", entity_id=entity_id, depth=depth)

    async with lc["db_manager"].session() as session:
        callees_by_depth_ids = get_callees_fn(graph, entity_id, depth, limit)

        all_ids = [eid for ids in callees_by_depth_ids.values() for eid in ids]
        entity_map = await fetch_entity_map(session, all_ids)

    callees_by_depth: dict[int, list[EntitySummary]] = {}
    total = 0
    for d, entity_ids in callees_by_depth_ids.items():
        summaries = [
            entity_to_summary(entity_map[e])
            for e in entity_ids if e in entity_map
        ]
        callees_by_depth[d] = summaries
        total += len(summaries)

    max_depth_reached = max(callees_by_depth.keys()) if callees_by_depth else 0

    return CalleesResponse(
        entity_id=entity_id,
        callees_by_depth=callees_by_depth,
        truncation=TruncationMetadata(
            truncated=any(len(ids) >= limit for ids in callees_by_depth_ids.values()),
            total_available=total,
            node_count=total,
            max_depth_requested=depth,
            max_depth_reached=max_depth_reached,
        ),
    )


@mcp.tool()
async def get_dependencies(
    ctx: Context,
    entity_id: Annotated[str, Field(description="Entity ID")],
    relationship: Annotated[
        Relationship | None,
        Field(description="Filter by relationship type"),
    ] = None,
    direction: Annotated[
        str,
        Field(description="Edge direction: incoming, outgoing, both"),
    ] = "both",
    limit: Annotated[int, Field(ge=1, le=500, description="Maximum results")] = 100,
) -> DependenciesResponse:
    """
    Get filtered dependencies by relationship type and direction.

    Relationship types: calls, uses, inherits, includes, contained_by.
    Direction: incoming, outgoing, both.
    """
    lc = get_ctx(ctx)
    graph = lc["graph"]

    log.info("get_dependencies", entity_id=entity_id, relationship=relationship, direction=direction)

    async with lc["db_manager"].session() as session:
        if entity_id not in graph:
            return DependenciesResponse(
                entity_id=entity_id,
                dependencies=[],
                truncation=TruncationMetadata(
                    truncated=False, total_available=0, node_count=0,
                ),
            )

        dep_records: list[tuple[str, str, str]] = []

        if direction in ("outgoing", "both"):
            for _, target, data in graph.out_edges(entity_id, data=True):
                edge_type = data.get("type", "")
                if relationship and edge_type != relationship:
                    continue
                dep_records.append((target, edge_type, "outgoing"))

        if direction in ("incoming", "both"):
            for source, _, data in graph.in_edges(entity_id, data=True):
                edge_type = data.get("type", "")
                if relationship and edge_type != relationship:
                    continue
                dep_records.append((source, edge_type, "incoming"))

        dep_records = dep_records[:limit]

        all_ids = list({r[0] for r in dep_records})
        entity_map = await fetch_entity_map(session, all_ids)

    dependencies = []
    for dep_id, edge_type, dep_dir in dep_records:
        if dep_id in entity_map:
            dependencies.append({
                "entity": entity_to_summary(entity_map[dep_id]),
                "relationship": edge_type,
                "direction": dep_dir,
            })

    return DependenciesResponse(
        entity_id=entity_id,
        dependencies=dependencies,
        truncation=TruncationMetadata(
            truncated=len(dependencies) >= limit,
            total_available=len(dependencies),
            node_count=len(dependencies),
        ),
    )


@mcp.tool()
async def get_class_hierarchy(
    ctx: Context,
    entity_id: Annotated[str, Field(description="Class entity ID")],
) -> ClassHierarchyResponse:
    """
    Get class hierarchy (base classes and derived classes).
    """
    lc = get_ctx(ctx)
    graph = lc["graph"]

    log.info("get_class_hierarchy", entity_id=entity_id)

    async with lc["db_manager"].session() as session:
        hierarchy = get_class_hierarchy_fn(graph, entity_id)

        all_ids = hierarchy["base_classes"] + hierarchy["derived_classes"]
        entity_map = await fetch_entity_map(session, all_ids)

    base_classes = [
        entity_to_summary(entity_map[e])
        for e in hierarchy["base_classes"] if e in entity_map
    ]
    derived_classes = [
        entity_to_summary(entity_map[e])
        for e in hierarchy["derived_classes"] if e in entity_map
    ]

    return ClassHierarchyResponse(
        entity_id=entity_id,
        base_classes=base_classes,
        derived_classes=derived_classes,
    )


@mcp.tool()
async def get_related_entities(
    ctx: Context,
    entity_id: Annotated[str, Field(description="Entity ID")],
    limit: Annotated[int, Field(ge=1, le=500, description="Maximum results")] = 100,
) -> RelatedEntitiesResponse:
    """
    Get all direct neighbors grouped by relationship type.
    """
    lc = get_ctx(ctx)
    graph = lc["graph"]

    log.info("get_related_entities", entity_id=entity_id)

    async with lc["db_manager"].session() as session:
        if entity_id not in graph:
            return RelatedEntitiesResponse(
                entity_id=entity_id,
                neighbors_by_relationship={},
                truncation=TruncationMetadata(
                    truncated=False, total_available=0, node_count=0,
                ),
            )

        all_neighbors: list[tuple[str, str, str]] = []
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

        all_neighbors = all_neighbors[:limit]

        all_ids = list({n[0] for n in all_neighbors})
        entity_map = await fetch_entity_map(session, all_ids)

    neighbors_by_relationship: dict[str, list[EntitySummary]] = {}
    total = 0
    for neighbor_id, rel_type, direction in all_neighbors:
        if neighbor_id in entity_map:
            key = f"{rel_type}_{direction}"
            neighbors_by_relationship.setdefault(key, []).append(
                entity_to_summary(entity_map[neighbor_id])
            )
            total += 1

    return RelatedEntitiesResponse(
        entity_id=entity_id,
        neighbors_by_relationship=neighbors_by_relationship,
        truncation=TruncationMetadata(
            truncated=total >= limit,
            total_available=total,
            node_count=total,
        ),
    )


@mcp.tool()
async def get_related_files(
    ctx: Context,
    file_path: Annotated[str, Field(description="Source file path")],
    limit: Annotated[int, Field(ge=1, le=200, description="Maximum results")] = 50,
) -> RelatedFilesResponse:
    """
    Find related files via include relationships.
    """
    lc = get_ctx(ctx)
    graph = lc["graph"]

    log.info("get_related_files", file_path=file_path)

    async with lc["db_manager"].session() as session:
        result = await session.execute(
            select(Entity).where(Entity.file_path == file_path).where(Entity.kind == "file")
        )
        file_entities = list(result.scalars().all())

        target_ids: list[str] = []
        for fe in file_entities:
            if fe.entity_id not in graph:
                continue
            for _, target, data in graph.out_edges(fe.entity_id, data=True):
                if data.get("type") == INCLUDES:
                    target_ids.append(target)

        entity_map = await fetch_entity_map(session, target_ids)

    related_map: dict[str, dict] = {}
    for target_id in target_ids:
        te = entity_map.get(target_id)
        if te and te.file_path:
            if te.file_path not in related_map:
                related_map[te.file_path] = {
                    "file_path": te.file_path,
                    "relationship": INCLUDES,
                    "entity_count": 0,
                }
            related_map[te.file_path]["entity_count"] += 1

    related_files = list(related_map.values())[:limit]

    return RelatedFilesResponse(
        file_path=file_path,
        related_files=related_files,
        truncation=TruncationMetadata(
            truncated=len(related_map) > limit,
            total_available=len(related_map),
            node_count=len(related_files),
        ),
    )
