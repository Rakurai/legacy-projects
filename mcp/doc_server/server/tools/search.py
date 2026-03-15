"""
Search Tool - Hybrid semantic + keyword search.

Tools are decorated at module level with @mcp.tool() and remain directly importable.
"""

from typing import Annotated

from fastmcp import Context
from pydantic import BaseModel, Field

from server.app import mcp, get_ctx
from server.enums import DocQuality, SearchMode
from server.logging_config import log
from server.models import SearchResult
from server.search import hybrid_search


# -- Response Model --

class SearchResponse(BaseModel):
    """Response from search tool."""
    search_mode: SearchMode
    results: list[SearchResult]
    query: str
    result_count: int


@mcp.tool()
async def search(
    ctx: Context,
    query: Annotated[str, Field(description="Search query (natural language or keywords)")],
    source: Annotated[
        str,
        Field(description="Search source ('entity' only in V1)"),
    ] = "entity",
    kind: Annotated[str | None, Field(description="Optional kind filter (function, class, etc.)")] = None,
    capability: Annotated[str | None, Field(description="Optional capability filter")] = None,
    min_doc_quality: Annotated[
        DocQuality | None,
        Field(description="Minimum documentation quality"),
    ] = None,
    limit: Annotated[int, Field(ge=1, le=100, description="Maximum results")] = 20,
) -> SearchResponse:
    """
    Perform hybrid semantic + keyword search.

    Combines exact match (10x boost), semantic similarity (0.6 weight),
    and keyword relevance (0.4 weight). Degrades to keyword-only if
    embedding service unavailable.
    """
    lc = get_ctx(ctx)

    log.info("search", query=query, kind=kind, capability=capability, limit=limit)

    if source != "entity":
        log.warning("Unsupported search source in V1", source=source)
        return SearchResponse(
            search_mode=SearchMode.KEYWORD_FALLBACK,
            results=[],
            query=query,
            result_count=0,
        )

    async with lc["db_manager"].session() as session:
        results, search_mode = await hybrid_search(
            session=session,
            query=query,
            embedding_client=lc["embedding_client"],
            embedding_model=lc["embedding_model"],
            kind=kind,
            capability=capability,
            min_doc_quality=min_doc_quality,
            limit=limit,
        )

    return SearchResponse(
        search_mode=search_mode,
        results=results,
        query=query,
        result_count=len(results),
    )
