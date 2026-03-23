"""End-to-end entity-search regression coverage at the tool wrapper boundary.

These tests exercise the MCP search tool wrapper with database-backed entities and
mixed-sign reranker logits so response validation matches the documented contract.
"""

import pytest

from server.tools.search import search


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("query", "expected_name", "expected_count"),
    [
        ("damage", "damage", 1),
        ("Combat::damage", "damage", 1),
        ("armor resistances", "damage", 1),
        ("", None, 0),
        ("xyzzy foobar baz", None, 0),
    ],
)
async def test_entity_search_wrapper_handles_mixed_sign_logits(mock_ctx, sample_entities, query, expected_name, expected_count):
    """Entity search wrapper accepts raw CE logits, including negative losing scores."""
    response = await search(
        ctx=mock_ctx,
        query=query,
        top_k=10,
    )

    assert response.result_count == len(response.results)
    assert response.result_count >= expected_count

    if expected_name is None:
        assert response.results == []
        return

    assert response.result_count > 0
    top = response.results[0]
    assert top.entity_summary is not None
    assert top.entity_summary.name == expected_name
    assert top.score == top.winning_score


@pytest.mark.asyncio
async def test_entity_search_returns_exact_name_match(mock_ctx, sample_entities):
    """Exact name match entity appears in results (CE determines final ordering)."""
    response = await search(
        ctx=mock_ctx,
        query="Character",
        top_k=10,
    )

    assert response.result_count > 0
    names = [r.entity_summary.name for r in response.results if r.entity_summary]
    assert "Character" in names


@pytest.mark.asyncio
async def test_entity_search_wrapper_allows_negative_losing_scores(mock_ctx, sample_entities):
    """Tool-layer serialization accepts negative losing logits for entity results."""
    # Use a sentence-like query (spaces → not symbol-like) so standard max(doc, sym)
    # arbitration applies and the losing view can produce negative logits.
    response = await search(
        ctx=mock_ctx,
        query="armor resistances",
        top_k=10,
    )

    assert response.result_count > 0
    assert any(result.losing_score < 0.0 for result in response.results)