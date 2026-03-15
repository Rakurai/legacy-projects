"""
Behavioral Analysis Tools - Call cone, state touches, and hotspot detection.

Tools:
- get_behavior_slice: Compute transitive call cone with capabilities touched,
  globals used, and side effects
- get_state_touches: Analyze direct/transitive global variable usage and side effects
- get_hotspots: Find architectural hotspots ranked by metric
"""

from typing import Literal

import networkx as nx
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from server.db_models import Entity
from server.errors import EntityNotFoundError
from server.graph import compute_call_cone
from server.logging_config import log
from server.models import (
    BehaviorSlice,
    CapabilityTouch,
    EntitySummary,
    GlobalTouch,
    SideEffectMarker,
    TruncationMetadata,
)
from server.resolver import entity_to_summary
from server.util import parse_json_field, fetch_entity_summaries, resolve_entity_id

# ---------- Parameter Models ----------

class GetBehaviorSliceParams(BaseModel):
    """Parameters for get_behavior_slice tool."""
    entity_id: str | None = Field(default=None, description="Seed entity ID")
    signature: str | None = Field(default=None, description="Entity signature (alternative to entity_id)")
    max_depth: int = Field(default=5, ge=1, le=10, description="Maximum traversal depth")
    max_cone_size: int = Field(default=200, ge=1, le=1000, description="Maximum cone size")


class GetStateTouchesParams(BaseModel):
    """Parameters for get_state_touches tool."""
    entity_id: str | None = Field(default=None, description="Entity ID")
    signature: str | None = Field(default=None, description="Entity signature (alternative to entity_id)")


class GetHotspotsParams(BaseModel):
    """Parameters for get_hotspots tool."""
    metric: Literal["fan_in", "fan_out", "bridge", "underdocumented"] = Field(
        description="Metric to rank by"
    )
    kind: str | None = Field(default=None, description="Optional kind filter")
    capability: str | None = Field(default=None, description="Optional capability filter")
    limit: int = Field(default=20, ge=1, le=100, description="Maximum results")


# ---------- Response Models ----------

class BehaviorSliceResponse(BaseModel):
    """Response from get_behavior_slice tool."""
    behavior: BehaviorSlice
    truncation: TruncationMetadata


class StateTouchesResponse(BaseModel):
    """Response from get_state_touches tool."""
    entity_id: str
    signature: str
    direct_uses: list[EntitySummary]
    direct_side_effects: list[SideEffectMarker]
    transitive_uses: list[EntitySummary]
    transitive_side_effects: list[SideEffectMarker]


class HotspotsResponse(BaseModel):
    """Response from get_hotspots tool."""
    metric: str
    hotspots: list[EntitySummary]
    truncation: TruncationMetadata


# ---------- Helpers ----------


def _extract_side_effects_for_entities(
    entities: dict[str, Entity],
    entity_ids: list[str],
    access_type: Literal["direct", "transitive"],
) -> list[SideEffectMarker]:
    """Extract side effect markers from a set of entities."""
    markers: list[SideEffectMarker] = []
    for eid in entity_ids:
        entity = entities.get(eid)
        if not entity:
            continue
        sem = parse_json_field(entity.side_effect_markers)
        if not sem or not isinstance(sem, dict):
            continue
        for category, functions in sem.items():
            if category not in ("messaging", "persistence", "state_mutation", "scheduling"):
                continue
            if isinstance(functions, list):
                for _ in functions:
                    markers.append(SideEffectMarker(
                        function_id=eid,
                        function_name=entity.name or eid,
                        category=category,  # type: ignore
                        access_type=access_type,
                        confidence="direct" if access_type == "direct" else "transitive",
                        provenance="heuristic",
                    ))
                    break  # One marker per category per entity
    return markers


# ---------- Tool Implementations ----------

async def get_behavior_slice_tool(
    session: AsyncSession,
    params: GetBehaviorSliceParams,
    graph: nx.MultiDiGraph,
) -> BehaviorSliceResponse:
    """
    Compute transitive call cone with capabilities touched, globals used, side effects.

    Per FR-053: groups by depth but does NOT return explicit wave arrays.

    Args:
        session: Database session
        params: Tool parameters
        graph: Dependency graph

    Returns:
        BehaviorSliceResponse with full analysis
    """
    log.info(
        "get_behavior_slice tool invoked",
        entity_id=params.entity_id,
        max_depth=params.max_depth,
        max_cone_size=params.max_cone_size,
    )

    # Resolve entity_id from entity_id or signature
    entity_id = await resolve_entity_id(session, params.entity_id, params.signature)

    # Get seed entity
    seed_entity = await session.get(Entity, entity_id)
    if not seed_entity:
        raise EntityNotFoundError(entity_id)

    seed_summary = entity_to_summary(seed_entity)

    # Compute call cone via BFS
    cone = compute_call_cone(
        graph,
        entity_id,
        max_depth=params.max_depth,
        max_size=params.max_cone_size,
    )

    direct_ids: list[str] = cone["direct"]
    transitive_ids: list[str] = cone["transitive"]
    all_cone_ids = direct_ids + transitive_ids
    truncated: bool = cone["truncated"]

    # Fetch all cone entities
    direct_summaries = await fetch_entity_summaries(session, direct_ids)
    transitive_summaries = await fetch_entity_summaries(session, transitive_ids)

    # Fetch full entity objects for capability/side-effect analysis
    all_entity_ids = [entity_id] + all_cone_ids
    result = await session.execute(
        select(Entity).where(Entity.entity_id.in_(all_entity_ids))
    )
    all_entities_map = {e.entity_id: e for e in result.scalars().all()}

    # --- Capabilities touched ---
    cap_touches: dict[str, CapabilityTouch] = {}
    for eid in all_cone_ids:
        entity = all_entities_map.get(eid)
        if not entity or not entity.capability:
            continue
        cap = entity.capability
        is_direct = eid in direct_ids
        if cap not in cap_touches:
            cap_touches[cap] = CapabilityTouch(
                capability=cap,
                direct_count=0,
                transitive_count=0,
                functions=[],
            )
        touch = cap_touches[cap]
        if is_direct:
            touch.direct_count += 1
        else:
            touch.transitive_count += 1
        if len(touch.functions) < 10:
            touch.functions.append(entity_to_summary(entity))

    # --- Globals used ---
    globals_used: list[GlobalTouch] = []
    # Direct USES edges from seed
    if entity_id in graph:
        for _, target, data in graph.out_edges(entity_id, data=True):
            if data.get("type") == "uses":
                target_entity = all_entities_map.get(target)
                if target_entity and target_entity.kind == "variable":
                    globals_used.append(GlobalTouch(
                        entity_id=target,
                        name=target_entity.name or target,
                        kind="variable",
                        access_type="direct",
                    ))

    # Transitive USES (from callees in cone)
    seen_globals = {g.entity_id for g in globals_used}
    for eid in all_cone_ids:
        if eid not in graph:
            continue
        for _, target, data in graph.out_edges(eid, data=True):
            if data.get("type") == "uses" and target not in seen_globals:
                target_entity = all_entities_map.get(target)
                if not target_entity:
                    target_entity = await session.get(Entity, target)
                if target_entity and target_entity.kind == "variable":
                    seen_globals.add(target)
                    globals_used.append(GlobalTouch(
                        entity_id=target,
                        name=target_entity.name or target,
                        kind="variable",
                        access_type="transitive",
                    ))

    # --- Side effects ---
    side_effects: dict[str, list[SideEffectMarker]] = {}
    # Direct side effects (from seed's direct callees)
    direct_markers = _extract_side_effects_for_entities(
        all_entities_map, direct_ids, "direct"
    )
    for m in direct_markers:
        side_effects.setdefault(m.category, []).append(m)

    # Transitive side effects
    transitive_markers = _extract_side_effects_for_entities(
        all_entities_map, transitive_ids, "transitive"
    )
    for m in transitive_markers:
        side_effects.setdefault(m.category, []).append(m)

    # Also check the seed entity itself
    seed_markers = _extract_side_effects_for_entities(
        all_entities_map, [entity_id], "direct"
    )
    for m in seed_markers:
        side_effects.setdefault(m.category, []).append(m)

    behavior = BehaviorSlice(
        entry_point=seed_summary,
        direct_callees=direct_summaries,
        transitive_cone=transitive_summaries,
        max_depth=cone["max_depth_reached"],
        truncated=truncated,
        capabilities_touched=cap_touches,
        globals_used=globals_used,
        side_effects=side_effects,
        provenance="inferred",
    )

    total_cone = len(direct_summaries) + len(transitive_summaries)
    return BehaviorSliceResponse(
        behavior=behavior,
        truncation=TruncationMetadata(
            truncated=truncated,
            total_available=total_cone,
            node_count=total_cone,
            max_depth_requested=params.max_depth,
            max_depth_reached=cone["max_depth_reached"],
            truncation_reason="node_limit" if truncated else "none",
        ),
    )


async def get_state_touches_tool(
    session: AsyncSession,
    params: GetStateTouchesParams,
    graph: nx.MultiDiGraph,
) -> StateTouchesResponse:
    """
    Analyze direct and transitive global variable usage and side effects.

    Direct: USES edges from entity (depth=1)
    Transitive: CALLS → USES (depth=2 hops max per DESIGN.md §8.4)

    Args:
        session: Database session
        params: Tool parameters
        graph: Dependency graph

    Returns:
        StateTouchesResponse with direct + transitive state touches
    """
    log.info("get_state_touches tool invoked", entity_id=params.entity_id)

    entity_id = await resolve_entity_id(session, params.entity_id, params.signature)

    entity = await session.get(Entity, entity_id)
    if not entity:
        raise EntityNotFoundError(entity_id)

    direct_use_ids: list[str] = []
    transitive_use_ids: list[str] = []
    direct_callee_ids: list[str] = []

    if entity_id in graph:
        # Direct USES
        for _, target, data in graph.out_edges(entity_id, data=True):
            if data.get("type") == "uses":
                direct_use_ids.append(target)
            elif data.get("type") == "calls":
                direct_callee_ids.append(target)

        # Transitive USES (callees' USES edges - 2 hop: seed→CALLS→callee→USES→var)
        seen_uses = set(direct_use_ids)
        for callee_id in direct_callee_ids:
            if callee_id not in graph:
                continue
            for _, target, data in graph.out_edges(callee_id, data=True):
                if data.get("type") == "uses" and target not in seen_uses:
                    seen_uses.add(target)
                    transitive_use_ids.append(target)

    # Fetch entities for uses
    all_use_ids = direct_use_ids + transitive_use_ids + direct_callee_ids + [entity_id]
    result = await session.execute(
        select(Entity).where(Entity.entity_id.in_(all_use_ids))
    )
    entity_map = {e.entity_id: e for e in result.scalars().all()}

    # Filter to variables only
    direct_uses = [
        entity_to_summary(entity_map[eid])
        for eid in direct_use_ids
        if eid in entity_map and entity_map[eid].kind == "variable"
    ]

    transitive_uses = [
        entity_to_summary(entity_map[eid])
        for eid in transitive_use_ids
        if eid in entity_map and entity_map[eid].kind == "variable"
    ]

    # Side effects from direct callees
    direct_side_effects = _extract_side_effects_for_entities(
        entity_map, direct_callee_ids, "direct"
    )

    # Transitive side effects (from callees of callees up to depth 2)
    indirect_callee_ids: list[str] = []
    for callee_id in direct_callee_ids:
        if callee_id not in graph:
            continue
        for _, target, data in graph.out_edges(callee_id, data=True):
            if data.get("type") == "calls" and target not in direct_callee_ids:
                indirect_callee_ids.append(target)

    # Fetch indirect callees
    if indirect_callee_ids:
        result2 = await session.execute(
            select(Entity).where(Entity.entity_id.in_(indirect_callee_ids))
        )
        for e in result2.scalars().all():
            entity_map[e.entity_id] = e

    transitive_side_effects = _extract_side_effects_for_entities(
        entity_map, indirect_callee_ids, "transitive"
    )

    return StateTouchesResponse(
        entity_id=entity_id,
        signature=entity.signature,
        direct_uses=direct_uses,
        direct_side_effects=direct_side_effects,
        transitive_uses=transitive_uses,
        transitive_side_effects=transitive_side_effects,
    )


async def get_hotspots_tool(
    session: AsyncSession,
    params: GetHotspotsParams,
) -> HotspotsResponse:
    """
    Find architectural hotspots ranked by metric.

    Metrics:
    - fan_in: Most called functions
    - fan_out: Functions calling the most things
    - bridge: Functions spanning multiple capabilities
    - underdocumented: Important functions with low doc quality

    Args:
        session: Database session
        params: Tool parameters

    Returns:
        HotspotsResponse with ranked entities
    """
    log.info(
        "get_hotspots tool invoked",
        metric=params.metric,
        kind=params.kind,
        capability=params.capability,
    )

    stmt = select(Entity)

    # Apply filters
    if params.kind:
        stmt = stmt.where(Entity.kind == params.kind)
    if params.capability:
        stmt = stmt.where(Entity.capability == params.capability)

    # Apply metric-specific ordering
    if params.metric == "fan_in":
        stmt = stmt.order_by(Entity.fan_in.desc())
    elif params.metric == "fan_out":
        stmt = stmt.order_by(Entity.fan_out.desc())
    elif params.metric == "bridge":
        stmt = stmt.where(Entity.is_bridge == True)  # noqa: E712
        stmt = stmt.order_by(Entity.fan_in.desc())
    elif params.metric == "underdocumented":
        # Important (high fan_in) but poorly documented
        stmt = stmt.where(Entity.doc_quality.in_(["low", "medium"]))
        stmt = stmt.order_by(Entity.fan_in.desc())

    stmt = stmt.limit(params.limit)

    result = await session.execute(stmt)
    entities = list(result.scalars().all())

    summaries = [entity_to_summary(e) for e in entities]

    return HotspotsResponse(
        metric=params.metric,
        hotspots=summaries,
        truncation=TruncationMetadata(
            truncated=False,  # We applied limit directly
            total_available=len(summaries),
            node_count=len(summaries),
        ),
    )
