# Search Tool Response Contract

**Phase 1 output** | **Date**: 2026-03-21

This document defines the contract for the `search` MCP tool's response shape. The search tool is the primary interface used by AI agents to discover entities in the legacy codebase.

---

## Tool Signature (unchanged)

```
search(
    query: str,                    # Natural language or identifier query
    source: "entity" | "usages",   # Default: "entity"
    kind: str | None,              # Optional kind filter
    capability: str | None,        # Optional capability filter
    top_k: int,                    # 1–100, default 10
) → SearchResponse
```

**No parameter changes** — the external interface is backward-compatible (FR-060).

---

## SearchResponse

```json
{
  "results": [ ...SearchResult ],
  "query": "send formatted text to character",
  "result_count": 7
}
```

### Fields

| Field | Type | Description | Change |
|-------|------|-------------|--------|
| `results` | `list[SearchResult]` | Ranked results | Type unchanged |
| `query` | `str` | Echo of input query | Unchanged |
| `result_count` | `int` | Length of results list | Unchanged |
| ~~`search_mode`~~ | ~~`SearchMode`~~ | ~~Search strategy used~~ | **REMOVED** (FR-070) |

---

## SearchResult

```json
{
  "result_type": "entity",
  "score": 0.847,
  "winning_view": "doc",
  "winning_score": 0.847,
  "losing_score": 0.412,
  "entity_summary": { ... },
  "matching_usages": null
}
```

### Fields

| Field | Type | Required | Description | Change |
|-------|------|----------|-------------|--------|
| `result_type` | `str` | Yes | `"entity"` in V1 | Unchanged |
| `score` | `float` | Yes | Cross-encoder score from winning view; raw logit may be negative | **Semantic change**: was weighted combo, now CE logit |
| `winning_view` | `"symbol" \| "doc"` | Yes | Which view produced the higher CE score | **NEW** (FR-040, FR-061) |
| `winning_score` | `float` | Yes | Cross-encoder score from winning view; raw logit may be negative | **NEW** (FR-040, FR-061) |
| `losing_score` | `float` | Yes | Cross-encoder score from losing view; raw logit may be negative | **NEW** (FR-040, FR-061) |
| `entity_summary` | `EntitySummary \| null` | Conditional | Present when `result_type="entity"` | Unchanged |
| `matching_usages` | `list[MatchingUsage] \| null` | Conditional | Present when `source="usages"` | Unchanged |
| ~~`search_mode`~~ | ~~`SearchMode`~~ | — | ~~Strategy used~~ | **REMOVED** (FR-070) |

### Score Semantics

- **V1 (current)**: `score` is a weighted combination: `10.0 * exact + 0.6 * semantic + 0.4 * keyword`. Exact matches score ≥ 10.0. Semantic/keyword scores are per-query normalized (top = 1.0).
- **V2 (target)**: `score` equals `max(symbol_ce_score, doc_ce_score)` — a raw cross-encoder logit. Higher = more relevant. **Not bounded to [0, 1]** (raw logits can be negative for irrelevant pairs). No per-query normalization (FR-041). `score == winning_score` always.

### winning_view Semantics

The `winning_view` field tells the agent *why* this result was ranked highly:
- `"symbol"` — the query matched the entity's code signature/name (useful for "I searched for a function name")
- `"doc"` — the query matched the entity's documentation prose (useful for "I searched by behavior/concept")

This replaces the old `search_mode` field, which indicated server capability, not result provenance.

---

## EntitySummary (unchanged)

```json
{
  "entity_id": "fn:a3f8c1d",
  "name": "stc",
  "signature": "void Logging::stc(const String &msg, Character *ch)",
  "kind": "function",
  "entity_type": "member",
  "file_path": "src/stc.cc",
  "brief": "Send a message to a character with color codes",
  "capability": "networking",
  "fan_in": 42,
  "fan_out": 3,
  "is_bridge": true,
  "is_entry_point": false
}
```

No changes to `EntitySummary` fields.

---

## MatchingUsage (unchanged)

```json
{
  "caller_compound": "class_character",
  "caller_sig": "void do_look(Character*, char*)",
  "description": "Calls stc to display room description to the character",
  "score": 0.82
}
```

No changes to `MatchingUsage` fields. Note: for `source="usages"`, the `winning_view`/`winning_score`/`losing_score` on the parent `SearchResult` reflect the *entity search* reranking, not the usage search. Usage search is out of scope (FR-062, A-009).

---

## Breaking Changes Summary

| Change | Impact | Migration |
|--------|--------|-----------|
| `search_mode` removed from `SearchResponse` | Agents parsing `search_mode` will break | Remove field references; there is only one mode |
| `search_mode` removed from `SearchResult` | Agents parsing per-result `search_mode` will break | Use `winning_view` for result provenance |
| `score` semantics changed | Agents comparing scores to fixed thresholds (e.g., `> 0.5`) may need adjustment | Cross-encoder logits have different scale |
| Three new fields on `SearchResult` | Additive — no breakage | No action needed |

---

## Example Responses

### Symbol Query: `"stc"`

```json
{
  "results": [
    {
      "result_type": "entity",
      "score": 8.41,
      "winning_view": "symbol",
      "winning_score": 8.41,
      "losing_score": 2.13,
      "entity_summary": {
        "entity_id": "fn:a3f8c1d",
        "name": "stc",
        "signature": "void Logging::stc(const String&, Character*)",
        "kind": "function",
        "brief": "Send a message to a character with color codes"
      }
    },
    {
      "result_type": "entity",
      "score": 5.67,
      "winning_view": "symbol",
      "winning_score": 5.67,
      "losing_score": 1.02,
      "entity_summary": {
        "entity_id": "fn:b4c9e2f",
        "name": "stc_color",
        "signature": "void Logging::stc_color(const String&, Character*, int)",
        "kind": "function",
        "brief": "Send a colored message to a character"
      }
    }
  ],
  "query": "stc",
  "result_count": 2
}
```

### Prose Query: `"send formatted text to character output buffer"`

```json
{
  "results": [
    {
      "result_type": "entity",
      "score": 7.23,
      "winning_view": "doc",
      "winning_score": 7.23,
      "losing_score": 3.45,
      "entity_summary": {
        "entity_id": "fn:a3f8c1d",
        "name": "stc",
        "signature": "void Logging::stc(const String&, Character*)",
        "kind": "function",
        "brief": "Send a message to a character with color codes"
      }
    }
  ],
  "query": "send formatted text to character output buffer",
  "result_count": 1
}
```

### Nonsense Query: `"xyzzy foobar baz"`

```json
{
  "results": [],
  "query": "xyzzy foobar baz",
  "result_count": 0
}
```
