"""
Model Evaluation — Embedding + Cross-Encoder comparison for multi-view search.

Resolves design open items E-01 (embedding model selection) and E-02 (cross-encoder
model selection) from specs/004-multi-view-search.

Usage:
    cd mcp/doc_server
    uv run python model_eval.py --generate         # generate eval_queries.json
    uv run python model_eval.py                    # run all evaluations
    uv run python model_eval.py --embedding-only   # embedding recall only
    uv run python model_eval.py --reranker-only    # cross-encoder rerank only
    uv run python model_eval.py --groups 1          # run only group 1

Workflow:
    1. Define queries in QUERY_DEFS (query/category/view)
    2. Run --generate to create eval_queries.json with candidates from 3 searches
    3. Hand-select expected_ids in the JSON file
    4. Run eval (default mode) to measure models against ground truth

Comparison groups (embedding eval is per-group, reranker eval uses fixed candidate pool):

    Group 1 — BGE+Jina split (doc=prose, symbol=code):
        embedding:  bge-base-en-v1.5      (doc view)
        embedding:  jina-embeddings-v2-base-code (symbol view)
        reranker:   jina-reranker-v1-turbo-en

    Group 2 — Control (current defaults):
        embedding:  bge-base-en-v1.5      (both views)
        reranker:   ms-marco-MiniLM-L-12-v2

Caches embedding vectors in artifacts/embed_cache_{model_slug}_{dim}_{view}.pkl
via build_helpers/embeddings_loader. Re-runnable — cached embeddings are reused.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import networkx as nx
import numpy as np
from sqlmodel import select
from tqdm import tqdm

from build_helpers.embeddings_loader import load_embedding_cache, save_embedding_cache
from server.config import ServerConfig
from server.cross_encoder import CrossEncoderProvider
from server.db import DatabaseManager
from server.db_models import Entity
from server.embedding import LocalEmbeddingProvider
from server.graph import CONTAINED_BY, get_callees, get_callers, load_graph
from server.search import _doc_keyword_scores, _exact_match_ids, _symbol_keyword_scores, _trigram_scores

# ---------------------------------------------------------------------------
# Ground-truth eval queries
# ---------------------------------------------------------------------------


@dataclass
class EvalQuery:
    """A ground-truth query with expected entity IDs and metadata."""

    query: str
    category: str  # US1, US2, US3, US4, NEG
    view: str  # "doc", "symbol", "both" — which view should find this
    expected_ids: list[str] = field(default_factory=list)


# Query definitions — add new queries here, then run --generate to populate candidates.
# expected_ids are loaded from eval_queries.json at eval time.
QUERY_DEFS: list[EvalQuery] = [
    # --- US1: Bare name lookups (ambiguous — multiple entities share the name) ---
    EvalQuery(query="damage", category="US1", view="both"),
    EvalQuery(query="act", category="US1", view="both"),
    EvalQuery(query="update", category="US1", view="both"),
    EvalQuery(query="name", category="US1", view="both"),
    EvalQuery(query="level", category="US1", view="both"),
    # --- US2: Natural language / behavioral queries ---
    EvalQuery(query="function that calculates melee combat damage", category="US2", view="doc"),
    EvalQuery(query="how does the auction system handle bidding", category="US2", view="doc"),
    EvalQuery(query="character death and respawn logic", category="US2", view="doc"),
    EvalQuery(query="send formatted text to player connection", category="US2", view="doc"),
    EvalQuery(query="calculate experience points gained from killing a mob", category="US2", view="doc"),
    EvalQuery(query="object wear location and equipment slot validation", category="US2", view="doc"),
    EvalQuery(query="moving a character between rooms", category="US2", view="doc"),
    EvalQuery(query="saving character data to disk", category="US2", view="doc"),
    EvalQuery(query="how does the weather system update game world conditions", category="US2", view="doc"),
    EvalQuery(query="character death and corpse creation", category="US2", view="doc"),
    EvalQuery(query="reading structured data from game files", category="US2", view="doc"),
    # --- US3: Scoped identifier queries ---
    EvalQuery(query="Character::level", category="US3", view="symbol"),
    EvalQuery(query="Room::exit", category="US3", view="symbol"),
    EvalQuery(query="Character::affected", category="US3", view="symbol"),
    EvalQuery(query="Room::name", category="US3", view="symbol"),
    EvalQuery(query="Room::is_dark", category="US3", view="symbol"),
    # --- US4: Full signature queries ---
    EvalQuery(query="void one_hit(Character*, Character*, int)", category="US4", view="symbol"),
    EvalQuery(query="bool Character::is_npc() const", category="US4", view="symbol"),
    EvalQuery(query="void damage(Character*, Character*, int, int, int)", category="US4", view="symbol"),
    EvalQuery(query="int hit_gain(Character*)", category="US4", view="symbol"),
    EvalQuery(query="void raw_kill(Character*, Character*)", category="US4", view="symbol"),
    # --- NEG: Negative / nonsense queries (should produce low scores) ---
    EvalQuery(query="javascript webpack configuration bundler", category="NEG", view="doc"),
    EvalQuery(query="kubernetes pod autoscaling horizontal", category="NEG", view="doc"),
    EvalQuery(query="react useState hook component lifecycle", category="NEG", view="doc"),
    EvalQuery(query="void AbstractFactoryBean::createProxy()", category="NEG", view="symbol"),
]

# Path to the eval queries JSON file (expected_ids + candidate annotations)
EVAL_QUERIES_FILE = Path(__file__).parent / "eval_queries.json"

# Max seed entities for graph expansion in --generate mode
_GRAPH_SEED_LIMIT = 5


# ---------------------------------------------------------------------------
# JSON file I/O — expected_ids + candidate annotations
# ---------------------------------------------------------------------------


def _entity_info(entity: Entity) -> dict[str, str | None]:
    """Minimal entity metadata for human review in JSON."""
    return {
        "entity_id": entity.entity_id,
        "kind": entity.kind,
        "name": entity.name,
        "qualified_name": entity.qualified_name,
        "signature": entity.signature,
        "brief": entity.brief,
    }


def load_eval_queries() -> list[EvalQuery]:
    """Load eval queries with expected_ids populated from the JSON file.

    Query definitions come from QUERY_DEFS (Python). expected_ids come from
    eval_queries.json. If the file is missing, expected_ids default to [].
    """
    expected_map: dict[str, list[str]] = {}
    if EVAL_QUERIES_FILE.exists():
        data = json.loads(EVAL_QUERIES_FILE.read_text())
        expected_map = {entry["query"]: entry.get("expected_ids", []) for entry in data}

    queries: list[EvalQuery] = []
    for qdef in QUERY_DEFS:
        ids = expected_map.get(qdef.query, [])
        queries.append(EvalQuery(
            query=qdef.query, category=qdef.category, view=qdef.view, expected_ids=ids,
        ))
    return queries


def _get_graph_neighbors(
    graph: nx.MultiDiGraph,
    entity_id: str,
    entity_map: dict[str, Entity],
) -> list[dict[str, Any]]:
    """Get direct callers, callees, containers, and containees for an entity."""
    neighbors: list[dict[str, Any]] = []
    seen: set[str] = set()

    def _add(eid: str, relation: str) -> None:
        if eid in seen or eid not in entity_map:
            return
        seen.add(eid)
        info = _entity_info(entity_map[eid])
        info["relation"] = relation
        info["seed_id"] = entity_id
        neighbors.append(info)

    # Callers (depth=1)
    callers = get_callers(graph, entity_id, depth=1, limit=10)
    for eid in callers.get(1, []):
        _add(eid, "caller")

    # Callees (depth=1)
    callees = get_callees(graph, entity_id, depth=1, limit=10)
    for eid in callees.get(1, []):
        _add(eid, "callee")

    # Container (outgoing contained_by edges)
    if entity_id in graph:
        for _, target, data in graph.out_edges(entity_id, data=True):
            if data.get("type") == CONTAINED_BY:
                _add(target, "container")

    # Containees (incoming contained_by edges)
    if entity_id in graph:
        for source, _, data in graph.in_edges(entity_id, data=True):
            if data.get("type") == CONTAINED_BY:
                _add(source, "containee")

    return neighbors


async def generate_eval_file() -> None:
    """Generate eval_queries.json with candidates from 3 search perspectives.

    For each query in QUERY_DEFS, gathers candidates via:
    1. Text search — exact match, doc/symbol keyword (ts_rank), trigram (pg_trgm)
    2. Semantic search — doc/symbol embedding cosine similarity
    3. Graph search — callers/callees/container/containee of top text+semantic hits

    Preserves existing expected_ids if the file already exists.
    """
    # Preserve existing expected_ids
    existing: dict[str, list[str]] = {}
    if EVAL_QUERIES_FILE.exists():
        for entry in json.loads(EVAL_QUERIES_FILE.read_text()):
            existing[entry["query"]] = entry.get("expected_ids", [])

    config = ServerConfig()
    db = DatabaseManager(config)
    artifacts_path = Path(__file__).resolve().parent.parent.parent / "artifacts"

    bge_config = EmbeddingModelConfig(
        name="BAAI/bge-base-en-v1.5", slug="BAAI-bge-base-en-v1.5", dimension=768,
    )

    async with db.session() as session:
        # Load entities + graph
        result = await session.execute(select(Entity))
        entities = list(result.scalars().all())
        entity_map: dict[str, Entity] = {e.entity_id: e for e in entities}
        graph = await load_graph(session)
        print(f"Loaded {len(entities)} entities, graph: {graph.number_of_nodes()} nodes, {graph.number_of_edges()} edges")

        # Prepare embedding matrices
        entity_ids = [e.entity_id for e in entities]
        doc_texts = {e.entity_id: assemble_doc_text(e) for e in entities}
        sym_texts = {e.entity_id: assemble_symbol_text(e) for e in entities}

        doc_embeddings = get_or_compute_embeddings(bge_config, "doc", entity_ids, doc_texts, artifacts_path)
        sym_embeddings = get_or_compute_embeddings(bge_config, "symbol", entity_ids, sym_texts, artifacts_path)

        doc_matrix = np.array([doc_embeddings[eid] for eid in entity_ids])
        sym_matrix = np.array([sym_embeddings[eid] for eid in entity_ids])

        doc_provider = _get_provider(bge_config)
        sym_provider = _get_provider(bge_config)

        per_channel = 20
        entries: list[dict[str, Any]] = []

        for qdef in tqdm(QUERY_DEFS, desc="Generating candidates", unit="query"):
            # Handle scoped queries: also search bare name
            search_query = qdef.query
            if "::" in qdef.query:
                parts = qdef.query.rsplit("::", 1)
                if len(parts) == 2 and parts[0].strip() and parts[1].strip():  # noqa: PLR2004
                    search_query = parts[1].strip()

            # --- 1. Text search ---
            text_candidates: list[dict[str, Any]] = []
            text_seen: set[str] = set()

            # Exact match
            exact_ids = await _exact_match_ids(session, search_query, None, None)
            for eid in sorted(exact_ids):
                if eid in entity_map and eid not in text_seen:
                    text_seen.add(eid)
                    info = _entity_info(entity_map[eid])
                    info["score"] = 1.0
                    info["channel"] = "exact"
                    text_candidates.append(info)

            # Qualified name match for scoped queries
            if "::" in qdef.query:
                from sqlalchemy import select as sa_select
                qn_stmt = sa_select(Entity.entity_id).where(
                    Entity.qualified_name.ilike(f"%{qdef.query}%"),
                )
                qn_result = await session.execute(qn_stmt)
                for (eid,) in qn_result.all():
                    if eid in entity_map and eid not in text_seen:
                        text_seen.add(eid)
                        info = _entity_info(entity_map[eid])
                        info["score"] = 1.0
                        info["channel"] = "qualified_name"
                        text_candidates.append(info)

            # Doc keyword (ts_rank)
            doc_kw = await _doc_keyword_scores(session, search_query, None, None, per_channel)
            for eid, score in sorted(doc_kw.items(), key=lambda x: x[1], reverse=True):
                if eid in entity_map and eid not in text_seen:
                    text_seen.add(eid)
                    info = _entity_info(entity_map[eid])
                    info["score"] = round(score, 4)
                    info["channel"] = "doc_keyword"
                    text_candidates.append(info)

            # Symbol keyword (ts_rank)
            sym_kw = await _symbol_keyword_scores(session, search_query, None, None, per_channel)
            for eid, score in sorted(sym_kw.items(), key=lambda x: x[1], reverse=True):
                if eid in entity_map and eid not in text_seen:
                    text_seen.add(eid)
                    info = _entity_info(entity_map[eid])
                    info["score"] = round(score, 4)
                    info["channel"] = "symbol_keyword"
                    text_candidates.append(info)

            # Trigram similarity
            trgm = await _trigram_scores(session, search_query, None, None, per_channel)
            for eid, score in sorted(trgm.items(), key=lambda x: x[1], reverse=True):
                if eid in entity_map and eid not in text_seen:
                    text_seen.add(eid)
                    info = _entity_info(entity_map[eid])
                    info["score"] = round(score, 4)
                    info["channel"] = "trigram"
                    text_candidates.append(info)

            # --- 2. Semantic search ---
            semantic_candidates: list[dict[str, Any]] = []
            semantic_seen: set[str] = set()

            doc_q_vec = np.array(doc_provider.embed(qdef.query))
            sym_q_vec = np.array(sym_provider.embed(qdef.query))
            doc_ranked = cosine_rank(doc_q_vec, doc_matrix, entity_ids)
            sym_ranked = cosine_rank(sym_q_vec, sym_matrix, entity_ids)

            for eid, score in doc_ranked[:per_channel]:
                if eid in entity_map and eid not in semantic_seen:
                    semantic_seen.add(eid)
                    info = _entity_info(entity_map[eid])
                    info["score"] = round(score, 4)
                    info["channel"] = "doc_cosine"
                    semantic_candidates.append(info)

            for eid, score in sym_ranked[:per_channel]:
                if eid in entity_map and eid not in semantic_seen:
                    semantic_seen.add(eid)
                    info = _entity_info(entity_map[eid])
                    info["score"] = round(score, 4)
                    info["channel"] = "symbol_cosine"
                    semantic_candidates.append(info)

            # --- 3. Graph search ---
            # Use top entities from text + semantic as seeds
            seed_ids: list[str] = []
            seed_seen: set[str] = set()
            for cand in text_candidates + semantic_candidates:
                eid = cand["entity_id"]
                if eid not in seed_seen:
                    seed_seen.add(eid)
                    seed_ids.append(eid)
                if len(seed_ids) >= _GRAPH_SEED_LIMIT:
                    break

            graph_candidates: list[dict[str, Any]] = []
            graph_seen: set[str] = set(seed_seen)  # don't repeat seeds
            for seed_id in seed_ids:
                for neighbor in _get_graph_neighbors(graph, seed_id, entity_map):
                    eid = neighbor["entity_id"]
                    if eid not in graph_seen:
                        graph_seen.add(eid)
                        graph_candidates.append(neighbor)

            entries.append({
                "query": qdef.query,
                "category": qdef.category,
                "view": qdef.view,
                "expected_ids": existing.get(qdef.query, []),
                "candidates": {
                    "text_search": text_candidates,
                    "semantic_search": semantic_candidates,
                    "graph_search": graph_candidates,
                },
            })

    await db.dispose()

    EVAL_QUERIES_FILE.write_text(json.dumps(entries, indent=2) + "\n")
    total_cands = sum(
        len(e["candidates"]["text_search"])
        + len(e["candidates"]["semantic_search"])
        + len(e["candidates"]["graph_search"])
        for e in entries
    )
    print(f"\nWrote {EVAL_QUERIES_FILE} ({len(entries)} queries, {total_cands} total candidates)")
    print("Edit expected_ids in the JSON file, then run the eval.")


# ---------------------------------------------------------------------------
# Model configuration
# ---------------------------------------------------------------------------


@dataclass
class EmbeddingModelConfig:
    """Configuration for one embedding model under evaluation."""

    name: str
    slug: str  # filesystem-safe identifier for cache files
    dimension: int
    provider_type: str = "local"  # "local" (fastembed)


@dataclass
class RerankerModelConfig:
    """Configuration for one cross-encoder/reranker model (fastembed)."""

    name: str


@dataclass
class ComparisonGroup:
    """A named combination of embedding model(s) and reranker to test together."""

    name: str
    doc_embedding: EmbeddingModelConfig
    symbol_embedding: EmbeddingModelConfig
    reranker: RerankerModelConfig


def build_comparison_groups() -> list[ComparisonGroup]:
    """Build comparison groups for embedding + reranker evaluation."""
    bge_base = EmbeddingModelConfig(
        name="BAAI/bge-base-en-v1.5",
        slug="BAAI-bge-base-en-v1.5",
        dimension=768,
        provider_type="local",
    )
    jina_code = EmbeddingModelConfig(
        name="jinaai/jina-embeddings-v2-base-code",
        slug="jinaai-jina-embeddings-v2-base-code",
        dimension=768,
        provider_type="local",
    )
    jina_reranker = RerankerModelConfig(name="jinaai/jina-reranker-v1-turbo-en")
    minilm_12 = RerankerModelConfig(name="Xenova/ms-marco-MiniLM-L-12-v2")

    return [
        ComparisonGroup(
            name="BGE+Jina split",
            doc_embedding=bge_base,
            symbol_embedding=jina_code,
            reranker=jina_reranker,
        ),
        ComparisonGroup(
            name="Control (current)",
            doc_embedding=bge_base,
            symbol_embedding=bge_base,
            reranker=minilm_12,
        ),
    ]


# ---------------------------------------------------------------------------
# Entity text assembly (mirrors server/lifespan.py)
# ---------------------------------------------------------------------------


def assemble_doc_text(entity: Entity) -> str:
    """Reconstruct doc embed text from Entity fields."""
    parts: list[str] = []
    if entity.brief:
        parts.append(f"BRIEF: {entity.brief}")
    if entity.details:
        parts.append(f"DETAILS: {entity.details}")
    if entity.params:
        params_text = " ".join(f"{k}: {v}" for k, v in entity.params.items())
        parts.append(f"PARAMS: {params_text}")
    if entity.returns:
        parts.append(f"RETURNS: {entity.returns}")
    if entity.notes:
        parts.append(f"NOTES: {entity.notes}")
    if entity.rationale:
        parts.append(f"RATIONALE: {entity.rationale}")
    return "\n".join(parts) if parts else entity.name


def assemble_symbol_text(entity: Entity) -> str:
    """Reconstruct symbol embed text from Entity fields."""
    if entity.kind == "function":
        qn = entity.qualified_name
        if qn and "::" in qn:
            sig = entity.signature
            if entity.name and entity.name in sig:
                return sig.replace(entity.name, qn, 1)
            return sig
        return entity.signature
    return entity.qualified_name or entity.name


# ---------------------------------------------------------------------------
# Embedding provider factory (eval-specific)
# ---------------------------------------------------------------------------


def create_eval_embedding_provider(config: EmbeddingModelConfig) -> LocalEmbeddingProvider:
    """Create an embedding provider for evaluation."""
    return LocalEmbeddingProvider(model_name=config.name)


# ---------------------------------------------------------------------------
# Cached embedding computation
# ---------------------------------------------------------------------------


def get_or_compute_embeddings(
    model_config: EmbeddingModelConfig,
    view_name: str,
    entity_ids: list[str],
    texts_by_id: dict[str, str],
    artifacts_path: Path,
) -> dict[str, list[float]]:
    """Load embeddings from cache or compute and cache them.

    Cache file: artifacts/embed_cache_{slug}_{dim}_{view}.pkl
    """
    cached = load_embedding_cache(artifacts_path, model_config.slug, model_config.dimension, view_name)

    if cached is not None:
        current_keys = set(entity_ids)
        cached_keys = set(cached.keys())
        missing = current_keys - cached_keys
        if not missing:
            print(f"  Cache hit: {model_config.slug}/{view_name} ({len(cached)} vectors)")
            stale = cached_keys - current_keys
            if stale:
                for k in stale:
                    del cached[k]
                save_embedding_cache(cached, artifacts_path, model_config.slug, model_config.dimension, view_name)
            return cached  # type: ignore[return-value]
        print(
            f"  Cache partial: {model_config.slug}/{view_name}"
            f" -- {len(missing)} missing, {len(cached_keys & current_keys)} cached"
        )
    else:
        missing = set(entity_ids)
        cached = {}

    provider = create_eval_embedding_provider(model_config)
    missing_list = sorted(missing)
    missing_texts = [texts_by_id[eid] for eid in missing_list]
    batch_size = provider.max_batch_size

    all_vectors: list[list[float]] = []
    for i in tqdm(
        range(0, len(missing_texts), batch_size),
        desc=f"  Embed {model_config.slug}/{view_name}",
        unit="batch",
    ):
        batch = missing_texts[i : i + batch_size]
        all_vectors.extend(provider.embed_batch(batch))

    for key, vec in zip(missing_list, all_vectors, strict=True):
        cached[key] = vec

    save_embedding_cache(cached, artifacts_path, model_config.slug, model_config.dimension, view_name)
    print(f"  Cached {len(missing)} new vectors for {model_config.slug}/{view_name}")
    return cached  # type: ignore[return-value]


# ---------------------------------------------------------------------------
# Cosine similarity ranking
# ---------------------------------------------------------------------------


def cosine_rank(
    query_vec: np.ndarray[Any, np.dtype[np.floating[Any]]],
    corpus_vecs: np.ndarray[Any, np.dtype[np.floating[Any]]],
    corpus_ids: list[str],
) -> list[tuple[str, float]]:
    """Rank corpus vectors by cosine similarity to query. Returns (entity_id, score) desc."""
    q_norm = query_vec / (np.linalg.norm(query_vec) + 1e-10)
    c_norms = np.linalg.norm(corpus_vecs, axis=1, keepdims=True) + 1e-10
    c_normed = corpus_vecs / c_norms
    scores = c_normed @ q_norm
    ranked_indices = np.argsort(scores)[::-1]
    return [(corpus_ids[int(i)], float(scores[int(i)])) for i in ranked_indices]


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------


@dataclass
class EmbeddingResult:
    """Result of one embedding eval query."""

    query: str
    category: str
    view: str
    model_slug: str
    rank: int | None  # rank of first expected entity (1-based), None if not found
    reciprocal_rank: float
    recall_at_10: float
    recall_at_20: float


@dataclass
class RerankerResult:
    """Result of one reranker eval query."""

    query: str
    category: str
    model_name: str
    rank_before: int | None
    rank_after: int | None
    reciprocal_rank: float
    latency_ms: float
    max_ce_score: float = 0.0  # max winning CE score — useful for NEG queries


@dataclass
class EvalReport:
    """Aggregated evaluation report for one comparison group."""

    group_name: str
    embedding_results: list[EmbeddingResult] = field(default_factory=list)
    reranker_results: list[RerankerResult] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Embedding evaluation
# ---------------------------------------------------------------------------

# Provider cache: avoid re-loading the same model multiple times across groups
_provider_cache: dict[str, LocalEmbeddingProvider] = {}


def _get_provider(config: EmbeddingModelConfig) -> LocalEmbeddingProvider:
    """Get or create a cached embedding provider."""
    key = config.name
    if key not in _provider_cache:
        _provider_cache[key] = create_eval_embedding_provider(config)
    return _provider_cache[key]


def evaluate_embeddings(
    group: ComparisonGroup,
    entities: list[Entity],
    artifacts_path: Path,
    eval_queries: list[EvalQuery] | None = None,
) -> list[EmbeddingResult]:
    """Evaluate embedding recall for one comparison group."""
    queries = eval_queries or QUERY_DEFS
    print(f"\n{'=' * 70}")
    print(f"Embedding Eval: {group.name}")
    print(f"  doc model:    {group.doc_embedding.name}")
    print(f"  symbol model: {group.symbol_embedding.name}")
    print(f"{'=' * 70}")

    entity_ids = [e.entity_id for e in entities]
    doc_texts = {e.entity_id: assemble_doc_text(e) for e in entities}
    sym_texts = {e.entity_id: assemble_symbol_text(e) for e in entities}

    # Get/compute corpus embeddings (cached)
    doc_embeddings = get_or_compute_embeddings(
        group.doc_embedding, "doc", entity_ids, doc_texts, artifacts_path,
    )
    sym_embeddings = get_or_compute_embeddings(
        group.symbol_embedding, "symbol", entity_ids, sym_texts, artifacts_path,
    )

    # Build numpy matrices (aligned by entity_ids order)
    doc_matrix = np.array([doc_embeddings[eid] for eid in entity_ids])
    sym_matrix = np.array([sym_embeddings[eid] for eid in entity_ids])

    # Get embedding providers for query embedding
    doc_provider = _get_provider(group.doc_embedding)
    sym_provider = _get_provider(group.symbol_embedding)

    results: list[EmbeddingResult] = []

    for eq in queries:
        views_to_test: list[str] = []
        if eq.view in ("doc", "both"):
            views_to_test.append("doc")
        if eq.view in ("symbol", "both"):
            views_to_test.append("symbol")

        for view in views_to_test:
            if view == "doc":
                q_vec = np.array(doc_provider.embed(eq.query))
                ranked = cosine_rank(q_vec, doc_matrix, entity_ids)
                slug = group.doc_embedding.slug
            else:
                q_vec = np.array(sym_provider.embed(eq.query))
                ranked = cosine_rank(q_vec, sym_matrix, entity_ids)
                slug = group.symbol_embedding.slug

            ranked_ids = [r[0] for r in ranked]
            expected_set = set(eq.expected_ids)

            best_rank: int | None = None
            if expected_set:
                for i, eid in enumerate(ranked_ids):
                    if eid in expected_set:
                        best_rank = i + 1
                        break

            if expected_set:
                top_10_set = set(ranked_ids[:10])
                top_20_set = set(ranked_ids[:20])
                recall_10 = len(expected_set & top_10_set) / len(expected_set)
                recall_20 = len(expected_set & top_20_set) / len(expected_set)
            else:
                recall_10 = recall_20 = 0.0

            rr = 1.0 / best_rank if best_rank is not None else 0.0

            results.append(EmbeddingResult(
                query=eq.query,
                category=eq.category,
                view=view,
                model_slug=slug,
                rank=best_rank,
                reciprocal_rank=rr,
                recall_at_10=recall_10,
                recall_at_20=recall_20,
            ))

    return results


# ---------------------------------------------------------------------------
# Reranker evaluation
# ---------------------------------------------------------------------------

# Reranker cache
_reranker_cache: dict[str, CrossEncoderProvider] = {}


def _get_fastembed_reranker(model_name: str) -> CrossEncoderProvider:
    """Get or create a cached fastembed reranker."""
    if model_name not in _reranker_cache:
        _reranker_cache[model_name] = CrossEncoderProvider(model_name=model_name)
    return _reranker_cache[model_name]


def generate_reranker_candidates(
    ref_doc_embedding: EmbeddingModelConfig,
    ref_sym_embedding: EmbeddingModelConfig,
    entities: list[Entity],
    artifacts_path: Path,
    eval_queries: list[EvalQuery] | None = None,
    per_view_n: int = 50,
) -> dict[str, list[str]]:
    """Generate a fixed candidate pool for reranker evaluation.

    Takes top per_view_n from each embedding view independently, then deduplicates.
    Returns a dict mapping query text -> list of candidate entity IDs.
    The same pool is used for all rerankers to ensure fair comparison.
    """
    queries = eval_queries or QUERY_DEFS
    entity_ids = [e.entity_id for e in entities]
    doc_texts = {e.entity_id: assemble_doc_text(e) for e in entities}
    sym_texts = {e.entity_id: assemble_symbol_text(e) for e in entities}

    doc_embeddings = get_or_compute_embeddings(
        ref_doc_embedding, "doc", entity_ids, doc_texts, artifacts_path,
    )
    sym_embeddings = get_or_compute_embeddings(
        ref_sym_embedding, "symbol", entity_ids, sym_texts, artifacts_path,
    )

    doc_matrix = np.array([doc_embeddings[eid] for eid in entity_ids])
    sym_matrix = np.array([sym_embeddings[eid] for eid in entity_ids])

    doc_provider = _get_provider(ref_doc_embedding)
    sym_provider = _get_provider(ref_sym_embedding)

    candidates: dict[str, list[str]] = {}
    for eq in queries:
        doc_q_vec = np.array(doc_provider.embed(eq.query))
        sym_q_vec = np.array(sym_provider.embed(eq.query))
        doc_ranked = cosine_rank(doc_q_vec, doc_matrix, entity_ids)
        sym_ranked = cosine_rank(sym_q_vec, sym_matrix, entity_ids)

        # Take top-N from each view independently, then deduplicate
        doc_top = [eid for eid, _ in doc_ranked[:per_view_n]]
        sym_top = [eid for eid, _ in sym_ranked[:per_view_n]]
        seen: set[str] = set()
        merged: list[str] = []
        for eid in doc_top + sym_top:
            if eid not in seen:
                seen.add(eid)
                merged.append(eid)
        candidates[eq.query] = merged

    return candidates


def evaluate_reranker(
    reranker_config: RerankerModelConfig,
    entities: list[Entity],
    candidate_pool: dict[str, list[str]],
    eval_queries: list[EvalQuery] | None = None,
) -> list[RerankerResult]:
    """Evaluate reranker quality on a fixed candidate pool.

    The candidate pool is shared across all rerankers for fair comparison.
    Candidates come from the union of top-N doc + top-N symbol embedding results.
    """
    queries = eval_queries or QUERY_DEFS
    print(f"\n{'=' * 70}")
    print(f"Reranker Eval: {reranker_config.name}")
    print(f"{'=' * 70}")

    doc_texts = {e.entity_id: assemble_doc_text(e) for e in entities}
    sym_texts = {e.entity_id: assemble_symbol_text(e) for e in entities}

    reranker = _get_fastembed_reranker(reranker_config.name)

    results: list[RerankerResult] = []

    for eq in tqdm(queries, desc=f"  Rerank {reranker_config.name}", unit="query"):
        candidate_ids = candidate_pool[eq.query]
        expected_set = set(eq.expected_ids)

        # Pre-rerank rank (position in the candidate list)
        rank_before: int | None = None
        if expected_set:
            for i, eid in enumerate(candidate_ids):
                if eid in expected_set:
                    rank_before = i + 1
                    break

        # Cross-encoder scores from both views
        doc_texts_for_ce = [doc_texts[eid] for eid in candidate_ids]
        sym_texts_for_ce = [sym_texts[eid] for eid in candidate_ids]

        start = time.monotonic()

        doc_scores = reranker.rerank(eq.query, doc_texts_for_ce)
        sym_scores = reranker.rerank(eq.query, sym_texts_for_ce)

        elapsed_ms = (time.monotonic() - start) * 1000

        # Per-candidate: winning = max(doc_ce, sym_ce), losing = min(doc_ce, sym_ce)
        winning_scores = [max(d, s) for d, s in zip(doc_scores, sym_scores, strict=True)]
        losing_scores = [min(d, s) for d, s in zip(doc_scores, sym_scores, strict=True)]

        # Sort by (winning_score, losing_score) descending — matches design Stage 7
        reranked_indices = sorted(
            range(len(winning_scores)),
            key=lambda j: (winning_scores[j], losing_scores[j]),
            reverse=True,
        )
        reranked_ids = [candidate_ids[j] for j in reranked_indices]

        rank_after: int | None = None
        if expected_set:
            for i, eid in enumerate(reranked_ids):
                if eid in expected_set:
                    rank_after = i + 1
                    break

        rr = 1.0 / rank_after if rank_after is not None else 0.0
        max_score = max(winning_scores) if winning_scores else 0.0

        results.append(RerankerResult(
            query=eq.query,
            category=eq.category,
            model_name=reranker_config.name,
            rank_before=rank_before,
            rank_after=rank_after,
            reciprocal_rank=rr,
            latency_ms=elapsed_ms,
            max_ce_score=max_score,
        ))

    return results


# ---------------------------------------------------------------------------
# Report printing
# ---------------------------------------------------------------------------


def print_embedding_report(report: EvalReport) -> None:
    """Print embedding evaluation results."""
    if not report.embedding_results:
        return

    print(f"\n{'=' * 70}")
    print(f"EMBEDDING RESULTS: {report.group_name}")
    print(f"{'=' * 70}")

    header = f"{'Query':<55s} {'Cat':4s} {'View':7s} {'Model':<30s} {'Rank':>5s} {'RR':>5s} {'R@10':>5s} {'R@20':>5s}"
    print(f"\n{header}")
    print("-" * len(header))
    for r in report.embedding_results:
        rank_str = str(r.rank) if r.rank is not None else "miss"
        print(
            f"{r.query[:54]:<55s} {r.category:4s} {r.view:7s} {r.model_slug[:29]:<30s} "
            f"{rank_str:>5s} {r.reciprocal_rank:5.3f} {r.recall_at_10:5.2f} {r.recall_at_20:5.2f}"
        )

    # Aggregate per-query (best view for both-view queries, avoiding double-count)
    # Exclude NEG queries from main metrics
    print("\n--- Aggregate by category (per-query, best view) ---")
    query_best: dict[str, EmbeddingResult] = {}
    for r in report.embedding_results:
        if r.category == "NEG":
            continue
        key = r.query
        if key not in query_best or r.reciprocal_rank > query_best[key].reciprocal_rank:
            query_best[key] = r
    deduped = list(query_best.values())

    categories = sorted({r.category for r in deduped})
    for cat in categories:
        cat_results = [r for r in deduped if r.category == cat]
        n = len(cat_results)
        mrr = sum(r.reciprocal_rank for r in cat_results) / n
        avg_r10 = sum(r.recall_at_10 for r in cat_results) / n
        avg_r20 = sum(r.recall_at_20 for r in cat_results) / n
        print(f"  {cat}: MRR={mrr:.3f}  R@10={avg_r10:.2f}  R@20={avg_r20:.2f}  (n={n})")

    n_all = len(deduped)
    overall_mrr = sum(r.reciprocal_rank for r in deduped) / n_all
    overall_r10 = sum(r.recall_at_10 for r in deduped) / n_all
    overall_r20 = sum(r.recall_at_20 for r in deduped) / n_all
    print(f"  OVERALL: MRR={overall_mrr:.3f}  R@10={overall_r10:.2f}  R@20={overall_r20:.2f}  (n={n_all})")

    # Report NEG queries separately
    neg_results = [r for r in report.embedding_results if r.category == "NEG"]
    if neg_results:
        print(f"  NEG: {len(neg_results)} negative queries (not included in metrics above)")


def print_reranker_report(report: EvalReport) -> None:
    """Print reranker evaluation results."""
    if not report.reranker_results:
        return

    print(f"\n{'=' * 70}")
    print(f"RERANKER RESULTS: {report.group_name}")
    print(f"{'=' * 70}")

    header = f"{'Query':<55s} {'Cat':4s} {'Before':>7s} {'After':>6s} {'RR':>5s} {'MaxCE':>6s} {'ms':>8s}"
    print(f"\n{header}")
    print("-" * len(header))
    for r in report.reranker_results:
        before_str = str(r.rank_before) if r.rank_before is not None else "n/a"
        after_str = str(r.rank_after) if r.rank_after is not None else "n/a"
        print(
            f"{r.query[:54]:<55s} {r.category:4s} {before_str:>7s} {after_str:>6s} "
            f"{r.reciprocal_rank:5.3f} {r.max_ce_score:6.2f} {r.latency_ms:8.1f}"
        )

    # Separate positive and negative queries
    pos_results = [r for r in report.reranker_results if r.category != "NEG"]
    neg_results = [r for r in report.reranker_results if r.category == "NEG"]

    if pos_results:
        n = len(pos_results)
        mrr = sum(r.reciprocal_rank for r in pos_results) / n
        avg_latency = sum(r.latency_ms for r in pos_results) / n
        promoted = sum(
            1 for r in pos_results
            if r.rank_before is not None and r.rank_after is not None and r.rank_after < r.rank_before
        )
        print(f"\n  Positive: MRR={mrr:.3f}  avg_latency={avg_latency:.0f}ms  promoted={promoted}/{n}")

    if neg_results:
        avg_max_ce = sum(r.max_ce_score for r in neg_results) / len(neg_results)
        max_max_ce = max(r.max_ce_score for r in neg_results)
        print(f"  Negative: avg_max_CE={avg_max_ce:.3f}  worst_max_CE={max_max_ce:.3f}  (n={len(neg_results)})")
        print(f"            (lower = better noise rejection)")


def print_comparison_summary(reports: list[EvalReport]) -> None:
    """Print side-by-side comparison across all groups."""
    print(f"\n{'=' * 70}")
    print("COMPARISON SUMMARY")
    print(f"{'=' * 70}")

    header = f"{'Group':<25s} {'Embed MRR':>10s} {'R@10':>6s} {'Rerank MRR':>11s} {'Latency':>8s}"
    print(f"\n{header}")
    print("-" * len(header))
    for report in reports:
        embed_mrr = embed_r10 = 0.0
        if report.embedding_results:
            query_best: dict[str, EmbeddingResult] = {}
            for r in report.embedding_results:
                if r.category == "NEG":
                    continue
                if r.query not in query_best or r.reciprocal_rank > query_best[r.query].reciprocal_rank:
                    query_best[r.query] = r
            deduped = list(query_best.values())
            n_e = len(deduped)
            embed_mrr = sum(r.reciprocal_rank for r in deduped) / n_e if n_e else 0.0
            embed_r10 = sum(r.recall_at_10 for r in deduped) / n_e if n_e else 0.0

        rerank_mrr = 0.0
        avg_lat = 0.0
        if report.reranker_results:
            pos_reranker = [r for r in report.reranker_results if r.category != "NEG"]
            n_r = len(pos_reranker)
            rerank_mrr = sum(r.reciprocal_rank for r in pos_reranker) / n_r if n_r else 0.0
            avg_lat = sum(r.latency_ms for r in pos_reranker) / n_r if n_r else 0.0

        lat_str = f"{avg_lat:.0f}ms" if report.reranker_results else "n/a"
        print(f"{report.group_name:<25s} {embed_mrr:10.3f} {embed_r10:6.2f} {rerank_mrr:11.3f} {lat_str:>8s}")


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------


async def load_entities() -> list[Entity]:
    """Load all entities from the database."""
    config = ServerConfig()
    db = DatabaseManager(config)
    async with db.session() as session:
        result = await session.execute(select(Entity))
        entities = list(result.scalars().all())
    await db.dispose()
    print(f"Loaded {len(entities)} entities from database")
    return entities


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    """Run model evaluation."""
    parser = argparse.ArgumentParser(description="Model evaluation for multi-view search (E-01/E-02)")
    parser.add_argument("--generate", action="store_true", help="Generate eval_queries.json with candidates")
    parser.add_argument("--embedding-only", action="store_true", help="Run embedding eval only")
    parser.add_argument("--reranker-only", action="store_true", help="Run reranker eval only")
    parser.add_argument(
        "--groups", nargs="+", type=int,
        help="Which comparison groups to run (1-indexed). Default: all.",
    )
    args = parser.parse_args()

    if args.generate:
        asyncio.run(generate_eval_file())
        return

    # Load expected_ids from JSON
    eval_queries = load_eval_queries()

    run_embeddings = not args.reranker_only
    run_reranker = not args.embedding_only

    entities = asyncio.run(load_entities())

    entity_id_set = {e.entity_id for e in entities}
    for eq in eval_queries:
        for eid in eq.expected_ids:
            assert eid in entity_id_set, f"Unknown entity_id: {eid!r} (query: {eq.query!r})"
    n_pos = sum(1 for eq in eval_queries if eq.category != "NEG")
    n_neg = sum(1 for eq in eval_queries if eq.category == "NEG")
    n_labeled = sum(1 for eq in eval_queries if eq.expected_ids or eq.category == "NEG")
    print(f"Loaded {len(eval_queries)} eval queries ({n_pos} positive, {n_neg} negative, {n_labeled} with labels)")
    if n_labeled < len(eval_queries):
        unlabeled = [eq.query for eq in eval_queries if not eq.expected_ids and eq.category != "NEG"]
        print(f"  WARNING: {len(unlabeled)} queries have no expected_ids (will score 0): {unlabeled[:5]}...")

    artifacts_path = Path(__file__).resolve().parent.parent.parent / "artifacts"

    all_groups = build_comparison_groups()
    groups = [all_groups[i - 1] for i in args.groups] if args.groups else all_groups

    reports: list[EvalReport] = []

    # --- Embedding evaluation (per group — different models) ---
    if run_embeddings:
        for group in groups:
            report = EvalReport(group_name=group.name)
            report.embedding_results = evaluate_embeddings(group, entities, artifacts_path, eval_queries)
            print_embedding_report(report)
            reports.append(report)

    # --- Reranker evaluation (fixed candidate pool for fair comparison) ---
    if run_reranker:
        # Generate candidates once from reference embeddings (control group: BGE both views)
        ref_group = all_groups[-1]  # Control group
        print(f"\nGenerating reference candidate pool from {ref_group.doc_embedding.name}...")
        candidate_pool = generate_reranker_candidates(
            ref_group.doc_embedding, ref_group.symbol_embedding,
            entities, artifacts_path, eval_queries,
        )
        pool_sizes = [len(v) for v in candidate_pool.values()]
        print(f"  Candidate pool: {len(candidate_pool)} queries, {min(pool_sizes)}-{max(pool_sizes)} candidates each")

        # Test each group's reranker on the same candidates
        reranker_configs = [g.reranker for g in groups]
        # Deduplicate rerankers (groups may share the same one)
        seen_rerankers: set[str] = set()
        unique_rerankers: list[RerankerModelConfig] = []
        for rc in reranker_configs:
            if rc.name not in seen_rerankers:
                seen_rerankers.add(rc.name)
                unique_rerankers.append(rc)

        for rc in unique_rerankers:
            reranker_report = EvalReport(group_name=rc.name)
            reranker_report.reranker_results = evaluate_reranker(rc, entities, candidate_pool, eval_queries)
            print_reranker_report(reranker_report)
            # Attach reranker results to existing reports or create new ones
            matched = False
            for report in reports:
                if any(g.reranker.name == rc.name and g.name == report.group_name for g in groups):
                    report.reranker_results = reranker_report.reranker_results
                    matched = True
                    break
            if not matched:
                reports.append(reranker_report)

    if len(reports) > 1:
        print_comparison_summary(reports)


if __name__ == "__main__":
    main()
