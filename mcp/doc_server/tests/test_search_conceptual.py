"""
US2: Behavioral / Conceptual Search — search contract tests.

Tests verify that natural-language behavioral queries surface entities
through documentation-driven matching (doc keyword channel) even when
the query terms do not appear in entity names or signatures.
"""

import pytest

from server.search import hybrid_search


@pytest.mark.asyncio
async def test_prose_query_finds_documented_entity(test_session, sample_entities):
    """Natural-language query matching doc prose surfaces the entity."""
    # "armor resistances" appears in damage entity's details field
    results = await hybrid_search(
        session=test_session,
        query="armor resistances",
        embedding_provider=None,
    )

    assert len(results) > 0
    entity_ids = [r.entity_summary.entity_id for r in results if r.entity_summary]
    assert "fn:a1b2c3d" in entity_ids  # damage entity


@pytest.mark.asyncio
async def test_behavioral_query_matches_notes(test_session, sample_entities):
    """Query matching notes/rationale fields surfaces entity via doc keyword channel."""
    # "poison" does not appear in any entity name but is in notes for damage ("Damage is capped...")
    # "immortal" appears in damage notes
    results = await hybrid_search(
        session=test_session,
        query="immortal characters immune",
        embedding_provider=None,
    )

    assert len(results) > 0
    top_ids = [r.entity_summary.entity_id for r in results if r.entity_summary]
    assert "fn:a1b2c3d" in top_ids  # damage entity has "Immortal characters are immune" in notes


@pytest.mark.asyncio
async def test_doc_query_does_not_match_symbol_only(test_session, sample_entities):
    """Query with no doc-prose match returns empty or low results."""
    results = await hybrid_search(
        session=test_session,
        query="zzz_completely_unrelated_concept_999",
        embedding_provider=None,
    )

    assert len(results) == 0


@pytest.mark.asyncio
async def test_doc_results_carry_winning_view(test_session, sample_entities):
    """Doc-channel results carry winning_view metadata."""
    results = await hybrid_search(
        session=test_session,
        query="combat damage",
        embedding_provider=None,
    )

    assert len(results) > 0
    for r in results:
        assert r.winning_view in ("doc", "symbol")
        assert r.winning_score >= 0.0
        assert r.losing_score >= 0.0


@pytest.mark.asyncio
async def test_kind_filter_with_prose_query(test_session, sample_entities):
    """Kind filter works with prose-based queries."""
    results = await hybrid_search(
        session=test_session,
        query="combat damage armor",
        embedding_provider=None,
        kind="function",
    )

    for r in results:
        assert r.entity_summary is not None
        assert r.entity_summary.kind == "function"


@pytest.mark.asyncio
async def test_capability_filter_with_prose_query(test_session, sample_entities):
    """Capability filter works with prose-based queries."""
    results = await hybrid_search(
        session=test_session,
        query="damage character",
        embedding_provider=None,
        capability="combat",
    )

    for r in results:
        assert r.entity_summary is not None
        assert r.entity_summary.capability == "combat"


@pytest.mark.asyncio
async def test_rationale_field_searchable(test_session, sample_entities):
    """Rationale text is indexed and searchable via doc keyword channel."""
    # "balance" appears in damage entity's rationale
    results = await hybrid_search(
        session=test_session,
        query="balance consistently",
        embedding_provider=None,
    )

    assert len(results) > 0
    entity_ids = [r.entity_summary.entity_id for r in results if r.entity_summary]
    assert "fn:a1b2c3d" in entity_ids
