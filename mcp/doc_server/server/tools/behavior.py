"""
Behavioral Analysis Tools - call cone, state touches, hotspot detection.

Tools are decorated at module level with @mcp.tool() and remain directly importable.
"""

from typing import Annotated

from fastmcp import Context
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from server.app import mcp, get_ctx
from server.converters import entity_to_summary
from server.db_models import Entity
from server.enums import AccessType, Confidence, DocQuality, HotspotMetric, Provenance, SideEffectCategory, TruncationReason
from server.errors import EntityNotFoundError
from server.graph import compute_call_cone, CALLS, USES
from server.logging_config import log
from server.models import (
    BehaviorSlice,
    CapabilityTouch,
    EntitySummary,
    GlobalTouch,
    SideEffectMarker,
    TruncationMetadata,
)
from server.util import fetch_entity_summaries, resolve_entity_id


# -- Response Models --

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


def _extract_side_effects_for_entities(
    entities: dict[str, Entity],
    entity_ids: list[str],
    access_type: AccessType,
) -> list[SideEffectMarker]:
    """Extract side effect markers from a set of entities."""
    markers: list[SideEffectMarker] = []
    for eid in entity_ids:
        entity = entities.get(eid)
        if not entity:
            continue
        sem = entity.side_effect_markers
        if not sem or not isinstance(sem, dict):
            continue
        for category, functions in sem.items():
            if category not in (SideEffectCategory.MESSAGING, SideEffectCategory.PERSISTENCE, SideEffectCategory.STATE_MUTATION, SideEffectCategory.SCHEDULING):
                continue
            if isinstance(functions, list) and functions:
                markers.append(SideEffectMarker(
                    function_id=eid,
                    function_name=entity.name or eid,
                    category=category,
                    access_type=access_type,
                    confidence=Confidence.DIRECT if access_type == AccessType.DIRECT else Confidence.TRANSITIVE,
                    provenance=Provenance.HEURISTIC,
                ))
    return markers


@mcp.tool()
async def get_behavior_slice(
    ctx: Context,
    entity_id: Annotated[str | None, Field(description="Seed entity ID")] = None,
    signature: Annotated[str | None, Field(description="Entity signature (alternative to entity_id)")] = None,
    max_depth: Annotated[int, Field(ge=1, le=10, description="Maximum traversal depth")] = 5,
    max_cone_size: Annotated[int, Field(ge=1, le=1000, description="Maximum cone size before truncation")] = 200,
) -> BehaviorSliceResponse:
    """
    Compute transitive call cone with behavioral analysis.

    Analyzes direct/transitive callees, capabilities touched,
    globals used, and side effects (messaging, persistence, state_mutation, scheduling).
    """
    lc = get_ctx(ctx)
    graph = lc["graph"]

    log.info("get_behavior_slice", entity_id=entity_id, max_depth=max_depth)

    async with lc["db_manager"].session() as session:
        eid = await resolve_entity_id(session, entity_id, signature)

        seed_entity = await session.get(Entity, eid)
        if not seed_entity:
            raise EntityNotFoundError(eid)

        seed_summary = entity_to_summary(seed_entity)

        cone = compute_call_cone(graph, eid, max_depth=max_depth, max_size=max_cone_size)
        direct_ids: list[str] = cone["direct"]
        transitive_ids: list[str] = cone["transitive"]
        all_cone_ids = direct_ids + transitive_ids
        truncated: bool = cone["truncated"]

        direct_summaries = await fetch_entity_summaries(session, direct_ids)
        transitive_summaries = await fetch_entity_summaries(session, transitive_ids)

        all_entity_ids = [eid] + all_cone_ids

        # Also fetch uses-targets so globals_used can resolve them
        uses_target_ids: list[str] = []
        for check_eid in [eid] + all_cone_ids:
            if check_eid not in graph:
                continue
            for _, target, data in graph.out_edges(check_eid, data=True):
                if data.get("type") == USES:
                    uses_target_ids.append(target)

        fetch_ids = list(set(all_entity_ids + uses_target_ids))
        result = await session.execute(
            select(Entity).where(Entity.entity_id.in_(fetch_ids))
        )
        all_entities_map = {e.entity_id: e for e in result.scalars().all()}

    # Capabilities touched
    cap_touches: dict[str, CapabilityTouch] = {}
    for cone_eid in all_cone_ids:
        entity = all_entities_map.get(cone_eid)
        if not entity or not entity.capability:
            continue
        cap = entity.capability
        is_direct = cone_eid in direct_ids
        if cap not in cap_touches:
            cap_touches[cap] = CapabilityTouch(
                capability=cap, direct_count=0, transitive_count=0, functions=[],
            )
        touch = cap_touches[cap]
        if is_direct:
            touch.direct_count += 1
        else:
            touch.transitive_count += 1
        if len(touch.functions) < 10:
            touch.functions.append(entity_to_summary(entity))

    # Globals used
    globals_used: list[GlobalTouch] = []
    if eid in graph:
        for _, target, data in graph.out_edges(eid, data=True):
            if data.get("type") == USES:
                te = all_entities_map.get(target)
                if te and te.kind == "variable":
                    globals_used.append(GlobalTouch(
                        entity_id=target, name=te.name or target,
                        kind="variable", access_type=AccessType.DIRECT,
                    ))

    seen_globals = {g.entity_id for g in globals_used}
    for cone_eid in all_cone_ids:
        if cone_eid not in graph:
            continue
        for _, target, data in graph.out_edges(cone_eid, data=True):
            if data.get("type") == USES and target not in seen_globals:
                te = all_entities_map.get(target)
                if te and te.kind == "variable":
                    seen_globals.add(target)
                    globals_used.append(GlobalTouch(
                        entity_id=target, name=te.name or target,
                        kind="variable", access_type=AccessType.TRANSITIVE,
                    ))

    # Side effects
    side_effects: dict[str, list[SideEffectMarker]] = {}
    for m in _extract_side_effects_for_entities(all_entities_map, [eid], AccessType.DIRECT):
        side_effects.setdefault(m.category, []).append(m)
    for m in _extract_side_effects_for_entities(all_entities_map, direct_ids, AccessType.DIRECT):
        side_effects.setdefault(m.category, []).append(m)
    for m in _extract_side_effects_for_entities(all_entities_map, transitive_ids, AccessType.TRANSITIVE):
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
        provenance=Provenance.INFERRED,
    )

    total_cone = len(direct_summaries) + len(transitive_summaries)
    return BehaviorSliceResponse(
        behavior=behavior,
        truncation=TruncationMetadata(
            truncated=truncated,
            total_available=total_cone,
            node_count=total_cone,
            max_depth_requested=max_depth,
            max_depth_reached=cone["max_depth_reached"],
            truncation_reason=TruncationReason.NODE_LIMIT if truncated else TruncationReason.NONE,
        ),
    )


@mcp.tool()
async def get_state_touches(
    ctx: Context,
    entity_id: Annotated[str | None, Field(description="Entity ID")] = None,
    signature: Annotated[str | None, Field(description="Entity signature (alternative to entity_id)")] = None,
) -> StateTouchesResponse:
    """
    Analyze global variable usage and side effects (direct + transitive).

    Direct: Variables this entity uses (USES edges, depth=1).
    Transitive: Variables reachable via CALLS→USES (depth=2 hops).
    """
    lc = get_ctx(ctx)
    graph = lc["graph"]

    log.info("get_state_touches", entity_id=entity_id)

    async with lc["db_manager"].session() as session:
        eid = await resolve_entity_id(session, entity_id, signature)

        entity = await session.get(Entity, eid)
        if not entity:
            raise EntityNotFoundError(eid)

        direct_use_ids: list[str] = []
        transitive_use_ids: list[str] = []
        direct_callee_ids: list[str] = []

        if eid in graph:
            for _, target, data in graph.out_edges(eid, data=True):
                if data.get("type") == USES:
                    direct_use_ids.append(target)
                elif data.get("type") == CALLS:
                    direct_callee_ids.append(target)

            seen_uses = set(direct_use_ids)
            for callee_id in direct_callee_ids:
                if callee_id not in graph:
                    continue
                for _, target, data in graph.out_edges(callee_id, data=True):
                    if data.get("type") == USES and target not in seen_uses:
                        seen_uses.add(target)
                        transitive_use_ids.append(target)

        all_use_ids = direct_use_ids + transitive_use_ids + direct_callee_ids + [eid]
        result = await session.execute(
            select(Entity).where(Entity.entity_id.in_(all_use_ids))
        )
        entity_map = {e.entity_id: e for e in result.scalars().all()}

        # Indirect callees for transitive side effects
        indirect_callee_ids: list[str] = []
        for callee_id in direct_callee_ids:
            if callee_id not in graph:
                continue
            for _, target, data in graph.out_edges(callee_id, data=True):
                if data.get("type") == CALLS and target not in direct_callee_ids:
                    indirect_callee_ids.append(target)

        if indirect_callee_ids:
            result2 = await session.execute(
                select(Entity).where(Entity.entity_id.in_(indirect_callee_ids))
            )
            for e in result2.scalars().all():
                entity_map[e.entity_id] = e

    direct_uses = [
        entity_to_summary(entity_map[e])
        for e in direct_use_ids
        if e in entity_map and entity_map[e].kind == "variable"
    ]
    transitive_uses = [
        entity_to_summary(entity_map[e])
        for e in transitive_use_ids
        if e in entity_map and entity_map[e].kind == "variable"
    ]
    direct_side_effects = _extract_side_effects_for_entities(entity_map, direct_callee_ids, AccessType.DIRECT)
    transitive_side_effects = _extract_side_effects_for_entities(entity_map, indirect_callee_ids, AccessType.TRANSITIVE)

    return StateTouchesResponse(
        entity_id=eid,
        signature=entity.signature,
        direct_uses=direct_uses,
        direct_side_effects=direct_side_effects,
        transitive_uses=transitive_uses,
        transitive_side_effects=transitive_side_effects,
    )


@mcp.tool()
async def get_hotspots(
    ctx: Context,
    metric: Annotated[
        HotspotMetric,
        Field(description="Ranking metric"),
    ],
    kind: Annotated[str | None, Field(description="Optional kind filter")] = None,
    capability: Annotated[str | None, Field(description="Optional capability filter")] = None,
    limit: Annotated[int, Field(ge=1, le=100, description="Maximum results")] = 20,
) -> HotspotsResponse:
    """
    Find architectural hotspots ranked by metric.

    Metrics: fan_in (most called), fan_out (calls most), bridge (cross-capability),
    underdocumented (important but poorly documented).
    """
    lc = get_ctx(ctx)

    log.info("get_hotspots", metric=metric, kind=kind, capability=capability)

    async with lc["db_manager"].session() as session:
        stmt = select(Entity)
        if kind:
            stmt = stmt.where(Entity.kind == kind)
        if capability:
            stmt = stmt.where(Entity.capability == capability)

        if metric == HotspotMetric.FAN_IN:
            stmt = stmt.order_by(Entity.fan_in.desc())
        elif metric == HotspotMetric.FAN_OUT:
            stmt = stmt.order_by(Entity.fan_out.desc())
        elif metric == HotspotMetric.BRIDGE:
            stmt = stmt.where(Entity.is_bridge == True)  # noqa: E712
            stmt = stmt.order_by(Entity.fan_in.desc())
        elif metric == HotspotMetric.UNDERDOCUMENTED:
            stmt = stmt.where(Entity.doc_quality.in_([DocQuality.LOW, DocQuality.MEDIUM]))
            stmt = stmt.order_by(Entity.fan_in.desc())

        stmt = stmt.limit(limit)

        result = await session.execute(stmt)
        entities = list(result.scalars().all())

    summaries = [entity_to_summary(e) for e in entities]

    return HotspotsResponse(
        metric=metric,
        hotspots=summaries,
        truncation=TruncationMetadata(
            truncated=False,
            total_available=len(summaries),
            node_count=len(summaries),
        ),
    )
