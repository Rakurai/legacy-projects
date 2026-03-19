# Research: Knowledge Graph Enrichment (V1)

**Date**: 2026-03-19
**Branch**: `001-kg-enrichment`

## R1: Usages Dict Format

**Decision**: Keys are flat strings formatted as `"{compound_id}, {caller_signature}"` → plain string description. Not nested dicts.

**Rationale**: Verified against actual artifacts (`artifacts/generated_docs/wiz__gen_8cc.json`, `_affect_8hh.json`). The spec assumption about nested `compound`, `sig`, `description` fields was incorrect — already corrected in spec to "consistent parseable format, verify before implementation."

**Parsing strategy**: Split key on first `", "` to extract `(caller_compound, caller_sig)`. The callee identity comes from the parent entity, not the usages dict itself.

**Alternatives considered**: None — this is an observed fact, not a design choice.

## R2: Doc State Values

**Decision**: The `state` field has at least four values: `refined_summary`, `generated_summary`, `extracted_summary`, `refined_usage`. The proposal only mentioned three.

**Rationale**: Corpus survey found `refined_usage` in entries like `mobiles_8cc.json`. The build pipeline should carry all values through without filtering — they're all valid trust signals.

**Alternatives considered**: Mapping to a reduced set (e.g., collapsing `refined_usage` into `refined_summary`). Rejected — preserving the original value is lossless and more informative.

## R3: `get_hotspots` Tool — Removed

`get_hotspots` was removed from the MCP server in a prior round of changes. The KG proposal's references to it were not updated. FR-011 (notes_length as hotspot signal) has been dropped. `notes_length` remains as an entity-level column for direct querying and filtering.

## R4: Entity Table Schema — Current vs. Needed

**Decision**: Four new columns on `entities` table, one new table.

**Current columns** (26 total): `entity_id`, `name`, `signature`, `kind`, `entity_type`, `file_path`, `body_start_line`, `body_end_line`, `decl_file_path`, `decl_line`, `definition_text`, `source_text`, `brief`, `details`, `params`, `returns`, `notes`, `rationale`, `usages`, `capability`, `is_entry_point`, `fan_in`, `fan_out`, `is_bridge`, `embedding`, `search_vector`.

**New columns**: `doc_state TEXT`, `notes_length INT`, `is_contract_seed BOOLEAN`, `rationale_specificity REAL`.

**New table**: `entity_usages` (~24,803 rows) with `callee_id`, `caller_compound`, `caller_sig`, `description`, `embedding`.

**Rationale**: `usages` is already stored as JSONB on the entity row. The `entity_usages` table materializes it as individual rows for embedding-based search and structured querying. The JSONB column can remain for backward compatibility (existing tools return it).

## R5: Embedding Infrastructure

**Decision**: Reuse existing `LocalEmbeddingProvider` with `BAAI/bge-base-en-v1.5` (768 dimensions) for usage description embeddings.

**Rationale**: Same model, same infrastructure. Usage descriptions are natural-language text similar to entity briefs — no reason to use a different model. FastEmbed handles batching locally.

**Alternatives considered**: Hosted embedding provider for faster throughput. Rejected — local provider avoids external dependency and is already proven for the entity embedding pipeline.

## R6: Hybrid Search Extension Pattern

**Decision**: Extend existing `hybrid_search()` in `server/search.py` to support `source="usages"` mode.

**Rationale**: Current search uses 3-strategy merge (exact match 10x, semantic 0.6, keyword 0.4). The usages search needs semantic + keyword over the `entity_usages` table instead of `entities`. Exact match boost doesn't apply (no name/signature to match). Results need post-grouping by `callee_id`.

**Implementation approach**: Add a parallel search path in `hybrid_search()` keyed on `source` parameter. For `source="usages"`: semantic search over `entity_usages.embedding`, keyword search over `entity_usages.description` (needs tsvector column), then group results by `callee_id` and return top-matching descriptions per entity.

**Alternatives considered**: Separate search function. Rejected — the existing search infrastructure handles degradation, scoring, and filtering; extending it is less code and more consistent.

## R7: `explain_interface` Composition

**Decision**: `explain_interface` is a tool that composes existing entity fields + `entity_usages` query, not an LLM call.

**Rationale**: All five contract parts map to existing data:
1. **Signature**: `entity.signature` + `entity.definition_text`
2. **Mechanism**: `entity.brief` + `entity.details`
3. **Contract**: `entity.rationale`
4. **Preconditions**: `entity.notes`
5. **Calling patterns**: Top 5 from `entity_usages` table, ranked by caller `fan_in`

The tool joins entity data with a `entity_usages` query (top 5 by caller fan-in). No LLM needed.

**Alternatives considered**: Making this a prompt rather than a tool. Rejected — the five-part composition requires a server-side join (entity row + usages query + caller fan-in ranking). An agent cannot replicate this without N+1 queries.

## R8: Test Fixture Extension

**Decision**: Extend existing `conftest.py` fixtures with `sample_entity_usages` and update `sample_entities` with new columns.

**Rationale**: Current test infrastructure uses 7 sample entities, 5 edges, mock context. The `damage` entity (index 0) already has `fan_in=23` and full docs — ideal for `is_contract_seed` and `explain_interface` testing. Add 3-5 `EntityUsage` rows for `damage` to test usage search and top-5 ranking.

**Alternatives considered**: Separate test file for new tools. Rejected — existing pattern is one test file per tool module; new tools get new test files, enhanced tools get additions to existing test files.
