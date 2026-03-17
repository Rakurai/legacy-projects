from typing import Dict, List

import legacy_common.doc_db as doc_db
import legacy_common.doxygen_graph as dg
import legacy_common.doxygen_parse as dp

def get_dependency_entities(db: dp.EntityDatabase, graph, node_id: str) -> Dict[str, dp.DoxygenEntity]:
    # get the list of predecessor nodes from the graph
    dependencies = dg.fan_in(graph, node_id)
    return {dep_id: db.get(dg.get_body_eid(db, dep_id)) for dep_id in dependencies}

def get_dependency_docs(db: dp.EntityDatabase, graph, node_id: str):
    """
    Analyze how dependencies are used in the given code.
    
    Args:
        node_id: The entity ID being documented
        
    Returns:
        Dictionary mapping dependency IDs to usage information
    """
    def dep_summary(dep: dp.DoxygenEntity) -> Dict[str, str]:
        summary = {
            "cid": dep.id.compound,
            "name": dep.name,
            "kind": dep.kind,
        }
#        print(f"{summary['id']} {summary['name']} {summary['signature']}")

        if isinstance(dep, dp.DoxygenFunction):
            summary['definition'] = dep.definition
            summary['argsstring'] = dep.argsstring

        # Add existing documentation if available
        doc = doc_db.get_doc(dep.id.compound, dep.signature)
        if doc:
            if doc.response:
                doc = doc.response

            summary['brief'] = doc.brief
            summary['details'] = doc.details
            summary['params'] = doc.params
            summary['returns'] = doc.returns

        return summary

    return {dep_id:dep_summary(dep) for dep_id, dep in get_dependency_entities(db, graph, node_id).items()}


# --- Retrieve summaries of dependencies ---
def format_dependency_summaries(db, graph, node_id, exclude_vars=True):
    dep_docs = get_dependency_docs(db, graph, node_id)

    for dep_id, doc in dep_docs.items():
        kind = doc.get('kind')

        # don't try to summarize variables in forward pass, they won't have meaningful docs until backward pass
        if exclude_vars and kind in ('variable',):
            continue

        if kind in ('function', 'friend'):
            name = doc.get('definition') + doc.get('argsstring')
        else:
            name = doc.get('name')

        brief = doc.get('brief') or doc.get('details') # could be pulling from code

        summary = f"* [{kind}] {name}"
        if brief:
            summary += f" - {brief}".rstrip('.')

        if kind in ('function', 'friend'):
            params = doc.get('params')
            if params:
                param_str = '; '.join([f'{param} - {desc}'.rstrip('.') for param, desc in params.items()])
            else:
                param_str = '; '.join(p.strip() for p in doc.get('argsstring', '()').strip('()').split(','))

            returns = (doc.get('return') or doc.get('definition').rsplit(' ', 1)[0])
            if params:
                summary += f".  Params: {param_str}"
            if returns:
                summary += f".  Returns: {returns}"

        yield summary.rstrip('.') + ('.' if brief else '')

def document_entity(entity: dp.DoxygenEntity):
    doc = doc_db.Document(
        cid = entity.id.compound,
        mid = entity.id.member,
        etype = dg.EntityType.COMPOUND if isinstance(entity, dp.DoxygenCompound) else dg.EntityType.MEMBER,
        kind = entity.kind,
        name = entity.name,
        definition = entity.definition if isinstance(entity, dp.DoxygenFunction) else None,
        argsstring = entity.argsstring if isinstance(entity, dp.DoxygenFunction) else None,
        brief = entity.doc.brief if entity.doc else None,
        details = entity.doc.details if entity.doc else None,
        params = entity.doc.params if entity.doc else None,
        returns = entity.doc.returns if entity.doc else None,
    )
    doc_db.add_doc(entity.id.compound, entity.signature, doc)
    return doc
