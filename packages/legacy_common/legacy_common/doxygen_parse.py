from functools import cache
from typing import Any, Dict, List, Optional, Set, Tuple
import xml.etree.ElementTree as ET
from pathlib import Path
import json
from loguru import logger as log
from pydantic import BaseModel, Field

# objective: build a database of items from the Doxygen output XML

# this class represents a Doxygen documentation block from a single
# source (in-code, generated, etc.)
# TODO hierarchical or 'best' selection of each field from multiple sources
class DoxygenDoc(BaseModel):
    brief: Optional[str] = None
    details: Optional[str] = None
    params: Optional[List[str]] = None
    returns: Optional[str] = None


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


possible_file_kinds = {'class', 'define', 'dir', 'enum', 'file', 'friend', 'function', 'namespace', 'struct', 'typedef', 'variable'}
possible_body_kinds = {'class', 'define', 'enum', 'friend', 'function', 'struct', 'typedef', 'variable'}
possible_decl_kinds = {'function', 'variable'}
#exclusive_file_kinds = ['dir', 'file', 'namespace']

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
    doc: Optional[DoxygenDoc] = None
    detailed_refs: List[Dict[str, Any]] = Field(default_factory=list)  # Detailed reference information

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

    @staticmethod
    def from_xml_dir(xml_dir: Path) -> EntityDatabase:
        db = EntityDatabase()

        for xml_path in xml_dir.glob("*.xml"):
            if xml_path.name == "index.xml":
                continue

            tree = ET.parse(xml_path)
            root = tree.getroot()

            elem = root.find(".//compounddef")
            if elem is None:
                continue

            data = parse_compounddef(elem)
            entity = DoxygenEntity.from_dict(data)
            db.add(entity)

            for elem in root.findall(".//memberdef"):
                data = parse_memberdef(elem)
                if data['kind'] in ('friend',):
                    continue
                entity = DoxygenEntity.from_dict(data)
                db.add(entity)


        return db


def parse_codeline(codeline_elem: ET.Element) -> Tuple[int, str|None, List[str]]:
    """
    Parse a <codeline> element to extract the line number and references.

    Args:
        codeline_elem: The XML element representing a <codeline>.

    Returns:
        A tuple containing:
        - The line number of the code line.
        - The reference ID if available.
        - A list of references found in the line.
    """
    lineno = int(codeline_elem.attrib.get("lineno", -1))
    eid = codeline_elem.attrib.get("refid")
    refs = []

    # Process each reference in the line
    for ref_elem in codeline_elem.findall(".//ref"):
        refid = ref_elem.attrib.get("refid")
        if refid:
            refs.append(refid)

    return lineno, eid, refs


def parse_location(entity_elem: ET.Element) -> Dict[str, Tuple[str, int, int]]:
    """Parse the location element from a Doxygen XML file."""
    location = entity_elem.find("location")
    if location is None:
        return {}

    # TODO need to do a correction here for 'bodyfile': for struct and class
    # definitions we're going to open the file and look at the bodyfile start
    # line, walk backwards until we encounter "struct" or "class"
    la = location.attrib
    data = {}
    if 'file' in la:
        data['file'] = {'fn': la['file'], 'line': int(la.get('line', -1)), 'column': int(la.get('column', -1)), 'type': 'file'}
    if 'declfile' in la:
        data['decl'] = {'fn': la['declfile'], 'line': int(la.get('declline', -1)), 'column': int(la.get('declcolumn', -1)), 'type': 'decl'}
    if 'bodyfile' in la:
        data['body'] = {'fn': la['bodyfile'], 'line': int(la.get('bodystart', -1)), 'end_line': int(la.get('bodyend', -1)), 'type': 'body'}
    for t in 'file', 'decl', 'body':
        if t in data:
            if data[t].get('line') == -1:
                data[t]['line'] = None # will remove below
            if 'column' in data[t] and data[t]['column'] == -1:
                data[t]['column'] = 0
            if 'end_line' in data[t] and data[t]['end_line'] == -1:
                data[t]['end_line'] = data[t]['line']
#    data = {k:v for k,v in data.items() if v.get('line') is not None}
    return data


def parse_descriptions(entity_elem: ET.Element) -> Dict[str, str]:
    """Parse description elements from Doxygen XML."""
    out = {}

    # Helper function to extract text from elements including ref tags
    def extract_text(elem):
        if elem is None:
            return ""
        return "".join(elem.itertext()).strip()

    # 1. Process brief description
    brief_elem = entity_elem.find("briefdescription")
    if brief_elem is not None:
        brief_parts = []
        for para in brief_elem.findall("para"):
            brief_text = extract_text(para)
            if brief_text:
                brief_parts.append(brief_text)
        
        brief = " ".join(brief_parts).strip()
        if brief:
            out['brief'] = brief

    # 2. Process detailed description
    detailed_elem = entity_elem.find("detaileddescription")
    if detailed_elem is not None:
        # 2a. Extract main description paragraphs
        detail_parts = []
        
        for para in detailed_elem.findall("para"):
            # Check if para contains parameterlist or simplesect
            param_list = para.find("parameterlist")
            simplesect = para.find("simplesect")
            
            if param_list is not None or simplesect is not None:
                # Extract text before the special sections
                para_content = ET.tostring(para, encoding="unicode")
                
                # Find the index of the first special section
                param_index = para_content.find("<parameterlist") if param_list is not None else len(para_content)
                simplesect_index = para_content.find("<simplesect") if simplesect is not None else len(para_content)
                cutoff_index = min(param_index, simplesect_index)
                
                # Create a new element with just the content before special sections
                if cutoff_index > 0:
                    import re
                    # Extract text up to the first special section
                    partial_content = para_content[:cutoff_index] + "</para>"
                    # Fix any unclosed tags
                    partial_content = re.sub(r'<([^/][^>]*)>(?!.*</\1>)', r'<\1></\1>', partial_content)
                    
                    try:
                        partial_elem = ET.fromstring(partial_content)
                        text = extract_text(partial_elem)
                        if text.strip():
                            detail_parts.append(text.strip())
                    except ET.ParseError:
                        # If parsing fails, try a simpler approach
                        text = para.text or ""
                        for child in para:
                            if child.tag in ("parameterlist", "simplesect"):
                                break
                            text += extract_text(child)
                            text += child.tail or ""
                        if text.strip():
                            detail_parts.append(text.strip())
            else:
                # Regular paragraph without special sections
                text = extract_text(para)
                if text.strip():
                    detail_parts.append(text.strip())
        
        if detail_parts:
            out["details"] = "\n".join(detail_parts).strip()

        # 2b. Process parameter descriptions
        for plist in detailed_elem.findall(".//parameterlist[@kind='param']"):
            for pitem in plist.findall("parameteritem"):
                pname = pitem.findtext(".//parametername", "").strip()
                pdesc_elem = pitem.find(".//parameterdescription/para")
                
                if pname and pdesc_elem is not None:
                    pdesc = extract_text(pdesc_elem)
                    if pdesc:
                        out.setdefault("params", {})[pname] = pdesc

        # 2c. Process return description
        for ssect in detailed_elem.findall(".//simplesect[@kind='return']/para"):
            rtext = extract_text(ssect)
            if rtext:
                out["returns"] = rtext

    return out

# Helper: recursively iterate all subelements, skipping certain tags
def iter_subelements_skip(elem: ET.Element, skip_tags=None):
    for child in elem:
        if skip_tags and child.tag in skip_tags:
            continue
        yield child
        yield from iter_subelements_skip(child, skip_tags)

def parse_entitydef(elem: ET.Element, skip_tags=set()) -> Dict[str, Any]:
    """
    Parse an entity definition element to an ID and dictionary of useful information.
    """
    references = []  # Changed from a set to a list to store rich reference data

    data = {
        "kind": elem.attrib["kind"],
        "extern": elem.attrib.get("extern", "no") == "yes",
        "appearance": parse_descriptions(elem),
    }

    skip_tags |= set([
        'collaborationgraph',
        'inheritancegraph',
        'listofallmembers',
        'invincdepgraph',
        'incdepgraph',
        'programlisting' # handled specially in file compounds
    ])

    # Use the helper to iterate subelements, skipping unwanted tags
    for child in iter_subelements_skip(elem, skip_tags=skip_tags):
        if child.tag == "qualifiedname":
            data["qualifiedname"] = ET.tostring(child, encoding="unicode", method="text").strip()
        if "refid" in child.attrib:
            # Get parent path to provide context for the reference
            # Build a parent map for walking up the tree
            # parent_map = {c: p for p in elem.iter() for c in p}
            # def get_element_path(child, root):
            #     path = []
            #     parent = child
            #     while parent is not None and parent != root:
            #         path.insert(0, parent.tag)
            #         parent = parent_map.get(parent)
            #     return path

            # parent_path = get_element_path(child, elem)

            # Store rich reference information
            references.append({
                "refid": child.attrib["refid"],
                "tag": child.tag,
                # "context": "|".join(parent_path) if parent_path else None,
                # Optional: Store additional attributes if needed
                "attrs": {k: v for k, v in child.attrib.items() if k != "refid"},
            })

    # Keep compatibility: store both detailed references and legacy refs list
    data["detailed_refs"] = references
    data["refs"] = [ref["refid"] for ref in references]

    data.update(parse_location(elem))

    return data


def parse_compounddef(elem: ET.Element) -> Dict[str, Any]:
    # Define reference fields based on compound types - these are the XML tags we want to track
    data = parse_entitydef(elem, skip_tags=set(['memberdef']))

    data.update({
        "id": {"compound": elem.attrib["id"]},
        "name": elem.findtext("compoundname", "").strip(),
    })

    # If <programlisting> exists, parse its <codeline> tags
    programlisting = elem.find("programlisting")
    if programlisting is not None:
        codeline_refs: Dict[str, List[str]] = {}
        codelines = [parse_codeline(c) for c in programlisting.findall("codeline")]
        line_eid = None
        min_line = None

        for lineno, eid, refs in sorted(codelines, key=lambda x: x[0]):
            line_eid = eid or line_eid
            if line_eid and refs:
                if min_line is None or lineno < min_line:
                    min_line = lineno
                codeline_refs.setdefault(line_eid, []).extend(refs)

        if codelines:
            data['file']['line'] = min_line
            data["codeline_refs"] = codeline_refs


    return data


def parse_memberdef(elem: ET.Element) -> Dict[str, Any]:
    # Define reference fields based on member types
    data = parse_entitydef(elem)
    eid = EntityID.from_str(elem.attrib['id'])

    data.update({
        "id": {"compound": eid.compound, "member": eid.member},
        "name": elem.findtext("name", "").strip(),
    })

    # Add function-specific information
    if data['kind'] in ('function', 'friend'):
        data.update({
            "definition": elem.findtext("definition", "").strip(),
            "argsstring": elem.findtext("argsstring", "").strip(),
        })

    return data

def load_db(db_path: Path) -> EntityDatabase:
    """
    Load an EntityDatabase from a JSON file.
    """
    if not db_path.exists():
        raise FileNotFoundError(f"Database file {db_path} does not exist.")
    
    with db_path.open('r', encoding='utf-8') as f:
        json_data = f.read()
    
    return EntityDatabase.from_json(json_data)

def save_db(db: EntityDatabase, db_path: Path) -> None:
    """
    Save an EntityDatabase to a JSON file.
    """
    with db_path.open('w', encoding='utf-8') as f:
        json_data = db.model_dump_json(indent=2)
        f.write(json_data)

    log.info(f"Database saved to {db_path}")
