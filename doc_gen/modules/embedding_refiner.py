"""
Embedding-based refinement module for subsystem discovery.

This module provides functionality to:
1. Generate code embeddings for nodes using CodeBERT
2. Calculate cosine similarity between nodes within and across subsystems
3. Identify nodes with low similarity to their current subsystem
4. Suggest regroupings based on embedding similarity scores
"""

import numpy as np
import pandas as pd
import networkx as nx
from typing import Dict, List, Set, Tuple, Any, Optional
from collections import defaultdict
from sklearn.metrics.pairwise import cosine_similarity
import torch
from transformers import AutoTokenizer, AutoModel
import os
import json

import subsystem_utils as su
import doc_db
import doxygen_parse as dp
import doxygen_graph as dg

# Constants
CODEBERT_MODEL = "microsoft/codebert-base"
SIMILARITY_THRESHOLD = 0.5  # Minimum similarity to belong to a subsystem
CONFIDENCE_THRESHOLD = 0.7  # High confidence threshold
MAX_TOKEN_LENGTH = 512  # Maximum token length for CodeBERT

from subsystem_utils import NodeID, Subsystem, SubsystemID
Embedding = np.ndarray
SimilarityMatrix = np.ndarray #Dict[NodeID, Dict[NodeID, float]]
SimilarityMatrixData = Dict[str, SimilarityMatrix|List[NodeID]]

class EmbeddingRefiner:
    """Class for refining subsystem assignments using code embeddings."""

    def __init__(self, db: dp.EntityDatabase, graph: nx.Graph, doc_database: doc_db.DocumentDB=None):
        """Initialize the embedding refiner with necessary data.
        
        Args:
            db: The Doxygen entity database
            graph: The NetworkX dependency graph
            doc_database: The documentation database (defaults to doc_db.docs)
        """
        self.db = db
        self.graph = graph
        self.docs = doc_database if doc_database is not None else doc_db.docs
        
        # Load CodeBERT model and tokenizer
        self.tokenizer = None
        self.model = None
        self.sbert_model = None
    
    def load_model(self) -> None:
        """Load the CodeBERT model and tokenizer."""
        print("Loading CodeBERT model and tokenizer...")
        self.tokenizer = AutoTokenizer.from_pretrained(CODEBERT_MODEL)
        self.model = AutoModel.from_pretrained(CODEBERT_MODEL)
        print("Model loaded successfully.")

    def load_sbert_model(self) -> None:
        """Load the Sentence-BERT model."""
        from sentence_transformers import SentenceTransformer
        self.sbert_model = SentenceTransformer("all-MiniLM-L6-v2")  # or all-mpnet-base-v2

    def generate_node_embedding(self, node_id: NodeID) -> Optional[Embedding]:
        """Generate an embedding vector for a given node.
        
        Args:
            node_id: The ID of the node to generate embeddings for
            
        Returns:
            A numpy array representing the node embedding
        """
        if self.tokenizer is None or self.model is None:
            self.load_model()
            
        # Get entity from the database
        eid = dg.get_body_eid(self.db, node_id)
        entity = self.db.get(eid)
        if entity is None:
            return None
            
        # Get entity documentation
        doc = self.docs[entity.id.compound][entity.signature]
        docstring = doc.to_doxygen()
        print(docstring)
            
        # Tokenize and generate embedding
        tokens = self.tokenizer.tokenize(docstring)
        if len(tokens) > MAX_TOKEN_LENGTH:
            tokens = tokens[:MAX_TOKEN_LENGTH]
            
        inputs = self.tokenizer(" ".join(tokens), return_tensors="pt", padding=True, truncation=True)
        
        # Get embedding using mean pooling
        with torch.no_grad():
            outputs = self.model(**inputs)
            # Use the CLS token embedding as the entity embedding
            embedding = outputs.last_hidden_state[:, 0, :].numpy()
            
        return embedding[0]

    def generate_node_embedding_sbert(self, node_id: NodeID) -> Optional[Embedding]:
        """Generate an embedding vector for a given node using Sentence-BERT.

        Args:
            node_id: The ID of the node to generate embeddings for

        Returns:
            A numpy array representing the node embedding
        """
        if self.sbert_model is None:
            self.load_sbert_model()
            
        # Get entity from the database
        eid = dg.get_body_eid(self.db, node_id)
        entity = self.db.get(eid)
        if entity is None:
            return None
            
        # Get entity documentation
        doc = self.docs[entity.id.compound][entity.signature]
        docstring = doc.to_doxygen()

        return self.sbert_model.encode(docstring, convert_to_numpy=True, normalize_embeddings=True)

    def generate_embeddings_for_subsystems(self, subsystems: Dict[SubsystemID, Subsystem]) -> Dict[SubsystemID, Dict[NodeID, Embedding]]:
        """Generate embeddings for all nodes in given subsystems.
        
        Args:
            subsystems: Dictionary mapping subsystem names to sets of node IDs
            
        Returns:
            Dictionary mapping subsystem names to node_id -> embedding mappings
        """
        embeddings = defaultdict(dict)
        total_nodes = sum(len(subsystem.nodes) for subsystem in subsystems.values())
        current_node = 0
        
        for subsystemID, subsystem in subsystems.items():
            print(f"Generating embeddings for subsystem: {subsystemID}")

            for node_id in subsystem.nodes:
                current_node += 1
                if current_node % 20 == 0:
                    print(f"Progress: {current_node}/{total_nodes}")

                embedding = self.generate_node_embedding_sbert(node_id)
                if embedding is not None:
                    embeddings[subsystemID][node_id] = embedding

            print(f"Generated {len(embeddings[subsystemID])} embeddings for subsystem {subsystemID}")

        return embeddings

    def calculate_similarity_matrices(self, subsystem_embeddings: Dict[SubsystemID, Dict[NodeID, Embedding]]) -> Dict[SubsystemID, SimilarityMatrixData]:
        """Calculate similarity matrices for each subsystem.
        
        Args:
            subsystem_embeddings: Dictionary mapping subsystems to their node embeddings

        Returns:
            Dictionary mapping subsystem names to their similarity matrices
        """
        similarity_matrices = {}
        
        for subsystem_name, embeddings in subsystem_embeddings.items():
            if not embeddings:
                continue

            node_ids: List[NodeID] = list(embeddings.keys())
            embedding_matrix = np.array([embeddings[node_id] for node_id in node_ids])
            
            # Calculate cosine similarity matrix
            sim_matrix: SimilarityMatrix = cosine_similarity(embedding_matrix, embedding_matrix)
            
            # Store with node IDs for reference
            similarity_matrices[subsystem_name] = {
                'node_ids': node_ids,
                'matrix': sim_matrix
            }
            
        return similarity_matrices
    
    def calculate_cross_subsystem_similarities(
        self, 
        subsystem_embeddings: Dict[SubsystemID, Dict[NodeID, Embedding]]
    ) -> Dict[NodeID, Dict[SubsystemID, Dict[NodeID, float]]]:
        """Calculate similarities between nodes across different subsystems.
        
        Args:
            subsystem_embeddings: Dictionary mapping subsystems to their node embeddings
            
        Returns:
            Nested dictionary: node_id -> other_subsystem -> {other_node_id: similarity}
        """
        cross_similarities = defaultdict(lambda: defaultdict(dict))
        
        # Get all subsystems and their nodes
        all_subsystems = list(subsystem_embeddings.keys())
        
        # Calculate similarities between nodes in different subsystems
        for i, subsystem1 in enumerate(all_subsystems):
            for subsystem2 in all_subsystems[i+1:]:
                nodes1 = list(subsystem_embeddings[subsystem1].keys())
                nodes2 = list(subsystem_embeddings[subsystem2].keys())
                
                if not nodes1 or not nodes2:
                    continue
                
                # Get embedding matrices
                embeddings1 = np.array([subsystem_embeddings[subsystem1][e] for e in nodes1])
                embeddings2 = np.array([subsystem_embeddings[subsystem2][e] for e in nodes2])
                
                # Calculate cosine similarity between all nodes
                sim_matrix = cosine_similarity(embeddings1, embeddings2)
                
                # Store cross-subsystem similarities
                for i, node1 in enumerate(nodes1):
                    for j, node2 in enumerate(nodes2):
                        sim_score = sim_matrix[i, j]
                        cross_similarities[node1][subsystem2][node2] = sim_score
                        cross_similarities[node2][subsystem1][node1] = sim_score
                        
        return cross_similarities
    
    def identify_outliers(
        self, 
        subsystems: Dict[SubsystemID, Subsystem],
        similarity_matrices: Dict[SubsystemID, SimilarityMatrixData],
        threshold: float = SIMILARITY_THRESHOLD
    ) -> List[Dict[str, Any]]:
        """Identify nodes with low similarity to their assigned subsystem.
        
        Args:
            subsystems: Dictionary mapping subsystem names to sets of node IDs
            similarity_matrices: Dictionary of similarity matrices by subsystem
            threshold: Similarity threshold below which nodes are considered outliers
            
        Returns:
            List of dictionaries with outlier information
        """
        outliers = []
        
        for subsystem_name, sim_data in similarity_matrices.items():
            node_ids: List[NodeID] = sim_data['node_ids']
            sim_matrix: SimilarityMatrix = sim_data['matrix']
            
            # Calculate average similarity for each node to all others in same subsystem
            for i, node_id in enumerate(node_ids):
                # Exclude self-similarity (1.0)
                similarities: List[float] = [sim_matrix[i, j] for j in range(len(node_ids)) if i != j]

                if not similarities:
                    continue
                    
                avg_similarity = np.mean(similarities)
                
                # If average similarity is below threshold, mark as outlier
                if avg_similarity < threshold:
                    node = self.db.get(node_id)
                    outlier_info = {
                        'node_id': node_id,
                        'name': node.name if node else "Unknown",
                        'current_subsystem': subsystem_name,
                        'average_similarity': float(avg_similarity),
                        'confidence': float(1.0 - avg_similarity)  # Lower similarity = higher confidence it's an outlier
                    }
                    outliers.append(outlier_info)
                    
        # Sort by confidence (highest first)
        outliers.sort(key=lambda x: x['confidence'], reverse=True)
        return outliers
    
    def suggest_regroupings(
        self, 
        outliers: List[Dict[str, Any]],
        cross_similarities: Dict[NodeID, Dict[SubsystemID, Dict[NodeID, float]]]
    ) -> List[Dict[str, Any]]:
        """Suggest new subsystem assignments for outlier nodes.
        
        Args:
            outliers: List of outlier nodes
            cross_similarities: Cross-subsystem similarity information
            
        Returns:
            List of dictionaries with regrouping suggestions
        """
        suggestions = []
        
        for outlier in outliers:
            nodeID: NodeID = outlier['node_id']
            current_subsystemID: SubsystemID = outlier['current_subsystem']

            # Skip if no cross-similarities available for this node
            if nodeID not in cross_similarities:
                continue
                
            # Find subsystem with highest average similarity
            best_subsystemID: SubsystemID = None
            best_similarity: float = 0.0
            best_nodes = []

            for subsystemID, similarities in cross_similarities[nodeID].items():
                if subsystemID == current_subsystemID:
                    continue
                
                if not similarities:
                    continue
                    
                avg_similarity = np.mean(list(similarities.values()))
                
                if avg_similarity > best_similarity:
                    best_similarity = avg_similarity
                    best_subsystemID = subsystemID

                    # Get top 3 most similar nodes in the subsystem
                    sorted_similarities = sorted(similarities.items(), key=lambda x: x[1], reverse=True)[:3]
                    best_similarities = [{'node_id': e, 'similarity': float(s)} for e, s in sorted_similarities]
            
            # Only suggest if the best similarity exceeds the original subsystem's
            if best_subsystemID and best_similarity > outlier['average_similarity']:
                suggestion = {
                    'node_id': nodeID,
                    'name': outlier['name'],
                    'current_subsystem': current_subsystemID,
                    'suggested_subsystem': best_subsystemID,
                    'current_similarity': float(outlier['average_similarity']),
                    'suggested_similarity': float(best_similarity),
#                    'confidence': float(best_similarity - outlier['average_similarity']),
                    'similar_nodes': best_similarities
                }
                suggestions.append(suggestion)

        max_similarity_difference = max((s['suggested_similarity'] - s['current_similarity'] for s in suggestions), default=0.0)
        for suggestion in suggestions:
            # Normalize confidence based on max similarity difference
            if max_similarity_difference > 0:
                suggestion['confidence'] = (suggestion['suggested_similarity'] - suggestion['current_similarity']) / max_similarity_difference
            else:
                suggestion['confidence'] = 0.0

        # Sort by confidence (highest first)
        suggestions.sort(key=lambda x: x['confidence'], reverse=True)
        return suggestions

    def refine_subsystems(self, subsystems: Dict[SubsystemID, Subsystem], embeddings: Dict[SubsystemID, Dict[NodeID, Embedding]]) -> Dict:
        """Perform embedding-based refinement on subsystem assignments.
        
        Args:
            subsystems: Dictionary mapping subsystem names to sets of node IDs
            
        Returns:
            Dictionary with refinement results
        """
        print("Starting embedding-based subsystem refinement...")
                
        # Calculate similarity matrices within subsystems
        similarity_matrices = self.calculate_similarity_matrices(embeddings)
        
        # Calculate similarities across subsystems
        cross_similarities = self.calculate_cross_subsystem_similarities(embeddings)
        
        # Identify outliers within each subsystem
        outliers = self.identify_outliers(subsystems, similarity_matrices)
        
        # Suggest regroupings for outliers
        suggestions = self.suggest_regroupings(outliers, cross_similarities)
        
        # Create refined subsystems by applying high-confidence suggestions
        refined_subsystems = {name: Subsystem.from_dict(s.to_dict()) for name, s in subsystems.items()}
        applied_suggestions = []
        
        for suggestion in suggestions:
            if suggestion['confidence'] > CONFIDENCE_THRESHOLD:
                node_id = suggestion['node_id']
                current = suggestion['current_subsystem']
                target = suggestion['suggested_subsystem']
                
                # Move node to suggested subsystem
                refined_subsystems[current].nodes.remove(node_id)
                refined_subsystems[target].nodes.add(node_id)
                applied_suggestions.append(suggestion)
        
        result = {
            'original_subsystems': {name: list(subsystem.nodes) for name, subsystem in subsystems.items()},
            'refined_subsystems': {name: list(subsystem.nodes) for name, subsystem in refined_subsystems.items()},
            'outliers': outliers,
            'suggestions': suggestions,
            'applied_suggestions': applied_suggestions,
            'stats': {
                'total_outliers': len(outliers),
                'total_suggestions': len(suggestions),
                'applied_suggestions': len(applied_suggestions)
            }
        }
        
        print(f"Refinement complete. Found {len(outliers)} outliers, made {len(suggestions)} suggestions, applied {len(applied_suggestions)}.")
        return result
        
    def save_refinement_results(self, results: Dict, output_path: str):
        """Save refinement results to a JSON file.
        
        Args:
            results: Dictionary with refinement results
            output_path: Path to save the JSON file
        """
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"Refinement results saved to {output_path}")
    
    def generate_refinement_report(self, results: Dict, output_path: str):
        """Generate a markdown report of refinement results.
        
        Args:
            results: Dictionary with refinement results
            output_path: Path to save the markdown report
        """
        outliers = results['outliers']
        suggestions = results['suggestions']
        applied = results['applied_suggestions']
        stats = results['stats']
        
        # Generate report content
        report = [
            "# Embedding-Based Subsystem Refinement Report",
            "",
            "## Overview",
            "",
            f"- Total nodes analyzed: {sum(len(group) for group in results['original_subsystems'].values())}",
            f"- Total subsystems: {len(results['original_subsystems'])}",
            f"- Outliers detected: {stats['total_outliers']}",
            f"- Regrouping suggestions: {stats['total_suggestions']}",
            f"- Applied suggestions: {stats['applied_suggestions']}",
            "",
            "## Applied Regroupings",
            "",
        ]
        
        if applied:
            report.append("| Entity | From Subsystem | To Subsystem | Confidence |")
            report.append("|--------|---------------|-------------|------------|")
            for item in applied:
                report.append(f"| {item['name']} | {item['current_subsystem']} | {item['suggested_subsystem']} | {item['confidence']:.3f} |")
        else:
            report.append("No regroupings were applied with high confidence.")
            
        report.extend([
            "",
            "## All Detected Outliers",
            "",
            "| Entity | Subsystem | Avg Similarity | Confidence |",
            "|--------|-----------|---------------|------------|",
        ])
        
        for item in outliers[:50]:  # Limit to top 50
            report.append(f"| {item['name']} | {item['current_subsystem']} | {item['average_similarity']:.3f} | {item['confidence']:.3f} |")
            
        report.extend([
            "",
            "## All Regrouping Suggestions",
            "",
            "| Entity | Current Subsystem | Suggested Subsystem | Current Similarity | Suggested Similarity | Confidence |",
            "|--------|------------------|---------------------|-------------------|---------------------|------------|",
        ])
        
        for item in suggestions[:50]:  # Limit to top 50
            report.append(f"| {item['name']} | {item['current_subsystem']} | {item['suggested_subsystem']} | {item['current_similarity']:.3f} | {item['suggested_similarity']:.3f} | {item['confidence']:.3f} |")
            
        # Write report
        with open(output_path, 'w') as f:
            f.write("\n".join(report))
            
        print(f"Refinement report saved to {output_path}")
