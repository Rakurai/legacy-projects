"""
Embeddings Loader - Schema-agnostic embedding cache operations.

Supports type-specific cache files: embed_cache_{model}_{dim}_{type}.pkl
Provides incremental cache synchronization: load, add missing keys, prune stale keys, save.
"""

import pickle
import re
import tempfile
from pathlib import Path

from tqdm import tqdm

from server.embedding import EmbeddingProvider
from server.logging_config import log


def _validate_type_identifier(embedding_type: str) -> None:
    """Validate type identifier format (alphanumeric, underscores, hyphens only).

    Args:
        embedding_type: Type identifier to validate

    Raises:
        ValueError: If embedding_type contains invalid characters
    """
    if not re.match(r"^[a-zA-Z0-9_-]+$", embedding_type):
        raise ValueError(
            f"Invalid embedding_type '{embedding_type}': "
            "must contain only alphanumeric characters, underscores, and hyphens"
        )


def save_embedding_cache(
    embeddings: dict[str | tuple[str, ...], list[float]],
    artifacts_path: Path,
    model_slug: str,
    dimension: int,
    embedding_type: str,
) -> None:
    """Save embeddings to type-specific cache file.

    Args:
        embeddings: Dict mapping identifiers to embedding vectors
        artifacts_path: Path to artifacts directory
        model_slug: Embedding model identifier (normalized, lowercase)
        dimension: Vector dimension
        embedding_type: Type identifier string (alphanumeric, underscores, hyphens)

    Raises:
        ValueError: If embedding_type contains invalid characters
        OSError: If cache file cannot be written
        PickleError: If embeddings dict cannot be serialized
    """
    _validate_type_identifier(embedding_type)

    cache_filename = f"embed_cache_{model_slug}_{dimension}_{embedding_type}.pkl"
    cache_path = artifacts_path / cache_filename

    artifacts_path.mkdir(parents=True, exist_ok=True)

    # Atomic write via temp file + rename
    fd, tmp_path = tempfile.mkstemp(dir=str(artifacts_path), suffix=".pkl.tmp")
    try:
        with open(fd, "wb") as f:
            pickle.dump(embeddings, f, protocol=pickle.HIGHEST_PROTOCOL)
        Path(tmp_path).rename(cache_path)
        log.info("Saved embedding cache", type=embedding_type, count=len(embeddings), path=str(cache_path))
    except Exception:
        Path(tmp_path).unlink(missing_ok=True)
        raise


def load_embedding_cache(
    artifacts_path: Path,
    model_slug: str,
    dimension: int,
    embedding_type: str,
) -> dict[str | tuple[str, ...], list[float]] | None:
    """Load embeddings from type-specific cache file.

    Args:
        artifacts_path: Path to artifacts directory
        model_slug: Embedding model identifier (normalized, lowercase)
        dimension: Vector dimension
        embedding_type: Type identifier string

    Returns:
        Cached embeddings if file exists and is valid, None otherwise

    Raises:
        ValueError: If embedding_type contains invalid characters
    """
    _validate_type_identifier(embedding_type)

    cache_filename = f"embed_cache_{model_slug}_{dimension}_{embedding_type}.pkl"
    cache_path = artifacts_path / cache_filename

    if not cache_path.exists():
        # Legacy file detection for entity type
        if embedding_type == "entity":
            legacy_filename = f"embed_cache_{model_slug}_{dimension}.pkl"
            legacy_path = artifacts_path / legacy_filename
            if legacy_path.exists():
                log.warning(
                    "Legacy cache file detected",
                    legacy_path=str(legacy_path),
                    new_path=str(cache_path),
                    message="Rename or delete legacy file to migrate",
                )

        log.info("No cache found", type=embedding_type, model=model_slug, dimension=dimension)
        return None

    try:
        with cache_path.open("rb") as f:
            embeddings: dict[str | tuple[str, ...], list[float]] = pickle.load(f)
        log.info("Loaded embedding cache", type=embedding_type, count=len(embeddings), path=str(cache_path))
        return embeddings
    except (pickle.UnpicklingError, EOFError) as exc:
        log.warning("Cache file corrupted, will regenerate", type=embedding_type, path=str(cache_path), error=str(exc))
        return None


def sync_embeddings_cache(
    artifacts_path: Path,
    model_slug: str,
    dimension: int,
    embedding_type: str,
    current_keys: list[str | tuple[str, ...]],
    texts_by_key: dict[str | tuple[str, ...], str],
    provider: EmbeddingProvider,
) -> dict[str | tuple[str, ...], list[float]]:
    """Synchronize embeddings cache with current data set.

    Loads cached embeddings, generates embeddings for missing keys only,
    prunes stale keys, and saves the updated cache. Fully schema-agnostic.

    Args:
        artifacts_path: Path to artifacts directory
        model_slug: Embedding model identifier
        dimension: Vector dimension
        embedding_type: Type identifier for cache file
        current_keys: List of all keys that should have embeddings
        texts_by_key: Mapping of keys to text strings to embed
        provider: Embedding provider for generating vectors

    Returns:
        Complete embeddings dict with all current_keys populated

    Raises:
        ValueError: If embedding_type contains invalid characters
    """
    cached_embeddings = load_embedding_cache(artifacts_path, model_slug, dimension, embedding_type)

    if cached_embeddings is not None:
        embeddings = cached_embeddings
        cached_count = len(embeddings)
    else:
        embeddings = {}
        cached_count = 0

    current_keys_set = set(current_keys)
    cached_keys_set = set(embeddings.keys())
    missing_keys = current_keys_set - cached_keys_set
    stale_keys = cached_keys_set - current_keys_set

    if missing_keys:
        log.info("Generating embeddings for missing keys", type=embedding_type, count=len(missing_keys))
        missing_keys_list = list(missing_keys)
        missing_texts = [texts_by_key[key] for key in missing_keys_list]
        batch_size = provider.max_batch_size

        all_vectors: list[list[float]] = []
        for i in tqdm(range(0, len(missing_texts), batch_size), desc=f"Embedding ({embedding_type})", unit="batch"):
            batch = missing_texts[i : i + batch_size]
            all_vectors.extend(provider.embed_batch(batch))

        for key, vector in zip(missing_keys_list, all_vectors, strict=True):
            embeddings[key] = vector

    if stale_keys:
        for stale_key in stale_keys:
            del embeddings[stale_key]

    if missing_keys or stale_keys:
        log.info(
            "Cache synchronized",
            type=embedding_type,
            cached=cached_count,
            current=len(current_keys_set),
            added=len(missing_keys),
            pruned=len(stale_keys),
        )
        save_embedding_cache(embeddings, artifacts_path, model_slug, dimension, embedding_type)
    elif cached_count > 0:
        log.info("Cache up to date", type=embedding_type, count=cached_count)

    return embeddings
