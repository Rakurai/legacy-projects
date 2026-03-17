"""
Hierarchy Builder Module

This module contains functionality for organizing subsystems into a hierarchical structure
and generating hierarchical documentation.
"""

from collections import defaultdict, Counter
from typing import Dict, List, Set, Tuple, Any, Optional
import networkx as nx
import json
from pathlib import Path
import numpy as np
# Note: community detection can use networkx's built-in algorithms instead

from . import subsystem_utils as su

class HierarchyNode:
    """Class representing a node in the hierarchy tree."""
    
    def __init__(self, name: str, node_id: str = None, size: int = None):
        """Initialize a hierarchy node.
        
        Args:
            name: Name of the node
            node_id: ID of the node (may be None for non-leaf nodes)
            size: Size metric (may be None for non-leaf nodes)
        """
        self.name = name
        self.id = node_id
        self.size = size
        self.children = []
        self.parent = None
        
    def add_child(self, child: 'HierarchyNode'):
        """Add a child node to this node."""
        child.parent = self
        self.children.append(child)
        
    def to_dict(self) -> Dict:
        """Convert the node and its children to a dictionary."""
        result = {"name": self.name}
        
        if self.id is not None:
            result["id"] = self.id
            
        if self.size is not None:
            result["size"] = self.size
            
        if self.children:
            result["children"] = [child.to_dict() for child in self.children]
            
        return result
        
    @classmethod
    def from_dict(cls, data: Dict) -> 'HierarchyNode':
        """Create a hierarchy tree from a dictionary."""
        node = cls(data["name"], data.get("id"), data.get("size"))
        
        for child_data in data.get("children", []):
            child = cls.from_dict(child_data)
            node.add_child(child)
            
        return node

def identify_subsystem_dependencies(
    subsystem: su.Subsystem, 
    entity_db, 
    graph: nx.Graph, 
    all_subsystems: Dict[str, su.Subsystem]
) -> Dict[str, int]:
    """
    Identify dependencies between subsystems.
    
    Args:
        subsystem: Subsystem to analyze
        entity_db: Entity database
        graph: NetworkX dependency graph
        all_subsystems: Dictionary of all subsystems
        
    Returns:
        Dictionary mapping subsystem IDs to dependency counts
    """
    # Create a mapping from entity to subsystem
    entity_to_subsystem = {}
    for s_id, s in all_subsystems.items():
        for entity in s.nodes:
            entity_to_subsystem[entity] = s_id
            
    # Identify subsystem dependencies
    dependencies = defaultdict(int)
    
    for entity in subsystem.nodes:
        # Check outgoing edges (dependencies)
        for target in graph.successors(entity):
            if target in entity_to_subsystem and entity_to_subsystem[target] != subsystem.subsystem_id:
                target_subsystem = entity_to_subsystem[target]
                dependencies[target_subsystem] += 1
    
    return dependencies

def build_subsystem_dependency_graph(
    subsystems: Dict[str, su.Subsystem], 
    entity_db, 
    graph: nx.Graph
) -> nx.DiGraph:
    """
    Build a graph where nodes are subsystems and edges represent dependencies.
    
    Args:
        subsystems: Dictionary of subsystem objects
        entity_db: Entity database
        graph: NetworkX dependency graph
        
    Returns:
        NetworkX directed graph of subsystem dependencies
    """
    # Create a new graph
    subsystem_graph = nx.DiGraph()
    
    # Add nodes
    for s_id, subsystem in subsystems.items():
        subsystem_graph.add_node(
            s_id, 
            name=subsystem.name, 
            classification=subsystem.classification,
            size=len(subsystem.nodes)
        )
    
    # Add edges based on dependencies
    for s_id, subsystem in subsystems.items():
        deps = identify_subsystem_dependencies(subsystem, entity_db, graph, subsystems)
        for target_id, weight in deps.items():
            subsystem_graph.add_edge(s_id, target_id, weight=weight)
    
    return subsystem_graph

def create_hierarchical_model(
    subsystems: Dict[str, su.Subsystem], 
    entity_db, 
    graph: nx.Graph,
    max_depth: int = 3
) -> Tuple[Dict, nx.DiGraph]:
    """
    Create a hierarchical model of subsystems.
    
    Args:
        subsystems: Dictionary of subsystem objects
        entity_db: Entity database
        graph: NetworkX dependency graph
        max_depth: Maximum depth of the hierarchy
        
    Returns:
        Tuple of (hierarchy dict, subsystem dependency graph)
    """
    # Build subsystem dependency graph
    subsystem_graph = build_subsystem_dependency_graph(subsystems, entity_db, graph)
    
    # Create root node
    root = HierarchyNode("Legacy MUD System")
    
    # Create first level based on classification
    classification_nodes = {}
    by_classification = defaultdict(list)
    
    for s_id, subsystem in subsystems.items():
        by_classification[subsystem.classification].append(s_id)
    
    for classification, s_ids in by_classification.items():
        class_node = HierarchyNode(classification)
        root.add_child(class_node)
        classification_nodes[classification] = class_node
    
    # Create second level based on centrality scores and dependencies
    for classification, s_ids in by_classification.items():
        class_node = classification_nodes[classification]
        
        if len(s_ids) <= 5:
            # Small classification - add subsystems directly
            for s_id in s_ids:
                subsystem = subsystems[s_id]
                leaf_node = HierarchyNode(subsystem.name, s_id, len(subsystem.nodes))
                class_node.add_child(leaf_node)
        else:
            # Larger classification - create subgroups
            subgraph = subsystem_graph.subgraph(s_ids)
            
            # Try to identify communities within this classification
            try:
                # Use NetworkX's built-in community detection
                undirected_subgraph = subgraph.to_undirected()
                if nx.__version__ >= '2.8.0':
                    from networkx.algorithms.community import greedy_modularity_communities
                    communities_generator = greedy_modularity_communities(undirected_subgraph)
                    communities = {i: list(comm) for i, comm in enumerate(communities_generator)}
                else:
                    # Fallback for older NetworkX versions
                    # Simple clustering based on connected components
                    communities = {i: list(comp) for i, comp in 
                                enumerate(nx.connected_components(undirected_subgraph))}
                
                # Create subgroups
                for comm_id, sub_s_ids in communities.items():
                    if len(sub_s_ids) == 1:
                        # Single subsystem, add directly to classification
                        s_id = sub_s_ids[0]
                        subsystem = subsystems[s_id]
                        leaf_node = HierarchyNode(subsystem.name, s_id, len(subsystem.nodes))
                        class_node.add_child(leaf_node)
                    else:
                        # Create a subgroup
                        # Find most central subsystem to name the group
                        subgroup_graph = subgraph.subgraph(sub_s_ids)
                        centrality = nx.betweenness_centrality(subgroup_graph)
                        central_id = max(centrality.items(), key=lambda x: x[1])[0]
                        central_subsystem = subsystems[central_id]
                        
                        subgroup_name = f"{central_subsystem.name} Group"
                        subgroup_node = HierarchyNode(subgroup_name)
                        class_node.add_child(subgroup_node)
                        
                        # Add subsystems to subgroup
                        for s_id in sub_s_ids:
                            subsystem = subsystems[s_id]
                            leaf_node = HierarchyNode(subsystem.name, s_id, len(subsystem.nodes))
                            subgroup_node.add_child(leaf_node)
            except:
                # Fallback if community detection fails
                for s_id in s_ids:
                    subsystem = subsystems[s_id]
                    leaf_node = HierarchyNode(subsystem.name, s_id, len(subsystem.nodes))
                    class_node.add_child(leaf_node)
    
    # Convert to dict
    hierarchy = root.to_dict()
    
    return hierarchy, subsystem_graph

def format_hierarchy_as_markdown(node: Dict, level: int = 0) -> List[str]:
    """
    Format a hierarchy as a nested Markdown list.
    
    Args:
        node: Hierarchy node dictionary
        level: Current indentation level
        
    Returns:
        List of formatted Markdown lines
    """
    lines = []
    indent = "  " * level
    
    if "children" in node:
        lines.append(f"{indent}- **{node['name']}**\n")
        for child in node["children"]:
            lines.extend(format_hierarchy_as_markdown(child, level + 1))
    else:
        # Leaf node
        size_str = f" ({node.get('size', '?')} entities)" if 'size' in node else ""
        lines.append(f"{indent}- {node['name']}{size_str}\n")
        
    return lines

def generate_hierarchical_view_document(
    hierarchy: Dict, 
    subsystems: Dict[str, su.Subsystem],
    subsystem_graph: nx.DiGraph,
    entity_db,
    graph: nx.Graph
) -> str:
    """
    Generate a markdown document describing the system hierarchy.
    
    Args:
        hierarchy: Hierarchy dictionary
        subsystems: Dictionary of subsystem objects
        subsystem_graph: Subsystem dependency graph
        entity_db: Entity database
        graph: NetworkX dependency graph
        
    Returns:
        Markdown content for the hierarchical view document
    """
    doc_lines = [
        "# Hierarchical System View\n",
        "\n## Overview\n",
        "This document presents a hierarchical view of the Legacy MUD system, ",
        "organizing subsystems into logical groups based on their function and relationships.\n",
        "\n## Hierarchy\n"
    ]
    
    # Format hierarchy as nested list
    doc_lines.extend(format_hierarchy_as_markdown(hierarchy))
    
    # Add dependency information
    doc_lines.append("\n## Subsystem Relationships\n")
    doc_lines.append("The following sections describe the relationships between subsystems.\n")
    
    # Get child nodes that are classification groups
    classification_groups = hierarchy.get("children", [])
    
    for group in sorted(classification_groups, key=lambda x: x["name"]):
        classification = group["name"]
        doc_lines.append(f"\n### {classification} Subsystems\n")
        
        # Process all subsystems in this classification
        for child in group.get("children", []):
            # Check if this is a subgroup or a leaf
            if "children" in child:
                # This is a subgroup
                doc_lines.append(f"#### {child['name']}\n")
                
                # Process all subsystems in the subgroup
                for leaf in child.get("children", []):
                    s_id = leaf.get("id")
                    if s_id and s_id in subsystems:
                        process_subsystem_dependencies(s_id, subsystems, entity_db, graph, doc_lines)
            else:
                # This is a leaf (direct subsystem)
                s_id = child.get("id")
                if s_id and s_id in subsystems:
                    s_name = subsystems[s_id].name
                    doc_lines.append(f"#### {s_name}\n")
                    process_subsystem_dependencies(s_id, subsystems, entity_db, graph, doc_lines)
    
    return "\n".join(doc_lines)

def process_subsystem_dependencies(
    s_id: str,
    subsystems: Dict[str, su.Subsystem],
    entity_db,
    graph: nx.Graph,
    doc_lines: List[str]
):
    """
    Process and document a subsystem's dependencies.
    
    Args:
        s_id: Subsystem ID
        subsystems: Dictionary of subsystem objects
        entity_db: Entity database
        graph: NetworkX dependency graph
        doc_lines: List of document lines to append to
    """
    s = subsystems[s_id]
    deps = identify_subsystem_dependencies(s, entity_db, graph, subsystems)
    
    if deps:
        doc_lines.append("**Dependencies**:\n")
        sorted_deps = sorted([(subsystems[dep_id].name, count) 
                            for dep_id, count in deps.items() if dep_id in subsystems],
                           key=lambda x: x[1], reverse=True)
        
        for dep_name, count in sorted_deps:
            doc_lines.append(f"- {dep_name} ({count} connections)")
        doc_lines.append("\n")
    else:
        doc_lines.append("No external dependencies.\n\n")
