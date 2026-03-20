# Data Model: Generalized Embedding Cache

**Branch**: `003-generalized-embedding-cache` | **Date**: 2026-03-20

---

## Overview

This document defines the cache file structure, type identifier semantics, and cache key composition for the generalized embedding cache mechanism. No database schema changes—all changes are to filesystem artifacts.

---

## Cache File Structure

### File Naming Convention

```
embed_cache_{model_slug}_{dimension}_{type}.pkl
```

**Components**:
- `model_slug`: Embedding model identifier (e.g., "bge-base-en-v1-5")
- `dimension`: Vector dimension (e.g., "768")
- `type`: Embedding package type (e.g., "entity", "usages", "subsystem")

**Examples**:
- `embed_cache_bge-base-en-v1-5_768_entity.pkl`
- `embed_cache_bge-base-en-v1-5_768_usages.pkl`
- `embed_cache_text-embedding-3-small_1536_subsystem.pkl`

### File Location

All cache files stored in the artifacts directory:
- Default: `artifacts/` (relative to repository root)
- Configurable via build script configuration

### File Format

Python pickle format (protocol version 5, Python 3.8+).

**Serialized Structure**:

```python
{
    "entity_id_1": [float, float, ...],  # 768-dim list
    "entity_id_2": [float, float, ...],
    ...
}
```

Or for usage embeddings:

```python
{
    ("callee_id", "caller_compound", "caller_sig"): [float, float, ...],
    ...
}
```

**Key properties**:
- Dict keys are the primary identifiers for the embedding source
- Dict values are lists of floats (embedding vectors)
- No metadata stored in cache file (model config is in filename)

---

## Type Identifier Semantics

### Built-in Types

| Type ID | Description | Key Format | Source Data |
|---------|-------------|------------|-------------|
| `entity` | Entity documentation embeddings | `entity_id: str` | Entity docs from doc_db |
| `usages` | Usage description embeddings | `(callee_id, caller_compound, caller_sig): tuple` | Usage descriptions |

### Future Types (Examples)

| Type ID | Description | Key Format | Source Data |
|---------|-------------|------------|-------------|
| `subsystem` | Subsystem docs | `subsystem_id: str` | Subsystem documentation |
| `capability` | Capability descriptions | `capability_name: str` | Capability definitions |

### Type Identifier Rules

- **Format**: Alphanumeric, underscores, hyphens only (`[a-zA-Z0-9_-]+`)
- **Case**: Lowercase recommended for consistency
- **Length**: No hard limit; keep under 20 characters for filename sanity
- **Reserved**: None; all identifiers available for use

---

## Cache Key Composition

**Cache Key** = `(model_slug, dimension, type)`

### Model Slug

- Derived from embedding model name
- Normalized: lowercase, spaces→hyphens, slashes→hyphens
- Examples:
  - `BAAI/bge-base-en-v1.5` → `bge-base-en-v1-5`
  - `text-embedding-3-small` → `text-embedding-3-small`

### Dimension

- Integer vector dimension as string
- Examples: `768`, `1536`, `3072`

### Type

- Embedding package type identifier
- Examples: `entity`, `usages`, `subsystem`

### Cache Invalidation

Cache is invalid (regenerated) if:
- Model slug changes (different model)
- Dimension changes (different model configuration)
- Type identifier changes (different embedding package)
- File does not exist
- File is corrupted (pickle deserialization fails)

Cache remains valid (reused) if:
- All three key components match existing file
- File exists and deserializes successfully

**Manual invalidation**: Operator deletes cache file to force regeneration.

---

## Invariants

1. **One file per type**: Each `(model, dimension, type)` tuple maps to exactly one cache file.
2. **Independent invalidation**: Invalidating one type's cache does not affect other types.
3. **Deterministic naming**: Same key always produces same filename.
4. **No metadata in file**: All configuration is encoded in filename; file contains only embeddings dict.
5. **No version tracking**: Cache does not store creation timestamp or model version; filename is the identity.

---

## Migration from Legacy

### Legacy Format

```
embed_cache_{model_slug}_{dimension}.pkl
```

(No type suffix)

### Migration Path

1. **Operator action required**: Rename or delete legacy files
2. **Suggested rename**: `embed_cache_bge-base-en-v1-5_768.pkl` → `embed_cache_bge-base-en-v1-5_768_entity.pkl`
3. **Alternative**: Delete legacy file; build regenerates with new naming

### Build Behavior

If loading entity embeddings and legacy file exists (no `_entity` suffix) but new file does not exist:
- Build logs clear message: "Legacy cache file detected at {path}. Rename to {new_path} or delete to regenerate."
- Build does NOT automatically load or migrate legacy file
- Build proceeds with cache miss (regenerate entity embeddings)
