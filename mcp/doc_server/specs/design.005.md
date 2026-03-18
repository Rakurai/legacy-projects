# Design 005: Deterministic Entity IDs & Documentation Merge Fix

**Status**: Accepted
**Date**: 2026-03-17
**Scope**: Build pipeline, schema, tool interfaces

---

## Problem

Two related issues block V1 release:

1. **Missing documentation.** Only ~330 of 5,293 entities retain their briefs after
   the build pipeline. The root cause is a stale `signature_map.json` — built from
   old Doxygen member hashes that no longer match the current `code_graph.json`.
   The merge logic itself is correct (iterates code_graph entities, looks up docs
   via signature_map), but when signature_map references stale member hashes, most
   lookups fail silently. Regenerating `signature_map.json` from current artifacts
   recovers ~85% of matches; the remaining ~15% are genuinely stale doc_db entries
   whose signatures no longer match (source code changed since docs were generated).

2. **Non-deterministic, ambiguous identity.** Entity IDs are Doxygen-internal
   compound+member hashes, opaque and non-deterministic across Doxygen runs. Tools
   accept both `entity_id` and `signature` interchangeably, but 521 signatures are
   shared by multiple entities. This conflation produces silent wrong-entity bugs
   when agents accumulate and pass references between tool calls.

---

## Decisions

### 1. Deterministic ID scheme

Every asset in the system receives a deterministic, type-prefixed, content-hashed
ID. The ID is computed from a **canonical key** — a tuple of identity-defining
properties for that asset type — passed through a truncated SHA-256.

**Format**: `{prefix}:{7 hex chars}`

7 hex characters = 28 bits. Collision probability at 10K assets: negligible. The
build script halts on collision (enforced by database UNIQUE constraint on PK
insert).

**Prefix table:**

| Prefix | Asset type | Canonical key (hash input) |
|--------|-----------|---------------------------|
| `fn` | function, define | doc_db key: `(compound_id, signature)` |
| `var` | variable | doc_db key: `(compound_id, name)` |
| `cls` | class, struct | doc_db key: `(compound_id, name)` |
| `sym` | enum, typedef, namespace, group, other | doc_db key: `(compound_id, name)` |
| `file` | source file | doc_db key: `(compound_id, filename)` |
| `doc` | subsystem document chunk (V2) | `source_file \0 section_path` |
| `help` | in-game help entry (V3) | `topic_name` |
| `bg` | builder guide section (V3+) | `url_path \0 section_anchor` |

For V1 code entities, the hash input is the **doc_db key** — the string-serialized
tuple `(compound_id, second_element)` that is already the primary key in both
`doc_db.json` and `signature_map.json`. This key is stable across Doxygen runs
because `compound_id` is derived from the C++ qualified name, and the second element
is the entity's signature (for functions) or name (for other kinds).

The prefix is determined by the entity's `kind` field:
- `function`, `define` → `fn`
- `variable` → `var`
- `class`, `struct` → `cls`
- `file` → `file`
- everything else (`enum`, `typedef`, `namespace`, `group`, etc.) → `sym`

**Examples**: `fn:a3f8c1d`, `var:91e2b3c`, `cls:c7d8e9f`, `file:2b3c4d5`

### 2. Single-source entity merge using doc_db key

The doc_db key `(compound_id, second_element)` is the authoritative identity for
all V1 entities. It appears as:
- The key in `doc_db.json` (5,293 entries with documentation)
- The key in `signature_map.json` (5,305 entries bridging to Doxygen member IDs)

The build pipeline must use this key as the single join key for merging entity
metadata, documentation, and graph data. The current pipeline's documentation loss
is caused by a stale `signature_map.json` — the fix is to ensure signature_map is
regenerated from current `code_graph.json` + `doc_db.json` before each build, and
to use the doc_db key (not the Doxygen member ID) as the primary identity
throughout the pipeline.

The Doxygen compound+member IDs (`mid` values from `signature_map.json`) are used
only for:
- Matching `code_graph.json` nodes to their doc_db entries during the merge
- Matching `code_graph.gml` edges to entities (since the GML uses Doxygen IDs)

After the merge, Doxygen IDs are discarded and the deterministic ID computed from
the doc_db key becomes the entity's permanent identity.

### 3. Signature is display-only, not a lookup key

The `signature` column remains in the schema as a human-readable display string.
It is returned in `EntitySummary` and `EntityDetail` for readability. It is never
accepted as a tool parameter for entity lookup. After resolution via `search`, all
tool calls use `entity_id` exclusively.

### 4. Retire `resolve_entity` tool

With deterministic IDs and signature removed as a lookup key, the two runtime
operations are:
- **Lookup**: agent has an ID → `get_entity(entity_id)` — one result
- **Search**: agent has a concept/name → `search(query)` — ranked array with IDs

The multi-stage resolution pipeline (name_exact → prefix → keyword → semantic)
remains as the internal implementation of `search`. `resolve_entity` is retired as
a separate tool. `ResolutionEnvelope` is removed from all response shapes — no tool
performs implicit resolution.

### 5. Remove `doc_quality` and `doc_state`

Quality assessment belongs to the artifact creation chain, not the server or agent.
An agent cannot meaningfully act on a "medium" quality signal — any document below
highest quality becomes untrusted, making the tiering useless.

Drop from schema: `doc_quality`, `doc_state`.
Drop from models: `EntitySummary.doc_quality`, `EntitySummary.doc_state`,
`EntityDetail.doc_quality`, `EntityDetail.doc_state`.
Drop from tools: `min_doc_quality` filter on `search`, `doc_quality_dist` on
capabilities.

The agent's practical signal is whether `brief` is null or not.

### 6. Remove Doxygen internal fields from schema

`compound_id` and `member_id` are build-time join keys with no runtime purpose.
Remove from the `entities` table and from `EntityDetail`.

### 7. Fix `list_entry_points` capability filter

The query must filter on `entry_points.capabilities` (JSONB array of capability
names the entry point exercises), not `entities.capability` (the group membership
column, correctly NULL for entry points). Same fix for `get_capability_detail`
entry_points population.

---

## Schema Changes

**Entities table — drop columns:**
- `compound_id`
- `member_id`
- `doc_state`
- `doc_quality`

**Entities table — change:**
- `entity_id` values change from Doxygen IDs to `{prefix}:{7 hex}` format
- `signature` remains as a display-only column (NOT unique — 521 signatures collide across compounds; no UNIQUE constraint)

**Capabilities table — drop column:**
- `doc_quality_dist`

**No new tables.** The entry_points table already has the correct `capabilities`
JSONB column.

---

## Tool Interface Changes

**All tools accepting `entity_id?: string, signature?: string`:**
- Accept only `entity_id: string` (required, not optional)
- Remove `signature` parameter

**Remove tools:**
- `resolve_entity`

**Remove from all response shapes:**
- `ResolutionEnvelope` / `resolution` field

**Remove from `EntitySummary`:**
- `doc_state`
- `doc_quality`

**Remove from `EntityDetail`:**
- `compound_id`
- `member_id`
- `doc_state`
- `doc_quality`

**Remove from `search` parameters:**
- `min_doc_quality`

**Remove from `list_capabilities` / `get_capability_detail` responses:**
- `doc_quality_dist`

**Fix `list_entry_points`:**
- Filter on `entry_points.capabilities` JSONB, not `entities.capability`

**Fix `get_capability_detail`:**
- Populate `entry_points` from `entry_points` table where capability name appears
  in the JSONB `capabilities` array

---

## Build Pipeline Changes

The build script must be restructured so that the doc_db key is the primary
identity throughout the pipeline. The general flow:

1. Load `doc_db.json` — each entry keyed by `(compound_id, second_element)` with
   documentation fields (brief, details, params, etc.)
2. Load `signature_map.json` — maps doc_db keys to Doxygen member IDs (`mid`)
3. Load `code_graph.json` — entity metadata (kind, file, body, definition, etc.)
   keyed by Doxygen compound+member ID
4. Match `code_graph.json` entities to doc_db entries using `signature_map.json`
   as the bridge (Doxygen ID → doc_db key)
5. For entities in `code_graph.json` without a doc_db match, create entries with
   null documentation
6. Compute deterministic ID from doc_db key: `{prefix}:{sha256(key)[:7]}`
7. Replace all Doxygen IDs with deterministic IDs
8. Load `code_graph.gml` edges — translate Doxygen node IDs to deterministic IDs
   using the mapping built in step 4
9. Continue with remaining pipeline steps (source extraction, capability assignment,
   metrics, embeddings, etc.) using deterministic IDs throughout

All three input artifacts (`code_graph.json`, `doc_db.json`, `signature_map.json`)
are pre-built and locked before the build pipeline runs. The pipeline loads them
as read-only inputs — it does not regenerate them. `code_graph.json` is the
canonical entity set, `doc_db.json` provides documentation, and
`signature_map.json` bridges them via stable `(compound_id, signature)` keys.

**Phantom references**: When translating GML edge endpoints to deterministic IDs
(step 8), ~506 referenced entity IDs in `code_graph.json` don't appear as
entities. These are `enumvalue` IDs (~479) and `friend` memberdefs (~27) — they
are expected and should be silently skipped. See `artifacts/artifacts.md` §5.

---

## ID Scheme — Forward Compatibility

The prefix+hash scheme extends to V2 and V3 asset types:

- **V2 subsystem doc chunks** (`doc:` prefix): chunked sections from
  `components/*.md`, keyed by `source_file + section_path`
- **V3 help entries** (`help:` prefix): in-game help topics, keyed by `topic_name`
- **V3+ builder guide sections** (`bg:` prefix): HTML section chunks, keyed by
  `url_path + section_anchor`

All share the same format, the same UNIQUE constraint, and the same "agent
accumulates IDs and passes them forward" interaction pattern. No existing IDs
change when new asset types are added.

---

## Invariants

- Every entity in the database has a deterministic ID computed from its doc_db key
- The same source artifacts produce the same IDs on every build
- No two entities share an ID (enforced by PK constraint; build halts on collision)
- Agents receive IDs in every response and use them for all follow-up calls
- No tool accepts a signature or name as an entity lookup parameter
- `search` is the sole path from human-readable text to entity IDs
