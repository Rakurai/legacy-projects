"""
US4: Qualified Name Navigation — search contract tests.

Tests verify that scoped queries (containing '::') disambiguate
same-name entities by qualified scope, and that database rows
contain derived qualified_name values.
"""

import pytest

from server.search import hybrid_search


@pytest.mark.asyncio
async def test_scoped_query_boosts_matching_scope(test_session, sample_entities):
    """Scoped query 'Combat::damage' ranks Combat-scoped entity above Logging-scoped."""
    results = await hybrid_search(
        session=test_session,
        query="Combat::damage",
        embedding_provider=None,
    )

    assert len(results) >= 1
    top = results[0]
    assert top.entity_summary is not None
    assert top.entity_summary.entity_id == "fn:a1b2c3d"  # Combat::damage


@pytest.mark.asyncio
async def test_different_scope_query(test_session, sample_entities):
    """Scoped query 'Logging::damage' ranks Logging-scoped entity at top."""
    results = await hybrid_search(
        session=test_session,
        query="Logging::damage",
        embedding_provider=None,
    )

    assert len(results) >= 1
    top = results[0]
    assert top.entity_summary is not None
    assert top.entity_summary.entity_id == "fn:h8i9j0k"  # Logging::damage


@pytest.mark.asyncio
async def test_unscoped_query_returns_both(test_session, sample_entities):
    """Unscoped 'damage' query returns both Combat::damage and Logging::damage."""
    results = await hybrid_search(
        session=test_session,
        query="damage",
        embedding_provider=None,
    )

    entity_ids = {r.entity_summary.entity_id for r in results if r.entity_summary}
    assert "fn:a1b2c3d" in entity_ids  # Combat::damage
    assert "fn:h8i9j0k" in entity_ids  # Logging::damage


@pytest.mark.asyncio
async def test_scoped_match_gets_boost(test_session, sample_entities):
    """Scope-matched entity gets score >= 10.0 (same as exact match boost)."""
    results = await hybrid_search(
        session=test_session,
        query="Combat::damage",
        embedding_provider=None,
    )

    assert len(results) >= 1
    combat_result = next(r for r in results if r.entity_summary and r.entity_summary.entity_id == "fn:a1b2c3d")
    assert combat_result.score >= 10.0


@pytest.mark.asyncio
async def test_qualified_name_populated(test_session, sample_entities):
    """Sample entities have qualified_name values set in the database."""
    from sqlmodel import select

    from server.db_models import Entity

    result = await test_session.execute(select(Entity.qualified_name).where(Entity.entity_id == "fn:a1b2c3d"))
    qn = result.scalar_one()
    assert qn == "Combat::damage"


@pytest.mark.asyncio
async def test_nonexistent_scope_returns_bare_name_results(test_session, sample_entities):
    """Scoped query with no matching scope falls back to bare name search."""
    results = await hybrid_search(
        session=test_session,
        query="Nonexistent::damage",
        embedding_provider=None,
    )

    # Should still find "damage" entities via bare name channels
    assert len(results) >= 1
    names = {r.entity_summary.name for r in results if r.entity_summary}
    assert "damage" in names
