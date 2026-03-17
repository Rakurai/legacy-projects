"""
Deterministic entity ID generation for the build pipeline.

Replaces opaque Doxygen IDs with stable, type-prefixed content-hashed IDs
of the form ``{prefix}:{sha256(canonical_key)[:7]}``.

The canonical key is the signature_map tuple ``(compound_id, second_element)``.
The server runtime treats entity_id as an opaque key — only the build
pipeline imports this module.
"""

import ast
import hashlib

from server.logging_config import log

# Prefix mapping: entity kind → short prefix for deterministic IDs.
_KIND_PREFIX: dict[str, str] = {
    "function": "fn",
    "define": "fn",
    "variable": "var",
    "class": "cls",
    "struct": "cls",
    "file": "file",
}

_DEFAULT_PREFIX = "sym"


def kind_to_prefix(kind: str) -> str:
    """Map an entity kind string to its short ID prefix."""
    return _KIND_PREFIX.get(kind, _DEFAULT_PREFIX)


def compute_entity_id(kind: str, compound_id: str, second_element: str) -> str:
    """Compute a deterministic entity ID from kind and canonical key components.

    The canonical key is ``repr((compound_id, second_element))`` — the same
    format used as keys in ``signature_map.json``.

    Returns:
        String in ``{prefix}:{7 hex}`` format, e.g. ``fn:a3f8c1d``.
    """
    prefix = kind_to_prefix(kind)
    canonical = repr((compound_id, second_element))
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:7]
    return f"{prefix}:{digest}"


def build_id_map(
    signature_map_data: dict[str, str],
    code_graph_entities: dict[str, dict],
) -> dict[str, str]:
    """Compute deterministic IDs for all entities and return old→new mapping.

    Args:
        signature_map_data: Raw signature_map.json dict
            (repr'd tuple key string → old entity_id).
        code_graph_entities: Dict of entity data keyed by old entity_id,
            each having at least a ``kind`` field.

    Returns:
        Dict mapping old Doxygen entity_id → new deterministic entity_id.

    Raises:
        RuntimeError: On any hash collision (two different keys producing
            the same prefixed ID).
    """
    old_to_new: dict[str, str] = {}
    seen_new_ids: dict[str, str] = {}  # new_id → raw key (for collision reporting)

    for doc_key_str, old_entity_id in signature_map_data.items():
        entity_data = code_graph_entities.get(old_entity_id)
        if entity_data is None:
            continue

        kind = entity_data.get("kind", "unknown")
        parsed_key: tuple[str, str] = ast.literal_eval(doc_key_str)
        compound_id, second_element = parsed_key

        new_id = compute_entity_id(kind, compound_id, second_element)

        if new_id in seen_new_ids:
            existing_key = seen_new_ids[new_id]
            raise RuntimeError(
                f"Hash collision: {new_id!r} produced by both "
                f"{existing_key!r} and {doc_key_str!r}"
            )

        seen_new_ids[new_id] = doc_key_str
        old_to_new[old_entity_id] = new_id

    log.info(
        "Deterministic ID map built",
        total=len(old_to_new),
        collision_check="passed",
    )
    return old_to_new
