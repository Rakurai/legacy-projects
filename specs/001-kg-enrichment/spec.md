# Feature Specification: Knowledge Graph Enrichment (V1)

**Feature Branch**: `001-kg-enrichment`
**Created**: 2026-03-19
**Status**: Draft
**Input**: User description: "write the spec for docs/migration/KG_PROPOSAL.md"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Spec Agent Retrieves Behavioral Contract (Priority: P1)

A spec-creating agent is writing a migration specification for a legacy function (e.g., `damage()`). The agent queries the MCP server and receives a five-part behavioral contract: signature, mechanism description, caller-derived contract (rationale), preconditions and quirks (notes), and top calling patterns with natural-language descriptions of how each caller uses the function. The agent uses this contract to write a migration spec grounded in evidence rather than guesswork.

**Why this priority**: This is the core value proposition — transforming opaque text blobs into structured, queryable behavioral contracts. Without this, agents continue working with unstructured documentation that requires manual interpretation.

**Independent Test**: Can be fully tested by querying a single well-documented entity (e.g., `damage()`) through the `explain_interface` tool and verifying all five contract parts are populated with evidence from existing doc fields.

**Acceptance Scenarios**:

1. **Given** an entity with `brief`, `details`, `rationale`, `notes`, and `usages` fields populated, **When** the agent calls `explain_interface` for that entity, **Then** the response contains all five contract sections with content derived from those fields.
2. **Given** an entity with missing `rationale` (no caller evidence), **When** the agent calls `explain_interface`, **Then** the response returns the available sections and clearly indicates which sections lack evidence.
3. **Given** an entity flagged as `is_contract_seed` (high fan-in + rationale present), **When** the agent retrieves it, **Then** the entity metadata includes the contract seed flag, signaling it as a natural starting point for Wave 1 specs.

---

### User Story 2 - Spec Agent Searches by Usage Intent (Priority: P1)

A spec-creating agent needs to find all entities involved in "applying debuffs after combat." Instead of searching entity names or briefs (which describe what functions do internally), the agent searches over usage descriptions (which describe how callers use functions). The search returns callee entities whose usage patterns match the behavioral query.

**Why this priority**: Usage-based search unlocks a qualitatively different kind of query — searching by behavioral role rather than implementation detail. This is the highest value-to-cost addition identified in the proposal.

**Independent Test**: Can be tested by issuing a semantic search with `source=usages` for a known behavioral pattern (e.g., "apply stat penalty") and verifying the results include entities whose usage descriptions match, even if their names or briefs do not.

**Acceptance Scenarios**:

1. **Given** the `entity_usages` table is populated with ~24,803 caller→callee usage descriptions with embeddings, **When** the agent searches with `source=usages` and query "apply duration-based stat penalties after combat," **Then** the results include entities whose usage descriptions semantically match, ranked by relevance.
2. **Given** a usage description search, **When** results are returned, **Then** each result includes the callee entity, the caller context, and the natural-language usage description.

---

### User Story 3 - Planning Agent Assesses Documentation Quality (Priority: P2)

A planning agent is estimating which entities need source-level verification before spec work can begin. The agent queries entity metadata and uses `doc_state` to distinguish between entities with refined LLM summaries (high confidence) versus extracted summaries (lower confidence). Combined with `notes_length` as a complexity proxy and `rationale_specificity` as a contract quality signal, the agent triages entities into "ready for spec" vs "needs verification."

**Why this priority**: Documentation quality signals reduce wasted agent effort — agents currently cannot distinguish well-documented entities from poorly-documented ones without reading the full text.

**Independent Test**: Can be tested by retrieving entities with varying `doc_state` values and verifying the metadata correctly reflects the documentation generation pass each entity went through.

**Acceptance Scenarios**:

1. **Given** an entity whose generated docs have `state: refined_summary`, **When** the agent retrieves the entity, **Then** the response includes `doc_state: refined_summary`.
2. **Given** an entity with a long, domain-specific rationale, **When** the agent retrieves it, **Then** `rationale_specificity` is higher than for an entity with a generic rationale like "facilitates various operations."
3. **Given** entity retrieval, **When** the agent fetches an entity with notes, **Then** `notes_length` is populated as a numeric complexity proxy available for filtering and ranking.

---

### User Story 4 - Auditor Agent Verifies Spec Claims Against Evidence (Priority: P2)

An auditor agent is reviewing a migration spec dossier. For each postcondition claimed in the spec, the auditor retrieves the `explain_interface` contract for the referenced entities and cross-references the spec's behavioral claims against caller-derived evidence (rationale + usage patterns). Discrepancies between the spec's stated contract and the evidence are flagged.

**Why this priority**: Auditing is a primary consumer of the enriched data but depends on Stories 1 and 2 being functional first.

**Independent Test**: Can be tested by providing a known spec claim about an entity's behavior, calling `explain_interface`, and verifying the evidence either supports or contradicts the claim.

**Acceptance Scenarios**:

1. **Given** a spec claiming "function X delivers damage based on weapon type," **When** the auditor calls `explain_interface` for function X, **Then** the usage patterns and rationale either confirm or contradict the weapon-type dependency.
2. **Given** an entity referenced in a spec but with `doc_state: extracted_summary`, **When** the auditor reviews it, **Then** the low-confidence doc state is visible, flagging it for source-level verification.

---

### Edge Cases

- What happens when an entity has no `usages` data (not among the 2,889 entities with caller evidence)? The system returns the available contract parts and omits the calling-patterns section rather than returning empty or fabricated data.
- What happens when usage description embeddings produce poor semantic matches? Results include keyword matches alongside semantic matches via hybrid search; the agent can broaden the query if initial results are insufficient.
- What happens when an entity's `rationale` is null? The `is_contract_seed` flag is false, `rationale_specificity` is null, and `explain_interface` omits the contract section with a clear indication.
- What happens when the build pipeline encounters a generated_docs entry with unexpected or missing fields? The build fails fast with a clear error identifying the malformed entry.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The build pipeline MUST carry the `doc_state` value from each generated_docs entry's `state` field into the `entities` table as a new column.
- **FR-002**: The build pipeline MUST compute and store `notes_length` (character count of the `notes` field) for each entity.
- **FR-003**: The build pipeline MUST compute and store an `is_contract_seed` boolean flag for each entity, true when `fan_in` exceeds a configurable threshold AND `rationale` is non-null.
- **FR-004**: The build pipeline MUST compute and store a `rationale_specificity` score derived from rationale text length and domain-term density.
- **FR-005**: The build pipeline MUST create and populate an `entity_usages` table by exploding the `usages` dicts from generated_docs, producing one row per caller→callee usage entry with the usage description text. The table MUST be dropped and fully recreated on each build (no incremental updates).
- **FR-006**: Each `entity_usages` row MUST include an embedding vector computed from the usage description text.
- **FR-007**: The MCP server MUST expose an `explain_interface` tool that returns a five-part behavioral contract (signature, mechanism, contract, preconditions, calling patterns) composed from existing entity fields and the new `entity_usages` data. The calling patterns section MUST include the top 5 usage patterns ranked by caller fan-in or relevance.
- **FR-008**: The MCP server's `search` tool MUST support a `source=usages` mode that performs hybrid search (semantic + keyword/full-text) over usage descriptions, consistent with the existing V1 hybrid search pattern. Results MUST be grouped by callee entity (one result per entity), with the top-matching usage descriptions inlined as supporting evidence.
- **FR-009**: The MCP server's `get_entity` response MUST include `doc_state`, `notes_length`, `is_contract_seed`, and `rationale_specificity` fields.
- **FR-010**: The MCP server's `get_entity` tool MUST support an `include_usages` parameter that, when true, inlines the top 5 usage patterns for the entity, ranked by caller fan-in or relevance.
- **FR-012**: The `entity_usages` table MUST support querying by callee (all callers of entity X and their usage descriptions) and by caller (all callees used by function Y and why).
- **FR-013**: The build pipeline MUST fail fast with a clear error if required source fields are missing or malformed in the generated_docs artifacts.

### Key Entities

- **Entity (enriched)**: A code element (function, variable, class, etc.) from the legacy codebase. Gains `doc_state`, `notes_length`, `is_contract_seed`, and `rationale_specificity` attributes. Represents the primary node in the knowledge graph.
- **Entity Usage**: A caller→callee relationship with a natural-language description of how the caller uses the callee. Keyed by (callee_id, caller_compound, caller_sig). Carries an embedding for semantic search. Represents a semantic edge in the knowledge graph.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All ~24,803 usage entries from the generated_docs corpus are materialized as queryable rows in the `entity_usages` table after a successful build.
- **SC-002**: The `explain_interface` tool returns a complete five-part contract for entities that have all source fields populated (brief, details, rationale, notes, usages) — covering at minimum the ~2,889 entities with usages data.
- **SC-003**: Semantic search with `source=usages` returns relevant results for domain-specific behavioral queries (e.g., "apply damage," "check immortal status," "send message to character") with the target entity in the top 10 results.
- **SC-004**: All 5,295 documented entities have `doc_state` populated after build, enabling agents to distinguish documentation quality tiers without reading full text.
- **SC-005**: Entities identified as contract seeds (`is_contract_seed = true`) correspond to high-fan-in entities with caller-derived behavioral descriptions — the natural starting points for Wave 1 migration specs.
- **SC-006**: The enriched build completes without requiring any new LLM inference — all new fields are derived from existing artifacts through aggregation, indexing, and heuristic computation.
- **SC-007**: Existing V1 tools (`get_entity`, `search`) continue to function with their current interfaces, gaining the new fields as additive extensions.

## Clarifications

### Session 2026-03-19

- Q: Should usage search results be grouped by entity or returned as individual rows? → A: Grouped by callee entity, top-matching usage descriptions inlined.
- Q: How many usage patterns should `explain_interface` and `include_usages` inline? → A: Top 5, ranked by caller fan-in or relevance.
- Q: Should the build support incremental updates for usage embeddings? → A: Full rebuild only — drop and recreate `entity_usages` each build.

## Assumptions

- The generated_docs artifacts in `artifacts/generated_docs/` are stable and will not change format before this feature is implemented.
- The `usages` dict structure in generated_docs has a consistent parseable format for each caller→callee entry. The exact key format must be verified against the artifacts before implementation.
- The existing `fan_in` value is already computed and available in the entities table at build time (or can be computed from the code graph).
- The `is_contract_seed` fan-in threshold will be determined empirically during implementation and made configurable.
- The `rationale_specificity` heuristic (length + domain-term density) is a v1 approximation; the specific formula will be refined based on corpus analysis.
- FastEmbed (already used by the V1 server) will generate embeddings for usage descriptions using the same model as entity embeddings.
- The existing contract test infrastructure (`tests/`) will be extended to cover the new tool and enhanced responses.
