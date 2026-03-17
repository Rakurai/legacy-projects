## Python Notebook Best Practices for Experimentation + Data Prep (AI-Agent Style Guide)

### Non-negotiable principles

* **Restart + Run All must succeed** without manual intervention.
* **Fail fast**: use assertions appropriately; let exceptions stop execution.
* **No defensive programming** in notebooks.
* **No fallback logic** (illegal unless explicitly requested).
* **No legacy handling** during refactors (illegal unless explicitly requested).
* **No silent “handling”** of bad inputs, schema drift, missing files, etc. Crash loudly.
* Each cell defines a contract boundary and is responsible only for the invariants it introduces or transforms.

---

## Notebook contract

Put this near the top (after basic imports). This is the canonical “how this notebook behaves” block. Keep it small, explicit, and consistent across notebooks.

**Contract must define:**

* **Directories**: `DATA_DIR`, `CACHE_DIR`, `OUT_DIR` (as `Path`)
* **Reproducibility**: `RANDOM_SEED` (if any randomness exists)
* **Behavior toggles**: `REBUILD_xxx` (for time-intensive cached tasks), but avoid proliferating toggles
* **Primary inputs**: filenames / dataset IDs / queries (as strings/constants)
* **Primary outputs**: key artifact paths produced by the notebook

**Contract must also include:**

* Assertions that validate environment assumptions early, but only where violations would otherwise be silent or ambiguous.

  * directories exist / are writable (only if not naturally enforced by first use)
  * required files exist (only if not naturally enforced by first use)
  * required package versions only if genuinely necessary (rare)

**Contract style rules:**

* Global config lives here; everything else is defined near first use.
* Keep it stable: do not scatter config across the notebook.

---

## Structure and readability

### Sections (no numbering)

* Use markdown headers with **intent text** beneath them.
* No numbered or sequential section identifiers (they rot). Ever.

Each section should state:

* what it does
* what it expects (preconditions)
* what it produces (variables/artifacts)

### Cell scope and responsibility

* One responsibility per cell.
* Each cell defines a contract boundary.
* A cell assumes its preconditions are satisfied, performs a transformation, and establishes guarantees for downstream cells.
* Don’t create hidden dependencies on execution order.
* Avoid “setup cells” that mutate global state quietly.

### End state

* The notebook should converge to a small set of clearly named outputs:

  * `df_raw`, `df_clean`, `df_features`, `splits`, `metrics`, etc.
* Avoid leaving many half-used variables lying around.

---

## Imports (lightweight-first, consistent)

### Import tiers

1. **Stdlib + lightweight** at the top: `pathlib`, `json`, `re`, `typing`, `dataclasses`, etc.
2. **Autoreload** immediately after general imports.
3. **Local repository imports** after autoreload.
4. **Heavy packages** only when needed (numpy/sklearn/torch/etc).

### Just-in-time imports

* Allowed only when the import is truly used in a single cell or optional function.
* Otherwise import near the top for discoverability.

### Forbidden patterns

* Importing heavy packages “just in case”.
* Multiple conflicting plotting/progress/logging systems in the same notebook.

---

## Visualization + progress + logging

* Plotting: `matplotlib` baseline; `seaborn` optional (styling/convenience)
* Progress: `tqdm.auto`
* Rich formatting / colored output: `rich` (optional)
* Debug prints: `icecream` (optional, keep minimal)

---

## Functions, annotations, and code placement

### Functions: just-in-time

* Define functions in the same cell block where first used.  Example:

```
def foo():
  ...

foo() # first (or only) foo call
```

* Keep functions small and composable.
* If the function becomes reused across sections/notebooks, extract it to a module.

### Types: always

* Every function has full type annotations (args + return).
* Prefer modern typing (`list[str]`, `dict[str, int]`, `Path`, etc).

### Docstrings: only if they help

* No boilerplate parameter docs (types already cover that).
* If used, docstring explains **purpose and constraints** only.

### Comments: only if they add intent/constraints

* Comments exist only to explain non-obvious intent, invariants, tradeoffs, or domain assumptions.
* No narration of obvious operations.
* Prefer expressive variable and function names over comments.
* Do not include historical or process commentary (moved/updated/legacy notes). Source reflects current truth only.
* Do not annotate refactors or version changes in-line.

---

## State, constants, and variable naming

### Variable reuse (preferred)

* Reuse names when the prior value is no longer relevant.
* Avoid `foo`, `foo2`, `foo_final`. If it’s still “the index”, reuse `index`.
* Rename only when meaning changes.

### Constants

* Define constants **where first used** for experimental iteration.
* Only promote to the top if:

  * used in multiple sections, or
  * true global config (e.g., `DATA_DIR`, `CACHE_DIR`, `RANDOM_SEED`)

---

## Data I/O, caching, and provenance

### Paths

* Use `Path` everywhere.
* No user-specific absolute paths unless explicitly required.

### Provenance (minimum)

Record:

* input identifiers (file name, timestamp, query, commit hash—whatever is applicable)
* row counts at major steps (only if meaningful for inspection)
* required columns/schema assumptions when they are part of the current cell’s contract

### Caching intermediates (optional, but clean)

* Cache expensive steps to `CACHE_DIR`.
* Cache filenames must be descriptive but not versioned (`dataset_clean.parquet`).
* If a cache is used, validate it only insofar as silent misuse could occur. If invalid: fail.

---

## Validation and Assertions (Contract-Based, Not Defensive)

Each cell defines a **contract boundary**.

A cell:

* assumes its preconditions are satisfied
* performs a transformation
* establishes new guarantees for downstream cells

Assertions are used only to enforce guarantees introduced or relied upon by the current cell.

### What assertions are for

Use assertions when:

* A violation would be silent or semantically dangerous.
* The error would not naturally surface as an exception at first use.
* The invariant is critical for downstream logic.
* The invariant is part of the cell’s responsibility.

Examples of appropriate assertions:

* Ensuring a transformation did not change row count unexpectedly.
* Ensuring values fall within a domain required for downstream modeling (without inventing arbitrary constraints).
* Ensuring a grouping operation did not create duplicate keys when uniqueness is required.
* Ensuring filtering removed exactly what the contract says it removes.

Assertions should:

* Be minimal.
* Be meaningful.
* Enforce a real invariant.
* Never invent arbitrary constraints.

### What assertions are NOT for

Do not assert conditions that would already fail loudly:

* “Column exists” if first access would raise.
* “File exists” if open/load would raise.
* “Key exists in dict” if direct access would raise.
* “Type is correct” if misuse would immediately error.

Do not implement paranoia checks.

Do not re-validate upstream contracts unless this cell explicitly transforms that property.

Do not stack redundant schema checks across notebooks.

### Assertion style rules

* Assertions supplement exceptions — they do not replace them.
* No celebratory or redundant success messages.
* If an assertion fails, execution stops. That is sufficient.
* If an invariant becomes invalid after refactoring, fix the logic — do not weaken the assertion.

---

## Output discipline (clutter control)

Notebook output must be value-adding and aligned with the cell’s role.

A cell’s successful execution (checkmark + elapsed time) already indicates success. Do not add decorative confirmation messages.

### Allowed output

Output is appropriate only if it:

* Helps inspect the result of the transformation.
* Confirms scale or scope (e.g., row count after load).
* Displays meaningful intermediate artifacts (DataFrame preview, plot, summary statistics).
* Shows progress for long-running tasks (e.g., `tqdm`).

Concise, value-adding descriptions are allowed, e.g.:

* `"Loaded dataset: 45,000 rows"`
* `"After filtering: 12,314 rows"`

These must be brief and informational — not ceremonial.

### Forbidden output

Do not insert:

* `"Assertion passed!"`
* `"Step completed successfully!"`
* `"Loaded input files!"`
* `"Processing done!"`
* Debug prints that restate obvious operations.
* Output that duplicates what the UI already shows.

Do not narrate execution.

The notebook is not a CLI tool.

---

## Refactoring rules (agent-critical)

When refactoring:

* Update call sites and interfaces everywhere.
* Remove dead code; do not keep it “just in case”.
* Do not add compatibility shims.
* Do not add “temporary” branches that persist.
* Do not insert historical commentary in code.
* If the notebook breaks due to interface changes: **fix the notebook**, don’t patch around it.

---

## Graduation path (when a notebook stabilizes)

When a transformation becomes stable/reusable:

* Move it to `src/...` as a function/module.
* Notebook becomes orchestration + inspection + parameter tweaks.
* Notebook should not become a mini-library.

---

## AI-Agent preflight checklist

Before declaring “done”:

* [ ] Restart kernel → Run All passes.
* [ ] Notebook contract exists and is complete.
* [ ] Each cell enforces only the invariants it owns.
* [ ] No fallback logic anywhere.
* [ ] No legacy compatibility logic anywhere.
* [ ] Assertions are minimal, meaningful, and not redundant.
* [ ] Imports follow the tiering and autoreload order.
* [ ] Functions are typed; docstrings only where helpful.
* [ ] Outputs are meaningful and not ceremonial.
