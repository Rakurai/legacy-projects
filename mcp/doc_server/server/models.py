"""
Pydantic API Models - MCP Tool Request/Response Schemas.

All models use Pydantic v2 patterns (BaseModel, Field, field_validator, ConfigDict).
Provenance fields track data source per FR-044.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Literal


# Provenance type (data source tracking per FR-044)
Provenance = Literal[
    "doxygen_extracted",      # From Doxygen XML
    "llm_generated",          # From LLM documentation generation
    "subsystem_narrative",    # From subsystem docs (V2)
    "precomputed",            # Pre-computed from build script (metrics, graph)
    "inferred",               # Inferred via algorithms (call cones, behavior slices)
    "heuristic",              # Heuristic-based (side effects, entry point detection)
    "measured"                # Measured at runtime (not used in V1)
]


class EntitySummary(BaseModel):
    """
    Compact entity representation used in all list tools.

    Used in search results, file listings, dependency lists, etc.
    """
    entity_id: str = Field(description="Internal Doxygen ID (for passing to get_entity)")
    signature: str = Field(description="Full human-readable signature")
    name: str = Field(description="Bare name")
    kind: Literal["function", "variable", "class", "struct", "file", "enum", "define", "typedef", "namespace", "dir", "group"]
    file_path: str | None = Field(default=None, description="Source file path")
    capability: str | None = Field(default=None, description="Capability group")
    brief: str | None = Field(default=None, description="One-line summary")
    doc_state: str = Field(description="Documentation pipeline state")
    doc_quality: Literal["high", "medium", "low"] = Field(description="Derived quality bucket")
    fan_in: int = Field(ge=0, description="Incoming CALLS edges")
    fan_out: int = Field(ge=0, description="Outgoing CALLS edges")
    provenance: Provenance = Field(default="precomputed", description="Data source")

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
    direction: Literal["incoming", "outgoing"]
    provenance: Provenance = Field(default="precomputed")


class EntityDetail(BaseModel):
    """
    Complete entity documentation and metadata.

    Returned by get_entity tool.
    """
    # Identity
    entity_id: str
    compound_id: str
    member_id: str | None
    signature: str
    name: str

    # Classification
    kind: str
    entity_type: Literal["compound", "member"]

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
    doc_state: str
    doc_quality: Literal["high", "medium", "low"]
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

    # Side effects
    side_effect_markers: dict[str, list[str]] | None

    # Optional neighbors (include_neighbors=true)
    neighbors: list[EntityNeighbor] | None = None

    # Provenance
    provenance: Provenance = Field(default="doxygen_extracted")


class ResolutionEnvelope(BaseModel):
    """Metadata about entity resolution."""
    resolution_status: Literal["exact", "ambiguous", "not_found"]
    resolved_from: str  # Original query string
    match_type: Literal["entity_id", "signature_exact", "name_exact", "name_prefix", "keyword", "semantic"]
    resolution_candidates: int  # Total matches found


class TruncationMetadata(BaseModel):
    """Metadata about result truncation."""
    truncated: bool
    total_available: int
    node_count: int  # Actual result count returned
    max_depth_requested: int | None = None
    max_depth_reached: int | None = None
    truncation_reason: Literal["depth_limit", "node_limit", "none"] | None = None


class SearchResult(BaseModel):
    """
    Search result with discriminated type.

    V1: result_type is always "entity"
    V2: adds "subsystem_doc" type
    """
    result_type: Literal["entity", "subsystem_doc"]  # V2: subsystem_doc not used in V1
    score: float = Field(ge=0, le=1, description="Normalized combined score")
    search_mode: Literal["hybrid", "semantic_only", "keyword_fallback"]
    provenance: Provenance
    entity_summary: EntitySummary | None = None  # Present when result_type="entity"


class CapabilityTouch(BaseModel):
    """Capability touched in behavior analysis."""
    capability: str
    direct_count: int
    transitive_count: int
    functions: list[EntitySummary]  # Sample (truncated if >10)
    provenance: Provenance = Field(default="inferred")


class GlobalTouch(BaseModel):
    """Global variable usage in behavior analysis."""
    entity_id: str
    name: str
    kind: Literal["variable"]
    access_type: Literal["direct", "transitive"]
    provenance: Provenance = Field(default="inferred")


class SideEffectMarker(BaseModel):
    """Side effect marker in behavior analysis."""
    function_id: str
    function_name: str
    category: Literal["messaging", "persistence", "state_mutation", "scheduling"]
    access_type: Literal["direct", "transitive"]
    confidence: Literal["direct", "heuristic", "transitive"]
    provenance: Provenance = Field(default="heuristic")


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

    # Side effects (categorized)
    side_effects: dict[str, list[SideEffectMarker]]  # category → markers

    provenance: Provenance = Field(default="inferred")


class CapabilitySummary(BaseModel):
    """Summary of a capability group."""
    name: str
    type: Literal["domain", "policy", "projection", "infrastructure", "utility"]
    description: str
    function_count: int
    stability: str | None
    doc_quality_dist: dict[str, int]  # {high: N, medium: N, low: N}
    provenance: Provenance = Field(default="precomputed")


class CapabilityDetail(BaseModel):
    """Detailed capability information."""
    name: str
    type: str
    description: str
    function_count: int
    stability: str | None
    doc_quality_dist: dict[str, int]
    dependencies: list[dict]  # Typed edges to other capabilities
    entry_points: list[str]  # Entry point function names
    functions: list[EntitySummary] | None = None  # Optional full function list
    provenance: Provenance = Field(default="precomputed")


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
    focus_type: Literal["entity", "subsystem", "capability", "entry_point"]
    focus: dict  # EntitySummary | SubsystemSummary | dict
    related_entities: list[EntitySummary]
    related_capabilities: list[dict]
    related_subsystems: list[SubsystemSummary]
    relevant_doc_sections: list[dict]
    confidence_notes: str | None = None
    truncated: bool = False
