"""
Pytest Configuration and Fixtures.

Provides test database, mock artifacts, and async support for integration tests.
"""

import pytest
import asyncio
from pathlib import Path
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlmodel import SQLModel

from server.config import ServerConfig
from server.db_models import Entity, Edge, Capability


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
        # High-quality function with full documentation
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

        # Entry point (command)
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
            brief="Kill command implementation",
            doc_state="generated_summary",
            doc_quality="medium",
            capability="commands",
            is_entry_point=True,
            fan_in=1,
            fan_out=15,
            is_bridge=False,
        ),

        # Class entity
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
    ]

    for entity in entities:
        test_session.add(entity)

    await test_session.commit()

    return entities


@pytest.fixture
async def sample_edges(test_session: AsyncSession, sample_entities: list[Entity]) -> list[Edge]:
    """Create sample edges for testing graph operations."""
    if len(sample_entities) < 2:
        return []

    edges = [
        Edge(
            source_id=sample_entities[1].entity_id,  # do_kill
            target_id=sample_entities[0].entity_id,  # damage
            relationship="calls",
        ),
    ]

    for edge in edges:
        test_session.add(edge)

    await test_session.commit()

    return edges
