"""
Minimal artifact models — replaces external doxygen_parse / doc_db / doxygen_graph imports.

These are lightweight, stdlib-only dataclasses that parse the same JSON artifacts
(code_graph.json, doc_db.json, code_graph.gml) without pulling in the full
gen_docs/clustering Pydantic models.

Only the fields actually read by build_helpers are included.
"""

from __future__ import annotations

import ast
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional

import networkx as nx

# ---------------------------------------------------------------------------
# Entity ID helpers
# ---------------------------------------------------------------------------


@dataclass
class EntityID:
    """Compound + optional member hash."""
    compound: str
    member: Optional[str] = None

    def __str__(self) -> str:
        if self.member:
            return f"{self.compound}_{self.member}"
        return self.compound

    def __hash__(self) -> int:
        return hash(str(self))

    def __eq__(self, other: object) -> bool:
        if isinstance(other, EntityID):
            return self.compound == other.compound and self.member == other.member
        return NotImplemented

    @staticmethod
    def from_str(entity_id: str) -> EntityID:
        # Split old Doxygen-format ID on last underscore: "fight_8cc_1a2b3c" → ("fight_8cc", "1a2b3c")
        idx = entity_id.rfind("_")
        if idx > 0:
            return EntityID(compound=entity_id[:idx], member=entity_id[idx + 1:])
        return EntityID(compound=entity_id)


# ---------------------------------------------------------------------------
# Location
# ---------------------------------------------------------------------------

@dataclass
class DoxygenLocation:
    fn: str
    line: int
    column: Optional[int] = None
    end_line: Optional[int] = None
    type: str = ""

    @staticmethod
    def from_dict(d: dict) -> Optional[DoxygenLocation]:
        if d is None or d.get("line") is None:
            return None
        return DoxygenLocation(
            fn=d["fn"],
            line=d["line"],
            column=d.get("column"),
            end_line=d.get("end_line"),
            type=d.get("type", ""),
        )


# ---------------------------------------------------------------------------
# Doxygen Entity (minimal view)
# ---------------------------------------------------------------------------

@dataclass
class DoxygenEntity:
    """
    Minimal entity read from code_graph.json.

    Carries only the fields the build_helpers actually access:
    id, kind, name, signature, body, decl, file.
    """
    id: EntityID
    kind: str
    name: str
    body: Optional[DoxygenLocation] = None
    decl: Optional[DoxygenLocation] = None
    file: Optional[DoxygenLocation] = None
    # signature is overridden for functions; defaults to name
    _definition: Optional[str] = field(default=None, repr=False)
    _argsstring: Optional[str] = field(default=None, repr=False)

    @property
    def signature(self) -> str:
        if self._definition and self._argsstring is not None:
            return f"{self._definition}{self._argsstring}"
        return self.name

    @staticmethod
    def from_dict(data: dict) -> DoxygenEntity:
        eid = EntityID(**data["id"]) if isinstance(data["id"], dict) else EntityID.from_str(data["id"])
        return DoxygenEntity(
            id=eid,
            kind=data.get("kind", ""),
            name=data.get("name", ""),
            body=DoxygenLocation.from_dict(data.get("body")),
            decl=DoxygenLocation.from_dict(data.get("decl")),
            file=DoxygenLocation.from_dict(data.get("file")),
            _definition=data.get("definition"),
            _argsstring=data.get("argsstring"),
        )


# ---------------------------------------------------------------------------
# Entity Database
# ---------------------------------------------------------------------------

class EntityDatabase:
    """
    Flat mapping of EntityID → DoxygenEntity loaded from code_graph.json.

    Only provides the .entities dict (compounds + members merged) used by
    entity_processor.merge_entities().
    """

    def __init__(self) -> None:
        self._entities: Dict[str, DoxygenEntity] = {}  # str(id) -> entity

    @property
    def entities(self) -> Dict[str, DoxygenEntity]:
        return self._entities

    def add(self, entity: DoxygenEntity) -> None:
        self._entities[str(entity.id)] = entity

    @staticmethod
    def from_json(json_data: str) -> EntityDatabase:
        db = EntityDatabase()
        for raw in json.loads(json_data):
            db.add(DoxygenEntity.from_dict(raw))
        return db


def load_entity_db(db_path: Path) -> EntityDatabase:
    """Load an EntityDatabase from code_graph.json."""
    with db_path.open("r", encoding="utf-8") as f:
        return EntityDatabase.from_json(f.read())


# ---------------------------------------------------------------------------
# Document / DocumentDB  (from doc_db.json)
# ---------------------------------------------------------------------------

@dataclass
class Document:
    """
    Minimal documentation record from doc_db.json.

    Only the fields accessed by entity_processor:
    state, brief, details, params, definition, argsstring, system,
    returns, rationale, usages, notes.
    """
    state: Optional[str] = None
    brief: Optional[str] = None
    details: Optional[str] = None
    params: Optional[Dict[str, str]] = None
    returns: Optional[str] = None
    rationale: Optional[str] = None
    usages: Optional[Dict[str, str]] = None
    notes: Optional[str] = None
    definition: Optional[str] = None
    argsstring: Optional[str] = None
    system: Optional[str] = None

    @staticmethod
    def from_dict(d: dict) -> Document:
        return Document(
            state=d.get("state"),
            brief=d.get("brief"),
            details=d.get("details"),
            params=d.get("params"),
            returns=d.get("returns") or d.get("return"),
            rationale=d.get("rationale"),
            usages=d.get("usages"),
            notes=d.get("notes"),
            definition=d.get("definition"),
            argsstring=d.get("argsstring"),
            system=d.get("system"),
        )


class DocumentDB:
    """
    Two-level mapping loaded from the flat doc_db.json.

    Keys in the JSON are string-repr tuples: "('compound_id', 'signature')".
    Provides .docs[compound_id][signature] → Document.
    """

    def __init__(self) -> None:
        self.docs: Dict[str, Dict[str, Document]] = {}

    def load(self, path: Path) -> DocumentDB:
        with path.open("r", encoding="utf-8") as f:
            raw: dict = json.load(f)
        for key_str, value in raw.items():
            cid, sig = ast.literal_eval(key_str)
            self.docs.setdefault(cid, {})[sig] = Document.from_dict(value)
        return self

    def count(self) -> int:
        return sum(len(sigs) for sigs in self.docs.values())

    def get_doc(self, compound_id: str, signature: str) -> Optional[Document]:
        return self.docs.get(compound_id, {}).get(signature)


# ---------------------------------------------------------------------------
# GML graph loader (replaces doxygen_graph.load_graph)
# ---------------------------------------------------------------------------

def load_gml_graph(gml_path: Path) -> nx.MultiDiGraph:
    """
    Load a GML dependency graph as a MultiDiGraph.

    Equivalent to doxygen_graph.load_graph but without extra dependencies.
    """
    g = nx.read_gml(str(gml_path), destringizer=int)
    if not isinstance(g, nx.MultiDiGraph):
        mg = nx.MultiDiGraph()
        mg.add_nodes_from(g.nodes(data=True))
        for u, v, data in g.edges(data=True):
            mg.add_edge(u, v, **data)
        return mg
    return g
