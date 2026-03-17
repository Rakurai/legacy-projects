"""
Integration tests for hybrid search.

Tests semantic + keyword + exact match combination and fallback modes.
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from server.search import hybrid_search
from server.db_models import Entity


@pytest.mark.asyncio
async def test_search_exact_match_boost(test_session: AsyncSession, sample_entities: list[Entity]):
    """Test that exact matches receive highest scores."""
    results, mode = await hybrid_search(
        session=test_session,
        query="damage",
        embedding_provider=None,  # Keyword-only mode
        limit=20,
    )

    assert mode == "keyword_fallback"
    assert len(results) >= 1

    # Exact match should be first
    assert results[0].entity_summary.name == "damage"  # type: ignore
    assert results[0].score > 0.5  # High score due to exact match


@pytest.mark.asyncio
async def test_search_with_kind_filter(test_session: AsyncSession, sample_entities: list[Entity]):
    """Test search with kind filter."""
    results, mode = await hybrid_search(
        session=test_session,
        query="damage",
        embedding_provider=None,
        kind="function",
        limit=20,
    )

    assert all(r.entity_summary.kind == "function" for r in results)  # type: ignore


@pytest.mark.asyncio
async def test_search_with_capability_filter(test_session: AsyncSession, sample_entities: list[Entity]):
    """Test search with capability filter."""
    results, mode = await hybrid_search(
        session=test_session,
        query="damage",
        embedding_provider=None,
        capability="combat",
        limit=20,
    )

    assert all(r.entity_summary.capability == "combat" for r in results)  # type: ignore


@pytest.mark.asyncio
async def test_search_provenance_tagging(test_session: AsyncSession, sample_entities: list[Entity]):
    """Test that search results include correct provenance."""
    results, mode = await hybrid_search(
        session=test_session,
        query="damage",
        embedding_provider=None,
        limit=20,
    )

    for result in results:
        assert result.provenance == "precomputed"
        assert result.search_mode == "keyword_fallback"
