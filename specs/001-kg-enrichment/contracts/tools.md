# Tool Contracts: Knowledge Graph Enrichment (V1)

**Branch**: `001-kg-enrichment`
**Date**: 2026-03-19

## New Tool: `explain_interface`

### Purpose
Returns a five-part behavioral contract for a code entity, composed from existing fields and materialized usage data. Primary tool for spec-creating and auditor agents.

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `entity_id` | str | Yes | — | Entity ID to explain |

### Response: `ExplainInterfaceResponse`

```
entity_id: str
signature: str
name: str
kind: str

signature_block: str | None
  — Full signature: definition_text + argsstring. Null for non-function entities.

mechanism: MechanismSection
  brief: str | None
  details: str | None

contract: ContractSection | None
  rationale: str | None
  — Null section when rationale is null.

preconditions: PreconditionsSection | None
  notes: str | None
  — Null section when notes is null.

calling_patterns: list[CallingPattern]
  caller_compound: str
  caller_sig: str
  description: str
  — Top 5 from entity_usages, ranked by caller fan_in.
  — Empty list when entity has no usages data.

metadata: ContractMetadata
  doc_state: str | None
  is_contract_seed: bool
  rationale_specificity: float | None
  fan_in: int
  fan_out: int
  capability: str | None
```

### Behavior
- Fetches entity row + top 5 entity_usages rows in a single query scope.
- Caller fan_in ranking: join `entity_usages.caller_compound` + `caller_sig` against `entities` to get the caller's `fan_in`, then order descending. If caller is not in entities table, fan_in defaults to 0 (ranked last).
- All sections are present in the response; null-valued sections indicate missing evidence.
- No LLM calls at query time.

---

## Enhanced Tool: `get_entity`

### New Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `include_usages` | bool | No | False | When true, inline top 5 usage patterns |

### New Response Fields (added to `EntityDetail`)

```
doc_state: str | None
notes_length: int | None
is_contract_seed: bool
rationale_specificity: float | None
top_usages: list[UsageEntry] | None
  — Only present when include_usages=true
  — UsageEntry: caller_compound, caller_sig, description
  — Ranked by caller fan_in, top 5
```

### Backward Compatibility
- Existing fields unchanged.
- New fields are additive — clients not expecting them can ignore them.
- `include_usages` defaults to false — existing callers see no behavior change.

---

## Enhanced Tool: `search`

### New Parameter Values

| Parameter | Change |
|-----------|--------|
| `source` | Gains `"usages"` option (existing: `"entity"`) |

### `source="usages"` Behavior

- Hybrid search (semantic + keyword) over `entity_usages` table.
- Semantic: cosine similarity on `entity_usages.embedding`.
- Keyword: `ts_rank` on `entity_usages.search_vector`.
- Scoring: Same weighting pattern as entity search (semantic 0.6, keyword 0.4). No exact-match boost (no name/signature to match).
- Results grouped by `callee_id`: one `SearchResult` per entity, with top-matching usage descriptions inlined.

### New Response Fields (when `source="usages"`)

Each `SearchResult` gains:
```
matching_usages: list[MatchingUsage] | None
  caller_compound: str
  caller_sig: str
  description: str
  score: float
  — Top matches from entity_usages for this callee, sorted by score
```

### Backward Compatibility
- `source="entity"` (default) behavior unchanged.
- `kind` and `capability` filters apply to the callee entity, not the usage row.
