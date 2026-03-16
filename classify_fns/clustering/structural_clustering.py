"""
Structural clustering module for subsystem discovery.

This module provides functionality to:
1. Apply community detection algorithms (Leiden, Louvain) to the code dependency graph
2. Filter utility nodes that might distort cluster boundaries
3. Evaluate clustering quality with various metrics
"""

import networkx as nx
import numpy as np
from typing import Callable, Dict, List, Set, Tuple, Any, Optional
from collections import defaultdict
import leidenalg as la
import igraph as ig
from loguru import logger as log
import time

import subsystem_utils as su
import json


def identify_utility_nodes(graph: nx.DiGraph, utility_threshold_fn, initial_clustering: Dict[su.NodeID, su.ClusterID]) -> Set[su.NodeID]:
    """
    Identify utility nodes that are highly connected and likely to be utilities, using initial clustering.

    Args:
        graph: Directed graph of code dependencies
        initial_clustering: Initial clustering results to identify unique cluster connections
        threshold: Threshold percentile for considering a node as utility

    Returns:
        Set of node IDs identified as utilities
    """
    log.info(f"Identifying utility nodes")
    start_time = time.time()

    # Calculate connectivity metrics
    log.info(f"Calculating in/out degree for {len(graph.nodes())} nodes")
    in_degree = dict(graph.in_degree())
    out_degree = dict(graph.out_degree())

    log.info("Computing betweenness centrality (this may take a while for large graphs)")
    betweenness = nx.betweenness_centrality(graph)

    # Calculate a utility score
    utility_values = {}
    for node in graph.nodes():
        if graph.nodes[node].get('kind') not in ('function', 'define', 'class', 'enum'):
            continue

        etypes = ('calls', 'uses', 'inherits', 'includes')

        # Count incoming and outgoing edges grouped by edge type
        fan_in = {etype: set() for etype in etypes}
        fan_out = {etype: set() for etype in etypes}
        fan_in_clusters = {etype: set([node]) for etype in etypes}
        fan_out_clusters = {etype: set() for etype in etypes}
        for p in graph.predecessors(node):
            edge_data = graph.get_edge_data(p, node)
            for etype in etypes:
                if etype in edge_data:
                    fan_in[etype].add(p)
                    fan_in_clusters[etype].add(initial_clustering.get(p))
        for s in graph.successors(node):
            edge_data = graph.get_edge_data(node, s)
            for etype in etypes:
                if etype in edge_data:
                    fan_out[etype].add(s)
                    fan_out_clusters[etype].add(initial_clustering.get(s))

        utility_values[node] = {
            'between': betweenness.get(node, 0),
        }
        for etype in etypes:
            utility_values[node][f'fan_in_{etype}'] = len(fan_in[etype])
            utility_values[node][f'fan_in_clusters_{etype}'] = len(fan_in_clusters[etype])
            utility_values[node][f'fan_out_{etype}'] = len(fan_out[etype])
            utility_values[node][f'fan_out_clusters_{etype}'] = len(fan_out_clusters[etype])
            utility_values[node][f'overlap_{etype}'] = len(fan_out_clusters[etype] & fan_in_clusters[etype])

    max_values = {
        k: max(utility_values[node][k] for node in utility_values) for k in utility_values[next(iter(utility_values))].keys()
    }
    utility_score = {
        node: {
            k: value / max_values[k] if max_values[k] > 0 else 0
            for k, value in values.items()
        } for node, values in utility_values.items()
    }

    # Weighted combination of metrics
    for node, values in utility_values.items():
        # overlap_score: 1 if overlap == max(unique_fan_out, unique_fan_in), 0 if overlap == unique_fan_out + unique_fan_in
        for etype in etypes:
            max_fan = max(values[f'fan_out_clusters_{etype}'], values[f'fan_in_clusters_{etype}'])
            utility_score[node][f'overlap_{etype}'] = values[f'overlap_{etype}'] / max_fan if max_fan > 0 else 0

    # Save utility_score to a JSON file
    utility_score_path = "utility_scores.json"
    with open(utility_score_path, "w") as f:
        json.dump({str(k): v for k, v in utility_score.items()}, f, indent=2)
    log.info(f"Utility scores saved to {utility_score_path}")

    # Get nodes above threshold
    # sorted_nodes = sorted(utility_score.items(), key=lambda x: x[1]['sum'], reverse=True)
    # threshold_idx = int(len(sorted_nodes) * threshold)
    # thresholded = sorted_nodes[:threshold_idx]
    # for node, score in thresholded:
    #     log.info(
    #         f" - {score['sum']:0.4f} "
    #         f"(in={score['in']:.2f}, out={score['out']:.2f}, between={score['between']:.2f}, "
    #         f"unique_fan_out={score['unique_fan_out']:.2f}, unique_fan_in={score['unique_fan_in']:.2f}, overlap={score['overlap']:.2f}) "
    #         f"- [{graph.nodes[node].get('kind')}] {graph.nodes[node].get('name')}"
    #     )
    utility_nodes = {node for node, score in utility_score.items() if utility_threshold_fn(score)}

    elapsed_time = time.time() - start_time
    log.info(f"Identified {len(utility_nodes)} utility nodes in {elapsed_time:.2f}s")
    return utility_nodes

def apply_leiden_clustering(graph: nx.Graph, resolution: float = 1.0) -> Dict[su.NodeID, su.ClusterID]:
    """
    Apply the Leiden community detection algorithm.
    
    Args:
        graph: NetworkX graph (can be DiGraph or MultiDiGraph)
        resolution: Resolution parameter (higher -> more communities)
        
    Returns:
        Dictionary mapping node ID to cluster ID
    """
    start_time = time.time()
    log.info(f"Applying Leiden clustering with resolution={resolution} on graph with {len(graph.nodes())} nodes and {len(graph.edges())} edges")

    filtered_graph = nx.Graph()

    for u, v, data in graph.edges(data=True):
        if data.get('type') not in ('calls', 'uses', 'inherits'):
            continue

        # Ensure we copy node attributes
        if not filtered_graph.has_node(u):
            filtered_graph.add_node(u, **graph.nodes[u])
        if not filtered_graph.has_node(v):
            filtered_graph.add_node(v, **graph.nodes[v])

        if not filtered_graph.has_edge(u, v):
            weight = data.get("weight", 1.0)
            filtered_graph.add_edge(u, v, weight=weight)

    log.info(f"Filtered graph created with {len(filtered_graph.nodes())} nodes and {len(filtered_graph.edges())} edges")

    # Convert NetworkX graph to igraph
    log.info("Converting NetworkX graph to iGraph format")
    node_map: Dict[su.NodeID, int] = {node: i for i, node in enumerate(filtered_graph.nodes())}
    reverse_map: Dict[int, su.NodeID] = {i: node for node, i in node_map.items()}

    edges: List[Tuple[int, int]] = [(node_map[u], node_map[v]) for u, v in filtered_graph.edges()]
    ig_graph = ig.Graph(n=len(node_map), edges=edges)
    
    # Run Leiden algorithm
    log.info("Running Leiden community detection algorithm")
    # ModularityVertexPartition doesn't take resolution_parameter
    # Use RBConfigurationVertexPartition instead which does support resolution parameter
    partition = la.find_partition(
        ig_graph, 
        n_iterations=-1,
        partition_type=la.RBConfigurationVertexPartition, 
        resolution_parameter=resolution
    )
    
    # Map back to original node IDs
    clusters: Dict[su.NodeID, su.ClusterID] = {}
    for i, cluster in enumerate(partition):
        for node_idx in cluster:
            node_id = reverse_map[node_idx]
            clusters[node_id] = i
    
    elapsed_time = time.time() - start_time
    log.info(f"Leiden clustering completed in {elapsed_time:.2f}s. Found {len(set(clusters.values()))} communities")
            
    return clusters

def create_filtered_graph(graph: nx.DiGraph, utility_nodes: Set[su.NodeID]) -> nx.DiGraph:
    """
    Create a filtered graph with utility nodes removed.
    
    Args:
        graph: Original graph
        utility_nodes: Set of utility node IDs to filter out
        
    Returns:
        Filtered graph
    """
    filtered_graph = graph.copy()
    filtered_graph.remove_nodes_from(utility_nodes)
    return filtered_graph

def calculate_modularity(graph: nx.Graph, clustering: Dict[su.NodeID, su.ClusterID]) -> float:
    """
    Calculate modularity of a graph clustering.
    
    Args:
        graph: NetworkX graph
        clustering: Dictionary mapping node ID to cluster ID
        
    Returns:
        Modularity score (higher is better)
    """
    if isinstance(graph, nx.DiGraph):
        graph = graph.to_undirected()
        
    # Group nodes by cluster
    communities: Dict[su.ClusterID, List[su.NodeID]] = defaultdict(list)
    for node_id, cluster_id in clustering.items():
        communities[cluster_id].append(node_id)

    # Use NetworkX's built-in modularity function
    return nx.algorithms.community.modularity(
        graph, 
        communities=list(communities.values())
    )

def calculate_coverage(graph: nx.Graph, clustering: Dict[su.NodeID, su.ClusterID]) -> float:
    """
    Calculate coverage (fraction of edges within communities).
    
    Args:
        graph: NetworkX graph
        clustering: Dictionary mapping node ID to cluster ID
        
    Returns:
        Coverage score (higher is better)
    """
    if isinstance(graph, nx.DiGraph):
        graph = graph.to_undirected()
    
    internal_edges = 0
    total_edges = graph.number_of_edges()
    
    for u, v in graph.edges():
        if u in clustering and v in clustering and clustering[u] == clustering[v]:
            internal_edges += 1
            
    return internal_edges / total_edges if total_edges > 0 else 0

def evaluate_clustering(graph: nx.Graph, clustering: Dict[su.NodeID, su.ClusterID]) -> Dict[str, float]:
    """
    Evaluate a graph clustering with multiple metrics.
    
    Args:
        graph: NetworkX graph
        clustering: Dictionary mapping node ID to cluster ID
        
    Returns:
        Dictionary of evaluation metrics
    """
    start_time = time.time()
    log.info("Evaluating clustering quality metrics")
    
    # Count clusters
    cluster_ids: Set[su.ClusterID] = set(clustering.values())
    cluster_count = len(cluster_ids)
    
    # Calculate cluster sizes
    cluster_sizes: Dict[su.ClusterID, int] = defaultdict(int)
    for cluster_id in clustering.values():
        cluster_sizes[cluster_id] += 1
    
    size_values: List[int] = list(cluster_sizes.values())
    
    # Calculate quality metrics
    log.info("Calculating modularity score")
    modularity = calculate_modularity(graph, clustering)
    
    log.info("Calculating coverage score")
    coverage = calculate_coverage(graph, clustering)
    
    result = {
        "cluster_count": cluster_count,
        "avg_cluster_size": np.mean(size_values),
        "min_cluster_size": min(size_values),
        "max_cluster_size": max(size_values),
        "size_std_dev": np.std(size_values),
        "modularity": modularity,
        "coverage": coverage
    }
    
    elapsed_time = time.time() - start_time
    log.info(f"Evaluation completed in {elapsed_time:.2f}s. Modularity: {modularity:.4f}, Coverage: {coverage:.4f}")
    
    return result

def run_structural_clustering(graph: nx.DiGraph, 
                             utility_threshold_fn: Callable[[Dict[str, float]], bool],
                             filter_utilities: bool = True,
                             resolution: float = 1.0) -> Tuple[Dict[su.NodeID, su.ClusterID], Dict]:
    """
    Run the full structural clustering pipeline using a two-stage process.

    Args:
        graph: NetworkX directed graph
        utility_threshold: Threshold for identifying utility nodes
        filter_utilities: Whether to filter utility nodes
        resolution: Resolution parameter for Leiden algorithm

    Returns:
        Tuple of (node_to_cluster_mapping, metadata)
    """
    start_time = time.time()
    log.info(f"Starting structural clustering on graph with {len(graph.nodes())} nodes and {len(graph.edges())} edges")
    log.info(f"Configuration: algorithm=leiden, filter_utilities={filter_utilities}, resolution={resolution}")

    metadata = {
        "algorithm": "leiden",
        "filter_utilities": filter_utilities,
        "resolution": resolution
    }

    # Stage 1: Initial clustering (with utility nodes)
    log.info("Stage 1: Initial clustering (including utility nodes)")
    initial_clustering: Dict[su.NodeID, su.ClusterID] = apply_leiden_clustering(graph.to_undirected(), resolution=resolution)
    metadata["initial_cluster_count"] = len(set(initial_clustering.values()))

    if filter_utilities:
        # Identify utility nodes based on initial clustering
        utility_nodes: Set[su.NodeID] = identify_utility_nodes(graph, utility_threshold_fn, initial_clustering)
        metadata["utility_node_count"] = len(utility_nodes)

        # Stage 2: Refined clustering (without utility nodes)
        log.info("Stage 2: Refined clustering (excluding utility nodes)")
        working_graph = create_filtered_graph(graph, utility_nodes) if filter_utilities else graph
        refined_clustering: Dict[su.NodeID, su.ClusterID] = apply_leiden_clustering(working_graph.to_undirected(), resolution=resolution)
        metadata["refined_cluster_count"] = len(set(refined_clustering.values()))

        # Reassign utility nodes to clusters based on initial clustering
        log.info("Reassigning utility nodes to clusters based on initial clustering")
        for node_id in utility_nodes:
            if node_id in graph:
                neighbors: List[su.NodeID] = list(graph.predecessors(node_id)) + list(graph.successors(node_id))
                neighbor_clusters: List[su.ClusterID] = [refined_clustering.get(n) for n in neighbors if n in refined_clustering]

                if neighbor_clusters:
                    # Assign to the most common cluster among neighbors
                    cluster_counts: Dict[su.ClusterID, int] = defaultdict(int)
                    for c in neighbor_clusters:
                        cluster_counts[c] += 1
                    refined_clustering[node_id] = max(cluster_counts.items(), key=lambda x: x[1])[0]
    else:
        refined_clustering = initial_clustering
        metadata["utility_node_count"] = 0
        metadata["refined_cluster_count"] = metadata["initial_cluster_count"]

    total_time = time.time() - start_time
    log.info(f"Structural clustering completed in {total_time:.2f}s. Found {len(set(refined_clustering.values()))} clusters")

    return refined_clustering, metadata

def clustering_to_cluster_objects(clustering: Dict[su.NodeID, su.ClusterID], 
                                source: str = "structural") -> Dict[su.ClusterID, su.Cluster]:
    """
    Convert a clustering dictionary to Cluster objects.
    
    Args:
        clustering: Dictionary mapping node ID to cluster ID
        source: Source of the clustering
        
    Returns:
        Dictionary mapping cluster ID to Cluster object
    """
    log.info(f"Converting {len(clustering)} nodes from {source} clustering to Cluster objects")
    
    # Group nodes by cluster
    clusters_map: Dict[su.ClusterID, Set[su.NodeID]] = defaultdict(set)
    for node, cluster_id in clustering.items():
        clusters_map[cluster_id].add(node)
    
    # Create Cluster objects
    result: Dict[su.ClusterID, su.Cluster] = {}
    for cluster_id, node_ids in clusters_map.items():
        result[cluster_id] = su.Cluster(
            cluster_id=cluster_id,
            nodes=node_ids,
            source=source
        )
    
    # Log cluster size distribution
    sizes = [len(c.nodes) for c in result.values()]
    log.info(f"Created {len(result)} cluster objects with size distribution: "
               f"min={min(sizes)}, max={max(sizes)}, avg={sum(sizes)/len(sizes):.1f}")
    
    return result
