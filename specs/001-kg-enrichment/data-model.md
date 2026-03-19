# Data Model: Knowledge Graph Enrichment (V1)

**Branch**: `001-kg-enrichment`
**Date**: 2026-03-19

## Entity Changes (enriched columns)

### New Columns on `entities` Table

| Column | Type | Nullable | Default | Source |
|--------|------|----------|---------|--------|
| `doc_state` | TEXT | Yes | None | `state` field from generated_docs entry |
| `notes_length` | INT | Yes | None | `len(entity.notes)` if notes is non-null |
| `is_contract_seed` | BOOLEAN | No | False | `fan_in > threshold AND rationale IS NOT NULL` |
| `rationale_specificity` | REAL | Yes | None | Heuristic: text length + domain-term density |

### Validation Rules

- `doc_state`: One of `refined_summary`, `generated_summary`, `extracted_summary`, `refined_usage`, or null (for entities without generated docs).
- `notes_length`: Null when `notes` is null; non-negative integer otherwise.
- `is_contract_seed`: Derived at build time. Threshold is configurable (build parameter, not runtime).
- `rationale_specificity`: Null when `rationale` is null; non-negative float otherwise. Formula TBD during implementation — initial heuristic is `len(rationale) * domain_term_ratio`.

## New Entity: EntityUsage

Materializes the `usages` JSONB dict into individual queryable rows with embeddings.

### Table: `entity_usages`

| Column | Type | Nullable | Notes |
|--------|------|----------|-------|
| `callee_id` | TEXT | No | FK → `entities.entity_id`. The entity being used. |
| `caller_compound` | TEXT | No | Compound ID of the calling context (e.g., `fight_8cc`). |
| `caller_sig` | TEXT | No | Signature of the calling function. |
| `description` | TEXT | No | Natural-language description of how caller uses callee. |
| `embedding` | VECTOR(768) | Yes | Embedding of `description` text. |
| `search_vector` | TSVECTOR | Yes | Full-text search vector over `description`. |

**Primary Key**: `(callee_id, caller_compound, caller_sig)`

**Indexes**:
- `idx_entity_usages_callee` on `callee_id` — supports "all callers of entity X"
- `idx_entity_usages_caller` on `(caller_compound, caller_sig)` — supports "all callees used by function Y"
- `idx_entity_usages_embedding` HNSW on `embedding` (vector_cosine_ops) — semantic search
- `idx_entity_usages_search` GIN on `search_vector` — full-text search

### Relationships

- `entity_usages.callee_id` → `entities.entity_id` (many-to-one: many usage rows per callee entity)
- Caller identity is textual (compound + sig), not a foreign key — callers may reference entities not in the entities table (e.g., functions from files not parsed by Doxygen)

### Key Format Parsing

Source usages dict key: `"{compound_id}, {caller_signature}"` → split on first `", "`.

Example:
- Key: `"fight_8cc, void damage(Character *ch, Character *victim, int dam, int dt, int dam_type)"`
- Parsed: `caller_compound = "fight_8cc"`, `caller_sig = "void damage(Character *ch, Character *victim, int dam, int dt, int dam_type)"`

### Scale

- ~2,889 entities have usages data
- ~24,803 total usage entries
- Average ~8.6 usage entries per entity with usages
- Each row gets a 768-dimension embedding vector

### Lifecycle

- Dropped and fully recreated on each build (no incremental updates)
- Embeddings computed fresh each build via `LocalEmbeddingProvider`

## Existing Entity Changes (no new tables)

The existing `usages` JSONB column on `entities` remains unchanged for backward compatibility. Tools that currently return the raw usages dict continue to work. The `entity_usages` table is an additive materialization, not a replacement.
