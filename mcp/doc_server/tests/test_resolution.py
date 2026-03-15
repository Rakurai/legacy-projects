"""
Integration tests for entity resolution pipeline.

Tests the multi-stage resolution: entity_id → signature → name → prefix → keyword → semantic.
Also covers ResolutionResult helper methods (to_envelope, to_entity_summaries).
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from server.resolver import resolve_entity, ResolutionResult, entity_to_summary
from server.db_models import Entity
from server.models import EntitySummary


@pytest.mark.asyncio
async def test_resolve_by_entity_id(test_session: AsyncSession, sample_entities: list[Entity]):
    """Test exact entity_id match (stage 1)."""
    entity_id = sample_entities[0].entity_id

    result = await resolve_entity(
        session=test_session,
        query=entity_id,
        kind=None,
        embedding_client=None,
        limit=20,
    )

    assert result.status == "exact"
    assert result.match_type == "entity_id"
    assert len(result.candidates) == 1
    assert result.candidates[0].entity_id == entity_id


@pytest.mark.asyncio
async def test_resolve_by_signature(test_session: AsyncSession, sample_entities: list[Entity]):
    """Test exact signature match (stage 2)."""
    signature = "void damage(Character *ch, Character *victim, int dam)"

    result = await resolve_entity(
        session=test_session,
        query=signature,
        kind=None,
        embedding_client=None,
        limit=20,
    )

    assert result.status == "exact"
    assert result.match_type == "signature_exact"
    assert len(result.candidates) == 1
    assert result.candidates[0].signature == signature


@pytest.mark.asyncio
async def test_resolve_by_name_exact(test_session: AsyncSession, sample_entities: list[Entity]):
    """Test exact name match (stage 3)."""
    result = await resolve_entity(
        session=test_session,
        query="damage",
        kind=None,
        embedding_client=None,
        limit=20,
    )

    assert result.status == "exact"
    assert result.match_type == "name_exact"
    assert len(result.candidates) == 1
    assert result.candidates[0].name == "damage"


@pytest.mark.asyncio
async def test_resolve_by_name_ambiguous(test_session: AsyncSession, sample_entities: list[Entity]):
    """Test ambiguous name match when multiple entities share a name."""
    # Add another entity with same name
    duplicate = Entity(
        entity_id="combat_8cc_duplicate",
        compound_id="combat_8cc",
        member_id="duplicate",
        name="damage",  # Same name as sample_entities[0]
        signature="int damage(Character *ch, int amount)",  # Different signature
        kind="function",
        entity_type="member",
        doc_state="extracted_summary",
        doc_quality="low",
        fan_in=5,
        fan_out=2,
    )
    test_session.add(duplicate)
    await test_session.commit()

    result = await resolve_entity(
        session=test_session,
        query="damage",
        kind=None,
        embedding_client=None,
        limit=20,
    )

    assert result.status == "ambiguous"
    assert result.match_type == "name_exact"
    assert len(result.candidates) == 2
    # Should be ranked by doc_quality (high before low)
    assert result.candidates[0].doc_quality == "high"


@pytest.mark.asyncio
async def test_resolve_by_prefix(test_session: AsyncSession, sample_entities: list[Entity]):
    """Test prefix match (stage 4)."""
    result = await resolve_entity(
        session=test_session,
        query="do_",
        kind=None,
        embedding_client=None,
        limit=20,
    )

    assert result.status == "ambiguous"
    assert result.match_type == "name_prefix"
    assert len(result.candidates) >= 1
    assert all(c.name.startswith("do_") for c in result.candidates)


@pytest.mark.asyncio
async def test_resolve_not_found(test_session: AsyncSession, sample_entities: list[Entity]):
    """Test entity not found."""
    result = await resolve_entity(
        session=test_session,
        query="nonexistent_function_xyz",
        kind=None,
        embedding_client=None,
        limit=20,
    )

    assert result.status == "not_found"
    assert len(result.candidates) == 0


@pytest.mark.asyncio
async def test_resolve_with_kind_filter(test_session: AsyncSession, sample_entities: list[Entity]):
    """Test resolution with kind filter."""
    result = await resolve_entity(
        session=test_session,
        query="Character",
        kind="class",
        embedding_client=None,
        limit=20,
    )

    assert result.status == "exact"
    assert len(result.candidates) == 1
    assert result.candidates[0].kind == "class"


# ---------- ResolutionResult helpers ----------

def _make_resolution_entity(**overrides) -> Entity:
    """Create a minimal Entity for ResolutionResult tests."""
    defaults = dict(
        entity_id="test_8cc_abc",
        compound_id="test_8cc",
        member_id="abc",
        name="test_func",
        signature="void test_func()",
        kind="function",
        entity_type="member",
        doc_state="extracted_summary",
        doc_quality="high",
        fan_in=5,
        fan_out=3,
    )
    defaults.update(overrides)
    return Entity(**defaults)


def test_resolution_result_to_envelope_exact():
    """to_envelope() returns correct envelope for exact match."""
    entity = _make_resolution_entity()
    r = ResolutionResult(
        status="exact",
        match_type="entity_id",
        candidates=[entity],
        resolved_from="test_8cc_abc",
    )
    env = r.to_envelope()
    assert env.resolution_status == "exact"
    assert env.match_type == "entity_id"
    assert env.resolution_candidates == 1
    assert env.resolved_from == "test_8cc_abc"


def test_resolution_result_to_envelope_ambiguous():
    """to_envelope() returns correct candidate count for ambiguous match."""
    entities = [_make_resolution_entity(entity_id=f"e{i}") for i in range(3)]
    r = ResolutionResult(
        status="ambiguous",
        match_type="name_prefix",
        candidates=entities,
        resolved_from="do_",
    )
    env = r.to_envelope()
    assert env.resolution_status == "ambiguous"
    assert env.resolution_candidates == 3


def test_resolution_result_to_envelope_not_found():
    """to_envelope() returns correct envelope for not_found."""
    r = ResolutionResult(
        status="not_found",
        match_type="semantic",
        candidates=[],
        resolved_from="xyz",
    )
    env = r.to_envelope()
    assert env.resolution_status == "not_found"
    assert env.resolution_candidates == 0


def test_resolution_result_to_entity_summaries():
    """to_entity_summaries() converts candidates to EntitySummary list."""
    entities = [
        _make_resolution_entity(entity_id="a", name="alpha", signature="void alpha()"),
        _make_resolution_entity(entity_id="b", name="beta", signature="void beta()"),
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
    assert summaries[0].entity_id == "a"
    assert summaries[1].entity_id == "b"
