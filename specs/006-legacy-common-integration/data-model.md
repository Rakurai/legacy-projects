# Data Model: Legacy Common Integration

## Entity Mapping: build_helpers → legacy_common

### EntityID

| Aspect | build_helpers (current) | legacy_common (target) |
|--------|------------------------|----------------------|
| Type | `@dataclass` | Pydantic `BaseModel` |
| Fields | `compound: str`, `member: str \| None` | `compound: str`, `member: str \| None` |
| Parsing | `from_str()`: splits on last `_` | `from_str()`: splits on last `_`; `split()`: regex-based |
| Hashing | `__hash__` on `str(self)` | `__hash__` on `str(self)` |
| String | `"{compound}_{member}"` or `"{compound}"` | Same |

**Migration**: Direct replacement. Key difference: `split()` static method uses regex `r"^(.*)_([0-9a-z]{2}[0-9a-f]{30,})$"` vs simple last-underscore split. Must validate equivalence for all entity IDs.

### DoxygenEntity

| Aspect | build_helpers (current) | legacy_common (target) |
|--------|------------------------|----------------------|
| Type | `@dataclass` | Pydantic `BaseModel` with subclasses |
| Core fields | id, kind, name, body, decl, file | id, kind, name, body, decl, file |
| Extra fields | — | extern, doc, detailed_refs |
| `.signature` | Computed: `definition + argsstring` for functions, `name` otherwise | Same logic, but via subclass override (DoxygenFunction) |
| `from_dict()` | Flat construction | Dispatches to DoxygenFunction/DoxygenMember/DoxygenClass/DoxygenCompound/DoxygenFile |
| Location fields | `DoxygenLocation` dataclass | `DoxygenLocation` BaseModel (same fields: fn, line, column, end_line, type) |

**Migration**: Direct replacement. Extra fields (extern, doc, detailed_refs) are harmless — pipeline accesses only needed fields. Subclass dispatch is transparent to consumers accessing common attributes.

### EntityDatabase

| Aspect | build_helpers (current) | legacy_common (target) |
|--------|------------------------|----------------------|
| Type | `@dataclass` with `dict[str, DoxygenEntity]` | Pydantic `BaseModel` with structured storage |
| Storage | Flat `entities: dict` | `compounds`, `members`, `member_groups`, `locations`, `codelines` |
| Flat access | Direct dict access | `.entities` property (merged compounds + members) |
| Key type | `str` | `EntityID` |
| `from_json()` | Parses JSON array → flat dict | Parses JSON → structured DB with subclass dispatch |

**Migration**: Use `entity_db.entities` for flat iteration. Adapt key access: `entity_db.entities[entity_id]` where `entity_id` is an `EntityID` object, or use `entity_db.get(id_string)` which accepts strings.

### Document

| Aspect | build_helpers (current) | legacy_common (target) |
|--------|------------------------|----------------------|
| Type | `@dataclass` | Pydantic `BaseModel` (extends DoxygenFields) |
| Core fields | state, brief, details, params, returns, rationale, usages, notes, definition, argsstring, system | Same + cid, mid, etype, kind, name, qualified_name, prompt, response, tparams, throws |
| `from_dict()` | Manual, handles `returns`/`return` key | Pydantic with `validation_alias` for returns/return |
| `to_doxygen()` | N/A (separate `build_embed_text()`) | Built-in method, returns formatted `/** ... */` block |

**Migration**: Replace `build_embed_text(raw_dict)` calls with `document.to_doxygen()`. The output format is functionally equivalent (Doxygen tag structure).

### DocumentDB

| Aspect | build_helpers (current) | legacy_common (target) |
|--------|------------------------|----------------------|
| Type | `@dataclass` | Pydantic `BaseModel` |
| Source | `doc_db.json` (flat file, repr-tuple keys) | `generated_docs/*.json` (per-compound files) |
| Key structure | `repr((compound_id, signature))` → Document | `compound_id` → `signature` → Document |
| Lookup | `get_doc(compound_id, signature)` | `get_doc(compound_id, entity_signature)` |
| Path config | Explicit path passed to loader | **Needs modification**: add `docs_dir` parameter |
| Coverage | 2,272 briefs (43%) | 4,946 briefs (93.4%) |

**Migration**: Modify `DocumentDB` to accept `docs_dir` parameter. Construct with explicit path from `server/config.py`. Two-level key structure replaces repr-tuple keys.

### SignatureMap (new)

| Aspect | Current (JSON file) | Target (computed) |
|--------|---------------------|-------------------|
| Source | `signature_map.json` pre-computed artifact | Computed from EntityDatabase + DocumentDB |
| Key | `repr((compound_id, second_element))` | Same canonical key format |
| Value | Old Doxygen entity ID string | Same |
| Lifecycle | Static file loaded at build start | Computed after entity and document loading |

**Migration**: New `SignatureMap` class in `build_helpers/` that takes `EntityDatabase` and `DocumentDB`, iterates document entries, and builds the mapping.

### ResolutionResult

| Aspect | Current | Target |
|--------|---------|--------|
| Type | `@dataclass` | Pydantic `BaseModel` |
| Fields | status, match_type, candidates, resolved_from | Same |
| Methods | `to_entity_summaries()` | Same |
| Validation | None | Pydantic field validation |

**Migration**: Change decorator from `@dataclass` to subclass `BaseModel`. Fields and methods unchanged.

## Dependency Flow

```text
legacy_common.doxygen_parse ──→ EntityID, DoxygenEntity, EntityDatabase
legacy_common.doc_db ──────────→ Document, DocumentDB (with docs_dir param)
legacy_common.doxygen_graph ───→ load_graph()

build_helpers/entity_ids.py ───→ compute_entity_id(), kind_to_prefix() [KEPT]
build_helpers/loaders.py ──────→ validate_artifacts(), load_* functions [MODIFIED]
build_helpers/entity_processor ─→ merge, enrich, ID assignment [MODIFIED]
build_helpers/embeddings_loader → embedding generation [MODIFIED]
build_helpers/graph_loader ────→ graph metrics [MODIFIED]

build_script/build_mcp_db.py ──→ orchestrator [MODIFIED]
```
