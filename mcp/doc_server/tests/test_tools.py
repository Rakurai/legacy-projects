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


# ---- Phase 6: Behavioral Analysis Tool Contract Tests (T067) ----


def test_get_behavior_slice_params_valid():
    """Test valid GetBehaviorSliceParams."""
    from server.tools.behavior import GetBehaviorSliceParams
    params = GetBehaviorSliceParams(entity_id="test_id", max_depth=5, max_cone_size=200)
    assert params.entity_id == "test_id"
    assert params.max_depth == 5
    assert params.max_cone_size == 200


def test_get_behavior_slice_params_defaults():
    """Test GetBehaviorSliceParams defaults."""
    from server.tools.behavior import GetBehaviorSliceParams
    params = GetBehaviorSliceParams(entity_id="test_id")
    assert params.max_depth == 5
    assert params.max_cone_size == 200


def test_get_behavior_slice_params_validation():
    """Test GetBehaviorSliceParams validation."""
    from server.tools.behavior import GetBehaviorSliceParams
    with pytest.raises(ValidationError):
        GetBehaviorSliceParams(entity_id="test_id", max_depth=0)
    with pytest.raises(ValidationError):
        GetBehaviorSliceParams(entity_id="test_id", max_cone_size=0)


def test_get_state_touches_params_valid():
    """Test valid GetStateTouchesParams."""
    from server.tools.behavior import GetStateTouchesParams
    params = GetStateTouchesParams(entity_id="test_id")
    assert params.entity_id == "test_id"


def test_get_hotspots_params_valid():
    """Test valid GetHotspotsParams."""
    from server.tools.behavior import GetHotspotsParams
    params = GetHotspotsParams(metric="fan_in", kind="function", capability="combat", limit=20)
    assert params.metric == "fan_in"
    assert params.kind == "function"
    assert params.capability == "combat"
    assert params.limit == 20


def test_get_hotspots_params_metric_validation():
    """Test GetHotspotsParams metric validation."""
    from server.tools.behavior import GetHotspotsParams
    with pytest.raises(ValidationError):
        GetHotspotsParams(metric="invalid_metric")


def test_behavior_slice_response_schema():
    """Test BehaviorSliceResponse schema."""
    from server.tools.behavior import BehaviorSliceResponse
    from server.models import (
        BehaviorSlice, EntitySummary, TruncationMetadata,
        CapabilityTouch, SideEffectMarker, GlobalTouch,
    )

    summary = EntitySummary(
        entity_id="test_id", signature="void test()", name="test",
        kind="function", doc_state="extracted_summary", doc_quality="high",
        fan_in=10, fan_out=5,
    )

    behavior = BehaviorSlice(
        entry_point=summary,
        direct_callees=[summary],
        transitive_cone=[],
        max_depth=3,
        truncated=False,
        capabilities_touched={
            "combat": CapabilityTouch(
                capability="combat", direct_count=1, transitive_count=0,
                functions=[summary],
            )
        },
        globals_used=[
            GlobalTouch(entity_id="var1", name="gsn_backstab", kind="variable", access_type="direct")
        ],
        side_effects={
            "messaging": [SideEffectMarker(
                function_id="fn1", function_name="send_to_char",
                category="messaging", access_type="direct",
                confidence="direct", provenance="heuristic",
            )]
        },
    )

    response = BehaviorSliceResponse(
        behavior=behavior,
        truncation=TruncationMetadata(truncated=False, total_available=1, node_count=1),
    )

    assert response.behavior.entry_point.entity_id == "test_id"
    assert "combat" in response.behavior.capabilities_touched
    assert len(response.behavior.globals_used) == 1
    assert "messaging" in response.behavior.side_effects


def test_state_touches_response_schema():
    """Test StateTouchesResponse schema."""
    from server.tools.behavior import StateTouchesResponse
    from server.models import EntitySummary, SideEffectMarker

    summary = EntitySummary(
        entity_id="test_id", signature="void test()", name="test",
        kind="function", doc_state="extracted_summary", doc_quality="high",
        fan_in=10, fan_out=5,
    )

    response = StateTouchesResponse(
        entity_id="test_id",
        signature="void test()",
        direct_uses=[summary],
        direct_side_effects=[],
        transitive_uses=[],
        transitive_side_effects=[],
    )

    assert response.entity_id == "test_id"
    assert len(response.direct_uses) == 1


def test_hotspots_response_schema():
    """Test HotspotsResponse schema."""
    from server.tools.behavior import HotspotsResponse
    from server.models import EntitySummary, TruncationMetadata

    summary = EntitySummary(
        entity_id="test_id", signature="void test()", name="test",
        kind="function", doc_state="extracted_summary", doc_quality="high",
        fan_in=100, fan_out=5,
    )

    response = HotspotsResponse(
        metric="fan_in",
        hotspots=[summary],
        truncation=TruncationMetadata(truncated=False, total_available=1, node_count=1),
    )

    assert response.metric == "fan_in"
    assert len(response.hotspots) == 1
    assert response.hotspots[0].fan_in == 100


# ---- Phase 7: Capability System Tool Contract Tests (T078) ----


def test_list_capabilities_params():
    """Test ListCapabilitiesParams (no params)."""
    from server.tools.capability import ListCapabilitiesParams
    params = ListCapabilitiesParams()
    assert params is not None


def test_get_capability_detail_params_valid():
    """Test valid GetCapabilityDetailParams."""
    from server.tools.capability import GetCapabilityDetailParams
    params = GetCapabilityDetailParams(capability="combat", include_functions=True)
    assert params.capability == "combat"
    assert params.include_functions is True


def test_compare_capabilities_params_valid():
    """Test valid CompareCapabilitiesParams."""
    from server.tools.capability import CompareCapabilitiesParams
    params = CompareCapabilitiesParams(capabilities=["combat", "magic"], limit=50)
    assert params.capabilities == ["combat", "magic"]
    assert params.limit == 50


def test_compare_capabilities_params_min_length():
    """Test CompareCapabilitiesParams requires at least 2 capabilities."""
    from server.tools.capability import CompareCapabilitiesParams
    with pytest.raises(ValidationError):
        CompareCapabilitiesParams(capabilities=["combat"])


def test_list_entry_points_params_valid():
    """Test valid ListEntryPointsParams."""
    from server.tools.capability import ListEntryPointsParams
    params = ListEntryPointsParams(capability="combat", name_pattern="do_%", limit=50)
    assert params.capability == "combat"
    assert params.name_pattern == "do_%"
    assert params.limit == 50


def test_get_entry_point_info_params_valid():
    """Test valid GetEntryPointInfoParams."""
    from server.tools.capability import GetEntryPointInfoParams
    params = GetEntryPointInfoParams(entity_id="test_id")
    assert params.entity_id == "test_id"


def test_list_capabilities_response_schema():
    """Test ListCapabilitiesResponse schema."""
    from server.tools.capability import ListCapabilitiesResponse
    from server.models import CapabilitySummary

    cap = CapabilitySummary(
        name="combat", type="domain",
        description="Combat mechanics",
        function_count=127, stability="stable",
        doc_quality_dist={"high": 95, "medium": 25, "low": 7},
    )

    response = ListCapabilitiesResponse(capabilities=[cap])
    assert len(response.capabilities) == 1
    assert response.capabilities[0].name == "combat"


def test_capability_detail_response_schema():
    """Test GetCapabilityDetailResponse schema."""
    from server.tools.capability import GetCapabilityDetailResponse
    from server.models import CapabilityDetail

    detail = CapabilityDetail(
        name="combat", type="domain",
        description="Combat mechanics",
        function_count=127, stability="stable",
        doc_quality_dist={"high": 95, "medium": 25, "low": 7},
        dependencies=[{"target_capability": "character_state", "edge_type": "requires_core", "call_count": 342}],
        entry_points=["do_kill", "do_flee"],
        functions=None,
    )

    response = GetCapabilityDetailResponse(detail=detail)
    assert response.detail.name == "combat"
    assert len(response.detail.dependencies) == 1
    assert len(response.detail.entry_points) == 2


def test_compare_capabilities_response_schema():
    """Test CompareCapabilitiesResponse schema."""
    from server.tools.capability import CompareCapabilitiesResponse
    from server.models import EntitySummary, TruncationMetadata

    summary = EntitySummary(
        entity_id="test_id", signature="void test()", name="test",
        kind="function", doc_state="extracted_summary", doc_quality="high",
        fan_in=10, fan_out=5,
    )

    response = CompareCapabilitiesResponse(
        capabilities=["combat", "magic"],
        shared_dependencies=[summary],
        unique_dependencies={"combat": [summary], "magic": []},
        bridge_entities=[],
        truncation=TruncationMetadata(truncated=False, total_available=2, node_count=2),
    )

    assert response.capabilities == ["combat", "magic"]
    assert len(response.shared_dependencies) == 1


def test_entry_point_info_response_schema():
    """Test EntryPointInfoResponse schema."""
    from server.tools.capability import EntryPointInfoResponse
    from server.models import EntitySummary

    summary = EntitySummary(
        entity_id="test_id", signature="void do_kill(Character *ch, String argument)",
        name="do_kill", kind="function", doc_state="refined_summary",
        doc_quality="high", fan_in=20, fan_out=12,
    )

    response = EntryPointInfoResponse(
        entry_point=summary,
        capabilities_exercised={
            "combat": {"capability": "combat", "direct_count": 8, "transitive_count": 42},
        },
    )

    assert response.entry_point.name == "do_kill"
    assert "combat" in response.capabilities_exercised
