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
async def test_resolve_by_keyword_stage(test_session: AsyncSession, sample_entities: list[Entity]):
    """Stage 5 keyword search triggers when stages 1-4 miss.

    The query "Apply damage character" doesn't match any entity_id, signature,
    name, or name prefix — but it DOES match tsvector content (brief/details)
    for the damage function.
    """
    result = await resolve_entity(
        session=test_session,
        query="Apply damage character",  # Matches tsvector content, not name/sig
        kind=None,
        embedding_client=None,
        limit=20,
    )

    assert result.status != "not_found", "Keyword stage should match tsvector content"
    assert result.match_type == "keyword"
    assert len(result.candidates) >= 1


@pytest.mark.asyncio
async def test_resolve_by_keyword_with_kind_filter(test_session: AsyncSession, sample_entities: list[Entity]):
    """Stage 5 keyword search respects kind filter — no variable matches 'Apply damage'."""
    result = await resolve_entity(
        session=test_session,
        query="Apply damage character",
        kind="variable",  # No variable has "Apply damage" in its tsvector
        embedding_client=None,
        limit=20,
    )

    # No variable should match, so either not_found or only variables returned
    assert result.status == "not_found" or all(c.kind == "variable" for c in result.candidates)


@pytest.mark.asyncio
async def test_resolve_semantic_stage_with_mock_client(test_session: AsyncSession, sample_entities: list[Entity]):
    """Stage 6 semantic search triggers when stages 1-5 miss and embedding client is available.

    Uses a mock embedding client that returns a fake vector. Since test entities
    have no embeddings, the semantic stage should return not_found gracefully.
    """
    # Build a mock embedding client
    mock_embedding = MagicMock()
    mock_response = MagicMock()
    mock_response.data = [MagicMock(embedding=[0.1] * 4096)]
    mock_embedding.embeddings = MagicMock()
    mock_embedding.embeddings.create = AsyncMock(return_value=mock_response)

    result = await resolve_entity(
        session=test_session,
        query="zzz_completely_unmatchable_xyz_42",  # Won't match any stage 1-5
        kind=None,
        embedding_client=mock_embedding,
        embedding_model="test-model",
        limit=20,
    )

    # With no embeddings in test data, this should be not_found
    # But the semantic stage should have been attempted (no exception)
    assert result.status == "not_found"
    assert result.match_type == "semantic"


@pytest.mark.asyncio
async def test_resolve_semantic_stage_handles_client_error(test_session: AsyncSession, sample_entities: list[Entity]):
    """Stage 6 gracefully handles embedding client errors."""
    mock_embedding = MagicMock()
    mock_embedding.embeddings = MagicMock()
    mock_embedding.embeddings.create = AsyncMock(side_effect=RuntimeError("API down"))

    result = await resolve_entity(
        session=test_session,
        query="zzz_completely_unmatchable_xyz_42",
        kind=None,
        embedding_client=mock_embedding,
        embedding_model="test-model",
        limit=20,
    )

    # Should still return not_found, not propagate the exception
    assert result.status == "not_found"



