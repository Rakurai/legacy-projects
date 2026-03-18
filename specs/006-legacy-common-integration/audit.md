# Implementation Audit: Legacy Common Integration

**Date**: 2026-03-18
**Branch**: `006-legacy-common-integration`
**Base**: `master`
**Files audited**: 53 (uncommitted changes; 2 deleted, 2 in legacy_common, 49 in mcp/doc_server)

---

## Findings

| ID | Category | Severity | Location | Description | Quoted Evidence |
|----|----------|----------|----------|-------------|-----------------|
| PH-001 | Phantom | HIGH | `mcp/doc_server/build_helpers/entity_processor.py:72-100` | `SignatureMap` class defined but never instantiated or referenced. Dead code. | `class SignatureMap:` ... `def __init__(self, entity_db: EntityDatabase) -> None:` — zero call sites across entire codebase |
| CV-001 | Constitution Violation | CRITICAL | `packages/legacy_common/legacy_common/doc_db.py:134-136` | `DocumentDB.load()` catches exceptions and uses `print()` instead of loguru, silently skipping malformed files. Violates fail-fast, no-print, no-silent-failure. | `except json.JSONDecodeError: print(f"Error loading {doc_path}, skipping")` / `except Exception as e: print(f"Error processing {doc_path}: {e}, skipping")` |
| CV-002 | Constitution Violation | CRITICAL | `packages/legacy_common/legacy_common/doc_db.py:113,122` | `docs_dir: Optional[Path] = None` with `self.docs_dir or GENERATED_DOCS_DIR` fallback introduced by this PR. Constitution prohibits fallback logic and legacy compatibility paths. | `source_dir = self.docs_dir or GENERATED_DOCS_DIR` |
| SF-001 | Silent Failure | HIGH | `mcp/doc_server/build_helpers/entity_processor.py:269,291` | Broad `except Exception` without re-raise during source extraction. Logs at debug level and continues — silent failure for unexpected errors. Pre-existing in changed file. | `except Exception as e: log.debug("Failed to extract definition", ...)` / `except Exception as e: log.debug("Failed to extract source", ...)` |
| SD-001 | Spec Drift | MEDIUM | `mcp/doc_server/build_helpers/entity_processor.py:83` | FR-006 specifies SignatureMap from EntityDatabase + DocumentDB. Implementation accepts only EntityDatabase. Moot since class is dead code (PH-001). | `def __init__(self, entity_db: EntityDatabase) -> None:` |
| CQ-001 | Code Quality | MEDIUM | `mcp/doc_server/server/resolver.py:40` | `arbitrary_types_allowed=True` weakens Pydantic type validation on `ResolutionResult`. Required because `candidates: list[Entity]` uses SQLModel table class. Constitution says "narrow types aggressively." | `model_config = ConfigDict(arbitrary_types_allowed=True)` |

---

## Requirement Traceability

| Requirement | Status | Implementing Code | Notes |
|-------------|--------|-------------------|-------|
| FR-001 | IMPLEMENTED | `entity_processor.py:16-17`, `loaders.py:17` | Entity models imported from `legacy_common.doxygen_parse` |
| FR-002 | IMPLEMENTED | `loaders.py:16`, `entity_processor.py:15` | Document/DocumentDB imported from `legacy_common.doc_db` |
| FR-003 | IMPLEMENTED | `loaders.py:115-121` | `DocumentDB(docs_dir=generated_docs_dir)` loads from `generated_docs/` |
| FR-004 | IMPLEMENTED | `embeddings_loader.py:87` | `doc.to_doxygen()` replaces `build_embed_text()` |
| FR-005 | IMPLEMENTED | `graph_loader.py:16` | `from legacy_common.doxygen_graph import load_graph` |
| FR-006 | DEVIATED | `entity_processor.py:72-100`, `entity_processor.py:180-185` | Goal achieved (no `signature_map.json` dependency) but via inline sig_key derivation in `merge_entities()`, not via SignatureMap class. SignatureMap class exists as dead code. |
| FR-007 | IMPLEMENTED | `loaders.py:48-70` | `doc_db.json` and `signature_map.json` removed from required list; `generated_docs/` validation added |
| FR-008 | IMPLEMENTED | (file deleted) | `artifact_models.py` deleted |
| FR-009 | IMPLEMENTED | (file deleted) | `embed_text.py` deleted; `test_embed_text.py` also deleted |
| FR-010 | IMPLEMENTED | `resolver.py:37-46` | `ResolutionResult` converted to Pydantic `BaseModel` with `ConfigDict(arbitrary_types_allowed=True)` |
| FR-011 | IMPLEMENTED | `pyproject.toml:9` | `"legacy-common"` added as dependency |
| FR-012 | IMPLEMENTED | `loaders.py:119` | Explicit path: `DocumentDB(docs_dir=generated_docs_dir)` |
| FR-013 | IMPLEMENTED | (verified absence) | No `ARTIFACTS_DIR` import from `legacy_common` in doc_server code |
| FR-014 | IMPLEMENTED | `tests/` | All test file changes are formatting-only (ruff); no behavioral modifications detected. `test_embed_text.py` deletion is consistent with spec. |

---

## Metrics

- **Files audited**: 53
- **Findings**: 2 critical, 2 high, 2 medium, 0 low
- **Spec coverage**: 13 / 14 requirements implemented (1 deviated)
- **Constitution compliance**: 2 violations found / 5 principles checked

---

## Remediation Decisions

For each item below, choose an action:
- **fix**: Create a remediation task to fix the implementation
- **spec**: Update the spec to match the implementation (if the implementation is actually correct)
- **skip**: Accept the finding and take no action
- **split**: Fix part in implementation, update part in spec (explain which)

### 1. [PH-001] SignatureMap class is dead code (HIGH)
**Location**: `mcp/doc_server/build_helpers/entity_processor.py:72-100`
**Spec says**: FR-006 requires a SignatureMap class computed from EntityDatabase and DocumentDB
**Code does**: The class exists (lines 72-100) but is never instantiated. `merge_entities()` derives sig_keys inline from entity IDs (lines 180-185), which is simpler and achieves the same goal. No code references `SignatureMap`.

Action: fix / spec / skip / split

### 2. [CV-001] Silent failure with print() in DocumentDB.load() (CRITICAL)
**Location**: `packages/legacy_common/legacy_common/doc_db.py:134-136`
**Constitution says**: "Silent failure, log-and-continue, and broad `except Exception` without immediate re-raise are prohibited." Also: "Logging: `from loguru import logger as log` — never `print`."
**Code does**: `except json.JSONDecodeError: print(f"Error loading {doc_path}, skipping")` and `except Exception as e: print(f"Error processing {doc_path}: {e}, skipping")` — catches, prints, and silently skips files.
**Spec edge case says**: "the build pipeline should log via loguru and continue"

Action: fix / spec / skip / split

### 3. [CV-002] Fallback pattern in DocumentDB constructor (CRITICAL)
**Location**: `packages/legacy_common/legacy_common/doc_db.py:113,122`
**Constitution says**: "No fallback logic — the word and practice are forbidden." and "No legacy compatibility paths or temporary bridging code."
**Code does**: `docs_dir: Optional[Path] = None` with `source_dir = self.docs_dir or GENERATED_DOCS_DIR` — introduced by this PR (task T003) to preserve backward compatibility with existing legacy_common consumers.
**Spec assumption says**: "preserve backward compatibility for existing singleton and callers"

Action: fix / spec / skip / split

### 4. [SF-001] Broad except Exception in source extraction (HIGH)
**Location**: `mcp/doc_server/build_helpers/entity_processor.py:269,291`
**Constitution says**: "Silent failure, log-and-continue, and broad `except Exception` without immediate re-raise are prohibited."
**Code does**: `except Exception as e: log.debug(...)` without re-raise in two source extraction blocks. Pre-existing code, not introduced by this PR, but in a changed file.

Action: fix / spec / skip / split

---

### MEDIUM / LOW Summary

- **[SD-001]** SignatureMap spec says EntityDatabase + DocumentDB; implementation uses only EntityDatabase. Moot since class is dead code — resolved by whichever action is taken on PH-001.
- **[CQ-001]** `arbitrary_types_allowed=True` on ResolutionResult is a pragmatic workaround for SQLModel Entity in Pydantic fields. Could be avoided by storing entity IDs and converting lazily, but this would change internal APIs.

Would you like to promote any MEDIUM findings to remediation tasks?
