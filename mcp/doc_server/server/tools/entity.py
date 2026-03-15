"""
Entity Lookup Tools - resolve, get, source code, file listing.

Tools are decorated at module level with @mcp.tool() and remain directly importable.
"""

from pathlib import Path
from typing import Annotated, Literal

import networkx as nx
from fastmcp import Context
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from server.app import mcp, get_ctx
from server.converters import entity_to_summary, entity_to_detail
from server.db_models import Entity
from server.errors import EntityNotFoundError
from server.logging_config import log
from server.models import EntityDetail, EntityNeighbor, EntitySummary, TruncationMetadata
from server.resolver import resolve_entity as resolve_entity_fn
from server.util import fetch_entity_map, doc_quality_sort_key

# -- Kind literal used by multiple tools --
EntityKind = Literal[
    "function", "variable", "class", "struct", "file",
    "enum", "define", "typedef", "namespace", "dir", "group",
]

# -- Response Models --

class ResolveEntityResponse(BaseModel):
    """Response from resolve_entity tool."""
    resolution_status: Literal["exact", "ambiguous", "not_found"]
    resolved_from: str
    match_type: Literal[
        "entity_id", "signature_exact", "name_exact",
        "name_prefix", "keyword", "semantic",
    ]
    resolution_candidates: int
    candidates: list[EntitySummary]


class FileSummaryResponse(BaseModel):
    """Response from get_file_summary tool."""
    file_path: str
    entity_count: int
    entity_count_by_kind: dict[str, int]
    capability_distribution: dict[str, int]
    doc_quality_distribution: dict[str, int]
    top_entities_by_fan_in: list[EntitySummary]
    truncation: TruncationMetadata


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


class ListFileEntitiesResponse(BaseModel):
    """Response from list_file_entities tool."""
    file_path: str
    entities: list[EntitySummary]
    truncation: TruncationMetadata


@mcp.tool()
async def resolve_entity(
    ctx: Context,
    query: Annotated[str, Field(description="Entity name, signature, or ID to resolve")],
    kind: Annotated[EntityKind | None, Field(description="Optional kind filter")] = None,
) -> ResolveEntityResponse:
    """
    Resolve entity name to ranked candidates.

    Multi-stage resolution: exact ID → exact signature → exact name → prefix → keyword → semantic.
    """
    lc = get_ctx(ctx)

    log.info("resolve_entity", query=query, kind=kind)

    async with lc["db_manager"].session() as session:
        result = await resolve_entity_fn(
            session=session,
            query=query,
            kind=kind,
            embedding_client=lc["embedding_client"],
            embedding_model=lc["embedding_model"],
            limit=20,
        )

    envelope = result.to_envelope()
    candidates = result.to_entity_summaries()

    return ResolveEntityResponse(
        resolution_status=envelope.resolution_status,
        resolved_from=envelope.resolved_from,
        match_type=envelope.match_type,
        resolution_candidates=envelope.resolution_candidates,
        candidates=candidates,
    )


@mcp.tool()
async def get_entity(
    ctx: Context,
    entity_id: Annotated[str | None, Field(description="Entity ID (from resolve_entity)")] = None,
    signature: Annotated[str | None, Field(description="Entity signature (alternative to entity_id)")] = None,
    include_code: Annotated[bool, Field(description="Include source code in response")] = False,
    include_neighbors: Annotated[bool, Field(description="Include direct neighbors in dependency graph")] = False,
) -> EntityDetail:
    """
    Fetch full entity details by ID or signature.

    Provides complete documentation: identity, source location,
    documentation, metrics, optional source code & neighbors.
    """
    lc = get_ctx(ctx)

    log.info("get_entity", entity_id=entity_id, signature=signature)

    async with lc["db_manager"].session() as session:
        # Fetch entity
        if entity_id:
            entity = await session.get(Entity, entity_id)
        elif signature:
            result = await session.execute(
                select(Entity).where(Entity.signature == signature)
                .order_by(doc_quality_sort_key(), Entity.fan_in.desc())
                .limit(1)
            )
            entity = result.scalar_one_or_none()
        else:
            raise ValueError("Either entity_id or signature must be provided")

        if not entity:
            raise EntityNotFoundError(entity_id or signature or "unknown")

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
                    neighbors.append(EntityNeighbor(
                        entity_id=ne.entity_id,
                        name=ne.name or nid,
                        kind=ne.kind,
                        relationship=rel.upper(),
                        direction=direction,
                    ))
            detail.neighbors = neighbors

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
            try:
                lines = source_file.read_text(encoding="utf-8", errors="replace").splitlines()
                start = entity.body_start_line - 1
                end = entity.body_end_line or start

                ctx_start = max(0, start - context_lines)
                ctx_end = min(len(lines), end + context_lines)

                context_before = "\n".join(lines[ctx_start:start])
                context_after = "\n".join(lines[end:ctx_end])
            except (OSError, UnicodeDecodeError) as e:
                log.warning("Could not read context from disk", file=str(source_file), error=str(e))

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


@mcp.tool()
async def list_file_entities(
    ctx: Context,
    file_path: Annotated[str, Field(description="Source file path (e.g., src/fight.cc)")],
    kind: Annotated[EntityKind | None, Field(description="Optional kind filter")] = None,
    limit: Annotated[int, Field(ge=1, le=500, description="Maximum results")] = 100,
) -> ListFileEntitiesResponse:
    """
    List all entities defined in a source file.
    """
    lc = get_ctx(ctx)

    log.info("list_file_entities", file_path=file_path, kind=kind)

    async with lc["db_manager"].session() as session:
        stmt = select(Entity).where(Entity.file_path == file_path)
        if kind:
            stmt = stmt.where(Entity.kind == kind)
        stmt = stmt.order_by(Entity.body_start_line).limit(limit)

        result = await session.execute(stmt)
        entities = list(result.scalars().all())

        count_stmt = select(func.count(Entity.entity_id)).where(Entity.file_path == file_path)
        if kind:
            count_stmt = count_stmt.where(Entity.kind == kind)
        total_count = await session.scalar(count_stmt) or 0

    summaries = [entity_to_summary(e) for e in entities]

    return ListFileEntitiesResponse(
        file_path=file_path,
        entities=summaries,
        truncation=TruncationMetadata(
            truncated=len(entities) < total_count,
            total_available=total_count,
            node_count=len(entities),
        ),
    )


@mcp.tool()
async def get_file_summary(
    ctx: Context,
    file_path: Annotated[str, Field(description="Source file path")],
) -> FileSummaryResponse:
    """
    Get file-level statistics and top entities.
    """
    lc = get_ctx(ctx)

    log.info("get_file_summary", file_path=file_path)

    async with lc["db_manager"].session() as session:
        result = await session.execute(
            select(Entity).where(Entity.file_path == file_path)
        )
        entities = list(result.scalars().all())

    if not entities:
        raise EntityNotFoundError(file_path, kind="file")

    entity_count_by_kind: dict[str, int] = {}
    capability_distribution: dict[str, int] = {}
    doc_quality_distribution: dict[str, int] = {}

    for entity in entities:
        entity_count_by_kind[entity.kind] = entity_count_by_kind.get(entity.kind, 0) + 1
        if entity.capability:
            capability_distribution[entity.capability] = capability_distribution.get(entity.capability, 0) + 1
        if entity.doc_quality:
            doc_quality_distribution[entity.doc_quality] = doc_quality_distribution.get(entity.doc_quality, 0) + 1

    top_entities = sorted(entities, key=lambda e: e.fan_in, reverse=True)[:10]
    top_summaries = [entity_to_summary(e) for e in top_entities]

    return FileSummaryResponse(
        file_path=file_path,
        entity_count=len(entities),
        entity_count_by_kind=entity_count_by_kind,
        capability_distribution=capability_distribution,
        doc_quality_distribution=doc_quality_distribution,
        top_entities_by_fan_in=top_summaries,
        truncation=TruncationMetadata(
            truncated=False,
            total_available=len(entities),
            node_count=len(entities),
        ),
    )
