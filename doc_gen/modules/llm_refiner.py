"""
LLM-based refinement module for subsystem discovery.

This module provides functionality to:
1. Generate summaries for subsystem clusters
2. Create templates for LLM-based evaluation of subsystems
3. Use LLMs to analyze and detect outlier entities in subsystems
4. Suggest regroupings based on semantic coherence
"""

import os
import json
import numpy as np
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any, Optional
from collections import defaultdict
from jinja2 import Environment, FileSystemLoader

import subsystem_utils as su
import doc_db
import doxygen_parse as dp
import doxygen_graph as dg
import networkx as nx
from llm_utils import call_openai, call_ollama

# Constants
DEFAULT_MODEL = "gpt-4.1-nano"
DEFAULT_MAX_TOKENS = 2000
CONFIDENCE_THRESHOLD = 0.7  # Threshold for regrouping suggestions
MAX_ENTITIES_PER_PROMPT = 10  # Maximum number of entities to include in a single prompt

from subsystem_utils import NodeID, SubsystemID, Subsystem


class LLMRefiner:
    """Class for refining subsystem assignments using LLM-based evaluation."""

    def __init__(self, db: dp.EntityDatabase, graph: nx.Graph, doc_database: Optional[doc_db.DocumentDB] = None, templates_dir: Optional[str] = None, use_ollama: bool = False):
        """Initialize the LLM refiner with necessary data.
        
        Args:
            db: The Doxygen entity database
            graph: The NetworkX dependency graph
            doc_database: The documentation database (defaults to doc_db.docs)
            templates_dir: Directory containing Jinja2 templates
            use_ollama: Whether to use Ollama instead of OpenAI
        """
        self.db: dp.EntityDatabase = db
        self.graph: nx.Graph = graph
        self.docs: doc_db.DocumentDB = doc_database if doc_database is not None else doc_db.docs
        
        # Set up template environment
        if templates_dir is None:
            project_root = Path('../..').resolve()
            templates_dir = project_root / ".ai/templates"
        
        self.env = Environment(loader=FileSystemLoader(templates_dir))
        self.use_ollama = use_ollama
    
    def get_entity_from_node_id(self, node_id: NodeID) -> Optional[dp.DoxygenEntity]:
        """Retrieve the entity associated with a given node ID.

        Args:
            node_id: The ID of the node to retrieve

        Returns:
            The corresponding Subsystem entity, or None if not found
        """
        eid = dg.get_body_eid(self.db, node_id)
        return self.db.get(eid)

    def generate_entity_summary(self, node_id: NodeID) -> str:
        entity = self.get_entity_from_node_id(node_id)
        if entity is None:
            return "Unknown entity"
        
        doc = None
        if entity.id.compound in self.docs and entity.signature in self.docs[entity.id.compound]:
            doc = self.docs[entity.id.compound][entity.signature]
        
        description_parts = []
        kind = entity.kind if entity.kind else "unknown"
        name = entity.name if entity.name else node_id.split('/')[-1]
        description_parts.append(f"[{kind}] {entity.name}")
        if entity.signature and entity.signature != entity.name:
            description_parts.append(f"Signature: {entity.signature}")
        if doc:
            if doc.brief:
                description_parts.append(f"Brief: {doc.brief}")
            if doc.details:
                description_parts.append(f"Details: {doc.details}")

        # Add consumer/caller context
        for caller in self.graph.predecessors(node_id):
            if self.graph[caller].get('type') in (dg.EntityType.COMPOUND, dg.EntityType.MEMBER):
                description_parts.append(f"Called by: {self.graph[caller].get('name')}")

        print(description_parts)
        return " | ".join(description_parts)

    def generate_entity_summary_old(self, node_id: NodeID) -> str:
        """Generate a summary description of an entity.
        
        Args:
            node_id: The ID of the entity to summarize
            
        Returns:
            A string summary of the entity
        """
        entity = self.get_entity_from_node_id(node_id)
        if entity is None:
            return "Unknown entity"
            
        # Get entity documentation
        doc = None
        if entity.id.compound in self.docs and entity.signature in self.docs[entity.id.compound]:
            doc = self.docs[entity.id.compound][entity.signature]
        
        description_parts = []
        
        # Add entity information
        kind = entity.kind if entity.kind else "unknown"
        name = entity.name if entity.name else node_id.split('/')[-1]
        description_parts.append(f"[{kind}] {entity.name}")
        
        # Add signature if available
        if entity.signature and entity.signature != entity.name:
            description_parts.append(f"Signature: {entity.signature}")
        
        # Add documentation if available
        if doc:
            if doc.brief:
                description_parts.append(f"Brief: {doc.brief}")
            if doc.details:
                description_parts.append(f"Details: {doc.details}")
        
        return " | ".join(description_parts)
    
    def generate_subsystem_summary(self, subsystem_name: SubsystemID, node_ids: Set[NodeID]) -> str:
        """Generate a summary for a subsystem based on its entities.
        
        Args:
            subsystem_name: The name of the subsystem
            node_ids: A set of entity IDs in the subsystem
            
        Returns:
            A summary of the subsystem
        """
        # Generate summaries for each entity
        entity_summaries = []
        for node_id in node_ids:
            summary = self.generate_entity_summary(node_id)
            entity_summaries.append(summary)
        
        # Compile the subsystem summary
        subsystem_summary = f"# {subsystem_name} Subsystem\n\n"
        subsystem_summary += f"Contains {len(node_ids)} entities:\n\n"
        for summary in entity_summaries:
            subsystem_summary += f"- {summary}\n"

        print(subsystem_summary)
        return subsystem_summary
    
    def create_outlier_detection_template(self) -> str:
        """Create a Jinja2 template for LLM-based outlier detection.
        
        Returns:
            Path to the created template file
        """
        template_path = "llm_outlier_detection.j2"
        template_content = """You are analyzing a subsystem in a legacy codebase to determine if any entities (functions, classes, variables, etc.) should be moved to a different subsystem.

### Current Subsystem: {{ subsystem_name }}

Here's a description of the main purpose and functionality of this subsystem:
{{ subsystem_description }}

### Potential Outlier Entities
I'll provide a list of entities that belong to this subsystem. For each entity, determine if it semantically belongs in this subsystem or if it seems out of place:

{% for entity in entities %}
Entity {{ loop.index }}: {{ entity.summary }}
{% endfor %}

For each entity, please analyze:
1. How well does it align with the subsystem's core purpose? 
2. Would it make more conceptual sense in a different subsystem?

Return your analysis in the following JSON format:
```json
{
  "entities": [
    {
      "node_id": "entity_id_1", 
      "is_outlier": true/false,
      "confidence": 0.1-1.0 (higher = more confident),
      "reasoning": "Brief explanation of your reasoning",
      "suggested_subsystem": "Name of better subsystem (if outlier)"
    },
    ...
  ]
}
```

Only include the JSON response without any other text.
"""
        # Create the template if it doesn't exist
        template_file_path = Path(self.env.loader.searchpath[0]) / template_path
        if not template_file_path.exists():
            with open(template_file_path, 'w') as f:
                f.write(template_content)
                
        return template_path
    
    def create_subsystem_comparison_template(self) -> str:
        """Create a Jinja2 template for comparing subsystems to find better fits for entities.
        
        Returns:
            Path to the created template file
        """
        template_path = "llm_subsystem_comparison.j2"
        template_content = """You are helping refine the organization of entities in a legacy codebase. An entity has been identified as potentially belonging to a different subsystem than its current assignment.

### Entity Details
{{ entity.summary }}

### Current Subsystem: {{ current_subsystem.name }}
{{ current_subsystem.description }}

### Potential New Subsystems
{% for subsystem in candidate_subsystems %}
Candidate {{ loop.index }}: {{ subsystem.name }}
{{ subsystem.description }}
{% endfor %}

Analyze which subsystem this entity belongs to most naturally based on its semantic meaning, purpose, and functionality. Consider:
1. Conceptual coherence with the subsystem's purpose
2. Functional alignment with other entities in the subsystem
3. Role within the overall system architecture

Return your analysis in the following JSON format:
```json
{
  "best_subsystem": "name_of_best_subsystem",
  "confidence": 0.1-1.0 (higher = more confident),
  "reasoning": "Brief explanation of your reasoning",
  "subsystem_rankings": [
    {"name": "subsystem1", "score": 0.1-1.0, "reason": "brief reason"},
    {"name": "subsystem2", "score": 0.1-1.0, "reason": "brief reason"},
    ...
  ]
}
```

Only include the JSON response without any other text.
"""
        # Create the template if it doesn't exist
        template_file_path = Path(self.env.loader.searchpath[0]) / template_path
        if not template_file_path.exists():
            with open(template_file_path, 'w') as f:
                f.write(template_content)
                
        return template_path
    
    def render_template(self, template_name: str, **context: Any) -> str:
        """Render a Jinja2 template with the given context.
        
        Args:
            template_name: Name of the template to render
            **context: Context variables for the template
            
        Returns:
            The rendered template as a string
        """
        template = self.env.get_template(template_name)
        return template.render(**context)
    
    def call_llm(self, prompt: str, model: str = DEFAULT_MODEL, max_tokens: int = DEFAULT_MAX_TOKENS) -> str:
        """Call the LLM with the given prompt.
        
        Args:
            prompt: The prompt to send to the LLM
            model: Model to use
            max_tokens: Maximum tokens to generate
            
        Returns:
            The LLM's response as a string
        """
        if self.use_ollama:
            return call_ollama(prompt, model, max_tokens)
        else:
            return call_openai(prompt, model, max_tokens)
    
    def process_llm_response(self, response: str) -> Dict:
        """Process the LLM response and extract JSON data.
        
        Args:
            response: The raw LLM response
            
        Returns:
            Parsed JSON data or empty dict if parsing fails
        """
        try:
            # Extract JSON data from response (might be wrapped in markdown code blocks)
            json_str = response.strip()
            if "```json" in json_str:
                json_str = json_str.split("```json", 1)[1]
                
            if "```" in json_str:
                json_str = json_str.split("```", 1)[0]
                
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            print(f"Failed to parse JSON response: {e}")
            return {}
    
    def detect_outliers_in_subsystem(
        self, 
        subsystem_name: SubsystemID, 
        node_ids: Set[NodeID], 
        subsystem_description: str = None
    ) -> List[Dict]:
        """Use LLM to detect outliers in a subsystem.
        
        Args:
            subsystem_name: The name of the subsystem
            node_ids: Set of entity IDs in the subsystem
            subsystem_description: Optional description of the subsystem
            
        Returns:
            List of dictionaries with outlier information
        """
        # Create outlier detection template if needed
        template_path = self.create_outlier_detection_template()
        
        # Generate subsystem description if not provided
        if subsystem_description is None:
            subsystem_description = f"A subsystem named '{subsystem_name}' containing {len(node_ids)} entities."
        
        # Process entities in batches to avoid token limits
        entity_list = list(node_ids)
        outliers = []
        
        for i in range(0, len(entity_list), MAX_ENTITIES_PER_PROMPT):
            batch = entity_list[i:i + MAX_ENTITIES_PER_PROMPT]
            
            # Generate entity summaries for this batch
            entity_data = []
            for node_id in batch:
                summary = self.generate_entity_summary(node_id)
                entity_data.append({
                    "id": node_id,
                    "summary": summary
                })
            
            # Render template and call LLM
            prompt = self.render_template(template_path, 
                                         subsystem_name=subsystem_name,
                                         subsystem_description=subsystem_description,
                                         entities=entity_data)
            
            response = self.call_llm(prompt)
            results = self.process_llm_response(response)
            
            # Extract outliers from response
            if 'entities' in results:
                for entity in results['entities']:
                    if entity.get('is_outlier', False):
                        # Add subsystem info
                        entity['current_subsystem'] = subsystem_name
                        outliers.append(entity)
        
        return outliers
    
    def find_best_subsystem_for_entity(
        self, 
        node_id: NodeID, 
        current_subsystem: str, 
        candidate_subsystems: Dict[SubsystemID, Set[NodeID]]
    ) -> Dict:
        """Find the best subsystem for an entity using LLM comparison.
        
        Args:
            node_id: ID of the entity to evaluate
            current_subsystem: Name of the entity's current subsystem
            candidate_subsystems: Dict of subsystem names to entity IDs
            
        Returns:
            Dictionary with comparison results
        """
        # Create subsystem comparison template if needed
        template_path = self.create_subsystem_comparison_template()
        
        # Generate entity summary
        entity_summary = self.generate_entity_summary(node_id)
        
        # Generate subsystem summaries
        subsystem_data = []
        for name, entities in candidate_subsystems.items():
            if name == current_subsystem:
                continue
                
            # Generate a condensed description of the subsystem
            description = f"Subsystem containing {len(entities)} entities, including:"
            # Sample a few entities for the description
            sample = list(entities)[:5] if len(entities) > 5 else list(entities)
            for eid in sample:
                summary = self.generate_entity_summary(eid)
                description += f"\n- {summary}"
                
            subsystem_data.append({
                "name": name,
                "description": description
            })
        
        # Generate current subsystem description
        current_entities = candidate_subsystems[current_subsystem]
        current_description = f"Subsystem containing {len(current_entities)} entities, including:"
        # Sample a few entities for the description
        sample = [eid for eid in current_entities if eid != node_id][:5]
        for eid in sample:
            summary = self.generate_entity_summary(eid)
            current_description += f"\n- {summary}"
            
        # Render template and call LLM
        prompt = self.render_template(template_path,
                                     entity={"id": node_id, "summary": entity_summary},
                                     current_subsystem={"name": current_subsystem, "description": current_description},
                                     candidate_subsystems=subsystem_data)
        
        response = self.call_llm(prompt)
        results = self.process_llm_response(response)
        
        # Add entity info to results
        results["node_id"] = node_id
        results["current_subsystem"] = current_subsystem
        
        return results
    
    def refine_subsystems(self, subsystems: Dict[SubsystemID, Set[NodeID]]) -> Dict:
        """Perform LLM-based refinement on subsystem assignments.
        
        Args:
            subsystems: Dictionary mapping subsystem names to sets of entity IDs
            
        Returns:
            Dictionary with refinement results
        """
        print("Starting LLM-based subsystem refinement...")
        
        # Step 1: Detect outliers in each subsystem
        all_outliers = []
        for subsystem_name, node_ids in subsystems.items():
            print(f"Analyzing subsystem: {subsystem_name} ({len(node_ids)} entities)")
            
            # Generate a high-level description for the subsystem
            subsystem_summary = self.generate_subsystem_summary(subsystem_name, node_ids)
            subsystem_description = subsystem_summary.split('\n\n', 1)[0]
            
            # Detect outliers
            outliers = self.detect_outliers_in_subsystem(subsystem_name, node_ids, subsystem_description)
            all_outliers.extend(outliers)
            print(f"Detected {len(outliers)} potential outliers in {subsystem_name}")
        
        # Step 2: For each outlier, find the best subsystem
        suggestions = []
        for outlier in all_outliers:
            node_id = outlier['node_id']
            current_subsystem = outlier['current_subsystem']

            # Find best subsystem
            if outlier.get('suggested_subsystem'):
                # If LLM already suggested a subsystem, use that
                suggestion = {
                    'node_id': node_id,
                    'current_subsystem': current_subsystem,
                    'suggested_subsystem': outlier['suggested_subsystem'],
                    'confidence': outlier.get('confidence', 0.5),
                    'reasoning': outlier.get('reasoning', 'LLM detected semantic mismatch')
                }
                suggestions.append(suggestion)
            else:
                # Otherwise, compare with other subsystems
                comparison = self.find_best_subsystem_for_entity(node_id, current_subsystem, subsystems)
                if comparison.get('best_subsystem'):
                    suggestion = {
                        'node_id': node_id,
                        'current_subsystem': current_subsystem,
                        'suggested_subsystem': comparison['best_subsystem'],
                        'confidence': comparison.get('confidence', 0.5),
                        'reasoning': comparison.get('reasoning', 'Determined through subsystem comparison')
                    }
                    suggestions.append(suggestion)
        
        # Step 3: Apply high-confidence suggestions to create refined subsystems
        refined_subsystems = {name: set(entities) for name, entities in subsystems.items()}
        applied_suggestions = []
        
        for suggestion in suggestions:
            if suggestion['confidence'] > CONFIDENCE_THRESHOLD:
                node_id = suggestion['entity_id']
                current = suggestion['current_subsystem']
                target = suggestion['suggested_subsystem']
                
                if target in refined_subsystems:
                    # Move entity to suggested subsystem
                    refined_subsystems[current].remove(node_id)
                    refined_subsystems[target].add(node_id)
                    applied_suggestions.append(suggestion)
        
        result = {
            'original_subsystems': {name: list(entities) for name, entities in subsystems.items()},
            'refined_subsystems': {name: list(entities) for name, entities in refined_subsystems.items()},
            'outliers': all_outliers,
            'suggestions': suggestions,
            'applied_suggestions': applied_suggestions,
            'stats': {
                'total_outliers': len(all_outliers),
                'total_suggestions': len(suggestions),
                'applied_suggestions': len(applied_suggestions)
            }
        }
        
        print(f"Refinement complete. Found {len(all_outliers)} outliers, made {len(suggestions)} suggestions, applied {len(applied_suggestions)}.")
        return result
    
    def save_refinement_results(self, results: Dict, output_path: str) -> None:
        """Save refinement results to a JSON file.
        
        Args:
            results: Dictionary with refinement results
            output_path: Path to save the JSON file
        """
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"Refinement results saved to {output_path}")
    
    def generate_refinement_report(self, results: Dict, output_path: str) -> None:
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
            "# LLM-Based Subsystem Refinement Report",
            "",
            "## Overview",
            "",
            f"- Total entities analyzed: {sum(len(group) for group in results['original_subsystems'].values())}",
            f"- Total subsystems: {len(results['original_subsystems'])}",
            f"- Outliers detected: {stats['total_outliers']}",
            f"- Regrouping suggestions: {stats['total_suggestions']}",
            f"- Applied suggestions: {stats['applied_suggestions']}",
            "",
            "## Applied Regroupings",
            "",
        ]
        
        if applied:
            report.append("| Node | From Subsystem | To Subsystem | Confidence | Reasoning |")
            report.append("|------|---------------|-------------|------------|-----------|")
            for item in applied:
                entity = self.get_entity_from_node_id(item['node_id'])
                entity_name = entity.name if entity else item['node_id']
                report.append(f"| {entity_name} | {item['current_subsystem']} | {item['suggested_subsystem']} | {item['confidence']:.3f} | {item['reasoning']} |")
        else:
            report.append("No regroupings were applied with high confidence.")

        report.extend([
            "",
            "## All Detected Outliers",
            "",
            "| Node | Subsystem | Confidence | Reasoning |",
            "|------|-----------|------------|-----------|",
        ])

        for item in outliers[:50]:  # Limit to top 50
            entity = self.db.get(item['node_id'])
            entity_name = entity.name if entity else item['node_id']
            report.append(f"| {entity_name} | {item['current_subsystem']} | {item.get('confidence', 'N/A')} | {item.get('reasoning', 'Not specified')} |")

        report.extend([
            "",
            "## All Regrouping Suggestions",
            "",
            "| Node | Current Subsystem | Suggested Subsystem | Confidence | Reasoning |",
            "|------|------------------|---------------------|------------|-----------|",
        ])

        for item in suggestions[:50]:  # Limit to top 50
            entity = self.get_entity_from_node_id(item['node_id'])
            entity_name = entity.name if entity else item['node_id']
            report.append(f"| {entity_name} | {item['current_subsystem']} | {item['suggested_subsystem']} | {item.get('confidence', 'N/A')} | {item.get('reasoning', 'Not specified')} |")
            
        # Write report
        with open(output_path, 'w') as f:
            f.write("\n".join(report))
            
        print(f"Refinement report saved to {output_path}")


def refine_subsystems_with_llm(db, graph, subsystems: Dict[SubsystemID, Set[NodeID]], output_dir, use_ollama=False):
    """Refine subsystems using LLM-based analysis and save results.
    
    Args:
        db: The Doxygen entity database
        graph: The NetworkX dependency graph
        subsystems: Dictionary mapping subsystem names to sets of entity IDs
        output_dir: Directory to save results
        use_ollama: Whether to use Ollama instead of OpenAI
        
    Returns:
        Dictionary with refinement results
    """
    refiner = LLMRefiner(db, graph, use_ollama=use_ollama)
    results = refiner.refine_subsystems(subsystems)
    
    # Save results and report
    os.makedirs(output_dir, exist_ok=True)
    
    json_path = os.path.join(output_dir, "llm_refined_clusters.json")
    report_path = os.path.join(output_dir, "llm_refinement_report.md")
    
    refiner.save_refinement_results(results, json_path)
    refiner.generate_refinement_report(results, report_path)
    
    return results
