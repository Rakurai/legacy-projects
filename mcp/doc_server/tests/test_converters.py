"""
Unit tests for converters module.

Tests entity_to_summary, entity_to_detail, and capability_to_summary
with various inputs to cover all conversion branches.
"""

import pytest

from server.db_models import Entity, Capability
from server.converters import entity_to_summary, entity_to_detail, capability_to_summary


def _make_entity(**overrides) -> Entity:
    """Create a minimal Entity for testing."""
    defaults = dict(
        entity_id="test_8cc_abc123",
        compound_id="test_8cc",
        member_id="abc123",
        name="test_func",
        signature="void test_func()",
        kind="function",
        entity_type="member",
        file_path="src/test.cc",
        body_start_line=10,
        body_end_line=20,
        definition_text="void test_func()",
        source_text="void test_func() { return; }",
        brief="Test function",
        details="A test function for unit testing.",
        params={"x": "parameter x"},
        returns="void",
        doc_state="refined_summary",
        doc_quality="high",
        capability="combat",
        is_entry_point=False,
        fan_in=5,
        fan_out=3,
        is_bridge=False,
        side_effect_markers=None,
    )
    defaults.update(overrides)
    return Entity(**defaults)


# ---------- entity_to_summary ----------

def test_entity_to_summary_basic():
    """entity_to_summary maps all fields correctly."""
    entity = _make_entity()
    summary = entity_to_summary(entity)

    assert summary.entity_id == entity.entity_id
    assert summary.signature == entity.signature
    assert summary.name == entity.name
    assert summary.kind == entity.kind
    assert summary.file_path == entity.file_path
    assert summary.capability == entity.capability
    assert summary.brief == entity.brief
    assert summary.doc_quality == "high"
    assert summary.fan_in == 5
    assert summary.fan_out == 3
    assert summary.provenance == "precomputed"


def test_entity_to_summary_null_doc_state():
    """entity_to_summary handles None doc_state with fallback."""
    entity = _make_entity(doc_state=None)
    summary = entity_to_summary(entity)
    assert summary.doc_state == "extracted_summary"


def test_entity_to_summary_null_doc_quality():
    """entity_to_summary handles None doc_quality with fallback."""
    entity = _make_entity(doc_quality=None)
    summary = entity_to_summary(entity)
    assert summary.doc_quality == "low"


# ---------- entity_to_detail ----------

def test_entity_to_detail_include_code_true():
    """entity_to_detail with include_code=True includes source_text."""
    entity = _make_entity(source_text="int x = 42;")
    detail = entity_to_detail(entity, include_code=True)

    assert detail.source_text == "int x = 42;"
    assert detail.entity_id == entity.entity_id
    assert detail.definition_text == entity.definition_text


def test_entity_to_detail_include_code_false():
    """entity_to_detail with include_code=False suppresses source_text."""
    entity = _make_entity(source_text="int x = 42;")
    detail = entity_to_detail(entity, include_code=False)

    assert detail.source_text is None


def test_entity_to_detail_provenance_extracted():
    """entity_to_detail sets doxygen_extracted provenance for extracted_summary."""
    entity = _make_entity(doc_state="extracted_summary")
    detail = entity_to_detail(entity)

    assert detail.provenance == "doxygen_extracted"


def test_entity_to_detail_provenance_llm_refined():
    """entity_to_detail sets llm_generated provenance for refined states."""
    entity = _make_entity(doc_state="refined_summary")
    detail = entity_to_detail(entity)

    assert detail.provenance == "llm_generated"


def test_entity_to_detail_provenance_llm_generated():
    """entity_to_detail sets llm_generated provenance for generated_summary."""
    entity = _make_entity(doc_state="generated_summary")
    detail = entity_to_detail(entity)

    assert detail.provenance == "llm_generated"


def test_entity_to_detail_all_fields():
    """entity_to_detail maps all Entity fields to EntityDetail."""
    entity = _make_entity(
        notes="Some implementation notes",
        rationale="Design choice explanation",
        usages={"caller_a": "calls for damage calc"},
        side_effect_markers={"messaging": ["send_to_char"]},
        is_bridge=True,
        is_entry_point=True,
    )
    detail = entity_to_detail(entity, include_code=True)

    assert detail.compound_id == entity.compound_id
    assert detail.member_id == entity.member_id
    assert detail.kind == entity.kind
    assert detail.entity_type == entity.entity_type
    assert detail.body_start_line == entity.body_start_line
    assert detail.body_end_line == entity.body_end_line
    assert detail.params == entity.params
    assert detail.returns == entity.returns
    assert detail.notes == "Some implementation notes"
    assert detail.rationale == "Design choice explanation"
    assert detail.usages == {"caller_a": "calls for damage calc"}
    assert detail.side_effect_markers == {"messaging": ["send_to_char"]}
    assert detail.is_bridge is True
    assert detail.is_entry_point is True


# ---------- capability_to_summary ----------

def test_capability_to_summary_basic():
    """capability_to_summary maps all fields correctly."""
    cap = Capability(
        name="combat",
        type="domain",
        description="Combat system",
        function_count=25,
        stability="stable",
        doc_quality_dist={"high": 10, "medium": 10, "low": 5},
    )
    summary = capability_to_summary(cap)

    assert summary.name == "combat"
    assert summary.type == "domain"
    assert summary.description == "Combat system"
    assert summary.function_count == 25
    assert summary.stability == "stable"
    assert summary.doc_quality_dist == {"high": 10, "medium": 10, "low": 5}
    assert summary.provenance == "precomputed"


def test_capability_to_summary_invalid_doc_quality_dist():
    """capability_to_summary falls back when doc_quality_dist is not a dict."""
    cap = Capability(
        name="test",
        type="utility",
        description="Test",
        function_count=0,
        stability=None,
        doc_quality_dist="invalid",  # type: ignore
    )
    summary = capability_to_summary(cap)

    assert summary.doc_quality_dist == {"high": 0, "medium": 0, "low": 0}
