# Phase A — Legacy Common Integration

> Replace `build_helpers/` reimplementations with `legacy_common` imports.
> Establishes the model layer everything else builds on.
>
> Items: gaps.md §4, §5, §6

---

## 1. Common Module Consolidation (gaps §4)

`build_helpers/` reimplements models and loaders that already exist in `packages/legacy_common/`. The three relevant `legacy_common` modules (`doc_db.py`, `doxygen_parse.py`, `doxygen_graph.py`) have **no heavy dependencies** — they use only stdlib + pydantic + networkx + loguru. (The heavy deps — `leidenalg`, `numpy`, `openai`, `scikit-learn` — are in other modules like `llm_utils.py`, `openai_embeddings.py`, `semantic_clustering.py`.) One unused import (`from jinja2 import is_undefined` in `doxygen_graph.py`) should be removed.

### 1a. Use `legacy_common` entity models and EntityID

`build_helpers/artifact_models.py` re-implements `EntityID`, `DoxygenLocation`, `DoxygenEntity`, and `EntityDatabase` as stdlib dataclasses. These are stripped-down copies of the Pydantic models in `legacy_common/doxygen_parse.py`. The `split_entity_id()` function in `entity_ids.py` duplicates `EntityID.split()`.

**Action:**
- Import `EntityID`, `DoxygenEntity`, `EntityDatabase`, `load_db` from `legacy_common.doxygen_parse`
- Remove duplicated models and `split_entity_id()` from `build_helpers`
- Use `EntityID` objects throughout the build pipeline, converting to string only at the DB boundary
- Add `legacy-common` as a workspace dependency in `mcp/doc_server/pyproject.toml`

### 1b. Use `legacy_common` Document model

`build_helpers/artifact_models.py` defines a dataclass `Document` with 11 fields — a subset of the Pydantic `Document` in `legacy_common/doc_db.py` which has the full field set including `cid`, `mid`, `etype`, `to_doxygen()`, etc.

**Action:**
- Import `Document` from `legacy_common.doc_db`
- Remove the dataclass reimplementation
- Replace `build_helpers/embed_text.py` (`build_embed_text()`) with `Document.to_doxygen()` calls

### 1c. DocumentDB — switch to legacy_common loader (generated_docs)

**Critical context:** The flat `artifacts/doc_db.json` is a **stale snapshot** — see Phase B. It has 12 fields, 2,272 briefs. The per-compound `generated_docs/` files have 20 fields, 4,946 briefs (93.4%), plus notes (83%), rationale (83%), and usages (55%) that doc_db.json entirely lacks. The MCP build must stop reading doc_db.json and use generated_docs directly.

The `DocumentDB` in `legacy_common/doc_db.py` loads from per-compound `generated_docs/*.json` files. The `Document` model there is a Pydantic BaseModel with the full field set (brief, details, params, returns, notes, rationale, usages, state, throws, tparams, etc.).

**Action:**
- Import `Document` and `DocumentDB` from `legacy_common.doc_db`
- Remove the flat-file `DocumentDB` from `build_helpers/artifact_models.py`
- The build pipeline constructs a `legacy_common.doc_db.DocumentDB` pointed at the generated_docs directory (via config, not the hardcoded singleton)
- Remove `doc_db.json` from the required artifacts list — it's a stale artifact superseded by generated_docs
- The `legacy_common.doc_db.Document.to_doxygen()` method replaces `build_embed_text()` (§1b)

### 1d. Use `legacy_common` graph loader

`build_helpers/artifact_models.py` has `load_gml_graph()` — identical to `legacy_common/doxygen_graph.py`'s `load_graph()`.

**Action:**
- Import `load_graph` from `legacy_common.doxygen_graph`
- Remove `load_gml_graph()` from `artifact_models.py`

### 1e. ARTIFACTS_DIR as configuration

`legacy_common/__init__.py` hardcodes `ARTIFACTS_DIR = REPO_ROOT / "artifacts"`. The MCP build passes artifacts paths explicitly (via `server/config.py`). This is fine — the build pipeline should continue to use explicit paths, not the hardcoded global.

No change needed to `legacy_common` — just don't import `ARTIFACTS_DIR` from it in the MCP server.

---

## 2. SignatureMap → Common Module (gaps §5)

`projects/doc_gen/build_signature_map.py` is a standalone script that generates `signature_map.json` by joining `code_graph.json` and `doc_db.json`. It doesn't use any `legacy_common` facilities — it manually parses raw JSON, reimplements signature construction, and reimplements entity_id construction.

The signature map is a derived artifact — it can be computed on the fly from the entity database + doc database, similar to how `doc_db.py` manages documents. There is no reason to pre-compute and ship it as a separate artifact.

**Action:**
- Create a `SignatureMap` class in `legacy_common` (or move the existing one from `build_helpers/entity_ids.py`) that builds itself from an `EntityDatabase` + `DocumentDB` at construction time
- The build pipeline constructs a `SignatureMap` from the loaded databases instead of loading a pre-computed JSON file
- `build_signature_map.py` becomes unnecessary (or becomes a thin CLI that dumps the computed map for debugging)
- Remove `signature_map.json` from the required artifacts list — validate_artifacts no longer checks for it

---

## 3. Dataclass → Pydantic Audit (gaps §6)

The MCP server should use Pydantic models consistently. Two files use stdlib `@dataclass`:

| File | Class | Notes |
|------|-------|-------|
| `build_helpers/artifact_models.py` | `EntityID`, `DoxygenLocation`, `DoxygenEntity`, `Document` | Replaced by §1a/§1b (use legacy_common Pydantic models) |
| `server/resolver.py` | `ResolutionResult` | Internal pipeline result — should be converted to Pydantic `BaseModel` |

**Action:**
- `artifact_models.py` dataclasses: eliminated by §1 consolidation
- `resolver.py` `ResolutionResult`: convert to `BaseModel`

---

## Deliverable

- `build_helpers/artifact_models.py` is either empty or deleted
- `build_helpers/embed_text.py` removed — replaced by `Document.to_doxygen()`
- `signature_map.json` removed from required artifacts
- The build pipeline imports models from `legacy_common` and no longer reimplements them
- `ResolutionResult` is a Pydantic `BaseModel`
- All existing tests pass (contract tests don't need DB)
