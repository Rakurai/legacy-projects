"""
MCP Resources - Read-only resource handlers for documentation artifacts.

Resources:
- legacy://capabilities          — List all capability groups
- legacy://capability/{name}     — Get capability detail
- legacy://entity/{entity_id}    — Get full entity details
- legacy://file/{path}           — List entities in a file
- legacy://stats                 — Server statistics
"""

from functools import lru_cache
from importlib.metadata import PackageNotFoundError, version

import networkx as nx
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from server.converters import entity_to_summary
from server.db_models import Capability, CapabilityEdge, Entity, EntryPoint
from server.logging_config import log


@lru_cache(maxsize=1)
def _get_version() -> str:
    """Read version from installed package metadata (falls back to unknown)."""
    try:
        return version("legacy-mcp-doc-server")
    except PackageNotFoundError:
        return "unknown"


async def get_capabilities_resource(session: AsyncSession) -> dict:
    """
    List all capability groups with metadata.

    Returns:
        Dict with capabilities list (for legacy://capabilities)
    """
    log.info("Resource: legacy://capabilities")

    result = await session.execute(select(Capability).order_by(Capability.name))
    capabilities = list(result.scalars().all())

    return {
        "capabilities": [
            {
                "name": cap.name,
                "type": cap.type,
                "description": cap.description,
                "function_count": cap.function_count,
                "stability": cap.stability,
            }
            for cap in capabilities
        ]
    }


async def get_capability_detail_resource(
    session: AsyncSession,
    name: str,
) -> dict:
    """
    Get detailed information for a specific capability group.

    Args:
        session: Database session
        name: Capability name

    Returns:
        Dict with full capability detail (for legacy://capability/{name})

    Raises:
        ValueError: If capability not found
    """
    log.info("Resource: legacy://capability/{name}", name=name)

    cap = await session.get(Capability, name)
    if not cap:
        raise ValueError(f"Capability not found: {name}")

    # Get edges
    edge_result = await session.execute(select(CapabilityEdge).where(CapabilityEdge.source_cap == name))
    edges = list(edge_result.scalars().all())

    # Get entry points
    ep_result = await session.execute(
        select(Entity)
        .where(Entity.capability == name)
        .where(Entity.is_entry_point == True)  # noqa: E712
        .order_by(Entity.name)
        .limit(20)
    )
    entry_points = list(ep_result.scalars().all())

    # Get sample functions (top by fan_in)
    func_result = await session.execute(
        select(Entity).where(Entity.capability == name).order_by(Entity.fan_in.desc()).limit(10)
    )
    sample_functions = list(func_result.scalars().all())

    return {
        "name": cap.name,
        "type": cap.type,
        "description": cap.description,
        "function_count": cap.function_count,
        "stability": cap.stability,
        "dependencies": [
            {
                "target_capability": e.target_cap,
                "edge_type": e.edge_type,
                "call_count": e.call_count,
            }
            for e in edges
        ],
        "entry_points": [
            {
                "entity_id": ep.entity_id,
                "signature": ep.signature,
                "name": ep.name,
            }
            for ep in entry_points
        ],
        "sample_functions": [entity_to_summary(e).model_dump() for e in sample_functions],
    }


async def get_entity_resource(
    session: AsyncSession,
    entity_id: str,
) -> dict:
    """
    Get full entity details by entity_id.

    Args:
        session: Database session
        entity_id: Entity ID

    Returns:
        Dict with full entity detail (for legacy://entity/{entity_id})

    Raises:
        ValueError: If entity not found
    """
    log.info("Resource: legacy://entity/{entity_id}", entity_id=entity_id)

    entity = await session.get(Entity, entity_id)
    if not entity:
        raise ValueError(f"Entity not found: {entity_id}")

    return {
        "entity_id": entity.entity_id,
        "signature": entity.signature,
        "name": entity.name,
        "kind": entity.kind,
        "entity_type": entity.entity_type,
        "file_path": entity.file_path,
        "body_start_line": entity.body_start_line,
        "body_end_line": entity.body_end_line,
        "decl_file_path": entity.decl_file_path,
        "decl_line": entity.decl_line,
        "definition_text": entity.definition_text,
        "source_text": entity.source_text,
        "capability": entity.capability,
        "fan_in": entity.fan_in,
        "fan_out": entity.fan_out,
        "is_bridge": entity.is_bridge,
        "is_entry_point": entity.is_entry_point,
        "brief": entity.brief,
        "details": entity.details,
        "params": entity.params,
        "returns": entity.returns,
        "rationale": entity.rationale,
        "usages": entity.usages,
        "notes": entity.notes,
    }


async def get_file_entities_resource(
    session: AsyncSession,
    file_path: str,
) -> dict:
    """
    List all entities defined in a source file.

    Args:
        session: Database session
        file_path: Relative file path

    Returns:
        Dict with file entities (for legacy://file/{path})
    """
    log.info("Resource: legacy://file/{path}", path=file_path)

    result = await session.execute(select(Entity).where(Entity.file_path == file_path).order_by(Entity.body_start_line))
    entities = list(result.scalars().all())

    return {
        "file_path": file_path,
        "entity_count": len(entities),
        "entities": [entity_to_summary(e).model_dump() for e in entities],
    }


async def get_stats_resource(
    session: AsyncSession,
    graph: nx.MultiDiGraph | None = None,
    embedding_available: bool = False,
) -> dict:
    """
    Get aggregate server statistics.

    Args:
        session: Database session
        graph: NetworkX graph (optional)
        embedding_available: Whether embedding endpoint is available

    Returns:
        Dict with server stats (for legacy://stats)
    """
    log.info("Resource: legacy://stats")

    # Entity stats
    total_entities = await session.scalar(select(func.count(Entity.entity_id))) or 0

    # Entities by kind
    kind_result = await session.execute(select(Entity.kind, func.count(Entity.entity_id)).group_by(Entity.kind))
    entities_by_kind = {row[0]: row[1] for row in kind_result.all()}

    # Entities with documentation
    entities_with_docs = await session.scalar(select(func.count(Entity.entity_id)).where(Entity.brief.isnot(None))) or 0

    # Entities with embeddings
    entities_with_embeddings = (
        await session.scalar(select(func.count(Entity.entity_id)).where(Entity.doc_embedding.isnot(None))) or 0
    )

    # Graph stats
    graph_stats = {
        "total_nodes": 0,
        "total_edges": 0,
        "edges_by_type": {},
    }
    if graph is not None:
        graph_stats["total_nodes"] = graph.number_of_nodes()
        graph_stats["total_edges"] = graph.number_of_edges()
        graph_stats["edges_by_type"] = graph.graph.get("edge_type_counts", {})

    # Capability stats
    total_capabilities = await session.scalar(select(func.count(Capability.name))) or 0

    cap_type_result = await session.execute(
        select(Capability.type, func.count(Capability.name)).group_by(Capability.type)
    )
    capabilities_by_type = {row[0]: row[1] for row in cap_type_result.all()}

    total_entry_points = await session.scalar(select(func.count(EntryPoint.entity_id))) or 0

    return {
        "entity_stats": {
            "total_entities": total_entities,
            "entities_by_kind": entities_by_kind,
            "entities_with_documentation": entities_with_docs,
            "entities_with_embeddings": entities_with_embeddings,
        },
        "graph_stats": graph_stats,
        "capability_stats": {
            "total_capabilities": total_capabilities,
            "capabilities_by_type": capabilities_by_type,
            "total_entry_points": total_entry_points,
        },
        "server_info": {
            "version": _get_version(),
            "embedding_endpoint_available": embedding_available,
            "database_connection_status": "connected",
        },
    }
