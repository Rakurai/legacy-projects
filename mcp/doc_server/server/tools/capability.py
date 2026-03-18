"""
Capability System Tools - list, detail, compare, entry points.

Tools are decorated at module level with @mcp.tool() and remain directly importable.
"""

from typing import Annotated

from fastmcp import Context
from pydantic import BaseModel, Field
from sqlmodel import select

from server.app import get_ctx, mcp
from server.converters import capability_to_summary, entity_to_summary
from server.db_models import Capability, CapabilityEdge, Entity, EntryPoint
from server.errors import CapabilityNotFoundError, EntityNotFoundError
from server.graph import CALLS, compute_call_cone
from server.logging_config import log
from server.models import (
    CapabilityDetail,
    CapabilitySummary,
    EntitySummary,
    TruncationMetadata,
)

# -- Response Models --

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
    capabilities_exercised: dict[str, dict]


@mcp.tool()
async def list_capabilities(ctx: Context) -> ListCapabilitiesResponse:
    """
    List all capability groups with metadata.

    Returns all 30 capability groups with type, description,
    function count, stability, and doc quality distribution.
    """
    lc = get_ctx(ctx)

    log.info("list_capabilities")

    async with lc["db_manager"].session() as session:
        result = await session.execute(
            select(Capability).order_by(Capability.name)
        )
        capabilities = list(result.scalars().all())

    return ListCapabilitiesResponse(
        capabilities=[capability_to_summary(cap) for cap in capabilities],
    )


@mcp.tool()
async def get_capability_detail(
    ctx: Context,
    capability: Annotated[str, Field(description="Capability name (e.g., combat, magic, persistence)")],
    include_functions: Annotated[bool, Field(description="Include full function list (may be large)")] = False,
) -> GetCapabilityDetailResponse:
    """
    Get detailed capability information with dependencies and entry points.
    """
    lc = get_ctx(ctx)

    log.info("get_capability_detail", capability=capability)

    async with lc["db_manager"].session() as session:
        cap = await session.get(Capability, capability)
        if not cap:
            raise CapabilityNotFoundError(capability)

        edge_result = await session.execute(
            select(CapabilityEdge).where(CapabilityEdge.source_cap == capability)
        )
        edges = list(edge_result.scalars().all())
        dependencies = [
            {"target_capability": e.target_cap, "edge_type": e.edge_type, "call_count": e.call_count}
            for e in edges
        ]

        ep_result = await session.execute(
            select(EntryPoint)
            .join(Entity, Entity.entity_id == EntryPoint.entity_id)
            .where(Entity.capability == capability)
            .order_by(EntryPoint.name)
        )
        entry_points = [ep.name for ep in ep_result.scalars().all()]

        functions: list[EntitySummary] | None = None
        if include_functions:
            func_result = await session.execute(
                select(Entity)
                .where(Entity.capability == capability)
                .order_by(Entity.fan_in.desc())
            )
            func_entities = list(func_result.scalars().all())
            functions = [entity_to_summary(e) for e in func_entities]

    detail = CapabilityDetail(
        name=cap.name,
        type=cap.type,
        description=cap.description,
        function_count=cap.function_count,
        stability=cap.stability,
        dependencies=dependencies,
        entry_points=entry_points,
        functions=functions,
        provenance="precomputed",
    )

    return GetCapabilityDetailResponse(detail=detail)


@mcp.tool()
async def compare_capabilities(
    ctx: Context,
    capabilities: Annotated[list[str], Field(min_length=2, description="2+ capability names to compare")],
    limit: Annotated[int, Field(ge=1, le=200, description="Maximum results per section")] = 50,
) -> CompareCapabilitiesResponse:
    """
    Compare capabilities: shared/unique dependencies and bridge entities.
    """
    lc = get_ctx(ctx)
    graph = lc["graph"]

    log.info("compare_capabilities", capabilities=capabilities)

    if len(capabilities) < 2:  # noqa: PLR2004  — minimum pair required
        raise ValueError("At least 2 capabilities required for comparison")

    async with lc["db_manager"].session() as session:
        cap_entities: dict[str, set[str]] = {}
        all_entity_ids: set[str] = set()

        for cap_name in capabilities:
            result = await session.execute(
                select(Entity.entity_id).where(Entity.capability == cap_name)
            )
            entity_ids = set(result.scalars().all())
            cap_entities[cap_name] = entity_ids
            all_entity_ids |= entity_ids

        entity_callers_caps: dict[str, set[str]] = {}
        for cap_name, eids in cap_entities.items():
            for eid in eids:
                if eid not in graph:
                    continue
                for _, target, data in graph.out_edges(eid, data=True):
                    if data.get("type") == CALLS:
                        entity_callers_caps.setdefault(target, set()).add(cap_name)

        cap_set = set(capabilities)
        shared_ids = [
            eid for eid, caps in entity_callers_caps.items()
            if len(caps & cap_set) >= 2  # noqa: PLR2004  — shared = used by ≥2
        ][:limit]

        unique_ids: dict[str, list[str]] = {cap: [] for cap in capabilities}
        for eid, caps in entity_callers_caps.items():
            matching = caps & cap_set
            if len(matching) == 1:
                cap_name = next(iter(matching))
                if len(unique_ids[cap_name]) < limit:
                    unique_ids[cap_name].append(eid)

        bridge_ids: list[str] = []
        for eid, caps in entity_callers_caps.items():
            for cap_name, eids in cap_entities.items():
                if eid in eids:
                    other_caps = caps - {cap_name}
                    if other_caps & cap_set:
                        bridge_ids.append(eid)
                        break
            if len(bridge_ids) >= limit:
                break

        all_fetch_ids = set(shared_ids) | set(bridge_ids)
        for ids in unique_ids.values():
            all_fetch_ids |= set(ids)

        entity_map: dict[str, Entity] = {}
        if all_fetch_ids:
            result = await session.execute(
                select(Entity).where(Entity.entity_id.in_(list(all_fetch_ids)))
            )
            entity_map = {e.entity_id: e for e in result.scalars().all()}

    shared = [entity_to_summary(entity_map[e]) for e in shared_ids if e in entity_map]
    unique: dict[str, list[EntitySummary]] = {}
    for cap_name, ids in unique_ids.items():
        unique[cap_name] = [entity_to_summary(entity_map[e]) for e in ids if e in entity_map]
    bridges = [entity_to_summary(entity_map[e]) for e in bridge_ids if e in entity_map]

    total = len(shared) + sum(len(v) for v in unique.values()) + len(bridges)

    return CompareCapabilitiesResponse(
        capabilities=capabilities,
        shared_dependencies=shared,
        unique_dependencies=unique,
        bridge_entities=bridges,
        truncation=TruncationMetadata(
            truncated=False, total_available=total, node_count=total,
        ),
    )


@mcp.tool()
async def list_entry_points(
    ctx: Context,
    capability: Annotated[str | None, Field(description="Optional capability filter")] = None,
    name_pattern: Annotated[str | None, Field(description="SQL LIKE pattern (e.g., 'do_look%')")] = None,
    limit: Annotated[int, Field(ge=1, le=500, description="Maximum results")] = 100,
) -> ListEntryPointsResponse:
    """
    List entry points (do_*, spell_*, spec_* functions).
    """
    lc = get_ctx(ctx)

    log.info("list_entry_points", capability=capability, name_pattern=name_pattern)

    async with lc["db_manager"].session() as session:
        stmt = select(Entity).where(Entity.is_entry_point == True)  # noqa: E712
        if capability:
            stmt = stmt.where(Entity.capability == capability)
        if name_pattern:
            stmt = stmt.where(Entity.name.like(name_pattern))
        stmt = stmt.order_by(Entity.name).limit(limit)

        result = await session.execute(stmt)
        entities = list(result.scalars().all())

    summaries = [entity_to_summary(e) for e in entities]

    return ListEntryPointsResponse(
        entry_points=summaries,
        truncation=TruncationMetadata(
            truncated=len(entities) >= limit,
            total_available=len(entities),
            node_count=len(entities),
        ),
    )


@mcp.tool()
async def get_entry_point_info(
    ctx: Context,
    entity_id: Annotated[str, Field(description="Entry point entity ID")],
) -> EntryPointInfoResponse:
    """
    Analyze which capabilities an entry point exercises.
    """
    lc = get_ctx(ctx)
    graph = lc["graph"]

    log.info("get_entry_point_info", entity_id=entity_id)

    async with lc["db_manager"].session() as session:
        entity = await session.get(Entity, entity_id)
        if not entity:
            raise EntityNotFoundError(entity_id)
        if not entity.is_entry_point:
            raise ValueError(f"Entity is not an entry point: {entity_id}")

        ep_summary = entity_to_summary(entity)

        cone = compute_call_cone(graph, entity_id, max_depth=5, max_size=200)
        direct_ids = cone["direct"]
        transitive_ids = cone["transitive"]
        all_ids = direct_ids + transitive_ids

        rows = []
        if all_ids:
            result = await session.execute(
                select(Entity.entity_id, Entity.capability)
                .where(Entity.entity_id.in_(all_ids))
                .where(Entity.capability.isnot(None))
            )
            rows = result.all()

    cap_exercise: dict[str, dict] = {}
    direct_set = set(direct_ids)
    for row_eid, cap in rows:
        if cap not in cap_exercise:
            cap_exercise[cap] = {"capability": cap, "direct_count": 0, "transitive_count": 0}
        if row_eid in direct_set:
            cap_exercise[cap]["direct_count"] += 1
        else:
            cap_exercise[cap]["transitive_count"] += 1

    return EntryPointInfoResponse(
        entry_point=ep_summary,
        capabilities_exercised=cap_exercise,
    )
