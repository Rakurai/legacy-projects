"""
Pydantic API Models - MCP Tool Request/Response Schemas.

All models use Pydantic v2 patterns (BaseModel, Field, field_validator, ConfigDict).
"""

from pydantic import BaseModel, Field, field_validator

from server.enums import (
    AccessType,
    CapabilityType,
    EntityKind,
    EntityType,
    FocusType,
    SearchMode,
    TruncationReason,
)


class EntitySummary(BaseModel):
    """
    Compact entity representation used in all list tools.

    Used in search results, file listings, dependency lists, etc.
    """
    entity_id: str = Field(description="Deterministic entity ID in {prefix}:{7 hex} format (for passing to get_entity)")
    signature: str = Field(description="Full human-readable signature")
    name: str = Field(description="Bare name")
    kind: EntityKind
    file_path: str | None = Field(default=None, description="Source file path")
    capability: str | None = Field(default=None, description="Capability group")
    brief: str | None = Field(default=None, description="One-line summary")
    fan_in: int = Field(ge=0, description="Incoming CALLS edges")
    fan_out: int = Field(ge=0, description="Outgoing CALLS edges")

    @field_validator("signature", "name")
    @classmethod
    def non_empty_strings(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Field cannot be empty")
        return v.strip()


class EntityNeighbor(BaseModel):
    """Direct neighbor in dependency graph."""
    entity_id: str
    name: str
    kind: str
    relationship: str  # CALLS, USES, INHERITS, INCLUDES, CONTAINED_BY
    direction: str  # "incoming" or "outgoing" (set dynamically from graph traversal)


class EntityDetail(BaseModel):
    """
    Complete entity documentation and metadata.

    Returned by get_entity tool.
    """
    # Identity
    entity_id: str
    signature: str
    name: str

    # Classification
    kind: str
    entity_type: EntityType

    # Source location
    file_path: str | None
    body_start_line: int | None
    body_end_line: int | None
    decl_file_path: str | None
    decl_line: int | None
    definition_text: str | None
    source_text: str | None  # Optional (include_code=true)

    # Capability & metrics
    capability: str | None
    fan_in: int
    fan_out: int
    is_bridge: bool
    is_entry_point: bool

    # Documentation
    brief: str | None
    details: str | None
    params: dict[str, str] | None
    returns: str | None
    rationale: str | None
    usages: dict[str, str] | None
    notes: str | None

    # Optional neighbors (include_neighbors=true)
    neighbors: list[EntityNeighbor] | None = None


class TruncationMetadata(BaseModel):
    """Metadata about result truncation."""
    truncated: bool
    total_available: int
    node_count: int  # Actual result count returned
    max_depth_requested: int | None = None
    max_depth_reached: int | None = None
    truncation_reason: TruncationReason | None = None


class SearchResult(BaseModel):
    """
    Search result with discriminated type.

    V1: result_type is always "entity"
    V2: adds "subsystem_doc" type
    """
    result_type: str  # "entity" in V1; V2 adds "subsystem_doc"
    score: float = Field(ge=0, le=1, description="Normalized combined score")
    search_mode: SearchMode
    entity_summary: EntitySummary | None = None  # Present when result_type="entity"


class CapabilityTouch(BaseModel):
    """Capability touched in behavior analysis."""
    capability: str
    direct_count: int
    transitive_count: int
    functions: list[EntitySummary]  # Sample (truncated if >10)


class GlobalTouch(BaseModel):
    """Global variable usage in behavior analysis."""
    entity_id: str
    name: str
    kind: EntityKind = EntityKind.VARIABLE
    access_type: AccessType


class BehaviorSlice(BaseModel):
    """
    Transitive call cone with behavioral metadata.

    Result from behavior analysis (call cone computation).
    """
    entry_point: EntitySummary  # Seed entity

    # Call structure
    direct_callees: list[EntitySummary]
    transitive_cone: list[EntitySummary]
    max_depth: int
    truncated: bool

    # Capabilities touched
    capabilities_touched: dict[str, CapabilityTouch]  # cap_name → touch metadata

    # Globals used
    globals_used: list[GlobalTouch]


class CapabilitySummary(BaseModel):
    """Summary of a capability group."""
    name: str
    type: CapabilityType
    description: str
    function_count: int
    stability: str | None


class CapabilityDetail(BaseModel):
    """Detailed capability information."""
    name: str
    type: str
    description: str
    function_count: int
    stability: str | None
    dependencies: list[dict]  # Typed edges to other capabilities
    entry_points: list[str]  # Entry point function names
    functions: list[EntitySummary] | None = None  # Optional full function list


# V2-Reserved Shapes (defined now to prevent response-shape drift)

class SubsystemSummary(BaseModel):
    """V2: Subsystem-level summary (not used in V1)."""
    id: str
    name: str
    parent_id: str | None
    description: str
    source_file: str
    entity_count: int
    doc_section_count: int
    depends_on_count: int
    depended_on_by_count: int


class SubsystemDocSummary(BaseModel):
    """V2: Subsystem documentation section summary (not used in V1)."""
    id: int
    subsystem_id: str
    subsystem_name: str
    section_path: str
    heading: str
    section_kind: str
    source_file: str
    line_range: tuple[int, int] | None
    excerpt: str


class ContextBundle(BaseModel):
    """V2: Mixed entity/system context assembly (not used in V1)."""
    focus_type: FocusType
    focus: dict  # EntitySummary | SubsystemSummary | dict
    related_entities: list[EntitySummary]
    related_capabilities: list[dict]
    related_subsystems: list[SubsystemSummary]
    relevant_doc_sections: list[dict]
    confidence_notes: str | None = None
    truncated: bool = False
