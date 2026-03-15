"""
Server Lifespan - Startup/shutdown lifecycle and global context.

Initializes database connection, loads dependency graph, and sets up
the embedding client during server startup. Cleans up on shutdown.
"""

from contextlib import asynccontextmanager

import networkx as nx
from fastmcp import FastMCP
from openai import AsyncOpenAI

from server.config import ServerConfig
from server.db import DatabaseManager
from server.graph import load_graph
from server.logging_config import configure_logging, log


class ServerContext:
    """Server context holding database and graph instances."""

    def __init__(self):
        self.config: ServerConfig | None = None
        self.db_manager: DatabaseManager | None = None
        self.graph: nx.MultiDiGraph | None = None
        self.embedding_client: AsyncOpenAI | None = None
        self.embedding_model: str = "text-embedding-3-large"


server_context = ServerContext()


@asynccontextmanager
async def lifespan(app: FastMCP):
    """
    Server lifespan manager.

    Initializes database connection and loads dependency graph at startup.
    Cleans up resources at shutdown.
    """
    # Startup
    log.info("Starting Legacy Documentation Server")

    # Load configuration
    config = ServerConfig()
    configure_logging(config.log_level)
    server_context.config = config

    log.info(
        "Configuration loaded",
        db_host=config.db_host,
        db_name=config.db_name,
        project_root=str(config.project_root),
    )

    # Initialize database manager
    db_manager = DatabaseManager(config)
    server_context.db_manager = db_manager

    log.info("Database connection established")

    # Load dependency graph
    log.info("Loading dependency graph from database")
    async with db_manager.session() as session:
        graph = await load_graph(session)
        server_context.graph = graph

    log.info(
        "Dependency graph loaded",
        nodes=graph.number_of_nodes(),
        edges=graph.number_of_edges(),
    )

    # Initialize embedding client (optional)
    if config.embedding_enabled:
        try:
            embedding_client = AsyncOpenAI(
                base_url=config.embedding_base_url,
                api_key=config.embedding_api_key or "default",
            )
            server_context.embedding_client = embedding_client
            if config.embedding_model:
                server_context.embedding_model = config.embedding_model
            log.info(
                "Embedding client initialized",
                base_url=config.embedding_base_url,
                model=server_context.embedding_model,
            )
        except Exception as e:
            log.warning("Embedding client initialization failed", error=str(e))
            server_context.embedding_client = None
    else:
        log.info("Embedding endpoint not configured; semantic search disabled")

    log.info("Server ready")

    yield

    # Shutdown
    log.info("Shutting down server")
    await db_manager.dispose()
    log.info("Server shutdown complete")
