import json
import logging
import sys
from pathlib import Path
import matplotlib.pyplot as plt
import networkx as nx

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
STATIC_DIR = PROJECT_ROOT / "projects/doc_gen/internal"

call_graph_path = STATIC_DIR / "clang_call_graph.json"

# Load the GML call graph
try:
    call_graph = nx.read_gml(call_graph_path)
    print(f"Successfully loaded graph with {len(call_graph.nodes)} nodes and {len(call_graph.edges)} edges")
except Exception as e:
    print(f"Error loading graph: {e}")
    sys.exit(1)

# Define color map for different entity types
color_map = {
    "CursorKind.FUNCTION_DECL": "blue",
    "CursorKind.CXX_METHOD": "green",
    "CursorKind.CONSTRUCTOR": "purple",
    "CursorKind.DESTRUCTOR": "red",
    "CursorKind.CLASS_DECL": "orange",
    "CLASS_DEFINITION": "darkred",
    "CursorKind.STRUCT_DECL": "brown",
    "CursorKind.NAMESPACE": "lightblue",
    "CursorKind.ENUM_DECL": "pink",
    "CursorKind.TYPEDEF_DECL": "gray",
    "CursorKind.CLASS_TEMPLATE": "cyan",
    "CursorKind.UNION_DECL": "magenta",
    "CursorKind.CONVERSION_FUNCTION": "yellow",
    "CursorKind.NAMESPACE_ALIAS": "lightgreen",
    "CursorKind.MACRO_DEFINITION": "black",
    "None": "lightgray"  # Default color
}

# Find root nodes (nodes with no incoming edges)
root_nodes = [node for node in call_graph.nodes if call_graph.in_degree(node) == 0]
print(f"Root nodes (no dependencies): {len(root_nodes)} found")

# Function to get color based on entity type
def get_node_color(node):
    entity_type = call_graph.nodes[node].get("entity_type", "None")
    return color_map.get(entity_type, color_map["None"])

def walk_tree(node, indent=0, visited=None):
    if visited is None:
        visited = set()
    if node in visited:
        return
    visited.add(node)
    label = call_graph.nodes[node].get("label", node)
    entity_type = call_graph.nodes[node].get("entity_type", "None")
    color = get_node_color(node)
    print(" " * indent + f"- {label} [{entity_type}] (color: {color})")
    for child in call_graph.successors(node):
        walk_tree(child, indent + 2, visited)

# Print a few roots with entity type information
print("\nFirst 5 root nodes with entity types:")
for root in root_nodes[:5]:
    walk_tree(root)

# Draw the graph with colors
def draw_graph(graph, max_nodes=100):
    if len(graph.nodes) > max_nodes:
        print(f"Graph too large to visualize ({len(graph.nodes)} nodes). Showing a sample of {max_nodes} nodes.")
        sample_nodes = list(graph.nodes)[:max_nodes]
        graph = graph.subgraph(sample_nodes)
    
    plt.figure(figsize=(20, 12))
    pos = nx.spring_layout(graph, k=0.15, iterations=20)
    
    # Get colors for nodes based on entity type
    colors = [get_node_color(node) for node in graph.nodes]
    
    nx.draw(graph, pos, with_labels=True, node_color=colors, 
            node_size=500, font_size=8, font_weight='bold',
            edge_color='gray', width=0.5, alpha=0.8)
    
    # Add a legend for entity types
    unique_types = set(graph.nodes[node].get("entity_type", "None") for node in graph.nodes)
    legend_elements = [plt.Line2D([0], [0], marker='o', color='w', 
                                 markerfacecolor=color_map.get(t, color_map["None"]), 
                                 markersize=10, label=t)
                      for t in unique_types]
    plt.legend(handles=legend_elements, loc='upper right')
    
    plt.title(f"Call Graph Visualization (showing {len(graph.nodes)} nodes)")
    plt.tight_layout()
    output_path = STATIC_DIR / "call_graph_visualization.png"
    plt.savefig(output_path)
    print(f"Graph visualization saved to {output_path}")
    plt.close()

# Draw the graph with colored nodes
draw_graph(call_graph)

# Create a component visualization (for a specific node and its neighborhood)
def draw_component_graph(central_node, depth=2):
    """Draw a graph centered on a specific node with given traversal depth"""
    if central_node not in call_graph.nodes:
        print(f"Node '{central_node}' not found in the graph")
        return
    
    # Gather nodes within the specified depth
    component_nodes = {central_node}
    current_layer = {central_node}
    for _ in range(depth):
        next_layer = set()
        for node in current_layer:
            next_layer.update(call_graph.successors(node))
            next_layer.update(call_graph.predecessors(node))
        current_layer = next_layer - component_nodes
        component_nodes.update(current_layer)
    
    # Create the subgraph
    component_graph = call_graph.subgraph(component_nodes)
    
    # Draw the component graph
    plt.figure(figsize=(16, 12))
    pos = nx.spring_layout(component_graph, k=0.3, iterations=50)
    
    # Get colors for nodes based on entity type
    colors = [get_node_color(node) for node in component_graph.nodes]
    
    # Highlight the central node
    node_sizes = [1000 if node == central_node else 500 for node in component_graph.nodes]
    
    nx.draw(component_graph, pos, with_labels=True, node_color=colors, 
            node_size=node_sizes, font_size=8, font_weight='bold',
            edge_color='gray', width=0.5, alpha=0.8)
    
    # Add a legend for entity types
    unique_types = set(component_graph.nodes[node].get("entity_type", "None") for node in component_graph.nodes)
    legend_elements = [plt.Line2D([0], [0], marker='o', color='w', 
                                 markerfacecolor=color_map.get(t, color_map["None"]), 
                                 markersize=10, label=t)
                      for t in unique_types]
    plt.legend(handles=legend_elements, loc='upper right')
    
    plt.title(f"Component Graph for '{central_node}' (depth={depth})")
    plt.tight_layout()
    safe_name = central_node.replace('::', '_').replace('<', '_').replace('>', '_')
    output_path = STATIC_DIR / f"component_graph_{safe_name}.png"
    plt.savefig(output_path)
    print(f"Component graph visualization saved to {output_path}")
    plt.close()

# Uncomment to visualize a specific component (e.g., a class or function)
# draw_component_graph("Area::reset", depth=2)
