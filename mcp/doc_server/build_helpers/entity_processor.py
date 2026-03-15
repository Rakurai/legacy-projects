"""
Entity Processor - Merge, enrich, and compute derived metrics.

Takes raw entity and documentation data and produces enriched entity records
ready for database insertion. Computes:
- doc_quality (high/medium/low based on doc_state and field presence)
- fan_in/fan_out (from CALLS edges in dependency graph)
- is_bridge (cross-capability callers/callees)
- side_effect_markers (categorized by type)
- is_entry_point (do_*, spell_*, spec_* pattern)
- search vectors (weighted tsvector composition)
"""

import re
from pathlib import Path
from typing import Any

from build_helpers.artifact_models import (
    DoxygenEntity,
    EntityDatabase,
    Document,
    DocumentDB,
)
from server.logging_config import log


# Side-effect function markers (categorized)
SIDE_EFFECT_FUNCTIONS = {
    "messaging": [
        "send_to_char", "send_to_room", "act", "printf_to_char", "page_to_char",
        "echo_to_char", "echo_to_room", "echo_to_all", "wiznet", "announce",
    ],
    "persistence": [
        "save_char", "save_char_obj", "save_area", "fwrite_char", "fwrite_obj",
        "sql_save", "sql_update", "sql_insert", "sql_delete", "write_player",
    ],
    "state_mutation": [
        "affect_to_char", "affect_strip", "affect_remove", "set_fighting",
        "stop_fighting", "extract_char", "char_from_room", "char_to_room",
        "obj_from_char", "obj_to_char", "obj_from_room", "obj_to_room",
    ],
    "scheduling": [
        "event_create", "add_event", "schedule", "WAIT_STATE", "delay_event",
    ],
}


class MergedEntity:
    """
    Merged entity record combining DoxygenEntity + Document + derived metrics.

    This is an intermediate representation before database insertion.
    """

    def __init__(self, entity: DoxygenEntity, doc: Document | None):
        self.entity = entity
        self.doc = doc

        # Derived fields (computed later)
        self.source_text: str | None = None
        self.definition_text: str | None = None
        self.doc_quality: str | None = None
        self.fan_in: int = 0
        self.fan_out: int = 0
        self.is_bridge: bool = False
        self.is_entry_point: bool = False
        self.side_effect_markers: dict[str, list[str]] = {}
        self._capability: str | None = None

    @property
    def entity_id(self) -> str:
        """Doxygen compound_member ID."""
        return str(self.entity.id)

    @property
    def compound_id(self) -> str:
        return self.entity.id.compound

    @property
    def member_id(self) -> str | None:
        return self.entity.id.member

    @property
    def signature(self) -> str:
        """Full signature from doc or entity name."""
        if self.doc and self.doc.definition and self.doc.argsstring:
            return f"{self.doc.definition}{self.doc.argsstring}".strip()
        return self.entity.signature

    @property
    def capability(self) -> str | None:
        """Capability group (from cap_graph assignment, fallback to doc.system)."""
        if self._capability is not None:
            return self._capability
        return self.doc.system if self.doc else None


def merge_entities(entity_db: EntityDatabase, doc_db: DocumentDB) -> list[MergedEntity]:
    """
    Merge entity database and documentation database via 1:1 join.

    Join key: (compound_id, signature)

    Args:
        entity_db: Entity database from code_graph.json
        doc_db: Documentation database from doc_db.json

    Returns:
        List of merged entity records
    """
    log.info("Merging entities and documentation")

    merged: list[MergedEntity] = []
    unmatched_entities = 0

    for entity in entity_db.entities.values():
        compound_id = entity.id.compound

        # Try to find matching doc by signature
        # Doc keys are (compound_id, signature)
        doc = None
        if compound_id in doc_db.docs:
            # Try exact signature match first
            for sig, candidate in doc_db.docs[compound_id].items():
                if sig == entity.name or sig.startswith(entity.name):
                    doc = candidate
                    break

        if doc is None:
            unmatched_entities += 1

        merged.append(MergedEntity(entity, doc))

    log.info(
        "Entities merged",
        total=len(merged),
        with_docs=len(merged) - unmatched_entities,
        without_docs=unmatched_entities
    )

    return merged


def extract_source_code(
    merged_entities: list[MergedEntity],
    project_root: Path
) -> None:
    """
    Extract source code from disk for entities with body location.

    Reads from disk using entity.body.fn, entity.body.line, entity.body.end_line.
    Updates merged_entity.source_text and merged_entity.definition_text in place.

    Args:
        merged_entities: List of merged entity records
        project_root: Repository root path
    """
    log.info("Extracting source code from disk", project_root=str(project_root))

    extracted_count = 0
    failed_count = 0

    for merged in merged_entities:
        entity = merged.entity

        # Extract definition line (first line of declaration or body)
        if entity.decl and entity.decl.fn:
            decl_file = project_root / entity.decl.fn
            if decl_file.exists():
                try:
                    with decl_file.open("r", encoding="utf-8", errors="ignore") as f:
                        lines = f.readlines()
                        if 0 < entity.decl.line <= len(lines):
                            merged.definition_text = lines[entity.decl.line - 1].strip()
                except Exception as e:
                    log.debug("Failed to extract definition", entity_id=merged.entity_id, error=str(e))

        # Extract full body source code
        if entity.body and entity.body.fn and entity.body.line and entity.body.end_line:
            body_file = project_root / entity.body.fn
            if body_file.exists():
                try:
                    with body_file.open("r", encoding="utf-8", errors="ignore") as f:
                        lines = f.readlines()
                        start_idx = entity.body.line - 1
                        end_idx = entity.body.end_line

                        if 0 <= start_idx < len(lines) and start_idx < end_idx <= len(lines):
                            merged.source_text = "".join(lines[start_idx:end_idx])
                            extracted_count += 1
                except Exception as e:
                    log.debug("Failed to extract source", entity_id=merged.entity_id, error=str(e))
                    failed_count += 1

    log.info(
        "Source code extracted",
        extracted=extracted_count,
        failed=failed_count
    )


def compute_doc_quality(merged_entities: list[MergedEntity]) -> None:
    """
    Compute doc_quality (high/medium/low) based on doc_state and field presence.

    Rules:
        - high: doc_state IN (refined_summary, refined_usage) AND details IS NOT NULL
                AND (params IS NOT NULL OR kind != 'function')
        - medium: doc_state = generated_summary OR (brief IS NOT NULL AND details IS NULL)
        - low: doc_state = extracted_summary OR brief IS NULL

    Updates merged_entity.doc_quality in place.

    Args:
        merged_entities: List of merged entity records
    """
    log.info("Computing documentation quality")

    for merged in merged_entities:
        doc = merged.doc
        if not doc:
            merged.doc_quality = "low"
            continue

        doc_state = doc.state or "extracted_summary"

        # High quality
        if doc_state in ("refined_summary", "refined_usage") and doc.details:
            if merged.entity.kind != "function" or doc.params:
                merged.doc_quality = "high"
                continue

        # Medium quality
        if doc_state == "generated_summary" or (doc.brief and not doc.details):
            merged.doc_quality = "medium"
            continue

        # Low quality (default)
        merged.doc_quality = "low"


def compute_is_entry_point(merged_entities: list[MergedEntity]) -> None:
    """
    Compute is_entry_point flag for functions matching entry point patterns.

    Patterns:
        - do_* (commands)
        - spell_* (spells)
        - spec_* (special procedures)

    Updates merged_entity.is_entry_point in place.

    Args:
        merged_entities: List of merged entity records
    """
    log.info("Computing entry point flags")

    entry_point_count = 0

    for merged in merged_entities:
        if merged.entity.kind == "function":
            name = merged.entity.name
            if name.startswith("do_") or name.startswith("spell_") or name.startswith("spec_"):
                merged.is_entry_point = True
                entry_point_count += 1

    log.info("Entry point flags computed", entry_point_count=entry_point_count)


def assign_capabilities(
    merged_entities: list[MergedEntity],
    cap_graph: dict
) -> None:
    """
    Assign capability groups to entities from capability_graph.json members.

    Builds a name→capability dict from cap_graph["capabilities"][name]["members"]
    and assigns to each entity's _capability field.

    Args:
        merged_entities: List of merged entity records
        cap_graph: Loaded capability_graph.json data
    """
    log.info("Assigning capabilities from capability graph")

    name_to_cap: dict[str, str] = {}
    capabilities = cap_graph.get("capabilities", {})
    for cap_name, cap_data in capabilities.items():
        for member in cap_data.get("members", []):
            member_name = member.get("name") if isinstance(member, dict) else member
            if member_name:
                name_to_cap[member_name] = cap_name

    assigned = 0
    for merged in merged_entities:
        cap = name_to_cap.get(merged.entity.name)
        if cap:
            merged._capability = cap
            assigned += 1

    log.info("Capabilities assigned", assigned=assigned, total=len(merged_entities))


# Note: fan_in, fan_out, is_bridge, and side_effect_markers
# are computed from the dependency graph in graph_loader.py
# after edges are loaded. These functions will be called from
# the main build pipeline after graph construction.
