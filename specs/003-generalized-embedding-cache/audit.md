# Implementation Audit Report

**Feature**: 003-generalized-embedding-cache
**Audit Date**: 2026-03-20
**Branch**: 003-generalized-embedding-cache
**Base Branch**: master
**Files Audited**: 4 implementation files (embeddings_loader.py, build_mcp_db.py, config.py, test_embeddings.py)

---

## Executive Summary

Implementation audit identified **3 findings** requiring remediation: 1 CRITICAL (silent partial cache application), 1 MEDIUM (stale docstring), and 1 LOW (import location).

---

## Findings

| ID | Category | Severity | Location | Description | Quoted Evidence |
|----|----------|----------|----------|-------------|-----------------|
| SF-001 | Silent Failure | CRITICAL | `build_mcp_db.py:236-243` | Partial cache hit silently accepted; missing usage keys result in NULL embeddings with misleading "loaded from cache" log | `if usage_key in cached_embeddings: rows[idx].embedding = cached_embeddings[usage_key]` followed by unconditional `log.info("Usage embeddings loaded from cache")` |
| SD-001 | Spec Drift | MEDIUM | `embeddings_loader.py:190-193` | Docstring claims function raises RuntimeError on corruption, but implementation returns None via load_embedding_cache() | `Raises: RuntimeError: If the artifact exists but is corrupt (from legacy code path).` |
| CQ-001 | Code Quality | LOW | `embeddings_loader.py:274` | Import statement inside function body instead of module level | `from typing import cast` inside `generate_embeddings()` function |

---

## Requirement Traceability

| Requirement | Status | Implementing Code | Notes |
|-------------|--------|-------------------|-------|
| FR-001 (type parameter) | IMPLEMENTED | `embeddings_loader.py:54-90` | save_embedding_cache(), load_embedding_cache() |
| FR-002 (file naming) | IMPLEMENTED | `embeddings_loader.py:78` | `embed_cache_{model_slug}_{dimension}_{embedding_type}.pkl` |
| FR-003 (entity type="entity") | IMPLEMENTED | `embeddings_loader.py:199`, `build_mcp_db.py:279` | Calls use `embedding_type="entity"` |
| FR-004 (save operation) | IMPLEMENTED | `embeddings_loader.py:54-90` | save_embedding_cache() |
| FR-005 (load operation) | IMPLEMENTED | `embeddings_loader.py:93-142` | load_embedding_cache() |
| FR-006 (independent files) | IMPLEMENTED | Tests verify in `test_embeddings.py:217-245` | Multiple types coexist independently |
| FR-007 (artifacts dir) | IMPLEMENTED | `embeddings_loader.py:81` | `artifacts_path.mkdir(parents=True, exist_ok=True)` |
| FR-008 (corruption → None) | IMPLEMENTED | `embeddings_loader.py:138-142` | Returns None on pickle errors |
| FR-009 (log hit/miss) | IMPLEMENTED | `embeddings_loader.py:132,138` | Logs with structured key-value pairs |
| FR-010 (legacy detection) | IMPLEMENTED | `embeddings_loader.py:118-128` | Warns on legacy file for entity type |
| FR-011 (no auto-migration) | IMPLEMENTED | `embeddings_loader.py:132` | Returns None, doesn't load legacy file |

**Coverage**: 11/11 requirements implemented (100%)

---

## Constitution Compliance

| Principle | Violations | Notes |
|-----------|------------|-------|
| Fail-Fast, No Fallbacks | 1 (SF-001) | Partial cache application violates fail-fast |
| Types Are Contracts | 0 | Type annotations complete, mypy --strict passes |
| Source Reflects Current Truth | 1 (SD-001) | Stale docstring contradicts implementation |
| uv-Only Toolchain | 0 | All commands use uv |
| Notebook Discipline | N/A | No notebooks modified |

---

## Metrics

- **Total files audited**: 4
- **Total findings**: 3
  - CRITICAL: 1
  - HIGH: 0
  - MEDIUM: 1
  - LOW: 1
- **Spec coverage**: 11/11 requirements implemented (100%)
- **Constitution compliance**: 2 violations (Fail-Fast, Source Reflects Current Truth)

---

## Detailed Analysis

### SF-001: Silent Partial Cache Application (CRITICAL)

**Location**: `build_mcp_db.py:236-243`

**Problem**: When loading cached usage embeddings, the code iterates through all current usage rows and attempts to find them in the cache:

```python
if cached_embeddings is not None:
    # Apply cached embeddings to rows
    for idx, usage_key in enumerate(usage_keys):
        if usage_key in cached_embeddings:
            rows[idx].embedding = cached_embeddings[usage_key]
    log.info("Usage embeddings loaded from cache")
```

If the cache doesn't contain all required keys (e.g., new functions added since cache was created), those rows retain `embedding=None` but the build logs "Usage embeddings loaded from cache" without indicating the partial miss.

**Constitution Violation**: Violates "Fail-Fast, No Fallbacks" principle. The code silently tolerates a cache mismatch instead of invalidating and regenerating.

**Correct Behavior**:
1. Verify cache contains all required keys before applying any embeddings
2. If any key is missing, invalidate entire cache and regenerate all usage embeddings
3. Log clear distinction between full cache hit and cache miss

**Impact**: Database may contain incomplete embedding coverage with no operator visibility, degrading search quality.

---

### SD-001: Stale Docstring (MEDIUM)

**Location**: `embeddings_loader.py:190-193`

**Problem**: The `load_embeddings()` docstring states:

```python
Raises:
    RuntimeError: If the artifact exists but is corrupt (from legacy code path).
```

But the refactored implementation delegates to `load_embedding_cache()`, which returns `None` on corruption per FR-008. The function never raises `RuntimeError`.

**Constitution Violation**: Violates "Source Reflects Current Truth" - documentation contradicts implementation.

**Correct Behavior**: Update docstring to reflect actual behavior:

```python
Returns:
    Dict mapping new deterministic entity_id → embedding vector, or None
    if the file doesn't exist or is corrupt.

Raises:
    ValueError: If embedding_type contains invalid characters.
```

---

### CQ-001: Import Inside Function (LOW)

**Location**: `embeddings_loader.py:274`

**Problem**: The `typing.cast` import is placed inside the `generate_embeddings()` function body instead of at module level:

```python
def generate_embeddings(...) -> dict[str, list[float]]:
    ...
    # Save to cache using generalized cache function with type="entity"
    from typing import cast

    save_embedding_cache(...)
```

**Issue**: Import statements should be at module level for clarity and performance (imports are cached, but checking cache on every call is unnecessary overhead).

**Correct Behavior**: Move import to module-level imports section.

---

## Remediation Decisions

**User decisions (2026-03-20)**:
- **SF-001**: FIX (revised approach) - Implement incremental cache update: load cache, add missing keys, prune stale keys, re-save (COMPLETED)
- **SD-001**: FIX - Update stale docstring to reflect actual behavior (COMPLETED)
- **CQ-001**: FIX - Move import to module level (COMPLETED)

## Remediation Implementation Summary

**T027 (SD-001)**: Updated `load_embeddings()` docstring to remove stale RuntimeError claim; now correctly documents that function returns None on corruption.

**T028 (CQ-001)**: Moved `from typing import cast` to module-level imports in embeddings_loader.py.

**T029 (SF-001)**: Implemented incremental cache synchronization in `populate_entity_usages()`:
- After loading cache, computes missing keys (current - cached) and stale keys (cached - current)
- Generates embeddings only for missing keys (not all keys)
- Merges new embeddings with cached embeddings
- Prunes stale keys from cache
- Saves updated cache if any changes were made
- Logs synchronization actions: cached count, current count, added count, pruned count
- Added FR-012 to spec.md documenting this behavior

All remediation tasks completed. Linting (ruff) and type checking (mypy) pass.

---

## Post-Audit Finding: Incomplete Generalization (FR-013)

**Discovery**: During code review, identified that the implementation only partially fulfilled the spec requirement "don't create a new code path, let's generalize and reuse":
- `save_embedding_cache()` and `load_embedding_cache()` are properly generalized ✓
- Entity-specific functions (`generate_embeddings()`, `load_embeddings()`, `attach_embeddings()`, etc.) remain in `embeddings_loader.py` ✗
- Incremental sync logic duplicated in `populate_entity_usages()` instead of being a reusable function ✗
- Entity embeddings still use all-or-nothing generation without incremental sync ✗

**Impact**: Code duplication, missed optimization for entity embeddings, schema-specific coupling in persistence layer.

**Resolution**: Added FR-013 to spec.md and T030-T040 to tasks.md for completing the generalization with proper architectural layering:

**Layer 1** (`embeddings_loader.py`) - Pure cache operations, schema-agnostic:
- `load_embedding_cache()`, `save_embedding_cache()`, `sync_embeddings_cache()`
- Knows about: pickle files, keys, texts, provider interface
- Doesn't know about: entities, usages, Doxygen, MergedEntity

**Layer 2** (`entity_processor.py`) - Entity domain logic:
- `build_entity_embed_texts()`, `build_minimal_embed_text()`
- Knows about: entities, Doxygen formatting, MergedEntity structure
- Doesn't know about: caching, providers, file I/O

**Layer 3** (`build_mcp_db.py`) - Orchestration:
- Calls Layer 2 to get entity texts
- Calls Layer 1 to sync cache
- Attaches results to data structures

**Layer 4** (`server/embedding.py`) - Provider abstraction (already correct):
- Sync methods for build-time, async methods for runtime
- No changes needed

This completes the original spec intent: single reusable code path for all embedding types, with proper separation of concerns.
