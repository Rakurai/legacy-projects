# Data Model: MCP Build Pipeline — Data Completeness Fixes

**Feature**: 007-data-completeness
**Phase**: 1 (Design & Contracts)
**Date**: 2026-03-18

## Overview

This spec modifies no database schema — all columns (`source_text`, `definition_text`, `params`, `embedding`) already exist in the `entities` table. The changes are purely in the **build pipeline** that populates these columns. This document describes the data flow changes.

---

## 1. Affected Entity Fields

### 1.1 `source_text` (existing column, currently unpopulated)

| Property | Value |
|----------|-------|
| **DB column** | `entities.source_text TEXT` |
| **ORM field** | `Entity.source_text: str \| None` |
| **Pipeline field** | `MergedEntity.source_text: str \| None` |
| **Populated by** | `extract_source_code()` in `entity_processor.py` |
| **Source** | C++ source file at `PROJECT_ROOT / entity.body.fn`, lines `body.line` to `body.end_line` |
| **Current state** | 0 / 5,305 populated (silent extraction failure) |
| **Target state** | ≥90% of entities with body locations |

### 1.2 `definition_text` (existing column, currently unpopulated)

| Property | Value |
|----------|-------|
| **DB column** | `entities.definition_text TEXT` |
| **ORM field** | `Entity.definition_text: str \| None` |
| **Pipeline field** | `MergedEntity.definition_text: str \| None` |
| **Populated by** | `extract_source_code()` in `entity_processor.py` |
| **Source** | C++ source file at `PROJECT_ROOT / entity.decl.fn`, line `decl.line` |
| **Current state** | 0 / 5,305 populated |
| **Target state** | ≥90% of entities with decl locations |

### 1.3 `params` (existing column, currently over-populated with `{}`)

| Property | Value |
|----------|-------|
| **DB column** | `entities.params JSONB` |
| **ORM field** | `Entity.params: dict \| None` (sa_column JSONB) |
| **Pipeline field** | `MergedEntity.doc.params: dict[str, str] \| None` |
| **Populated by** | `populate_entities()` in `build_mcp_db.py` |
| **Current state** | 5,055 non-null (but ~3,256 are `{}`) |
| **Target state** | ~1,800–2,100 non-null (only meaningful content) |
| **Normalization rule** | `None` or `{}` → `NULL`; non-empty dict → stored as-is |

### 1.4 `embedding` (existing column, partially populated)

| Property | Value |
|----------|-------|
| **DB column** | `entities.embedding vector(768)` |
| **ORM field** | `Entity.embedding: list[float] \| None` (sa_column Vector) |
| **Pipeline field** | `MergedEntity.embedding: list[float] \| None` |
| **Populated by** | `generate_embeddings()` + `attach_embeddings()` in `embeddings_loader.py` |
| **Current state** | 4,516 / 5,305 populated (doc-gated) |
| **Target state** | ≥95% of all entities |

---

## 2. New Build Pipeline Behaviors

### 2.1 Source Extraction Validation

**Location**: `extract_source_code()` in `entity_processor.py`

**State transition**:
```
Before: entities with body locations → silent skip → source_text = None
After:  entities with body locations → extract or warn → source_text = text | None
        zero successes + any body-located entities → BuildError raised
```

**New exception**: `BuildError` (or similar) raised when `extracted_count == 0 and body_located_count > 0`.

### 2.2 Minimal Embedding Generation

**Location**: `generate_embeddings()` in `embeddings_loader.py`

**New function**: `build_minimal_embed_text(entity: MergedEntity) -> str | None`

Produces a Doxygen-formatted minimal text:
```
/**
 * @{tag} {signature_or_name}
 *
 * @file {file_path}
 */
```

**Tag mapping** (same as `Document.to_doxygen()`):

| Kind | Tag |
|------|-----|
| function | `@fn` |
| variable | `@var` |
| class | `@class` |
| struct | `@struct` |
| file | `@file` |
| dir | `@dir` |
| namespace | `@namespace` |
| define | `@def` |
| group | `@defgroup` |
| enum | `@enum` |
| typedef | `@typedef` |
| union | `@union` |

**Skip rule**: Returns `None` when all of `name`, `signature`, `kind` are empty/null.

### 2.3 Params Normalization

**Location**: `populate_entities()` in `build_mcp_db.py`

**Change**: Single line at entity construction:
```python
# Before:
params=merged.doc.params if merged.doc else None,
# After:
params=merged.doc.params if merged.doc and merged.doc.params else None,
```

---

## 3. No Schema Changes

This spec does not alter:
- Table definitions (no new columns, no type changes)
- Indexes
- SQLModel class definitions
- Entity ID generation
- Edge tables
- Capability tables

All changes are build-pipeline-only.
