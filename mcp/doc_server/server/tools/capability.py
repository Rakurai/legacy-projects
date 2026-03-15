"""
Capability System Tools - Capability navigation, entry point analysis, comparison.

Tools:
- list_capabilities: List all capability groups with metadata
- get_capability_detail: Get detailed capability info including dependencies
- compare_capabilities: Compare multiple capabilities
- list_entry_points: List entry points filterable by capability
- get_entry_point_info: Analyze which capabilities an entry point exercises
"""

import networkx as nx
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from server.db_models import Capability, CapabilityEdge, Entity, EntryPoint
from server.errors import CapabilityNotFoundError, EntityNotFoundError
from server.logging_config import log
from server.models import (
    CapabilityDetail,
    CapabilitySummary,
    EntitySummary,
    TruncationMetadata,
)
from server.util import parse_json_field, resolve_entity_id
from server.resolver import entity_to_summary

# ---------- Parameter Models ----------

class ListCapabilitiesParams(BaseModel):
    """Parameters for list_capabilities tool (no params)."""
    pass


class GetCapabilityDetailParams(BaseModel):
    """Parameters for get_capability_detail tool."""
    capability: str = Field(description="Capability name")
    include_functions: bool = Field(
        default=False,
        description="Include full function list (may be large)"
    )


class CompareCapabilitiesParams(BaseModel):
    """Parameters for compare_capabilities tool."""
    capabilities: list[str] = Field(
        min_length=2,
        description="2+ capability names to compare"
    )
    limit: int = Field(default=50, ge=1, le=200, description="Maximum results per section")


class ListEntryPointsParams(BaseModel):
    """Parameters for list_entry_points tool."""
    capability: str | None = Field(default=None, description="Filter by capability")
    name_pattern: str | None = Field(default=None, description="SQL LIKE pattern (e.g. 'do_look%')")
    limit: int = Field(default=100, ge=1, le=500, description="Maximum results")


class GetEntryPointInfoParams(BaseModel):
    """Parameters for get_entry_point_info tool."""
    entity_id: str | None = Field(default=None, description="Entry point entity ID")
    signature: str | None = Field(default=None, description="Entity signature (alternative to entity_id)")


# ---------- Response Models ----------

class ListCapabilitiesResponse(BaseModel):
    """Response from list_capabilities tool."""
    capabilities: list[CapabilitySummary]


class GetCapabilityDetailResponse(BaseModel):
    """Response from get_capability_detail tool."""
    detail: CapabilityDetail


class CompareCapabilitiesResponse(BaseModel):
    """Response from compare_capabilities tool."""
    capabilities: list[str]
    shared_dependencies: list[EntitySummary]
    unique_dependencies: dict[str, list[EntitySummary]]
    bridge_entities: list[EntitySummary]
    truncation: TruncationMetadata


class ListEntryPointsResponse(BaseModel):
    """Response from list_entry_points tool."""
    entry_points: list[EntitySummary]
    truncation: TruncationMetadata


class EntryPointInfoResponse(BaseModel):
    """Response from get_entry_point_info tool."""
    entry_point: EntitySummary
    capabilities_exercised: dict[str, dict]  # cap_name → {direct_count, transitive_count}


# ---------- Helpers ----------


def _capability_to_summary(cap: Capability) -> CapabilitySummary:
    """Convert Capability DB model to CapabilitySummary."""
    dqd = parse_json_field(cap.doc_quality_dist)
    if not isinstance(dqd, dict):
        dqd = {"high": 0, "medium": 0, "low": 0}
    return CapabilitySummary(
        name=cap.name,
        type=cap.type,  # type: ignore
        description=cap.description,
        function_count=cap.function_count,
        stability=cap.stability,
        doc_quality_dist=dqd,
        provenance="precomputed",
    )


# ---------- Tool Implementations ----------

async def list_capabilities_tool(
    session: AsyncSession,
    params: ListCapabilitiesParams,
) -> ListCapabilitiesResponse:
    """
    List all capability groups with metadata.

    Args:
        session: Database session
        params: Tool parameters (empty)

    Returns:
        ListCapabilitiesResponse with all capabilities
    """
    log.info("list_capabilities tool invoked")

    result = await session.execute(
        select(Capability).order_by(Capability.name)
    )
    capabilities = list(result.scalars().all())

    summaries = [_capability_to_summary(cap) for cap in capabilities]

    return ListCapabilitiesResponse(capabilities=summaries)


async def get_capability_detail_tool(
    session: AsyncSession,
    params: GetCapabilityDetailParams,
) -> GetCapabilityDetailResponse:
    """
    Get detailed capability information including dependencies and entry points.

    Args:
        session: Database session
        params: Tool parameters

    Returns:
        GetCapabilityDetailResponse with full capability info
    """
    log.info("get_capability_detail tool invoked", capability=params.capability)

    cap = await session.get(Capability, params.capability)
    if not cap:
        raise CapabilityNotFoundError(params.capability)

    # Get capability edges (dependencies)
    edge_result = await session.execute(
        select(CapabilityEdge).where(CapabilityEdge.source_cap == params.capability)
    )
    edges = list(edge_result.scalars().all())
    dependencies = [
        {
            "target_capability": e.target_cap,
            "edge_type": e.edge_type,
            "call_count": e.call_count,
        }
        for e in edges
    ]

    # Get entry points for this capability
    ep_result = await session.execute(
        select(EntryPoint)
        .join(Entity, Entity.entity_id == EntryPoint.entity_id)
        .where(Entity.capability == params.capability)
        .order_by(EntryPoint.name)
    )
    entry_points = [ep.name for ep in ep_result.scalars().all()]

    # Optional: include full function list
    functions: list[EntitySummary] | None = None
    if params.include_functions:
        func_result = await session.execute(
            select(Entity)
            .where(Entity.capability == params.capability)
            .order_by(Entity.fan_in.desc())
        )
        func_entities = list(func_result.scalars().all())
        functions = [entity_to_summary(e) for e in func_entities]

    dqd = parse_json_field(cap.doc_quality_dist)
    if not isinstance(dqd, dict):
        dqd = {"high": 0, "medium": 0, "low": 0}

    detail = CapabilityDetail(
        name=cap.name,
        type=cap.type,
        description=cap.description,
        function_count=cap.function_count,
        stability=cap.stability,
        doc_quality_dist=dqd,
        dependencies=dependencies,
        entry_points=entry_points,
        functions=functions,
        provenance="precomputed",
    )

    return GetCapabilityDetailResponse(detail=detail)


async def compare_capabilities_tool(
    session: AsyncSession,
    params: CompareCapabilitiesParams,
    graph: nx.MultiDiGraph,
) -> CompareCapabilitiesResponse:
    """
    Compare multiple capabilities: shared/unique dependencies and bridge entities.

    Args:
        session: Database session
        params: Tool parameters
        graph: Dependency graph

    Returns:
        CompareCapabilitiesResponse with comparison data
    """
    log.info("compare_capabilities tool invoked", capabilities=params.capabilities)

    # Fetch all entities for each capability
    cap_entities: dict[str, set[str]] = {}  # cap_name → set of entity_ids
    all_entity_ids: set[str] = set()

    for cap_name in params.capabilities:
        result = await session.execute(
            select(Entity.entity_id).where(Entity.capability == cap_name)
        )
        entity_ids = set(result.scalars().all())
        cap_entities[cap_name] = entity_ids
        all_entity_ids |= entity_ids

    # Compute shared vs unique
    if len(params.capabilities) < 2:
        raise ValueError("At least 2 capabilities required for comparison")

    # For each entity, find which capabilities' functions call it
    # "shared dependency" = entity called by functions from multiple capabilities
    entity_callers_caps: dict[str, set[str]] = {}  # entity_id → set of cap names that call it

    for cap_name, eids in cap_entities.items():
        for eid in eids:
            if eid not in graph:
                continue
            for _, target, data in graph.out_edges(eid, data=True):
                if data.get("type") == "calls":
                    if target not in entity_callers_caps:
                        entity_callers_caps[target] = set()
                    entity_callers_caps[target].add(cap_name)

    # Shared: called by 2+ of the compared capabilities
    shared_ids = [
        eid for eid, caps in entity_callers_caps.items()
        if len(caps & set(params.capabilities)) >= 2
    ][:params.limit]

    # Unique: called only by one of the compared capabilities
    unique_ids: dict[str, list[str]] = {cap: [] for cap in params.capabilities}
    for eid, caps in entity_callers_caps.items():
        matching = caps & set(params.capabilities)
        if len(matching) == 1:
            cap_name = next(iter(matching))
            if len(unique_ids[cap_name]) < params.limit:
                unique_ids[cap_name].append(eid)

    # Bridge entities: entities that belong to one compared cap but are called by another
    bridge_ids: list[str] = []
    for eid, caps in entity_callers_caps.items():
        # Check if entity belongs to one of the compared caps
        for cap_name, eids in cap_entities.items():
            if eid in eids:
                # Entity is in cap_name, check if called by a different compared cap
                other_caps = caps - {cap_name}
                if other_caps & set(params.capabilities):
                    bridge_ids.append(eid)
                    break
        if len(bridge_ids) >= params.limit:
            break

    # Fetch summaries
    all_fetch_ids = set(shared_ids) | set(bridge_ids)
    for ids in unique_ids.values():
        all_fetch_ids |= set(ids)

    entity_map: dict[str, Entity] = {}
    if all_fetch_ids:
        result = await session.execute(
            select(Entity).where(Entity.entity_id.in_(list(all_fetch_ids)))
        )
        entity_map = {e.entity_id: e for e in result.scalars().all()}

    shared_summaries = [
        entity_to_summary(entity_map[eid])
        for eid in shared_ids if eid in entity_map
    ]

    unique_summaries: dict[str, list[EntitySummary]] = {}
    for cap_name, ids in unique_ids.items():
        unique_summaries[cap_name] = [
            entity_to_summary(entity_map[eid])
            for eid in ids if eid in entity_map
        ]

    bridge_summaries = [
        entity_to_summary(entity_map[eid])
        for eid in bridge_ids if eid in entity_map
    ]

    total = len(shared_summaries) + sum(len(v) for v in unique_summaries.values()) + len(bridge_summaries)

    return CompareCapabilitiesResponse(
        capabilities=params.capabilities,
        shared_dependencies=shared_summaries,
        unique_dependencies=unique_summaries,
        bridge_entities=bridge_summaries,
        truncation=TruncationMetadata(
            truncated=False,
            total_available=total,
            node_count=total,
        ),
    )


async def list_entry_points_tool(
    session: AsyncSession,
    params: ListEntryPointsParams,
) -> ListEntryPointsResponse:
    """
    List entry points filterable by capability and name pattern.

    Args:
        session: Database session
        params: Tool parameters

    Returns:
        ListEntryPointsResponse with entry point summaries
    """
    log.info(
        "list_entry_points tool invoked",
        capability=params.capability,
        name_pattern=params.name_pattern,
    )

    # Start with entity query for entry points
    stmt = (
        select(Entity)
        .where(Entity.is_entry_point == True)  # noqa: E712
    )

    if params.capability:
        stmt = stmt.where(Entity.capability == params.capability)

    if params.name_pattern:
        stmt = stmt.where(Entity.name.like(params.name_pattern))

    stmt = stmt.order_by(Entity.name).limit(params.limit)

    result = await session.execute(stmt)
    entities = list(result.scalars().all())

    summaries = [entity_to_summary(e) for e in entities]

    return ListEntryPointsResponse(
        entry_points=summaries,
        truncation=TruncationMetadata(
            truncated=len(entities) >= params.limit,
            total_available=len(entities),
            node_count=len(entities),
        ),
    )


async def get_entry_point_info_tool(
    session: AsyncSession,
    params: GetEntryPointInfoParams,
    graph: nx.MultiDiGraph,
) -> EntryPointInfoResponse:
    """
    Analyze which capabilities an entry point exercises (direct and transitive).

    Args:
        session: Database session
        params: Tool parameters
        graph: Dependency graph

    Returns:
        EntryPointInfoResponse with capability exercise data
    """
    log.info("get_entry_point_info tool invoked", entity_id=params.entity_id)

    entity_id = await resolve_entity_id(session, params.entity_id, params.signature)

    entity = await session.get(Entity, entity_id)
    if not entity:
        raise EntityNotFoundError(entity_id)

    if not entity.is_entry_point:
        raise ValueError(f"Entity is not an entry point: {entity_id}")

    ep_summary = entity_to_summary(entity)

    # Compute call cone (depth=5) to find all capabilities exercised
    from server.graph import compute_call_cone
    cone = compute_call_cone(graph, entity_id, max_depth=5, max_size=200)

    direct_ids = cone["direct"]
    transitive_ids = cone["transitive"]
    all_ids = direct_ids + transitive_ids

    # Fetch capability info for all cone entities
    if all_ids:
        result = await session.execute(
            select(Entity.entity_id, Entity.capability)
            .where(Entity.entity_id.in_(all_ids))
            .where(Entity.capability.isnot(None))
        )
        rows = result.all()
    else:
        rows = []

    # Build capability exercise map
    cap_exercise: dict[str, dict] = {}
    direct_set = set(direct_ids)

    for eid, cap in rows:
        if cap not in cap_exercise:
            cap_exercise[cap] = {
                "capability": cap,
                "direct_count": 0,
                "transitive_count": 0,
            }
        if eid in direct_set:
            cap_exercise[cap]["direct_count"] += 1
        else:
            cap_exercise[cap]["transitive_count"] += 1

    return EntryPointInfoResponse(
        entry_point=ep_summary,
        capabilities_exercised=cap_exercise,
    )
