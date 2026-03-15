"""
Entity Lookup Tools - MCP tools for entity resolution and retrieval.

Tools:
- resolve_entity: Resolve entity name to ranked candidates
- get_entity: Fetch full entity details by ID or signature
- get_source_code: Retrieve source code with context
- list_file_entities: List all entities in a file
- get_file_summary: Get file-level statistics
"""

from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from typing import Literal
from pathlib import Path

import networkx as nx

from server.db_models import Entity
from server.errors import EntityNotFoundError
from server.models import EntitySummary, EntityDetail, EntityNeighbor, TruncationMetadata
from server.resolver import resolve_entity as resolve_entity_fn, entity_to_summary
from server.logging_config import log
from server.util import parse_json_field, fetch_entity_map, doc_quality_sort_key


# Tool Parameter Models

class ResolveEntityParams(BaseModel):
    """Parameters for resolve_entity tool."""
    query: str = Field(description="Entity name, signature, or ID to resolve")
    kind: Literal["function", "variable", "class", "struct", "file", "enum", "define", "typedef", "namespace", "dir", "group"] | None = Field(
        default=None,
        description="Optional kind filter"
    )


class GetEntityParams(BaseModel):
    """Parameters for get_entity tool."""
    entity_id: str | None = Field(default=None, description="Entity ID (from resolve_entity)")
    signature: str | None = Field(default=None, description="Entity signature (alternative to entity_id)")
    include_code: bool = Field(default=False, description="Include source code in response")
    include_neighbors: bool = Field(default=False, description="Include direct neighbors in dependency graph")


class GetSourceCodeParams(BaseModel):
    """Parameters for get_source_code tool."""
    entity_id: str = Field(description="Entity ID")
    context_lines: int = Field(default=5, ge=0, le=50, description="Number of context lines before/after")


class ListFileEntitiesParams(BaseModel):
    """Parameters for list_file_entities tool."""
    file_path: str = Field(description="Source file path (e.g., src/fight.cc)")
    kind: str | None = Field(default=None, description="Optional kind filter")
    limit: int = Field(default=100, ge=1, le=500, description="Maximum results")


class GetFileSummaryParams(BaseModel):
    """Parameters for get_file_summary tool."""
    file_path: str = Field(description="Source file path")


# Tool Response Models

class ResolveEntityResponse(BaseModel):
    """Response from resolve_entity tool."""
    resolution_status: Literal["exact", "ambiguous", "not_found"]
    resolved_from: str
    match_type: Literal["entity_id", "signature_exact", "name_exact", "name_prefix", "keyword", "semantic"]
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


# Tool Implementations

async def resolve_entity_tool(
    session: AsyncSession,
    params: ResolveEntityParams,
    embedding_client=None,
    embedding_model: str = "text-embedding-3-large",
) -> ResolveEntityResponse:
    """
    Resolve entity name to ranked candidates.

    Multi-stage resolution pipeline:
    1. Exact entity_id → exact signature → exact name → prefix → keyword → semantic

    Args:
        session: Database session
        params: Tool parameters
        embedding_client: Optional OpenAI client for semantic search

    Returns:
        Resolution envelope with candidates
    """
    log.info("resolve_entity tool invoked", query=params.query, kind=params.kind)

    result = await resolve_entity_fn(
        session=session,
        query=params.query,
        kind=params.kind,
        embedding_client=embedding_client,
        embedding_model=embedding_model,
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


async def get_entity_tool(
    session: AsyncSession,
    params: GetEntityParams,
    graph: "nx.MultiDiGraph | None" = None,
) -> EntityDetail:
    """
    Fetch full entity details by ID or signature.

    Args:
        session: Database session
        params: Tool parameters

    Returns:
        EntityDetail with complete documentation

    Raises:
        ValueError: If neither entity_id nor signature provided, or entity not found
    """
    log.info("get_entity tool invoked", entity_id=params.entity_id, signature=params.signature)

    # Fetch entity
    if params.entity_id:
        entity = await session.get(Entity, params.entity_id)
    elif params.signature:
        result = await session.execute(
            select(Entity).where(Entity.signature == params.signature)
            .order_by(doc_quality_sort_key(), Entity.fan_in.desc())
            .limit(1)
        )
        entity = result.scalar_one_or_none()
    else:
        raise ValueError("Either entity_id or signature must be provided")

    if not entity:
        raise EntityNotFoundError(params.entity_id or params.signature or "unknown")

    # Build EntityDetail
    detail = EntityDetail(
        entity_id=entity.entity_id,
        compound_id=entity.compound_id,
        member_id=entity.member_id,
        signature=entity.signature,
        name=entity.name,
        kind=entity.kind,
        entity_type=entity.entity_type,  # type: ignore
        file_path=entity.file_path,
        body_start_line=entity.body_start_line,
        body_end_line=entity.body_end_line,
        decl_file_path=entity.decl_file_path,
        decl_line=entity.decl_line,
        definition_text=entity.definition_text,
        source_text=entity.source_text if params.include_code else None,
        capability=entity.capability,
        doc_state=entity.doc_state or "extracted_summary",
        doc_quality=entity.doc_quality or "low",  # type: ignore
        fan_in=entity.fan_in,
        fan_out=entity.fan_out,
        is_bridge=entity.is_bridge,
        is_entry_point=entity.is_entry_point,
        brief=entity.brief,
        details=entity.details,
        params=parse_json_field(entity.params),
        returns=entity.returns,
        rationale=entity.rationale,
        usages=parse_json_field(entity.usages),
        notes=entity.notes,
        side_effect_markers=parse_json_field(entity.side_effect_markers),
        neighbors=None,  # Populated below if include_neighbors=true
        provenance="doxygen_extracted" if entity.doc_state == "extracted_summary" else "llm_generated",
    )

    # Populate neighbors if requested and graph available
    if params.include_neighbors and graph and entity.entity_id in graph:
        neighbor_records: list[tuple[str, str, str]] = []  # (id, rel, dir)
        for _, target, data in graph.out_edges(entity.entity_id, data=True):
            neighbor_records.append((target, data.get("type", "unknown"), "outgoing"))
        for source, _, data in graph.in_edges(entity.entity_id, data=True):
            neighbor_records.append((source, data.get("type", "unknown"), "incoming"))

        # Batch-fetch neighbor entities
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
                    direction=direction,  # type: ignore
                ))
        detail.neighbors = neighbors

    return detail


async def get_source_code_tool(
    session: AsyncSession,
    params: GetSourceCodeParams,
    project_root: Path | None = None,
) -> dict:
    """
    Retrieve source code with optional context lines.

    When context_lines > 0, reads surrounding lines from disk using project_root.

    Args:
        session: Database session
        params: Tool parameters
        project_root: Repository root for disk reads

    Returns:
        Dict with source_text, file_path, line_range, and optional context
    """
    log.info("get_source_code tool invoked", entity_id=params.entity_id)

    entity = await session.get(Entity, params.entity_id)
    if not entity:
        raise EntityNotFoundError(params.entity_id)

    result: dict = {
        "entity_id": entity.entity_id,
        "signature": entity.signature,
        "file_path": entity.file_path,
        "start_line": entity.body_start_line,
        "end_line": entity.body_end_line,
        "source_text": entity.source_text,
        "definition_text": entity.definition_text,
        "context_lines": params.context_lines,
    }

    # Read context from disk if requested
    if params.context_lines > 0 and project_root and entity.file_path and entity.body_start_line:
        source_file = project_root / entity.file_path
        try:
            lines = source_file.read_text(encoding="utf-8", errors="replace").splitlines()
            start = entity.body_start_line - 1  # 0-indexed
            end = entity.body_end_line or start  # 0-indexed end

            ctx_start = max(0, start - params.context_lines)
            ctx_end = min(len(lines), end + params.context_lines)

            result["context_before"] = "\n".join(lines[ctx_start:start])
            result["context_after"] = "\n".join(lines[end:ctx_end])
        except (OSError, UnicodeDecodeError) as e:
            log.warning("Could not read context from disk", file=str(source_file), error=str(e))

    return result


async def list_file_entities_tool(
    session: AsyncSession,
    params: ListFileEntitiesParams,
) -> dict:
    """
    List all entities defined in a file.

    Args:
        session: Database session
        params: Tool parameters

    Returns:
        Dict with entities list and truncation metadata
    """
    log.info("list_file_entities tool invoked", file_path=params.file_path, kind=params.kind)

    stmt = select(Entity).where(Entity.file_path == params.file_path)

    if params.kind:
        stmt = stmt.where(Entity.kind == params.kind)

    stmt = stmt.order_by(Entity.body_start_line).limit(params.limit)

    result = await session.execute(stmt)
    entities = list(result.scalars().all())

    # Count total available (for truncation metadata)
    from sqlalchemy import func
    count_stmt = select(func.count(Entity.entity_id)).where(Entity.file_path == params.file_path)
    if params.kind:
        count_stmt = count_stmt.where(Entity.kind == params.kind)
    total_count = await session.scalar(count_stmt) or 0

    summaries = [entity_to_summary(e) for e in entities]

    return {
        "file_path": params.file_path,
        "entities": summaries,
        "truncation": TruncationMetadata(
            truncated=len(entities) < total_count,
            total_available=total_count,
            node_count=len(entities),
        ),
    }


async def get_file_summary_tool(
    session: AsyncSession,
    params: GetFileSummaryParams,
) -> FileSummaryResponse:
    """
    Get file-level statistics and top entities.

    Args:
        session: Database session
        params: Tool parameters

    Returns:
        FileSummaryResponse with aggregated stats
    """
    log.info("get_file_summary tool invoked", file_path=params.file_path)

    # Get all entities in file
    result = await session.execute(
        select(Entity).where(Entity.file_path == params.file_path)
    )
    entities = list(result.scalars().all())

    if not entities:
        raise EntityNotFoundError(params.file_path, kind="file")

    # Aggregate statistics
    entity_count = len(entities)

    entity_count_by_kind: dict[str, int] = {}
    capability_distribution: dict[str, int] = {}
    doc_quality_distribution: dict[str, int] = {}

    for entity in entities:
        # Count by kind
        entity_count_by_kind[entity.kind] = entity_count_by_kind.get(entity.kind, 0) + 1

        # Count by capability
        if entity.capability:
            capability_distribution[entity.capability] = capability_distribution.get(entity.capability, 0) + 1

        # Count by doc quality
        if entity.doc_quality:
            doc_quality_distribution[entity.doc_quality] = doc_quality_distribution.get(entity.doc_quality, 0) + 1

    # Get top entities by fan_in
    top_entities = sorted(entities, key=lambda e: e.fan_in, reverse=True)[:10]
    top_summaries = [entity_to_summary(e) for e in top_entities]

    return FileSummaryResponse(
        file_path=params.file_path,
        entity_count=entity_count,
        entity_count_by_kind=entity_count_by_kind,
        capability_distribution=capability_distribution,
        doc_quality_distribution=doc_quality_distribution,
        top_entities_by_fan_in=top_summaries,
        truncation=TruncationMetadata(
            truncated=False,
            total_available=entity_count,
            node_count=entity_count,
        ),
    )
