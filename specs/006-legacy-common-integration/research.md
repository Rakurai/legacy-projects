# Research: Legacy Common Integration

## R-001: DocumentDB Path Configuration

**Decision**: Modify `DocumentDB` in `legacy_common/doc_db.py` to accept an optional `docs_dir: Path | None` constructor parameter. When provided, use it instead of the `GENERATED_DOCS_DIR` constant.

**Rationale**: The current `DocumentDB.__init__()` auto-calls `load()` which reads from the hardcoded `GENERATED_DOCS_DIR` constant (`ARTIFACTS_DIR / "generated_docs"`). The build pipeline must point to a configurable path via `server/config.py`, not the legacy_common default. A constructor parameter is the minimal, non-breaking change.

**Alternatives considered**:
- Monkey-patching `GENERATED_DOCS_DIR` before construction — fragile, violates fail-fast
- Subclassing `DocumentDB` in build_helpers — reintroduces duplication
- Using environment variable — implicit coupling, not typed

**Implementation**: Add `docs_dir: Path | None = None` field to `DocumentDB`. In `load()`, use `self.docs_dir or GENERATED_DOCS_DIR`. This preserves backward compatibility for existing callers (the singleton, doc_gen scripts).

---

## R-002: EntityDatabase API Shape Mismatch

**Decision**: Use `EntityDatabase.entities` property to get a flat `Dict[EntityID, DoxygenEntity]` mapping, then adapt access patterns in the build pipeline.

**Rationale**: The build_helpers `EntityDatabase` is a flat `dict[str, DoxygenEntity]` keyed by string entity IDs. The legacy_common `EntityDatabase` stores compounds and members separately and exposes a merged view via the `.entities` property (returns `Dict[EntityID, DoxygenEntity]`). The build pipeline iterates over all entities — `.entities` provides exactly this. Key type changes from `str` to `EntityID` but `EntityID.__str__()` and `EntityID.__hash__()` exist, so dict lookups can be adapted.

**Alternatives considered**:
- Adding a flat dict property to legacy_common — unnecessary; `.entities` already serves this purpose
- Wrapping EntityDatabase in an adapter — reintroduces indirection

**Key difference**: `EntityDatabase.from_json()` in legacy_common parses JSON and dispatches to subclasses (DoxygenFunction, DoxygenClass, etc.) via `DoxygenEntity.from_dict()`. The build_helpers version creates flat `DoxygenEntity` instances. The subclass dispatch is fine — the pipeline accesses common fields (id, kind, name, body, decl, file, signature) that exist on all subclasses.

---

## R-003: EntityID.split() vs split_entity_id()

**Decision**: The spec mentions replacing `split_entity_id()` in `entity_ids.py`, but this function does **not exist** in `entity_ids.py`. The ID splitting is done by `EntityID.from_str()` in `artifact_models.py`. After `artifact_models.py` is deleted, `EntityID.from_str()` from `legacy_common` takes over naturally — no explicit replacement needed.

**Rationale**: Research confirmed `entity_ids.py` contains only `compute_entity_id()` and `kind_to_prefix()`. The `EntityID` class and its `from_str()` method live in `artifact_models.py`. The legacy_common `EntityID.split()` uses a regex approach (`r"^(.*)_([0-9a-z]{2}[0-9a-f]{30,})$"`) while the build_helpers `EntityID.from_str()` splits on the last underscore. These may differ for edge cases, but both are only used for parsing `code_graph.json` entity IDs which follow a consistent format.

**Action**: Verify that `EntityID.split()` and `EntityID.from_str()` produce identical results for all ~5,300 entity IDs in `code_graph.json` during implementation. Add a validation assertion in the build script.

---

## R-004: Test File Impact — FR-014 Correction

**Decision**: FR-014 ("all existing contract tests pass without modification") needs amendment. Two test files import from modules being deleted.

**Rationale**: Research found:
- `test_embed_text.py` imports `build_embed_text` from `build_helpers.embed_text` — this module is being deleted (FR-009). The test must be deleted or rewritten to test `Document.to_doxygen()`.
- `test_entity_ids.py` imports `compute_entity_id`, `kind_to_prefix` from `build_helpers.entity_ids` — this module is **not** being deleted (it has no equivalent in legacy_common). No changes needed.
- No other test files import from `artifact_models.py`.
- The spec references `tests/test_tools.py` which does not exist. Tests are spread across 20 modules.

**Action**: Delete `test_embed_text.py` (the function it tests is being removed; `Document.to_doxygen()` is tested in legacy_common's own tests). Update FR-014 to clarify that contract tests for runtime server behavior pass without modification; build helper tests for deleted modules are removed.

---

## R-005: build_helpers Package Registration

**Decision**: Remove `build_helpers` from the `packages` list in `mcp/doc_server/pyproject.toml` after `artifact_models.py` and `embed_text.py` are deleted. Keep `build_helpers/` as a directory (it still contains `entity_ids.py`, `entity_processor.py`, `embeddings_loader.py`, `graph_loader.py`, `loaders.py`).

**Rationale**: The `pyproject.toml` currently lists `packages = ["server", "build_helpers"]` under `[tool.hatch.build.targets.wheel]`. Since `build_helpers` is not a published library (it's only used by the build script), removing it from the wheel is correct. The build script imports it as a local package during `uv run`.

**Alternatives considered**:
- Keeping it in the wheel — unnecessary; build_helpers is not used at runtime by the MCP server

---

## R-006: Signature Map On-the-Fly Computation

**Decision**: Create a `SignatureMap` class in `build_helpers/` that constructs the mapping from `EntityDatabase` and `DocumentDB` at build time.

**Rationale**: The current `signature_map.json` maps `repr((compound_id, second_element))` → old Doxygen entity ID. This same mapping can be derived by iterating `DocumentDB.docs` (which is keyed by `compound_id → signature → Document`) and matching against `EntityDatabase`. The `compute_entity_id()` function in `entity_ids.py` already uses `repr((compound_id, second_element))` as its canonical key format.

**Implementation approach**:
- Iterate `DocumentDB.docs`: for each `(compound_id, signature)` pair, look up the matching entity in `EntityDatabase` by matching compound ID and signature
- Store mapping: `(compound_id, second_element)` → old Doxygen entity ID string
- The `second_element` is the document signature (member name/function signature)
- Provide dict-like lookup interface matching current `signature_map[repr((cid, sig))]` usage

---

## R-007: jinja2 Import Removal in legacy_common

**Decision**: Remove `from jinja2 import is_undefined` from `legacy_common/doxygen_graph.py`.

**Rationale**: Research confirmed the import exists at the top of the file but is never used in any function. Removing it eliminates an unnecessary dependency pull. The `jinja2` package is still listed in legacy_common's dependencies (used elsewhere for templating), so the package dependency itself stays.

**Action**: Single line deletion. No behavioral change.
