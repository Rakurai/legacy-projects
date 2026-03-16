# doc_gen — AI-Assisted Codebase Archaeology (Archived)

This project used AI coding agents (GitHub Copilot in VS Code) to systematically
read, summarize, and document every source file in the Legacy MUD C++ codebase.
The work is complete and all reusable outputs have been promoted to their
permanent locations. Everything here is the working material that drove the
process.

---

## What This Project Did

The Legacy codebase is ~90 KLOC of C++14 spread across ~220 source and header
files with no prior documentation beyond scattered code comments. This project
created a comprehensive understanding of the system by having an AI agent read
every file, summarize it, group files into subsystems, and produce per-subsystem
documentation.

The process ran across multiple Copilot agent sessions, guided by reusable
prompts and a structured plan. Each session picked up where the previous one
left off using `files_old.json` as a progress ledger.

---

## Phases

### Phase 1 — Discovery & Inventory

Built the initial context that all later phases depended on.

- **cscope** indexed the source tree → `context/internal/cscope.files`
- `scripts/generate_dependency_graph_md.py` processed cscope output →
  `context/dependency_graph.md` (6,080 lines of per-file symbol defs, includes,
  calls, and references)
- `scripts/generate_files_old.py` + `scripts/categorize_files_old.py` built the
  file inventory → `context/files_old.json` (every file with LOC, category,
  summary initially null)
- `context/files_old.md` was the human-readable view of the same data

### Phase 2 — Header File Summarization

A Copilot agent session guided by
`prompts/doc_gen.prompt.md` + `prompts/doc_gen_batch.prompt.md`.

The agent worked through all `.h` / `.hh` files in batches grouped by
subdirectory. For each file it read the source, wrote a summary, and set the
`summary` field in `files_old.json`. The dependency graph provided cross-file
context.

### Phase 3 — Implementation File Summarization

Same process as Phase 2 but for `.cc` / `.cpp` files, with header summaries
from Phase 2 available as additional context.

### Phase 4a — Initial Component Grouping

The agent synthesized file summaries into 9 high-level component group documents
in `old_component_groups/`:

- `admin_systems.md`
- `character_system.md`
- `game_mechanics.md`
- `information_systems.md`
- `infrastructure.md`
- `interaction_systems.md`
- `object_system.md`
- `user_experience.md`
- `world_system.md`

These were a first draft — broad groupings with some misclassified content.

### Phase 4b — Reclassification into 23 Subsystem Docs

Using `prompts/doc_gen_regroup_loop.prompt.md`, the agent extracted, refined,
and reclassified content from the 9 old groups into 23 focused subsystem docs.
Progress was tracked via `component_doc_checklist.md` (all items completed).

**Output:** `.ai/docs/components/*.md` — the current subsystem documentation
(still in the active tree, not archived here).

---

## Artifacts in This Archive

### `plan.md`
The project plan describing all phases, deliverables, workflow, and success
criteria.

### `component_doc_checklist.md`
Tracking checklist for the Phase 4b reclassification loop. All 23 subsystems
checked off.

### `context/`
Working context consumed by the agent during documentation sessions.

| File | Description |
|------|-------------|
| `files_old.json` | Master file inventory — 220 entries with path, LOC, category, and LLM-written summary per file. The progress ledger for Phases 2–3. |
| `files_old.md` | Human-readable markdown view of the file inventory, grouped by subsystem. |
| `dependency_graph.md` | Per-file symbol definitions, includes, function calls, and symbol references. 6,080 lines generated from cscope output. |
| `files_docs.md` | Self-referential index of documentation files (stale). |
| `internal/cscope.files` | File list used as input to cscope indexing. |
| `mud_system_architecture_final.md` | 7-group architecture overview |
| `system_architecture_overview.md` | top-level architecture narrative |

### `old_component_groups/`
The 9 first-pass component group documents from Phase 4a. Superseded by the 23
subsystem docs in `.ai/docs/components/`.

### `prompts/`
VS Code Copilot agent prompts that guided each phase.

| Prompt | Used In | Purpose |
|--------|---------|---------|
| `doc_gen.prompt.md` | Phases 2–3 | Master workflow: iterate through headers then source files, update `files_old.json` |
| `doc_gen_batch.prompt.md` | Phases 2–3 | Per-batch: group by subdirectory, summarize each file, update JSON |
| `doc_gen_regroup_loop.prompt.md` | Phase 4b | Reclassification: extract from old groups into new per-subsystem docs |

### `scripts/`
One-shot Python scripts used during Phase 1 discovery. None are needed again.

| Script | Purpose |
|--------|---------|
| `generate_dependency_graph_md.py` | cscope output → `dependency_graph.md` |
| `generate_files_old.py` | Build initial `files_old.json` from directory scan |
| `categorize_files_old.py` | Add category field to `files_old.json` entries |
| `list_null_summaries.py` | Show files not yet summarized (progress check) |
| `update_file_summaries.py` | Batch-update summaries in `files_old.json` |
| `build_call_graph.py` | Early call-graph builder (ctags-based, not used in final) |
| `build_call_graph_doxygen.py` | Call-graph builder using Doxygen XML (exploratory) |
| `build_call_graph_lc.py` | Call-graph builder using libclang (exploratory) |
| `draw_call_graph.py` | Visualization of call graphs (exploratory) |
| `format_call_graph.py` | Format call graph for display (exploratory) |
| `translate_call_graph.py` | Convert call graph between formats (exploratory) |
| `traverse_call_graph.py` | Walk call graph for analysis (exploratory) |
| `debug_clang.py` | Debug libclang parsing issues (exploratory) |

---

## Outputs That Survived (Not Archived)

The following outputs from this project remain in the active tree:

- `.ai/docs/components/*.md` — 23 subsystem documentation files (Phase 4b output)

These are the durable products of the project. The Doxygen-based entity pipeline
(`.ai/gen_docs/`, `.ai/artifacts/`) later built on top of these as additional
context, but that is a separate project.
