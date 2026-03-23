"""
Server Lifespan - Startup/shutdown lifecycle.

Yields a dict that FastMCP makes available via ctx.lifespan_context
in every tool/resource handler. No module-level singletons.
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import TypedDict

import networkx as nx
from fastmcp import FastMCP
from sqlmodel import select

from server.config import ServerConfig
from server.cross_encoder import CrossEncoderProvider
from server.db import DatabaseManager
from server.db_models import Entity, SearchConfig
from server.embedding import EmbeddingProvider, create_provider
from server.graph import load_graph
from server.logging_config import configure_logging, log
from server.retrieval_view import RetrievalView


def _assemble_doc_embed_text(entity: Entity) -> str:
    """Reconstruct doc embed text from Entity fields at reranking time."""
    parts: list[str] = []
    if entity.brief:
        parts.append(f"BRIEF: {entity.brief}")
    if entity.details:
        parts.append(f"DETAILS: {entity.details}")
    if entity.params:
        params_text = " ".join(f"{k}: {v}" for k, v in entity.params.items())
        parts.append(f"PARAMS: {params_text}")
    if entity.returns:
        parts.append(f"RETURNS: {entity.returns}")
    if entity.notes:
        parts.append(f"NOTES: {entity.notes}")
    if entity.rationale:
        parts.append(f"RATIONALE: {entity.rationale}")
    return "\n".join(parts) if parts else entity.name


def _assemble_symbol_embed_text(entity: Entity) -> str:
    """Reconstruct symbol embed text from Entity fields at reranking time."""
    if entity.kind == "function":
        if entity.qualified_name and "::" in entity.qualified_name:
            sig = entity.signature
            name = entity.name
            if name and name in sig:
                return sig.replace(name, entity.qualified_name, 1)
            return sig
        return entity.signature
    return entity.qualified_name or entity.name


class LifespanContext(TypedDict):
    """Typed dict yielded by lifespan, accessible via ctx.lifespan_context."""

    config: ServerConfig
    db_manager: DatabaseManager
    graph: nx.MultiDiGraph
    doc_embedding_provider: EmbeddingProvider
    symbol_embedding_provider: EmbeddingProvider
    cross_encoder: CrossEncoderProvider
    doc_view: RetrievalView
    symbol_view: RetrievalView


@asynccontextmanager
async def lifespan(app: FastMCP) -> AsyncIterator[LifespanContext]:
    """
    Server lifespan manager.

    Yields a LifespanContext dict that FastMCP injects into every
    tool/resource/prompt via ctx.lifespan_context.
    """
    log.info("Starting Legacy Documentation Server")

    # Load configuration
    config = ServerConfig()
    configure_logging(config.log_level)

    log.info(
        "Configuration loaded",
        db_host=config.db_host,
        db_name=config.db_name,
        project_root=str(config.project_root),
    )

    # Initialize database manager
    db_manager = DatabaseManager(config)

    log.info("Database connection established")

    # Load dependency graph
    log.info("Loading dependency graph from database")
    async with db_manager.session() as session:
        graph = await load_graph(session)

    log.info(
        "Dependency graph loaded",
        nodes=graph.number_of_nodes(),
        edges=graph.number_of_edges(),
    )

    # Initialize embedding providers (doc + symbol, may use different models)
    doc_embedding_provider = create_provider(config)
    symbol_embedding_provider = create_provider(
        config, model_name_override=config.embedding_local_symbol_model,
    )
    log.info(
        "Embedding providers initialized",
        provider=config.embedding_provider,
        doc_model=config.embedding_local_model,
        symbol_model=config.embedding_local_symbol_model,
        dimension=doc_embedding_provider.dimension,
    )

    # Initialize cross-encoder (required — fail fast)
    cross_encoder = CrossEncoderProvider(model_name=config.cross_encoder_model)

    # Load ts_rank ceilings from search_config table
    async with db_manager.session() as session:
        result = await session.execute(select(SearchConfig))
        ceilings = {row.key: row.value for row in result.scalars().all()}

    doc_ceiling = ceilings.get("doc_tsrank_ceiling", 1.0)
    symbol_ceiling = ceilings.get("symbol_tsrank_ceiling", 1.0)
    log.info("ts_rank ceilings loaded", doc=doc_ceiling, symbol=symbol_ceiling)

    # Instantiate RetrievalViews
    doc_view = RetrievalView(
        name="doc",
        embedding_column="doc_embedding",
        tsvector_column="doc_search_vector",
        tsvector_dictionary="english",
        cross_encoder=cross_encoder,
        ts_rank_ceiling=doc_ceiling,
        floor_thresholds={
            "semantic": config.floor_doc_semantic,
            "keyword_shaped": config.floor_doc_keyword_shaped,
        },
        assemble_embed_text=_assemble_doc_embed_text,
    )

    symbol_view = RetrievalView(
        name="symbol",
        embedding_column="symbol_embedding",
        tsvector_column="symbol_search_vector",
        tsvector_dictionary="simple",
        cross_encoder=cross_encoder,
        ts_rank_ceiling=symbol_ceiling,
        floor_thresholds={
            "semantic": config.floor_symbol_semantic,
            "keyword_shaped": config.floor_symbol_keyword_shaped,
            "trigram": config.floor_trigram,
        },
        assemble_embed_text=_assemble_symbol_embed_text,
    )

    log.info("Server ready")

    yield LifespanContext(
        config=config,
        db_manager=db_manager,
        graph=graph,
        doc_embedding_provider=doc_embedding_provider,
        symbol_embedding_provider=symbol_embedding_provider,
        cross_encoder=cross_encoder,
        doc_view=doc_view,
        symbol_view=symbol_view,
    )

    # Shutdown
    log.info("Shutting down server")
    await db_manager.dispose()
    log.info("Server shutdown complete")
