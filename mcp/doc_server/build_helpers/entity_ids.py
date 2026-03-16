"""
Centralized entity_id operations for the build pipeline.

All logic that treats entity_id as anything other than an opaque unique string
lives here. The server runtime must never import this module — it should treat
entity_id as an opaque key.

Provides:
- split_entity_id(): Canonical compound/member decomposition.
- SignatureMap: Loads signature_map.json and provides bidirectional lookups
  between entity_id and doc_db key (compound_id, signature).
"""

from __future__ import annotations

import ast
import json
import re
from pathlib import Path
from typing import Optional

from server.logging_config import log

_MEMBER_RE = re.compile(r"^(.*)_([0-9a-z]{2}[0-9a-f]{30,})$")


def split_entity_id(entity_id: str) -> tuple[str, Optional[str]]:
    """Split a Doxygen entity_id into (compound_id, member_hash | None).

    This is the single canonical implementation of this operation.
    The regex matches a trailing ``_XX<30+ hex>`` suffix as the member hash.
    """
    m = _MEMBER_RE.match(entity_id.strip())
    return (m.group(1), m.group(2)) if m else (entity_id, None)


class SignatureMap:
    """Bidirectional mapping between entity_id and doc_db key.

    Loaded from ``signature_map.json`` whose keys are string-repr tuples
    ``"('compound_id', 'signature')"`` and values are entity_id strings.

    Provides:
    - forward:  doc_db_key (str) → entity_id
    - reverse:  entity_id → doc_db_key (str)
    - doc_key_for(): entity_id → parsed (compound_id, signature) tuple
    """

    def __init__(self, forward: dict[str, str]) -> None:
        self._forward = forward
        self._reverse: dict[str, str] = {v: k for k, v in forward.items()}

    @staticmethod
    def load(artifacts_dir: Path) -> SignatureMap:
        path = artifacts_dir / "signature_map.json"
        log.info("Loading signature map", path=str(path))
        with path.open("r", encoding="utf-8") as f:
            forward = json.load(f)
        sm = SignatureMap(forward)
        log.info("Signature map loaded", entries=len(forward))
        return sm

    # -- forward lookups (doc_db key → entity_id) --

    def entity_id_for_doc_key(self, doc_key: str) -> str | None:
        """Return entity_id for a raw doc_db key string, or None."""
        return self._forward.get(doc_key)

    # -- reverse lookups (entity_id → doc_db key) --

    def doc_key_for(self, entity_id: str) -> tuple[str, str] | None:
        """Return parsed (compound_id, signature) for an entity_id, or None."""
        raw = self._reverse.get(entity_id)
        if raw is None:
            return None
        return ast.literal_eval(raw)

    def has_entity(self, entity_id: str) -> bool:
        return entity_id in self._reverse

    @property
    def entity_ids(self) -> set[str]:
        return set(self._reverse.keys())

    def __len__(self) -> int:
        return len(self._forward)
