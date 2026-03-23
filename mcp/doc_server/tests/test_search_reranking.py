"""
US3: Noise Filtering and Reranking — search contract tests.

Tests verify that:
- Nonsense queries return zero results (floor filtering removes all candidates)
- Returned results carry winning_view, winning_score, and losing_score metadata
- Results are sorted by score descending
- Exact matches bypass floor filtering and rank at top
"""

import pytest
from sqlalchemy import text

from server.search import hybrid_search


@pytest.mark.asyncio
async def test_nonsense_query_returns_empty(
    test_session, sample_entities, mock_embedding_provider, mock_doc_view, mock_symbol_view
):
    """Floor filtering eliminates all candidates for nonsense queries."""
    results = await hybrid_search(
        session=test_session,
        query="xyzzy foobar baz",
        doc_embedding_provider=mock_embedding_provider,
        symbol_embedding_provider=mock_embedding_provider,
        doc_view=mock_doc_view,
        symbol_view=mock_symbol_view,
    )

    assert results == []


@pytest.mark.asyncio
async def test_results_sorted_descending(
    test_session, sample_entities, mock_embedding_provider, mock_doc_view, mock_symbol_view
):
    """Results are sorted by (winning_score, losing_score) descending."""
    results = await hybrid_search(
        session=test_session,
        query="damage",
        doc_embedding_provider=mock_embedding_provider,
        symbol_embedding_provider=mock_embedding_provider,
        doc_view=mock_doc_view,
        symbol_view=mock_symbol_view,
    )

    assert len(results) >= 1
    sort_keys = [(r.winning_score, r.losing_score) for r in results]
    assert sort_keys == sorted(sort_keys, reverse=True)


@pytest.mark.asyncio
async def test_winning_view_metadata_present(
    test_session, sample_entities, mock_embedding_provider, mock_doc_view, mock_symbol_view
):
    """All results carry winning_view, winning_score, and losing_score."""
    results = await hybrid_search(
        session=test_session,
        query="damage",
        doc_embedding_provider=mock_embedding_provider,
        symbol_embedding_provider=mock_embedding_provider,
        doc_view=mock_doc_view,
        symbol_view=mock_symbol_view,
    )

    assert len(results) > 0
    for r in results:
        assert r.winning_view in ("doc", "symbol")
        assert r.score == r.winning_score
        assert isinstance(r.winning_score, float)
        assert isinstance(r.losing_score, float)


@pytest.mark.asyncio
async def test_exact_match_bypasses_floor_filter(
    test_session, sample_entities, mock_embedding_provider, mock_doc_view, mock_symbol_view
):
    """Exact name match survives floor filtering even if other signals are weak."""
    results = await hybrid_search(
        session=test_session,
        query="damage",
        doc_embedding_provider=mock_embedding_provider,
        symbol_embedding_provider=mock_embedding_provider,
        doc_view=mock_doc_view,
        symbol_view=mock_symbol_view,
    )

    assert len(results) > 0
    # Exact match entity should be present and sorted first by CE score
    top = results[0]
    assert top.entity_summary is not None
    assert top.entity_summary.name == "damage"


@pytest.mark.asyncio
async def test_limit_respected(test_session, sample_entities, mock_embedding_provider, mock_doc_view, mock_symbol_view):
    """Results count does not exceed requested limit."""
    results = await hybrid_search(
        session=test_session,
        query="damage",
        doc_embedding_provider=mock_embedding_provider,
        symbol_embedding_provider=mock_embedding_provider,
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
        doc_embedding_provider=mock_embedding_provider,
        symbol_embedding_provider=mock_embedding_provider,
        doc_view=mock_doc_view,
        symbol_view=mock_symbol_view,
    )

    assert len(results) > 0
    assert not hasattr(results[0], "search_mode")


@pytest.mark.asyncio
async def test_scores_preserve_winning_score_semantics(
    test_session, sample_entities, mock_embedding_provider, mock_doc_view, mock_symbol_view
):
    """Cross-encoder results preserve `score == winning_score` semantics."""
    results = await hybrid_search(
        session=test_session,
        query="combat character damage",
        doc_embedding_provider=mock_embedding_provider,
        symbol_embedding_provider=mock_embedding_provider,
        doc_view=mock_doc_view,
        symbol_view=mock_symbol_view,
    )

    for r in results:
        assert r.score == r.winning_score
        assert isinstance(r.winning_score, float)
        assert isinstance(r.losing_score, float)


@pytest.mark.asyncio
async def test_negative_rerank_scores_are_rejected_after_filtering(
    test_session,
    sample_entities,
    mock_embedding_provider,
    mock_doc_view,
    mock_symbol_view,
    monkeypatch,
):
    """Candidates that survive Stage 4 but rerank strongly negative are dropped."""

    async def fake_doc_semantic(*args, **kwargs):
        return {"fn:a1b2c3d": 0.9, "fn:b2c3d4e": 0.85}

    async def fake_symbol_semantic(*args, **kwargs):
        return {"fn:a1b2c3d": 0.88, "fn:b2c3d4e": 0.82}

    async def fake_empty(*args, **kwargs):
        return {}

    async def fake_arerank(query, documents):
        return [-6.0 for _ in documents]

    monkeypatch.setattr("server.search._doc_semantic_scores", fake_doc_semantic)
    monkeypatch.setattr("server.search._symbol_semantic_scores", fake_symbol_semantic)
    monkeypatch.setattr("server.search._doc_keyword_scores", fake_empty)
    monkeypatch.setattr("server.search._symbol_keyword_scores", fake_empty)
    monkeypatch.setattr("server.search._trigram_scores", fake_empty)
    mock_doc_view.cross_encoder.arerank.side_effect = fake_arerank
    mock_symbol_view.cross_encoder.arerank.side_effect = fake_arerank

    results = await hybrid_search(
        session=test_session,
        query="xyzzy foobar baz",
        doc_embedding_provider=mock_embedding_provider,
        symbol_embedding_provider=mock_embedding_provider,
        doc_view=mock_doc_view,
        symbol_view=mock_symbol_view,
    )

    assert results == []
