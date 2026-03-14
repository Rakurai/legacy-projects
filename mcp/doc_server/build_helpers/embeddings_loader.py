"""
Embeddings Loader - Unpickle embeddings_cache.pkl and map to entity IDs.

The embeddings cache is a pickled dict mapping entity keys to 4096-dim embeddings.
Keys are (compound_id, member_id) tuples or compound_id strings.
"""

import pickle
from pathlib import Path
from typing import Any

from build_helpers.entity_processor import MergedEntity
from server.logging_config import log


def load_embeddings(artifacts_dir: Path) -> dict[str, list[float]]:
    """
    Load embeddings from embeddings_cache.pkl.

    Returns dict mapping entity_id (string) to 4096-dim embedding vector.

    Args:
        artifacts_dir: Path to artifacts directory

    Returns:
        Dict mapping entity_id → embedding vector

    Raises:
        FileNotFoundError: If embeddings_cache.pkl doesn't exist
    """
    embeddings_path = artifacts_dir / "embeddings_cache.pkl"
    log.info("Loading embeddings cache", path=str(embeddings_path))

    with embeddings_path.open("rb") as f:
        raw_embeddings = pickle.load(f)

    # Convert keys to entity_id strings
    # Keys may be tuples (compound_id, member_id) or strings (compound_id)
    embeddings: dict[str, list[float]] = {}

    for key, embedding in raw_embeddings.items():
        if isinstance(key, tuple):
            # (compound_id, member_id) → "compound_id_member_id"
            entity_id = f"{key[0]}_{key[1]}"
        else:
            # compound_id → "compound_id"
            entity_id = str(key)

        embeddings[entity_id] = embedding

    log.info("Embeddings loaded", embedding_count=len(embeddings))
    return embeddings


def attach_embeddings(
    merged_entities: list[MergedEntity],
    embeddings: dict[str, list[float]]
) -> None:
    """
    Attach embeddings to merged entities.

    Matches by entity_id. Updates merged_entity in place (adds embedding attribute).

    Args:
        merged_entities: List of merged entity records
        embeddings: Dict mapping entity_id → embedding vector
    """
    log.info("Attaching embeddings to entities")

    matched_count = 0

    for merged in merged_entities:
        entity_id = merged.entity_id
        if entity_id in embeddings:
            # Add embedding as attribute (will be stored in Entity model)
            # Store as Python list (pgvector handles conversion)
            merged.embedding = embeddings[entity_id]
            matched_count += 1
        else:
            merged.embedding = None

    log.info(
        "Embeddings attached",
        matched=matched_count,
        unmatched=len(merged_entities) - matched_count
    )
