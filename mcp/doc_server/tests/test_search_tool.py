"""
Integration test for the search MCP tool wrapper.

Tests server.tools.search.search() via mock_ctx, not just hybrid_search() directly.
"""

import pytest
from unittest.mock import MagicMock

from server.tools.search import search


@pytest.mark.asyncio
async def test_search_tool_keyword_mode(mock_ctx, sample_entities):
    """Search tool returns results via mock context (keyword fallback)."""
    response = await search(
        ctx=mock_ctx,
        query="damage",
        limit=20,
    )

    assert response.search_mode == "keyword_fallback"
    assert response.query == "damage"
    assert response.result_count == len(response.results)
    assert response.result_count >= 1


@pytest.mark.asyncio
async def test_search_tool_unsupported_source(mock_ctx, sample_entities):
    """Search tool returns empty results for non-entity source."""
    response = await search(
        ctx=mock_ctx,
        query="damage",
        source="capability",  # type: ignore  — V1 only supports "entity"
        limit=20,
    )

    assert response.result_count == 0
    assert response.results == []
    assert response.search_mode == "keyword_fallback"


@pytest.mark.asyncio
async def test_search_tool_with_filters(mock_ctx, sample_entities):
    """Search tool passes kind and capability filters through."""
    response = await search(
        ctx=mock_ctx,
        query="damage",
        kind="function",
        capability="combat",
        limit=20,
    )

    for r in response.results:
        assert r.entity_summary.kind == "function"  # type: ignore
        assert r.entity_summary.capability == "combat"  # type: ignore


@pytest.mark.asyncio
async def test_search_tool_empty_results(mock_ctx, sample_entities):
    """Search tool returns empty for no-match query."""
    response = await search(
        ctx=mock_ctx,
        query="zzz_nonexistent_xyz_999",
        limit=20,
    )

    assert response.result_count == 0
    assert response.results == []
