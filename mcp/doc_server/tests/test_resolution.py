"""
Integration tests for entity resolution pipeline.

Tests the multi-stage resolution: entity_id → signature → name → prefix → keyword → semantic.
Also covers ResolutionResult helper method (to_entity_summaries).
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from server.resolver import resolve_entity, ResolutionResult, entity_to_summary
from server.db_models import Entity
from server.models import EntitySummary


@pytest.mark.asyncio
async def test_resolve_by_entity_id(test_session: AsyncSession, sample_entities: list[Entity], mock_embedding_provider):
    """Test exact entity_id match (stage 1)."""
    entity_id = sample_entities[0].entity_id

    result = await resolve_entity(
        session=test_session,
        query=entity_id,
        kind=None,
        embedding_provider=mock_embedding_provider,
        limit=20,
    )

    assert result.status == "exact"
    assert result.match_type == "entity_id"
    assert len(result.candidates) == 1
    assert result.candidates[0].entity_id == entity_id


@pytest.mark.asyncio
async def test_resolve_by_signature(test_session: AsyncSession, sample_entities: list[Entity], mock_embedding_provider):
    signature = "void damage(Character *ch, Character *victim, int dam)"

    result = await resolve_entity(
        session=test_session,
        query=signature,
        kind=None,
        embedding_provider=mock_embedding_provider,
        limit=20,
    )

    assert result.status == "exact"
    assert result.match_type == "signature_exact"
    assert len(result.candidates) == 1
    assert result.candidates[0].signature == signature


@pytest.mark.asyncio
async def test_resolve_by_name_exact(
    test_session: AsyncSession, sample_entities: list[Entity], mock_embedding_provider
):
    """Test exact name match (stage 3)."""
    result = await resolve_entity(
        session=test_session,
        query="damage",
        kind=None,
        embedding_provider=mock_embedding_provider,
        limit=20,
    )

    assert result.status == "ambiguous"
    assert result.match_type == "name_exact"
    assert len(result.candidates) == 2  # Combat::damage + Logging::damage
    assert all(c.name == "damage" for c in result.candidates)


@pytest.mark.asyncio
async def test_resolve_by_name_ambiguous(
    test_session: AsyncSession, sample_entities: list[Entity], mock_embedding_provider
):
    """Test ambiguous name match when multiple entities share a name."""
    duplicate = Entity(
        entity_id="fn:dup0001",
        name="damage",
        signature="int damage(Character *ch, int amount)",
        kind="function",
        entity_type="member",
        fan_in=5,
        fan_out=2,
    )
    test_session.add(duplicate)
    await test_session.commit()

    result = await resolve_entity(
        session=test_session,
        query="damage",
        kind=None,
        embedding_provider=mock_embedding_provider,
        limit=20,
    )

    assert result.status == "ambiguous"
    assert result.match_type == "name_exact"
    assert len(result.candidates) == 3  # Combat::damage + Logging::damage + duplicate
    # Ranked by fan_in descending
    assert result.candidates[0].fan_in >= result.candidates[1].fan_in


@pytest.mark.asyncio
async def test_resolve_by_prefix(test_session: AsyncSession, sample_entities: list[Entity], mock_embedding_provider):
    result = await resolve_entity(
        session=test_session,
        query="do_",
        kind=None,
        embedding_provider=mock_embedding_provider,
        limit=20,
    )

    assert result.status == "ambiguous"
    assert result.match_type == "name_prefix"
    assert len(result.candidates) >= 1
    assert all(c.name.startswith("do_") for c in result.candidates)


@pytest.mark.asyncio
async def test_resolve_not_found(test_session: AsyncSession, sample_entities: list[Entity], mock_embedding_provider):
    result = await resolve_entity(
        session=test_session,
        query="nonexistent_function_xyz",
        kind=None,
        embedding_provider=mock_embedding_provider,
        limit=20,
    )

    assert result.status == "not_found"
    assert len(result.candidates) == 0


@pytest.mark.asyncio
async def test_resolve_with_kind_filter(
    test_session: AsyncSession, sample_entities: list[Entity], mock_embedding_provider
):
    result = await resolve_entity(
        session=test_session,
        query="Character",
        kind="class",
        embedding_provider=mock_embedding_provider,
        limit=20,
    )

    assert result.status == "exact"
    assert len(result.candidates) == 1
    assert result.candidates[0].kind == "class"


# ---------- ResolutionResult helpers ----------


def _make_resolution_entity(**overrides) -> Entity:
    """Create a minimal Entity for ResolutionResult tests."""
    defaults = dict(
        entity_id="fn:abc1234",
        name="test_func",
        signature="void test_func()",
        kind="function",
        entity_type="member",
        fan_in=5,
        fan_out=3,
    )
    defaults.update(overrides)
    return Entity(**defaults)


def test_resolution_result_to_entity_summaries():
    """to_entity_summaries() converts candidates to EntitySummary list."""
    entities = [
        _make_resolution_entity(entity_id="fn:aaa0001", name="alpha", signature="void alpha()"),
        _make_resolution_entity(entity_id="fn:bbb0002", name="beta", signature="void beta()"),
    ]
    r = ResolutionResult(
        status="ambiguous",
        match_type="name_prefix",
        candidates=entities,
        resolved_from="al",
    )
    summaries = r.to_entity_summaries()
    assert len(summaries) == 2
    assert all(isinstance(s, EntitySummary) for s in summaries)
    assert summaries[0].entity_id == "fn:aaa0001"
    assert summaries[1].entity_id == "fn:bbb0002"
