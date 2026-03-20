# Contract: Embedding Cache Persistence

**Module**: `mcp/doc_server/build_helpers/embeddings.py`
**Date**: 2026-03-20

---

## Overview

This contract defines the save and load functions for the generalized embedding cache mechanism. Both functions accept a type identifier parameter to distinguish between different embedding packages.

---

## Function: `save_embedding_cache`

### Signature

```python
def save_embedding_cache(
    embeddings: dict[str | tuple, list[float]],
    artifacts_path: Path,
    model_slug: str,
    dimension: int,
    embedding_type: str,
) -> None:
```

### Parameters

- **`embeddings`**: Dict mapping entity/usage identifiers to embedding vectors
  - Keys: `str` (entity IDs) or `tuple` (usage composite keys)
  - Values: `list[float]` (embedding vectors, length = dimension)
- **`artifacts_path`**: Path to artifacts directory where cache files are stored
- **`model_slug`**: Embedding model identifier (normalized, lowercase)
- **`dimension`**: Vector dimension (must match actual embedding vector length)
- **`embedding_type`**: Type identifier string (alphanumeric, underscores, hyphens)

### Returns

- **`None`**: Function succeeds silently

### Raises

- **`ValueError`**: If `embedding_type` contains invalid characters (not alphanumeric/underscore/hyphen)
- **`OSError`**: If cache file cannot be written (permissions, disk full, etc.)
- **`PickleError`**: If embeddings dict cannot be serialized

### Behavior

1. Validate `embedding_type` format (alphanumeric, `_`, `-` only)
2. Construct cache filename: `embed_cache_{model_slug}_{dimension}_{embedding_type}.pkl`
3. Serialize `embeddings` dict to pickle format (protocol 5)
4. Write to `artifacts_path / filename` atomically (write temp, rename)
5. Log success: `log.info("Saved embedding cache", type=embedding_type, count=len(embeddings), path=str(path))`

### Invariants

- Function is idempotent: calling twice with same inputs produces identical file
- File is created atomically (no partial writes observable)
- No automatic retry on failure
- Does not check for existing file before overwriting

---

## Function: `load_embedding_cache`

### Signature

```python
def load_embedding_cache(
    artifacts_path: Path,
    model_slug: str,
    dimension: int,
    embedding_type: str,
) -> dict[str | tuple, list[float]] | None:
```

### Parameters

- **`artifacts_path`**: Path to artifacts directory where cache files are stored
- **`model_slug`**: Embedding model identifier (normalized, lowercase)
- **`dimension`**: Vector dimension
- **`embedding_type`**: Type identifier string

### Returns

- **`dict[str | tuple, list[float]]`**: Cached embeddings if file exists and is valid
- **`None`**: If file does not exist or cannot be loaded

### Raises

- **`ValueError`**: If `embedding_type` contains invalid characters

### Behavior

1. Validate `embedding_type` format
2. Construct cache filename: `embed_cache_{model_slug}_{dimension}_{embedding_type}.pkl`
3. Check if file exists at `artifacts_path / filename`
4. If file does not exist:
   - Log: `log.info("No cache found", type=embedding_type, model=model_slug, dimension=dimension)`
   - Return `None`
5. If file exists:
   - Attempt to load via `pickle.load()`
   - If deserialization succeeds:
     - Log: `log.info("Loaded embedding cache", type=embedding_type, count=len(embeddings), path=str(path))`
     - Return embeddings dict
   - If deserialization fails (corrupt file):
     - Log: `log.warning("Cache file corrupted, will regenerate", type=embedding_type, path=str(path), error=str(exc))`
     - Return `None`

### Invariants

- Function never raises on missing or corrupt cache file (returns `None`)
- Function is deterministic: same inputs + same file → same output
- Does not modify filesystem
- Does not validate embedding vector dimensions or types (caller's responsibility)

---

## Legacy File Detection

When `embedding_type == "entity"`, the load function also checks for legacy cache file without suffix.

### Behavior

1. Attempt to load `embed_cache_{model_slug}_{dimension}_entity.pkl`
2. If not found, check for legacy `embed_cache_{model_slug}_{dimension}.pkl`
3. If legacy file exists:
   - Log: `log.warning("Legacy cache file detected", legacy_path=str(legacy_path), new_path=str(new_path), message="Rename or delete legacy file to migrate")`
   - Return `None` (do not load legacy file)

**Rationale**: Forces operators to explicitly migrate, maintains consistency.

---

## Type Identifier Validation

### Valid Format

- Regex: `^[a-zA-Z0-9_-]+$`
- Examples: `entity`, `usages`, `subsystem_v2`, `cap-descriptions`

### Invalid Examples

- `entity.usages` (contains dot)
- `entity/usages` (contains slash)
- `entity usages` (contains space)
- `""` (empty string)

### Validation Logic

```python
import re

def _validate_type_identifier(embedding_type: str) -> None:
    if not re.match(r'^[a-zA-Z0-9_-]+$', embedding_type):
        raise ValueError(
            f"Invalid embedding_type '{embedding_type}': "
            "must contain only alphanumeric characters, underscores, and hyphens"
        )
```

---

## Usage Examples

### Save Entity Embeddings

```python
from pathlib import Path
from build_helpers.embeddings import save_embedding_cache

embeddings = {
    "fn:abc123": [0.1, 0.2, ...],  # 768 floats
    "cls:def456": [0.3, 0.4, ...],
}

save_embedding_cache(
    embeddings=embeddings,
    artifacts_path=Path("artifacts"),
    model_slug="bge-base-en-v1-5",
    dimension=768,
    embedding_type="entity",
)
# → Creates artifacts/embed_cache_bge-base-en-v1-5_768_entity.pkl
```

### Load Usage Embeddings

```python
from build_helpers.embeddings import load_embedding_cache

embeddings = load_embedding_cache(
    artifacts_path=Path("artifacts"),
    model_slug="bge-base-en-v1-5",
    dimension=768,
    embedding_type="usages",
)

if embeddings is None:
    # Cache miss or corrupt file → regenerate
    embeddings = generate_usage_embeddings()
    save_embedding_cache(embeddings, Path("artifacts"), "bge-base-en-v1-5", 768, "usages")
else:
    # Cache hit → reuse
    pass
```

---

## Error Handling

### Caller Responsibilities

- Ensure `artifacts_path` exists and is writable
- Pass correct `dimension` matching actual embedding vectors
- Handle `None` return from load (cache miss)
- Regenerate embeddings on cache miss

### Function Responsibilities

- Validate type identifier format (raise `ValueError`)
- Log all cache operations at INFO level
- Log corruption/errors at WARNING level
- Never silently fail or fall back
