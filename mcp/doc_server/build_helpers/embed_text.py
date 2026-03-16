"""
Embed Text Builder - Reconstruct Doxygen-formatted docstring for embedding.

Replicates the text format from the original gen_docs Document.to_doxygen() method.
Takes a raw doc_db.json dict entry and always produces text (never None),
matching the original regen_embeddings.py pipeline which embeds ALL docs.
"""

from __future__ import annotations

from typing import Any

# Tag mapping: entity kind → Doxygen tag
_KIND_TAG_MAP: dict[str, str] = {
    "function": "@fn",
    "variable": "@var",
    "enum": "@enum",
    "class": "@class",
    "struct": "@struct",
    "namespace": "@namespace",
    "define": "@def",
    "group": "@defgroup",
}


def build_embed_text(doc: dict[str, Any]) -> str:
    """Build Doxygen-formatted docstring from a raw doc_db.json entry.

    This matches the original Document.to_doxygen() method exactly.
    Every doc entry produces text — this function never returns None.

    Args:
        doc: A dict from doc_db.json with keys like kind, name, definition,
             argsstring, brief, details, params, returns, notes, rationale.

    Returns:
        Formatted Doxygen docstring.
    """
    kind = doc.get("kind", "")
    name = doc.get("name", "")
    definition = doc.get("definition", "")
    argsstring = doc.get("argsstring", "")

    lines: list[str] = ["/**"]

    tag = _KIND_TAG_MAP.get(kind, "@fn")
    if kind == "function" and definition and argsstring is not None:
        lines.append(f" * {tag} {definition}{argsstring}")
    else:
        lines.append(f" * {tag} {name}")

    brief = doc.get("brief")
    details = doc.get("details")
    notes = doc.get("notes")
    rationale = doc.get("rationale")
    tparams = doc.get("tparams")
    params = doc.get("params")
    returns = doc.get("returns") or doc.get("return")
    throws = doc.get("throws")

    if brief:
        lines.append(" *")
        lines.append(f" * @brief {brief}")
    if details:
        lines.append(" *")
        lines.append(f" * @details {details}")
    if notes:
        lines.append(" *")
        lines.append(f" * @note {notes}")
    if rationale:
        lines.append(" *")
        lines.append(f" * @rationale {rationale}")

    lines.append(" *")

    if tparams:
        for tname, desc in tparams.items():
            lines.append(f" * @tparam {tname} {desc}")
    if params:
        for pname, desc in params.items():
            lines.append(f" * @param {pname} {desc}")
    if returns:
        lines.append(f" * @return {returns}")
    if throws:
        lines.append(f" * @throws {throws}")

    lines.append(" */")
    return "\n".join(lines)
