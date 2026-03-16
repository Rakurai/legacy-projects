"""
Subsystem Identifier Module

This module contains functionality for identifying, naming, and classifying
subsystems in the codebase based on the integrated clusters.
"""

from collections import Counter, defaultdict
from typing import Dict, List, Set, Tuple, Any, Optional
import networkx as nx
from pathlib import Path
import re
import json

import subsystem_utils as su
import doxygen_parse as dp

from doc_db import DocumentDB, Document
from subsystem_utils import Subsystem, SubsystemID, ClusterID, Cluster, NodeID

# Common programming terms to filter out when identifying subsystem themes
COMMON_STOP_WORDS = {
    'get', 'set', 'init', 'create', 'delete', 'update', 'check', 'is', 'has',
    'value', 'data', 'index', 'type', 'size', 'count', 'new', 'add', 'remove',
    'first', 'last', 'next', 'prev', 'start', 'end', 'find', 'search', 'sort',
    'max', 'min', 'begin', 'finish', 'done', 'load', 'save', 'open', 'close'
}

# Domain-specific keywords for classification
CLASSIFICATION_KEYWORDS = {
    'Interface': {
        'display', 'input', 'output', 'terminal', 'screen', 'message', 'print',
        'prompt', 'command', 'menu', 'window', 'console', 'user', 'client', 
        'socket', 'network', 'protocol', 'packet', 'connection', 'comm'
    },
    'Core': {
        'game', 'player', 'character', 'mob', 'npc', 'combat', 'fight', 'spell',
        'skill', 'item', 'object', 'room', 'area', 'world', 'quest', 'mission',
        'event', 'action', 'time', 'trigger', 'script', 'effect', 'stat', 'attribute'
    },
    'Data': {
        'data', 'storage', 'file', 'database', 'save', 'load', 'persist', 'record',
        'table', 'json', 'xml', 'config', 'setting', 'profile', 'account', 'db'
    },
    'Support': {
        'util', 'helper', 'common', 'tool', 'service', 'manager', 'factory',
        'builder', 'handler', 'processor', 'logger', 'debug', 'error', 'format'
    },
    'Extension': {
        'module', 'plugin', 'extension', 'addon', 'feature', 'script', 
        'dynamic', 'custom', 'hook', 'event'
    }
}

def extract_significant_terms(entity_names: List[str]) -> Counter:
    """
    Extract and count significant terms from entity names.
    
    Args:
        entity_names: List of entity names to analyze
        
    Returns:
        Counter of significant terms
    """
    # Split names into words and count occurrences
    term_counter = Counter()
    
    for name in entity_names:
        # Convert camelCase or PascalCase to snake_case for consistent separation
        name_snake = re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower()
        # Split by common separators
        words = re.split(r'[_\s\-.]', name_snake)
        # Filter out common programming terms and very short words
        words = [word for word in words if word not in COMMON_STOP_WORDS and len(word) > 2]
        term_counter.update(words)
    
    return term_counter

def classify_subsystem(term_counter: Counter) -> str:
    """
    Determine subsystem classification based on significant terms.
    
    Args:
        term_counter: Counter of significant terms from entity names
        
    Returns:
        Classification string (Core, Interface, Support, Data, Extension)
    """
    # Default classification
    classification = 'Core'
    
    # Check term overlap with classification keywords
    max_overlap = 0
    for category, keywords in CLASSIFICATION_KEYWORDS.items():
        overlap = sum(term_counter[term] for term in keywords & set(term_counter.keys()))
        
        if overlap > max_overlap:
            max_overlap = overlap
            classification = category
    
    return classification

def determine_subsystem_name(term_counter: Counter, entity_types: Counter, classification: str) -> str:
    """
    Generate a meaningful name for a subsystem based on its contents.
    
    Args:
        term_counter: Counter of significant terms
        entity_types: Counter of entity types (classes, functions, etc.)
        classification: Subsystem classification
        
    Returns:
        Proposed subsystem name
    """
    # Get top terms (excluding classification-specific keywords to avoid redundancy)
    keywords = CLASSIFICATION_KEYWORDS.get(classification, set())
    filtered_counter = Counter({term: count for term, count in term_counter.items() 
                               if term not in keywords})
    
    top_terms = [term for term, _ in filtered_counter.most_common(3)]
    
    if not top_terms:
        # If no significant terms found, use the classification and dominant type
        dominant_type = entity_types.most_common(1)[0][0] if entity_types else "Component"
        return f"{classification} {dominant_type}"
    
    # Use top terms to create name
    if len(top_terms) >= 2:
        # Join top two terms
        name = ' '.join(term.capitalize() for term in top_terms[:2])
    else:
        # Use single term with classification
        name = f"{top_terms[0].capitalize()} {classification}"
    
    return name

def extract_key_concepts(term_counter: Counter, classification: str, top_n: int = 5) -> List[str]:
    """
    Extract key concepts that define the subsystem's domain.
    
    Args:
        term_counter: Counter of significant terms
        classification: Subsystem classification
        top_n: Number of top terms to return
        
    Returns:
        List of key concept terms
    """
    # Exclude words that are already part of the classification name
    keywords = CLASSIFICATION_KEYWORDS.get(classification, set())
    filtered_counter = Counter({term: count for term, count in term_counter.items() 
                               if term not in keywords})
    
    return [term for term, _ in filtered_counter.most_common(top_n)]

def analyze_cluster(cluster: Cluster, entity_db: dp.EntityDatabase, docs_db: DocumentDB, graph: nx.Graph) -> Dict[str, Any]:
    """
    Analyze a cluster and suggest a name, classification, and other metadata.
    
    Args:
        cluster: Cluster object to analyze
        entity_db: Entity database
        docs_db: Document database
        graph: NetworkX dependency graph
        
    Returns:
        Dictionary with subsystem analysis metadata
    """
    # Get entity types and names
    entity_types = []
    entity_names = []
    
    for node_id in cluster.nodes:
        entity = su.get_entity(entity_db, node_id)
        if entity:
            entity_types.append(entity.kind)
            entity_names.append(entity.name)

    # Count types
    type_counts = Counter(entity_types)
    dominant_type = type_counts.most_common(1)[0][0] if type_counts else 'unknown'
    
    # Extract significant terms
    term_counter = extract_significant_terms(entity_names)
    
    # Determine classification
    classification = classify_subsystem(term_counter)
    
    # Generate subsystem name
    subsystem_name = determine_subsystem_name(term_counter, type_counts, classification)
    
    # Extract key concepts
    key_concepts = extract_key_concepts(term_counter, classification)
    
    # Compute additional metrics
    connectivity = calculate_internal_connectivity(cluster, graph)
    
    return {
        'name': subsystem_name,
        'classification': classification,
        'dominant_type': dominant_type,
        'key_concepts': key_concepts,
        'entity_count': len(cluster.nodes),
        'internal_connectivity': connectivity,
        'term_frequencies': dict(term_counter.most_common(20))
    }

def calculate_internal_connectivity(cluster: Cluster, graph: nx.Graph) -> float:
    """
    Calculate the internal connectivity of a cluster.
    
    Args:
        cluster: Cluster to analyze
        graph: NetworkX dependency graph
        
    Returns:
        Connectivity metric value
    """
    nodes = list(cluster.nodes)
    if len(nodes) <= 1:
        return 0.0
        
    # Count internal edges
    internal_edges = 0
    for u in nodes:
        for v in nodes:
            if u != v and graph.has_edge(u, v):
                internal_edges += 1
                
    # Maximum possible internal edges (n * (n-1) for directed graph)
    max_possible = len(nodes) * (len(nodes) - 1)
    
    # Return density
    return internal_edges / max_possible if max_possible > 0 else 0.0

def process_clusters(clusters: Dict[ClusterID, Cluster], entity_db: dp.EntityDatabase, docs_db: DocumentDB, graph: nx.Graph) -> Dict[SubsystemID, Subsystem]:
    """
    Process all clusters and convert them to subsystems.
    
    Args:
        clusters: Dictionary of clusters
        entity_db: Entity database
        docs_db: Document database
        graph: NetworkX dependency graph
        
    Returns:
        Dictionary of subsystem objects
    """
    subsystems = {}
    
    for cluster_id, cluster in clusters.items():
        # Analyze the cluster
        analysis = analyze_cluster(cluster, entity_db, docs_db, graph)
        
        # Create a subsystem ID
        subsystem_id = f"s{cluster_id}"
        
        # Create a Subsystem object
        subsystem = Subsystem(
            subsystem_id=subsystem_id,
            name=analysis['name'],
            nodes=cluster.nodes,
            classification=analysis['classification']
        )
        
        # Add analysis to metadata
        subsystem.metadata.update(analysis)
        
        subsystems[subsystem_id] = subsystem
        
    return subsystems

def generate_subsystems_catalog(subsystems: Dict[SubsystemID, Subsystem]) -> str:
    """
    Generate a markdown catalog of all subsystems.
    
    Args:
        subsystems: Dictionary of subsystem objects
        
    Returns:
        Markdown content for the catalog
    """
    # Group by classification
    by_classification = defaultdict(list)
    for subsystem in subsystems.values():
        by_classification[subsystem.classification].append(subsystem)
        
    # Template for catalog
    catalog = [
        "# Subsystems Catalog\n",
        "This document catalogs the high-level subsystems identified in the Legacy MUD codebase.",
        "Each subsystem has been named and classified according to its function in the overall system.\n",
        f"## Overview\n",
        f"Total subsystems identified: {len(subsystems)}\n",
        "## Subsystem Classification\n",
        "Subsystems are classified into the following categories:\n",
        "- **Core**: Essential game mechanics and systems",
        "- **Interface**: User interaction and I/O",
        "- **Support**: Supporting functionality and utilities",
        "- **Data**: Data management and persistence",
        "- **Extension**: Optional or add-on features\n",
        "## Subsystems\n"
    ]
    
    # Add each classification group
    for classification in sorted(by_classification.keys()):
        catalog.append(f"### {classification}\n")
        
        for subsystem in sorted(by_classification[classification], key=lambda s: s.name):
            catalog.append(f"#### {subsystem.name}\n")
            catalog.append(f"**ID**: {subsystem.subsystem_id}\n")
            catalog.append(f"**Entity Count**: {len(subsystem.nodes)}\n")
            
            # Add key concepts
            if 'key_concepts' in subsystem.metadata:
                key_concepts = subsystem.metadata['key_concepts']
                if key_concepts:
                    catalog.append(f"**Key Concepts**: {', '.join(key_concepts)}\n")
            
            catalog.append("\n")
            
    return "\n".join(catalog)
