import networkx as nx
from pathlib import Path
import json
from loguru import logger as log

GRAPH_INPUT = Path("projects/doc_gen/internal/code_graph.gml")
TRAVERSAL_OUTPUT = Path("projects/doc_gen/internal/traversal_order.json")

REQUIRES = "requires"
CONTAINS = "contains"


def load_graph():
    return nx.read_gml(GRAPH_INPUT)

def break_cycles(g):
    # sccs = list(nx.strongly_connected_components(g))
    # removed_edges = []
    # for component in sccs:
    #     if len(component) > 1:
    #         sub = g.subgraph(component)
    #         back_edges = list(nx.find_cycle(sub, orientation='original'))
    #         for u, v, _ in back_edges:
    #             if g.has_edge(u, v):
    #                 g.remove_edge(u, v)
    #                 removed_edges.append((u, v))
    # return removed_edges
    """Removes a minimal feedback arc set to break all cycles."""
    from networkx.algorithms.approximation import minimum_feedback_arc_set
    feedback_edges = list(minimum_feedback_arc_set(graph))
    for u, v in feedback_edges:
        graph.remove_edge(u, v)
    return feedback_edges

def compute_traversal_order(graph):
    """
    Computes a list of member nodes such that each node appears
    after all of the nodes it depends on (via REQUIRES edges).
    Compound nodes are ignored in traversal.
    """
    # Filter to member nodes only
    member_nodes = [n for n, d in graph.nodes(data=True) if d.get("type") == "member"]
    subgraph = graph.subgraph(member_nodes).copy()

    # Keep only requires edges
    edges_to_keep = [(u, v) for u, v, d in subgraph.edges(data=True) if d.get("type") == REQUIRES]
    subgraph = nx.DiGraph()
    subgraph.add_nodes_from(member_nodes)
    subgraph.add_edges_from(edges_to_keep)

    try:
        sorted_nodes = list(nx.topological_sort(subgraph))
        log.info(f"Generated traversal order with {len(sorted_nodes)} nodes.")
        return sorted_nodes
    except nx.NetworkXUnfeasible:
        log.error("Graph has cycles; cannot perform topological sort.")
        raise


def export_traversal_order(graph, ordered_nodes):
    result = []
    for node_id in ordered_nodes:
        node = graph.nodes[node_id]
        result.append({
            "id": node_id,
            "name": node.get("name"),
            "decl_file": node.get("decl_file"),
            "decl_line": node.get("decl_line"),
            "doc_comment": node.get("doc_comment")
        })
    with open(TRAVERSAL_OUTPUT, 'w') as f:
        json.dump(result, f, indent=2)
    log.info(f"Traversal order written to {TRAVERSAL_OUTPUT}")


if __name__ == "__main__":
    log.info("Loading call graph...")
    graph = load_graph()
    print(f"graph has {len(graph.nodes)} nodes and {len(graph.edges)} edges")
    log.info("Breaking cycles...")
    removed = break_cycles(graph)
    print(f"graph has {len(graph.nodes)} nodes and {len(graph.edges)} edges")
    removed.extend(break_cycles(graph))
    print(f"graph has {len(graph.nodes)} nodes and {len(graph.edges)} edges")
    removed.extend(break_cycles(graph))
    print(f"graph has {len(graph.nodes)} nodes and {len(graph.edges)} edges")
    print(f"Removed edges: {removed}")
    log.info("Computing topological traversal order...")
    ordered_nodes = compute_traversal_order(graph)
    export_traversal_order(graph, ordered_nodes)
    log.info("Done.")