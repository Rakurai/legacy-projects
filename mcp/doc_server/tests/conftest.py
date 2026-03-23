"""
Pytest Configuration and Fixtures.

Provides test database, mock artifacts, and async support for integration tests.
"""

import pytest
from contextlib import asynccontextmanager
from pathlib import Path
import re
from unittest.mock import AsyncMock, MagicMock

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import text
from sqlmodel import SQLModel

import networkx as nx

from server.config import ServerConfig
from server.db_models import Capability, CapabilityEdge, Edge, Entity, EntityUsage, EntryPoint
from server.retrieval_view import RetrievalView


def _score_documents(query: str, docs: list[str]) -> list[float]:
    """Deterministic mixed-sign logit fixture for search tests."""
    query_lower = query.lower().strip()
    query_tokens = {token for token in re.findall(r"[a-z0-9_]+", query_lower) if token}
    if not query_lower:
        return []

    scores: list[float] = []
    for doc in docs:
        doc_lower = doc.lower()
        doc_tokens = {token for token in re.findall(r"[a-z0-9_]+", doc_lower) if token}
        overlap = len(query_tokens & doc_tokens)
        score = -1.25 + (0.65 * overlap)

        if query_lower in doc_lower:
            score += 1.4

        if "::" in query_lower and query_lower in doc_lower:
            score += 0.4

        if overlap == 0:
            score -= 0.35

        scores.append(score)

    return scores


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
        artifacts_dir=Path("artifacts"),
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

    # Create extensions and tables
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm"))
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
        # [0] High-quality function with full documentation — is_contract_seed candidate
        Entity(
            entity_id="fn:a1b2c3d",
            name="damage",
            qualified_name="Combat::damage",
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
            notes="Damage is capped at max_damage. Immortal characters are immune. The dam parameter is base damage before armor mitigation.",
            rationale="Central combat damage function called by spells, attacks, and traps. Must handle all damage types consistently to ensure balance.",
            capability="combat",
            is_entry_point=False,
            fan_in=23,
            fan_out=8,
            is_bridge=True,
            doc_state="refined_summary",
            notes_length=150,
            is_contract_seed=True,
            rationale_specificity=0.85,
            symbol_searchable="damage combat::damage void damage character ch character victim int dam",
        ),
        # [1] Entry point (command) — calls damage
        Entity(
            entity_id="fn:b2c3d4e",
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
            capability="commands",
            is_entry_point=True,
            fan_in=1,
            fan_out=15,
            is_bridge=False,
            doc_state="generated_summary",
            notes_length=None,
            is_contract_seed=False,
            rationale_specificity=None,
            symbol_searchable="do_kill void do_kill character ch string argument",
        ),
        # [2] Class entity
        Entity(
            entity_id="cls:c3d4e5f",
            name="Character",
            signature="class Character",
            kind="class",
            entity_type="compound",
            file_path="src/include/Character.hh",
            brief="Core character class",
            capability="character_state",
            is_entry_point=False,
            fan_in=0,
            fan_out=0,
            doc_state="extracted_summary",
            notes_length=None,
            is_contract_seed=False,
            rationale_specificity=None,
            symbol_searchable="character class character",
        ),
        # [3] Global variable (used by damage)
        Entity(
            entity_id="var:d4e5f6a",
            name="max_damage",
            signature="int max_damage",
            kind="variable",
            entity_type="member",
            file_path="src/fight.cc",
            body_start_line=10,
            body_end_line=10,
            brief="Maximum damage cap",
            capability="combat",
            is_entry_point=False,
            fan_in=5,
            fan_out=0,
            doc_state="extracted_summary",
            notes_length=None,
            is_contract_seed=False,
            rationale_specificity=None,
            symbol_searchable="max_damage int max_damage",
        ),
        # [4] Another function in combat capability (called by damage transitively)
        Entity(
            entity_id="fn:e5f6a7b",
            name="armor_absorb",
            qualified_name="Combat::armor_absorb",
            signature="int armor_absorb(Character *victim, int dam)",
            kind="function",
            entity_type="member",
            file_path="src/fight.cc",
            body_start_line=50,
            body_end_line=80,
            definition_text="int armor_absorb(Character *victim, int dam)",
            source_text="int armor_absorb(Character *victim, int dam) { return dam / 2; }",
            brief="Calculate armor absorption",
            capability="combat",
            is_entry_point=False,
            fan_in=10,
            fan_out=2,
            is_bridge=False,
            doc_state="refined_usage",
            notes_length=None,
            is_contract_seed=False,
            rationale_specificity=0.30,
            symbol_searchable="armor_absorb combat::armor_absorb int armor_absorb character victim int dam",
        ),
        # [5] File entity for src/fight.cc (used by related_files)
        Entity(
            entity_id="file:f6a7b8c",
            name="fight.cc",
            signature="src/fight.cc",
            kind="file",
            entity_type="compound",
            file_path="src/fight.cc",
            brief="Combat implementation file",
            capability="combat",
            is_entry_point=False,
            fan_in=0,
            fan_out=0,
            doc_state=None,
            notes_length=None,
            is_contract_seed=False,
            rationale_specificity=None,
            symbol_searchable="fight.cc src/fight.cc",
        ),
        # [6] File entity for src/include/Character.hh (include target)
        Entity(
            entity_id="file:a7b8c9d",
            name="Character.hh",
            signature="src/include/Character.hh",
            kind="file",
            entity_type="compound",
            file_path="src/include/Character.hh",
            brief="Character class header",
            capability="character_state",
            is_entry_point=False,
            fan_in=0,
            fan_out=0,
            doc_state=None,
            notes_length=None,
            is_contract_seed=False,
            rationale_specificity=None,
            symbol_searchable="character.hh src/include/character.hh",
        ),
        # [7] Same name "damage" but in Logging scope — for qualified name disambiguation tests
        Entity(
            entity_id="fn:h8i9j0k",
            name="damage",
            qualified_name="Logging::damage",
            signature="void damage(const char *msg)",
            kind="function",
            entity_type="member",
            file_path="src/logging.cc",
            body_start_line=30,
            body_end_line=40,
            definition_text="void damage(const char *msg)",
            source_text="void damage(const char *msg) { log_info(msg); }",
            brief="Log a damage event",
            capability="logging",
            is_entry_point=False,
            fan_in=2,
            fan_out=1,
            is_bridge=False,
            doc_state="generated_summary",
            notes_length=None,
            is_contract_seed=False,
            rationale_specificity=None,
            symbol_searchable="damage logging::damage void damage const char msg",
        ),
    ]

    for entity in entities:
        test_session.add(entity)

    await test_session.commit()

    # Populate dual tsvectors for full-text search in tests
    await test_session.execute(
        text(
            "UPDATE entities SET doc_search_vector = "
            "setweight(to_tsvector('english', coalesce(name, '')), 'A') || "
            "setweight(to_tsvector('english', coalesce(brief, '') || ' ' || coalesce(details, '')), 'B') || "
            "setweight(to_tsvector('english', coalesce(notes, '') || ' ' || coalesce(rationale, '') || ' ' || coalesce(returns, '') || ' ' || coalesce((SELECT string_agg(value, ' ') FROM jsonb_each_text(params)), '')), 'C')"
        )
    )
    await test_session.execute(
        text(
            "UPDATE entities SET symbol_search_vector = "
            "setweight(to_tsvector('simple', coalesce(name, '')), 'A') || "
            "setweight(to_tsvector('simple', coalesce(qualified_name, '') || ' ' || coalesce(signature, '')), 'B') || "
            "setweight(to_tsvector('simple', coalesce(definition_text, '')), 'C')"
        )
    )
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
        # Character → Character.hh (inherits — for class hierarchy direction tests)
        Edge(
            source_id=sample_entities[2].entity_id,
            target_id=sample_entities[6].entity_id,
            relationship="inherits",
        ),
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
        ),
        Capability(
            name="commands",
            type="policy",
            description="Player command handlers (do_* functions)",
            function_count=80,
            stability="evolving",
        ),
        Capability(
            name="character_state",
            type="domain",
            description="Character attributes, stats, and state management",
            function_count=40,
            stability="stable",
        ),
        Capability(
            name="logging",
            type="infrastructure",
            description="Logging and diagnostic output",
            function_count=10,
            stability="stable",
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


@pytest.fixture
def mock_embedding_provider():
    """Mock embedding provider for tests that call hybrid_search directly."""
    mock = MagicMock()
    mock.dimension = 768
    mock.aembed = AsyncMock(return_value=[0.0] * 768)
    return mock


@pytest.fixture
def mock_cross_encoder():
    """Mock cross-encoder for tests that call hybrid_search directly."""
    mock = MagicMock()
    mock.arerank = AsyncMock(side_effect=_score_documents)
    return mock


@pytest.fixture
def mock_doc_view(mock_cross_encoder):
    """Mock doc RetrievalView for tests."""
    return RetrievalView(
        name="doc",
        embedding_column="doc_embedding",
        tsvector_column="doc_search_vector",
        tsvector_dictionary="english",
        cross_encoder=mock_cross_encoder,
        ts_rank_ceiling=1.0,
        floor_thresholds={"semantic": 0.3, "keyword_shaped": 0.05},
        assemble_embed_text=lambda e: e.brief or e.name,
    )


@pytest.fixture
def mock_symbol_view(mock_cross_encoder):
    """Mock symbol RetrievalView for tests."""
    return RetrievalView(
        name="symbol",
        embedding_column="symbol_embedding",
        tsvector_column="symbol_search_vector",
        tsvector_dictionary="simple",
        cross_encoder=mock_cross_encoder,
        ts_rank_ceiling=1.0,
        floor_thresholds={"semantic": 0.3, "keyword_shaped": 0.05, "trigram": 0.2},
        assemble_embed_text=lambda e: f"{e.qualified_name or e.name} {e.signature or ''}",
    )


@pytest.fixture
def mock_ctx(test_session: AsyncSession, sample_graph: nx.MultiDiGraph, test_config: ServerConfig):
    """
    Create a mock FastMCP Context for direct tool invocation in tests.

    The mock wraps test_session inside a db_manager.session() context manager
    so tools that do ``async with lc["db_manager"].session() as session:`` get
    the same session that already contains the test fixtures.
    """
    mock_db_manager = MagicMock()

    @asynccontextmanager
    async def _yield_session():
        yield test_session

    mock_db_manager.session = _yield_session

    # Mock embedding provider (returns zero vector)
    mock_embedding = MagicMock()
    mock_embedding.dimension = 768
    mock_embedding.aembed = AsyncMock(return_value=[0.0] * 768)

    # Mock cross-encoder (returns representative mixed-sign logits)
    mock_cross_encoder = MagicMock()
    mock_cross_encoder.arerank = AsyncMock(side_effect=_score_documents)

    doc_view = RetrievalView(
        name="doc",
        embedding_column="doc_embedding",
        tsvector_column="doc_search_vector",
        tsvector_dictionary="english",
        cross_encoder=mock_cross_encoder,
        ts_rank_ceiling=1.0,
        floor_thresholds={"semantic": 0.3, "keyword_shaped": 0.05},
        assemble_embed_text=lambda e: e.brief or e.name,
    )

    symbol_view = RetrievalView(
        name="symbol",
        embedding_column="symbol_embedding",
        tsvector_column="symbol_search_vector",
        tsvector_dictionary="simple",
        cross_encoder=mock_cross_encoder,
        ts_rank_ceiling=1.0,
        floor_thresholds={"semantic": 0.3, "keyword_shaped": 0.05, "trigram": 0.2},
        assemble_embed_text=lambda e: f"{e.qualified_name or e.name} {e.signature or ''}",
    )

    lifespan_context = {
        "config": test_config,
        "db_manager": mock_db_manager,
        "graph": sample_graph,
        "doc_embedding_provider": mock_embedding,
        "symbol_embedding_provider": mock_embedding,
        "doc_view": doc_view,
        "symbol_view": symbol_view,
    }

    ctx = MagicMock()
    ctx.lifespan_context = lifespan_context

    return ctx


@pytest.fixture
async def sample_entity_usages(
    test_session: AsyncSession,
    sample_entities: list[Entity],
) -> list[EntityUsage]:
    """
    Create sample EntityUsage rows for the damage entity (index 0).

    Provides 5 distinct caller→callee usage entries for testing explain_interface,
    usage-based search, and include_usages functionality. Embeddings are None
    (tests use keyword search or bypass semantic scoring).
    """
    damage_id = sample_entities[0].entity_id  # "fn:a1b2c3d"

    usages = [
        EntityUsage(
            callee_id=damage_id,
            caller_compound="act_wiz_8cc",
            caller_sig="void do_kill(Character *ch, String argument)",
            description="Calls damage to apply a lethal blow to the target character in combat.",
            embedding=None,
            search_vector=None,
        ),
        EntityUsage(
            callee_id=damage_id,
            caller_compound="spell_8cc",
            caller_sig="void spell_fireball(Character *ch, Character *victim, int level)",
            description="Used to deliver fire-based magical damage after computing spell power from caster level.",
            embedding=None,
            search_vector=None,
        ),
        EntityUsage(
            callee_id=damage_id,
            caller_compound="fight_8cc",
            caller_sig="void one_hit(Character *ch, Character *victim, int dt)",
            description="Applies physical attack damage for a single weapon strike, passing computed dam value.",
            embedding=None,
            search_vector=None,
        ),
        EntityUsage(
            callee_id=damage_id,
            caller_compound="affect_8cc",
            caller_sig="void affect_tick(Character *ch)",
            description="Applies poison damage each game tick while the poison affect is active on the character.",
            embedding=None,
            search_vector=None,
        ),
        EntityUsage(
            callee_id=damage_id,
            caller_compound="trap_8cc",
            caller_sig="void trigger_trap(Character *ch, Object *obj)",
            description="Delivers trap damage when a character activates a trapped object or room trigger.",
            embedding=None,
            search_vector=None,
        ),
    ]

    for usage in usages:
        test_session.add(usage)

    await test_session.commit()

    # Populate tsvectors for full-text search in tests
    await test_session.execute(text("UPDATE entity_usages SET search_vector = to_tsvector('english', description)"))
    await test_session.commit()

    return usages


@pytest.fixture
def mock_ctx_no_graph(test_session: AsyncSession, test_config: ServerConfig):
    """Mock Context without a graph (for tools that don't need it)."""
    mock_db_manager = MagicMock()

    @asynccontextmanager
    async def _yield_session():
        yield test_session

    mock_db_manager.session = _yield_session

    mock_embedding = MagicMock()
    mock_embedding.dimension = 768
    mock_embedding.aembed = AsyncMock(return_value=[0.0] * 768)

    mock_cross_encoder = MagicMock()
    mock_cross_encoder.arerank = AsyncMock(side_effect=_score_documents)

    doc_view = RetrievalView(
        name="doc",
        embedding_column="doc_embedding",
        tsvector_column="doc_search_vector",
        tsvector_dictionary="english",
        cross_encoder=mock_cross_encoder,
        ts_rank_ceiling=1.0,
        floor_thresholds={"semantic": 0.3, "keyword_shaped": 0.05},
        assemble_embed_text=lambda e: e.brief or e.name,
    )

    symbol_view = RetrievalView(
        name="symbol",
        embedding_column="symbol_embedding",
        tsvector_column="symbol_search_vector",
        tsvector_dictionary="simple",
        cross_encoder=mock_cross_encoder,
        ts_rank_ceiling=1.0,
        floor_thresholds={"semantic": 0.3, "keyword_shaped": 0.05, "trigram": 0.2},
        assemble_embed_text=lambda e: f"{e.qualified_name or e.name} {e.signature or ''}",
    )

    lifespan_context = {
        "config": test_config,
        "db_manager": mock_db_manager,
        "graph": nx.MultiDiGraph(),
        "embedding_provider": mock_embedding,
        "doc_view": doc_view,
        "symbol_view": symbol_view,
    }

    ctx = MagicMock()
    ctx.lifespan_context = lifespan_context

    return ctx
