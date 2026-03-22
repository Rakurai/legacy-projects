"""
Tests for resolver stages 5 (keyword) and 6 (semantic).

These stages are only reached when stages 1-4 produce no results,
so we need queries that don't match any entity_id, signature, name, or prefix.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession

from server.resolver import resolve_entity
from server.db_models import Entity


@pytest.mark.asyncio
async def test_resolve_by_keyword_stage(
    test_session: AsyncSession, sample_entities: list[Entity], mock_embedding_provider
):
    """Stage 5 keyword search triggers when stages 1-4 miss.

    The query "Apply damage character" doesn't match any entity_id, signature,
    name, or name prefix — but it DOES match tsvector content (brief/details)
    for the damage function.
    """
    result = await resolve_entity(
        session=test_session,
        query="Apply damage character",  # Matches tsvector content, not name/sig
        kind=None,
        embedding_provider=mock_embedding_provider,
        limit=20,
    )

    assert result.status != "not_found", "Keyword stage should match tsvector content"
    assert result.match_type == "keyword"
    assert len(result.candidates) >= 1


@pytest.mark.asyncio
async def test_resolve_by_keyword_with_kind_filter(
    test_session: AsyncSession, sample_entities: list[Entity], mock_embedding_provider
):
    """Stage 5 keyword search respects kind filter — no variable matches 'Apply damage'."""
    result = await resolve_entity(
        session=test_session,
        query="Apply damage character",
        kind="variable",  # No variable has "Apply damage" in its tsvector
        embedding_provider=mock_embedding_provider,
        limit=20,
    )

    # No variable should match, so either not_found or only variables returned
    assert result.status == "not_found" or all(c.kind == "variable" for c in result.candidates)


@pytest.mark.asyncio
async def test_resolve_semantic_stage_with_mock_client(test_session: AsyncSession, sample_entities: list[Entity]):
    """Stage 6 semantic search triggers when stages 1-5 miss and embedding provider is available.

    Uses a mock embedding provider that returns a fake vector. Since test entities
    have no embeddings, the semantic stage should return not_found gracefully.
    """
    # Build a mock embedding provider conforming to EmbeddingProvider protocol
    mock_provider = MagicMock()
    mock_provider.dimension = 768
    mock_provider.aembed = AsyncMock(return_value=[0.1] * 768)

    result = await resolve_entity(
        session=test_session,
        query="zzz_completely_unmatchable_xyz_42",  # Won't match any stage 1-5
        kind=None,
        embedding_provider=mock_provider,
        limit=20,
    )

    # With no embeddings in test data, this should be not_found
    # But the semantic stage should have been attempted (no exception)
    assert result.status == "not_found"
    assert result.match_type == "semantic"


@pytest.mark.asyncio
async def test_resolve_semantic_stage_propagates_client_error(
    test_session: AsyncSession, sample_entities: list[Entity]
):
    """Stage 6 propagates embedding provider errors — fail-fast, no silent fallback."""
    mock_provider = MagicMock()
    mock_provider.dimension = 768
    mock_provider.aembed = AsyncMock(side_effect=RuntimeError("API down"))

    with pytest.raises(RuntimeError, match="API down"):
        await resolve_entity(
            session=test_session,
            query="zzz_completely_unmatchable_xyz_42",
            kind=None,
            embedding_provider=mock_provider,
            limit=20,
        )
