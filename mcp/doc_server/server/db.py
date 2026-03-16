"""
Database Access Layer - SQLAlchemy async engine + session management.

Uses asyncpg driver (transitive via SQLAlchemy[asyncio]).
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from server.config import ServerConfig
from server.logging_config import log


def build_engine(config: ServerConfig) -> AsyncEngine:
    """Create SQLAlchemy async engine with asyncpg driver."""
    log.info("Creating database engine", url=config.db_url.replace(config.db_password, "***"))
    return create_async_engine(
        config.db_url,
        pool_size=10,
        max_overflow=0,
        echo=False,
    )


def build_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """Create session factory for async sessions."""
    return async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


class DatabaseManager:
    """Database connection manager with session factory and lifecycle."""

    def __init__(self, config: ServerConfig):
        self.config = config
        self.engine = build_engine(config)
        self.session_factory = build_session_factory(self.engine)

    @asynccontextmanager
    async def session(self) -> AsyncIterator[AsyncSession]:
        """Context manager for async sessions (read-only server, no explicit rollback needed)."""
        async with self.session_factory() as session:
            yield session

    async def dispose(self) -> None:
        """Dispose engine and close all connections."""
        log.info("Disposing database engine")
        await self.engine.dispose()
