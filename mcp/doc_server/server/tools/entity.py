"""
Entity Lookup Tools - get, source code, file listing.

Tools are decorated at module level with @mcp.tool() and remain directly importable.
"""

from pathlib import Path
from typing import Annotated

import networkx as nx
from fastmcp import Context
from pydantic import BaseModel, Field

from server.app import get_ctx, mcp
from server.converters import entity_to_detail
from server.db_models import Entity
from server.errors import EntityNotFoundError
from server.logging_config import log
from server.models import (
    EntityDetail,
    EntityNeighbor,
)
from server.util import fetch_entity_map, fetch_top_callers

# -- Response Models --


class SourceCodeResponse(BaseModel):
    """Response from get_source_code tool."""

    entity_id: str
    signature: str
    file_path: str | None
    start_line: int | None
    end_line: int | None
    source_text: str | None
    definition_text: str | None
    context_lines: int
    context_before: str | None = None
    context_after: str | None = None


@mcp.tool()
async def get_entity(
    ctx: Context,
    entity_id: Annotated[str, Field(description="Entity ID (from search)")],
    include_code: Annotated[bool, Field(description="Include source code in response")] = False,
    include_neighbors: Annotated[bool, Field(description="Include direct neighbors in dependency graph")] = False,
    include_usages: Annotated[bool, Field(description="Include top 5 usage patterns from callers")] = False,
) -> EntityDetail:
    """
    Fetch full entity details by ID.

    Provides complete documentation: identity, source location,
    documentation, metrics, optional source code & neighbors.
    """
    lc = get_ctx(ctx)

    log.info("get_entity", entity_id=entity_id)

    async with lc["db_manager"].session() as session:
        entity = await session.get(Entity, entity_id)

        if not entity:
            raise EntityNotFoundError(entity_id)

        detail = entity_to_detail(entity, include_code=include_code)

        # Populate neighbors if requested
        if include_neighbors and lc["graph"] and entity.entity_id in lc["graph"]:
            graph: nx.MultiDiGraph = lc["graph"]
            neighbor_records: list[tuple[str, str, str]] = []
            for _, target, data in graph.out_edges(entity.entity_id, data=True):
                neighbor_records.append((target, data.get("type", "unknown"), "outgoing"))
            for source, _, data in graph.in_edges(entity.entity_id, data=True):
                neighbor_records.append((source, data.get("type", "unknown"), "incoming"))

            neighbor_ids = list({r[0] for r in neighbor_records})
            neighbor_map = await fetch_entity_map(session, neighbor_ids)

            neighbors: list[EntityNeighbor] = []
            for nid, rel, direction in neighbor_records:
                ne = neighbor_map.get(nid)
                if ne:
                    neighbors.append(
                        EntityNeighbor(
                            entity_id=ne.entity_id,
                            name=ne.name or nid,
                            kind=ne.kind,
                            relationship=rel.upper(),
                            direction=direction,
                        )
                    )
            detail.neighbors = neighbors

        # Populate top_usages if requested (same fan_in ranking as explain_interface)
        if include_usages:
            detail.top_usages = await fetch_top_callers(session, entity_id, limit=5)

    return detail


@mcp.tool()
async def get_source_code(
    ctx: Context,
    entity_id: Annotated[str, Field(description="Entity ID")],
    context_lines: Annotated[int, Field(ge=0, le=50, description="Number of context lines before/after")] = 5,
) -> SourceCodeResponse:
    """
    Retrieve source code for an entity with optional context lines.
    """
    lc = get_ctx(ctx)
    project_root: Path | None = lc["config"].project_root

    log.info("get_source_code", entity_id=entity_id)

    async with lc["db_manager"].session() as session:
        entity = await session.get(Entity, entity_id)
        if not entity:
            raise EntityNotFoundError(entity_id)

        context_before: str | None = None
        context_after: str | None = None

        if context_lines > 0 and project_root and entity.file_path and entity.body_start_line:
            source_file = project_root / entity.file_path
            lines = source_file.read_text(encoding="utf-8", errors="replace").splitlines()
            start = entity.body_start_line - 1
            end = entity.body_end_line or start

            ctx_start = max(0, start - context_lines)
            ctx_end = min(len(lines), end + context_lines)

            context_before = "\n".join(lines[ctx_start:start])
            context_after = "\n".join(lines[end:ctx_end])

    return SourceCodeResponse(
        entity_id=entity.entity_id,
        signature=entity.signature,
        file_path=entity.file_path,
        start_line=entity.body_start_line,
        end_line=entity.body_end_line,
        source_text=entity.source_text,
        definition_text=entity.definition_text,
        context_lines=context_lines,
        context_before=context_before,
        context_after=context_after,
    )
