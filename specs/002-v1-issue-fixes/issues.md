# V1 Known Issues

**Date**: 2026-03-19
**Updated**: 2026-03-20 (post-feedback revision)
**Source**: Full usability test of 001-kg-enrichment (see `specs/001-kg-enrichment/full-test.md`)
**Feedback**: `issues-feedback.gpt.md`, `issues-feedback.claude.md`, `issues-feedback.summary.md`

---

## I-001: Split entities — declaration and definition stored as separate rows (HIGH)

### Problem

Many C++ entities exist as two separate database rows with different `entity_id` values but identical name, signature, and file path. One row carries the code graph metrics (`fan_in`, `fan_out`, `is_bridge`) while the other carries the generated_docs content (`usages`, `rationale`, `notes`, `doc_state="refined_summary"`).

### Examples

| Function | Entity with graph metrics | fan_in | Entity with doc content | Usages |
|----------|--------------------------|--------|------------------------|--------|
| `damage` | `fn:7858ec6` | 49 | `fn:51a4e7a` | 45 callers |
| `stc` | `fn:4b7e3b7` | 640 | `fn:d275dc8` | ~100+ callers |
| `interpret` | `fn:cb00ae1` | 9 | `fn:e1593b9` | unknown |

### Root cause

Doxygen generates separate compounds for declarations (header `.hh` files) and definitions (source `.cc` files). The build pipeline's signature map creates two distinct canonical keys from the different `compound_id` values, producing two entity IDs. The code graph (`.gml`) edges reference one compound while the generated_docs records reference the other.

The entity ID formula `{prefix}:{sha256(compound_id, signature)[:7]}` is deterministic per compound, so the two compounds produce two stable but distinct IDs.

### Impact

1. **`is_contract_seed` is systematically wrong for split entities.** The entity with real `fan_in` lacks `rationale` (→ false), and the entity with `rationale` has `fan_in=0` (→ false). Neither gets flagged even though the combined data would qualify. Example: `stc` has fan_in=640 and rationale present — across two rows.

2. **`explain_interface` returns empty `calling_patterns` on the graph-reachable entity.** An agent following graph traversal (`get_callers` → caller entity_id → `explain_interface`) arrives at the entity with fan_in but no usages, getting empty calling_patterns. The entity with usages is unreachable via the graph.

3. **Usage search returns the low-fan_in entity.** `search source="usages"` returns the entity that has usage rows (fan_in=0). An agent then calling `get_callers` on that entity_id finds no graph neighbors.

4. **Search returns both entities for the same function.** A search for "damage" returns `fn:7858ec6` (score 1.0) and `fn:51a4e7a` (score 0.9997) as separate results. Agents must guess which is the "real" one.

5. **Effective entity count is inflated.** The ~5,305 entity count includes both halves of every split pair. The true logical entity count is lower.

### Where to fix

**Build pipeline only.** The merge should happen at build time, in the entity processing phase that produces rows for the database. The code graph (`code_graph.gml`) is loaded into a NetworkX `MultiDiGraph` at build time for metric computation AND at server startup for runtime traversal — but the graph itself doesn't need to change. The graph's node IDs are compound-based strings; once the build pipeline resolves which compound "wins" for a given `(name, signature, file_path)` triple and merges doc content onto it, the surviving entity_id will already be the one the graph references. The other compound's entity row is simply not emitted.

The graph must be loaded *before* the merge phase (currently loaded after) so graph node IDs are available to determine the surviving compound. This is a pipeline reordering change, not a graph format change.

Entity merge must happen before capability assignment and bridge computation to maintain existing pipeline ordering dependencies (FR-059).

### Direction

During the build pipeline's merge phase, detect when two compounds resolve to the same `(name, signature, file_path)` triple. Unify them into a single entity row: keep the compound_id that the code graph references (so entity_id remains graph-addressable), and copy doc fields (`usages`, `rationale`, `notes`, `doc_state`, etc.) from the other compound onto it.

---

## I-002: Low-quality usage descriptions pollute search results (DEFERRED → reranking.md)

### Problem

The LLM that generated usage descriptions sometimes produced entries for parameters that aren't meaningfully "used" — just passed through or present in a signature. Examples: "Not used directly in this function," "Not directly used within the function body," "the argument is of type String but only checked for emptiness."

### Why deferred

A build-time pattern filter ("not used", "not directly used", etc.) is fragile: it risks over-filtering mixed descriptions and under-filtering novel phrasings. Low-quality usage descriptions are better addressed within the reranking pipeline's pre-rerank filtering stage, where weak-evidence candidates can be demoted without a brittle keyword list. See `reranking.md` → **Deferred issues: I-003**.

---

## I-003: `stc` (fan_in=640) has `is_contract_seed=false` (MEDIUM)

### Problem

This is a specific manifestation of I-001. `fn:4b7e3b7` (`stc`, the most-called function in the codebase with fan_in=640) has `is_contract_seed=false` because its rationale is null. The rationale exists on the sibling entity `fn:d275dc8` (fan_in=0).

Expected to resolve automatically when I-001 (entity merging) is implemented. Retained as a named test case to verify the fix.

### Verification

After I-001 fix, confirm:
- `stc` entity has both `fan_in=640` and non-null `rationale` → `is_contract_seed=true`
- `explain_interface` for stc returns populated `calling_patterns`
- `search source="usages"` for "send text to character" returns stc with `fan_in=640`

### Impact

The highest-traffic function in the entire codebase — the primary output mechanism — is invisible to any workflow that starts from contract seeds. An auditor agent using `is_contract_seed` to find Wave 1 migration candidates would miss it entirely.

---

## Deferred: Search score calibration

Per-query score normalization makes all top scores 1.0, preventing score-based noise filtering. This issue and the broader search scoring discussion (keyword normalization, threshold-based filtering, agent context window efficiency) are tracked separately in `reranking.md`.
