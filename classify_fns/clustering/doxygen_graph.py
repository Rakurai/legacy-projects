"""
Graph builder and loader for the Legacy MUD entity dependency graph.

Defines EntityType/Relationship enums, classify_reference(), build_graph(),
load_graph()/save_graph(), and the topological visit-list scheduler.

Functions that depended on source-code extraction (get_code_body, get_body_eid)
and the condensation DAG code have been removed.
"""
from __future__ import annotations
from enum import Enum
from typing import Dict, Generator, List, Optional, Set, Tuple
from pathlib import Path
import networkx as nx
from loguru import logger as log
import doxygen_parse as dp

# Node types
class EntityType(str, Enum):
    COMPOUND = "compound"
    MEMBER = "member"
    BODY = "body"
    DECLARATION = "decl"
    FILE = "file"


# Graph edge types
class Relationship(str, Enum):
    CONTAINED_BY = "contained_by"
#    REQUIRED_BY = "required_by"   # Generic fallback relationship
    REPRESENTED_BY = "represented_by"
    CALLS = "calls"               # Function calls another function
    USES = "uses"                 # Entity uses another entity (variables, types)
    INHERITS = "inherits"         # Class inheritance relationships
    INCLUDES = "includes"         # File inclusion relationships


def classify_reference(ref_tag: str, source: dp.DoxygenEntity, target: dp.DoxygenEntity) -> Tuple[dp.DoxygenEntity, dp.DoxygenEntity, Relationship]:
    """
    Classify a reference relationship based on entity kinds, reference tag, and context.
    
    Args:
        ref_data: Dictionary containing reference metadata including tag and context
        source: Entity making the reference
        target: Entity being referenced

    Returns:
        Tuple of (source_id, target_id, relationship_type)
        For tags ending in "by", the direction is reversed
    """
    possible_tags = {
        # these 4 "owns" tags appear on compounds to refer to other compounds defined within
        'innerclass', # can appear on file, class, struct, or namespace compounds to refer to a contained class or struct
        'innernamespace', # can appear on file compounds to refer to a contained namespace (could be multiple since namespaces can span files)
        'innerfile', # can appear on dir compounds to refer to contained files
        'innerdir', # can appear on dir compounds to refer to contained dirs

        # these two appear on class/struct member functions to indicate overrides, could be redundant with eachother
        'reimplementedby', # can appear on functions that are overridden by <refid> function
        'reimplements', # can appear on functions that override <refid> function

        # these two appear on files to indicate inclusion relationships, could be redundant with eachother
        'includedby', # can appear on files that are included by other files
        'includes', # can appear on files that include other files
        # NOTE: 'includes' can also appear on struct compounds and includes the containing header file, we can ignore these

        # these two appear on members and indicate reference relationships, could be redundant with eachother
        'referencedby', # can appear on functions, variables, or defines and refer to functions
        'references', # can appear on functions and refer to other functions, variables, or defines

        # these two appear on classes and structs to indicate inheritance, could be redundant with eachother
        'derivedcompoundref', # can appear on base classes or structs to refer to derivatives
        'basecompoundref', # can appear on derived classes or structs to refer to bases

        'codeline', # unique to a line of code, refers to the entity that "owns" that line

        'ref' # refers to any entity and can appear in these forms:
        # <any compound or member>    <detaileddescription><para><ref>
        # <any compound or member>    <briefdescription><para><ref>
        # <function|variable|typedef> <type><ref>
        # <function>                  <param><defval><ref>
        # <function>                  <param><type><ref>
        # <variable|define>           <initializer><ref>
        # <file>                      <programlisting><codeline><highlight><ref>
    }

    ref_tag = ref_tag.lower().strip()
    
    # Define a helper function to return the appropriate tuple
    def make_tuple(relationship: Relationship, reverse=False):
        # Check if this is a "by" relationship (reversed direction)
        if reverse:
            return target, source, relationship
        else:
            return source, target, relationship

    if ref_tag == 'ref':
        if source.id == target.id:
            return make_tuple(None)
        ref_tag = 'references'
        # if target.kind in ('function', 'define'):
        #     return make_tuple(Relationship.CALLS)
        # else:
        #     return make_tuple(Relationship.USES)

    # Handle inheritance relationships (basecompoundref, derivedcompoundref)
    if ref_tag == 'basecompoundref':
        if source.kind in ('class', 'struct') and target.kind in ('class', 'struct'):
            return make_tuple(Relationship.INHERITS)
    elif ref_tag == 'derivedcompoundref':
        if source.kind in ('class', 'struct') and target.kind in ('class', 'struct'):
            return make_tuple(Relationship.INHERITS, reverse=True)

    elif ref_tag == 'reimplements':
        if source.kind == 'function' and target.kind == 'function':
            return make_tuple(Relationship.INHERITS)
    elif ref_tag == 'reimplementedby':
        if source.kind == 'function' and target.kind == 'function':
            return make_tuple(Relationship.INHERITS, reverse=True)

    # Handle include relationships
    elif ref_tag == 'includes':
        if source.kind == 'file' and target.kind == 'file':
            return make_tuple(Relationship.INCLUDES)
        if source.kind in ('class', 'struct'):
            return make_tuple(None)
    elif ref_tag == 'includedby':
        if source.kind == 'file' and target.kind == 'file':
            return make_tuple(Relationship.INCLUDES, reverse=True)
    
    # Handle function calls
    elif ref_tag == 'references':
        if source.kind in ('function', 'define') and target.kind in ('function', 'define'):
            return make_tuple(Relationship.CALLS)
        if target.kind in ('variable', 'typedef', 'class', 'struct', 'enum', 'namespace', 'function', 'define'):
            return make_tuple(Relationship.USES)
        if target.kind in ('file',):
            return make_tuple(None)
    elif ref_tag == 'referencedby':
        if source.kind in ('function', 'define') and target.kind in ('function', 'define'):
            return make_tuple(Relationship.CALLS, reverse=True)
        if source.kind in ('class', 'struct', 'variable'):
            return make_tuple(Relationship.USES, reverse=True)

    elif ref_tag == 'innerclass':
        if source.kind in ('file', 'namespace', 'class', 'struct') and target.kind in ('class', 'struct'):
            return make_tuple(Relationship.CONTAINED_BY, reverse=True)
    elif ref_tag == 'innernamespace':
        if source.kind in ('file',) and target.kind in ('namespace',):
            return make_tuple(Relationship.CONTAINED_BY, reverse=True)
    elif ref_tag == 'innerfile':
        if source.kind in ('dir',) and target.kind in ('file',):
            return make_tuple(Relationship.CONTAINED_BY, reverse=True)
    elif ref_tag == 'innerdir':
        if source.kind in ('dir',) and target.kind in ('dir',):
            return make_tuple(Relationship.CONTAINED_BY, reverse=True)

    elif ref_tag == 'member':
        if source.kind in ('file', 'namespace') and target.kind in ('variable', 'define'):
            return make_tuple(Relationship.CONTAINED_BY, reverse=True)

    elif ref_tag == '_in_compound':
        return make_tuple(Relationship.CONTAINED_BY)

    # If we couldn't identify the relationship at all, throw an exception
    # This helps us identify unhandled cases that we need to add rules for
    raise Exception(f"Unknown reference relationship: {ref_tag} from {source.kind} to {target.kind}: {source.id}, {target.id}")


def compose_structural_reference_list(db: dp.EntityDatabase) -> Generator[Tuple[dp.EntityID, str, str], None, None]:
    """
    Compose a list of structural references from the entity database.
    
    Args:
        db: Entity database
    
    Returns:
        Generator of tuples (source_entity_id, target_entity_id, reference_tag)
    """
    for eid, c in db.compounds.items():
        for ref in c.detailed_refs:
            yield (eid, ref['refid'], ref['tag'])

    for eid, m in db.members.items():
        yield (eid, eid.compound, '_in_compound')

        for ref in m.detailed_refs:
            yield (eid, ref['refid'], ref['tag'])


def build_graph(db: dp.EntityDatabase, exclude: Set[dp.EntityID] = set()) -> nx.MultiDiGraph:
    """
    Build a directed multigraph where nodes are entities and edges represent relationships.
    Using a MultiDiGraph allows multiple edges between the same nodes with different relationship types.
    
    Args:
        db: Entity database
        exclude: Set of entity IDs to exclude
        
    Returns:
        NetworkX directed multigraph
    """
    from doxygen_parse import EntityID, DoxygenCompound, DoxygenMember
    # Change from DiGraph to MultiDiGraph to support multiple edges
    G = nx.MultiDiGraph()
    refs: List[Tuple[dp.EntityID, str, str]] = []

    compounds: Dict[EntityID, DoxygenCompound] = {
        eid:e for eid, e in db.compounds.items()
        if eid not in exclude
         and e.kind not in (
            # 'dir',
            # 'file',
            # 'namespace',
            # 'friend',
        )
    }
    members: Dict[EntityID, DoxygenMember] = {
        eid:e for eid, e in db.members.items()
        if eid not in exclude
         and e.kind not in (
            'friend',
#            'enumvalue',
        )# and EntityID(compound=eid.compound,member=None) in compounds # filter members with filtered compounds
    }

    for eid, c in compounds.items():
        G.add_node(
            str(eid),
            name=c.name,
            kind=c.kind,
            type=EntityType.COMPOUND,
        )

    for eid, m in members.items():
        # leave enumvalue in the graph, but filter from forward pass
        # if m.kind in ('enumvalue'):
        #     continue

        if eid.member in G.nodes:
            assert m.kind == G.nodes[eid.member]['kind'], f"{eid.member} already in G with kind {m.kind}, not {G.nodes[eid.member]['kind']}"
            assert m.signature == G.nodes[eid.member]['name'], f"{eid.member} already in G with name {m.signature}, not {G.nodes[eid.member]['name']}"
        else:
            G.add_node(
                eid.member,
                name=m.signature,
                kind=m.kind,
                type=EntityType.MEMBER,
            )

    refs = list(compose_structural_reference_list(db))
#    refs.extend(compose_codeline_reference_list(db))

    # Process all structural references
    for source_eid, target_eid, ref_tag in refs:
        source = db.get(source_eid)
        target = db.get(target_eid)
        if source is None or target is None:
#            print(f"Missing entity in reference: {source_eid} -> {target_eid}")
            continue
        source, target, rel_type = classify_reference(ref_tag, source, target)
        if rel_type is None:
            continue
        source_gid = source.id.member or source.id.compound
        target_gid = target.id.member or target.id.compound
        if source_gid in G and target_gid in G:
            # Add edge with relationship type as a key
            # This allows multiple edges between the same nodes with different types
            G.add_edge(source_gid, target_gid, key=rel_type, type=rel_type)

    # add location nodes and edges
    for eid, e in list(compounds.items()) + list(members.items()):
        gid = eid.member or eid.compound

        # Add location-based information
        for loc in (e.file, e.decl, e.body):
            if loc:
                loc_id = str(loc.id)
                loc_type = EntityType(loc.type)

                if loc_id in G:
                    # already exists, but replace 'file' with 'decl' or 'body'
                    if G.nodes[loc_id]['type'] == EntityType.FILE:
                        G.nodes[loc_id]['type'] = loc_type
                    elif loc_type != EntityType.FILE:
                        assert loc_type == G.nodes[loc_id]['type'], f"{loc_id} already in G with type {loc_type}, not {G.nodes[loc_id]['type']}"
                else:
                    G.add_node(
                        loc_id,
                        type=loc_type
                    )

                rel_type = Relationship.REPRESENTED_BY
                G.add_edge(loc_id, gid, key=rel_type, type=rel_type)

    return G


def create_visit_list(
    g: nx.DiGraph,
    skip_fn: lambda node: False
) -> List[Dict[str, str|int]]:

    # Track visited documentation units
    visited = set()
    unvisited = set(n for n in g.nodes)

    # # Map from member -> compound
    # compound_of = {
    #     n: next((u for u in g.predecessors(n) if g.edges[u, n].get("type") == dg.CONTAINED_BY), None)
    #     for n in member_nodes
    # }

    # # Map from compound -> list of its member nodes
    # members_by_compound = defaultdict(list)
    # for n, comp in compound_of.items():
    #     if comp:
    #         members_by_compound[comp].append(n)

    def get_unvisited_fan_in(node):
        """Number of unvisited dependencies (incoming 'requires' edges)."""
        return sum(
            1 for pred in g.predecessors(node)
            if pred not in visited 
            and not skip_fn(pred)
        #    and g.edges[pred, node].get("type") == dg.Relationship.REQUIRED_BY
        )
    def get_unvisited_fan_out(node):
        """Number of unvisited dependencies (outgoing 'requires' edges)."""
        return sum(
            1 for succ in g.successors(node)
            if succ not in visited
            and not skip_fn(succ)
        #    and g.edges[node, succ].get("type") == dg.Relationship.REQUIRED_BY and succ not in visited
        )

    unvisited_fan_in_cache = {}
    def update_unvisited_fan_in_cache():
        """Update the cache of unvisited fan-in counts."""
        unvisited_fan_in_cache.clear()
        for n in unvisited:
            unvisited_fan_in_cache[n] = get_unvisited_fan_in(n)

    update_unvisited_fan_in_cache()

    # Main scheduling loop
    schedule = []

    while len(unvisited):
        min_fan_in = min(unvisited_fan_in_cache.values(), default=0)
        nodes_in_group = [n for n, fanin in unvisited_fan_in_cache.items() if fanin == min_fan_in]

        unvisited_fan_out = {n: get_unvisited_fan_out(n) for n in nodes_in_group}

        # if we don't have any with 0 fan_in, select the one with the most fan_out and do it alone,
        # maybe we can break the cycle
        if min_fan_in > 0:
            max_fan_out = max(unvisited_fan_out.values())
            for node in nodes_in_group:
                if unvisited_fan_out[node] == max_fan_out:
                    nodes_in_group = [node]
                    break

        skipped = 0

        for node in sorted(nodes_in_group, key=lambda n: unvisited_fan_out[n], reverse=True):
            if skip_fn(node):
                skipped += 1
            else:
                schedule.append({
                    "id": node,
                    "kind": g.nodes[node].get("kind", g.nodes[node].get("type", "")),
                    "name": g.nodes[node].get("name", ""),
                    "fan_in": unvisited_fan_in_cache.get(node, 0),
                    "fan_out": unvisited_fan_out.get(node, 0),
                })
            visited.add(node)
            unvisited.remove(node)

        print(f"Skipped {skipped:>5}, Scheduled {len(nodes_in_group)-skipped:>5} nodes with fan-in {min_fan_in}. Total visited: {len(visited)}/{len(g.nodes())}")
        update_unvisited_fan_in_cache()

    print(f"Final schedule length: {len(schedule)}")
    return schedule


def fan_in(g: nx.DiGraph, node_id: str, edge_type: Relationship = None) -> list:
    """Return list of predecessors connected by the given edge type(s)."""
    if edge_type:
        if isinstance(edge_type, Relationship):
            edge_type = {edge_type}
        else:
            edge_type = set(edge_type)
    return [pred for pred in g.predecessors(node_id)
            if not edge_type or any(
                d.get("type") in edge_type
                for _, _, d in g.edges(pred, node_id, data=True)
            )]


def load_graph(gml_path: Path) -> nx.MultiDiGraph:
    """Load the dependency graph from a GML file."""
    if not gml_path.exists():
        raise FileNotFoundError(f"Graph file {gml_path} does not exist.")

    try:
        g = nx.read_gml(gml_path, destringizer=int)
    except Exception as e:
        log.error(f"Failed to read GML file {gml_path}: {e}")
        raise

    # Ensure we have a MultiDiGraph
    if not isinstance(g, nx.MultiDiGraph):
        log.info("Converting loaded graph to MultiDiGraph")
        mg = nx.MultiDiGraph()
        mg.add_nodes_from(g.nodes(data=True))
        for u, v, data in g.edges(data=True):
            mg.add_edge(u, v, **data)
        g = mg

    log.info(f"Graph loaded from {gml_path}, nodes: {len(g.nodes)}, edges: {len(g.edges)}")
    return g


def save_graph(g: nx.MultiDiGraph, gml_path: Path):
    """Export the dependency graph to a GML file."""
    nx.write_gml(g, gml_path)
    log.info(f"Graph written to {gml_path}")



def get_body_eid(db: dp.EntityDatabase, node_id: str):
    if node_id in db.member_groups:
        members = [m for m in db.member_groups[node_id] if not m.extern]
        if len(members) == 1:
            return members[0].id

        # figure out which one owns the body the most
        # simple test: the owning compound will have both a file and a body
        # location, both with the same filename and starting line
        owners: Set[dp.EntityID] = set() # just to double check
        for m in db.member_groups[node_id]:
            if m.body and m.file and m.body.fn == m.file.fn and m.body.line == m.file.line:
                owners.add(m.id)

        if len(owners) == 1:
            return owners.pop()

        cc_compounds = [m.id for m in members if m.id.compound.endswith('cc')]
        if len(cc_compounds) > 0:
            return cc_compounds[0]

        raise Exception(f"bad graph member node {node_id}, compounds = {[m.id.compound for m in members]}")
    else:
        eid = dp.EntityID.from_str(node_id)
        if eid in db.compounds:
            return eid
    raise Exception(f"bad graph node {node_id}")
