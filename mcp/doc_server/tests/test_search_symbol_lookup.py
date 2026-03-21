"""
US1: Symbol-Precise Entity Lookup — search contract tests.

Tests verify that exact name matches, partial/fuzzy trigram matches,
and symbol keyword matches surface the correct entities through the
multi-view search pipeline.
"""

import pytest

from server.search import hybrid_search


@pytest.mark.asyncio
async def test_exact_name_match_ranks_first(test_session, sample_entities):
    """Exact bare name match appears in results with score >= 10.0."""
    results = await hybrid_search(
        session=test_session,
        query="damage",
        embedding_provider=None,
    )

    assert len(results) > 0
    top = results[0]
    assert top.entity_summary is not None
    assert top.entity_summary.name == "damage"
    assert top.score >= 10.0


@pytest.mark.asyncio
async def test_exact_signature_match(test_session, sample_entities):
    """Exact signature match appears in results."""
    results = await hybrid_search(
        session=test_session,
        query="void damage(Character *ch, Character *victim, int dam)",
        embedding_provider=None,
    )

    assert len(results) > 0
    entity_ids = [r.entity_summary.entity_id for r in results if r.entity_summary]
    assert "fn:a1b2c3d" in entity_ids


@pytest.mark.asyncio
async def test_symbol_keyword_no_stemming(test_session, sample_entities):
    """Symbol keyword search uses simple dictionary (no stemming).

    'Character' should match as an identifier, not be stemmed to 'charact'.
    """
    results = await hybrid_search(
        session=test_session,
        query="Character",
        embedding_provider=None,
    )

    assert len(results) > 0
    names = [r.entity_summary.name for r in results if r.entity_summary]
    assert "Character" in names


@pytest.mark.asyncio
async def test_empty_query_returns_empty(test_session, sample_entities):
    """Empty query returns zero results."""
    results = await hybrid_search(
        session=test_session,
        query="",
        embedding_provider=None,
    )
    assert results == []


@pytest.mark.asyncio
async def test_results_have_winning_view_metadata(test_session, sample_entities):
    """All results carry winning_view, winning_score, losing_score."""
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
async def test_kind_filter_applied(test_session, sample_entities):
    """Kind filter restricts results to matching entity kind."""
    results = await hybrid_search(
        session=test_session,
        query="damage",
        embedding_provider=None,
        kind="function",
    )

    for r in results:
        assert r.entity_summary is not None
        assert r.entity_summary.kind == "function"


@pytest.mark.asyncio
async def test_capability_filter_applied(test_session, sample_entities):
    """Capability filter restricts results to matching capability."""
    results = await hybrid_search(
        session=test_session,
        query="damage",
        embedding_provider=None,
        capability="combat",
    )

    for r in results:
        assert r.entity_summary is not None
        assert r.entity_summary.capability == "combat"


@pytest.mark.asyncio
async def test_no_search_mode_in_results(test_session, sample_entities):
    """SearchResult no longer has a search_mode field (FR-070)."""
    results = await hybrid_search(
        session=test_session,
        query="damage",
        embedding_provider=None,
    )

    assert len(results) > 0
    assert not hasattr(results[0], "search_mode")
