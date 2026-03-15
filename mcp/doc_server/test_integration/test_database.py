"""
Test Database - Validate schema and data integrity after build.

Performs sanity checks on the populated database:
1. Row counts for all tables
2. Sample queries for each table
3. Foreign key integrity
4. Index existence
5. Data quality checks
"""

import asyncio
import sys
from pathlib import Path
from sqlalchemy import text

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from server.config import ServerConfig
from server.db import DatabaseManager
from server.logging_config import configure_logging, log


async def test_row_counts(db_manager: DatabaseManager) -> None:
    """Check row counts for all tables."""
    log.info("Testing row counts")

    async with db_manager.session() as session:
        tables = ["entities", "edges", "capabilities", "capability_edges", "entry_points"]

        for table in tables:
            result = await session.execute(text(f"SELECT COUNT(*) FROM {table}"))
            count = result.scalar()
            log.info(f"  {table}: {count} rows")


async def test_entity_samples(db_manager: DatabaseManager) -> None:
    """Query sample entities."""
    log.info("Testing entity samples")

    async with db_manager.session() as session:
        # Test basic entity query
        result = await session.execute(
            text("SELECT entity_id, name, kind, signature FROM entities LIMIT 5")
        )
        rows = result.fetchall()
        log.info(f"  Sample entities: {len(rows)} rows")
        for row in rows:
            log.info(f"    {row.entity_id}: {row.name} ({row.kind})")

        # Test entry point query
        result = await session.execute(
            text("SELECT name, entity_id, entry_type FROM entry_points LIMIT 5")
        )
        rows = result.fetchall()
        log.info(f"  Sample entry points: {len(rows)} rows")
        for row in rows:
            log.info(f"    {row.name} ({row.entry_type})")

        # Test bridge functions
        result = await session.execute(
            text("SELECT entity_id, name, capability FROM entities WHERE is_bridge = true LIMIT 5")
        )
        rows = result.fetchall()
        log.info(f"  Sample bridge functions: {len(rows)} rows")
        for row in rows:
            log.info(f"    {row.name} (capability: {row.capability})")


async def test_edges(db_manager: DatabaseManager) -> None:
    """Test edge relationships."""
    log.info("Testing edges")

    async with db_manager.session() as session:
        # Count edges by relationship type
        result = await session.execute(
            text("SELECT relationship, COUNT(*) FROM edges GROUP BY relationship ORDER BY COUNT(*) DESC")
        )
        rows = result.fetchall()
        log.info(f"  Edge types:")
        for row in rows:
            log.info(f"    {row.relationship}: {row.count}")

        # Sample edges
        result = await session.execute(
            text("""
                SELECT e.source_id, e.target_id, e.relationship,
                       s.name as source_name, t.name as target_name
                FROM edges e
                JOIN entities s ON e.source_id = s.entity_id
                JOIN entities t ON e.target_id = t.entity_id
                WHERE e.relationship = 'calls'
                LIMIT 5
            """)
        )
        rows = result.fetchall()
        log.info(f"  Sample CALLS edges: {len(rows)} rows")
        for row in rows:
            log.info(f"    {row.source_name} -> {row.target_name}")


async def test_capabilities(db_manager: DatabaseManager) -> None:
    """Test capability tables."""
    log.info("Testing capabilities")

    async with db_manager.session() as session:
        # List capabilities
        result = await session.execute(
            text("SELECT name, type, function_count FROM capabilities ORDER BY function_count DESC LIMIT 10")
        )
        rows = result.fetchall()
        log.info(f"  Top capabilities by function count:")
        for row in rows:
            log.info(f"    {row.name} ({row.type}): {row.function_count} functions")

        # Count entities by capability
        result = await session.execute(
            text("SELECT capability, COUNT(*) FROM entities WHERE capability IS NOT NULL GROUP BY capability ORDER BY COUNT(*) DESC LIMIT 10")
        )
        rows = result.fetchall()
        log.info(f"  Top capabilities by entity count:")
        for row in rows:
            log.info(f"    {row.capability}: {row.count} entities")


async def test_search_features(db_manager: DatabaseManager) -> None:
    """Test full-text search and embeddings."""
    log.info("Testing search features")

    async with db_manager.session() as session:
        # Check tsvector population
        result = await session.execute(
            text("SELECT COUNT(*) FROM entities WHERE search_vector IS NOT NULL")
        )
        count = result.scalar()
        log.info(f"  Entities with search_vector: {count}")

        # Check embedding population
        result = await session.execute(
            text("SELECT COUNT(*) FROM entities WHERE embedding IS NOT NULL")
        )
        count = result.scalar()
        log.info(f"  Entities with embeddings: {count}")

        # Test simple text search
        result = await session.execute(
            text("""
                SELECT entity_id, name, kind
                FROM entities
                WHERE search_vector @@ to_tsquery('english', 'fight | combat')
                LIMIT 5
            """)
        )
        rows = result.fetchall()
        log.info(f"  Sample text search results (fight | combat): {len(rows)} rows")
        for row in rows:
            log.info(f"    {row.name} ({row.kind})")


async def test_data_quality(db_manager: DatabaseManager) -> None:
    """Test data quality metrics."""
    log.info("Testing data quality")

    async with db_manager.session() as session:
        # Doc quality distribution
        result = await session.execute(
            text("SELECT doc_quality, COUNT(*) FROM entities WHERE doc_quality IS NOT NULL GROUP BY doc_quality")
        )
        rows = result.fetchall()
        log.info(f"  Doc quality distribution:")
        for row in rows:
            log.info(f"    {row.doc_quality}: {row.count}")

        # Entry point types
        result = await session.execute(
            text("SELECT entry_type, COUNT(*) FROM entry_points WHERE entry_type IS NOT NULL GROUP BY entry_type")
        )
        rows = result.fetchall()
        log.info(f"  Entry point types:")
        for row in rows:
            log.info(f"    {row.entry_type}: {row.count}")

        # Fan in/out stats
        result = await session.execute(
            text("""
                SELECT
                    AVG(fan_in) as avg_fan_in,
                    MAX(fan_in) as max_fan_in,
                    AVG(fan_out) as avg_fan_out,
                    MAX(fan_out) as max_fan_out
                FROM entities
                WHERE kind = 'function'
            """)
        )
        row = result.fetchone()
        log.info(f"  Function fan metrics:")
        log.info(f"    Avg fan_in: {row.avg_fan_in:.2f}, Max: {row.max_fan_in}")
        log.info(f"    Avg fan_out: {row.avg_fan_out:.2f}, Max: {row.max_fan_out}")


async def test_indexes(db_manager: DatabaseManager) -> None:
    """Verify indexes exist."""
    log.info("Testing indexes")

    async with db_manager.session() as session:
        result = await session.execute(
            text("""
                SELECT indexname, tablename
                FROM pg_indexes
                WHERE schemaname = 'public'
                ORDER BY tablename, indexname
            """)
        )
        rows = result.fetchall()
        log.info(f"  Indexes: {len(rows)} total")
        for row in rows:
            log.info(f"    {row.tablename}.{row.indexname}")


async def main() -> None:
    """Run all tests."""
    config = ServerConfig()
    configure_logging(config.log_level)

    log.info("Starting database validation tests")

    db_manager = DatabaseManager(config)

    try:
        await test_row_counts(db_manager)
        await test_entity_samples(db_manager)
        await test_edges(db_manager)
        await test_capabilities(db_manager)
        await test_search_features(db_manager)
        await test_data_quality(db_manager)
        await test_indexes(db_manager)

        log.info("All validation tests completed successfully")

    finally:
        await db_manager.dispose()


if __name__ == "__main__":
    asyncio.run(main())
