# Audit Report: MCP Build Pipeline — Data Completeness Fixes

**Feature**: 007-data-completeness  
**Audit Date**: 2026-03-18  
**Branch**: `007-data-completeness`  
**Base Branch**: `master`  
**Files Audited**: 7 (5 modified source files, 2 new test files)  
**Test Status**: 17/17 passing  

---

## Findings

| ID | Category | Severity | Location | Description | Quoted Evidence |
|----|----------|----------|----------|-------------|-----------------|
| SD-001 | Spec Drift | HIGH | `entity_processor.py:262` | Line range exceeding file length silently drops entity — now raises `BuildError` | **FIXED** — spec edge case updated: build fails on stale/corrupt line range |
| CV-001 | Constitution Violation | MEDIUM | `entity_processor.py:246,265` | Broad `except Exception` narrowed to `(OSError, UnicodeDecodeError)` | **FIXED** |
| CV-002 | Constitution Violation | MEDIUM | `entity_processor.py:13`, `test_entity_processor.py:3`, `test_embeddings.py:3` | Import sorting violations (ruff I001) | **FIXED** via `ruff check --fix` |
| CV-003 | Constitution Violation | MEDIUM | `test_embeddings.py:122,158` | Missing `Path` type annotations on `tmp_path` | **FIXED** |
| CQ-001 | Code Quality | MEDIUM | `embeddings_loader.py:20` | Comment claims "same as Document.to_doxygen()" but is a superset | **FIXED** — updated to "extends ... with structural compound tags" |
| CQ-002 | Code Quality | LOW | `embeddings_loader.py:130` | Stale docstring said "every entity that has a document" | **FIXED** — updated docstring |
| TQ-001 | Test Quality | LOW | `test_embeddings.py:30-35` | Dead `sig_override` code path in `_make_merged` helper | **FIXED** — parameter removed |

---

## Traceability Table

| Requirement | Status | Implementing Code | Notes |
|-------------|--------|-------------------|-------|
| FR-001: Build fails on zero source extraction | IMPLEMENTED | `entity_processor.py:283-287` | `BuildError` raised correctly |
| FR-002: Error message includes PROJECT_ROOT | IMPLEMENTED | `entity_processor.py:285-286` | Path included in message |
| FR-003: Populate source_text for body-located entities | IMPLEMENTED | `entity_processor.py:252-264` | Reads from `project_root / body.fn` |
| FR-004: Populate definition_text for decl-located entities | IMPLEMENTED | `entity_processor.py:238-247` | Single decl line extracted |
| FR-005: Params NULL when empty | IMPLEMENTED | `build_mcp_db.py:139`, `db_models.py:51` | Both insertion-side and ORM-side (JSONB none_as_null) |
| FR-006: Minimal embeddings for doc-less entities | IMPLEMENTED | `embeddings_loader.py:38-67` | `build_minimal_embed_text()` handles all entity kinds |
| FR-007: Structured Doxygen-like format | IMPLEMENTED | `embeddings_loader.py:58-67` | `/**` block with tag + display + file |
| FR-008: Source extraction summary log | IMPLEMENTED | `embeddings_loader.py:272-280` | body_located, extracted, failed, skipped, rate |
| FR-009: Embedding generation summary log | IMPLEMENTED | `embeddings_loader.py:163-170` | doc_embeds, minimal_embeds, no_embed, coverage |
| FR-010: Individual file failures as warnings | IMPLEMENTED | `entity_processor.py:246-247,265-270` | Warnings logged, build continues |
| Edge Case: line range exceeds file | DEVIATED | `entity_processor.py:262` | **SD-001** — silently dropped instead of capturing to EOF with warning |
| Edge Case: relative path mismatch | IMPLEMENTED | `entity_processor.py:269-270` | Logged as "Source file not found" warning |
| Edge Case: sig but no name/kind | IMPLEMENTED | `embeddings_loader.py:53-54` | Returns embedding from sig alone |
| Edge Case: embedding provider not configured | N/A | (caller responsibility) | Existing behavior unchanged |

---

## Metrics

| Metric | Value |
|--------|-------|
| Total files audited | 7 |
| CRITICAL findings | 0 |
| HIGH findings | 1 |
| MEDIUM findings | 4 |
| LOW findings | 2 |
| Spec coverage | 10/10 FRs implemented, 1/4 edge cases deviated |
| Constitution compliance | 3 violations / 5 principles checked |

---

## Remediation Decisions

For each item below, choose an action:
- **fix**: Create a remediation task to fix the implementation
- **spec**: Update the spec to match the implementation (if the implementation is actually correct)
- **skip**: Accept the finding and take no action
- **split**: Fix part in implementation, update part in spec (explain which)

### 1. [SD-001] Line range exceeding file length silently drops entity (HIGH)
**Location**: `entity_processor.py:262`  
**Spec says**: "The extraction should capture up to the end of the file and log a warning"  
**Code does**: Falls through the `if` condition without incrementing any counter or logging — entity is silently lost from all extraction metrics  

Action: fix / spec / skip / split

### 2. [CV-001] Broad `except Exception` without narrowing (MEDIUM)
**Location**: `entity_processor.py:246,265`  
**Constitution says**: "broad `except Exception` without immediate re-raise are prohibited"  
**Code does**: Catches `Exception`, logs warning, continues. FR-010 justifies not re-raising, but the catch could be narrowed to `(OSError, UnicodeDecodeError)`  

Action: fix / spec / skip / split

### 3. [CV-002] Import sorting violations — ruff I001 (MEDIUM)
**Location**: `entity_processor.py:13`, `test_entity_processor.py:3`, `test_embeddings.py:3`  
**Constitution says**: Code must pass `uv run ruff check .`  
**Code does**: Three files have unsorted import blocks  

Action: fix / skip

### 4. [CV-003] Missing type annotations on test `tmp_path` params (MEDIUM)
**Location**: `test_embeddings.py:122,158`  
**Constitution says**: "Strict typing is mandatory everywhere"  
**Code does**: `tmp_path` parameters lack `Path` type annotation  

Action: fix / skip

---

### MEDIUM/LOW Summary

The following findings are lower priority. Let me know if you want any promoted to remediation tasks:

- **CQ-001** (MEDIUM): `_KIND_TAG_MAP` comment says "same as Document.to_doxygen()" but it's a superset. Fix: update comment to "extends Document.to_doxygen() tag_map with structural compound tags".
- **CQ-002** (LOW): `generate_embeddings()` docstring is stale — still says "entity that has a document". Fix: update docstring.
- **TQ-001** (LOW): Dead `sig_override` code path in `test_embeddings.py::_make_merged`. Fix: remove the parameter and dead branch.
