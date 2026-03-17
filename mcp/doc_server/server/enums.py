"""
Canonical StrEnum definitions for categorical string domains.

StrEnum members ARE strings (DocQuality.HIGH == "high" is True), so they:
- Serialize as plain strings in JSON (Pydantic, FastMCP, MCP protocol)
- Work in SQLAlchemy == / .in_() comparisons against DB str columns
- Provide IDE autocompletion and typo protection at assignment sites

Import enums here for internal logic. Pydantic models annotate fields
directly with the enum type — Pydantic v2 accepts StrEnum natively.
"""

from enum import StrEnum

# ---------------------------------------------------------------------------
# Entity classification
# ---------------------------------------------------------------------------

class EntityKind(StrEnum):
    """Doxygen entity kind."""
    FUNCTION = "function"
    VARIABLE = "variable"
    CLASS = "class"
    STRUCT = "struct"
    FILE = "file"
    ENUM = "enum"
    DEFINE = "define"
    TYPEDEF = "typedef"
    NAMESPACE = "namespace"
    DIR = "dir"
    GROUP = "group"


class EntityType(StrEnum):
    """Whether an entity is a Doxygen compound or member."""
    COMPOUND = "compound"
    MEMBER = "member"


# ---------------------------------------------------------------------------
# Graph relationships
# ---------------------------------------------------------------------------

class Relationship(StrEnum):
    """Edge type in the dependency graph."""
    CALLS = "calls"
    USES = "uses"
    INHERITS = "inherits"
    INCLUDES = "includes"
    CONTAINED_BY = "contained_by"


# ---------------------------------------------------------------------------
# Side-effect analysis
# ---------------------------------------------------------------------------

class SideEffectCategory(StrEnum):
    """Categories of side effects detected by heuristic analysis."""
    MESSAGING = "messaging"
    PERSISTENCE = "persistence"
    STATE_MUTATION = "state_mutation"
    SCHEDULING = "scheduling"


class AccessType(StrEnum):
    """Whether a relationship is direct or transitive."""
    DIRECT = "direct"
    TRANSITIVE = "transitive"


class Confidence(StrEnum):
    """Confidence level of a side-effect marker."""
    DIRECT = "direct"
    HEURISTIC = "heuristic"
    TRANSITIVE = "transitive"


# ---------------------------------------------------------------------------
# Provenance tracking (FR-044)
# ---------------------------------------------------------------------------

class Provenance(StrEnum):
    """Data source label per FR-044."""
    DOXYGEN_EXTRACTED = "doxygen_extracted"
    LLM_GENERATED = "llm_generated"
    SUBSYSTEM_NARRATIVE = "subsystem_narrative"
    PRECOMPUTED = "precomputed"
    INFERRED = "inferred"
    HEURISTIC = "heuristic"
    MEASURED = "measured"


# ---------------------------------------------------------------------------
# Resolution pipeline
# ---------------------------------------------------------------------------

class ResolutionStatus(StrEnum):
    """Outcome of entity resolution."""
    EXACT = "exact"
    AMBIGUOUS = "ambiguous"
    NOT_FOUND = "not_found"


class MatchType(StrEnum):
    """Which resolution stage matched."""
    ENTITY_ID = "entity_id"
    SIGNATURE_EXACT = "signature_exact"
    NAME_EXACT = "name_exact"
    NAME_PREFIX = "name_prefix"
    KEYWORD = "keyword"
    SEMANTIC = "semantic"


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------

class SearchMode(StrEnum):
    """Which search strategy was used."""
    HYBRID = "hybrid"
    SEMANTIC_ONLY = "semantic_only"
    KEYWORD_FALLBACK = "keyword_fallback"


# ---------------------------------------------------------------------------
# Truncation
# ---------------------------------------------------------------------------

class TruncationReason(StrEnum):
    """Why results were truncated."""
    DEPTH_LIMIT = "depth_limit"
    NODE_LIMIT = "node_limit"
    NONE = "none"


# ---------------------------------------------------------------------------
# Capability classification
# ---------------------------------------------------------------------------

class CapabilityType(StrEnum):
    """Capability architectural type."""
    DOMAIN = "domain"
    POLICY = "policy"
    PROJECTION = "projection"
    INFRASTRUCTURE = "infrastructure"
    UTILITY = "utility"


# ---------------------------------------------------------------------------
# Hotspot metrics
# ---------------------------------------------------------------------------

class HotspotMetric(StrEnum):
    """Ranking metric for hotspot detection."""
    FAN_IN = "fan_in"
    FAN_OUT = "fan_out"
    BRIDGE = "bridge"
    UNDERDOCUMENTED = "underdocumented"


# ---------------------------------------------------------------------------
# V2 placeholders
# ---------------------------------------------------------------------------

class FocusType(StrEnum):
    """V2: Context bundle focus type."""
    ENTITY = "entity"
    SUBSYSTEM = "subsystem"
    CAPABILITY = "capability"
    ENTRY_POINT = "entry_point"
