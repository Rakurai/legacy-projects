"""
Graph Navigation Tools - callers, callees, dependencies, hierarchy, related.

Tools are decorated at module level with @mcp.tool() and remain directly importable.
"""

from typing import Annotated, Literal

from fastmcp import Context
from pydantic import BaseModel, Field

from server.app import get_ctx, mcp
from server.converters import entity_to_summary
from server.enums import Relationship
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
        summaries = [entity_to_summary(entity_map[e]) for e in entity_ids if e in entity_map]
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
        summaries = [entity_to_summary(entity_map[e]) for e in entity_ids if e in entity_map]
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
    ] = "outgoing",
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
                    truncated=False,
                    total_available=0,
                    node_count=0,
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
            dependencies.append(
                {
                    "entity": entity_to_summary(entity_map[dep_id]),
                    "relationship": edge_type,
                    "direction": dep_dir,
                }
            )

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
    direction: Annotated[
        Literal["ancestors", "descendants", "both"],
        Field(description="Which direction: ancestors, descendants, or both"),
    ] = "both",
) -> ClassHierarchyResponse:
    """
    Get class hierarchy (base classes and derived classes).

    direction: 'ancestors' (base classes only), 'descendants' (derived only), 'both'.
    """
    lc = get_ctx(ctx)
    graph = lc["graph"]

    log.info("get_class_hierarchy", entity_id=entity_id, direction=direction)

    async with lc["db_manager"].session() as session:
        hierarchy = get_class_hierarchy_fn(graph, entity_id)

        base_ids = hierarchy["base_classes"] if direction in ("ancestors", "both") else []
        derived_ids = hierarchy["derived_classes"] if direction in ("descendants", "both") else []
        all_ids = base_ids + derived_ids
        entity_map = await fetch_entity_map(session, all_ids)

    base_classes = [entity_to_summary(entity_map[e]) for e in base_ids if e in entity_map]
    derived_classes = [entity_to_summary(entity_map[e]) for e in derived_ids if e in entity_map]

    return ClassHierarchyResponse(
        entity_id=entity_id,
        base_classes=base_classes,
        derived_classes=derived_classes,
    )


@mcp.tool()
async def get_related_entities(
    ctx: Context,
    entity_id: Annotated[str, Field(description="Entity ID")],
    limit_per_type: Annotated[int, Field(ge=1, le=500, description="Maximum results per relationship group")] = 20,
) -> RelatedEntitiesResponse:
    """
    Get all direct neighbors grouped by relationship type.

    Results are capped per relationship group (limit_per_type).
    """
    lc = get_ctx(ctx)
    graph = lc["graph"]

    log.info("get_related_entities", entity_id=entity_id, limit_per_type=limit_per_type)

    async with lc["db_manager"].session() as session:
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

        # Collect all neighbors, grouped by relationship key
        groups: dict[str, list[str]] = {}

        for _, target, data in graph.out_edges(entity_id, data=True):
            key = f"{data.get('type', 'unknown')}_outgoing"
            groups.setdefault(key, []).append(target)

        for source, _, data in graph.in_edges(entity_id, data=True):
            key = f"{data.get('type', 'unknown')}_incoming"
            groups.setdefault(key, []).append(source)

        # Collect unique IDs for DB fetch (all groups, pre-truncation)
        all_ids = list({eid for ids in groups.values() for eid in ids})
        entity_map = await fetch_entity_map(session, all_ids)

    # Truncate per group and build response
    truncated = False
    neighbors_by_relationship: dict[str, list[EntitySummary]] = {}
    total_available = 0
    total_returned = 0

    for key, neighbor_ids in groups.items():
        # Deduplicate within group
        seen: set[str] = set()
        unique_ids: list[str] = []
        for nid in neighbor_ids:
            if nid not in seen:
                seen.add(nid)
                unique_ids.append(nid)

        total_available += len(unique_ids)

        if len(unique_ids) > limit_per_type:
            truncated = True
            unique_ids = unique_ids[:limit_per_type]

        summaries = [entity_to_summary(entity_map[nid]) for nid in unique_ids if nid in entity_map]
        if summaries:
            neighbors_by_relationship[key] = summaries
            total_returned += len(summaries)

    return RelatedEntitiesResponse(
        entity_id=entity_id,
        neighbors_by_relationship=neighbors_by_relationship,
        truncation=TruncationMetadata(
            truncated=truncated,
            total_available=total_available,
            node_count=total_returned,
        ),
    )
