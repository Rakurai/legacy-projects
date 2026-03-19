"""
Behavioral Analysis Tools - call cone, state touches, hotspot detection.

Tools are decorated at module level with @mcp.tool() and remain directly importable.
"""

from typing import Annotated

from fastmcp import Context
from pydantic import BaseModel, Field
from sqlmodel import select

from server.app import get_ctx, mcp
from server.converters import entity_to_summary
from server.db_models import Entity
from server.enums import (
    AccessType,
    TruncationReason,
)
from server.errors import EntityNotFoundError
from server.graph import CALLS, USES, compute_call_cone
from server.logging_config import log
from server.models import (
    BehaviorSlice,
    CapabilityTouch,
    EntitySummary,
    GlobalTouch,
    TruncationMetadata,
)
from server.util import fetch_entity_summaries

# Maximum number of example functions listed per capability touch
_MAX_FUNCTIONS_PER_TOUCH = 10

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
    transitive_uses: list[EntitySummary]


@mcp.tool()
async def get_behavior_slice(
    ctx: Context,
    entity_id: Annotated[str, Field(description="Seed entity ID")],
    max_depth: Annotated[int, Field(ge=1, le=10, description="Maximum traversal depth")] = 5,
    max_cone_size: Annotated[int, Field(ge=1, le=1000, description="Maximum cone size before truncation")] = 200,
) -> BehaviorSliceResponse:
    """
    Compute transitive call cone with behavioral analysis.

    Analyzes direct/transitive callees, capabilities touched,
    and globals used.
    """
    lc = get_ctx(ctx)
    graph = lc["graph"]

    log.info("get_behavior_slice", entity_id=entity_id, max_depth=max_depth)

    async with lc["db_manager"].session() as session:
        seed_entity = await session.get(Entity, entity_id)
        if not seed_entity:
            raise EntityNotFoundError(entity_id)

        seed_summary = entity_to_summary(seed_entity)

        cone = compute_call_cone(graph, entity_id, max_depth=max_depth, max_size=max_cone_size)
        direct_ids: list[str] = cone["direct"]
        transitive_ids: list[str] = cone["transitive"]
        all_cone_ids = direct_ids + transitive_ids
        truncated: bool = cone["truncated"]

        direct_summaries = await fetch_entity_summaries(session, direct_ids)
        transitive_summaries = await fetch_entity_summaries(session, transitive_ids)

        all_entity_ids = [entity_id, *all_cone_ids]

        # Also fetch uses-targets so globals_used can resolve them
        uses_target_ids: list[str] = []
        for check_eid in [entity_id, *all_cone_ids]:
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
        if len(touch.functions) < _MAX_FUNCTIONS_PER_TOUCH:
            touch.functions.append(entity_to_summary(entity))

    # Globals used
    globals_used: list[GlobalTouch] = []
    if entity_id in graph:
        for _, target, data in graph.out_edges(entity_id, data=True):
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

    behavior = BehaviorSlice(
        entry_point=seed_summary,
        direct_callees=direct_summaries,
        transitive_cone=transitive_summaries,
        max_depth=cone["max_depth_reached"],
        truncated=truncated,
        capabilities_touched=cap_touches,
        globals_used=globals_used,
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
    entity_id: Annotated[str, Field(description="Entity ID")],
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
        entity = await session.get(Entity, entity_id)
        if not entity:
            raise EntityNotFoundError(entity_id)

        direct_use_ids: list[str] = []
        transitive_use_ids: list[str] = []
        direct_callee_ids: list[str] = []

        if entity_id in graph:
            for _, target, data in graph.out_edges(entity_id, data=True):
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

        all_use_ids = direct_use_ids + transitive_use_ids + direct_callee_ids + [entity_id]
        result = await session.execute(
            select(Entity).where(Entity.entity_id.in_(all_use_ids))
        )
        entity_map = {e.entity_id: e for e in result.scalars().all()}

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

    return StateTouchesResponse(
        entity_id=entity_id,
        signature=entity.signature,
        direct_uses=direct_uses,
        transitive_uses=transitive_uses,
    )
