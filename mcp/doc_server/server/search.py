"""
Hybrid Search - Semantic + Keyword + Exact Match.

Combines three search strategies:
1. Exact match (signature or name) - highest boost
2. Semantic search (pgvector cosine similarity)
3. Keyword search (PostgreSQL full-text via tsvector)

Scores are normalized and combined with weights:
- Exact: 10x boost
- Semantic: 0.6 weight
- Keyword: 0.4 weight

Degrades gracefully to keyword-only mode if embedding service unavailable.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import Literal

from server.db_models import Entity
from server.models import SearchResult, EntitySummary, Provenance
from server.resolver import entity_to_summary
from server.logging_config import log


SearchMode = Literal["hybrid", "semantic_only", "keyword_fallback"]


async def hybrid_search(
    session: AsyncSession,
    query: str,
    embedding_client=None,
    kind: str | None = None,
    capability: str | None = None,
    min_doc_quality: str | None = None,
    limit: int = 20,
) -> tuple[list[SearchResult], SearchMode]:
    """
    Perform hybrid search combining semantic, keyword, and exact matching.

    Args:
        session: Database session
        query: Search query
        embedding_client: Optional OpenAI client for embeddings
        kind: Optional kind filter
        capability: Optional capability filter
        min_doc_quality: Optional minimum doc quality (high, medium, low)
        limit: Maximum results

    Returns:
        Tuple of (search results, search mode used)
    """
    log.info("Hybrid search", query=query, kind=kind, capability=capability)

    # Get query embedding (if available)
    query_embedding = None
    search_mode: SearchMode = "hybrid"

    if embedding_client:
        try:
            response = await embedding_client.embeddings.create(
                model="text-embedding-3-large",  # or configured model
                input=query,
                encoding_format="float"
            )
            query_embedding = response.data[0].embedding
            log.debug("Query embedding generated", dimensions=len(query_embedding))
        except Exception as e:
            log.warning("Embedding generation failed; falling back to keyword-only", error=str(e))
            search_mode = "keyword_fallback"
    else:
        log.info("Embedding client not available; using keyword-only mode")
        search_mode = "keyword_fallback"

    # Build filters
    filters = []
    if kind:
        filters.append(f"kind = '{kind}'")
    if capability:
        filters.append(f"capability = '{capability}'")
    if min_doc_quality:
        # Map quality to ordering: high > medium > low
        quality_order = {"high": 3, "medium": 2, "low": 1}
        min_order = quality_order.get(min_doc_quality, 1)
        if min_order == 3:
            filters.append("doc_quality = 'high'")
        elif min_order == 2:
            filters.append("doc_quality IN ('high', 'medium')")
        # low includes all

    filter_clause = " AND " + " AND ".join(filters) if filters else ""

    # Execute hybrid query
    if search_mode == "hybrid" and query_embedding:
        results = await _execute_hybrid_query(
            session, query, query_embedding, filter_clause, limit
        )
    else:
        results = await _execute_keyword_query(
            session, query, filter_clause, limit
        )

    log.info("Search complete", result_count=len(results), search_mode=search_mode)

    return results, search_mode


async def _execute_hybrid_query(
    session: AsyncSession,
    query: str,
    query_embedding: list[float],
    filter_clause: str,
    limit: int,
) -> list[SearchResult]:
    """
    Execute hybrid search query combining exact, semantic, and keyword.

    Query structure:
    - CTE for exact matches (signature or name)
    - CTE for semantic matches (pgvector cosine)
    - CTE for keyword matches (tsvector)
    - JOIN and combine scores: exact*10 + semantic*0.6 + keyword*0.4
    """
    hybrid_sql = text(f"""
        WITH exact AS (
            SELECT entity_id, 1.0 AS score
            FROM entities
            WHERE (signature = :query OR name = :query)
            {filter_clause}
        ),
        semantic AS (
            SELECT entity_id, 1 - (embedding <=> :embedding::vector) AS score
            FROM entities
            WHERE embedding IS NOT NULL
            {filter_clause}
            ORDER BY score DESC
            LIMIT 100
        ),
        keyword AS (
            SELECT entity_id, ts_rank(search_vector, plainto_tsquery('english', :query)) AS score
            FROM entities
            WHERE search_vector @@ plainto_tsquery('english', :query)
            {filter_clause}
            ORDER BY score DESC
            LIMIT 100
        )
        SELECT
            e.*,
            COALESCE(ex.score, 0) * 10 + COALESCE(s.score, 0) * 0.6 + COALESCE(k.score, 0) * 0.4 AS combined_score
        FROM entities e
        LEFT JOIN exact ex USING (entity_id)
        LEFT JOIN semantic s USING (entity_id)
        LEFT JOIN keyword k USING (entity_id)
        WHERE ex.entity_id IS NOT NULL OR s.entity_id IS NOT NULL OR k.entity_id IS NOT NULL
        ORDER BY combined_score DESC
        LIMIT :limit
    """)

    result = await session.execute(
        hybrid_sql,
        {"query": query, "embedding": query_embedding, "limit": limit}
    )

    rows = result.fetchall()

    # Convert to SearchResult objects
    search_results = []
    for row in rows:
        entity_dict = {k: v for k, v in row._mapping.items() if k != "combined_score"}
        entity = Entity(**entity_dict)
        summary = entity_to_summary(entity)

        # Determine provenance based on doc_state
        provenance: Provenance = "doxygen_extracted"
        if entity.doc_state in ("refined_summary", "refined_usage", "generated_summary"):
            provenance = "llm_generated"

        search_results.append(
            SearchResult(
                result_type="entity",
                score=min(float(row._mapping["combined_score"]), 1.0),  # Normalize to 0-1
                search_mode="hybrid",
                provenance=provenance,
                entity_summary=summary,
            )
        )

    return search_results


async def _execute_keyword_query(
    session: AsyncSession,
    query: str,
    filter_clause: str,
    limit: int,
) -> list[SearchResult]:
    """
    Execute keyword-only search (fallback when embeddings unavailable).

    Uses PostgreSQL full-text search with exact match boost.
    """
    keyword_sql = text(f"""
        WITH exact AS (
            SELECT entity_id, 1.0 AS score
            FROM entities
            WHERE (signature = :query OR name = :query)
            {filter_clause}
        ),
        keyword AS (
            SELECT entity_id, ts_rank(search_vector, plainto_tsquery('english', :query)) AS score
            FROM entities
            WHERE search_vector @@ plainto_tsquery('english', :query)
            {filter_clause}
            ORDER BY score DESC
            LIMIT 100
        )
        SELECT
            e.*,
            COALESCE(ex.score, 0) * 10 + COALESCE(k.score, 0) AS combined_score
        FROM entities e
        LEFT JOIN exact ex USING (entity_id)
        LEFT JOIN keyword k USING (entity_id)
        WHERE ex.entity_id IS NOT NULL OR k.entity_id IS NOT NULL
        ORDER BY combined_score DESC
        LIMIT :limit
    """)

    result = await session.execute(
        keyword_sql,
        {"query": query, "limit": limit}
    )

    rows = result.fetchall()

    search_results = []
    for row in rows:
        entity_dict = {k: v for k, v in row._mapping.items() if k != "combined_score"}
        entity = Entity(**entity_dict)
        summary = entity_to_summary(entity)

        provenance: Provenance = "doxygen_extracted"
        if entity.doc_state in ("refined_summary", "refined_usage", "generated_summary"):
            provenance = "llm_generated"

        search_results.append(
            SearchResult(
                result_type="entity",
                score=min(float(row._mapping["combined_score"]) / 10.0, 1.0),  # Normalize
                search_mode="keyword_fallback",
                provenance=provenance,
                entity_summary=summary,
            )
        )

    return search_results
