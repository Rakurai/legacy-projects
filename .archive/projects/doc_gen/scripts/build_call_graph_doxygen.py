from functools import cache
import os
import xml.etree.ElementTree as ET
from pathlib import Path
import networkx as nx
import json
from loguru import logger as log

# Configuration
DOXYGEN_XML_DIR = Path("projects/doc_gen/doxygen_output/xml")
INDEX_XML = DOXYGEN_XML_DIR / "index.xml"
GRAPH_OUTPUT = Path("projects/doc_gen/internal/code_graph.gml")

# Graph edge types
CONTAINS = "contains"
REQUIRES = "requires"

# Node types
COMPOUND = "compound"
MEMBER = "member"

call_graph = nx.DiGraph()


def parse_index():
    """Parse index.xml to build initial compound/member index."""
    tree = ET.parse(INDEX_XML)
    root = tree.getroot()

    for compound in root.findall("compound"):
        compound_id = compound.attrib.get("refid")
        compound_name = compound.findtext("name")
        compound_kind = compound.attrib.get("kind")
        compound_label = f"{compound_kind}::{compound_name}"

        # skip some entities at least for now
        if compound_kind in (
            'dir', # probably not going to document a directory, only has file references inside
        ):
            continue

        call_graph.add_node(
            compound_id,
            name=compound_name,
            kind=compound_kind,
            type=COMPOUND
        )

        for member in compound.findall("member"):
            member_id = member.attrib.get("refid")
            member_name = member.findtext("name")
            member_kind = member.attrib.get("kind")

            call_graph.add_node(
                member_id,
                name=member_name,
                kind=member_kind,
                type=MEMBER
            )
            call_graph.add_edge(compound_id, member_id, type=CONTAINS)

    num_compound_nodes = sum(1 for n, d in call_graph.nodes(data=True) if d['type'] == COMPOUND)
    num_member_nodes = sum(1 for n, d in call_graph.nodes(data=True) if d['type'] == MEMBER)
    kinds = set(d['kind'] for n, d in call_graph.nodes(data=True))
    log.info(f"Number of compound nodes in call_graph: {num_compound_nodes}")
    log.info(f"Number of member nodes in call_graph: {num_member_nodes}")
    log.info(f"Number of contains edges in call_graph: {call_graph.number_of_edges()}")
    log.info(f"Found kinds in call_graph: {kinds}")

@cache
def get_nodes(g, kind=None, type=None):
    """Get all nodes in the graph."""
    for n, d in g.nodes(data=True):
        if (kind is None or d['kind'] == kind) and (type is None or d['type'] == type):
            yield n

def extract_doc_comment(member):
    brief = member.find("briefdescription")
    detailed = member.find("detaileddescription")

    def extract_text(elem):
        if elem is None:
            return ""
        return " ".join(t.strip() for t in elem.itertext()).strip()

    return "\n".join(
        filter(None, [extract_text(brief), extract_text(detailed)])
    ).strip()

def get_compound_id(member_id):
    """Get the compound ID for a given member ID."""
    # Doxygen member IDs are typically of the form <compound_id>_1<something>
    # To get the compound_id, strip trailing digits and underscores after the last underscore
    return member_id.rsplit('_', 1)[0] if '_' in member_id else None

def parse_compounds():
    """Iterate over compound nodes, open each xml, iterate over members and update callgraph links."""
    for compound_id in get_nodes(call_graph, type=COMPOUND):
        xml_path = DOXYGEN_XML_DIR / f"{compound_id}.xml"
        if not xml_path.exists():
            raise FileNotFoundError(f"XML file not found: {xml_path}")

        tree = ET.parse(xml_path)
        root = tree.getroot()

        for member in root.findall(".//memberdef"):
            member_id = member.attrib.get("id")

            doc = extract_doc_comment(member)
            # Update node attributes using the update method
            call_graph.nodes[member_id].update({
                "doc_comment": doc,
                "external": member.attrib.get("extern", "no") == "yes",
            })

            # get the location of the code snippet
            location = member.find("location")
            if location is not None:
                # if the function is external the location has different keys
                if call_graph.nodes[member_id]["external"]:
                    decl = (location.attrib.get("declfile"), location.attrib.get("declline"))
                    impl = None
                else:
                    decl = (location.attrib.get("file"), location.attrib.get("line"))
                    impl = (location.attrib.get("bodyfile"), location.attrib.get("bodystart"), location.attrib.get("bodyend"))

                call_graph.nodes[member_id]["decl_file"] = decl[0]
                call_graph.nodes[member_id]["decl_line"] = int(decl[1])

                if impl and impl[0]:
                    call_graph.nodes[member_id]["impl_file"] = impl[0]
                    call_graph.nodes[member_id]["impl_start"] = int(impl[1])
                    call_graph.nodes[member_id]["impl_end"] = int(impl[2])

            for ref in member.findall("references"):
                callee_id = ref.attrib.get("refid")
                if not callee_id:
                    raise ValueError(f"Callee ID not found in reference: {ET.tostring(ref, encoding='unicode')}")
                if callee_id not in call_graph:
                    raise ValueError(f"Callee ID not found in call graph: {callee_id}")

                call_graph.add_edge(member_id, callee_id, type=REQUIRES)

    num_requires_edges = sum(1 for u, v, d in call_graph.edges(data=True) if d.get('type') == REQUIRES)
    log.info(f"Number of requires edges in call_graph: {num_requires_edges}")


def export_graph():
    nx.write_gml(call_graph, GRAPH_OUTPUT)
    log.info(f"Graph written to {GRAPH_OUTPUT}")


if __name__ == "__main__":
    log.info("Parsing index.xml and building abstract code graph...")
    parse_index()
    parse_compounds()
    export_graph()
    log.info("Done.")