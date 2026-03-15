"""
Entity/Capability Converters - Single source of truth for DB model → Pydantic model conversion.

All ORM-to-API-model conversions live here. No defensive fallbacks — if the data
is wrong, we fail loudly rather than silently coercing.
"""

from server.enums import DocQuality, DocState, Provenance
from server.db_models import Entity, Capability
from server.models import EntitySummary, EntityDetail, CapabilitySummary


def entity_to_summary(entity: Entity) -> EntitySummary:
    """Convert Entity DB model to EntitySummary API model."""
    return EntitySummary(
        entity_id=entity.entity_id,
        signature=entity.signature,
        name=entity.name,
        kind=entity.kind,
        file_path=entity.file_path,
        capability=entity.capability,
        brief=entity.brief,
        doc_state=entity.doc_state or DocState.EXTRACTED_SUMMARY,
        doc_quality=entity.doc_quality or DocQuality.LOW,
        fan_in=entity.fan_in,
        fan_out=entity.fan_out,
        provenance=Provenance.PRECOMPUTED,
    )


def entity_to_detail(
    entity: Entity,
    *,
    include_code: bool = False,
) -> EntityDetail:
    """Convert Entity DB model to EntityDetail API model."""
    return EntityDetail(
        entity_id=entity.entity_id,
        compound_id=entity.compound_id,
        member_id=entity.member_id,
        signature=entity.signature,
        name=entity.name,
        kind=entity.kind,
        entity_type=entity.entity_type,
        file_path=entity.file_path,
        body_start_line=entity.body_start_line,
        body_end_line=entity.body_end_line,
        decl_file_path=entity.decl_file_path,
        decl_line=entity.decl_line,
        definition_text=entity.definition_text,
        source_text=entity.source_text if include_code else None,
        capability=entity.capability,
        doc_state=entity.doc_state or DocState.EXTRACTED_SUMMARY,
        doc_quality=entity.doc_quality or DocQuality.LOW,
        fan_in=entity.fan_in,
        fan_out=entity.fan_out,
        is_bridge=entity.is_bridge,
        is_entry_point=entity.is_entry_point,
        brief=entity.brief,
        details=entity.details,
        params=entity.params,
        returns=entity.returns,
        rationale=entity.rationale,
        usages=entity.usages,
        notes=entity.notes,
        side_effect_markers=entity.side_effect_markers,
        provenance=Provenance.DOXYGEN_EXTRACTED if entity.doc_state == DocState.EXTRACTED_SUMMARY else Provenance.LLM_GENERATED,
    )


def capability_to_summary(cap: Capability) -> CapabilitySummary:
    """Convert Capability DB model to CapabilitySummary API model."""
    dqd = cap.doc_quality_dist
    if not isinstance(dqd, dict):
        dqd = {"high": 0, "medium": 0, "low": 0}
    return CapabilitySummary(
        name=cap.name,
        type=cap.type,
        description=cap.description,
        function_count=cap.function_count,
        stability=cap.stability,
        doc_quality_dist=dqd,
        provenance=Provenance.PRECOMPUTED,
    )
