# AI Agent Documentation Generation Batch Workflow Prompt

---
mode: 'agent'
tools: ['githubRepo', 'codebase']
description: 'Process and summarize a batch of codebase files'
---

## Batch-Level Workflow Instructions

1. **Review Context and Select Workload**
   - Review `.ai/context/files_old.json` for a list of all source files and their summarization status. This file is a structured JSON object mapping file paths to their metadata (LOC, category, summary).
   - Identify files in the target directory (or subdirectory) that have not yet been summarized (i.e., where the `summary` field is null).
   - Select a batch of unsummarized files to process (grouped by the most specific subdirectory).
   - Reference `.ai/context/dependency_graph.md` for file/module relationships.

2. **Summarize Batch**
   - For each file in the batch, generate a summary with key structures, functions, and dependencies.
   - Use available context from `.ai/context/files_old.json` and `.ai/context/dependency_graph.md`.
   - Update `.ai/context/files_old.json` with new insights and summarization status for each file (set the `summary` field).
   - Store the batch summary in `.ai/docs/summary_batch_<subdir>.md`.  An example of a good summary format would be:
```markdown
# XXX System Header Batch Summary (src/include/xxx/)

This batch includes the following header files:
- file_1.hh
- file_2.hh

## Overview

### Key Structures and Types

### Key Functions and Operations

### Dependencies

## Open Questions / Assumptions
```

---

This prompt should be referenced at the start of each batch documentation session to guide your workflow and ensure a consistent, high-quality, and traceable process for each batch.
