"""
US3: Noise Filtering and Reranking — search contract tests.

Tests verify that:
- Nonsense queries return zero results (floor filtering removes all candidates)
- Returned results carry winning_view, winning_score, and losing_score metadata
- Results are sorted by score descending
- Exact matches bypass floor filtering and rank at top
"""

import pytest

from server.search import hybrid_search


@pytest.mark.asyncio
async def test_nonsense_query_returns_empty(test_session, sample_entities):
    """Floor filtering eliminates all candidates for nonsense queries."""
    results = await hybrid_search(
        session=test_session,
        query="xyzzy foobar baz",
        embedding_provider=None,
    )

    assert results == []


@pytest.mark.asyncio
async def test_results_sorted_descending(test_session, sample_entities):
    """Results are sorted by score descending."""
    results = await hybrid_search(
        session=test_session,
        query="damage",
        embedding_provider=None,
    )

    assert len(results) >= 1
    scores = [r.score for r in results]
    assert scores == sorted(scores, reverse=True)


@pytest.mark.asyncio
async def test_winning_view_metadata_present(test_session, sample_entities):
    """All results carry winning_view, winning_score, and losing_score."""
    results = await hybrid_search(
        session=test_session,
        query="damage",
        embedding_provider=None,
    )

    assert len(results) > 0
    for r in results:
        assert r.winning_view in ("doc", "symbol")
        assert r.winning_score >= 0.0
        assert r.losing_score >= 0.0


@pytest.mark.asyncio
async def test_exact_match_bypasses_floor_filter(test_session, sample_entities):
    """Exact name match survives floor filtering even if other signals are weak."""
    results = await hybrid_search(
        session=test_session,
        query="damage",
        embedding_provider=None,
    )

    assert len(results) > 0
    # Exact match entity should be present and boosted
    top = results[0]
    assert top.entity_summary is not None
    assert top.entity_summary.name == "damage"
    assert top.score >= 10.0


@pytest.mark.asyncio
async def test_limit_respected(test_session, sample_entities):
    """Results count does not exceed requested limit."""
    results = await hybrid_search(
        session=test_session,
        query="damage",
        embedding_provider=None,
        limit=2,
    )

    assert len(results) <= 2


@pytest.mark.asyncio
async def test_no_search_mode_field(test_session, sample_entities):
    """SearchResult no longer has a search_mode field (FR-070)."""
    results = await hybrid_search(
        session=test_session,
        query="damage",
        embedding_provider=None,
    )

    assert len(results) > 0
    assert not hasattr(results[0], "search_mode")


@pytest.mark.asyncio
async def test_score_non_negative(test_session, sample_entities):
    """All scores are non-negative."""
    results = await hybrid_search(
        session=test_session,
        query="combat character damage",
        embedding_provider=None,
    )

    for r in results:
        assert r.score >= 0.0
        assert r.winning_score >= 0.0
        assert r.losing_score >= 0.0
