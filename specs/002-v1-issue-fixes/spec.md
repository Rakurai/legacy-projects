# Feature Specification: V1 Known Issue Fixes

**Feature Branch**: `002-v1-issue-fixes`
**Created**: 2026-03-20
**Status**: Draft
**Source**: `mcp/doc_server/specs/v1/issues.md` (post-feedback revision 2026-03-20)

---

## Clarifications

### Session 2026-03-20

- Q: Should "nonsense query returns zero results" (SC-003) be exactly zero or tolerate at most one low-confidence result? → A: Exactly zero. The threshold must be tuned to achieve this; a single garbage result is not acceptable.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Contract Seed Discovery Works for High-Traffic Functions (Priority: P1)

An agent tasked with identifying Wave 1 migration candidates queries the knowledge store for the most-called functions in the codebase. It expects that functions with high caller counts AND documented rationale are surfaced as contract seeds. Currently, the highest-traffic function (`stc`, fan_in=640) is invisible to this workflow because its graph metrics and documentation exist on two separate records that never combine.

After this fix, a search for any high-traffic function returns a single, complete record — one that carries both the caller count and the documentation needed to evaluate migration priority. The contract seed flag is computed from the unified record and is correct.

**Why this priority**: Data corruption. The most important entities for migration planning are systematically misclassified. An auditor agent following the contract-seed workflow would miss every function affected by the declaration/definition split.

**Independent Test**: Can be fully tested by querying the knowledge store for `stc` and verifying it is returned as a single record with both its caller count (640) and its rationale present, and that it is flagged as a contract seed.

**Acceptance Scenarios**:

1. **Given** the knowledge store has been rebuilt, **When** an agent retrieves the entity for `stc`, **Then** it receives exactly one record with fan_in=640, non-null rationale, and is_contract_seed=true.
2. **Given** the knowledge store has been rebuilt, **When** an agent searches for "damage" by name, **Then** it receives one result — not two near-identical results — with both caller count and documentation present.
3. **Given** the knowledge store has been rebuilt, **When** an agent counts all logical entities, **Then** the count is lower than the pre-fix count, reflecting the removal of duplicate declaration/definition pairs.

---

### User Story 2 — Graph Traversal Yields Complete Interface Documentation (Priority: P1)

An agent navigating the call graph follows a path: identify a callee entity, retrieve its callers, then call `explain_interface` to understand the calling patterns. Currently this workflow silently returns empty calling patterns because graph traversal lands on the half of a split entity that has metrics but no documentation. The agent sees zero calling patterns and cannot determine how the function is actually used.

After this fix, any entity reachable via graph traversal carries complete documentation. The entity identifier in the graph and the entity identifier in the documentation store resolve to the same record.

**Why this priority**: Silent failure. The graph traversal → explain_interface workflow is a primary agent navigation pattern. Empty calling patterns produce no error — the agent simply receives no useful information and may conclude the function has no documented callers.

**Independent Test**: Can be fully tested by traversing the graph to a high-fan_in entity (e.g., `stc` or `damage`), calling `explain_interface`, and verifying that calling_patterns is non-empty.

**Acceptance Scenarios**:

1. **Given** an agent retrieves callers of `stc` via graph traversal, **When** it calls `explain_interface` on the returned entity identifier, **Then** calling_patterns is non-empty and contains behavioral descriptions of how callers use the function.
2. **Given** an agent follows any graph edge to a function with fan_in > 20, **When** it calls `explain_interface` on the destination entity, **Then** calling_patterns reflects the documented usage patterns for that function.

---

### User Story 3 — Search Does Not Return Noise Results for Weak Queries (Priority: P2)

An agent issuing a vague or nonsense query currently receives results that look identical in score to a perfect match — the top result always scores 1.0 regardless of actual relevance. An agent cannot distinguish "perfect match" from "least bad result." Noise results consume context window and require the agent to reason about irrelevance rather than relevance.

After this fix, queries with no meaningful matches return zero results. Queries with genuine matches return those results. The agent no longer needs to evaluate and discard irrelevant results.

**Why this priority**: Agent efficiency. The failure is not catastrophic — agents can still identify irrelevance from content — but it forces unnecessary reasoning and wastes context window on every weak query.

**Independent Test**: Can be fully tested by issuing a nonsense query and verifying it returns zero results, then issuing an exact-name query and verifying it returns the target entity.

**Acceptance Scenarios**:

1. **Given** an agent issues a query with no plausible match in the corpus, **When** results are returned, **Then** zero results are returned — not a full result set with high-looking scores.
2. **Given** an agent issues an exact function-name query, **When** results are returned, **Then** the matching entity appears first, and its score is visibly distinguishable from any weaker matches.
3. **Given** an agent issues a behavioral description query for a known high-traffic function, **When** results are returned, **Then** the correct entity appears in the result set.

---

### Edge Cases

- What if a function exists only as a declaration (header-only, no definition in the code graph)? The entity must still be represented in the knowledge store — it must not be silently dropped.
- What if both the declaration and the definition compound appear as nodes in the code graph? The merge logic must deterministically choose one (the definition).
- What if the noise threshold excludes a genuinely relevant result for an unusual query? Exact-name matches must always be returned regardless of combined score.
- What if an entity has been fragmented into more than two records (e.g., multiple forward declarations)? All fragments must be collapsed into one surviving record.

---

## Requirements *(mandatory)*

### Functional Requirements

#### Entity Integrity (I-001)

- **FR-001**: The knowledge store MUST contain at most one record per logical entity, where a logical entity is uniquely identified by the combination of its name, signature, and source file path.
- **FR-002**: Each entity record MUST carry both its graph metrics (caller count, callee count, bridge status) and its documentation fields (rationale, usage descriptions, documentation state) on the same record.
- **FR-003**: The entity identifier used in the knowledge store MUST be the same identifier used in the code graph, so that graph traversal and knowledge store lookup resolve to the same record without an additional mapping step.
- **FR-004**: The contract seed flag for each entity MUST be computed from the unified record that contains both graph metrics and documentation — not from a fragment that carries only one.
- **FR-005**: The build process MUST log the count of declaration/definition pairs that were unified during the merge phase, for observability.

#### Search Quality — Noise Filtering (I-002)

- **FR-006**: The keyword search component MUST have its scores normalized within the query's result set before being combined with semantic scores, so that the keyword contribution is bounded and the combined score is predictable.
- **FR-007**: Search MUST NOT apply per-query score normalization. The score returned for a result MUST reflect absolute match quality, not rank within the current result set.
- **FR-008**: Results with combined scores below a minimum relevance threshold MUST be excluded from the returned result set. For entity search, exact-name matches MUST be returned unconditionally regardless of combined score (exact-name boost always places these well above any threshold). For usage search, the threshold applies uniformly — there is no exact-name carve-out because usage search has no name-match boost.
- **FR-009**: The search endpoint MUST return the raw combined score. Score ordering determines result ranking; score value signals match strength.

#### Regression Verification (I-004)

- **FR-010**: After rebuild, the entity for `stc` (fan_in=640) MUST have is_contract_seed=true, non-null rationale, and populated calling_patterns when retrieved via `explain_interface`.

### Key Entities

- **Logical Entity**: A distinct function, type, or variable in the codebase, uniquely identified by its name, signature, and source file. After this fix, each logical entity corresponds to exactly one knowledge store record.
- **Entity Fragment**: Either half of a declaration/definition pair before unification. Fragments carry either graph metrics or documentation, but not both. Fragments are a build-time intermediate artifact and must not appear in the final knowledge store.
- **Graph-Referenced Compound**: The compiler-generated description of an entity whose identifier appears as a node in the code graph. This compound is the canonical identity for a logical entity and is the record retained after a declaration/definition merge.
- **Usage Description**: A behavioral description of how a specific parameter or caller argument is used within a function.
- **Contract Seed**: An entity flagged as a high-value migration candidate based on its caller count and the presence of documented rationale. Requires a unified entity record to be computed correctly.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: After rebuild, the knowledge store entity count is lower than the pre-fix count by at least the number of confirmed declaration/definition pairs (verified by the merge log produced per FR-005).
- **SC-002**: The entity `stc` is returned as a single record with fan_in=640, is_contract_seed=true, and non-empty calling_patterns via `explain_interface` — verifying that the highest-traffic function in the codebase is correctly indexed.
- **SC-003**: A nonsense query (no plausible match in the corpus) returns zero results.
- **SC-004**: An exact-name query for `stc` returns the target entity as the first result.
- **SC-005**: All existing contract tests pass without modification after the rebuild and search changes are applied.
- **SC-006**: The build process completes without errors and emits the entity merge count log (FR-005).

---

## Assumptions

- The code graph is the authority for determining which compound is the canonical half of a declaration/definition pair. If neither compound appears in the graph, this is an error condition — the build process must raise explicitly rather than silently pick one.
- A pair of entity records is a declaration/definition split if and only if they share identical name, signature, and source file path. No other deduplication criterion is applied.
- The minimum relevance threshold for noise filtering (FR-008) is tuned to pass SC-003 and SC-004 before being committed. The approximate value is 0.2 combined score, based on the semantic similarity floor for genuine matches, but this is validated empirically against the known query set.
- Score changes affect only score values, not ranking order. Agent workflows that read result content (names, signatures, briefs) rather than score values are unaffected.
- The full regression test suite (`specs/001-kg-enrichment/full-test.md`, 37 tests) passes after all changes are applied.
