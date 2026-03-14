"""
Contract tests for MCP tools - validates input/output schemas.

Ensures tools accept expected parameters and return correct response shapes.
"""

import pytest
from pydantic import ValidationError

from server.tools.entity import (
    ResolveEntityParams,
    GetEntityParams,
    GetSourceCodeParams,
    ListFileEntitiesParams,
    GetFileSummaryParams,
    ResolveEntityResponse,
    FileSummaryResponse,
)
from server.models import EntityDetail


def test_resolve_entity_params_valid():
    """Test valid ResolveEntityParams."""
    params = ResolveEntityParams(query="damage", kind="function")
    assert params.query == "damage"
    assert params.kind == "function"


def test_resolve_entity_params_no_kind():
    """Test ResolveEntityParams without kind filter."""
    params = ResolveEntityParams(query="damage")
    assert params.query == "damage"
    assert params.kind is None


def test_get_entity_params_entity_id():
    """Test GetEntityParams with entity_id."""
    params = GetEntityParams(entity_id="fight_8cc_1a2b3c", include_code=True)
    assert params.entity_id == "fight_8cc_1a2b3c"
    assert params.signature is None
    assert params.include_code is True


def test_get_entity_params_signature():
    """Test GetEntityParams with signature."""
    params = GetEntityParams(signature="void damage(Character *ch, int dam)")
    assert params.signature == "void damage(Character *ch, int dam)"
    assert params.entity_id is None


def test_get_source_code_params_valid():
    """Test valid GetSourceCodeParams."""
    params = GetSourceCodeParams(entity_id="fight_8cc_1a2b3c", context_lines=10)
    assert params.entity_id == "fight_8cc_1a2b3c"
    assert params.context_lines == 10


def test_get_source_code_params_context_limits():
    """Test GetSourceCodeParams context_lines validation."""
    # Valid range
    params = GetSourceCodeParams(entity_id="test", context_lines=0)
    assert params.context_lines == 0

    params = GetSourceCodeParams(entity_id="test", context_lines=50)
    assert params.context_lines == 50

    # Invalid range should fail
    with pytest.raises(ValidationError):
        GetSourceCodeParams(entity_id="test", context_lines=-1)

    with pytest.raises(ValidationError):
        GetSourceCodeParams(entity_id="test", context_lines=100)


def test_list_file_entities_params_valid():
    """Test valid ListFileEntitiesParams."""
    params = ListFileEntitiesParams(
        file_path="src/fight.cc",
        kind="function",
        limit=50
    )
    assert params.file_path == "src/fight.cc"
    assert params.kind == "function"
    assert params.limit == 50


def test_list_file_entities_params_limit_validation():
    """Test ListFileEntitiesParams limit validation."""
    # Valid range
    params = ListFileEntitiesParams(file_path="test.cc", limit=1)
    assert params.limit == 1

    params = ListFileEntitiesParams(file_path="test.cc", limit=500)
    assert params.limit == 500

    # Invalid range should fail
    with pytest.raises(ValidationError):
        ListFileEntitiesParams(file_path="test.cc", limit=0)

    with pytest.raises(ValidationError):
        ListFileEntitiesParams(file_path="test.cc", limit=1000)


def test_get_file_summary_params_valid():
    """Test valid GetFileSummaryParams."""
    params = GetFileSummaryParams(file_path="src/fight.cc")
    assert params.file_path == "src/fight.cc"


def test_resolve_entity_response_schema():
    """Test ResolveEntityResponse schema."""
    from server.models import EntitySummary

    summary = EntitySummary(
        entity_id="test_id",
        signature="void test()",
        name="test",
        kind="function",
        doc_state="extracted_summary",
        doc_quality="high",
        fan_in=10,
        fan_out=5,
    )

    response = ResolveEntityResponse(
        resolution_status="exact",
        resolved_from="test",
        match_type="signature_exact",
        resolution_candidates=1,
        candidates=[summary],
    )

    assert response.resolution_status == "exact"
    assert response.match_type == "signature_exact"
    assert len(response.candidates) == 1


def test_file_summary_response_schema():
    """Test FileSummaryResponse schema."""
    from server.models import EntitySummary, TruncationMetadata

    summary = EntitySummary(
        entity_id="test_id",
        signature="void test()",
        name="test",
        kind="function",
        doc_state="extracted_summary",
        doc_quality="high",
        fan_in=10,
        fan_out=5,
    )

    response = FileSummaryResponse(
        file_path="src/test.cc",
        entity_count=5,
        entity_count_by_kind={"function": 3, "variable": 2},
        capability_distribution={"combat": 5},
        doc_quality_distribution={"high": 3, "medium": 2},
        top_entities_by_fan_in=[summary],
        truncation=TruncationMetadata(
            truncated=False,
            total_available=5,
            node_count=5,
        ),
    )

    assert response.file_path == "src/test.cc"
    assert response.entity_count == 5
    assert len(response.top_entities_by_fan_in) == 1


def test_entity_detail_schema():
    """Test EntityDetail schema."""
    detail = EntityDetail(
        entity_id="test_id",
        compound_id="test_compound",
        member_id="test_member",
        signature="void test()",
        name="test",
        kind="function",
        entity_type="member",
        file_path="src/test.cc",
        body_start_line=10,
        body_end_line=20,
        decl_file_path="src/test.hh",
        decl_line=5,
        definition_text="void test()",
        source_text="void test() { }",
        capability="test",
        doc_state="refined_summary",
        doc_quality="high",
        fan_in=10,
        fan_out=5,
        is_bridge=True,
        is_entry_point=False,
        brief="Test function",
        details="Detailed description",
        params={"x": "Input parameter"},
        returns="Nothing",
        rationale="Design rationale",
        usages={"caller1": "Usage example"},
        notes="Implementation notes",
        side_effect_markers={"messaging": ["send_to_char"]},
        neighbors=None,
        provenance="llm_generated",
    )

    assert detail.entity_id == "test_id"
    assert detail.doc_quality == "high"
    assert detail.provenance == "llm_generated"
