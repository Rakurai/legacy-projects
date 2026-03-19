"""
Contract tests for the explain_interface tool.

Tests the five-part behavioral contract composition from entity fields
and entity_usages data. Uses async mock-context pattern (no real DB semantics
beyond the test session).
"""

import pytest

from server.errors import EntityNotFoundError
from server.tools.explain import explain_interface


# ---------- Full contract ----------


@pytest.mark.asyncio
async def test_full_contract(mock_ctx, sample_entities, sample_entity_usages):
    """explain_interface returns all five sections for a well-documented entity."""
    damage_id = sample_entities[0].entity_id  # fn:a1b2c3d — full docs + usages

    response = await explain_interface(mock_ctx, entity_id=damage_id)

    # Part 1: Signature
    assert response.signature_block is not None
    assert "damage" in response.signature_block

    # Part 2: Mechanism
    assert response.mechanism.brief is not None
    assert response.mechanism.details is not None
    assert "damage" in response.mechanism.brief.lower()

    # Part 3: Contract (rationale present on damage entity)
    assert response.contract is not None
    assert response.contract.rationale is not None
    assert len(response.contract.rationale) > 0

    # Part 4: Preconditions (notes present on damage entity)
    assert response.preconditions is not None
    assert response.preconditions.notes is not None
    assert len(response.preconditions.notes) > 0

    # Part 5: Calling patterns from sample_entity_usages (5 rows)
    assert len(response.calling_patterns) <= 5
    assert len(response.calling_patterns) > 0
    for pattern in response.calling_patterns:
        assert pattern.caller_compound
        assert pattern.caller_sig
        assert pattern.description


# ---------- Partial contract (no rationale) ----------


@pytest.mark.asyncio
async def test_partial_contract_no_rationale(mock_ctx, sample_entities):
    """explain_interface omits contract section when rationale is null."""
    # do_kill (index 1) has no rationale in fixture
    do_kill_id = sample_entities[1].entity_id

    response = await explain_interface(mock_ctx, entity_id=do_kill_id)

    assert response.contract is None
    assert response.mechanism.brief is not None  # brief is present


@pytest.mark.asyncio
async def test_partial_contract_no_notes(mock_ctx, sample_entities):
    """explain_interface omits preconditions section when notes is null."""
    # Character class (index 2) has no notes in fixture
    char_id = sample_entities[2].entity_id

    response = await explain_interface(mock_ctx, entity_id=char_id)

    assert response.preconditions is None


@pytest.mark.asyncio
async def test_no_calling_patterns_when_no_usages(mock_ctx, sample_entities):
    """explain_interface returns empty calling_patterns for entities with no usages."""
    do_kill_id = sample_entities[1].entity_id  # no sample_entity_usages for do_kill

    response = await explain_interface(mock_ctx, entity_id=do_kill_id)

    assert response.calling_patterns == []


# ---------- Entity not found ----------


@pytest.mark.asyncio
async def test_entity_not_found(mock_ctx, sample_entities):
    """explain_interface raises EntityNotFoundError for unknown entity_id."""
    with pytest.raises(EntityNotFoundError):
        await explain_interface(mock_ctx, entity_id="fn:0000000")


# ---------- Metadata fields ----------


@pytest.mark.asyncio
async def test_metadata_fields(mock_ctx, sample_entities, sample_entity_usages):
    """explain_interface metadata contains all contract quality signals."""
    damage_id = sample_entities[0].entity_id

    response = await explain_interface(mock_ctx, entity_id=damage_id)

    meta = response.metadata
    assert meta.doc_state == "refined_summary"
    assert meta.is_contract_seed is True
    assert meta.rationale_specificity == pytest.approx(0.85)
    assert meta.fan_in == 23
    assert meta.fan_out == 8
    assert meta.capability == "combat"


@pytest.mark.asyncio
async def test_metadata_null_fields(mock_ctx, sample_entities):
    """explain_interface metadata correctly represents null quality fields."""
    # do_kill has doc_state="generated_summary", no rationale_specificity
    do_kill_id = sample_entities[1].entity_id

    response = await explain_interface(mock_ctx, entity_id=do_kill_id)

    meta = response.metadata
    assert meta.doc_state == "generated_summary"
    assert meta.is_contract_seed is False
    assert meta.rationale_specificity is None


# ---------- US4: Auditor workflow validation (T023) ----------


@pytest.mark.asyncio
async def test_auditor_evidence_completeness(mock_ctx, sample_entities, sample_entity_usages):
    """
    Given a well-documented entity, explain_interface provides sufficient evidence
    for an auditor to cross-reference spec claims against caller evidence.

    Verifies:
    - doc_state is present (trust signal for auditor)
    - calling_patterns contains evidence from diverse callers
    - contract section provides caller-derived rationale
    """
    damage_id = sample_entities[0].entity_id

    response = await explain_interface(mock_ctx, entity_id=damage_id)

    # Trust signal available
    assert response.metadata.doc_state is not None

    # Caller evidence from multiple distinct callers
    compounds = {p.caller_compound for p in response.calling_patterns}
    assert len(compounds) >= 2, "Auditor needs evidence from multiple callers"

    # Contract rationale present
    assert response.contract is not None
    assert response.contract.rationale is not None
