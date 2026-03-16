"""
Cluster integration module for subsystem discovery.

This module provides functionality to:
1. Combine results from different clustering approaches
2. Generate consensus clusters
3. Resolve conflicts between different clustering methods
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Set, Tuple, Any, Optional
from collections import defaultdict
from sklearn.metrics import normalized_mutual_info_score
from scipy.optimize import linear_sum_assignment

import subsystem_utils as su

def calculate_cluster_similarity_matrix(clusterings: Dict[su.NodeID, Dict[su.NodeID, su.ClusterID]]) -> Dict[Tuple[su.NodeID, su.ClusterID], Dict[Tuple[su.NodeID, su.ClusterID], float]]:
    """
    Calculate similarity between clusters from different clusterings.
    
    Args:
        clusterings: Dictionary mapping clustering source to node-cluster mappings
        
    Returns:
        Dictionary mapping (source, cluster_id) pairs to dictionaries of similarities to other clusters
    """
    # Identify all nodes across all clusterings
    all_nodes: Set[su.NodeID] = set()
    for clustering in clusterings.values():
        all_nodes.update(clustering.keys())
    
    # Create inverted mappings (cluster -> nodes) for each clustering
    inverted_clusterings: Dict[su.NodeID, Dict[Tuple[su.NodeID, su.ClusterID], Set[su.NodeID]]] = {}
    for source, clustering in clusterings.items():
        inverted: Dict[Tuple[su.NodeID, su.ClusterID], Set[su.NodeID]] = defaultdict(set)
        for node_id, cluster_id in clustering.items():
            inverted[(source, cluster_id)].add(node_id)
        inverted_clusterings[source] = inverted
    
    # Flatten the inverted clusterings into a single dictionary
    all_clusters: Dict[Tuple[su.NodeID, su.ClusterID], Set[su.NodeID]] = {}
    for source, inverted in inverted_clusterings.items():
        all_clusters.update(inverted)
    
    # Calculate Jaccard similarity between all pairs of clusters
    similarity_matrix: Dict[Tuple[su.NodeID, su.ClusterID], Dict[Tuple[su.NodeID, su.ClusterID], float]] = defaultdict(dict)
    cluster_keys: List[Tuple[su.NodeID, su.ClusterID]] = list(all_clusters.keys())

    for i, key1 in enumerate(cluster_keys):
        for key2 in cluster_keys:
            # Skip self-comparisons
            if key1 == key2:
                similarity_matrix[key1][key2] = 1.0
                continue
                
            # Skip comparisons within the same source
            if key1[0] == key2[0]:
                continue
                
            # Calculate Jaccard similarity
            nodes1: Set[su.NodeID] = all_clusters[key1]
            nodes2: Set[su.NodeID] = all_clusters[key2]

            intersection = len(nodes1 & nodes2)
            union = len(nodes1 | nodes2)
            
            if union > 0:
                similarity = intersection / union
            else:
                similarity = 0.0
                
            similarity_matrix[key1][key2] = similarity
    
    return similarity_matrix

def evaluate_clustering_agreement(clusterings: Dict[su.NodeID, Dict[su.NodeID, su.ClusterID]]) -> Dict[Tuple[su.NodeID, su.NodeID], float]:
    """
    Evaluate agreement between different clusterings using Normalized Mutual Information.
    
    Args:
        clusterings: Dictionary mapping clustering source to node-cluster mappings

    Returns:
        Dictionary mapping source pairs to NMI scores
    """
    # Get all sources
    sources: List[su.NodeID] = list(clusterings.keys())

    # Get all nodes across all clusterings
    all_nodes: Set[su.NodeID] = set()
    for clustering in clusterings.values():
        all_nodes.update(clustering.keys())
    all_nodes = sorted(all_nodes)  # Sort for consistent ordering
    
    # Create node-to-index mapping
    node_to_idx: Dict[su.NodeID, int] = {node: i for i, node in enumerate(all_nodes)}

    # Create label arrays for each clustering
    label_arrays: Dict[su.NodeID, np.ndarray] = {}
    for source, clustering in clusterings.items():
        labels = np.zeros(len(all_nodes)) - 1  # -1 for nodes not in this clustering
        for node, cluster_id in clustering.items():
            idx = node_to_idx.get(node)
            if idx is not None:
                labels[idx] = cluster_id
        label_arrays[source] = labels
    
    # Calculate NMI for each pair of clusterings
    agreement_scores: Dict[Tuple[su.NodeID, su.NodeID], float] = {}
    for i, source1 in enumerate(sources):
        for j, source2 in enumerate(sources):
            if i >= j:
                continue

            labels1: np.ndarray = label_arrays[source1]
            labels2: np.ndarray = label_arrays[source2]

            # Filter out nodes not present in both clusterings
            mask = (labels1 >= 0) & (labels2 >= 0)
            if np.sum(mask) < 2:
                agreement_scores[(source1, source2)] = 0.0
                continue
                
            # Calculate NMI
            nmi = normalized_mutual_info_score(
                labels1[mask].astype(int),
                labels2[mask].astype(int)
            )
            
            agreement_scores[(source1, source2)] = nmi
    
    return agreement_scores

def generate_consensus_clustering(clusterings: Dict[su.NodeID, Dict[su.NodeID, su.ClusterID]],
                                 weights: Dict[su.NodeID, float] = None,
                                 n_clusters: int = None) -> Dict[su.NodeID, su.ClusterID]:
    """
    Generate a consensus clustering by combining multiple clusterings.
    
    Args:
        clusterings: Dictionary mapping clustering source to node-cluster mappings
        weights: Dictionary mapping clustering source to weight
        
    Returns:
        Consensus clustering (node_id to cluster_id mapping)
    """
    # Default weights if not provided
    if weights is None:
        weights: Dict[su.NodeID, float] = {source: 1.0 for source in clusterings}

    # Normalize weights
    total_weight = sum(weights.values())
    if total_weight > 0:
        weights = {source: weight / total_weight for source, weight in weights.items()}
    
    # Get all nodes across all clusterings
    all_nodes: Set[su.NodeID] = set()
    for clustering in clusterings.values():
        all_nodes.update(clustering.keys())
    
    # Build co-occurrence matrix
    n_nodes = len(all_nodes)
    node_list: List[su.NodeID] = sorted(all_nodes)
    node_to_idx: Dict[su.NodeID, int] = {node: i for i, node in enumerate(node_list)}

    co_occurrence = np.zeros((n_nodes, n_nodes))
    
    for source, clustering in clusterings.items():
        # Group nodes by cluster
        clusters = defaultdict(set)
        for node, cluster_id in clustering.items():
            clusters[cluster_id].add(node)
        
        # Update co-occurrence matrix
        source_weight = weights.get(source, 1.0)
        for nodes in clusters.values():
            for node1 in nodes:
                idx1 = node_to_idx[node1]
                for node2 in nodes:
                    idx2 = node_to_idx[node2]
                    co_occurrence[idx1, idx2] += source_weight
    
    # Normalize co-occurrence matrix
    np.fill_diagonal(co_occurrence, 0)  # Zero out diagonal
    row_sums = co_occurrence.sum(axis=1, keepdims=True)
    row_sums[row_sums == 0] = 1  # Avoid division by zero
    co_occurrence = co_occurrence / row_sums
    
    # Convert to distance matrix
    distance_matrix = 1 - co_occurrence
    
    # Apply hierarchical clustering to the co-occurrence matrix
    from sklearn.cluster import AgglomerativeClustering
    
    # Estimate number of clusters
    if n_clusters is None:
        n_clusters = max(2, int(np.sqrt(n_nodes / 2)))
    
    clustering = AgglomerativeClustering(
        n_clusters=n_clusters,
        metric='precomputed',
        linkage='average'
    )
    
    cluster_assignments = clustering.fit_predict(distance_matrix)
    
    # Map back to node IDs
    consensus: Dict[su.NodeID, su.ClusterID] = {
        node_list[i]: int(cluster_id)
        for i, cluster_id in enumerate(cluster_assignments)
    }
    
    return consensus

def optimize_cluster_mapping(source_clustering: Dict[su.NodeID, su.ClusterID],
                            target_clustering: Dict[su.NodeID, su.ClusterID]) -> Dict[su.ClusterID, su.ClusterID]:
    """
    Optimize mapping between source and target clustering.
    
    Args:
        source_clustering: Source clustering (node_id to cluster_id mapping)
        target_clustering: Target clustering (node_id to cluster_id mapping)
        
    Returns:
        Mapping from source cluster IDs to target cluster IDs
    """
    # Get common nodes
    common_nodes: Set[su.NodeID] = set(source_clustering.keys()) & set(target_clustering.keys())

    if not common_nodes:
        return {}
    
    # Get unique cluster IDs
    source_clusters: Set[su.ClusterID] = set(source_clustering[e] for e in common_nodes)
    target_clusters: Set[su.ClusterID] = set(target_clustering[e] for e in common_nodes)

    # Create confusion matrix
    confusion_matrix = np.zeros((len(source_clusters), len(target_clusters)))

    source_id_to_idx: Dict[su.ClusterID, int] = {cluster_id: i for i, cluster_id in enumerate(sorted(source_clusters))}
    target_id_to_idx: Dict[su.ClusterID, int] = {cluster_id: i for i, cluster_id in enumerate(sorted(target_clusters))}

    for node in common_nodes:
        source_idx = source_id_to_idx[source_clustering[node]]
        target_idx = target_id_to_idx[target_clustering[node]]
        confusion_matrix[source_idx, target_idx] += 1
    
    # Use Hungarian algorithm to find optimal assignment
    row_ind, col_ind = linear_sum_assignment(-confusion_matrix)
    
    # Create mapping
    mapping: Dict[su.ClusterID, su.ClusterID] = {
        sorted(source_clusters)[i]: sorted(target_clusters)[j]
        for i, j in zip(row_ind, col_ind)
    }
    
    return mapping

def apply_cluster_mapping(clustering: Dict[su.NodeID, su.ClusterID], mapping: Dict[su.ClusterID, su.ClusterID]) -> Dict[su.NodeID, su.ClusterID]:
    """
    Apply a cluster mapping to a clustering.
    
    Args:
        clustering: Original clustering (node_id to cluster_id mapping)
        mapping: Mapping from original cluster IDs to new cluster IDs
        
    Returns:
        Updated clustering with mapped cluster IDs
    """
    result: Dict[su.NodeID, su.ClusterID] = {}
    for node_id, cluster_id in clustering.items():
        if cluster_id in mapping:
            result[node_id] = mapping[cluster_id]
        else:
            result[node_id] = cluster_id
    return result

def run_cluster_integration(structural_clustering: Dict[su.NodeID, su.ClusterID],
                           semantic_clustering: Dict[su.NodeID, su.ClusterID],
                           weights: Dict[str, float] = None,
                           n_clusters: int = None) -> Tuple[Dict[su.NodeID, su.ClusterID], Dict]:
    """
    Run the full cluster integration pipeline.
    
    Args:
        structural_clustering: Structural clustering (node_id to cluster_id mapping)
        semantic_clustering: Semantic clustering (node_id to cluster_id mapping)
        usage_clustering: Usage-based clustering (node_id to cluster_id mapping)
        weights: Dictionary mapping clustering source to weight
        
    Returns:
        Tuple of (consensus clustering, metadata)
    """
    # Prepare input clusterings
    clusterings = {
        "structural": structural_clustering,
        "semantic": semantic_clustering,
    }
    
    # Filter out empty clusterings
    clusterings: Dict[str, Dict[su.NodeID, su.ClusterID]] = {
        source: clustering
        for source, clustering in clusterings.items()
        if clustering
    }
    
    # Return early if we have only one clustering
    if len(clusterings) <= 1:
        source = next(iter(clusterings.keys())) if clusterings else None
        if source:
            return clusterings[source], {
                "warning": f"Only {source} clustering available",
                "sources": [source]
            }
        else:
            return {}, {"error": "No valid clusterings provided"}
    
    # Set default weights if not provided
    if weights is None:
        weights = {
            "structural": 0.5,
            "semantic": 0.3,
            "usage": 0.2
        }
    
    # Prepare metadata
    metadata = {
        "sources": list(clusterings.keys()),
        "weights": weights,
        "node_counts": {
            source: len(clustering)
            for source, clustering in clusterings.items()
        }
    }
    
    # Evaluate agreement between clusterings
    agreement_scores = evaluate_clustering_agreement(clusterings)
    metadata["agreement_scores"] = {
        f"{source1}_{source2}": score
        for (source1, source2), score in agreement_scores.items()
    }
    
    # Generate consensus clustering
    consensus_clustering: Dict[su.NodeID, su.ClusterID] = generate_consensus_clustering(
        clusterings=clusterings,
        weights=weights,
        n_clusters=n_clusters
    )
    
    # Map original clusters to consensus clusters
    mappings: Dict[str, Dict[su.ClusterID, su.ClusterID]] = {}
    for source, clustering in clusterings.items():
        mapping = optimize_cluster_mapping(clustering, consensus_clustering)
        mappings[source] = mapping
    
    metadata["mappings"] = mappings
    
    # Count nodes and clusters
    metadata["node_count"] = len(consensus_clustering)
    metadata["cluster_count"] = len(set(consensus_clustering.values()))
    
    return consensus_clustering, metadata

def clustering_to_cluster_objects(clustering: Dict[su.NodeID, su.ClusterID], 
                                source: str = "integrated") -> Dict[su.ClusterID, su.Cluster]:
    """
    Convert a clustering dictionary to Cluster objects.
    
    Args:
        clustering: Dictionary mapping node ID to cluster ID
        source: Source of the clustering
        
    Returns:
        Dictionary mapping cluster ID to Cluster object
    """
    # Group nodes by cluster
    clusters_map = defaultdict(set)
    for node, cluster_id in clustering.items():
        clusters_map[cluster_id].add(node)
    
    # Create Cluster objects
    result: Dict[su.ClusterID, su.Cluster] = {}
    for cluster_id, nodes in clusters_map.items():
        result[cluster_id] = su.Cluster(
            cluster_id=cluster_id,
            nodes=nodes,
            source=source
        )
    
    return result
