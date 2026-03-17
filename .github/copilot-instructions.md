# legacy Development Guidelines

## Dependency / environment management (uv)
- This repository uses **uv** for dependency and environment management.
- **Never** run `python`, `pip`, `pytest`, `ruff`, `mypy`, or any Python module directly.
- Always execute Python and Python tooling via uv so the correct virtual environment is used.

## Python execution
- ALWAYS use `uv run python` instead of `python` or `python3`
- ALWAYS use `uv run pytest`, `uv run ruff`, etc. for any tool in the project

### When adding/changing dependencies
- Add runtime deps: `uv add <pkg>`
- Add dev deps: `uv add --dev <pkg>`
- Sync/install: `uv sync`

## Running Python code
- NEVER use `python -c "..."` for anything longer than a single expression
- For any multi-line script: write it to a `.scratch/` file first, then run it
- `.scratch/` is gitignored and pre-approved for temp files — use it freely
- NEVER write temp scripts to `/tmp`, `/dev/null`, or system directories
- NEVER write and delete a script in the same shell command
  - Write → verify it looks right → run → check output → then delete if cleanup needed

## Terminal output
- NEVER set `PYTHONIOENCODING=utf-8` and `NO_COLOR=1` when running scripts (causes approval trigger)
- Use `--no-color` / `--color=never` flags where available (pytest, ruff, etc.)
- Pipe verbose output through `| head -100` if you only need a sample

## Shell scripting
- NEVER use heredoc (`<<EOF`) syntax — it breaks in many terminal contexts
- Use explicit file writes (`tee`, `cat >`, or a write_file tool call) instead
- Prefer multiple simple shell commands over one complex chained command

---

## Jupyter notebooks (.ipynb) editing rules (MUST FOLLOW)
- **Do not** edit `.ipynb` notebooks using plain-text edits, JSON edits, regex/multi-string replacements, “search and replace”, or partial rewrites of the notebook file content.
- **Do not** treat notebooks as regular JSON text files. Avoid any approach that rewrites or patches raw notebook JSON.
- **Always** use VS Code’s **Notebook editing tools/operations** to make notebook changes:
  - insert/delete/move cells
  - edit cell contents through the notebook cell editor
  - run cells when needed
  - change cell type (code/markdown) using notebook UI operations
- When you need to update multiple cells, perform the changes cell-by-cell using notebook operations (even if slower). This avoids corrupting cell structure/metadata and avoids non-persisted changes due to VS Code’s internal notebook representation.
- If you cannot access notebook editing operations in the current context, **do not proceed** with notebook modifications; instead, describe the required notebook cell-level edits precisely (cell titles/positions + exact code/markdown to paste).

---

## Python discipline (strict)

These rules apply to all Python code in this repository.

### Fail-fast / contract discipline

- Do not add defensive programming.
- Do not add fallback logic.
- Do not add legacy compatibility paths.
- Let errors raise unless explicitly instructed otherwise.
- Use assertions only to enforce meaningful contract invariants.
- Do not assert conditions that would already fail loudly.

### Refactoring behavior

- Update interfaces everywhere.
- Remove dead code.
- Do not add compatibility shims.
- Do not preserve obsolete branches.
- Do not annotate refactors in comments.
- Source reflects current truth; history lives in git.

### Comment discipline

- Do not narrate obvious operations.
- Do not restate symbol names.
- Do not add historical or version commentary.
- Prefer precise naming over explanatory comments.
- Comments should explain intent or invariants only.

---

## Notebook-specific discipline

These rules apply when editing or creating Jupyter notebooks.

### Output discipline

- Do not emit ceremonial output:
  - no “assertion passed”
  - no “step completed”
  - no decorative status prints
- The execution checkmark and elapsed time already indicate success.
- Only display output that helps inspect data or reason about progress.
- Prefer concise, value-adding summaries when useful.
- Avoid output spam.

### Assertion discipline in notebooks

- Each cell has a responsibility boundary.
- Only assert invariants that this cell introduces or is responsible for enforcing.
- Do not add speculative domain constraints.
- Do not re-check conditions that would already fail naturally.

### Structural discipline

- One responsibility per cell.
- No hidden cross-cell state mutations.
- No fallback logic inside notebooks.
- Do not turn notebooks into compatibility layers.
