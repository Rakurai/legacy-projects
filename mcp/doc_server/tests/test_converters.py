"""
Unit tests for converters module.

Tests entity_to_summary, entity_to_detail, and capability_to_summary
with various inputs to cover all conversion branches.
"""

from server.converters import capability_to_summary, entity_to_detail, entity_to_summary
from server.db_models import Capability, Entity


def _make_entity(**overrides) -> Entity:
    """Create a minimal Entity for testing."""
    defaults = dict(
        entity_id="fn:a1b2c3d",
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
        capability="combat",
        is_entry_point=False,
        fan_in=5,
        fan_out=3,
        is_bridge=False,
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
    assert summary.fan_in == 5
    assert summary.fan_out == 3


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


def test_entity_to_detail_all_fields():
    """entity_to_detail maps all Entity fields to EntityDetail."""
    entity = _make_entity(
        notes="Some implementation notes",
        rationale="Design choice explanation",
        usages={"caller_a": "calls for damage calc"},
        is_bridge=True,
        is_entry_point=True,
    )
    detail = entity_to_detail(entity, include_code=True)

    assert detail.kind == entity.kind
    assert detail.entity_type == entity.entity_type
    assert detail.body_start_line == entity.body_start_line
    assert detail.body_end_line == entity.body_end_line
    assert detail.params == entity.params
    assert detail.returns == entity.returns
    assert detail.notes == "Some implementation notes"
    assert detail.rationale == "Design choice explanation"
    assert detail.usages == {"caller_a": "calls for damage calc"}
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
    )
    summary = capability_to_summary(cap)

    assert summary.name == "combat"
    assert summary.type == "domain"
    assert summary.description == "Combat system"
    assert summary.function_count == 25
    assert summary.stability == "stable"
