"""
Entity Processor - Merge, enrich, and compute derived metrics.

Takes raw entity and documentation data and produces enriched entity records
ready for database insertion. Computes:
- fan_in/fan_out (from CALLS edges in dependency graph)
- is_bridge (cross-capability callers/callees)
- side_effect_markers (categorized by type)
- is_entry_point (do_*, spell_*, spec_* pattern)
- search vectors (weighted tsvector composition)
"""

from collections.abc import ItemsView
from pathlib import Path

from build_helpers.entity_ids import compute_entity_id
from legacy_common.doc_db import Document, DocumentDB
from legacy_common.doxygen_parse import DoxygenEntity, EntityDatabase
from server.logging_config import log


class BuildError(Exception):
    """Raised when the build pipeline detects an unrecoverable data problem."""


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


class SignatureMap:
    """
    Mapping from repr((compound_id, second_element)) → old Doxygen entity ID.

    Computed on-the-fly from EntityDatabase. Replaces the pre-computed
    signature_map.json artifact. Every entity in the database gets an entry:
    - Members: second_element = member hash
    - Compounds: second_element = compound ID
    """

    def __init__(self, entity_db: EntityDatabase) -> None:
        self._map: dict[str, str] = {}
        for entity in entity_db.entities.values():
            compound_id = entity.id.compound
            second_element = entity.id.member if entity.id.member else compound_id
            old_entity_id = str(entity.id)
            self._map[repr((compound_id, second_element))] = old_entity_id

        log.info("SignatureMap built", entries=len(self._map))

    def __getitem__(self, key: str) -> str:
        return self._map[key]

    def get(self, key: str, default: str | None = None) -> str | None:
        return self._map.get(key, default)

    def items(self) -> ItemsView[str, str]:
        return self._map.items()

    def __len__(self) -> int:
        return len(self._map)


class MergedEntity:
    """
    Merged entity record combining DoxygenEntity + Document + derived metrics.

    This is an intermediate representation before database insertion.
    """

    def __init__(self, entity: DoxygenEntity, doc: Document | None, sig_key: tuple[str, str]):
        self.entity = entity
        self.doc = doc
        self._sig_key = sig_key  # (compound_id, second_element) from signature_map

        self._deterministic_id: str | None = None

        # Derived fields (computed later)
        self.source_text: str | None = None
        self.definition_text: str | None = None
        self.fan_in: int = 0
        self.fan_out: int = 0
        self.is_bridge: bool = False
        self.is_entry_point: bool = False
        self.side_effect_markers: dict[str, list[str]] = {}
        self.embedding: list[float] | None = None
        self._capability: str | None = None

    @property
    def old_entity_id(self) -> str:
        """Original Doxygen entity ID for cross-referencing during build."""
        return str(self.entity.id)

    @property
    def entity_id(self) -> str:
        """Deterministic entity ID. Must be assigned before use."""
        assert self._deterministic_id is not None, "Deterministic ID not yet assigned"
        return self._deterministic_id

    @property
    def signature(self) -> str:
        """Full signature from doc or entity name."""
        if self.doc and self.doc.definition and self.doc.argsstring:
            return f"{self.doc.definition}{self.doc.argsstring}".strip()
        return self.entity.signature

    @property
    def capability(self) -> str | None:
        """Capability group (from cap_graph assignment)."""
        return self._capability


def merge_entities(
    entity_db: EntityDatabase,
    doc_db: DocumentDB,
) -> list[MergedEntity]:
    """
    Merge entity database and documentation database.

    For each entity, derives (compound_id, second_element) from its EntityID
    and looks up the corresponding Document in DocumentDB. No signature_map.json
    required — the mapping is computed on-the-fly from entity IDs.

    Args:
        entity_db: Entity database from code_graph.json (legacy_common)
        doc_db: Documentation database from generated_docs/ (legacy_common)

    Returns:
        List of merged entity records
    """
    log.info("Merging entities and documentation")

    merged: list[MergedEntity] = []
    unmatched_entities = 0

    for entity in entity_db.entities.values():
        compound_id = entity.id.compound
        second_element = entity.id.member if entity.id.member else compound_id
        sig_key = (compound_id, second_element)

        doc = doc_db.get_doc(compound_id, entity.signature)

        if doc is None:
            unmatched_entities += 1

        merged.append(MergedEntity(entity, doc, sig_key))

    log.info(
        "Entities merged",
        total=len(merged),
        with_docs=len(merged) - unmatched_entities,
        without_docs=unmatched_entities
    )

    return merged


def assign_deterministic_ids(merged_entities: list[MergedEntity]) -> dict[str, str]:
    """
    Compute and assign deterministic IDs to all merged entities.

    Returns:
        Dict mapping old Doxygen entity_id → new deterministic entity_id.

    Raises:
        RuntimeError: On any hash collision.
    """
    log.info("Assigning deterministic entity IDs")

    old_to_new: dict[str, str] = {}
    seen_new_ids: dict[str, str] = {}  # new_id → old_entity_id for collision reporting

    for merged in merged_entities:
        kind = merged.entity.kind
        compound_id, second_element = merged._sig_key
        new_id = compute_entity_id(kind, compound_id, second_element)

        if new_id in seen_new_ids:
            raise RuntimeError(
                f"Hash collision: {new_id!r} produced by both "
                f"{seen_new_ids[new_id]!r} and {merged.old_entity_id!r}"
            )

        seen_new_ids[new_id] = merged.old_entity_id
        merged._deterministic_id = new_id
        old_to_new[merged.old_entity_id] = new_id

    log.info(
        "Deterministic IDs assigned",
        total=len(old_to_new),
        collision_check="passed",
    )
    return old_to_new


def extract_source_code(
    merged_entities: list[MergedEntity],
    project_root: Path
) -> None:
    """
    Extract source code from disk for entities with body location.

    Reads from disk using entity.body.fn, entity.body.line, entity.body.end_line.
    Updates merged_entity.source_text and merged_entity.definition_text in place.

    Raises:
        BuildError: When body-located entities exist but none could be extracted
            (indicates PROJECT_ROOT is misconfigured).
    """
    log.info("Extracting source code from disk", project_root=str(project_root))

    extracted_count = 0
    failed_count = 0
    skipped_count = 0
    body_located = 0

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
                except (OSError, UnicodeDecodeError) as e:
                    log.warning("Failed to extract definition", entity_id=merged.entity_id, path=str(decl_file), error=str(e))
            else:
                log.warning("Declaration file not found", entity_id=merged.entity_id, path=str(decl_file))

        # Extract full body source code
        if entity.body and entity.body.fn and entity.body.line and entity.body.end_line:
            body_located += 1
            body_file = project_root / entity.body.fn
            if body_file.exists():
                try:
                    with body_file.open("r", encoding="utf-8", errors="ignore") as f:
                        lines = f.readlines()
                        start_idx = entity.body.line - 1
                        end_idx = entity.body.end_line

                        if not (0 <= start_idx < len(lines) and start_idx < end_idx <= len(lines)):
                            raise BuildError(
                                f"Line range {entity.body.line}-{entity.body.end_line} invalid for "
                                f"{body_file} ({len(lines)} lines) — code graph is stale or corrupt"
                            )
                        merged.source_text = "".join(lines[start_idx:end_idx])
                        extracted_count += 1
                except (OSError, UnicodeDecodeError) as e:
                    log.warning("Failed to extract source", entity_id=merged.entity_id, path=str(body_file), error=str(e))
                    failed_count += 1
            else:
                log.warning("Source file not found", entity_id=merged.entity_id, path=str(body_file))
                skipped_count += 1

    success_rate = round(100.0 * extracted_count / body_located, 1) if body_located > 0 else 0.0
    log.info(
        "Source code extraction summary",
        body_located=body_located,
        extracted=extracted_count,
        failed=failed_count,
        skipped=skipped_count,
        success_rate=f"{success_rate}%",
    )

    if body_located > 0 and extracted_count == 0:
        raise BuildError(
            f"Zero source files extracted from {body_located} body-located entities. "
            f"PROJECT_ROOT may be misconfigured: {project_root}"
        )


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

    # TODO: capability_graph.json members use bare names ("act_bug") and scoped
    #   names ("Logging::bug"), neither of which is an entity_id.  Name-based
    #   matching is lossy when names collide (e.g., 38 entities named "name").
    #   Fix requires adding entity_ids to capability_graph.json members in the
    #   gen_docs pipeline.
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
