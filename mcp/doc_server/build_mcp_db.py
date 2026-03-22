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
from datetime import datetime
from pathlib import Path
from typing import cast

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from build_helpers.embeddings_loader import sync_embeddings_cache
from build_helpers.entity_processor import (
    MergedEntity,
    assign_capabilities,
    assign_deterministic_ids,
    build_doc_embed_texts,
    build_symbol_embed_texts,
    build_symbol_searchable,
    compute_enriched_fields,
    compute_is_entry_point,
    derive_qualified_names,
    extract_source_code,
    merge_entities,
)
from build_helpers.graph_loader import (
    compute_bridge_flags,
    compute_fan_metrics,
    load_graph_edges,
    load_graph_node_ids,
)
from build_helpers.loaders import (
    load_capability_defs,
    load_capability_graph,
    load_documents,
    load_entities,
    validate_artifacts,
)
from server.config import ServerConfig
from server.db import DatabaseManager
from server.db_models import Capability, CapabilityEdge, Edge, Entity, EntityUsage, EntryPoint, SearchConfig
from server.embedding import EmbeddingProvider, create_provider
from server.logging_config import configure_logging, log


async def drop_and_create_schema(engine: AsyncEngine) -> None:
    """
    Drop existing tables and recreate schema with indexes.

    Uses a single engine for all DDL operations (DROP, CREATE TABLE, CREATE INDEX)
    to avoid split-transaction issues. This ensures idempotent builds.

    Args:
        engine: SQLAlchemy async engine from DatabaseManager
    """
    from sqlmodel import SQLModel

    from server import db_models  # noqa: F401 — registers models with SQLModel metadata

    log.info("Dropping existing tables")

    async with engine.begin() as conn:
        await conn.execute(text("DROP TABLE IF EXISTS search_config CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS entry_points CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS capability_edges CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS capabilities CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS edges CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS entity_usages CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS entities CASCADE"))
        await conn.execute(text("DROP INDEX IF EXISTS entities_signature_key"))

    log.info("Creating schema")

    # Create extensions + tables
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm"))
        await conn.run_sync(SQLModel.metadata.create_all)

    # Create indexes — each in its own transaction so one failure doesn't cascade
    log.info("Creating indexes")

    indexes = [
        # Entity identity/filter indexes
        "CREATE INDEX IF NOT EXISTS idx_entities_signature ON entities(signature)",
        "CREATE INDEX IF NOT EXISTS idx_entities_name ON entities(name)",
        "CREATE INDEX IF NOT EXISTS idx_entities_kind ON entities(kind)",
        "CREATE INDEX IF NOT EXISTS idx_entities_file ON entities(file_path)",
        "CREATE INDEX IF NOT EXISTS idx_entities_capability ON entities(capability)",
        "CREATE INDEX IF NOT EXISTS idx_entities_entry ON entities(is_entry_point) WHERE is_entry_point",
        "CREATE INDEX IF NOT EXISTS idx_entities_bridge ON entities(is_bridge) WHERE is_bridge",
        # Dual embedding indexes (HNSW)
        "CREATE INDEX IF NOT EXISTS ix_entities_doc_embedding ON entities USING hnsw (doc_embedding vector_cosine_ops) WITH (m=16, ef_construction=64)",
        "CREATE INDEX IF NOT EXISTS ix_entities_symbol_embedding ON entities USING hnsw (symbol_embedding vector_cosine_ops) WITH (m=16, ef_construction=64)",
        # Dual tsvector indexes (GIN)
        "CREATE INDEX IF NOT EXISTS ix_entities_doc_search_vector ON entities USING GIN(doc_search_vector)",
        "CREATE INDEX IF NOT EXISTS ix_entities_symbol_search_vector ON entities USING GIN(symbol_search_vector)",
        # Trigram index (GiST)
        "CREATE INDEX IF NOT EXISTS ix_entities_symbol_searchable ON entities USING GiST(symbol_searchable gist_trgm_ops)",
        # Edge/capability indexes
        "CREATE INDEX IF NOT EXISTS idx_edges_source ON edges(source_id)",
        "CREATE INDEX IF NOT EXISTS idx_edges_target ON edges(target_id)",
        "CREATE INDEX IF NOT EXISTS idx_edges_rel ON edges(relationship)",
        "CREATE INDEX IF NOT EXISTS idx_capability_edges_source ON capability_edges(source_cap)",
        "CREATE INDEX IF NOT EXISTS idx_capability_edges_target ON capability_edges(target_cap)",
    ]

    for idx_sql in indexes:
        async with engine.begin() as conn:
            await conn.execute(text(idx_sql))

    log.info("Schema created with indexes")


async def populate_entities(session: AsyncSession, merged_entities: list[MergedEntity]) -> None:
    """
    Populate entities table with enriched entity records.

    Also generates tsvector for full-text search using PostgreSQL function.
    """
    log.info("Populating entities table", count=len(merged_entities))

    entities_batch: list[Entity] = []
    for merged in merged_entities:
        entity = Entity(
            entity_id=merged.entity_id,
            name=merged.entity.name,
            signature=merged.signature,
            kind=merged.entity.kind,
            entity_type="member" if merged.entity.id.member else "compound",
            file_path=merged.entity.body.fn if merged.entity.body else None,
            body_start_line=merged.entity.body.line if merged.entity.body else None,
            body_end_line=merged.entity.body.end_line if merged.entity.body else None,
            decl_file_path=merged.entity.decl.fn if merged.entity.decl else None,
            decl_line=merged.entity.decl.line if merged.entity.decl else None,
            definition_text=merged.definition_text,
            source_text=merged.source_text,
            brief=merged.doc.brief if merged.doc else None,
            details=merged.doc.details if merged.doc else None,
            params=merged.doc.params if merged.doc and merged.doc.params else None,
            returns=merged.doc.returns if merged.doc else None,
            notes=merged.doc.notes if merged.doc else None,
            rationale=merged.doc.rationale if merged.doc else None,
            usages=merged.doc.usages if merged.doc else None,
            capability=merged.capability,
            is_entry_point=merged.is_entry_point,
            fan_in=merged.fan_in,
            fan_out=merged.fan_out,
            is_bridge=merged.is_bridge,
            doc_embedding=merged.doc_embedding,
            symbol_embedding=merged.symbol_embedding,
            doc_search_vector=None,
            symbol_search_vector=None,
            symbol_searchable=merged.symbol_searchable,
            qualified_name=merged.qualified_name,
            doc_state=merged.doc_state,
            notes_length=merged.notes_length,
            is_contract_seed=merged.is_contract_seed,
            rationale_specificity=merged.rationale_specificity,
        )
        entities_batch.append(entity)

    session.add_all(entities_batch)
    await session.commit()

    # Generate dual tsvectors via SQL (weighted composition)
    log.info("Generating dual tsvector search vectors")

    doc_tsvector_sql = text("""
        UPDATE entities
        SET doc_search_vector =
            setweight(to_tsvector('english', COALESCE(name, '')), 'A') ||
            setweight(to_tsvector('english', COALESCE(brief, '') || ' ' || COALESCE(details, '')), 'B') ||
            setweight(to_tsvector('english', COALESCE(notes, '') || ' ' || COALESCE(rationale, '') || ' ' || COALESCE(returns, '') || ' ' || COALESCE((SELECT string_agg(value, ' ') FROM jsonb_each_text(params)), '')), 'C')
    """)

    symbol_tsvector_sql = text("""
        UPDATE entities
        SET symbol_search_vector =
            setweight(to_tsvector('simple', COALESCE(name, '')), 'A') ||
            setweight(to_tsvector('simple', COALESCE(qualified_name, '') || ' ' || COALESCE(signature, '')), 'B') ||
            setweight(to_tsvector('simple', COALESCE(definition_text, '')), 'C')
    """)

    await session.execute(doc_tsvector_sql)
    await session.execute(symbol_tsvector_sql)
    await session.commit()

    log.info("Entities table populated")


async def compute_and_store_tsrank_ceilings(session: AsyncSession) -> None:
    """Compute p99 ts_rank for each tsvector column and store in search_config table."""
    log.info("Computing ts_rank ceilings")

    for col_name, config_key in [
        ("doc_search_vector", "doc_tsrank_ceiling"),
        ("symbol_search_vector", "symbol_tsrank_ceiling"),
    ]:
        # Use a broad query to compute p99 ts_rank across all entities
        # We use the 'simple' dictionary for a generic probe query that hits all tsvectors
        p99_sql = text(f"""
            SELECT COALESCE(
                percentile_cont(0.99) WITHIN GROUP (
                    ORDER BY ts_rank({col_name}, to_tsquery('simple', 'a'))
                ),
                1.0
            ) AS ceiling
            FROM entities
            WHERE {col_name} IS NOT NULL
        """)
        result = await session.execute(p99_sql)
        ceiling = float(result.scalar_one())
        # Ensure ceiling is positive (log1p denominator requirement)
        ceiling = max(ceiling, 0.01)

        session.add(SearchConfig(key=config_key, value=ceiling))
        log.info("ts_rank ceiling computed", column=col_name, ceiling=ceiling)

    await session.commit()
    log.info("ts_rank ceilings stored in search_config")


async def populate_entity_usages(
    session: AsyncSession,
    merged_entities: list[MergedEntity],
    provider: EmbeddingProvider,
    config: ServerConfig,
    artifacts_dir: Path,
) -> None:
    """
    Populate entity_usages table by exploding usages dicts from entity docs (FR-005, FR-006).

    For each entity with a non-null usages dict, parses each key as
    "{caller_compound}, {caller_sig}" and creates one EntityUsage row per entry.

    Usage embeddings are cached separately from entity embeddings with type="usages".
    Cache key is composite tuple (callee_id, caller_compound, caller_sig).

    Full rebuild: entity_usages is dropped and recreated each build (FR-005).
    tsvectors are generated via SQL after insertion for keyword search (FR-006).
    """
    log.info("Populating entity_usages table")

    # Collect all usage rows and their descriptions for batch embedding
    rows: list[EntityUsage] = []
    usage_keys: list[tuple[str, str, str]] = []  # (callee_id, caller_compound, caller_sig)

    for merged in merged_entities:
        if not merged.doc or not merged.doc.usages:
            continue
        callee_id = merged.entity_id
        for key, description in merged.doc.usages.items():
            caller_compound, caller_sig = key.split(", ", 1)
            rows.append(
                EntityUsage(
                    callee_id=callee_id,
                    caller_compound=caller_compound,
                    caller_sig=caller_sig,
                    description=description,
                    embedding=None,
                    search_vector=None,
                )
            )
            usage_keys.append((callee_id, caller_compound, caller_sig))

    log.info("Usage rows collected", count=len(rows))

    if rows:
        texts_by_key = {key: rows[idx].description for idx, key in enumerate(usage_keys)}
        usage_embeddings_raw = sync_embeddings_cache(
            artifacts_path=artifacts_dir,
            model_slug=config.embedding_model_slug,
            dimension=config.embedding_dimension,
            embedding_type="usages",
            current_keys=cast(list[str | tuple[str, ...]], usage_keys),
            texts_by_key=cast(dict[str | tuple[str, ...], str], texts_by_key),
            provider=provider,
        )
        usage_embeddings = cast(dict[tuple[str, str, str], list[float]], usage_embeddings_raw)
        for idx, usage_key in enumerate(usage_keys):
            rows[idx].embedding = usage_embeddings[usage_key]

    # Insert all rows
    session.add_all(rows)
    await session.commit()

    # Generate tsvectors for full-text search via SQL (FR-006)
    log.info("Generating entity_usages tsvectors")
    await session.execute(text("UPDATE entity_usages SET search_vector = to_tsvector('english', description)"))
    await session.commit()

    log.info("entity_usages table populated", rows=len(rows))


async def populate_edges(session: AsyncSession, edges: list[tuple[str, str, str]]) -> None:
    """Populate edges table."""
    log.info("Populating edges table", count=len(edges))

    edge_batch = [
        Edge(source_id=source, target_id=target, relationship=relationship.lower())
        for source, target, relationship in edges
    ]
    session.add_all(edge_batch)
    await session.commit()
    log.info("Edges table populated")


async def populate_capabilities(
    session: AsyncSession,
    cap_defs: dict,
    cap_graph: dict,
) -> None:
    """Populate capabilities and capability_edges tables."""
    log.info("Populating capabilities table")

    cap_graph_caps = cap_graph.get("capabilities", {})

    # Populate capabilities
    for cap_name, cap_def in cap_defs.items():
        function_count = 0
        if cap_name in cap_graph_caps:
            function_count = cap_graph_caps[cap_name].get("function_count", 0)

        description = cap_def.get("desc", "")

        capability = Capability(
            name=cap_name,
            type=cap_def.get("type", "domain"),
            description=description,
            function_count=function_count,
            stability=cap_def.get("stability"),
        )
        session.add(capability)

    await session.commit()

    # Populate capability edges from nested "dependencies" dict
    log.info("Populating capability_edges table")

    edge_count = 0
    for source_cap, targets in cap_graph.get("dependencies", {}).items():
        for target_cap, edge_data in targets.items():
            cap_edge = CapabilityEdge(
                source_cap=source_cap,
                target_cap=target_cap,
                edge_type=edge_data.get("edge_type", "requires_core"),
                call_count=edge_data.get("call_count", 0),
                in_dag=edge_data.get("in_dag", False),
            )
            session.add(cap_edge)
            edge_count += 1

    await session.commit()
    log.info("Capabilities tables populated", capabilities=len(cap_defs), edges=edge_count)


async def populate_entry_points(
    session: AsyncSession,
    merged_entities: list[MergedEntity],
    edges: list[tuple[str, str, str]],
) -> None:
    """
    Populate entry_points table from entities where is_entry_point=true.

    Computes transitive capabilities for each entry point by traversing
    CALLS edges and collecting all capability names in the call cone.
    """
    log.info("Populating entry_points table")

    # Build CALLS adjacency and capability map for call cone computation
    callees_map: dict[str, list[str]] = {}
    for source, target, rel in edges:
        if rel.lower() == "calls":
            callees_map.setdefault(source, []).append(target)

    cap_map: dict[str, str | None] = {m.entity_id: m.capability for m in merged_entities}

    entry_point_count = 0

    for merged in merged_entities:
        if merged.is_entry_point:
            name = merged.entity.name
            if name.startswith("do_"):
                entry_type = "do_"
            elif name.startswith("spell_"):
                entry_type = "spell_"
            elif name.startswith("spec_"):
                entry_type = "spec_"
            else:
                entry_type = None

            # BFS to collect all capabilities reachable via CALLS edges
            visited: set[str] = {merged.entity_id}
            queue = list(callees_map.get(merged.entity_id, []))
            visited.update(queue)
            caps: set[str] = set()

            if merged.capability:
                caps.add(merged.capability)

            while queue:
                current = queue.pop(0)
                cap = cap_map.get(current)
                if cap:
                    caps.add(cap)
                for callee in callees_map.get(current, []):
                    if callee not in visited:
                        visited.add(callee)
                        queue.append(callee)

            entry_point = EntryPoint(
                name=name,
                entity_id=merged.entity_id,
                capabilities=sorted(caps) if caps else [],
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

    validate_artifacts(config.artifacts_path)

    entity_db = load_entities(config.artifacts_path)
    doc_db = load_documents(config.artifacts_path)

    graph_node_ids = load_graph_node_ids(config.artifacts_path)
    merged_entities = merge_entities(entity_db, doc_db, graph_node_ids)

    assign_deterministic_ids(merged_entities)

    extract_source_code(merged_entities, config.project_root)

    cap_defs = load_capability_defs(config.artifacts_path)
    cap_graph = load_capability_graph(config.artifacts_path)

    assign_capabilities(merged_entities, cap_graph)

    edges = load_graph_edges(config.artifacts_path, merged_entities)
    compute_fan_metrics(merged_entities, edges)
    compute_bridge_flags(merged_entities, edges)

    compute_is_entry_point(merged_entities)
    compute_enriched_fields(merged_entities)

    # Derive qualified names from containment graph (must precede embed text assembly)
    derive_qualified_names(merged_entities, config.artifacts_path)
    build_symbol_searchable(merged_entities)

    provider = create_provider(config)

    # Dual embedding caches: doc + symbol
    entity_keys = [m.entity_id for m in merged_entities]

    doc_texts = build_doc_embed_texts(merged_entities)
    doc_embeddings_raw = sync_embeddings_cache(
        artifacts_path=config.artifacts_path,
        model_slug=config.embedding_model_slug,
        dimension=config.embedding_dimension,
        embedding_type="doc",
        current_keys=cast(list[str | tuple[str, ...]], entity_keys),
        texts_by_key=cast(dict[str | tuple[str, ...], str], doc_texts),
        provider=provider,
    )
    doc_embeddings = cast(dict[str, list[float]], doc_embeddings_raw)

    symbol_texts = build_symbol_embed_texts(merged_entities)
    symbol_embeddings_raw = sync_embeddings_cache(
        artifacts_path=config.artifacts_path,
        model_slug=config.embedding_model_slug,
        dimension=config.embedding_dimension,
        embedding_type="symbol",
        current_keys=cast(list[str | tuple[str, ...]], entity_keys),
        texts_by_key=cast(dict[str | tuple[str, ...], str], symbol_texts),
        provider=provider,
    )
    symbol_embeddings = cast(dict[str, list[float]], symbol_embeddings_raw)

    for merged in merged_entities:
        merged.doc_embedding = doc_embeddings.get(merged.entity_id)
        merged.symbol_embedding = symbol_embeddings.get(merged.entity_id)

    db_manager = DatabaseManager(config)

    # DDL (tables + indexes) uses engine directly, outside session
    await drop_and_create_schema(db_manager.engine)

    async with db_manager.session() as session:
        await populate_entities(session, merged_entities)
        await compute_and_store_tsrank_ceilings(session)
        await populate_entity_usages(session, merged_entities, provider, config, config.artifacts_path)
        await populate_edges(session, edges)
        await populate_capabilities(session, cap_defs, cap_graph)
        await populate_entry_points(session, merged_entities, edges)

        # Analyze tables for query planner
        log.info("Analyzing tables")
        await session.execute(text("ANALYZE entities"))
        await session.execute(text("ANALYZE edges"))
        await session.execute(text("ANALYZE entity_usages"))
        await session.execute(text("ANALYZE search_config"))
        await session.commit()

    await db_manager.dispose()

    elapsed = (datetime.now() - start_time).total_seconds()
    log.info("MCP database build complete", duration_seconds=round(elapsed, 1))


if __name__ == "__main__":
    asyncio.run(main())
