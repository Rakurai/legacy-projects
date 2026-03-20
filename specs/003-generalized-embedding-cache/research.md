# Research: Generalized Embedding Cache

**Branch**: `003-generalized-embedding-cache` | **Date**: 2026-03-20

---

## R-001: Cache Persistence Format

**Decision**: Continue using pickle format (`.pkl` files) for all embedding types.

**Rationale**:
- Existing entity embedding cache already uses pickle successfully
- Pickle handles numpy arrays and complex nested structures natively
- Performance is sufficient for build-time caching (load/save under 1 second)
- No schema evolution needed (regenerate cache if model changes)
- Standard library support, no additional dependencies

**Alternatives considered**:
- **JSON**: Cannot serialize numpy arrays without custom encoding; slower
- **NPZ (numpy)**: Only handles numpy arrays, not general dicts/metadata
- **HDF5**: Over-engineered for simple key-value cache; adds dependency
- **MessagePack**: Additional dependency; no significant benefit over pickle for offline use

---

## R-002: Type Parameterization Strategy

**Decision**: Accept type identifier as a string parameter to save/load functions. Append type to filename stem.

**Rationale**:
- Enables unlimited embedding types without code changes
- Type identifier becomes part of cache key (model + dimension + type)
- Each type gets independent cache file for selective invalidation
- Clear naming convention: `embed_cache_{model}_{dim}_{type}.pkl`

**Alternatives considered**:
- **Separate save/load functions per type**: Violates DRY; doesn't scale
- **Type enum**: Requires code changes for new types; too restrictive
- **Directory per type**: Adds filesystem complexity; flat structure simpler

---

## R-003: Cache Key Design

**Decision**: Cache key is `(model_slug, dimension, type)`. Filename: `embed_cache_{model}_{dim}_{type}.pkl`.

**Rationale**:
- Model slug identifies the embedding model (e.g., "bge-base-en-v1-5")
- Dimension distinguishes different model configurations
- Type distinguishes embedding packages (entity, usages, etc.)
- If any component changes, cache is invalid and regenerated
- Operators manually delete cache if model internals change

**Alternatives considered**:
- **Include provider type**: Adds unnecessary complexity; model slug already identifies the model
- **Include model version hash**: Over-engineered; operators can delete cache manually
- **Include timestamp**: Breaks deterministic caching; wrong layer for invalidation

---

## R-004: Corruption Detection

**Decision**: Detect corruption via pickle deserialization errors only. No checksums or size validation.

**Rationale**:
- Pickle deserialization fails loudly on invalid data
- Worst case: regenerate embeddings (acceptable for build-time cache)
- Checksums add overhead for minimal benefit in offline build context
- Size checks don't catch semantic corruption (wrong embeddings cached)

**Alternatives considered**:
- **Checksum validation**: Adds overhead, false sense of security (doesn't catch semantic errors)
- **Size checks**: Doesn't detect corruption, only truncation; pickle handles that
- **Embedding count/dimension validation**: Requires passing expected metadata; adds complexity

---

## R-005: Concurrent Build Safety

**Decision**: No special handling. Assume operators don't run concurrent builds targeting the same artifacts directory.

**Rationale**:
- Typical use case is single sequential build
- File locking adds platform-specific complexity
- Conflict detection adds overhead and doesn't prevent issues
- Operators can use separate artifacts directories for parallel builds

**Alternatives considered**:
- **File locking**: Platform-specific; deadlock risk; unnecessary for typical use
- **Conflict detection**: Catches issues late; doesn't prevent corruption
- **Atomic writes**: Still allows last-write-wins; doesn't solve the problem

---

## R-006: Legacy File Migration

**Decision**: No automatic migration. Operators manually rename or delete legacy `embed_cache_{model}_{dim}.pkl` files.

**Rationale**:
- Clean consistent naming: all types use `_type` suffix
- Automatic migration adds complexity and edge cases
- One-time operator action is acceptable for feature upgrade
- Clear error message guides operators to correct action

**Alternatives considered**:
- **Automatic fallback**: Entity embeddings special-cased; violates consistency
- **Automatic rename**: Risky (file permissions, race conditions); better to let operators control
- **Dual naming support**: Perpetuates inconsistency; defeats the point

---

## Unresolved Questions

None. All design decisions finalized during planning.
