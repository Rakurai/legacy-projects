"""
Integration tests for entity resolution pipeline.

Tests the multi-stage resolution: entity_id → signature → name → prefix → keyword → semantic
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from server.resolver import resolve_entity, entity_to_summary
from server.db_models import Entity


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


@pytest.mark.asyncio
async def test_entity_to_summary_conversion(sample_entities: list[Entity]):
    """Test Entity to EntitySummary conversion."""
    entity = sample_entities[0]
    summary = entity_to_summary(entity)

    assert summary.entity_id == entity.entity_id
    assert summary.signature == entity.signature
    assert summary.name == entity.name
    assert summary.kind == entity.kind
    assert summary.doc_quality == entity.doc_quality
    assert summary.provenance == "precomputed"
