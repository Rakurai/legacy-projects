"""
Entity Processor - Merge, enrich, and compute derived metrics.

Takes raw entity and documentation data and produces enriched entity records
ready for database insertion. Computes:
- fan_in/fan_out (from CALLS edges in dependency graph)
- is_bridge (cross-capability callers/callees)
- is_entry_point (do_*, spell_*, spec_* pattern)
- search vectors (weighted tsvector composition)
"""

import re
from collections import defaultdict
from collections.abc import ItemsView
from pathlib import Path

from legacy_common.doc_db import Document, DocumentDB
from legacy_common.doxygen_graph import load_graph
from legacy_common.doxygen_parse import DoxygenEntity, EntityDatabase
from legacy_common.entity_ids import compute_entity_id
from server.logging_config import log


class BuildError(Exception):
    """Raised when the build pipeline detects an unrecoverable data problem."""


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


_CONTRACT_SEED_FAN_IN_THRESHOLD = 10
"""Minimum fan_in for an entity to qualify as a contract seed (configurable)."""

# Domain-specific terms from the Legacy MUD codebase vocabulary.
# Used for rationale_specificity heuristic (domain-term density component).
_DOMAIN_TERMS: frozenset[str] = frozenset(
    {
        "damage",
        "spell",
        "magic",
        "combat",
        "character",
        "player",
        "mobile",
        "mob",
        "room",
        "area",
        "effect",
        "affect",
        "buff",
        "debuff",
        "weapon",
        "skill",
        "level",
        "experience",
        "hit",
        "attack",
        "defense",
        "poison",
        "heal",
        "cure",
        "cast",
        "ability",
        "stat",
        "attribute",
        "condition",
        "mortal",
        "immortal",
        "deity",
        "mana",
        "hitpoint",
        "movement",
        "fight",
        "flee",
        "death",
        "respawn",
        "save",
        "resist",
        "immunity",
        "vulnerability",
        "flag",
        "bitvector",
        "tick",
        "pulse",
        "act",
        "command",
        "do_",
        "spell_",
        "spec_",
        "clan",
        "guild",
        "race",
        "class",
        "alignment",
        "karma",
        "reputation",
        "quest",
        "auction",
        "shop",
        "object",
        "item",
        "container",
        "wear",
        "wield",
        "inventory",
        "equipment",
    }
)


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
        self.doc_embedding: list[float] | None = None
        self.symbol_embedding: list[float] | None = None
        self.qualified_name: str | None = None
        self.symbol_searchable: str | None = None
        self._capability: str | None = None

        # KG enrichment fields (FR-001 through FR-004)
        self.doc_state: str | None = None
        self.notes_length: int | None = None
        self.is_contract_seed: bool = False
        self.rationale_specificity: float | None = None

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
    graph_node_ids: frozenset[str],
) -> list[MergedEntity]:
    """
    Merge entity database and documentation database, deduplicating split pairs.

    Groups entities by entity.id.member (Doxygen's authoritative member hash).
    Entities where id.member is None are pure compounds and pass through as
    single-entity groups. For multi-entity groups (declaration/definition splits),
    selects the definition fragment (entity.body is not None) as the survivor.

    Args:
        entity_db: Entity database from code_graph.json (legacy_common)
        doc_db: Documentation database from generated_docs/ (legacy_common)
        graph_node_ids: Node IDs present in code_graph.gml (from load_graph_node_ids)

    Returns:
        List of merged entity records with at most one record per logical entity

    Raises:
        BuildError: If a split entity has no definition fragment in the graph
    """
    log.info("Merging entities and documentation")

    # Group entities by logical identity: member hash (or compound ID for non-members)
    groups: dict[str, list[tuple[DoxygenEntity, Document | None]]] = defaultdict(list)

    for entity in entity_db.entities.values():
        dedup_key = str(entity.id.member) if entity.id.member else f"_compound_{entity.id.compound}"
        compound_id = entity.id.compound
        doc = doc_db.get_doc(compound_id, entity.signature)
        groups[dedup_key].append((entity, doc))

    merged: list[MergedEntity] = []
    unmatched_entities = 0
    merged_pair_count = 0

    for _dedup_key, fragments in groups.items():
        if len(fragments) == 1:
            entity, doc = fragments[0]
            compound_id = entity.id.compound
            second_element = entity.id.member if entity.id.member else compound_id
            if doc is None:
                unmatched_entities += 1
            merged.append(MergedEntity(entity, doc, (compound_id, second_element)))
        else:
            # Declaration/definition split — find graph-referenced fragments
            in_graph = [
                (e, d)
                for e, d in fragments
                if (str(e.id.member) if e.id.member else str(e.id.compound)) in graph_node_ids
            ]

            if not in_graph:
                first_entity = fragments[0][0]
                raise BuildError(
                    f"Split entity '{first_entity.name}' has no graph-referenced compound — "
                    f"neither compound appears in code_graph.gml"
                )

            # Find the definition fragment (entity.body is not None)
            body_candidates = [(e, d) for e, d in in_graph if e.body is not None]

            if not body_candidates:
                first_entity = fragments[0][0]
                raise BuildError(
                    f"Split entity '{first_entity.name}' has no definition fragment with body — "
                    f"all fragments are declaration-only"
                )

            survivor_entity, survivor_doc = body_candidates[0]

            # Copy doc from sibling if survivor has none
            if survivor_doc is None:
                for e, d in fragments:
                    if e is not survivor_entity and d is not None:
                        survivor_doc = d
                        break

            compound_id = survivor_entity.id.compound
            second_element = survivor_entity.id.member if survivor_entity.id.member else compound_id

            if survivor_doc is None:
                unmatched_entities += 1

            merged_pair_count += 1
            merged.append(MergedEntity(survivor_entity, survivor_doc, (compound_id, second_element)))

    log.info(
        "Entities merged",
        total=len(merged),
        with_docs=len(merged) - unmatched_entities,
        without_docs=unmatched_entities,
        split_pairs_unified=merged_pair_count,
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
                f"Hash collision: {new_id!r} produced by both {seen_new_ids[new_id]!r} and {merged.old_entity_id!r}"
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


def extract_source_code(merged_entities: list[MergedEntity], project_root: Path) -> None:
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
                    log.warning(
                        "Failed to extract definition", entity_id=merged.entity_id, path=str(decl_file), error=str(e)
                    )
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
                    log.warning(
                        "Failed to extract source", entity_id=merged.entity_id, path=str(body_file), error=str(e)
                    )
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


def assign_capabilities(merged_entities: list[MergedEntity], cap_graph: dict) -> None:
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


def compute_enriched_fields(merged_entities: list[MergedEntity]) -> None:
    """
    Compute KG-enrichment derived fields for all merged entities (FR-001 through FR-004, FR-013).

    Computes:
    - doc_state: carried from doc.state (the documentation generation tier)
    - notes_length: character count of the notes field
    - is_contract_seed: fan_in > threshold AND rationale is non-null
    - rationale_specificity: heuristic score based on length x domain-term density

    Must be called AFTER fan_in values are assigned (i.e., after graph metrics are computed).

    Raises:
        BuildError: If a documented entity is missing the required `state` field (FR-013).
    """
    log.info("Computing KG enrichment fields")

    seeds = 0
    with_doc_state = 0

    for merged in merged_entities:
        doc = merged.doc
        if doc is None:
            continue

        # FR-001: Carry doc_state from doc.state. Required field — fail fast if missing.
        if doc.state is None:
            raise BuildError(
                f"Entity {merged.old_entity_id!r} (sig: {merged.entity.signature!r}) "
                f"has a generated_docs entry but missing required 'state' field. "
                f"Check the generated_docs artifact for this entity."
            )
        merged.doc_state = doc.state
        with_doc_state += 1

        # FR-002: notes_length from character count of notes field
        notes = getattr(doc, "notes", None)
        if notes:
            merged.notes_length = len(notes)

        # FR-003: is_contract_seed — high fan_in AND rationale present
        rationale = getattr(doc, "rationale", None)
        if merged.fan_in > _CONTRACT_SEED_FAN_IN_THRESHOLD and rationale:
            merged.is_contract_seed = True
            seeds += 1

        # FR-004: rationale_specificity heuristic (length x domain-term density)
        if rationale:
            words = rationale.lower().split()
            if words:
                word_set = set(words)
                domain_hits = len(word_set & _DOMAIN_TERMS)
                density = domain_hits / len(word_set)
                # Normalize length: cap at 500 chars for a score of 1.0
                length_score = min(len(rationale) / 500.0, 1.0)
                merged.rationale_specificity = round(length_score * (0.5 + 0.5 * density), 4)

    log.info(
        "KG enrichment fields computed",
        with_doc_state=with_doc_state,
        contract_seeds=seeds,
    )


# Note: fan_in, fan_out, and is_bridge are computed from the
# dependency graph in graph_loader.py after edges are loaded.
# These functions will be called from the main build pipeline
# after graph construction.


# Doxygen tag mapping for embedding text generation
_KIND_TAG_MAP: dict[str, str] = {
    "function": "@fn",
    "variable": "@var",
    "class": "@class",
    "struct": "@struct",
    "file": "@file",
    "dir": "@dir",
    "namespace": "@namespace",
    "define": "@def",
    "group": "@defgroup",
    "enum": "@enum",
    "typedef": "@typedef",
    "union": "@union",
}


def build_minimal_embed_text(merged: MergedEntity) -> str | None:
    """Build a minimal Doxygen-formatted embedding text for a doc-less entity.

    Returns None when name, signature, and kind are all empty — nothing
    meaningful to embed.
    """
    kind = merged.entity.kind or ""
    name = merged.entity.name or ""
    sig = merged.signature or ""
    file_path = merged.entity.body.fn if merged.entity.body else merged.entity.decl.fn if merged.entity.decl else None

    if not kind and not name and not sig:
        return None

    tag = _KIND_TAG_MAP.get(kind, "@fn")
    display = sig if sig else name

    lines = ["/**"]
    lines.append(f" * {tag} {display}")

    if file_path:
        lines.append(" *")
        lines.append(f" * @file {file_path}")

    lines.append(" */")
    return "\n".join(lines)


def derive_qualified_names(merged_entities: list[MergedEntity], artifacts_path: Path) -> None:
    """Derive qualified_name for each entity by walking contained_by edges in the GML graph.

    Strategy:
    1. Walk contained_by edges from child → parent to build scope chain
    2. Fall back to parsing definition_text for :: separators
    3. Fall back to bare name
    """
    log.info("Deriving qualified names from containment graph")

    gml_path = artifacts_path / "code_graph.gml"
    g = load_graph(gml_path)

    # Build node_id → entity mapping and contained_by adjacency
    # GML nodes use bare member hash or compound ID
    entity_by_node: dict[str, MergedEntity] = {}
    for merged in merged_entities:
        member = merged.entity.id.member
        if member:
            entity_by_node[member] = merged
        else:
            entity_by_node[merged.entity.id.compound] = merged

    # Build child → parent map from contained_by edges
    child_to_parent: dict[str, str] = {}
    for source, target, data in g.edges(data=True):
        if data.get("type", "").lower() == "contained_by":
            child_to_parent[source] = target

    # Node → name map for scope chain assembly
    node_name: dict[str, str] = {}
    for merged in merged_entities:
        member = merged.entity.id.member
        node_id = member if member else merged.entity.id.compound
        node_name[node_id] = merged.entity.name

    derived_count = 0
    fallback_count = 0

    for merged in merged_entities:
        member = merged.entity.id.member
        node_id = member if member else merged.entity.id.compound

        # Walk contained_by chain to build scope
        max_scope_depth = 10
        scope_parts: list[str] = []
        current = child_to_parent.get(node_id)
        while current and len(scope_parts) < max_scope_depth:
            parent_name = node_name.get(current, "")
            if parent_name and parent_name not in ("", "/"):
                scope_parts.append(parent_name)
            current = child_to_parent.get(current)

        if scope_parts:
            scope_parts.reverse()
            merged.qualified_name = "::".join(scope_parts) + "::" + merged.entity.name
            derived_count += 1
        elif merged.definition_text and "::" in merged.definition_text:
            # Fallback: parse definition_text for :: separator
            match = re.search(r"([\w:]+)::" + re.escape(merged.entity.name), merged.definition_text)
            if match:
                merged.qualified_name = match.group(0)
                fallback_count += 1
            else:
                merged.qualified_name = merged.entity.name
        else:
            merged.qualified_name = merged.entity.name

    log.info(
        "Qualified names derived",
        graph_derived=derived_count,
        definition_fallback=fallback_count,
        bare_name=len(merged_entities) - derived_count - fallback_count,
    )


def build_symbol_searchable(merged_entities: list[MergedEntity]) -> None:
    """Build lowercased, punctuation-stripped symbol_searchable text for pg_trgm."""
    log.info("Building symbol_searchable column values")

    for merged in merged_entities:
        parts = [merged.entity.name]
        if merged.qualified_name:
            parts.append(merged.qualified_name)
        parts.append(merged.signature)
        raw = " ".join(p for p in parts if p)
        # Lowercase and strip non-alphanumeric (keep spaces for trigram matching)
        merged.symbol_searchable = re.sub(r"[^a-z0-9_ ]", "", raw.lower())

    log.info("symbol_searchable built", count=len(merged_entities))


def build_doc_embed_texts(merged_entities: list[MergedEntity]) -> dict[str, str]:
    """Build labeled prose field text for doc embedding.

    Assembles BRIEF/DETAILS/PARAMS/RETURNS/NOTES/RATIONALE labels.
    Falls back to bare name for entities with no prose fields.
    """
    texts: dict[str, str] = {}
    for merged in merged_entities:
        parts: list[str] = []
        if merged.doc:
            if merged.doc.brief:
                parts.append(f"BRIEF: {merged.doc.brief}")
            if merged.doc.details:
                parts.append(f"DETAILS: {merged.doc.details}")
            if merged.doc.params:
                params_text = " ".join(f"{k}: {v}" for k, v in merged.doc.params.items())
                parts.append(f"PARAMS: {params_text}")
            if merged.doc.returns:
                parts.append(f"RETURNS: {merged.doc.returns}")
            if merged.doc.notes:
                parts.append(f"NOTES: {merged.doc.notes}")
            if merged.doc.rationale:
                parts.append(f"RATIONALE: {merged.doc.rationale}")
        texts[merged.entity_id] = "\n".join(parts) if parts else merged.entity.name
    return texts


def build_symbol_embed_texts(merged_entities: list[MergedEntity]) -> dict[str, str]:
    """Build qualified signature text for symbol embedding.

    Functions: qualified signature in natural C++ form.
    Non-functions: qualified name only.
    """
    texts: dict[str, str] = {}
    for merged in merged_entities:
        if merged.entity.kind == "function":
            # Use qualified_name in signature if available
            if merged.qualified_name and "::" in merged.qualified_name:
                # Replace bare name in signature with qualified name
                sig = merged.signature
                name = merged.entity.name
                if name and name in sig:
                    texts[merged.entity_id] = sig.replace(name, merged.qualified_name, 1)
                else:
                    texts[merged.entity_id] = sig
            else:
                texts[merged.entity_id] = merged.signature
        else:
            texts[merged.entity_id] = merged.qualified_name or merged.entity.name
    return texts
