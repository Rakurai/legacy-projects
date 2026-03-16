"""
Semantic clustering module for subsystem discovery.

This module provides functionality to:
1. Extract embeddings from entity documentation
2. Perform topic modeling (LDA, NMF)
3. Implement semantic similarity clustering
"""

import numpy as np
import pandas as pd
import re
from typing import Dict, List, Set, Tuple, Any, Optional
from collections import defaultdict
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.decomposition import LatentDirichletAllocation, NMF
from sklearn.cluster import AgglomerativeClustering, KMeans
from sklearn.metrics import silhouette_score
from scipy.sparse import csr_matrix
from loguru import logger as log
import time

import subsystem_utils as su
import doxygen_parse as dp
from doc_db import DocumentDB


def clean_text(text: str) -> str:
    """
    Clean and preprocess text for NLP.
    
    Args:
        text: Input text
        
    Returns:
        Cleaned text
    """
    if not text:
        return ""
    
    # Convert to lowercase
    text = text.lower()
    
    # Remove code snippets
    text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
    
    # Remove special characters but keep alphanumeric and spaces
    text = re.sub(r'[^\w\s]', ' ', text)
    
    # Replace multiple spaces with single space
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def extract_entity_texts(graph, entity_db: dp.EntityDatabase, doc_database: DocumentDB) -> Dict[str, str]:
    """
    Extract text content from entity documentation.
    
    Args:
        graph: The knowledge graph
        entity_db: The entity database
        doc_database: Document database object
        
    Returns:
        Dictionary mapping entity ID to text content
    """
    start_time = time.time()
    log.info("Extracting textual content from document database")
    
    entity_texts = {}
    doc_count = 0
    
    for node_id in graph.nodes:
        entity = su.get_entity(entity_db, node_id)
        if entity is None:
            continue
        doc = doc_database.get_doc(entity.id.compound, entity.signature)
        if doc is None:
            continue

        # Combine relevant text fields
        text_parts = []

        # Add brief description if available
        if doc.brief:
            text_parts.append(doc.brief)
        
        # Add detailed description if available
        if doc.details:
            text_parts.append(doc.details)

        # Add example usage if available
        if doc.rationale:
            text_parts.append(f"Rationale: {doc.rationale}")

        # Add return information if available
        if doc.returns:
            text_parts.append(f"Returns: {doc.returns}")
        
        # Join all parts and clean
        if text_parts:
            combined_text = ' '.join(text_parts)
            entity_texts[node_id] = clean_text(combined_text)
            doc_count += 1
    
    elapsed_time = time.time() - start_time
    log.info(f"Extracted text from {doc_count} documents in {elapsed_time:.2f}s")
    return entity_texts

def create_document_term_matrix(entity_texts: Dict[str, str], 
                               min_df: float = 0.01, 
                               max_df: float = 0.95) -> Tuple[csr_matrix, List[str], List[str]]:
    """
    Create a document-term matrix using TF-IDF vectorization.
    
    Args:
        entity_texts: Dictionary mapping entity ID to text content
        min_df: Minimum document frequency for terms
        max_df: Maximum document frequency for terms
        
    Returns:
        Tuple of (document-term matrix, entity IDs, feature names)
    """
    start_time = time.time()
    log.info(f"Creating document-term matrix with TF-IDF vectorization (min_df={min_df}, max_df={max_df})")
    
    # Extract document IDs and texts in consistent order
    doc_ids = list(entity_texts.keys())
    texts = [entity_texts[doc_id] for doc_id in doc_ids]
    
    # Create TF-IDF vectorizer
    log.info(f"Creating TF-IDF vectorizer for {len(texts)} documents")
    vectorizer = TfidfVectorizer(
        min_df=min_df,
        max_df=max_df,
        stop_words='english',
        ngram_range=(1, 2)
    )
    
    # Create document-term matrix
    dtm = vectorizer.fit_transform(texts)
    
    # Get feature names
    try:
        feature_names = vectorizer.get_feature_names_out()
    except AttributeError:
        # For older scikit-learn versions
        feature_names = vectorizer.get_feature_names()
    
    elapsed_time = time.time() - start_time
    log.info(f"Created document-term matrix with shape {dtm.shape} and {len(feature_names)} features in {elapsed_time:.2f}s")
    
    return dtm, doc_ids, feature_names

def apply_topic_modeling(dtm: csr_matrix, 
                        n_topics: int, 
                        method: str = "lda",
                        random_state: int = 42) -> Tuple[np.ndarray, np.ndarray]:
    """
    Apply topic modeling to a document-term matrix.
    
    Args:
        dtm: Document-term matrix
        n_topics: Number of topics to extract
        method: Topic modeling method ("lda" or "nmf")
        random_state: Random seed
        
    Returns:
        Tuple of (document-topic matrix, topic-term matrix)
    """
    if method.lower() == "lda":
        # Convert to term-frequency for LDA
        count_vectorizer = CountVectorizer()
        count_matrix = dtm
        
        # Apply LDA
        model = LatentDirichletAllocation(
            n_components=n_topics,
            random_state=random_state,
            max_iter=20
        )
    elif method.lower() == "nmf":
        # Apply NMF directly to TF-IDF
        model = NMF(
            n_components=n_topics,
            random_state=random_state,
            max_iter=200
        )
    else:
        raise ValueError(f"Unknown topic modeling method: {method}")
    
    # Fit model
    document_topic_matrix = model.fit_transform(dtm)
    topic_term_matrix = model.components_
    
    return document_topic_matrix, topic_term_matrix

def get_optimal_topics(dtm: csr_matrix, 
                      min_topics: int = 5, 
                      max_topics: int = 30,
                      step: int = 5) -> int:
    """
    Get the optimal number of topics based on coherence.
    
    Args:
        dtm: Document-term matrix
        min_topics: Minimum number of topics to try
        max_topics: Maximum number of topics to try
        step: Step size for topics
        
    Returns:
        Optimal number of topics
    """
    # Placeholder implementation
    # In a real implementation, we would calculate coherence scores
    # and pick the number of topics that maximizes coherence
    
    # For now, use a simple heuristic based on matrix dimensions
    n_docs = dtm.shape[0]
    
    if n_docs < 50:
        return min(5, n_docs - 1) if n_docs > 1 else 1
    elif n_docs < 200:
        return 10
    elif n_docs < 500:
        return 15
    else:
        return 20

def cluster_by_topic_distribution(document_topic_matrix: np.ndarray,
                                 n_clusters: int = None,
                                 method: str = "kmeans",
                                 random_state: int = 42) -> np.ndarray:
    """
    Cluster entities based on their topic distributions.
    
    Args:
        document_topic_matrix: Matrix of document-topic weights
        n_clusters: Number of clusters (if None, estimated from data)
        method: Clustering method ("kmeans" or "hierarchical")
        random_state: Random seed
        
    Returns:
        Array of cluster assignments
    """
    # Estimate number of clusters if not specified
    if n_clusters is None:
        # Simple heuristic: use approximately sqrt(n) clusters
        n_clusters = max(2, int(np.sqrt(document_topic_matrix.shape[0] / 2)))
    
    # Apply clustering
    if method.lower() == "kmeans":
        clustering = KMeans(
            n_clusters=n_clusters,
            random_state=random_state,
            n_init=10
        )
    elif method.lower() == "hierarchical":
        clustering = AgglomerativeClustering(
            n_clusters=n_clusters,
            affinity="euclidean",
            linkage="ward"
        )
    else:
        raise ValueError(f"Unknown clustering method: {method}")
    
    # Fit clustering
    cluster_assignments = clustering.fit_predict(document_topic_matrix)
    
    return cluster_assignments

def evaluate_topic_clustering(document_topic_matrix: np.ndarray, 
                             cluster_assignments: np.ndarray) -> Dict[str, float]:
    """
    Evaluate the quality of topic-based clustering.
    
    Args:
        document_topic_matrix: Matrix of document-topic weights
        cluster_assignments: Array of cluster assignments
        
    Returns:
        Dictionary of evaluation metrics
    """
    metrics = {}
    
    # Number of clusters
    n_clusters = len(set(cluster_assignments))
    metrics["n_clusters"] = n_clusters
    
    # Cluster sizes
    unique, counts = np.unique(cluster_assignments, return_counts=True)
    metrics["avg_cluster_size"] = np.mean(counts)
    metrics["min_cluster_size"] = np.min(counts)
    metrics["max_cluster_size"] = np.max(counts)
    metrics["size_std_dev"] = np.std(counts)
    
    # Silhouette score (if more than one cluster)
    if n_clusters > 1 and n_clusters < len(cluster_assignments):
        try:
            metrics["silhouette_score"] = silhouette_score(
                document_topic_matrix, 
                cluster_assignments
            )
        except:
            metrics["silhouette_score"] = 0
    else:
        metrics["silhouette_score"] = 0
    
    return metrics

def get_top_terms_per_topic(topic_term_matrix: np.ndarray, 
                           feature_names: List[str],
                           n_terms: int = 10) -> List[List[str]]:
    """
    Get the top terms for each topic.
    
    Args:
        topic_term_matrix: Matrix of topic-term weights
        feature_names: List of feature names
        n_terms: Number of top terms to include per topic
        
    Returns:
        List of lists containing top terms for each topic
    """
    return [
        [feature_names[i] for i in topic.argsort()[:-n_terms-1:-1]]
        for topic in topic_term_matrix
    ]

def run_semantic_clustering(graph, entity_db: dp.EntityDatabase,
                           doc_database: DocumentDB,
                           topic_method: str = "lda",
                           n_topics: int = None,
                           cluster_method: str = "kmeans",
                           n_clusters: int = None,
                           random_state: int = 42) -> Tuple[Dict[str, int], Dict]:
    """
    Run the full semantic clustering pipeline.
    
    Args:
        graph: NetworkX graph object
        entity_db: Entity database object
        doc_database: Document database object
        topic_method: Topic modeling method ("lda" or "nmf")
        n_topics: Number of topics (if None, estimated from data)
        cluster_method: Clustering method ("kmeans" or "hierarchical")
        n_clusters: Number of clusters (if None, estimated from data)
        random_state: Random seed
        
    Returns:
        Tuple of (entity_id to cluster_id mapping, metadata)
    """
    start_time = time.time()
    log.info(f"Starting semantic clustering with {topic_method} topic modeling and {cluster_method} clustering")
    
    metadata = {
        "topic_method": topic_method,
        "cluster_method": cluster_method,
        "random_state": random_state
    }
    
    # Extract text from entity documentation
    entity_texts = extract_entity_texts(graph, entity_db, doc_database)
    metadata["entity_count"] = len(entity_texts)
    
    # Filter out entities with no text
    non_empty_entities = {eid: text for eid, text in entity_texts.items() if text.strip()}
    metadata["non_empty_entity_count"] = len(non_empty_entities)
    
    # If too few non-empty entities, return empty results
    if len(non_empty_entities) < 3:
        return {}, {"error": "Too few entities with documentation"}
    
    # Create document-term matrix
    dtm, entity_ids, feature_names = create_document_term_matrix(non_empty_entities)
    
    # Determine optimal number of topics if not specified
    if n_topics is None:
        n_topics = get_optimal_topics(dtm)
    metadata["n_topics"] = n_topics
    
    # Apply topic modeling
    document_topic_matrix, topic_term_matrix = apply_topic_modeling(
        dtm=dtm,
        n_topics=n_topics,
        method=topic_method,
        random_state=random_state
    )
    
    # Get top terms for each topic
    top_terms = get_top_terms_per_topic(topic_term_matrix, feature_names)
    topic_labels = [f"Topic {i}: {' '.join(terms[:5])}" for i, terms in enumerate(top_terms)]
    metadata["topic_labels"] = topic_labels
    
    # Cluster by topic distribution
    cluster_assignments = cluster_by_topic_distribution(
        document_topic_matrix=document_topic_matrix,
        n_clusters=n_clusters,
        method=cluster_method,
        random_state=random_state
    )
    
    # Evaluate clustering
    clustering_metrics = evaluate_topic_clustering(
        document_topic_matrix=document_topic_matrix,
        cluster_assignments=cluster_assignments
    )
    metadata.update(clustering_metrics)
    
    # Map back to entity IDs
    entity_to_cluster = {
        entity_ids[i]: int(cluster_assignments[i])
        for i in range(len(entity_ids))
    }
    
    total_time = time.time() - start_time
    cluster_count = len(set(entity_to_cluster.values()))
    log.info(f"Semantic clustering completed in {total_time:.2f}s. Found {cluster_count} clusters")
    
    return entity_to_cluster, metadata

def clustering_to_cluster_objects(clustering: Dict[su.NodeID, su.ClusterID], 
                                source: str = "semantic") -> Dict[su.ClusterID, su.Cluster]:
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
    clusters_map: defaultdict[su.ClusterID, set[su.NodeID]] = defaultdict(set)
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
    
    # Log cluster size distribution
    sizes = [len(c.nodes) for c in result.values()]
    log.info(f"Created {len(result)} cluster objects with size distribution: "
               f"min={min(sizes)}, max={max(sizes)}, avg={sum(sizes)/len(sizes):.1f}")
    
    return result
