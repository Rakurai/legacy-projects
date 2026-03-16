"""
Entity database models for the Legacy MUD codebase.

Defines EntityID, LocationID, DoxygenEntity hierarchy, and EntityDatabase.
Loads/saves from/to code_graph.json (flat JSON array of entities).

The XML parsing functions that originally built these from Doxygen output
have been removed — the canonical data source is now code_graph.json.
"""
from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path
import json
from loguru import logger as log
from pydantic import BaseModel, Field


class EntityID(BaseModel):
    compound: str
    member: Optional[str] = None

    def __hash__(self):
        return hash(str(self))

    @property
    def is_member_id(self) -> bool:
        return bool(self.member)
    @property
    def is_compound_id(self) -> bool:
        return not self.is_member_id
    
    def __str__(self):
        if self.is_member_id:
            return f"{self.compound}_{self.member}"
        return self.compound

    @staticmethod
    def from_str(entity_id: str) -> EntityID:
        cid, mid = EntityID.split(entity_id)
        return EntityID(compound=cid, member=mid)
    
    @staticmethod
    def split(entity_id: str) -> Tuple[str, Optional[str]]:
        """Split a Doxygen entity ID into its compound and member parts."""
        import re
        m = re.match(r"^(.*)_([0-9a-z]{2}[0-9a-f]{30,})$", entity_id.strip())
        return (m.group(1), m.group(2)) if m else (entity_id, None)


class LocationID(BaseModel):
    """A class representing a Doxygen location ID."""
    fn: str
    line: int
    column: Optional[int] = None
    end_line: Optional[int] = None

    def __hash__(self):
        return hash(str(self))

    def __str__(self):
        s = f"{self.fn}:{self.line}"
        if self.column is not None:
            s += f":{self.column}"
        if self.end_line is not None:
            s += f"-{self.end_line}"
        return s

    @staticmethod
    def from_str(location_id: str) -> LocationID:
        if location_id.count(":") == 2:
            fn, line, column = location_id.split(":")
            return LocationID(fn=fn, line=int(line), column=int(column))
        elif location_id.count(":") == 1:
            fn, lines = location_id.split(":")
            line, end_line = lines.split("-")
            return LocationID(fn=fn, line=int(line), end_line=int(end_line))
        raise ValueError(f"Invalid location ID format: {location_id}")


class DoxygenLocation(BaseModel):
    fn: str
    line: int
    column: Optional[int] = None
    end_line: Optional[int] = None
    type: str

    @property
    def id(self) -> str:
        return LocationID(fn=self.fn, line=self.line, column=self.column, end_line=self.end_line)

class DoxygenEntity(BaseModel):
    """A class representing a Doxygen compound."""
    id: EntityID
    kind: str
    name: str
    extern: Optional[bool] = False
    file: Optional[DoxygenLocation] = None
    decl: Optional[DoxygenLocation] = None
    body: Optional[DoxygenLocation] = None
    detailed_refs: List[Dict[str, Any]] = Field(default_factory=list)

    @property
    def signature(self) -> str:
        return self.name
    
    @property
    def refs(self) -> List[EntityID]:
        return [EntityID.from_str(r['refid']) for r in self.detailed_refs]

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> DoxygenEntity:
        for key in ['file', 'decl', 'body']:
            if key in data and data[key].get('line') is None:
                del data[key]

        if data['id'].get('member'):
            if data['kind'] in ('function', 'friend'):
                entity = DoxygenFunction(**data)
            else:
                entity = DoxygenMember(**data)
        else:
            if data['kind'] in ('class', 'struct'):
                entity = DoxygenClass(**data)
            elif data['kind'] in ('file',):
                entity = DoxygenFile(**data)
            else:
                entity = DoxygenCompound(**data)

        return entity

    @staticmethod
    def from_json(data: Dict[str, Any]) -> DoxygenEntity:
        return DoxygenEntity.from_dict(data)
    
    def get_code_location(self):
        if self.body:
            return self.body.fn, self.body.line, self.body.end_line or self.body.line
        elif self.file:
            return self.file.fn, self.file.line, self.file.line
        elif self.decl:
            return self.decl.fn, self.decl.line, self.decl.line


class DoxygenCompound(DoxygenEntity):
    """A class representing a Doxygen compound."""
    pass


class DoxygenFile(DoxygenCompound):
    codeline_refs: Dict[str, List[str]] = {}


class DoxygenClass(DoxygenCompound):
    """A class representing a Doxygen class."""
    def get_code_location(self):
        fn, start, end = self.body.fn, self.body.line, self.body.end_line or self.body.line
        # structs and classes have the class definition start at file.line, not body.line
        if self.file and self.file.fn == fn and 0 < (self.file.line - start) < 6: # number of lines might be wrong for long inheritance lists
            start = self.file.line
        return fn, start, end


class DoxygenMember(DoxygenEntity):
    """A class representing a Doxygen member."""


class DoxygenFunction(DoxygenMember):
    """A class representing a Doxygen function."""
    definition: str
    argsstring: str

    @property
    def signature(self) -> str:
        return f"{self.definition}{self.argsstring}"

    # TODO need to ensure that params descriptions actually match argsstring or better yet the XML parameter names


class EntityDatabase(BaseModel):
    compounds: Dict[EntityID, DoxygenCompound] = {}
    members: Dict[EntityID, DoxygenMember] = {}
    member_groups: Dict[str, List[DoxygenMember]] = {}
    locations: Dict[LocationID, DoxygenLocation] = {}
    codelines: Dict[str, Dict[int, Dict[str, str|List[str]]]] = {}

    @property
    def entities(self) -> Dict[EntityID, DoxygenEntity]:
        return dict(list(self.compounds.items()) + list(self.members.items()))

    def add(self, entity: DoxygenEntity) -> None:
        if isinstance(entity, DoxygenCompound):
            if entity.id in self.compounds:
                raise Exception(f"duplicate compound ID {entity.id}")

            self.compounds[entity.id] = entity

            if isinstance(entity, DoxygenFile) and entity.codeline_refs:
                # print(entity.id)
                # print(entity)
                self.codelines.setdefault(entity.file.fn, {}).update(entity.codeline_refs)
        else:
            self.members[entity.id] = entity
            self.member_groups.setdefault(entity.id.member, []).append(entity)

        for loc in (entity.file, entity.decl, entity.body):
            if loc:
                # don't let 'file' replace 'decl' or 'body'
                if (loc.id in self.locations
                    and self.locations[loc.id].type != 'file'
                    and self.locations[loc.id].type != loc.type):
                        # if there's a conflict and this is a 'file', just skip it
                        if loc.type != 'file':
                            print(f"duplicate location ID {loc.id} with types {self.locations[loc.id].type} and {loc.type}")
                else:
                    self.locations[loc.id] = loc

    def get(self, entity_id: str|EntityID) -> DoxygenEntity | None:
        if not isinstance(entity_id, EntityID):
            entity_id = EntityID.from_str(entity_id)
        if entity_id.is_member_id:
            return self.members.get(entity_id)
        return self.compounds.get(entity_id)

    def get_codelines(self, fn: str, start: int, end: int) -> Dict[int, Dict[str, str|List[str]]]:
        return {
            line: self.codelines.get(fn, {}).get(line, {})
            for line in range(start, end + 1)
        }

    def model_dump_json(self, **kwargs) -> str:
        # in-memory we use a dict, but we can rebuild the dict from the
        # entries without worrying about tuple keys so just serialize as
        # a list of all entries
        """Custom JSON serialization to preserve subclass fields."""
        data = [e.model_dump(exclude_none=True) for d in (self.compounds, self.members) for e in d.values()]
        # Convert to JSON
        return json.dumps(data, **kwargs)

    @staticmethod
    def from_json(json_data: str) -> EntityDatabase:
        db = EntityDatabase()
        for entity_data in json.loads(json_data):
            entity = DoxygenEntity.from_json(entity_data)
            db.add(entity)
        return db


def load_db(db_path: Path) -> EntityDatabase:
    """Load an EntityDatabase from a JSON file (code_graph.json)."""
    if not db_path.exists():
        raise FileNotFoundError(f"Database file {db_path} does not exist.")
    with db_path.open("r", encoding="utf-8") as f:
        json_data = f.read()
    return EntityDatabase.from_json(json_data)


def save_db(db: EntityDatabase, db_path: Path) -> None:
    """Save an EntityDatabase to a JSON file."""
    with db_path.open("w", encoding="utf-8") as f:
        f.write(db.model_dump_json(indent=2))
    log.info(f"Database saved to {db_path}")
