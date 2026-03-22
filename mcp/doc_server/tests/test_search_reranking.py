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
async def test_nonsense_query_returns_empty(
    test_session, sample_entities, mock_embedding_provider, mock_doc_view, mock_symbol_view
):
    """Floor filtering eliminates all candidates for nonsense queries."""
    results = await hybrid_search(
        session=test_session,
        query="xyzzy foobar baz",
        embedding_provider=mock_embedding_provider,
        doc_view=mock_doc_view,
        symbol_view=mock_symbol_view,
    )

    assert results == []


@pytest.mark.asyncio
async def test_results_sorted_descending(
    test_session, sample_entities, mock_embedding_provider, mock_doc_view, mock_symbol_view
):
    """Results are sorted by (tier, score) descending."""
    results = await hybrid_search(
        session=test_session,
        query="damage",
        embedding_provider=mock_embedding_provider,
        doc_view=mock_doc_view,
        symbol_view=mock_symbol_view,
    )

    assert len(results) >= 1
    sort_keys = [(r.sort_tier, r.score) for r in results]
    assert sort_keys == sorted(sort_keys, reverse=True)


@pytest.mark.asyncio
async def test_winning_view_metadata_present(
    test_session, sample_entities, mock_embedding_provider, mock_doc_view, mock_symbol_view
):
    """All results carry winning_view, winning_score, and losing_score."""
    results = await hybrid_search(
        session=test_session,
        query="damage",
        embedding_provider=mock_embedding_provider,
        doc_view=mock_doc_view,
        symbol_view=mock_symbol_view,
    )

    assert len(results) > 0
    for r in results:
        assert r.winning_view in ("doc", "symbol")
        assert r.winning_score >= 0.0
        assert r.losing_score >= 0.0


@pytest.mark.asyncio
async def test_exact_match_bypasses_floor_filter(
    test_session, sample_entities, mock_embedding_provider, mock_doc_view, mock_symbol_view
):
    """Exact name match survives floor filtering even if other signals are weak."""
    results = await hybrid_search(
        session=test_session,
        query="damage",
        embedding_provider=mock_embedding_provider,
        doc_view=mock_doc_view,
        symbol_view=mock_symbol_view,
    )

    assert len(results) > 0
    # Exact match entity should be present and sorted first via tier
    top = results[0]
    assert top.entity_summary is not None
    assert top.entity_summary.name == "damage"
    assert top.sort_tier >= 1


@pytest.mark.asyncio
async def test_limit_respected(test_session, sample_entities, mock_embedding_provider, mock_doc_view, mock_symbol_view):
    """Results count does not exceed requested limit."""
    results = await hybrid_search(
        session=test_session,
        query="damage",
        embedding_provider=mock_embedding_provider,
        doc_view=mock_doc_view,
        symbol_view=mock_symbol_view,
        limit=2,
    )

    assert len(results) <= 2


@pytest.mark.asyncio
async def test_no_search_mode_field(
    test_session, sample_entities, mock_embedding_provider, mock_doc_view, mock_symbol_view
):
    """SearchResult no longer has a search_mode field (FR-070)."""
    results = await hybrid_search(
        session=test_session,
        query="damage",
        embedding_provider=mock_embedding_provider,
        doc_view=mock_doc_view,
        symbol_view=mock_symbol_view,
    )

    assert len(results) > 0
    assert not hasattr(results[0], "search_mode")


@pytest.mark.asyncio
async def test_score_non_negative(
    test_session, sample_entities, mock_embedding_provider, mock_doc_view, mock_symbol_view
):
    """All scores are non-negative."""
    results = await hybrid_search(
        session=test_session,
        query="combat character damage",
        embedding_provider=mock_embedding_provider,
        doc_view=mock_doc_view,
        symbol_view=mock_symbol_view,
    )

    for r in results:
        assert r.score >= 0.0
        assert r.winning_score >= 0.0
        assert r.losing_score >= 0.0
