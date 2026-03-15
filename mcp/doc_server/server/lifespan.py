"""
Server Lifespan - Startup/shutdown lifecycle.

Yields a dict that FastMCP makes available via ctx.lifespan_context
in every tool/resource handler. No module-level singletons.
"""

from contextlib import asynccontextmanager
from typing import TypedDict

import networkx as nx
from fastmcp import FastMCP
from openai import AsyncOpenAI

from server.config import ServerConfig
from server.db import DatabaseManager
from server.graph import load_graph
from server.logging_config import configure_logging, log


class LifespanContext(TypedDict):
    """Typed dict yielded by lifespan, accessible via ctx.lifespan_context."""
    config: ServerConfig
    db_manager: DatabaseManager
    graph: nx.MultiDiGraph
    embedding_client: AsyncOpenAI | None
    embedding_model: str


@asynccontextmanager
async def lifespan(app: FastMCP):
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

    # Initialize embedding client (optional)
    embedding_client: AsyncOpenAI | None = None
    embedding_model = "text-embedding-3-large"

    if config.embedding_enabled:
        try:
            embedding_client = AsyncOpenAI(
                base_url=config.embedding_base_url,
                api_key=config.embedding_api_key or "default",
            )
            if config.embedding_model:
                embedding_model = config.embedding_model
            log.info(
                "Embedding client initialized",
                base_url=config.embedding_base_url,
                model=embedding_model,
            )
        except Exception as e:
            log.warning("Embedding client initialization failed", error=str(e))
    else:
        log.info("Embedding endpoint not configured; semantic search disabled")

    log.info("Server ready")

    yield LifespanContext(
        config=config,
        db_manager=db_manager,
        graph=graph,
        embedding_client=embedding_client,
        embedding_model=embedding_model,
    )

    # Shutdown
    log.info("Shutting down server")
    await db_manager.dispose()
    log.info("Server shutdown complete")
