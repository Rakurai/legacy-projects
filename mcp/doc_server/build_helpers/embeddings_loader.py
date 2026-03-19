"""
Embeddings Loader - Load, generate, and attach embedding vectors.

Supports config-aware artifact naming (embed_cache_{model}_{dim}.pkl).
Can generate embeddings on demand via an EmbeddingProvider when no artifact exists.

Generation iterates merged entities directly, using Document.to_doxygen() for text.
Doc-less entities get minimal Doxygen-formatted text from kind + name + signature + file_path.
"""

import pickle
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
    merged_entities: list[MergedEntity],
) -> dict[str, list[float]]:
    """Generate embeddings for all entities — doc-rich via to_doxygen(), doc-less via minimal text.

    Entity IDs are already computed (deterministic) on the merged entities.
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
