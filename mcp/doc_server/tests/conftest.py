"""
Pytest Configuration and Fixtures.

Provides test database, mock artifacts, and async support for integration tests.
"""

import pytest
import asyncio
from pathlib import Path
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlmodel import SQLModel

import networkx as nx

from server.config import ServerConfig
from server.db_models import Entity, Edge, Capability, CapabilityEdge, EntryPoint


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_config() -> ServerConfig:
    """
    Test configuration using in-memory or test database.

    Override with environment variables for integration tests.
    """
    return ServerConfig(
        db_host="localhost",
        db_port=4010,
        db_name="legacy_og_docs_test",
        db_user="postgres",
        db_password="postgres",
        project_root=Path("/tmp/legacy_test"),
        artifacts_dir=Path(".ai/artifacts"),
        log_level="DEBUG",
    )


@pytest.fixture
async def test_engine(test_config: ServerConfig):
    """Create test database engine."""
    engine = create_async_engine(
        test_config.db_url,
        pool_pre_ping=True,
        echo=False,
    )

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    yield engine

    # Drop tables
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
async def test_session(test_engine) -> AsyncSession:
    """Create test database session."""
    session_factory = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with session_factory() as session:
        yield session


@pytest.fixture
async def sample_entities(test_session: AsyncSession) -> list[Entity]:
    """
    Create sample entities for testing.

    Provides a minimal set of entities covering different kinds and quality levels.
    """
    entities = [
        # [0] High-quality function with full documentation
        Entity(
            entity_id="fight_8cc_1a2b3c4d5e6f",
            compound_id="fight_8cc",
            member_id="1a2b3c4d5e6f",
            name="damage",
            signature="void damage(Character *ch, Character *victim, int dam)",
            kind="function",
            entity_type="member",
            file_path="src/fight.cc",
            body_start_line=100,
            body_end_line=150,
            definition_text="void damage(Character *ch, Character *victim, int dam)",
            source_text="void damage(Character *ch, Character *victim, int dam) {\n    // Apply damage\n}",
            brief="Apply damage to a character",
            details="Calculates and applies damage to a victim character, considering armor, resistances, and other factors.",
            params={"ch": "Attacker", "victim": "Target", "dam": "Base damage amount"},
            returns="void",
            doc_state="refined_summary",
            doc_quality="high",
            capability="combat",
            is_entry_point=False,
            fan_in=23,
            fan_out=8,
            is_bridge=True,
            side_effect_markers={"messaging": ["send_to_char"], "state_mutation": ["affect_to_char"]},
        ),

        # [1] Entry point (command) — calls damage
        Entity(
            entity_id="act_8wiz_8cc_2b3c4d5e6f7g",
            compound_id="act_8wiz_8cc",
            member_id="2b3c4d5e6f7g",
            name="do_kill",
            signature="void do_kill(Character *ch, String argument)",
            kind="function",
            entity_type="member",
            file_path="src/act_wiz.cc",
            body_start_line=200,
            body_end_line=250,
            definition_text="void do_kill(Character *ch, String argument)",
            source_text="void do_kill(Character *ch, String argument) {\n    // Kill handler\n    damage(ch, victim, 100);\n}",
            brief="Kill command implementation",
            doc_state="generated_summary",
            doc_quality="medium",
            capability="commands",
            is_entry_point=True,
            fan_in=1,
            fan_out=15,
            is_bridge=False,
            side_effect_markers={"messaging": ["send_to_char"]},
        ),

        # [2] Class entity
        Entity(
            entity_id="Character_8hh",
            compound_id="Character_8hh",
            member_id=None,
            name="Character",
            signature="class Character",
            kind="class",
            entity_type="compound",
            file_path="src/include/Character.hh",
            brief="Core character class",
            doc_state="extracted_summary",
            doc_quality="low",
            capability="character_state",
            is_entry_point=False,
            fan_in=0,
            fan_out=0,
        ),

        # [3] Global variable (used by damage)
        Entity(
            entity_id="global_max_damage",
            compound_id="fight_8cc",
            member_id="max_damage_var",
            name="max_damage",
            signature="int max_damage",
            kind="variable",
            entity_type="member",
            file_path="src/fight.cc",
            body_start_line=10,
            body_end_line=10,
            brief="Maximum damage cap",
            doc_state="extracted_summary",
            doc_quality="low",
            capability="combat",
            is_entry_point=False,
            fan_in=5,
            fan_out=0,
        ),

        # [4] Another function in combat capability (called by damage transitively)
        Entity(
            entity_id="fight_8cc_armor_absorb",
            compound_id="fight_8cc",
            member_id="armor_absorb",
            name="armor_absorb",
            signature="int armor_absorb(Character *victim, int dam)",
            kind="function",
            entity_type="member",
            file_path="src/fight.cc",
            body_start_line=50,
            body_end_line=80,
            definition_text="int armor_absorb(Character *victim, int dam)",
            source_text="int armor_absorb(Character *victim, int dam) { return dam / 2; }",
            brief="Calculate armor absorption",
            doc_state="refined_summary",
            doc_quality="high",
            capability="combat",
            is_entry_point=False,
            fan_in=10,
            fan_out=2,
            is_bridge=False,
        ),

        # [5] File entity for src/fight.cc (used by related_files)
        Entity(
            entity_id="file_fight_cc",
            compound_id="file_fight_cc",
            member_id=None,
            name="fight.cc",
            signature="src/fight.cc",
            kind="file",
            entity_type="compound",
            file_path="src/fight.cc",
            brief="Combat implementation file",
            doc_state="extracted_summary",
            doc_quality="medium",
            capability="combat",
            is_entry_point=False,
            fan_in=0,
            fan_out=0,
        ),

        # [6] File entity for src/include/Character.hh (include target)
        Entity(
            entity_id="file_character_hh",
            compound_id="file_character_hh",
            member_id=None,
            name="Character.hh",
            signature="src/include/Character.hh",
            kind="file",
            entity_type="compound",
            file_path="src/include/Character.hh",
            brief="Character class header",
            doc_state="extracted_summary",
            doc_quality="medium",
            capability="character_state",
            is_entry_point=False,
            fan_in=0,
            fan_out=0,
        ),
    ]

    for entity in entities:
        test_session.add(entity)

    await test_session.commit()

    return entities


@pytest.fixture
async def sample_edges(test_session: AsyncSession, sample_entities: list[Entity]) -> list[Edge]:
    """Create sample edges for testing graph operations."""
    edges = [
        # do_kill → damage (calls)
        Edge(
            source_id=sample_entities[1].entity_id,
            target_id=sample_entities[0].entity_id,
            relationship="calls",
        ),
        # damage → armor_absorb (calls)
        Edge(
            source_id=sample_entities[0].entity_id,
            target_id=sample_entities[4].entity_id,
            relationship="calls",
        ),
        # damage → max_damage (uses — global variable)
        Edge(
            source_id=sample_entities[0].entity_id,
            target_id=sample_entities[3].entity_id,
            relationship="uses",
        ),
        # file_fight_cc → file_character_hh (includes)
        Edge(
            source_id=sample_entities[5].entity_id,
            target_id=sample_entities[6].entity_id,
            relationship="includes",
        ),
        # Character → Character_8hh (inherits — for class hierarchy test)
        # We'll pretend Character has a base class; use the file entity as stand-in.
    ]

    for edge in edges:
        test_session.add(edge)

    await test_session.commit()

    return edges


@pytest.fixture
async def sample_capabilities(test_session: AsyncSession, sample_entities: list[Entity]) -> list[Capability]:
    """Create sample capability groups for testing."""
    capabilities = [
        Capability(
            name="combat",
            type="domain",
            description="Combat system: damage, healing, attacks",
            function_count=25,
            stability="stable",
            doc_quality_dist={"high": 10, "medium": 10, "low": 5},
        ),
        Capability(
            name="commands",
            type="policy",
            description="Player command handlers (do_* functions)",
            function_count=80,
            stability="evolving",
            doc_quality_dist={"high": 20, "medium": 40, "low": 20},
        ),
        Capability(
            name="character_state",
            type="domain",
            description="Character attributes, stats, and state management",
            function_count=40,
            stability="stable",
            doc_quality_dist={"high": 15, "medium": 15, "low": 10},
        ),
    ]

    for cap in capabilities:
        test_session.add(cap)

    await test_session.commit()

    return capabilities


@pytest.fixture
async def sample_capability_edges(
    test_session: AsyncSession,
    sample_capabilities: list[Capability],
) -> list[CapabilityEdge]:
    """Create sample capability edges for testing."""
    edges = [
        CapabilityEdge(
            source_cap="commands",
            target_cap="combat",
            edge_type="requires_core",
            call_count=42,
            in_dag=True,
        ),
        CapabilityEdge(
            source_cap="combat",
            target_cap="character_state",
            edge_type="requires_core",
            call_count=31,
            in_dag=True,
        ),
    ]

    for edge in edges:
        test_session.add(edge)

    await test_session.commit()

    return edges


@pytest.fixture
async def sample_entry_points(
    test_session: AsyncSession,
    sample_entities: list[Entity],
) -> list[EntryPoint]:
    """Create sample entry point records for testing."""
    entry_points = [
        EntryPoint(
            entity_id=sample_entities[1].entity_id,  # do_kill
            name="do_kill",
            capabilities=["commands", "combat"],
            entry_type="do_",
        ),
    ]

    for ep in entry_points:
        test_session.add(ep)

    await test_session.commit()

    return entry_points


@pytest.fixture
def sample_graph(sample_entities: list[Entity], sample_edges: list[Edge]) -> nx.MultiDiGraph:
    """
    Build a NetworkX graph from sample entities and edges.

    Mirrors the structure built by server.graph.load_graph but from test data.
    """
    g = nx.MultiDiGraph()

    # Add nodes
    for entity in sample_entities:
        g.add_node(entity.entity_id, name=entity.name, kind=entity.kind)

    # Add edges
    for edge in sample_edges:
        g.add_edge(
            edge.source_id,
            edge.target_id,
            type=edge.relationship,
        )

    return g
