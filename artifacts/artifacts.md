# Artifact Primer

This document describes the two primary data artifacts produced and consumed by the pipeline—**`code_graph.json`** (the entity database) and the **doc_db** system (`generated_docs/*.json` plus the `doc_db` module)—and how they relate to the companion **`code_graph.gml`** graph file.

---

## Big-Picture View

```
Doxygen XML  ──►  doxygen_parse  ──►  code_graph.json   (canonical entity database)
                  doxygen_graph  ──►  code_graph.gml     (dependency graph)

                        ▼                    ▼
              ┌─────────┴────────────────────┴──────────┐
              │  docgen notebooks (forward / backward)  │
              │  gen_common  ·  llm_utils  ·  templates │
              └──────────────────┬───────────────────────┘
                                 ▼
                    generated_docs/<compound>.json  ──►  doc_db.json
                                                            │
              code_graph.json + doc_db.json  ──►  signature_map.json
                                                     (entity ID bridge)
                                                            │
              ┌─────────────────────────────────────────────┘
              │  MCP server build  ·  classify_fns  ·  clustering
              └─────────────────────────────────────────────────
```

The **entity database** (`code_graph.json`) is a flat list of every Doxygen-recognized entity (functions, classes, structs, files, variables, etc.) extracted from the legacy C++ codebase. The **dependency graph** (`code_graph.gml`) is a directed multigraph built from references found in those entities—"who calls whom," "who includes whom," "who inherits from whom." The **document database** (`generated_docs/`) stores the LLM-generated documentation for each entity, keyed by compound ID and entity signature.

All three are produced once (by `code_graph.ipynb`) and then consumed as read-only inputs by every downstream notebook and module.

---

## 1. `code_graph.json` — The Entity Database

### What it is

A JSON array of objects. Each object describes a single Doxygen entity parsed from the legacy project's XML output. The file currently contains **5,305 entries** spanning compounds (structs, classes, files, namespaces, directories, groups) and members (functions, variables, defines, enums, typedefs).

### How it's created

1. Doxygen runs on the legacy C++ source, producing XML in `<legacy>/doxygen_output/xml/`.
2. `code_graph.ipynb` calls `doxygen_parse.EntityDatabase.from_xml_dir(xml_dir)` which parses every `<compounddef>` and `<memberdef>` element.
3. The resulting `EntityDatabase` is serialized with `doxygen_parse.save_db(db, path)`, which calls `EntityDatabase.model_dump_json()` — this flattens the in-memory dictionaries into a single JSON array.

### How to load it

```python
import doxygen_parse as dp

db = dp.load_db(Path("context/internal/code_graph.json"))
# db.compounds  → Dict[EntityID, DoxygenCompound]
# db.members    → Dict[EntityID, DoxygenMember]
# db.entities   → combined dict of both
# db.get("class_room_i_d")  → DoxygenClass(...)
```

### Entry schema

Every entry is a dict that can be deserialized into a `DoxygenEntity` subclass. The fields are:

| Field | Type | Description |
|-------|------|-------------|
| `id` | `{compound, member?}` | **Primary key.** `compound` is always present (Doxygen's compound refid, e.g. `"structrace__type"`). `member` is present only for member entities (a 32+ hex-char suffix, e.g. `"1acb9fb86413bad3f692989a4d59200b39"`). |
| `kind` | string | Entity kind: `function`, `variable`, `class`, `struct`, `file`, `namespace`, `dir`, `group`, `enum`, `define`, `typedef`. |
| `name` | string | Human-readable name (e.g. `"race_type"`, `"do_look"`, `"merc.hh"`). |
| `extern` | bool | `true` if the entity is declared externally (typically `false`). |
| `file` | location? | Where the entity is referenced at file scope — `{fn, line, column, type:"file"}`. |
| `decl` | location? | Declaration location — `{fn, line, column, type:"decl"}`. Present mainly for functions and variables. |
| `body` | location? | Body/definition location — `{fn, line, end_line, type:"body"}`. This is the span of source code. |
| `detailed_refs` | array | Cross-references extracted from Doxygen XML. See "References" below. |
| `definition` | string? | Full definition text (functions only, e.g. `"RoomID::RoomID"`). |
| `argsstring` | string? | Argument string (functions only, e.g. `"(int vnum)"`). |
| `appearance` | object? | Pre-existing Doxygen documentation: `{brief?, details?, params?, returns?}`. Only present when the source already has doc comments. |
| `codeline_refs` | object? | File compounds only. Maps member entity IDs to lists of referenced entity IDs, extracted from `<programlisting>` sections. |

### Location objects

Locations appear in `file`, `decl`, and `body` and share this shape:

```json
{
  "fn": "src/include/merc.hh",   // path relative to project root
  "line": 141,                    // start line (1-based)
  "column": 1,                    // column (0-based), absent on body
  "end_line": 152,                // end line (body only)
  "type": "file" | "decl" | "body"
}
```

- **file**: the file-level location where Doxygen first sees the entity.
- **decl**: explicit declaration location (forward declarations, function declarations in headers).
- **body**: the actual source definition, with a span from `line` to `end_line`.

### Entity ID structure

The `id` object is split into `compound` and optionally `member`:

- **Compound-only** (structs, classes, files, namespaces, dirs, groups): `{"compound": "structrace__type"}` — the Doxygen refid for the compound.
- **Member** (functions, variables, defines, enums, typedefs): `{"compound": "class_room_i_d", "member": "1acb9fb86413bad3f692989a4d59200b39"}` — the compound that contains the member plus a unique hash suffix.

The string form is `compound_member` (joined with `_`), e.g. `"class_room_i_d_1acb9fb86413bad3f692989a4d59200b39"`. Use `EntityID.from_str()` or `EntityID.split()` to parse.

### Reference objects (`detailed_refs`)

Each reference captures a cross-reference found in the Doxygen XML:

```json
{
  "refid": "class_room_i_d_1a8e94af33f120368add8456779bd45624",
  "tag": "referencedby",
  "attrs": {"compoundref": "_room_i_d_8cc", "startline": "17", "endline": "36"}
}
```

The `tag` values determine the relationship type when building the graph:

| Tag | Meaning | Graph edge |
|-----|---------|------------|
| `references` | This entity references another | CALLS (fn→fn) or USES (→var/type) |
| `referencedby` | Another entity references this one | CALLS / USES (reversed) |
| `basecompoundref` | This class/struct inherits from target | INHERITS |
| `derivedcompoundref` | Target inherits from this (reversed) | INHERITS |
| `includes` | This file includes target file | INCLUDES |
| `includedby` | Target file includes this (reversed) | INCLUDES |
| `innerclass`, `innernamespace`, `innerfile`, `innerdir` | Containment | CONTAINED_BY (reversed) |
| `reimplements` / `reimplementedby` | Virtual function override | INHERITS |
| `_in_compound` | Synthetic: member belongs to its compound | CONTAINED_BY |

### Entity kind breakdown (current data)

| Kind | Count | Level |
|------|-------|-------|
| function | 2,365 | member |
| variable | 2,369 | member |
| file | 217 | compound |
| struct | 80 | compound |
| group | 85 | compound |
| class | 56 | compound |
| dir | 20 | compound |
| define | 82 | member |
| enum | 11 | member |
| namespace | 11 | compound |
| typedef | 9 | member |

---

## 2. `code_graph.gml` — The Dependency Graph

### What it is

A NetworkX `MultiDiGraph` serialized as GML. Nodes represent entities (compounds and members) plus **location nodes** (source positions). Edges represent typed relationships.

### How it's created

`code_graph.ipynb` calls `doxygen_graph.build_graph(db)` which:

1. Creates a node for each compound (keyed by compound ID string) and each member (keyed by the member hash).
2. Iterates `detailed_refs` from every entity, classifies each reference via `classify_reference()`, and adds typed edges.
3. Adds location nodes (body/decl/file positions as string IDs like `"src/include/merc.hh:141:1-152"`) connected to their entities by `REPRESENTED_BY` edges.

### How to load it

```python
import doxygen_graph as dg

g = dg.load_graph(Path("context/internal/code_graph.gml"))
# g.nodes[node_id]  → {"name": ..., "kind": ..., "type": ...}
# g.edges(data=True) → (u, v, {"type": Relationship.CALLS, ...})
```

### Node attributes

| Attribute | Description |
|-----------|-------------|
| `name` | Human-readable name or signature |
| `kind` | Entity kind (`function`, `class`, `struct`, etc.) — absent on location nodes |
| `type` | `EntityType` enum: `"compound"`, `"member"`, `"body"`, `"decl"`, `"file"` |

### Edge types (Relationship enum)

| Type | Meaning | Source → Target |
|------|---------|-----------------|
| `CONTAINED_BY` | Member belongs to compound, or nested class in outer class | child → parent |
| `CALLS` | Function/define calls another function/define | caller → callee |
| `USES` | Entity uses a variable, type, class, etc. | user → used |
| `INHERITS` | Class/struct inheritance or function override | derived → base |
| `INCLUDES` | File includes another file | includer → included |
| `REPRESENTED_BY` | Location node points to the entity it locates | location → entity |

Edges are keyed by relationship type (it's a `MultiDiGraph`), so a pair of nodes can have multiple edges with different types.

### Relationship to `code_graph.json`

The graph and the entity database are **complementary views of the same data**:

- **Entity DB** → rich per-entity metadata (locations, names, definitions, existing docs, raw references).
- **Graph** → the *relationship structure* between entities (who calls whom, containment hierarchy, inheritance tree).

The graph's node IDs map back to entity IDs: compound nodes use the compound refid string, member nodes use the member hash. Use `doxygen_graph.get_body_eid(db, node_id)` to resolve a graph node back to its canonical `EntityID` in the database.

---

## 3. `doc_db` — The Document Database

### What it is

LLM-generated documentation for each entity, produced by the docgen notebooks (forward, backward, refinement passes). Stored on disk as individual JSON files in `context/internal/generated_docs/`, one file per compound. Currently **475 files** containing **5,295 document entries**.

### How it's organized

On disk, each file is named `<compound_id>.json` (e.g. `_affect_8hh.json`) and contains a flat dict mapping **entity signatures** to `Document` objects:

```json
{
  "Actable.hh": { "state": "extracted_summary", "cid": "_actable_8hh", ... },
  "void do_something(Character *ch)": { "state": "refined_summary", ... }
}
```

Keys are the entity's **signature** — for functions this is `definition + argsstring` (e.g. `"void do_look(Character *ch, String argument)"`), for everything else it's the `name` field.

### How to load and use it

The `doc_db` module exposes a singleton `DocumentDB` instance that loads all files on import:

```python
import doc_db

# Get a specific document
doc = doc_db.get_doc("class_room_i_d", "RoomID::RoomID()")

# Add/update a document
doc_db.add_doc(compound_id, entity_signature, document)

# Iterate all documents
for key, doc in doc_db.docs_db.items():
    print(key, doc.state)

# Access by compound
for sig, doc in doc_db.docs_db["_affect_8hh"].items():
    print(sig, doc.brief)
```

### Document schema

Each document is a `Document` Pydantic model (inherits from `DoxygenFields`):

| Field | Type | Description |
|-------|------|-------------|
| **Identity fields** | | |
| `cid` | string | Compound ID (matches `id.compound` in `code_graph.json`) |
| `mid` | string | Member ID hash (or compound ID for compound entities) |
| `etype` | string | `"compound"` or `"member"` |
| `kind` | string | Entity kind (`function`, `variable`, `class`, etc.) |
| `name` | string | Entity name |
| `qualified_name` | string? | Fully qualified name if available |
| `definition` | string? | Function definition text |
| `argsstring` | string? | Function argument string |
| **Documentation fields** (from `DoxygenFields`) | | |
| `brief` | string? | One-line summary |
| `details` | string? | Detailed description |
| `params` | dict? | Parameter name → description mapping |
| `returns` | string? | Return value description |
| `tparams` | dict? | Template parameter descriptions |
| `throws` | string? | Exception descriptions |
| `notes` | string? | Additional notes |
| `rationale` | string? | Why this entity exists / design rationale |
| **Pipeline fields** | | |
| `state` | string | Current documentation state (see lifecycle below) |
| `prompt` | string? | The LLM prompt used to generate this doc |
| `response` | DoxygenFields? | Raw LLM response (structured) |
| `usages` | dict? | Maps `"compound, signature"` → usage description (from backward pass) |

### Document lifecycle states

Documents progress through states as the docgen pipeline runs:

```
extracted_summary  →  generated_summary  →  refined_summary
                                ↓
                       generated_usage  →  refined_usage
```

| State | Set by | Meaning |
|-------|--------|---------|
| `extracted_summary` | `gen_common.document_entity()` | Initial entry with only pre-existing Doxygen comments (may be empty) |
| `generated_summary` | `docgen_forward.ipynb` | LLM has generated a first-pass "what does it do?" description from source code and dependency summaries |
| `refined_summary` | `docgen_forward_refine.ipynb` | Summary refined with dependency docs, usage examples, and kind-specific templates |
| `generated_usage` | `docgen_backward.ipynb` | "What is it for?" — LLM has analyzed callers/users and generated usage descriptions |
| `refined_usage` | `docgen_backward_refine.ipynb` | Usage and rationale refined from the backward-pass analysis |

Current state distribution: 4,447 refined_summary, 732 extracted_summary, 94 generated_summary, 22 refined_usage.

### `doc_db.json` (serialized documentation database) — STALE

<!-- spec 005, gaps.md §15: doc_db.json is a stale snapshot. The MCP build pipeline should switch to reading generated_docs/ directly. -->

> **Warning:** `doc_db.json` is a **stale snapshot** serialized before the LLM refinement passes. It contains only 12 fields and 2,272 briefs. The actual `generated_docs/` files have 20 fields and 4,946 briefs (93.4%), plus notes (83%), rationale (83%), and usages (55%). See `mcp/doc_server/specs/v1/gaps.B.md §1` for the full data audit.

`artifacts/doc_db.json` is a flat JSON dictionary keyed by string-repr tuples `"('compound_id', 'signature')"` → document objects. Currently **5,307 entries** (of which only ~2,272 have non-empty `brief` fields — vs 4,946 in the actual generated_docs source).

The MCP doc server's build pipeline (`build_helpers/loaders.py`) currently loads this file. **This should be replaced** with loading from `generated_docs/` per-compound files via `legacy_common.doc_db.DocumentDB`.

---

## 4. `signature_map.json` — Entity ID Bridge

### What it is

A derived mapping that bridges `code_graph.json` entity IDs to `doc_db.json` keys. It is regenerated from those two sources whenever code_graph.json is refreshed.

### Why it exists

`code_graph.json` identifies members by Doxygen member hashes (e.g. `1acb9fb86413bad3f692989a4d59200b39`), but these hashes change every time Doxygen processes modified source code. `doc_db.json` keys are `(compound_id, signature)` tuples which are stable across regenerations. `signature_map.json` connects the two: given a current entity ID from code_graph, it tells you which doc_db key holds that entity's documentation.

### How it's created

`projects/doc_gen/build_signature_map.py` loads both `code_graph.json` and `doc_db.json`, builds a signature for each code_graph entity using `definition + argsstring` (functions) or `name` (everything else), and matches against doc_db keys sharing the same `compound_id`. The output is a dict mapping each entity ID string to its doc_db `(compound_id, signature)` key.

### When to regenerate

Regenerate `signature_map.json` any time `code_graph.json` is refreshed from new Doxygen output:

```bash
uv run python projects/doc_gen/build_signature_map.py
```

---

## 5. Entity ID Reconciliation

### The member hash instability problem

Doxygen assigns each `<memberdef>` a hash (the `member` part of an entity ID, e.g. `1acb9fb86413bad3f692989a4d59200b39`). These hashes **change when source code changes** — even whitespace-only edits can produce different hashes. This means:

- `code_graph.json` entity IDs are only valid for the Doxygen run that produced them.
- `doc_db.json` entries store a `mid` field from a previous Doxygen run. After refreshing code_graph.json, these `mid` values no longer match.
- **`compound_id` is stable.** Doxygen compound refids (e.g. `class_room_i_d`, `_fight_8cc`) are deterministic and don't change across runs.

### Which artifact is canonical

**`code_graph.json` is canonical** — it is kept fresh with the current Doxygen output and is the source of truth for entity structure, locations, and relationships. When it's regenerated, `signature_map.json` must be re-derived from it. `doc_db.json` entries are stable (keyed by compound_id + signature), but their `mid` field should not be trusted without cross-checking via `signature_map.json`.

### What about entities in doc_db but not code_graph?

`code_graph.json` is intentionally pruned — `doxygen_parse.py` skips `friend`-kind members, and the graph only includes entities that Doxygen emitted as `<memberdef>` or `<compounddef>`. Some doc_db entries reference member hashes from a previous Doxygen run that no longer appear in the current code_graph. These are not "missing" entities — they're stale references. The `signature_map` reconciliation handles this: entries that can't be matched by `(compound_id, signature)` are simply unmatched and get no docs in the MCP server build.

### What are the "phantom" references in code_graph.json?

`code_graph.json` entities contain `detailed_refs` and `codeline_refs` arrays that reference other entity IDs. Some of these referenced IDs (506 in current data) don't appear as entities in the `id` fields. Investigation shows these are:

| Category | Count | Explanation |
|----------|-------|-------------|
| **`enumvalue` IDs** | ~479 | Individual enum constants (e.g. `TO_ROOM`, `paladin`). Doxygen gives each `<enumvalue>` its own ID, but the parser treats the enclosing `<memberdef kind="enum">` as the entity — individual values are sub-entity detail. |
| **`friend` memberdefs** | ~27 | Friend function declarations, explicitly filtered out by `doxygen_parse.py`. |

These are **not missing entities**. They're cross-references at a finer granularity than the entity model supports. The enum and group source-code handling (below) ensures their information is still accessible.

### Enum and group source code

Enums and groups (`@defgroup` blocks for flag constants) contain sub-members whose values matter for understanding the entity, but those sub-members aren't individual entities in the graph. To make this information available:

1. **Enums** already have `body` locations from Doxygen — the source span covers the full enum definition including all values and inline `/**<` comments.

2. **Groups** (`@defgroup` blocks defining sets of `constexpr` flag constants) historically had no `body` because Doxygen doesn't put a `<location>` on group `<compounddef>` elements. We now synthesize a body range from the min/max source lines of the group's member definitions during `parse_compounddef()`.

3. **The MCP server** auto-includes `source_text` for enum and group entities in `get_entity` responses (regardless of `include_code` flag), so the LLM consumer always sees the full list of values without needing a separate request.

This means an agent asking about `ActMessageTypes` (a group) gets the docstring *and* the source block showing `TO_ROOM = 0`, `TO_NOTVICT = 1`, etc. No need to look up individual flag constants as separate entities.

---

## 6. `forward_pass_schedule.json` — Visit Order

### What it is

A JSON array of **4,560 entries**, each describing a graph node to visit during the forward documentation pass. Produced by `doxygen_graph.create_visit_list()`.

### Entry schema

```json
{
  "id": "1acf4d33ee4cff36f69b924471174dcb11",
  "kind": "variable",
  "name": "level",
  "fan_in": 0,
  "fan_out": 204
}
```

| Field | Description |
|-------|-------------|
| `id` | Graph node ID (member hash or compound refid) |
| `kind` | Entity kind |
| `name` | Entity name/signature |
| `fan_in` | Number of unvisited dependencies at scheduling time |
| `fan_out` | Number of unvisited dependants at scheduling time |

Entities with `fan_in: 0` are leaf nodes with no unseen dependencies—they're documented first. The schedule ensures that by the time an entity is documented, its dependencies already have summaries in the doc_db for the LLM to reference.

---

## 7. How the Artifacts Connect

Here's a concrete example of how entity `"RoomID::RoomID()"` is represented across the three artifacts:

**In `code_graph.json`:**
```json
{
  "id": {"compound": "class_room_i_d", "member": "1acb9fb86413bad3f692989a4d59200b39"},
  "kind": "function",
  "name": "RoomID",
  "definition": "RoomID::RoomID",
  "argsstring": "()",
  "body": {"fn": "src/include/RoomID.hh", "line": 7, "end_line": 7, "type": "body"},
  "detailed_refs": [{"refid": "...", "tag": "referencedby", ...}]
}
```

**In `code_graph.gml`** (graph node `"1acb9fb86413bad3f692989a4d59200b39"`):
- `name`: `"RoomID::RoomID()"`
- `kind`: `"function"`
- `type`: `"member"`
- Edges: `CONTAINED_BY → class_room_i_d`, `REPRESENTED_BY ← src/include/RoomID.hh:7:1-7`

**In `generated_docs/class_room_i_d.json`** (key `"RoomID::RoomID()"`):
- `cid`: `"class_room_i_d"`
- `mid`: `"1acb9fb86413bad3f692989a4d59200b39"`
- `state`: `"refined_summary"` (or whatever the pipeline has reached)
- `brief`, `details`, etc. — the generated documentation

The **entity ID** (`compound` + `member`) joins code_graph.json to code_graph.gml. The **signature_map** bridges entity IDs to doc_db keys: `entity_id → (compound_id, signature)`. Do not attempt to join code_graph and doc_db by member hash directly — use `signature_map.json`.
