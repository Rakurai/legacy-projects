"""
Document database for the Legacy MUD codebase.

Loads/saves the flat doc_db.json file and exposes a queryable DocumentDB.
Each document represents a documented entity (function, class, struct, etc.)
with LLM-generated documentation and optional system/subsystem classification.
"""
import ast
import json
from enum import Enum
from pathlib import Path
from typing import Dict, Iterator, List, Optional, Tuple

from pydantic import AliasChoices, BaseModel, Field

# ── paths (relative to this file) ──────────────────────────────────────

_HERE = Path(__file__).resolve().parent
DOC_DB_PATH = _HERE / "doc_db.json"
DOC_DB_BACKUP_PATH = _HERE / "doc_db.backup.json"


# ── enums ───────────────────────────────────────────────────────────────

class DocumentState(str, Enum):
    EXTRACTED_SUMMARY = "extracted_summary"
    GENERATED_SUMMARY = "generated_summary"
    GENERATED_USAGE = "generated_usage"
    REFINED_USAGE = "refined_usage"
    REFINED_SUMMARY = "refined_summary"


# ── models ──────────────────────────────────────────────────────────────

class DoxygenFields(BaseModel):
    brief: Optional[str] = None
    details: Optional[str] = None
    params: Optional[Dict[str, str]] = None
    returns: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("return", "returns"),
        serialization_alias="returns",
    )
    tparams: Optional[Dict[str, str]] = None
    throws: Optional[str] = None
    notes: Optional[str] = None
    rationale: Optional[str] = None


class Document(DoxygenFields):
    # ── identity ────────────────────────────────────────────────────────
    state: Optional[str] = None
    cid: str
    mid: str
    etype: str
    kind: str
    name: str
    qualified_name: Optional[str] = None
    definition: Optional[str] = None
    argsstring: Optional[str] = None

    # ── pipeline artefacts (may be absent in legacy flat file) ──────────
    prompt: Optional[str] = None
    response: Optional[DoxygenFields] = None
    usages: Optional[Dict[str, str]] = None

    # ── classification ──────────────────────────────────────────────────
    system: Optional[str] = None
    subsystem: Optional[str] = None
    system_candidates: Optional[List[str]] = None
    subsystem_candidates: Optional[List[str]] = None

    # ── doxygen export ──────────────────────────────────────────────────

    def to_doxygen(self) -> str:
        lines = ["/**"]

        tag_map = {
            "function": "@fn",
            "variable": "@var",
            "enum": "@enum",
            "class": "@class",
            "struct": "@struct",
            "namespace": "@namespace",
            "define": "@def",
            "group": "@defgroup",
        }
        tag = tag_map.get(self.kind, "@fn")
        if self.kind == "function":
            lines.append(f" * {tag} {self.definition}{self.argsstring}")
        else:
            lines.append(f" * {tag} {self.name}")

        if self.brief:
            lines.append(" *")
            lines.append(f" * @brief {self.brief}")
        if self.details:
            lines.append(" *")
            lines.append(f" * @details {self.details}")
        if self.notes:
            lines.append(" *")
            lines.append(f" * @note {self.notes}")
        if self.rationale:
            lines.append(" *")
            lines.append(f" * @rationale {self.rationale}")
        lines.append(" *")

        if self.tparams:
            for tname, desc in self.tparams.items():
                lines.append(f" * @tparam {tname} {desc}")
        if self.params:
            for pname, desc in self.params.items():
                lines.append(f" * @param {pname} {desc}")
        if self.returns:
            lines.append(f" * @return {self.returns}")
        if self.throws:
            lines.append(f" * @throws {self.throws}")

        lines.append(" */")
        return "\n".join(lines)


# ── database ────────────────────────────────────────────────────────────

class DocumentDB(BaseModel):
    """Two-level dict of documents: compound_id → signature → Document."""

    docs: Dict[str, Dict[str, Document]] = {}

    # ── persistence ─────────────────────────────────────────────────────

    def load(self, path: Path | str | None = None) -> "DocumentDB":
        """Load from the flat doc_db.json (string-tuple keys)."""
        path = Path(path) if path else DOC_DB_PATH
        with open(path, "r") as f:
            raw: dict = json.load(f)

        doc_map: Dict[str, Dict[str, Document]] = {}
        for key_str, value in raw.items():
            # keys are like "('compound_id', 'signature')"
            cid, sig = ast.literal_eval(key_str)
            doc = Document(**value)
            doc_map.setdefault(cid, {})[sig] = doc

        self.docs = doc_map
        return self

    def save(self, path: Path | str | None = None) -> None:
        """Save back to the flat doc_db.json format with string-tuple keys."""
        path = Path(path) if path else DOC_DB_PATH
        flat: dict = {}
        for cid, entities in self.docs.items():
            for sig, doc in entities.items():
                key = repr((cid, sig))
                flat[key] = doc.model_dump(exclude_none=True, by_alias=True)
        with open(path, "w") as f:
            json.dump(flat, f, indent=2)

    # ── access ──────────────────────────────────────────────────────────

    def get_doc(self, compound_id: str, entity_signature: str) -> Optional[Document]:
        """Get a document by compound_id and entity_signature."""
        return self.docs.get(compound_id, {}).get(entity_signature)

    def add_doc(self, compound_id: str, entity_signature: str, doc: Document) -> None:
        """Add or replace a document."""
        self.docs.setdefault(compound_id, {})[entity_signature] = doc

    def items(self) -> Iterator[Tuple[str, str, Document]]:
        """Iterate (compound_id, signature, document) triples."""
        for cid, entities in self.docs.items():
            for sig, doc in entities.items():
                yield cid, sig, doc

    def all_docs(self) -> Iterator[Document]:
        """Iterate all documents."""
        for entities in self.docs.values():
            yield from entities.values()

    def count(self) -> int:
        """Total number of documents."""
        return sum(len(e) for e in self.docs.values())

    # ── dict-like access ────────────────────────────────────────────────

    def __getitem__(self, key: str) -> Dict[str, Document]:
        return self.docs[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self.docs)

    def __len__(self) -> int:
        return len(self.docs)

    def __contains__(self, key: str) -> bool:
        return key in self.docs
