"""
Integration test for the search MCP tool wrapper.

Tests server.tools.search.search() via mock_ctx, not just hybrid_search() directly.
"""

import pytest

from server.tools.search import search


@pytest.mark.asyncio
async def test_search_tool_returns_results(mock_ctx, sample_entities):
    """Search tool returns results via mock context."""
    response = await search(
        ctx=mock_ctx,
        query="damage",
        top_k=20,
    )

    assert response.query == "damage"
    assert response.result_count == len(response.results)
    assert response.result_count >= 1


@pytest.mark.asyncio
async def test_search_tool_unsupported_source(mock_ctx, sample_entities):
    """Search tool raises ValueError for unsupported source values."""
    with pytest.raises(ValueError, match="Unsupported search source"):
        await search(
            ctx=mock_ctx,
            query="damage",
            source="capability",  # type: ignore  — not a valid SearchSource
            top_k=20,
        )


@pytest.mark.asyncio
async def test_search_tool_with_filters(mock_ctx, sample_entities):
    """Search tool passes kind and capability filters through."""
    response = await search(
        ctx=mock_ctx,
        query="damage",
        kind="function",
        capability="combat",
        top_k=20,
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
        top_k=20,
    )

    assert response.result_count == 0
    assert response.results == []


# ---------- source="usages" (US2) ----------


@pytest.mark.asyncio
async def test_search_usages_returns_matching_usages(mock_ctx, sample_entities, sample_entity_usages):
    """source='usages' returns results with matching_usages field populated."""
    # "poison" appears in the affect_tick usage description
    response = await search(
        ctx=mock_ctx,
        query="poison damage",
        source="usages",
        top_k=10,
    )

    assert response.result_count > 0
    for result in response.results:
        # Each result must have matching_usages populated
        assert result.matching_usages is not None
        assert len(result.matching_usages) > 0


@pytest.mark.asyncio
async def test_search_usages_groups_by_callee(mock_ctx, sample_entities, sample_entity_usages):
    """source='usages' returns at most one result per callee entity_id."""
    response = await search(
        ctx=mock_ctx,
        query="damage attack combat",
        source="usages",
        top_k=10,
    )

    callee_ids = [r.entity_summary.entity_id for r in response.results if r.entity_summary]  # type: ignore
    assert len(callee_ids) == len(set(callee_ids)), "Duplicate callee entity_ids in usages search results"


@pytest.mark.asyncio
async def test_search_usages_kind_filter(mock_ctx, sample_entities, sample_entity_usages):
    """source='usages' kind filter applies to callee entity."""
    response = await search(
        ctx=mock_ctx,
        query="damage",
        source="usages",
        kind="function",
        top_k=10,
    )

    for result in response.results:
        assert result.entity_summary is not None
        assert result.entity_summary.kind == "function"  # type: ignore


@pytest.mark.asyncio
async def test_search_entity_default_unchanged(mock_ctx, sample_entities):
    """Default source='entity' behavior is unchanged after adding usages support."""
    response = await search(
        ctx=mock_ctx,
        query="damage",
        top_k=10,
    )

    assert response.result_count > 0
    # Default results should NOT have matching_usages (entity search)
    for result in response.results:
        assert result.matching_usages is None


# ---------- Score threshold contract tests (I-002) ----------


@pytest.mark.asyncio
async def test_exact_match_score_dominates(mock_ctx, sample_entities):
    """Exact name match returns score > 1.0 — distinguishable from weak matches (SC-004 / FR-009)."""
    response = await search(
        ctx=mock_ctx,
        query="damage",
        top_k=10,
    )

    assert response.result_count > 0
    # Exact match entity (name="damage") must be first and score > 1.0
    assert response.results[0].entity_summary is not None  # type: ignore
    assert response.results[0].entity_summary.name == "damage"  # type: ignore
    assert response.results[0].score > 1.0


@pytest.mark.asyncio
async def test_returned_results_have_valid_metadata(mock_ctx, sample_entities):
    """All returned results carry winning_view and score metadata."""
    response = await search(
        ctx=mock_ctx,
        query="damage",
        top_k=20,
    )

    assert response.result_count > 0
    for result in response.results:
        assert result.winning_view in ("doc", "symbol")
        assert result.winning_score >= 0.0
        assert result.losing_score >= 0.0
        assert result.score >= 0.0
