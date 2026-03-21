"""
SQLModel Table Definitions - Canonical Schema Location.

These models define the database schema and serve as the ORM layer.
Build helpers import from here to populate the database.
"""

import os

from pgvector.sqlalchemy import Vector
from sqlalchemy import Index
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR
from sqlmodel import Column, Field, SQLModel

# Read embedding dimension from environment at import time.
# Safe because the schema is dropped and recreated on every build.
_EMBEDDING_DIM = int(os.environ.get("EMBEDDING_DIMENSION", "768"))


class Entity(SQLModel, table=True):
    """
    Core entity table storing all documentation, metrics, embeddings, and search vectors.

    Represents functions, classes, variables, structs, and other code entities extracted
    from the Legacy MUD codebase via Doxygen and enriched with LLM-generated documentation.
    """

    __tablename__ = "entities"

    # Identity
    entity_id: str = Field(primary_key=True, description="Deterministic {prefix}:{7 hex} ID")

    # Identity (user-facing)
    name: str = Field(default="", description="Bare name: do_look, race_type, etc. (empty for files/dirs)")
    signature: str = Field(
        description="Full signature: void do_look(Character *ch, String argument) (not unique, indexed)"
    )
    kind: str = Field(
        description="function, variable, class, struct, file, enum, define, typedef, namespace, dir, group"
    )
    entity_type: str = Field(description="compound or member")

    # Source location
    file_path: str | None = Field(default=None, description="Relative path: src/fight.cc")
    body_start_line: int | None = Field(default=None, description="Body start line (1-based)")
    body_end_line: int | None = Field(default=None, description="Body end line")
    decl_file_path: str | None = Field(default=None, description="Declaration file path")
    decl_line: int | None = Field(default=None, description="Declaration line number")

    # Source code (extracted at build time from disk)
    definition_text: str | None = Field(default=None, description="C++ definition line")
    source_text: str | None = Field(default=None, description="Full body source code")

    # Documentation
    brief: str | None = Field(default=None, description="One-line summary")
    details: str | None = Field(default=None, description="Detailed documentation")
    params: dict[str, str] | None = Field(
        default=None, sa_column=Column(JSONB(none_as_null=True)), description="JSON: {param_name: description}"
    )
    returns: str | None = Field(default=None, description="Return value description")
    notes: str | None = Field(default=None, description="Implementation notes")
    rationale: str | None = Field(default=None, description="Design rationale")
    usages: dict[str, str] | None = Field(
        default=None, sa_column=Column(JSONB), description="JSON: {caller_key: usage_description}"
    )

    # Classification
    capability: str | None = Field(default=None, description="Capability group name")
    is_entry_point: bool = Field(default=False, description="Is do_*, spell_*, or spec_* function")

    # Precomputed metrics (from build script)
    fan_in: int = Field(default=0, ge=0, description="Incoming CALLS edges")
    fan_out: int = Field(default=0, ge=0, description="Outgoing CALLS edges")
    is_bridge: bool = Field(default=False, description="Callers/callees span different capabilities")

    # Documentation quality signals (FR-001 through FR-004)
    doc_state: str | None = Field(
        default=None,
        description="Documentation generation state: refined_summary, generated_summary, extracted_summary, refined_usage",
    )
    notes_length: int | None = Field(
        default=None, ge=0, description="Character count of notes field (complexity proxy)"
    )
    is_contract_seed: bool = Field(default=False, description="True when fan_in > threshold AND rationale is non-null")
    rationale_specificity: float | None = Field(
        default=None, ge=0.0, le=1.0, description="Heuristic score: rationale length x domain-term density"
    )

    # Embedding (dual views)
    doc_embedding: list[float] | None = Field(
        default=None,
        sa_column=Column(Vector(_EMBEDDING_DIM)),
        description=f"{_EMBEDDING_DIM}-dim embedding of labeled prose fields",
    )
    symbol_embedding: list[float] | None = Field(
        default=None,
        sa_column=Column(Vector(_EMBEDDING_DIM)),
        description=f"{_EMBEDDING_DIM}-dim embedding of qualified scoped signature",
    )

    # Full-text search (dual views)
    doc_search_vector: str | None = Field(
        default=None,
        sa_column=Column(TSVECTOR),
        description="Weighted tsvector: name=A, brief+details=B, notes+rationale+params+returns=C (english)",
    )
    symbol_search_vector: str | None = Field(
        default=None,
        sa_column=Column(TSVECTOR),
        description="Weighted tsvector: name=A, qualified_name+signature=B, definition_text=C (simple)",
    )

    # Trigram similarity
    symbol_searchable: str | None = Field(
        default=None,
        description="Lowercased punctuation-stripped name+qualified_name+signature for pg_trgm",
    )

    # Qualified name
    qualified_name: str | None = Field(
        default=None,
        description="Fully-qualified C++ name (e.g., Logging::stc, Character::position)",
    )


class EntityUsage(SQLModel, table=True):
    """
    Materialized caller→callee usage table (FR-005, FR-006, FR-012).

    Exploded from the `usages` JSONB dict on each Entity row.
    One row per caller→callee pair with a natural-language description.
    Dropped and fully recreated on every build (no incremental updates).
    """

    __tablename__ = "entity_usages"
    __table_args__ = (
        Index("ix_entity_usages_callee", "callee_id"),
        Index("ix_entity_usages_caller", "caller_compound", "caller_sig"),
        Index(
            "ix_entity_usages_embedding",
            "embedding",
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 64},
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
        Index(
            "ix_entity_usages_search_vector",
            "search_vector",
            postgresql_using="gin",
        ),
    )

    # Composite primary key: (callee, caller_compound, caller_sig)
    callee_id: str = Field(
        primary_key=True,
        foreign_key="entities.entity_id",
        description="The callee entity ID",
    )
    caller_compound: str = Field(
        primary_key=True,
        description="Caller compound ID (file-based, from usages key)",
    )
    caller_sig: str = Field(
        primary_key=True,
        description="Caller function signature (from usages key)",
    )

    # Content
    description: str = Field(description="Natural-language description of how the caller uses the callee")

    # Semantic search
    embedding: list[float] | None = Field(
        default=None,
        sa_column=Column(Vector(_EMBEDDING_DIM)),
        description=f"{_EMBEDDING_DIM}-dim embedding of the description text",
    )

    # Keyword search
    search_vector: str | None = Field(
        default=None,
        sa_column=Column(TSVECTOR),
        description="tsvector of description for full-text search",
    )


class Edge(SQLModel, table=True):
    """
    Dependency graph edges (subset of in-memory NetworkX graph).

    Represents relationships between entities: function calls, variable uses,
    class inheritance, file includes, and containment.
    """

    __tablename__ = "edges"

    source_id: str = Field(foreign_key="entities.entity_id", primary_key=True)
    target_id: str = Field(foreign_key="entities.entity_id", primary_key=True)
    relationship: str = Field(primary_key=True, description="calls, uses, inherits, includes, contained_by")


class Capability(SQLModel, table=True):
    """
    Capability group definitions (30 architectural groups).

    Represents high-level functional groupings of related code
    (e.g., combat, magic, persistence, character_state).
    """

    __tablename__ = "capabilities"

    name: str = Field(primary_key=True, description="Capability group name")
    type: str = Field(description="domain, policy, projection, infrastructure, utility")
    description: str = Field(description="Human-readable description")
    function_count: int = Field(ge=0, description="Number of functions in this capability")
    stability: str | None = Field(default=None, description="stable, evolving, experimental")


class CapabilityEdge(SQLModel, table=True):
    """
    Typed dependencies between capability groups.

    Represents architectural relationships: which capabilities depend on which others,
    and how many cross-capability function calls exist.
    """

    __tablename__ = "capability_edges"

    source_cap: str = Field(foreign_key="capabilities.name", primary_key=True)
    target_cap: str = Field(foreign_key="capabilities.name", primary_key=True)
    edge_type: str = Field(
        description="requires_core, requires_policy, requires_projection, requires_infrastructure, uses_utility"
    )
    call_count: int = Field(ge=0, description="Number of cross-capability CALLS edges")
    in_dag: bool = Field(default=False, description="Whether this edge is in the DAG overlay")


class EntryPoint(SQLModel, table=True):
    """
    Entry point functions (commands, spells, special procedures).

    Tracks which capabilities each entry point exercises (direct and transitive).
    """

    __tablename__ = "entry_points"

    entity_id: str = Field(primary_key=True, foreign_key="entities.entity_id")
    name: str = Field(description="do_kill, spell_fireball, spec_cast_cleric, etc.")
    capabilities: list[str] | None = Field(
        default=None, sa_column=Column(JSONB), description="List of capability names exercised"
    )
    entry_type: str | None = Field(default=None, description="do_, spell_, spec_")


class SearchConfig(SQLModel, table=True):
    """
    Precomputed search calibration values produced by the build pipeline.

    The server loads these at startup and caches them for its lifetime.
    """

    __tablename__ = "search_config"

    key: str = Field(primary_key=True, description="Config key (e.g., 'doc_tsrank_ceiling')")
    value: float = Field(description="Numeric config value")
