"""
Embeddings Loader - Load, generate, and attach embedding vectors.

Supports config-aware artifact naming (embed_cache_{model}_{dim}.pkl).
Can generate embeddings on demand via an EmbeddingProvider when no artifact exists.

Generation iterates doc_db.json entries directly, using signature_map_data and
id_map to convert doc_db keys to deterministic entity_ids.
"""

import json
import pickle
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, Any

from build_helpers.embed_text import build_embed_text
from build_helpers.entity_processor import MergedEntity
from server.logging_config import log

if TYPE_CHECKING:
    from server.config import ServerConfig
    from server.embedding import EmbeddingProvider


def get_embed_cache_path(artifacts_dir: Path, config: ServerConfig) -> Path:
    """Return the full path to the embedding artifact for the current config."""
    return artifacts_dir / config.embed_cache_filename


def load_embeddings(
    artifacts_dir: Path,
    config: ServerConfig,
    id_map: dict[str, str],
) -> dict[str, list[float]] | None:
    """Load embeddings from a config-derived artifact file.

    Re-keys old entity_id keys to deterministic IDs via id_map.

    Returns:
        Dict mapping new deterministic entity_id → embedding vector, or None
        if the file doesn't exist.

    Raises:
        RuntimeError: If the artifact exists but is corrupt.
    """
    embeddings_path = get_embed_cache_path(artifacts_dir, config)

    if not embeddings_path.exists():
        log.info("No embedding artifact found", path=str(embeddings_path))
        return None

    log.info("Loading embeddings cache", path=str(embeddings_path))

    try:
        with embeddings_path.open("rb") as f:
            raw_embeddings = pickle.load(f)
    except (pickle.UnpicklingError, EOFError) as e:
        raise RuntimeError(
            f"Corrupt embedding artifact at {embeddings_path}. "
            f"Delete the file and re-run the build to regenerate. Error: {e}"
        ) from e

    new_id_set = set(id_map.values())
    embeddings: dict[str, list[float]] = {}
    for key, embedding in raw_embeddings.items():
        key_str = str(key)
        # Try translating as old ID
        new_id = id_map.get(key_str)
        if new_id:
            embeddings[new_id] = embedding
        elif key_str in new_id_set:
            # Already a new-format key (from a previous build with new code)
            embeddings[key_str] = embedding

    log.info("Embeddings loaded", embedding_count=len(embeddings))
    return embeddings


def generate_embeddings(
    artifacts_dir: Path,
    provider: EmbeddingProvider,
    config: ServerConfig,
    signature_map_data: dict[str, str],
    id_map: dict[str, str],
) -> dict[str, list[float]]:
    """Generate embeddings for every doc_db.json entry, save artifact.

    Uses signature_map_data to find old entity_id per doc_db key, then
    id_map to translate to deterministic entity_id.

    Args:
        artifacts_dir: Directory containing doc_db.json and for the artifact file.
        provider: An active EmbeddingProvider instance.
        config: Server config (for filename derivation).
        signature_map_data: Raw signature_map.json dict.
        id_map: old Doxygen entity_id → new deterministic entity_id.

    Returns:
        Dict mapping deterministic entity_id → embedding vector.
    """
    doc_db_path = config.artifacts_path / "doc_db.json"
    log.info("Loading doc_db.json for embedding generation", path=str(doc_db_path))

    with doc_db_path.open("r", encoding="utf-8") as f:
        raw_docs: dict[str, dict[str, Any]] = json.load(f)

    log.info("Generating embeddings from doc_db", doc_count=len(raw_docs))

    entity_ids: list[str] = []
    texts: list[str] = []

    for key_str, doc in raw_docs.items():
        old_eid = signature_map_data.get(key_str)
        if old_eid is None:
            continue
        new_eid = id_map.get(old_eid)
        if new_eid is None:
            continue
        text = build_embed_text(doc)
        entity_ids.append(new_eid)
        texts.append(text)

    log.info("Docs to embed", count=len(texts))

    if not texts:
        log.warning("No docs found in doc_db; no embeddings generated")
        return {}

    vectors = provider.embed_documents_sync(texts)

    embeddings: dict[str, list[float]] = {}
    for eid, vec in zip(entity_ids, vectors, strict=True):
        embeddings[eid] = vec

    log.info("Embeddings generated", count=len(embeddings))

    # Save artifact (atomic write via temp file + rename)
    artifact_path = get_embed_cache_path(artifacts_dir, config)
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    fd, tmp_path = tempfile.mkstemp(dir=str(artifacts_dir), suffix=".pkl.tmp")
    try:
        with open(fd, "wb") as f:
            pickle.dump(embeddings, f, protocol=pickle.HIGHEST_PROTOCOL)
        Path(tmp_path).rename(artifact_path)
        log.info("Embedding artifact saved", path=str(artifact_path))
    except Exception:
        Path(tmp_path).unlink(missing_ok=True)
        raise

    return embeddings


def attach_embeddings(
    merged_entities: list[MergedEntity],
    embeddings: dict[str, list[float]],
) -> None:
    """Attach embeddings to merged entities.

    Matches by entity_id. Updates merged_entity in place (adds embedding attribute).
    """
    log.info("Attaching embeddings to entities")

    matched_count = 0
    for merged in merged_entities:
        entity_id = merged.entity_id
        if entity_id in embeddings:
            merged.embedding = embeddings[entity_id]
            matched_count += 1
        else:
            merged.embedding = None

    log.info(
        "Embeddings attached",
        matched=matched_count,
        unmatched=len(merged_entities) - matched_count,
    )
