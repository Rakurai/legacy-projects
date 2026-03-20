"""
Embeddings Loader - Load, generate, and attach embedding vectors.

Supports config-aware artifact naming (embed_cache_{model}_{dim}.pkl).
Can generate embeddings on demand via an EmbeddingProvider when no artifact exists.

Generation iterates merged entities directly, using Document.to_doxygen() for text.
Doc-less entities get minimal Doxygen-formatted text from kind + name + signature + file_path.
"""

import pickle
import re
import tempfile
from pathlib import Path

from build_helpers.entity_processor import MergedEntity
from server.config import ServerConfig
from server.embedding import EmbeddingProvider
from server.logging_config import log

# Doxygen tag mapping — extends Document.to_doxygen() tag_map with structural compound tags
_KIND_TAG_MAP: dict[str, str] = {
    "function": "@fn",
    "variable": "@var",
    "class": "@class",
    "struct": "@struct",
    "file": "@file",
    "dir": "@dir",
    "namespace": "@namespace",
    "define": "@def",
    "group": "@defgroup",
    "enum": "@enum",
    "typedef": "@typedef",
    "union": "@union",
}


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


def build_minimal_embed_text(merged: MergedEntity) -> str | None:
    """Build a minimal Doxygen-formatted embedding text for a doc-less entity.

    Returns None when name, signature, and kind are all empty — nothing
    meaningful to embed.
    """
    kind = merged.entity.kind or ""
    name = merged.entity.name or ""
    sig = merged.signature or ""
    file_path = merged.entity.body.fn if merged.entity.body else merged.entity.decl.fn if merged.entity.decl else None

    if not kind and not name and not sig:
        return None

    tag = _KIND_TAG_MAP.get(kind, "@fn")
    display = sig if sig else name

    lines = ["/**"]
    lines.append(f" * {tag} {display}")

    if file_path:
        lines.append(" *")
        lines.append(f" * @file {file_path}")

    lines.append(" */")
    return "\n".join(lines)


def get_embed_cache_path(artifacts_dir: Path, config: ServerConfig) -> Path:
    """Return the full path to the embedding artifact for the current config."""
    return artifacts_dir / config.embed_cache_filename


def load_embeddings(
    artifacts_dir: Path,
    config: ServerConfig,
    id_map: dict[str, str],
) -> dict[str, list[float]] | None:
    """Load entity embeddings from cache file, re-keying old IDs to deterministic IDs.

    This is a compatibility wrapper around load_embedding_cache() that handles
    id_map translation for entity embeddings.

    Returns:
        Dict mapping new deterministic entity_id → embedding vector, or None
        if the file doesn't exist.

    Raises:
        RuntimeError: If the artifact exists but is corrupt (from legacy code path).
    """
    # Use new generalized cache loader with type="entity"
    raw_embeddings = load_embedding_cache(
        artifacts_path=artifacts_dir,
        model_slug=config.embedding_model_slug,
        dimension=config.embedding_dimension,
        embedding_type="entity",
    )

    if raw_embeddings is None:
        return None

    # Re-key old entity_id keys to deterministic IDs via id_map
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

    log.info("Embeddings re-keyed", embedding_count=len(embeddings))
    return embeddings


def generate_embeddings(
    artifacts_dir: Path,
    provider: EmbeddingProvider,
    config: ServerConfig,
    merged_entities: list[MergedEntity],
) -> dict[str, list[float]]:
    """Generate entity embeddings — doc-rich via to_doxygen(), doc-less via minimal text.

    Entity IDs are already computed (deterministic) on the merged entities.
    Saves to cache with type="entity".
    """
    log.info("Generating embeddings from merged entities")

    # Doc-rich entities: full Doxygen text
    docs_to_embed = [(m.entity_id, m.doc.to_doxygen()) for m in merged_entities if m.doc is not None]

    # Doc-less entities: minimal Doxygen text
    minimal_to_embed: list[tuple[str, str]] = []
    for m in merged_entities:
        if m.doc is None:
            text = build_minimal_embed_text(m)
            if text is not None:
                minimal_to_embed.append((m.entity_id, text))

    all_to_embed = docs_to_embed + minimal_to_embed
    entity_ids = [eid for eid, _ in all_to_embed]
    texts = [text for _, text in all_to_embed]

    no_embed = len(merged_entities) - len(all_to_embed)
    coverage = round(100.0 * len(all_to_embed) / len(merged_entities), 1) if merged_entities else 0.0
    log.info(
        "Embedding generation summary",
        doc_embeds=len(docs_to_embed),
        minimal_embeds=len(minimal_to_embed),
        no_embed=no_embed,
        coverage=f"{coverage}%",
    )

    if not texts:
        log.warning("No docs found in entity set; no embeddings generated")
        return {}

    vectors = provider.embed_documents_sync(texts)

    embeddings: dict[str, list[float]] = {}
    for eid, vec in zip(entity_ids, vectors, strict=True):
        embeddings[eid] = vec

    log.info("Embeddings generated", count=len(embeddings))

    # Save to cache using generalized cache function with type="entity"
    from typing import cast

    save_embedding_cache(
        embeddings=cast(dict[str | tuple[str, ...], list[float]], embeddings),
        artifacts_path=artifacts_dir,
        model_slug=config.embedding_model_slug,
        dimension=config.embedding_dimension,
        embedding_type="entity",
    )

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
