"""
Artifact Loaders - Validation and parsing of pre-computed artifacts.

Reuses existing parsers from .ai/gen_docs/clustering/ to load:
- code_graph.json (entity database via doxygen_parse)
- doc_db.json (documentation database via doc_db)
- capability_defs.json (capability group definitions)
- capability_graph.json (capability dependencies)

Validates all required files exist before parsing.
"""

import json
import sys
from pathlib import Path
from typing import Any

# Add clustering module to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / ".ai" / "gen_docs" / "clustering"))

from doxygen_parse import load_db as load_entity_db, EntityDatabase, DoxygenEntity
from doc_db import DocumentDB, Document

from server.logging_config import log


class ArtifactValidationError(Exception):
    """Raised when required artifacts are missing or invalid."""
    pass


def validate_artifacts(artifacts_dir: Path) -> None:
    """
    Validate that all required artifact files exist and are parseable.

    Required files:
        - code_graph.json (entity database)
        - code_graph.gml (dependency graph)
        - doc_db.json (documentation database)
        - embeddings_cache.pkl (embeddings)
        - capability_defs.json (capability definitions)
        - capability_graph.json (capability dependencies)

    Args:
        artifacts_dir: Path to artifacts directory

    Raises:
        ArtifactValidationError: If any required file is missing or invalid
    """
    log.info("Validating artifacts", artifacts_dir=str(artifacts_dir))

    required_files = [
        "code_graph.json",
        "code_graph.gml",
        "doc_db.json",
        "embeddings_cache.pkl",
        "capability_defs.json",
        "capability_graph.json",
    ]

    missing_files = []
    for filename in required_files:
        file_path = artifacts_dir / filename
        if not file_path.exists():
            missing_files.append(filename)
        elif file_path.stat().st_size == 0:
            missing_files.append(f"{filename} (empty)")

    if missing_files:
        raise ArtifactValidationError(
            f"Missing or empty artifact files: {', '.join(missing_files)}"
        )

    log.info("All required artifacts present and valid")


def load_entities(artifacts_dir: Path) -> EntityDatabase:
    """
    Load entity database from code_graph.json.

    Uses doxygen_parse.load_db() to parse the flat JSON array.

    Args:
        artifacts_dir: Path to artifacts directory

    Returns:
        EntityDatabase with ~5300 entities

    Raises:
        FileNotFoundError: If code_graph.json doesn't exist
        json.JSONDecodeError: If code_graph.json is malformed
    """
    code_graph_path = artifacts_dir / "code_graph.json"
    log.info("Loading entity database", path=str(code_graph_path))

    entity_db = load_entity_db(code_graph_path)

    log.info("Entity database loaded", entity_count=len(entity_db.entities))
    return entity_db


def load_documents(artifacts_dir: Path) -> DocumentDB:
    """
    Load documentation database from doc_db.json.

    Uses DocumentDB.load() to parse the flat JSON with string-tuple keys.

    Args:
        artifacts_dir: Path to artifacts directory

    Returns:
        DocumentDB with ~5293 documents

    Raises:
        FileNotFoundError: If doc_db.json doesn't exist
        json.JSONDecodeError: If doc_db.json is malformed
    """
    doc_db_path = artifacts_dir / "doc_db.json"
    log.info("Loading documentation database", path=str(doc_db_path))

    doc_db = DocumentDB().load(doc_db_path)

    log.info("Documentation database loaded", document_count=doc_db.count())
    return doc_db


def load_capability_defs(artifacts_dir: Path) -> dict[str, Any]:
    """
    Load capability group definitions from capability_defs.json.

    Format:
        {
            "capability_name": {
                "type": str (domain/policy/projection/infrastructure/utility),
                "desc": str (human-readable description),
                "stability": str (stable/evolving/experimental),
                "avoid": list[str] (optional, entity names to avoid),
                "migration_role": str,
                "target_surfaces": str,
                "locked": bool
            }
        }

    Note: Description key is "desc", not "description". No "functions" key exists;
    function counts are in capability_graph.json.

    Args:
        artifacts_dir: Path to artifacts directory

    Returns:
        Dict mapping capability name to definition

    Raises:
        FileNotFoundError: If capability_defs.json doesn't exist
        json.JSONDecodeError: If capability_defs.json is malformed
    """
    cap_defs_path = artifacts_dir / "capability_defs.json"
    log.info("Loading capability definitions", path=str(cap_defs_path))

    with cap_defs_path.open("r", encoding="utf-8") as f:
        cap_defs = json.load(f)

    log.info("Capability definitions loaded", capability_count=len(cap_defs))
    return cap_defs


def load_capability_graph(artifacts_dir: Path) -> dict[str, Any]:
    """
    Load capability dependency graph from capability_graph.json.

    Format:
        {
            "metadata": { ... },
            "capabilities": {
                "cap_name": {
                    "type": str,
                    "description": str,
                    "stability": str,
                    "function_count": int,
                    "members": [
                        {"name": str, "brief": str|null, "min_depth": int}
                    ]
                }
            },
            "dependencies": {
                "source_cap": {
                    "target_cap": {
                        "edge_type": str (uses_utility/requires_core/...),
                        "call_count": int,
                        "in_dag": bool
                    }
                }
            },
            "waves": [...],
            "entry_points": { ... }
        }

    Args:
        artifacts_dir: Path to artifacts directory

    Returns:
        Dict with capabilities, dependencies, and metadata

    Raises:
        FileNotFoundError: If capability_graph.json doesn't exist
        json.JSONDecodeError: If capability_graph.json is malformed
    """
    cap_graph_path = artifacts_dir / "capability_graph.json"
    log.info("Loading capability graph", path=str(cap_graph_path))

    with cap_graph_path.open("r", encoding="utf-8") as f:
        cap_graph = json.load(f)

    log.info(
        "Capability graph loaded",
        capability_count=len(cap_graph.get("capabilities", {})),
        dependency_sources=len(cap_graph.get("dependencies", {}))
    )
    return cap_graph
