"""
Search Tool - Hybrid semantic + keyword search.

Combines exact matching, semantic similarity (pgvector), and keyword search (tsvector).
Degrades gracefully to keyword-only mode when embedding service unavailable.
"""

from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Literal

from server.search import hybrid_search
from server.models import SearchResult
from server.logging_config import log


class SearchParams(BaseModel):
    """Parameters for search tool."""
    query: str = Field(description="Search query (natural language or keywords)")
    source: Literal["entity"] = Field(
        default="entity",
        description="Search source (V2-reserved: 'entity' or 'subsystem_doc'; V1 only supports 'entity')"
    )
    kind: str | None = Field(default=None, description="Optional kind filter (function, class, etc.)")
    capability: str | None = Field(default=None, description="Optional capability filter")
    min_doc_quality: Literal["high", "medium", "low"] | None = Field(
        default=None,
        description="Minimum documentation quality"
    )
    limit: int = Field(default=20, ge=1, le=100, description="Maximum results")


class SearchResponse(BaseModel):
    """Response from search tool."""
    search_mode: Literal["hybrid", "semantic_only", "keyword_fallback"]
    results: list[SearchResult]
    query: str
    result_count: int


async def search_tool(
    session: AsyncSession,
    params: SearchParams,
    embedding_client=None,
) -> SearchResponse:
    """
    Perform hybrid semantic + keyword search.

    Search strategy:
    1. Exact match boost (signature or name = query) - 10x weight
    2. Semantic similarity (pgvector cosine) - 0.6 weight
    3. Keyword relevance (tsvector ts_rank) - 0.4 weight

    Degrades to keyword-only if embedding service unavailable (explicit mode reporting).

    Args:
        session: Database session
        params: Search parameters
        embedding_client: Optional OpenAI client for embeddings

    Returns:
        Search results with mode indicator
    """
    log.info(
        "search tool invoked",
        query=params.query,
        source=params.source,
        kind=params.kind,
        capability=params.capability,
        limit=params.limit,
    )

    # V2-reserved: only 'entity' source is functional in V1
    if params.source != "entity":
        log.warning("Unsupported search source in V1", source=params.source)
        return SearchResponse(
            search_mode="keyword_fallback",
            results=[],
            query=params.query,
            result_count=0,
        )

    # Execute hybrid search
    results, search_mode = await hybrid_search(
        session=session,
        query=params.query,
        embedding_client=embedding_client,
        kind=params.kind,
        capability=params.capability,
        min_doc_quality=params.min_doc_quality,
        limit=params.limit,
    )

    return SearchResponse(
        search_mode=search_mode,
        results=results,
        query=params.query,
        result_count=len(results),
    )
