# Feature Specification: Local FastEmbed Provider

**Feature Branch**: `004-local-fastembed-provider`  
**Created**: 2026-03-15  
**Status**: Draft  
**Input**: User description: "Integrate FastEmbed as a bundled local embedding provider to replace hosted model dependency, with runtime provider selection and auto-generation of embedding artifacts"

## Clarifications

### Session 2026-03-15

- Q: When source data changes but a stale artifact exists, how should the build handle invalidation? → A: Manual invalidation only — developer deletes the artifact file to trigger regeneration.
- Q: What should the server do at startup if the database contains vectors of a different dimension than the configured provider? → A: Ignore — rely on the developer to rebuild after config changes; pgvector errors surface naturally at query time.

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Zero-Dependency Database Build (Priority: P1)

A developer clones the repository and runs the database build script for the first time. They have no pre-computed embedding artifact and no hosted embedding service. The build script detects that the embedding artifact is missing, generates embeddings locally using the bundled model, saves the artifact for future builds, and loads the vectors into the database. Subsequent builds skip generation and load the cached artifact directly.

**Why this priority**: This is the core value proposition — the server becomes self-contained. Without this, developers must either run a separate hosted embedding service or obtain a pre-built artifact from another source before they can build.

**Independent Test**: Run `build_mcp_db.py` with embedding provider set to "local" and no artifact file present. Verify that the artifact is created, entities receive embeddings, and the database is populated.

**Acceptance Scenarios**:

1. **Given** embedding provider is configured as "local" and no matching artifact file exists, **When** the build script runs, **Then** embeddings are generated for all documented entities, saved to an artifact file named by model and dimension, and loaded into the database.
2. **Given** a matching artifact file already exists from a previous build, **When** the build script runs, **Then** the existing artifact is loaded directly without regenerating embeddings.
3. **Given** embedding provider is not configured (unset), **When** the build script runs and no artifact exists, **Then** the build completes successfully with no embeddings (entities have null embedding columns) and a warning is logged.

---

### User Story 2 — Semantic Search with Local Embeddings (Priority: P1)

A user issues a search query through the MCP server (e.g., searching for "combat damage calculation"). The server embeds the query locally using the same bundled model that produced the stored vectors, performs a cosine similarity search against the database, and returns ranked results combining semantic and keyword scores.

**Why this priority**: Semantic search is the primary consumer of embeddings at runtime. If query-time embedding doesn't work, the stored vectors have no value.

**Independent Test**: Start the server with embedding provider set to "local", issue a search query via an MCP tool, and verify results include semantic scores (not just keyword fallback).

**Acceptance Scenarios**:

1. **Given** the server is running with a local embedding provider and entities have stored embeddings, **When** a user performs a search query, **Then** the search returns results with `search_mode: "hybrid"` (not "keyword_fallback") and results are ranked by combined semantic + keyword scores.
2. **Given** the server is running with no embedding provider configured, **When** a user performs a search query, **Then** the search gracefully degrades to keyword-only mode and results have `search_mode: "keyword_fallback"`.
3. **Given** the local embedding model encounters an error during query embedding, **When** a user performs a search, **Then** the system logs the error and falls back to keyword-only search rather than failing.

---

### User Story 3 — Hosted Provider Remains Available (Priority: P2)

A developer who prefers a hosted embedding service (e.g., a local LM Studio instance or OpenAI API) configures the server to use hosted mode. The system uses the hosted service for both artifact generation and runtime query embedding, following the same artifact caching and query patterns as local mode.

**Why this priority**: Preserving the hosted option ensures backward compatibility and lets developers with access to higher-quality hosted models continue using them.

**Independent Test**: Configure embedding provider as "hosted" with a running OpenAI-compatible endpoint, build the database, start the server, and verify semantic search works end-to-end.

**Acceptance Scenarios**:

1. **Given** embedding provider is set to "hosted" with valid endpoint configuration, **When** the build script runs without a matching artifact, **Then** embeddings are generated via the hosted service, saved to an artifact file named by the hosted model and dimension, and loaded into the database.
2. **Given** embedding provider is set to "hosted", **When** the server processes a search query, **Then** the query is embedded via the hosted service and semantic search returns hybrid results.
3. **Given** embedding provider is set to "hosted" but the endpoint is unreachable at build time, **When** the build script runs and no artifact exists, **Then** the build fails with a clear error message indicating the hosted service is unavailable.

---

### User Story 4 — Switching Between Providers (Priority: P3)

A developer decides to switch from a hosted embedding model to the local model (or vice versa). They update the environment configuration and re-run the database build. The system detects that no artifact exists for the newly configured model, generates a fresh one, and rebuilds the database with the new vectors at the correct dimension.

**Why this priority**: Clean provider switching is important for flexibility but is a less frequent operation than day-to-day building and searching.

**Independent Test**: Build once with "hosted" provider, then change config to "local" and rebuild. Verify a new artifact is generated and the database uses the new dimension.

**Acceptance Scenarios**:

1. **Given** a database was previously built with a hosted model (e.g., 4096-dim) and the developer changes config to local (768-dim), **When** the build script runs, **Then** a new artifact is generated for the local model, the database schema is recreated with the correct vector dimension, and search works correctly.
2. **Given** artifacts exist for both provider configurations, **When** the build script runs with either provider, **Then** the matching artifact is loaded based on the model name and dimension in the filename.

---

### Edge Cases

- **Mismatched dimension**: The configured dimension does not match the actual model output. The system must detect this and fail fast with a clear error at startup or build time rather than silently storing wrong-dimension vectors.
- **Corrupt or truncated artifact**: The artifact file exists but is corrupted (e.g., partial write). The build should fail with a clear error rather than loading garbage vectors.
- **Empty entity documentation**: An entity has no documentation fields (no brief, details, params, etc.). The system should skip embedding generation for that entity rather than embedding an empty or stub string.
- **First-run model download**: The local model ONNX files are not yet cached on the machine. The system should log that a download is occurring and handle download failures gracefully with a clear error.
- **Concurrent builds**: Two build processes run simultaneously and attempt to write the same artifact file. The system should not corrupt the artifact. (Acceptable: last-write-wins; not acceptable: partial/corrupt file.)
- **Stale artifact**: Source documentation has changed but the artifact file still exists from a previous build. The system loads the stale artifact without warning. The developer is responsible for deleting the artifact to force regeneration.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST support a configurable embedding provider with at least two modes: "local" (bundled, no external service) and "hosted" (OpenAI-compatible endpoint), selectable via environment configuration.
- **FR-002**: System MUST support a "no provider" mode where embedding is entirely disabled, and all search degrades to keyword-only. This MUST be the default when no provider is configured.
- **FR-003**: When configured for local mode, the system MUST default to the bundled ONNX-based embedding model BAAI/bge-base-en-v1.5 (768-dim). The model name MUST be configurable via `EMBEDDING_LOCAL_MODEL` to allow advanced users to substitute a different FastEmbed-compatible model, but only the default model is tested and documented. No network access is required after the initial one-time model download.
- **FR-004**: The database build process MUST load embedding vectors from a cached artifact file if one matching the current model configuration exists. Artifact invalidation is manual — the developer deletes the file to trigger regeneration. No automatic staleness detection is required.
- **FR-005**: The database build process MUST generate embeddings on demand when no matching artifact file exists and an embedding provider is configured, then save the result as an artifact for future builds.
- **FR-006**: Embedding artifacts MUST be named using a convention that encodes the model identity and vector dimension (e.g., `embed_cache_{model}_{dim}.pkl`) so that artifacts for different models coexist without collision.
- **FR-007**: The database schema MUST use a vector column dimension that matches the configured embedding provider's output dimension, not a hardcoded value.
- **FR-008**: The text used for embedding each entity MUST be a structured docstring reconstructed from entity documentation fields (name, kind, brief, details, params, returns, notes, rationale), matching the format used by the original embedding generation pipeline.
- **FR-009**: The runtime query embedding pathway MUST use the same provider and model that generated the stored vectors, ensuring dimensional and semantic consistency.
- **FR-010**: The old hardcoded `embeddings_cache.pkl` artifact (4096-dim) MUST no longer be a required build artifact. The build validation step MUST NOT fail when this file is absent.
- **FR-011**: The system MUST validate at startup that the configured vector dimension matches the embedding provider's actual output dimension and fail fast with a clear error if they disagree. No validation is required against the database's stored vector dimension — the developer is responsible for rebuilding after config changes.
- **FR-012**: The local embedding provider MUST NOT block the server's event loop during query-time embedding. Embedding computation MUST be offloaded to a background thread.
- **FR-013**: Entities with no documentable content (no brief, details, params, or other documentation fields) MUST be skipped during embedding generation and receive a null embedding.

### Key Entities

- **Embedding Provider**: An abstraction that can embed a single query string or a batch of document strings into fixed-dimension float vectors. Has a declared dimension. Two variants: local (bundled ONNX model) and hosted (OpenAI-compatible endpoint).
- **Embedding Artifact**: A serialized file mapping entity identifiers to their embedding vectors. Named by model and dimension. Produced once during build, loaded on subsequent builds.
- **Entity Embed Text**: The canonical text representation of an entity used as input to the embedding model. Constructed from entity documentation fields in a structured Doxygen-like format. Consistent across both providers.
- **Entity (existing)**: Extended with a vector column whose dimension is configured rather than fixed. Null embedding allowed for entities without documentation.

## Assumptions

- The BAAI/bge-base-en-v1.5 model produces 768-dimensional vectors. This is verified at runtime; if a future model version changes dimensions, the config must be updated accordingly.
- The ONNX model files are cached locally by the FastEmbed library (in `~/.cache/fastembed/`) after initial download. First-run requires internet access for this download; subsequent runs are fully offline.
- The database schema is dropped and recreated on every build. No migration is needed for dimension changes — a clean rebuild handles it.
- Embedding ~5,300 entities locally takes approximately 1–3 minutes on a modern CPU. This is acceptable for an offline build step.
- Single-query local embedding takes approximately 5–20ms on a modern CPU, which is acceptable for interactive search latency.
- The artifact file format remains Python pickle. Both providers produce Python `list[float]` vectors stored identically.
- Build and server always share the same embedding dimension configuration (both read from the same environment).
- After switching embedding providers, the developer is responsible for re-running the database build. The server does not detect or warn about dimension mismatches between the configured provider and vectors already in the database.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A developer can build the database and run semantic searches with zero external service dependencies by configuring "local" mode. No hosted endpoint, API key, or pre-built artifact is required.
- **SC-002**: Semantic search quality with the local model returns relevant results for domain-specific queries (e.g., searching "combat damage" surfaces `fight.cc` functions, searching "save player" surfaces `save.cc` functions) in the top 5 results.
- **SC-003**: Embedding artifact generation for the full entity set (~5,300 entities) completes within 5 minutes on a standard development machine.
- **SC-004**: Query-time embedding adds less than 100ms of latency to search requests when using the local provider.
- **SC-005**: Switching between local and hosted providers requires only changing environment configuration and re-running the build — no code changes, no manual artifact management.
- **SC-006**: The build process correctly loads cached artifacts when present, avoiding re-generation. A second build with no source changes skips embedding generation entirely.
