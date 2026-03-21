"""
Integration tests for hybrid search.

Tests multi-view search pipeline with keyword channels (no embedding provider).
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from server.db_models import Entity
from server.search import hybrid_search


@pytest.mark.asyncio
async def test_search_exact_match_boost(test_session: AsyncSession, sample_entities: list[Entity]):
    """Test that exact matches receive highest scores."""
    results = await hybrid_search(
        session=test_session,
        query="damage",
        embedding_provider=None,
        limit=20,
    )

    assert len(results) >= 1
    # Exact match should be first
    assert results[0].entity_summary.name == "damage"  # type: ignore


@pytest.mark.asyncio
async def test_search_with_kind_filter(test_session: AsyncSession, sample_entities: list[Entity]):
    """Test search with kind filter."""
    results = await hybrid_search(
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
    results = await hybrid_search(
        session=test_session,
        query="damage",
        embedding_provider=None,
        capability="combat",
        limit=20,
    )

    assert all(r.entity_summary.capability == "combat" for r in results)  # type: ignore
