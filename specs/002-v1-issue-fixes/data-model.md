# Data Model: V1 Known Issue Fixes

**Branch**: `002-v1-issue-fixes` | **Date**: 2026-03-20

No schema changes. The `entities` and `entity_usages` tables are unchanged. This document records the invariants this feature enforces on existing tables and the build-time intermediate structures.

---

## Schema (unchanged)

### `entities` table

| Column | Type | Notes |
|---|---|---|
| `entity_id` | `str` PK | `{prefix}:{sha256(compound_id, second_element)[:7]}` |
| `name` | `str` | Entity name |
| `signature` | `str` | Full C++ signature |
| `fan_in` | `int` | Incoming CALLS edge count |
| `fan_out` | `int` | Outgoing CALLS edge count |
| `is_bridge` | `bool` | Cross-capability bridge flag |
| `is_contract_seed` | `bool` | High fan_in AND rationale present |
| `rationale` | `str \| None` | LLM-generated rationale |
| `doc_state` | `str \| None` | Documentation generation tier |
| ... | | Other enrichment fields |

### `entity_usages` table

| Column | Type | Notes |
|---|---|---|
| `callee_id` | `str` PK (FK → entities) | Entity being described |
| `caller_compound` | `str` PK | Caller's Doxygen compound ID |
| `caller_sig` | `str` PK | Caller function signature |
| `description` | `str` | Behavioral usage description |
| `embedding` | `vector(768) \| None` | Semantic search vector |
| `search_vector` | `tsvector \| None` | Keyword search vector |

---

## Invariants enforced by this feature

### I-001: Entity uniqueness invariant

**Before this fix**: Two rows in `entities` can share the same `(name, signature, file_path)` with different `entity_id` values. One row has `fan_in > 0` and `rationale = None`; the other has `fan_in = 0` and `rationale != None`.

**After this fix**:

> For every logical entity (unique `name` + `signature` + `file_path`), exactly one row exists in `entities`. That row carries both `fan_in` from the code graph AND `rationale` from the documentation pipeline.

Formally:
- `SELECT entity_id FROM entities GROUP BY name, signature, file_path HAVING COUNT(*) > 1` returns zero rows.
- For every `entity_id` that appears as a source or target in the graph edges, a row exists in `entities` with `fan_in` reflecting its actual caller count.
- `is_contract_seed = (fan_in >= threshold AND rationale IS NOT NULL)` is computed from the same row.

### I-002: Search score semantics invariant

**Before this fix**: `score` in search results is query-relative (top result always = 1.0).

**After this fix**:

> `score` in search results is an absolute signal. A nonsense query returns zero results. An exact-name match scores visibly higher than a semantic-only match.

Formally:
- Results with combined score < 0.2 are excluded from the result set (except exact-name matches, which are unconditionally included).
- The keyword contribution to `score` is bounded to `[0, 0.4]` (via intra-query normalization before weight application).
- The semantic contribution is bounded to `[0, 0.6]` (cosine similarity is already `[0, 1]`).
- An exact match adds 10.0, always dominating the combined score.

---

## Build-time intermediate: `MergedEntity`

`MergedEntity` (`build_helpers/entity_processor.py:138`) is the build pipeline's unit of work. It is not persisted; it is consumed by `populate_entities()`.

**Invariant added by this feature**:

> After `merge_entities()` returns, no two `MergedEntity` instances in the list share the same `(name, signature, file_path)` triple. Every instance whose `entity_id` will appear in the code graph has both `fan_in` assignable from graph edges AND `doc` non-null (if documentation exists for that logical entity).

**Surviving compound selection rule**:

1. Load raw GML node IDs into `frozenset[str]` before merge.
2. Group entities by `(name, signature, file_path)`.
3. For each group of size > 1:
   - The entity whose `id.member or id.compound` is in the GML node set is the survivor.
   - If neither: `BuildError` (unresolvable — graph references an unknown compound).
   - If both: keep the entity whose file path is a definition file (`.cc`/`.cpp`); if ambiguous, keep the one with non-null `doc`.
4. Copy `doc` from non-surviving sibling onto survivor if survivor's `doc` is `None`.
5. Log: `log.info("split entity merged", name=..., surviving_compound=..., discarded_compound=...)`.

---

## No changes to runtime graph

The `nx.MultiDiGraph` loaded by the server at startup (`server/graph.py` or similar) is unchanged. The graph's node IDs are compound-based strings; after the build fix, the surviving entity's `entity_id` is already derived from the graph-referenced compound, so runtime traversal (`get_callers`, `get_callees`) resolves to the correct database row without any server-side changes.
