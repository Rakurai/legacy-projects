"""
Subsystem Documenter Module

This module contains functionality for generating detailed documentation
for each subsystem identified in the codebase.
"""

from collections import defaultdict, Counter
from typing import Dict, List, Set, Tuple, Any, Optional
import networkx as nx
from pathlib import Path

from . import subsystem_utils as su

def identify_subsystem_interfaces(
    subsystem: su.Subsystem,
    entity_db,
    graph: nx.Graph,
    all_subsystems: Dict[str, su.Subsystem]
) -> Dict[str, Set[str]]:
    """
    Identify the interfaces of a subsystem.
    
    Args:
        subsystem: Subsystem to analyze
        entity_db: Entity database
        graph: NetworkX dependency graph
        all_subsystems: Dictionary of all subsystems
        
    Returns:
        Dictionary with 'incoming' and 'outgoing' interface sets
    """
    # Create a mapping from entity to subsystem
    entity_to_subsystem = {}
    for s_id, s in all_subsystems.items():
        for entity in s.nodes:
            entity_to_subsystem[entity] = s_id
            
    # Identify incoming and outgoing interfaces
    incoming = set()
    outgoing = set()

    for entity in subsystem.nodes:
        # Check outgoing edges (dependencies)
        for target in graph.successors(entity):
            if target in entity_to_subsystem and entity_to_subsystem[target] != subsystem.subsystem_id:
                outgoing.add(target)
                
        # Check incoming edges (dependents)
        for source in graph.predecessors(entity):
            if source in entity_to_subsystem and entity_to_subsystem[source] != subsystem.subsystem_id:
                incoming.add(entity)  # This entity is an interface
    
    return {
        'incoming': incoming,
        'outgoing': outgoing
    }

def identify_key_entities(
    subsystem: su.Subsystem,
    entity_db,
    graph: nx.Graph,
    n: int = 5
) -> List[str]:
    """
    Identify the most important entities in a subsystem based on connectivity.
    
    Args:
        subsystem: Subsystem to analyze
        entity_db: Entity database
        graph: NetworkX dependency graph
        n: Number of key entities to identify
        
    Returns:
        List of entity IDs
    """
    if not subsystem.nodes:
        return []
        
    # Create subgraph for this subsystem
    subgraph = graph.subgraph(subsystem.nodes)
    
    # Calculate centrality metrics
    try:
        # Try betweenness centrality first (identifies bridging components)
        centrality = nx.betweenness_centrality(subgraph)
    except:
        try:
            # Fallback to degree centrality (identifies hubs)
            centrality = nx.degree_centrality(subgraph)
        except:
            # Last resort - just count degrees
            centrality = {node: subgraph.degree(node) for node in subgraph.nodes()}
    
    # Return top n entities by centrality
    top_entities = sorted(centrality.items(), key=lambda x: x[1], reverse=True)
    return [entity for entity, _ in top_entities[:n]]

def format_entity_reference(entity_id: str, entity_db) -> str:
    """
    Format an entity reference for documentation.
    
    Args:
        entity_id: Entity ID
        entity_db: Entity database
        
    Returns:
        Formatted entity reference string
    """
    entity = su.get_entity(entity_db, entity_id)
    
    if entity:
        name = entity.name
        kind = entity.kind
        return f"`{name}` ({kind})"
    else:
        return f"`{entity_id}` (Unknown)"

def generate_subsystem_document(
    subsystem: su.Subsystem,
    entity_db,
    graph: nx.Graph,
    all_subsystems: Dict[str, su.Subsystem],
    docs_db
) -> str:
    """
    Generate detailed documentation for a subsystem.
    
    Args:
        subsystem: Subsystem to document
        entity_db: Entity database
        graph: NetworkX dependency graph
        all_subsystems: Dictionary of all subsystems
        docs_db: Document database
        
    Returns:
        Markdown content for subsystem documentation
    """
    # Identify interfaces
    interfaces = identify_subsystem_interfaces(subsystem, entity_db, graph, all_subsystems)
    
    # Identify key entities
    key_entities = identify_key_entities(subsystem, entity_db, graph)
    
    # Get sample nodes (including key entities)
    sample_size = min(10, len(subsystem.nodes))
    sample = set(key_entities)
    
    # Add other entities to sample if needed
    other_entities = sorted(list(subsystem.nodes - set(key_entities)))
    sample.update(other_entities[:max(0, sample_size - len(sample))])
    
    # Format components section
    components = []
    for entity_id in sorted(sample):
        components.append(format_entity_reference(entity_id, entity_db))
        
    if len(subsystem.nodes) > sample_size:
        components.append(f"*...and {len(subsystem.nodes) - len(sample)} more*")
        
    components_str = "\n".join(components) if components else "No components identified."
    
    # Format key concepts
    key_concepts = "No key concepts identified."
    if 'key_concepts' in subsystem.metadata and subsystem.metadata['key_concepts']:
        key_concepts = "\n".join([f"- {word.capitalize()}" for word in subsystem.metadata['key_concepts']])
    
    # Format interfaces
    interface_lines = []
    
    if interfaces['incoming']:
        interface_lines.append("### Incoming Interfaces")
        interface_lines.append("These components serve as entry points to the subsystem:")
        
        for node_id in sorted(interfaces['incoming']):
            interface_lines.append(f"- {format_entity_reference(node_id, entity_db)}")
                
    if interfaces['outgoing']:
        if interface_lines:
            interface_lines.append("")
            
        interface_lines.append("### Outgoing Interfaces")
        interface_lines.append("These external components are used by this subsystem:")
        
        for node_id in sorted(interfaces['outgoing']):
            interface_lines.append(f"- {format_entity_reference(node_id, entity_db)}")
                
    interfaces_str = "\n".join(interface_lines) if interface_lines else "No interfaces identified."
    
    # Format dependencies
    from hierarchy_builder import identify_subsystem_dependencies
    dependencies = identify_subsystem_dependencies(subsystem, entity_db, graph, all_subsystems)
    
    dependency_lines = []
    
    if dependencies:
        # Sort by dependency count
        sorted_deps = sorted(dependencies.items(), key=lambda x: x[1], reverse=True)
        
        for dep_id, count in sorted_deps:
            if dep_id in all_subsystems:
                dep_name = all_subsystems[dep_id].name
                dependency_lines.append(f"- **{dep_name}** ({count} connections)")
    
    dependencies_str = "\n".join(dependency_lines) if dependency_lines else "No external dependencies identified."
    
    # Extract documentation for key entities
    doc_samples = []
    for entity_id in key_entities[:3]:  # Limit to top 3 for brevity
        entity = su.get_entity(entity_db, entity_id)
        if entity:
            # Try to get documentation
            doc = None
            if hasattr(entity, 'compound') and hasattr(entity, 'member'):
                doc = su.get_doc(docs_db, entity.compound, entity.member)
            
            if doc and (doc.brief or doc.details):
                doc_samples.append(f"### {entity.name}\n")
                if doc.brief:
                    doc_samples.append(f"{doc.brief}\n")
                if doc.details:
                    doc_samples.append(f"{doc.details}\n")
    
    docs_str = "\n".join(doc_samples) if doc_samples else "No detailed documentation available for key components."
    
    # Generate document content
    template = """# {name}

**Classification**: {classification}
**ID**: {subsystem_id}

## Overview

This subsystem contains {entity_count} entities and represents a cohesive functional unit within the Legacy MUD codebase.
{internal_connectivity_info}

## Key Concepts

{key_concepts}

## Components

{components}

## Interfaces

{interfaces}

## Dependencies

{dependencies}

## Documentation Samples

{docs}
"""
    
    # Prepare connectivity info
    connectivity_info = ""
    if 'internal_connectivity' in subsystem.metadata:
        conn = subsystem.metadata['internal_connectivity']
        if conn > 0.5:
            connectivity_info = "\nIt has high internal connectivity, suggesting a tightly coupled design."
        elif conn > 0.2:
            connectivity_info = "\nIt has moderate internal connectivity."
        else:
            connectivity_info = "\nIt has low internal connectivity, suggesting a loosely coupled design."
    
    # Fill template
    doc_content = template.format(
        name=subsystem.name,
        classification=subsystem.classification,
        subsystem_id=subsystem.subsystem_id,
        entity_count=len(subsystem.nodes),
        internal_connectivity_info=connectivity_info,
        key_concepts=key_concepts,
        components=components_str,
        interfaces=interfaces_str,
        dependencies=dependencies_str,
        docs=docs_str
    )
    
    return doc_content

def generate_all_subsystem_documents(
    subsystems: Dict[str, su.Subsystem],
    entity_db,
    graph: nx.Graph,
    docs_db,
    output_dir: Path
) -> None:
    """
    Generate documentation for all subsystems.
    
    Args:
        subsystems: Dictionary of subsystem objects
        entity_db: Entity database
        graph: NetworkX dependency graph
        docs_db: Document database
        output_dir: Output directory for documentation files
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    for subsystem_id, subsystem in subsystems.items():
        # Generate document
        doc_content = generate_subsystem_document(
            subsystem, entity_db, graph, subsystems, docs_db)
        
        # Generate filename
        filename = f"{subsystem.name.lower().replace(' ', '_')}.md"
        doc_path = output_dir / filename
        
        # Save document
        with open(doc_path, 'w') as f:
            f.write(doc_content)
