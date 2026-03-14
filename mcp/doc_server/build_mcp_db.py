"""
MCP Database Build Script - Offline ETL Pipeline.

Transforms pre-computed artifacts into queryable PostgreSQL database:
1. Validate all required artifacts
2. Load entities and documentation
3. Merge and enrich with source code
4. Load dependency graph and compute metrics
5. Load embeddings
6. Populate database tables (entities, edges, capabilities, entry_points)

Run from project root: uv run python build_mcp_db.py

Expected runtime: ~20-30 seconds for full rebuild.
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

# Setup paths
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from server.config import ServerConfig
from server.db import DatabaseManager, EntityRepository
from server.db_models import Entity, Edge, Capability, CapabilityEdge, EntryPoint
from server.logging_config import configure_logging, log

from build_helpers.loaders import (
    validate_artifacts,
    load_entities,
    load_documents,
    load_capability_defs,
    load_capability_graph,
)
from build_helpers.entity_processor import (
    merge_entities,
    extract_source_code,
    compute_doc_quality,
    compute_is_entry_point,
    generate_tsvector_text,
    MergedEntity,
)
from build_helpers.graph_loader import (
    load_graph_edges,
    compute_fan_metrics,
    compute_bridge_flags,
    compute_side_effect_markers,
)
from build_helpers.embeddings_loader import load_embeddings, attach_embeddings


async def drop_and_create_schema(session: AsyncSession) -> None:
    """
    Drop existing tables and recreate schema.

    This ensures idempotent builds (same input → same output).
    """
    log.info("Dropping existing tables")

    await session.execute(text("DROP TABLE IF EXISTS entry_points CASCADE"))
    await session.execute(text("DROP TABLE IF EXISTS capability_edges CASCADE"))
    await session.execute(text("DROP TABLE IF EXISTS capabilities CASCADE"))
    await session.execute(text("DROP TABLE IF EXISTS edges CASCADE"))
    await session.execute(text("DROP TABLE IF EXISTS entities CASCADE"))

    log.info("Creating schema")

    # Create pgvector extension
    await session.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))

    # Create tables (SQLModel will use metadata, but we need to ensure order)
    # Import to trigger metadata registration
    from server import db_models

    # Create tables via SQLModel metadata
    from sqlmodel import SQLModel
    from server.db import build_engine
    config = ServerConfig()
    engine = build_engine(config)

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    # Create indexes
    log.info("Creating indexes")

    indexes = [
        "CREATE INDEX idx_entities_name ON entities(name)",
        "CREATE INDEX idx_entities_kind ON entities(kind)",
        "CREATE INDEX idx_entities_file ON entities(file_path)",
        "CREATE INDEX idx_entities_capability ON entities(capability)",
        "CREATE INDEX idx_entities_entry ON entities(is_entry_point) WHERE is_entry_point",
        "CREATE INDEX idx_entities_bridge ON entities(is_bridge) WHERE is_bridge",
        "CREATE INDEX idx_entities_search ON entities USING GIN(search_vector)",
        "CREATE INDEX idx_entities_embedding ON entities USING ivfflat (embedding vector_cosine_ops) WITH (lists = 50)",
        "CREATE INDEX idx_edges_source ON edges(source_id)",
        "CREATE INDEX idx_edges_target ON edges(target_id)",
        "CREATE INDEX idx_edges_rel ON edges(relationship)",
        "CREATE INDEX idx_capability_edges_source ON capability_edges(source_cap)",
        "CREATE INDEX idx_capability_edges_target ON capability_edges(target_cap)",
    ]

    for idx_sql in indexes:
        try:
            await session.execute(text(idx_sql))
        except Exception as e:
            log.warning("Index creation failed (may already exist)", sql=idx_sql[:50], error=str(e))

    await session.commit()
    log.info("Schema created")


async def populate_entities(session: AsyncSession, merged_entities: list[MergedEntity]) -> None:
    """
    Populate entities table with enriched entity records.

    Also generates tsvector for full-text search using PostgreSQL function.
    """
    log.info("Populating entities table", count=len(merged_entities))

    for merged in merged_entities:
        entity = Entity(
            entity_id=merged.entity_id,
            compound_id=merged.compound_id,
            member_id=merged.member_id,
            name=merged.entity.name,
            signature=merged.signature,
            kind=merged.entity.kind,
            entity_type="member" if merged.member_id else "compound",
            file_path=merged.entity.body.fn if merged.entity.body else None,
            body_start_line=merged.entity.body.line if merged.entity.body else None,
            body_end_line=merged.entity.body.end_line if merged.entity.body else None,
            decl_file_path=merged.entity.decl.fn if merged.entity.decl else None,
            decl_line=merged.entity.decl.line if merged.entity.decl else None,
            definition_text=merged.definition_text,
            source_text=merged.source_text,
            brief=merged.doc.brief if merged.doc else None,
            details=merged.doc.details if merged.doc else None,
            params=merged.doc.params if merged.doc else None,
            returns=merged.doc.returns if merged.doc else None,
            notes=merged.doc.notes if merged.doc else None,
            rationale=merged.doc.rationale if merged.doc else None,
            usages=merged.doc.usages if merged.doc else None,
            doc_state=merged.doc.state if merged.doc else "extracted_summary",
            doc_quality=merged.doc_quality,
            capability=merged.capability,
            is_entry_point=merged.is_entry_point,
            fan_in=merged.fan_in,
            fan_out=merged.fan_out,
            is_bridge=merged.is_bridge,
            side_effect_markers=merged.side_effect_markers if merged.side_effect_markers else None,
            embedding=merged.embedding if hasattr(merged, 'embedding') else None,
            search_vector=None,  # Will be populated via SQL below
        )

        session.add(entity)

    await session.commit()

    # Generate tsvectors via SQL (weighted composition)
    log.info("Generating tsvector search vectors")

    tsvector_sql = text("""
        UPDATE entities
        SET search_vector =
            setweight(to_tsvector('english', COALESCE(name, '')), 'A') ||
            setweight(to_tsvector('english', COALESCE(brief, '') || ' ' || COALESCE(details, '')), 'B') ||
            setweight(to_tsvector('english', COALESCE(definition_text, '')), 'C') ||
            setweight(to_tsvector('english', COALESCE(SUBSTRING(source_text, 1, 1000), '')), 'D')
    """)

    await session.execute(tsvector_sql)
    await session.commit()

    log.info("Entities table populated")


async def populate_edges(session: AsyncSession, edges: list[tuple[str, str, str]]) -> None:
    """Populate edges table."""
    log.info("Populating edges table", count=len(edges))

    for source, target, relationship in edges:
        edge = Edge(
            source_id=source,
            target_id=target,
            relationship=relationship.lower()
        )
        session.add(edge)

    await session.commit()
    log.info("Edges table populated")


async def populate_capabilities(
    session: AsyncSession,
    cap_defs: dict,
    cap_graph: dict
) -> None:
    """Populate capabilities and capability_edges tables."""
    log.info("Populating capabilities table")

    # Populate capabilities
    for cap_name, cap_def in cap_defs.items():
        # Compute doc_quality distribution
        # (Would need to aggregate from entities, simplifying for now)
        doc_quality_dist = {"high": 0, "medium": 0, "low": 0}

        capability = Capability(
            name=cap_name,
            type=cap_def.get("type", "domain"),
            description=cap_def.get("description", ""),
            function_count=len(cap_def.get("functions", [])),
            stability=cap_def.get("stability"),
            doc_quality_dist=doc_quality_dist,
        )
        session.add(capability)

    await session.commit()

    # Populate capability edges
    log.info("Populating capability_edges table")

    for edge in cap_graph.get("edges", []):
        cap_edge = CapabilityEdge(
            source_cap=edge["source"],
            target_cap=edge["target"],
            edge_type=edge.get("type", "requires_core"),
            call_count=edge.get("call_count", 0),
            in_dag=edge.get("in_dag", False),
        )
        session.add(cap_edge)

    await session.commit()
    log.info("Capabilities tables populated")


async def populate_entry_points(
    session: AsyncSession,
    merged_entities: list[MergedEntity]
) -> None:
    """
    Populate entry_points table from entities where is_entry_point=true.

    Computes which capabilities each entry point exercises (simplified version).
    """
    log.info("Populating entry_points table")

    entry_point_count = 0

    for merged in merged_entities:
        if merged.is_entry_point:
            # Determine entry type
            name = merged.entity.name
            if name.startswith("do_"):
                entry_type = "do_"
            elif name.startswith("spell_"):
                entry_type = "spell_"
            elif name.startswith("spec_"):
                entry_type = "spec_"
            else:
                entry_type = None

            # Capabilities exercised (simplified: just direct capability)
            capabilities = [merged.capability] if merged.capability else []

            entry_point = EntryPoint(
                name=name,
                entity_id=merged.entity_id,
                capabilities=capabilities,
                entry_type=entry_type,
            )
            session.add(entry_point)
            entry_point_count += 1

    await session.commit()
    log.info("Entry points table populated", count=entry_point_count)


async def main() -> None:
    """Main build pipeline."""
    start_time = datetime.now()

    # Load configuration
    config = ServerConfig()
    configure_logging(config.log_level)

    log.info("Starting MCP database build", artifacts_dir=str(config.artifacts_path))

    # Stage 1: Validate artifacts
    validate_artifacts(config.artifacts_path)

    # Stage 2: Load entities and docs
    entity_db = load_entities(config.artifacts_path)
    doc_db = load_documents(config.artifacts_path)

    # Stage 3: Merge
    merged_entities = merge_entities(entity_db, doc_db)

    # Stage 4: Extract source code
    extract_source_code(merged_entities, config.project_root)

    # Stage 5: Load graph and compute metrics
    edges = load_graph_edges(config.artifacts_path)
    compute_fan_metrics(merged_entities, edges)
    compute_bridge_flags(merged_entities, edges)
    compute_side_effect_markers(merged_entities, edges)

    # Stage 6: Compute other derived fields
    compute_doc_quality(merged_entities)
    compute_is_entry_point(merged_entities)
    generate_tsvector_text(merged_entities)

    # Stage 7: Load embeddings
    embeddings = load_embeddings(config.artifacts_path)
    attach_embeddings(merged_entities, embeddings)

    # Stage 8: Load capabilities
    cap_defs = load_capability_defs(config.artifacts_path)
    cap_graph = load_capability_graph(config.artifacts_path)

    # Stage 9: Populate database
    db_manager = DatabaseManager(config)

    async with db_manager.session() as session:
        await drop_and_create_schema(session)
        await populate_entities(session, merged_entities)
        await populate_edges(session, edges)
        await populate_capabilities(session, cap_defs, cap_graph)
        await populate_entry_points(session, merged_entities)

        # Analyze tables for query planner
        log.info("Analyzing tables")
        await session.execute(text("ANALYZE entities"))
        await session.execute(text("ANALYZE edges"))
        await session.commit()

    await db_manager.dispose()

    elapsed = (datetime.now() - start_time).total_seconds()
    log.info("MCP database build complete", duration_seconds=round(elapsed, 1))


if __name__ == "__main__":
    asyncio.run(main())
