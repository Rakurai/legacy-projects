# PATTERNS.md — Universal Development Patterns

Applies to all domains (backend, frontend, workers, CLI).
Voice: imperative, rule-based. Audience: expert coding agent.
Scope: PoC-ready code that is clean, consistent, and DevOps-handoffable without production hardening.

---

## Core Philosophy

* **Clean break**: treat the codebase as greenfield. No legacy references, no migration bridges, no temporary shims.
* **Fail-fast**: startup validates configuration and dependencies; if invalid, **crash immediately** with a helpful error.
* **Schema-first**: define strict typed contracts before logic; enforce at the edges (schemas/types).
* **Program to contract**: trust validated types; **no defensive programming** against inputs already guaranteed by the contract.
* **Composition over inheritance**: prefer composition; keep inheritance shallow and local if used.
* **Minimal, additive documentation**: comments/docstrings must add non-obvious value; do not restate names or signatures.
* **No fallbacks**: the word and practice are **forbidden**. If something is required, it must be present or the program fails usefully.
* **No in-code history**: no versioning, change logs, references to changed/removed code, etc. in the source code.  History is the role of the version control system.

---

## Type Safety as Contract

**Principle**: Types are executable contracts.

**Rules**

* Enforce strict typing everywhere (Python: mypy `--strict`; TS: `strict`).
* No `Any` in production paths. If unavoidable, annotate with `Any` and add `# TODO refine type`.
* Narrow types aggressively (Literal/union/enums). Prefer Protocol/TypedDict over weakening types.
* Public interfaces must be fully typed; return `Optional[T]` **only** when `None` is intentional.
* Interface consistency: return types, error types, and data shapes must be consistent between producer and consumer. If a function's signature or return shape changes, update all callers in the same change.
* **Python 3.14+** lazy evaluation of annotations is native; no `from __future__ import annotations` needed. Forward references work unquoted.
* Use Unicode for all strings.

---

## Dependency Injection

**Principle**: Explicit, testable dependencies.

**Rules**

* Declare dependencies in constructors or framework DI; no hidden globals or dynamic imports.
* Make dependencies mockable. Do not create them inside business logic.

---

## Error Handling

**Principle**: Handle only where you own the responsibility; otherwise propagate.

**Rules**

* Never mask or downgrade errors; no silent catches; no broad `except Exception` without immediate re-raise.
* If an error cannot be meaningfully handled at the current layer, **let it propagate**. Crashing during PoC is informative.
* Wrap external/library exceptions into domain errors **only** when adding actionable context, then re-raise.

---

## Tooling

**Rules**

* **Logging**: `from loguru import logger as log` in every module.
* **Linting & formatting**: `ruff` (lint + format).
* **Static type checking**: `mypy --strict`.
* **Testing**: `pytest` and `pytest-randomly` to detect inter-test coupling.
* **Dependency manifest**: every new third-party import must have a corresponding entry in the project's dependency manifest. Do not import packages that aren't declared.

---

## Minimal, Consistent Logging

**Principle**: Structured context; signal, not noise.

**Rules**

* Log **start**, **error**, **completion** of meaningful operations with contextual fields (resource IDs, operation names).
* Do not duplicate logs and errors; prefer one precise log at the owner boundary.
* Never use `print`. Use `log` (loguru) everywhere.

---

## Interfaces & Resource Design

**Principle**: Predictable, resource-oriented boundaries.

**Rules**

* Use resource-based URLs and appropriate verbs (GET/POST/PUT/PATCH/DELETE) in HTTP services.
* Adhere to the project’s interface contract doc (see INTERFACES.md).
* Do not invent ad-hoc JSON shapes; all payloads must be schema-first and typed.

---

## Naming Conventions

* `snake_case` for functions, methods, variables, and modules.
* `PascalCase` for classes.
* `UPPER_CASE` for module-level constants.
* Names carry intent; if a name needs a comment to explain itself, rename it.

---

## Long-Running Work

**Principle**: Non-blocking orchestration with explicit status (when applicable to the project).

**Rules**

* If work cannot complete within a request boundary, return a **job handle** and expose a status query.
* Do not block threads or event loops waiting for long jobs.
* Keep status schemas typed and minimal (state, updated_at, optional progress/result/error).

---

## Configuration

**Principle**: Typed, validated settings loaded once at startup.

**Rules**

* Use `pydantic-settings` `BaseSettings` for all configuration.
* Load environment-specific values from `.env` files; never hardcode secrets.
* Validate eagerly at startup — missing or invalid config crashes immediately.

---

## Resource & Process Hygiene

**Principle**: Leave the system clean on all paths.

**Rules**

* Validate config and external resources at startup; import required packages at module scope so missing deps fail early.
* Use context managers for files, sockets, sessions, and subprocesses. Ensure cleanup on success, failure, and cancellation paths.

---

## Testing Principles (PoC Scope)

**Principle**: Prove the happy path works; avoid test whirlpools.

**Rules**

* Write **happy-path** tests that confirm contracts and core flows execute successfully.
* Do not construct exhaustive edge-case matrices in PoC.
* Negative-path coverage for spec-defined error conditions is required; exhaustive edge-case matrices are not.
* Tests must be **falsifiable** — each test should fail if its target behavior were broken. Tests that only assert mocks, hardcoded values, or nothing at all are prohibited.
* Prefer a few high-signal integration/contract tests over broad unit coverage.
* If tests or code fail, fix the **implementation**, not by trivializing tests.

---

## Documentation & Code Organization

**Principle**: Small, cohesive units; clarity first.

**Rules**

* One functional unit per file (≤ ~200 LOC) unless a tiny, cohesive family fits better together.
* Names must carry intent; comments/docstrings should explain **why**, not **what** is already obvious.
* Keep domain specifics (logging impl, framework mechanics) in domain docs; keep universal rules here.

---
## Wiring Discipline

**Principle**: Every component must be reachable.

**Rules**

* Every new function, endpoint, handler, config key, or scheduled task must be reachable from at least one production entry point. Dead code on creation is prohibited.
* After renaming, moving, or changing a function signature, verify that every call site uses the new name, location, and signature. No stale references.
* Config keys and environment variables referenced in code must exist in config files or `.env.example`. Config entries that no code references should be removed.

---
## Prohibited Practices

* “Fallback” anything (terminology or behavior).
* Defensive checks against already-validated inputs.
* Silent failure, log-and-continue, or catching without re-raising.
* Legacy/migration/temporary bridging code.
* Hardcoded secrets or credentials; use environment variables or secret management.

---

## Quick Checklist

* [ ] Greenfield mindset: no legacy/migration code.
* [ ] Strict typing (`mypy --strict`); no `Any` (or TODO-marked if unavoidable).
* [ ] DI explicit; no hidden globals or dynamic imports.
* [ ] Fail-fast on config/deps; helpful crash messages.
* [ ] Errors handled at owner layer only; otherwise propagate.
* [ ] Logging via loguru (`from loguru import logger as log`); no `print`.
* [ ] Linting/formatting via `ruff`.
* [ ] Resource-based interfaces; schema-first.
* [ ] Context managers for all resources; cleanup on every path.
* [ ] Happy-path tests + spec-defined negative paths; few high-signal checks.
* [ ] Tests are falsifiable — each would fail if target behavior were broken.
* [ ] Every new component is reachable from a production entry point.
* [ ] All call sites updated after renames/signature changes.
* [ ] New imports declared in dependency manifest.
* [ ] Comments/docstrings add non-obvious value only.
