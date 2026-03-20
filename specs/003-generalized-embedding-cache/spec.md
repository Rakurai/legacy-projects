# Feature Specification: Generalized Embedding Cache

**Feature Branch**: `003-generalized-embedding-cache`
**Created**: 2026-03-20
**Status**: Draft
**Input**: User description: "we need to save/load embeddings that are generated from usages, using a different pkl file (append \"_usages\" to the current embed_cache file stem).  don't create a new code path, let's generalize and reuse the embedding persistence as we may have more embedding packages to handle later"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Entity Embedding Cache Persistence (Priority: P1) 🎯 MVP

The build script generates embeddings for ~5,300 entities during database population. When the same embedding model configuration is used across multiple builds, the build operator expects the script to reuse cached embeddings from the previous run rather than regenerating them, reducing build time from ~3 minutes to seconds for the embedding phase. The existing entity embedding cache file (`embed_cache_{model}_{dim}.pkl`) must continue to work without changes.

**Why this priority**: This is the baseline functionality that already exists. Preserving it ensures no regression while adding new capabilities. The generalized mechanism must maintain backward compatibility with existing cache files.

**Independent Test**: Can be fully tested by running two consecutive builds with the same embedding configuration and verifying that the second build reuses the entity embedding cache, completing the embedding phase in under 10 seconds.

**Acceptance Scenarios**:

1. **Given** an existing entity embedding cache file, **When** build runs with matching model configuration, **Then** entity embeddings are loaded from cache and not regenerated
2. **Given** no entity embedding cache exists, **When** build completes, **Then** entity embedding cache file is created for reuse in subsequent builds
3. **Given** entity embedding cache with different model configuration, **When** build runs with new configuration, **Then** cache is regenerated with new model and saved

---

### User Story 2 - Usage Embedding Cache Persistence (Priority: P2)

The build script generates embeddings for entity usage descriptions (behavioral descriptions of how parameters are used in calling contexts). When building the database multiple times with the same embedding configuration, the build operator expects usage embeddings to be cached separately from entity embeddings so that changes to entity data do not invalidate the usage embedding cache, and vice versa. Usage embedding cache files are named with the suffix `_usages` (e.g., `embed_cache_{model}_{dim}_usages.pkl`).

**Why this priority**: Usage embeddings are a distinct embedding package with different source data from entity embeddings. Caching them separately allows independent invalidation and reduces unnecessary regeneration when only one data source changes.

**Independent Test**: Can be fully tested by running a build that generates usage embeddings, modifying entity data but not usage data, then rebuilding and verifying that usage embeddings are loaded from cache while entity embeddings are regenerated.

**Acceptance Scenarios**:

1. **Given** an existing usage embedding cache file, **When** build runs with matching model configuration, **Then** usage embeddings are loaded from cache
2. **Given** no usage embedding cache exists, **When** build generates usage embeddings, **Then** usage embedding cache file is created with `_usages` suffix
3. **Given** entity embedding cache is invalidated, **When** build regenerates entity embeddings, **Then** usage embedding cache remains valid and is reused

---

### User Story 3 - Extensible Cache Mechanism for Future Types (Priority: P3)

The build system maintainer needs to add new embedding types in the future (e.g., subsystem documentation embeddings, capability description embeddings). The cache persistence mechanism should support adding new types by specifying a type identifier without duplicating save/load logic. Each type gets its own cache file with the type identifier as a suffix.

**Why this priority**: This is a design goal rather than immediate functionality. The generalized mechanism makes future additions straightforward without refactoring.

**Independent Test**: Can be tested by adding a new embedding type (e.g., "subsystem") and verifying that the cache mechanism automatically creates and loads `embed_cache_{model}_{dim}_subsystem.pkl` without requiring new save/load code paths.

**Acceptance Scenarios**:

1. **Given** a new embedding type identifier, **When** save operation is called with that type, **Then** cache file is created with the type suffix appended
2. **Given** multiple embedding types in use, **When** one type's cache is invalidated, **Then** other types' caches remain valid and are reused
3. **Given** a new embedding type, **When** load operation is called, **Then** type-specific cache file is located and loaded without code changes

---

### Edge Cases

- What happens when an embedding type's cache file exists but is corrupted (invalid pickle data)? The build detects corruption via pickle deserialization errors, logs a clear warning, regenerates embeddings for that type, and saves a new cache file.
- What happens when multiple embedding types are cached but the embedding model configuration changes? All cache files for the old configuration must be ignored, and new cache files must be generated for each type with the new configuration.
- What happens when the type identifier contains characters invalid for filenames? The cache mechanism must sanitize or reject invalid type identifiers to prevent filesystem errors.
- What happens when an embedding type's source data changes (e.g., usage descriptions updated) but the model configuration remains the same? The operator must manually delete the type-specific cache file to force regeneration, or the build script must detect source data changes and invalidate the cache automatically (implementation decides which approach).

## Requirements *(mandatory)*

### Functional Requirements

#### Generalized Cache Mechanism

- **FR-001**: The embedding cache persistence mechanism MUST accept a type identifier parameter (string) to distinguish between different embedding packages (e.g., "entity", "usages")
- **FR-002**: Cache files MUST be named using model slug, dimension, and type identifier: `embed_cache_{model_slug}_{dimension}_{type}.pkl` where {model_slug} identifies the embedding model, {dimension} is the vector dimension, and {type} is the embedding package type (e.g., `embed_cache_bge-base-en-v1-5_768_usages.pkl`). Provider type and model version are not included in the filename.
- **FR-003**: The type identifier for entity embeddings MUST be "entity", resulting in cache files named `embed_cache_{model}_{dim}_entity.pkl`. All embedding types use consistent naming with type-specific suffixes.
- **FR-004**: The save operation MUST accept embeddings data and a type identifier, and persist the data to the type-specific cache file
- **FR-005**: The load operation MUST accept a type identifier, locate the corresponding cache file, and return the cached embeddings if the file exists and is valid

#### Cache File Management

- **FR-006**: Each embedding type MUST have its own independent cache file so that invalidating one type's cache does not affect other types
- **FR-007**: Cache files MUST be stored in the artifacts directory alongside other build artifacts (`artifacts/` by default)
- **FR-008**: Cache file existence MUST be checked before attempting to load. If the file exists, attempt to load via pickle deserialization. If deserialization raises an exception (corruption, invalid format), return None or indicate cache miss. No additional validation (size checks, checksums) is performed.
- **FR-009**: The build script MUST log cache hit/miss status for each embedding type during the load phase (INFO level: "Loaded {N} embeddings from cache for type '{type}'" or "No cache found for type '{type}', will generate embeddings")

#### Migration

- **FR-010**: When loading entity embeddings, if a legacy cache file without suffix (`embed_cache_{model}_{dim}.pkl`) exists but no `_entity` suffix file exists, the build MUST log a clear message indicating the legacy file must be renamed or deleted
- **FR-011**: The build script MUST NOT automatically migrate or fall back to legacy cache file naming. Operators are responsible for manually migrating existing cache files by renaming or deleting them.

### Key Entities

- **Embedding Package**: A collection of embeddings generated from a specific data source (entities, usages, subsystems, etc.) with a unique type identifier. Each package has its own cache file.
- **Cache File**: A pickle file storing pre-computed embeddings for an embedding package, keyed by the type identifier and model configuration. File naming: `embed_cache_{model_slug}_{dimension}_{type}.pkl`.
- **Type Identifier**: A string label distinguishing different embedding packages (e.g., "entity", "usages", "subsystem"). Used as a suffix in cache filenames.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: After a full build generating both entity and usage embeddings, two distinct cache files exist in the artifacts directory: one for entities, one for usages
- **SC-002**: When only entity data changes, a rebuild reuses the usage embedding cache and completes usage embedding phase in under 5 seconds
- **SC-003**: When only usage data changes, a rebuild reuses the entity embedding cache and completes entity embedding phase in under 5 seconds
- **SC-004**: Adding a new embedding type requires no changes to the save/load persistence functions, only passing a new type identifier
- **SC-005**: Build script logs clearly indicate cache hit/miss status for each embedding type, allowing operators to verify cache reuse
- **SC-006**: Corrupted cache files are detected and regenerated without build failure, with a clear warning logged

### Assumptions

- **A-001**: Embedding type identifiers are known at build time and are provided as string constants or configuration parameters
- **A-002**: Each embedding type's data source is independent, so caching one type does not require caching another
- **A-003**: Cache invalidation is manual or based on model configuration changes; automatic source data change detection is not required
- **A-004**: Type identifiers are filesystem-safe (alphanumeric, underscores, hyphens) and do not contain path separators or special characters
- **A-005**: Cache files use pickle format consistently across all embedding types
- **A-006**: The model configuration (model slug, dimension) is the same for all embedding types in a given build (or each type specifies its own model configuration explicitly if they differ)
- **A-007**: Operators do not run concurrent builds writing to the same artifacts directory; no file locking or conflict detection is required
- **A-008**: Cache invalidation based on model slug and dimension is sufficient; if model implementation details change (different checkpoint, version, or provider) while maintaining the same slug/dimension, operators must manually delete cache files to force regeneration

## Clarifications

### Session 2026-03-20

- Q: Should entity embeddings use a type suffix ("entity") or remain without suffix for backward compatibility? → A: Use `_entity` suffix for consistency. All embedding types use the same naming pattern with type-specific suffixes. Operators must manually rename or delete existing `embed_cache_{model}_{dim}.pkl` files to migrate to the new naming convention.
- Q: How should the cache mechanism handle concurrent builds writing to the same cache files? → A: No special handling; assume operators don't run concurrent builds targeting the same artifacts directory.
- Q: What level of cache corruption detection should be implemented? → A: Only catch pickle deserialization errors during load; no proactive validation such as size checks or checksums.
- Q: What components should form the cache key for identifying cache files? → A: Model slug + dimension only.
