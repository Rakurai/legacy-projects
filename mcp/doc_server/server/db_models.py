"""
SQLModel Table Definitions - Canonical Schema Location.

These models define the database schema and serve as the ORM layer.
Build helpers import from here to populate the database.
"""

import os

from sqlmodel import SQLModel, Field, Column
from sqlalchemy.dialects.postgresql import TSVECTOR, JSONB
from pgvector.sqlalchemy import Vector

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

    # Identity (internal)
    entity_id: str = Field(primary_key=True, description="Doxygen compound_member ID")
    compound_id: str = Field(description="Doxygen compound refid")
    member_id: str | None = Field(default=None, description="Member hex hash (NULL for compounds)")

    # Identity (user-facing)
    name: str = Field(default="", description="Bare name: do_look, race_type, etc. (empty for files/dirs)")
    signature: str = Field(description="Full signature: void do_look(Character *ch, String argument) (not unique, indexed)")
    kind: str = Field(description="function, variable, class, struct, file, enum, define, typedef, namespace, dir, group")
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
    params: dict[str, str] | None = Field(default=None, sa_column=Column(JSONB), description="JSON: {param_name: description}")
    returns: str | None = Field(default=None, description="Return value description")
    notes: str | None = Field(default=None, description="Implementation notes")
    rationale: str | None = Field(default=None, description="Design rationale")
    usages: dict[str, str] | None = Field(default=None, sa_column=Column(JSONB), description="JSON: {caller_key: usage_description}")
    doc_state: str | None = Field(default=None, description="extracted_summary, refined_summary, etc.")
    doc_quality: str | None = Field(default=None, description="Derived: high, medium, low")

    # Classification
    capability: str | None = Field(default=None, description="Capability group name")
    is_entry_point: bool = Field(default=False, description="Is do_*, spell_*, or spec_* function")

    # Precomputed metrics (from build script)
    fan_in: int = Field(default=0, ge=0, description="Incoming CALLS edges")
    fan_out: int = Field(default=0, ge=0, description="Outgoing CALLS edges")
    is_bridge: bool = Field(default=False, description="Callers/callees span different capabilities")
    side_effect_markers: dict[str, list[str]] | None = Field(
        default=None,
        sa_column=Column(JSONB),
        description="JSON: {messaging: [...], persistence: [...], state_mutation: [...], scheduling: [...]}"
    )

    # Embedding
    embedding: list[float] | None = Field(
        default=None,
        sa_column=Column(Vector(_EMBEDDING_DIM)),
        description=f"{_EMBEDDING_DIM}-dim pgvector embedding",
    )

    # Full-text search
    search_vector: str | None = Field(
        default=None,
        sa_column=Column(TSVECTOR),
        description="Weighted tsvector: name=A, brief/details=B, definition=C, source_text=D"
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
    relationship: str = Field(
        primary_key=True,
        description="calls, uses, inherits, includes, contained_by"
    )


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
    doc_quality_dist: dict = Field(
        sa_column=Column(JSONB),
        description="{high: N, medium: N, low: N}"
    )


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
        default=None,
        sa_column=Column(JSONB),
        description="List of capability names exercised"
    )
    entry_type: str | None = Field(default=None, description="do_, spell_, spec_")
