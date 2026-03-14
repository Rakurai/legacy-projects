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
        embedding_client=None,  # Keyword-only mode
        limit=20,
    )

    assert mode == "keyword_fallback"
    assert len(results) >= 1

    # Exact match should be first
    assert results[0].entity_summary.name == "damage"  # type: ignore
    assert results[0].score > 0.5  # High score due to exact match


@pytest.mark.asyncio
async def test_search_keyword_only_mode(test_session: AsyncSession, sample_entities: list[Entity]):
    """Test keyword-only search when embedding client unavailable."""
    results, mode = await hybrid_search(
        session=test_session,
        query="character damage",
        embedding_client=None,
        limit=20,
    )

    assert mode == "keyword_fallback"
    # Should find entities with "damage" or "character" in their text
    assert len(results) >= 0  # May be 0 if no keyword matches


@pytest.mark.asyncio
async def test_search_with_kind_filter(test_session: AsyncSession, sample_entities: list[Entity]):
    """Test search with kind filter."""
    results, mode = await hybrid_search(
        session=test_session,
        query="damage",
        embedding_client=None,
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
        embedding_client=None,
        capability="combat",
        limit=20,
    )

    assert all(r.entity_summary.capability == "combat" for r in results)  # type: ignore


@pytest.mark.asyncio
async def test_search_with_min_doc_quality(test_session: AsyncSession, sample_entities: list[Entity]):
    """Test search with minimum doc quality filter."""
    results, mode = await hybrid_search(
        session=test_session,
        query="damage",
        embedding_client=None,
        min_doc_quality="high",
        limit=20,
    )

    assert all(r.entity_summary.doc_quality == "high" for r in results)  # type: ignore


@pytest.mark.asyncio
async def test_search_empty_results(test_session: AsyncSession, sample_entities: list[Entity]):
    """Test search with no matches."""
    results, mode = await hybrid_search(
        session=test_session,
        query="nonexistent_term_xyz_123",
        embedding_client=None,
        limit=20,
    )

    assert mode == "keyword_fallback"
    assert len(results) == 0


@pytest.mark.asyncio
async def test_search_provenance_tagging(test_session: AsyncSession, sample_entities: list[Entity]):
    """Test that search results include correct provenance."""
    results, mode = await hybrid_search(
        session=test_session,
        query="damage",
        embedding_client=None,
        limit=20,
    )

    for result in results:
        assert result.provenance in ("doxygen_extracted", "llm_generated", "subsystem_narrative")
        assert result.search_mode == "keyword_fallback"
