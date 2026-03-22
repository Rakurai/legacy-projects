"""
Search Tool - Hybrid semantic + keyword search.

Tools are decorated at module level with @mcp.tool() and remain directly importable.
"""

from typing import Annotated

from fastmcp import Context
from pydantic import BaseModel, Field

from server.app import get_ctx, mcp
from server.enums import SearchSource
from server.logging_config import log
from server.models import SearchResult
from server.search import hybrid_search, hybrid_search_usages

# -- Response Model --


class SearchResponse(BaseModel):
    """Response from search tool."""

    results: list[SearchResult]
    query: str
    result_count: int


@mcp.tool()
async def search(
    ctx: Context,
    query: Annotated[str, Field(description="Search query (natural language or keywords)")],
    source: Annotated[
        SearchSource,
        Field(description="Search source: 'entity' (default) or 'usages' (search by caller intent)"),
    ] = SearchSource.ENTITY,
    kind: Annotated[str | None, Field(description="Optional kind filter (function, class, etc.)")] = None,
    capability: Annotated[str | None, Field(description="Optional capability filter")] = None,
    top_k: Annotated[int, Field(ge=1, le=100, description="Number of results")] = 10,
) -> SearchResponse:
    """
    Perform multi-view search over documented code entities.

    Uses dual retrieval views (symbol + doc), cross-encoder reranking,
    and per-signal floor filtering.
    """
    lc = get_ctx(ctx)

    log.info("search", query=query, source=source, kind=kind, capability=capability, top_k=top_k)

    if source not in SearchSource:
        raise ValueError(f"Unsupported search source: {source!r}. Valid values: {[s.value for s in SearchSource]}")

    async with lc["db_manager"].session() as session:
        if source == SearchSource.USAGES:
            results = await hybrid_search_usages(
                session=session,
                query=query,
                embedding_provider=lc["embedding_provider"],
                kind=kind,
                capability=capability,
                limit=top_k,
            )
        else:
            results = await hybrid_search(
                session=session,
                query=query,
                embedding_provider=lc["embedding_provider"],
                kind=kind,
                capability=capability,
                limit=top_k,
                doc_view=lc["doc_view"],
                symbol_view=lc["symbol_view"],
            )

    return SearchResponse(
        results=results,
        query=query,
        result_count=len(results),
    )
