"""
Utility functions for subsystem discovery and analysis.

This module provides shared functionality for loading and parsing resources,
standard data structures for representing clusters and subsystems,
and resource validation and error handling.
"""

import os
import json
import networkx as nx
import numpy as np
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any, Optional, Union
import doxygen_parse
import doxygen_graph


# Paths
AI_DIR = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CONTEXT_DIR = AI_DIR / "context"
INTERNAL_DIR = CONTEXT_DIR / "internal"
DOCS_DIR = AI_DIR / "docs"
SUBSYSTEMS_DIR = DOCS_DIR / "subsystems"
VISUALIZATIONS_DIR = AI_DIR / "visualizations"

# Ensure directories exist
SUBSYSTEMS_DIR.mkdir(exist_ok=True, parents=True)
VISUALIZATIONS_DIR.mkdir(exist_ok=True, parents=True)

# Default paths for resources
DEFAULT_GRAPH_PATH = INTERNAL_DIR / "code_graph.gml"
DEFAULT_DB_PATH = INTERNAL_DIR / "code_graph.json"

# Standard data structures
NodeID = str
ClusterID = int
SubsystemID = str

class Cluster:
    """Represents a cluster of related nodes."""
    
    def __init__(self, cluster_id: ClusterID, nodes: Set[NodeID], 
                 source: str = None, metadata: Dict = None):
        """
        Initialize a cluster.
        
        Args:
            cluster_id: Unique identifier for the cluster
            nodes: Set of node IDs contained in the cluster
            source: Source of the clustering (e.g., "structural", "semantic")
            metadata: Additional metadata about the cluster
        """
        self.cluster_id = cluster_id
        self.nodes = nodes
        self.source = source
        self.metadata = metadata or {}
        
    def __len__(self):
        return len(self.nodes)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "cluster_id": self.cluster_id,
            "source": self.source,
            "node_count": len(self.nodes),
            "nodes": list(self.nodes),
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "Cluster":
        """Create a Cluster object from a dictionary."""
        return cls(
            cluster_id=data["cluster_id"],
            nodes=set(data["nodes"]),
            source=data.get("source"),
            metadata=data.get("metadata", {})
        )

class Subsystem:
    """Represents a subsystem composed of related clusters and entities."""
    
    def __init__(self, subsystem_id: SubsystemID, name: str,
                 nodes: Set[NodeID] = None, 
                 classification: str = None,
                 description: str = None,
                 parent: Optional[SubsystemID] = None,
                 children: Set[SubsystemID] = None,
                 metadata: Dict = None):
        """
        Initialize a subsystem.
        
        Args:
            subsystem_id: Unique identifier for the subsystem
            name: Human-readable name for the subsystem
            nodes: Set of node IDs contained in the subsystem
            classification: Classification (e.g., "core", "interface")
            description: Human-readable description
            parent: ID of parent subsystem (if any)
            children: Set of child subsystem IDs
            metadata: Additional metadata
        """
        self.subsystem_id = subsystem_id
        self.name = name
        self.nodes = nodes or set()
        self.classification = classification
        self.description = description
        self.parent = parent
        self.children = children or set()
        self.metadata = metadata or {}
        
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "subsystem_id": self.subsystem_id,
            "name": self.name,
            "classification": self.classification,
            "description": self.description,
            "node_count": len(self.nodes),
            "nodes": list(self.nodes),
            "parent": self.parent,
            "children": list(self.children),
            "metadata": self.metadata
        }
        
    @classmethod
    def from_dict(cls, data: Dict) -> "Subsystem":
        """Create a Subsystem object from a dictionary."""
        return cls(
            subsystem_id=data["subsystem_id"],
            name=data["name"],
            nodes=set(data.get("nodes", [])),
            classification=data.get("classification"),
            description=data.get("description"),
            parent=data.get("parent"),
            children=set(data.get("children", [])),
            metadata=data.get("metadata", {})
        )

def get_entity(entity_db: doxygen_parse.EntityDatabase, node_id: NodeID) -> Optional[doxygen_parse.DoxygenEntity]:
    """
    Get the entity corresponding to a node ID.
    
    Args:
        entity_db: The entity database to look up the entity.
        node_id: The node ID to look up.
        
    Returns:
        The corresponding Entity object, or None if not found.
    """
    eid = doxygen_graph.get_body_eid(entity_db, node_id)
    return entity_db.get(eid)

# Resource loading helpers
def load_graph(graph_path: Path = None) -> nx.MultiDiGraph:
    """
    Load the NetworkX graph.
    
    Args:
        graph_path: Path to the graph file (defaults to DEFAULT_GRAPH_PATH)
        
    Returns:
        The loaded graph as a MultiDiGraph
    """
    graph_path = graph_path or DEFAULT_GRAPH_PATH
    try:
        g = doxygen_graph.load_graph(graph_path)
        subgraph_nodes = [
            n for n, data in g.nodes(data=True)
            if data.get('type') in {doxygen_graph.EntityType.COMPOUND, doxygen_graph.EntityType.MEMBER}
            and data.get('kind') not in {
                'dir', 'file', 'namespace'
            }
        ]
        return g.subgraph(subgraph_nodes).copy()
    except Exception as e:
        raise ValueError(f"Failed to load graph from {graph_path}: {e}")

def load_entity_db(entity_db_path: Path) -> doxygen_parse.EntityDatabase:
    """
    Load the entity database from a JSON file.
    
    Args:
        entity_db_path: Path to the JSON file containing the entity database
        
    Returns:
        The loaded entity database
    """
    try:
        return doxygen_parse.load_db(entity_db_path)
    except Exception as e:
        raise ValueError(f"Failed to load entity database from {entity_db_path}: {e}")

def load_clusters(file_path: Path) -> Dict[ClusterID, Cluster]:
    """
    Load clusters from a JSON file.
    
    Args:
        file_path: Path to the JSON file containing clusters
        
    Returns:
        Dictionary mapping cluster IDs to Cluster objects
    """
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        clusters = {}
        for cluster_data in data["clusters"]:
            cluster = Cluster.from_dict(cluster_data)
            clusters[cluster.cluster_id] = cluster
        
        return clusters
    except Exception as e:
        raise ValueError(f"Failed to load clusters from {file_path}: {e}")

def numpy_safe_encoder(obj):
    """Convert NumPy types to Python built-in types for JSON serialization."""
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, np.floating):
        return float(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, np.bool_):
        return bool(obj)
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

def save_clusters(clusters: Dict[ClusterID, Cluster], file_path: Path, 
                  metadata: Dict = None) -> None:
    """
    Save clusters to a JSON file.
    
    Args:
        clusters: Dictionary mapping cluster IDs to Cluster objects
        file_path: Path to save the JSON file
        metadata: Additional metadata to include in the file
    """
    # Convert any NumPy types in metadata to Python built-in types
    if metadata:
        metadata = json.loads(json.dumps(metadata, default=numpy_safe_encoder))
    
    data = {
        "metadata": metadata or {},
        "cluster_count": len(clusters),
        "clusters": [cluster.to_dict() for cluster in clusters.values()]
    }
    
    try:
        # Ensure directory exists
        file_path.parent.mkdir(exist_ok=True, parents=True)
        
        with open(file_path, 'w') as f:
            json.dump(data, f, default=numpy_safe_encoder, indent=2)
    except Exception as e:
        raise ValueError(f"Failed to save clusters to {file_path}: {e}")

def load_subsystems(file_path: Path) -> Dict[SubsystemID, Subsystem]:
    """
    Load subsystems from a JSON file.
    
    Args:
        file_path: Path to the JSON file containing subsystems
        
    Returns:
        Dictionary mapping subsystem IDs to Subsystem objects
    """
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        subsystems = {}
        for subsystem_data in data["subsystems"]:
            subsystem = Subsystem.from_dict(subsystem_data)
            subsystems[subsystem.subsystem_id] = subsystem
        
        return subsystems
    except Exception as e:
        raise ValueError(f"Failed to load subsystems from {file_path}: {e}")

def save_subsystems(subsystems: Dict[SubsystemID, Subsystem], file_path: Path,
                   metadata: Dict = None) -> None:
    """
    Save subsystems to a JSON file.
    
    Args:
        subsystems: Dictionary mapping subsystem IDs to Subsystem objects
        file_path: Path to save the JSON file
        metadata: Additional metadata to include in the file
    """
    data = {
        "metadata": metadata or {},
        "subsystem_count": len(subsystems),
        "subsystems": [subsystem.to_dict() for subsystem in subsystems.values()]
    }
    
    try:
        # Ensure directory exists
        file_path.parent.mkdir(exist_ok=True, parents=True)
        
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        raise ValueError(f"Failed to save subsystems to {file_path}: {e}")

def evaluate_clustering_quality(graph: nx.Graph, clusters: Dict[ClusterID, Cluster]) -> Dict:
    """
    Evaluate the quality of clustering.
    
    Args:
        graph: NetworkX graph representing the code
        clusters: Dictionary mapping cluster IDs to Cluster objects
        
    Returns:
        Dictionary with quality metrics
    """
    # Implementation would calculate metrics like:
    # - Modularity
    # - Silhouette coefficient
    # - Inter-cluster vs intra-cluster edges
    # Placeholder for now
    return {
        "cluster_count": len(clusters),
        "average_cluster_size": np.mean([len(c.entities) for c in clusters.values()]),
        "min_cluster_size": min([len(c.entities) for c in clusters.values()]),
        "max_cluster_size": max([len(c.entities) for c in clusters.values()]),
    }

def create_markdown_report(title: str, content: str, file_path: Path) -> None:
    """
    Create a Markdown report file.
    
    Args:
        title: Title of the report
        content: Markdown content
        file_path: Path to save the report
    """
    try:
        # Ensure directory exists
        file_path.parent.mkdir(exist_ok=True, parents=True)
        
        with open(file_path, 'w') as f:
            f.write(f"# {title}\n\n")
            f.write(content)
    except Exception as e:
        raise ValueError(f"Failed to create report at {file_path}: {e}")
