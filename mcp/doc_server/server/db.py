"""
Database Access Layer - SQLAlchemy async engine + Repository pattern.

Repositories encapsulate DB access; services own transactions.
Uses asyncpg driver (transitive via SQLAlchemy[asyncio]).
"""

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession, AsyncEngine
from sqlmodel import select
from typing import Sequence
from contextlib import asynccontextmanager

from server.db_models import Entity, Edge, Capability, CapabilityEdge, EntryPoint
from server.config import ServerConfig
from server.logging_config import log
from server.util import doc_quality_sort_key


def build_engine(config: ServerConfig) -> AsyncEngine:
    """
    Create SQLAlchemy async engine with asyncpg driver.

    Args:
        config: Server configuration

    Returns:
        Configured async engine
    """
    log.info("Creating database engine", url=config.db_url.replace(config.db_password, "***"))
    return create_async_engine(
        config.db_url,
        pool_size=10,
        max_overflow=0,
        echo=False,  # Set to True for SQL query logging
    )


def build_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """
    Create session factory for async sessions.

    Args:
        engine: Async engine

    Returns:
        Session factory
    """
    return async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,  # Allow access to objects after commit
    )


class DatabaseManager:
    """
    Database connection manager.

    Provides async session factory and lifecycle management.
    """

    def __init__(self, config: ServerConfig):
        self.config = config
        self.engine = build_engine(config)
        self.session_factory = build_session_factory(self.engine)

    @asynccontextmanager
    async def session(self):
        """Context manager for async sessions."""
        async with self.session_factory() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    async def dispose(self) -> None:
        """Dispose engine and close all connections."""
        log.info("Disposing database engine")
        await self.engine.dispose()


# Repository Pattern (per SQLMODEL.md)

class EntityRepository:
    """
    Entity database access.

    Repositories never commit — caller owns transaction.
    """

    async def get_by_id(self, session: AsyncSession, entity_id: str) -> Entity | None:
        """Get entity by ID."""
        return await session.get(Entity, entity_id)

    async def get_by_signature(self, session: AsyncSession, signature: str) -> Entity | None:
        """Get entity by exact signature."""
        result = await session.execute(
            select(Entity).where(Entity.signature == signature)
        )
        return result.scalar_one_or_none()

    async def get_by_name(self, session: AsyncSession, name: str, limit: int = 20) -> Sequence[Entity]:
        """
        Get entities by exact name (ranked by doc_quality, fan_in).

        Args:
            session: Async session
            name: Entity name
            limit: Maximum results

        Returns:
            List of entities
        """
        result = await session.execute(
            select(Entity)
            .where(Entity.name == name)
            .order_by(doc_quality_sort_key(), Entity.fan_in.desc())
            .limit(limit)
        )
        return result.scalars().all()

    async def get_by_prefix(self, session: AsyncSession, prefix: str, limit: int = 20) -> Sequence[Entity]:
        """
        Get entities by name prefix (ranked by length, doc_quality).

        Args:
            session: Async session
            prefix: Name prefix
            limit: Maximum results

        Returns:
            List of entities
        """
        from sqlalchemy import func

        result = await session.execute(
            select(Entity)
            .where(Entity.name.startswith(prefix))
            .order_by(func.length(Entity.name), doc_quality_sort_key())
            .limit(limit)
        )
        return result.scalars().all()

    async def get_by_file(
        self,
        session: AsyncSession,
        file_path: str,
        kind: str | None = None,
        limit: int = 100
    ) -> Sequence[Entity]:
        """
        Get entities defined in a file.

        Args:
            session: Async session
            file_path: File path
            kind: Optional kind filter
            limit: Maximum results

        Returns:
            List of entities
        """
        stmt = select(Entity).where(Entity.file_path == file_path)
        if kind:
            stmt = stmt.where(Entity.kind == kind)
        stmt = stmt.order_by(Entity.body_start_line).limit(limit)

        result = await session.execute(stmt)
        return result.scalars().all()

    async def count(self, session: AsyncSession) -> int:
        """Count total entities."""
        from sqlalchemy import func

        result = await session.execute(select(func.count(Entity.entity_id)))
        return result.scalar_one()


class EdgeRepository:
    """Edge (dependency graph) database access."""

    async def get_by_source(
        self,
        session: AsyncSession,
        source_id: str,
        relationship: str | None = None,
        limit: int = 100
    ) -> Sequence[Edge]:
        """Get edges from a source entity."""
        stmt = select(Edge).where(Edge.source_id == source_id)
        if relationship:
            stmt = stmt.where(Edge.relationship == relationship)
        stmt = stmt.limit(limit)

        result = await session.execute(stmt)
        return result.scalars().all()

    async def get_by_target(
        self,
        session: AsyncSession,
        target_id: str,
        relationship: str | None = None,
        limit: int = 100
    ) -> Sequence[Edge]:
        """Get edges to a target entity."""
        stmt = select(Edge).where(Edge.target_id == target_id)
        if relationship:
            stmt = stmt.where(Edge.relationship == relationship)
        stmt = stmt.limit(limit)

        result = await session.execute(stmt)
        return result.scalars().all()

    async def get_all(self, session: AsyncSession) -> Sequence[Edge]:
        """Get all edges (for graph loading)."""
        result = await session.execute(select(Edge))
        return result.scalars().all()

    async def count(self, session: AsyncSession) -> int:
        """Count total edges."""
        from sqlalchemy import func

        result = await session.execute(select(func.count()).select_from(Edge))
        return result.scalar_one()


class CapabilityRepository:
    """Capability database access."""

    async def get_by_name(self, session: AsyncSession, name: str) -> Capability | None:
        """Get capability by name."""
        return await session.get(Capability, name)

    async def get_all(self, session: AsyncSession) -> Sequence[Capability]:
        """Get all capabilities."""
        result = await session.execute(select(Capability).order_by(Capability.name))
        return result.scalars().all()

    async def get_edges(self, session: AsyncSession, source_cap: str) -> Sequence[CapabilityEdge]:
        """Get capability edges from a source capability."""
        result = await session.execute(
            select(CapabilityEdge).where(CapabilityEdge.source_cap == source_cap)
        )
        return result.scalars().all()


class EntryPointRepository:
    """Entry point database access."""

    async def get_by_name(self, session: AsyncSession, name: str) -> EntryPoint | None:
        """Get entry point by name."""
        return await session.get(EntryPoint, name)

    async def get_all(
        self,
        session: AsyncSession,
        entry_type: str | None = None,
        capability: str | None = None,
        limit: int = 100
    ) -> Sequence[EntryPoint]:
        """
        Get entry points with optional filters.

        Args:
            session: Async session
            entry_type: Filter by entry type (do_, spell_, spec_)
            capability: Filter by capability (checks capabilities JSONB array)
            limit: Maximum results

        Returns:
            List of entry points
        """
        stmt = select(EntryPoint)

        if entry_type:
            stmt = stmt.where(EntryPoint.entry_type == entry_type)

        # Note: Filtering by capability in JSONB array requires raw SQL or jsonb_array_elements
        # For simplicity, fetch all and filter in Python (acceptable for ~633 entry points)

        stmt = stmt.order_by(EntryPoint.name).limit(limit)

        result = await session.execute(stmt)
        entry_points = result.scalars().all()

        # Filter by capability if specified
        if capability:
            entry_points = [
                ep for ep in entry_points
                if ep.capabilities and capability in ep.capabilities
            ]

        return entry_points
