"""
Deterministic entity ID generation.

Replaces opaque Doxygen IDs with stable, type-prefixed content-hashed IDs
of the form ``{prefix}:{sha256(canonical_key)[:7]}``.

The canonical key is ``repr((compound_id, second_element))`` where
second_element is the member hash for members, or the compound ID for compounds.
"""

import hashlib

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

    Returns:
        String in ``{prefix}:{7 hex}`` format, e.g. ``fn:a3f8c1d``.
    """
    prefix = kind_to_prefix(kind)
    canonical = repr((compound_id, second_element))
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:7]
    return f"{prefix}:{digest}"
