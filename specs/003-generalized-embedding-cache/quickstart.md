# Quickstart: Generalized Embedding Cache

**Feature**: 003-generalized-embedding-cache
**Date**: 2026-03-20

---

## Overview

This quickstart demonstrates how to use the generalized embedding cache mechanism to save and load embeddings for different types (entities, usages, future types).

---

## Prerequisites

- Python 3.14+ environment with uv
- Artifacts directory exists (default: `artifacts/`)
- Embedding provider configured (for generation)

---

## Basic Usage

### 1. Save Embeddings

```python
from pathlib import Path
from build_helpers.embeddings import save_embedding_cache

# Generate or obtain embeddings
embeddings = {
    "fn:abc123": [0.1, 0.2, 0.3, ...],  # 768-dimensional vector
    "cls:def456": [0.4, 0.5, 0.6, ...],
}

# Save to cache with type identifier
save_embedding_cache(
    embeddings=embeddings,
    artifacts_path=Path("artifacts"),
    model_slug="bge-base-en-v1-5",
    dimension=768,
    embedding_type="entity",
)

# Result: artifacts/embed_cache_bge-base-en-v1-5_768_entity.pkl created
```

### 2. Load Embeddings

```python
from build_helpers.embeddings import load_embedding_cache

# Attempt to load from cache
embeddings = load_embedding_cache(
    artifacts_path=Path("artifacts"),
    model_slug="bge-base-en-v1-5",
    dimension=768,
    embedding_type="entity",
)

if embeddings is None:
    # Cache miss → generate embeddings
    embeddings = generate_entity_embeddings()
    # Save for next build
    save_embedding_cache(embeddings, Path("artifacts"), "bge-base-en-v1-5", 768, "entity")
else:
    # Cache hit → use cached embeddings
    print(f"Loaded {len(embeddings)} embeddings from cache")
```

---

## Integration with Build Script

### Entity Embeddings

```python
# In build_mcp_db.py

from build_helpers.embeddings import load_embedding_cache, save_embedding_cache

# Try to load from cache
entity_embeddings = load_embedding_cache(
    artifacts_path=config.artifacts_path,
    model_slug=embedding_provider.model_slug,
    dimension=embedding_provider.dimension,
    embedding_type="entity",
)

if entity_embeddings is None:
    # Generate embeddings for all entities
    log.info("Generating entity embeddings")
    entity_embeddings = generate_embeddings(
        provider=embedding_provider,
        texts=[entity.to_doxygen() for entity in entities],
        keys=[entity.entity_id for entity in entities],
    )
    # Save to cache
    save_embedding_cache(
        embeddings=entity_embeddings,
        artifacts_path=config.artifacts_path,
        model_slug=embedding_provider.model_slug,
        dimension=embedding_provider.dimension,
        embedding_type="entity",
    )

# Use embeddings to populate database
for entity_id, vector in entity_embeddings.items():
    # ... insert into database
```

### Usage Embeddings

```python
# In build_mcp_db.py

# Try to load from cache
usage_embeddings = load_embedding_cache(
    artifacts_path=config.artifacts_path,
    model_slug=embedding_provider.model_slug,
    dimension=embedding_provider.dimension,
    embedding_type="usages",
)

if usage_embeddings is None:
    # Generate embeddings for all usage descriptions
    log.info("Generating usage embeddings")
    usage_embeddings = generate_embeddings(
        provider=embedding_provider,
        texts=[usage.description for usage in all_usages],
        keys=[(u.callee_id, u.caller_compound, u.caller_sig) for u in all_usages],
    )
    # Save to cache
    save_embedding_cache(
        embeddings=usage_embeddings,
        artifacts_path=config.artifacts_path,
        model_slug=embedding_provider.model_slug,
        dimension=embedding_provider.dimension,
        embedding_type="usages",
    )

# Use embeddings to populate database
for (callee_id, caller_compound, caller_sig), vector in usage_embeddings.items():
    # ... insert into database
```

---

## Adding a New Embedding Type

To add a new embedding type (e.g., subsystem documentation):

1. **Choose a type identifier**: `"subsystem"` (lowercase, alphanumeric, underscores, hyphens)

2. **Generate embeddings** for your data source:

```python
subsystem_embeddings = generate_embeddings(
    provider=embedding_provider,
    texts=[subsystem.full_description for subsystem in subsystems],
    keys=[subsystem.id for subsystem in subsystems],
)
```

3. **Save to cache** with new type identifier:

```python
save_embedding_cache(
    embeddings=subsystem_embeddings,
    artifacts_path=config.artifacts_path,
    model_slug=embedding_provider.model_slug,
    dimension=embedding_provider.dimension,
    embedding_type="subsystem",  # New type identifier
)
```

4. **Load from cache** in future builds:

```python
subsystem_embeddings = load_embedding_cache(
    artifacts_path=config.artifacts_path,
    model_slug=embedding_provider.model_slug,
    dimension=embedding_provider.dimension,
    embedding_type="subsystem",  # Same type identifier
)
```

**No code changes needed** to save/load functions. Just pass a new type identifier.

---

## Migrating Legacy Entity Cache

If you have an existing entity cache file without suffix:

### Before

```
artifacts/embed_cache_bge-base-en-v1-5_768.pkl
```

### After

```
artifacts/embed_cache_bge-base-en-v1-5_768_entity.pkl
```

### Migration Steps

**Option 1: Rename**

```bash
cd artifacts
mv embed_cache_bge-base-en-v1-5_768.pkl embed_cache_bge-base-en-v1-5_768_entity.pkl
```

**Option 2: Delete and regenerate**

```bash
rm artifacts/embed_cache_bge-base-en-v1-5_768.pkl
# Next build will regenerate with new naming
```

---

## Cache Invalidation

### Automatic Invalidation

Cache is automatically invalidated (regenerated) when:
- Embedding model changes (`model_slug` changes)
- Vector dimension changes
- Type identifier changes
- Cache file does not exist
- Cache file is corrupted (pickle deserialization fails)

### Manual Invalidation

To force regeneration for a specific type:

```bash
rm artifacts/embed_cache_*_entity.pkl    # Invalidate entity embeddings only
rm artifacts/embed_cache_*_usages.pkl    # Invalidate usage embeddings only
rm artifacts/embed_cache_*.pkl           # Invalidate all types
```

---

## Troubleshooting

### Cache not being reused

**Symptom**: Build regenerates embeddings every time

**Check**:
1. Model slug matches: `log.info` output shows same model slug in save and load
2. Dimension matches: verify dimension parameter is consistent
3. Type identifier matches: check for typos (`"entity"` vs `"entities"`)
4. Artifacts path correct: verify same path passed to save and load
5. File exists: `ls artifacts/embed_cache_*.pkl`

### Corrupted cache file

**Symptom**: Warning logged: "Cache file corrupted, will regenerate"

**Action**: Delete corrupted file and rebuild. Cache will be regenerated.

```bash
rm artifacts/embed_cache_bge-base-en-v1-5_768_entity.pkl
uv run python -m build_script.build_mcp_db
```

### Legacy file warning

**Symptom**: Warning logged: "Legacy cache file detected"

**Action**: Rename or delete legacy file as shown in Migration section above.

---

## Verification

After implementation, verify the cache mechanism works:

```bash
# First build (cold cache)
uv run python -m build_script.build_mcp_db
# Check logs: "Generating entity embeddings" and "Generating usage embeddings"
# Check files: ls artifacts/embed_cache_*_entity.pkl artifacts/embed_cache_*_usages.pkl

# Second build (warm cache)
uv run python -m build_script.build_mcp_db
# Check logs: "Loaded N embeddings from cache for type 'entity'" and same for 'usages'
# Verify embedding phase completes in under 10 seconds
```

Expected output:
- First build: ~3 minutes for embedding generation
- Second build: <10 seconds for embedding phase (cache hit)
- Two distinct cache files in artifacts directory
