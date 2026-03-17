# doc_gen — Documentation Generation Pipeline

Generates LLM-powered documentation for the legacy C++ MUD codebase (~5,300 entities) by mining Doxygen XML output and iteratively refining with GPT-4.1-nano.

## Target Artifacts

| Artifact | Format | Description |
|----------|--------|-------------|
| `code_graph.json` | JSON array (5,305 entities) | Entity database parsed from Doxygen XML — compounds, members, locations, relationships |
| `code_graph.gml` | GML multigraph (~14.5K nodes, ~44.5K edges) | Directed dependency graph: calls, uses, contained_by, inherits, includes, represented_by |
| `doc_db.json` | Flat JSON dict keyed by `(compound_id, signature)` | LLM-generated documentation: brief, details, params, returns, rationale, usages |

All three end up in `artifacts/` for consumption by the MCP server build pipeline and the `classify_fns` project.

## Pipeline Phases

### Phase 0: Graph Construction — `notebooks/code_graph.ipynb`

**Input:** Doxygen XML from the legacy C++ repo (`doxygen_output/xml/`)

1. Parse XML with `dp.EntityDatabase.from_xml_dir()` → save as `code_graph.json`
2. Build directed multigraph with `dg.build_graph()`, excluding `__`-prefixed members → save as `code_graph.gml`

Both files are created once and never modified by subsequent phases. The notebook also contains several TEST cells for sanity-checking parsed data (duplicate signatures, forward declarations, location consistency) — these are diagnostic, not part of the production flow.

### Phase 1: Forward Pass — `notebooks/docgen_forward.ipynb`

**Input:** `code_graph.gml`, `code_graph.json`
**Scope:** Functions only

Traverses entities leaf-first (fewest dependencies first) via `dg.create_visit_list()`. For each function:

1. Extract source code via `dg.get_code_body()`
2. Gather dependency briefs via `gen_common.format_dependency_summaries()`
3. Build prompt (inline template — not Jinja2)
4. Call GPT-4.1-nano → parse JSON response
5. Store as `doc.response` (a `DoxygenFields` object)
6. Save per-compound to `generated_docs/{compound_id}.json`

A `commit_docs()` step merges `doc.response` fields into main doc fields and clears the response. A final prune step removes entries whose signatures aren't in the graph.

**Fields populated:** `brief`, `details`, `params`, `returns`, `throws`
**State:** `GENERATED_SUMMARY`

### Phase 2: Backward Pass — `notebooks/docgen_backward.ipynb`

**Input:** `code_graph.gml`, `code_graph.json`, partial `doc_db`
**Scope:** Functions only

Traverses entities in reverse priority order (highest-level first). For each function:

1. Find all dependencies via `dg.fan_in()`
2. For each dependency without existing usage docs:
   - Extract the caller's source code
   - Build a usage-analysis prompt asking how each dependency is used
   - Call GPT-4.1-nano → JSON dict mapping dependency names to usage descriptions
3. Map LLM output names back to node IDs (includes `extract_function_name()` cleanup logic for LLM output variations)
4. Store in `dep_doc.usages[caller_key] = description`

**Fields populated:** `usages` (Dict mapping `"{compound_id}, {signature}"` → usage description)
**State:** `GENERATED_USAGE`

### Phase 3: Forward Refinement — `notebooks/docgen_forward_refine.ipynb`

**Input:** `code_graph.gml`, `code_graph.json`, partial `doc_db`
**Scope:** All entity types (variable, enum, function, define, struct, class, typedef, group, namespace)

Same leaf-first traversal as Phase 1, but with expanded scope and improved prompts:

1. Extract code body
2. Gather dependency docs (reads `doc.response` if available for latest summary)
3. Build prompt via **Jinja2 templates** (`templates/docgen_fw_refine_*.j2`) — kind-specific templates for function, variable, enum, class, and group entities
4. Call GPT-4.1-nano → `DoxygenFields`
5. Store as `doc.response`

A `commit_docs()` step merges response fields into main doc fields (same pattern as Phase 1, but also handles `notes` and `rationale`).

**Fields populated:** `brief`, `details`, `params`, `returns`, `tparams`, `throws`, `notes`, `rationale`
**State:** `REFINED_SUMMARY`

### Phase 4: Backward Refinement — `notebooks/docgen_backward_refine.ipynb`

**Input:** `code_graph.gml`, `code_graph.json`, `doc_db`
**Scope:** Functions with usages in `GENERATED_USAGE` state

Evaluates and refines the usage descriptions from Phase 2:

1. Build evaluation prompt listing all usages for an entity
2. Call GPT-4.1-nano to score each usage on plausibility (0–1) and specificity (0–1)
3. Apply actions: keep, discard, or rewrite

**Fields refined:** `usages` (low-quality entries removed, vague entries rewritten)
**State:** `REFINED_USAGE`

### Phase 5: Classification (separate project)

`classify_fns/classify.ipynb` reads the consolidated `doc_db.json` and writes `system` and `subsystem` labels back to it. This is downstream of doc_gen but modifies the same artifact.

## Notebooks That Don't Modify the Target Artifacts

These notebooks read the artifacts for analysis but do not contribute to building `code_graph.json`, `code_graph.gml`, or `doc_db.json`:

| Notebook | Purpose | Outputs |
|----------|---------|---------|
| `docgen_cluster.ipynb` | Leiden community detection on the code graph | `leiden_communities.json`, `community_classifications.json` |
| `subsystem_discovery.ipynb` | Multi-dimensional clustering (structural + semantic + usage) | `structural_clusters.json`, `semantic_clusters.json`, `integrated_clusters.json` |
| `subsystem_phase_2.ipynb` | Hierarchical subsystem organization with CodeBERT embeddings | `subsystems.json`, `system_hierarchy.json`, `docs/subsystems/*.md` |
| `subsystem_discovery.old.ipynb` | Superseded clustering attempt | — |
| `subsystem_visualization.ipynb` | Visualization | — |
| `explore_xml.ipynb` | Doxygen XML exploration | — |

## Storage Formats

The doc_gen notebooks write to **per-compound JSON files** in `artifacts/generated_docs/{compound_id}.json` via the `doc_db` module's singleton `DocumentDB`. Each file contains a dict of `{signature: Document}`.

The **consolidated `artifacts/doc_db.json`** is a different format: a flat dict keyed by stringified `(compound_id, signature)` tuples. This is what downstream consumers (`classify_fns`, MCP server build) read. The conversion between these two formats is not currently automated in this pipeline.

## Key Shared Code

| Module | Role |
|--------|------|
| `legacy_common/doxygen_parse.py` | `EntityDatabase.from_xml_dir()`, `save_db()`, `load_db()` |
| `legacy_common/doxygen_graph.py` | `build_graph()`, `save_graph()`, `load_graph()`, `create_visit_list()`, `get_code_body()`, `get_body_eid()`, `fan_in()` |
| `legacy_common/doc_db.py` | `DocumentDB`, `Document`, `DoxygenFields`, `DocumentState` |
| `legacy_common/llm_utils.py` | `call_openai()` wrapper |
| `doc_gen/gen_common.py` | `format_dependency_summaries()`, `get_dependency_docs()`, `document_entity()` |
| `doc_gen/src_utils.py` | `extract_lines()`, `extract_preceding_comments_from_source_file()` — earlier comment-extraction approach, not used in main pipeline |
| `templates/docgen_fw_refine_*.j2` | Jinja2 prompt templates for Phase 3 refinement |

## Known Issues

- **`extract_function_name()`** is duplicated verbatim between `docgen_backward.ipynb` and `docgen_backward_refine.ipynb`.
- **`commit_docs()`** is duplicated between `docgen_forward.ipynb` and `docgen_forward_refine.ipynb` (Phase 3 version adds `notes` and `rationale`).
- **Per-compound → flat `doc_db.json` consolidation** has no automated step in this pipeline. The two formats coexist with no explicit conversion script.
- **Path references in `classify_fns`** (`DOC_DB_PATH`, `DOC_DB_BACKUP_PATH`) are stale after the monorepo reorganization.
