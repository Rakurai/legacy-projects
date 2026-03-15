# PYDANTIC.md — Pydantic v2 Directives

Audience: expert coding agent. Scope: strict Pydantic v2 usage; v1 patterns forbidden.
Schemas provide strong, schema-first contracts; complements [FASTAPI.md], [SQLMODEL.md], and [PATTERNS.md].

---

## Core Mandate

**All code MUST use Pydantic v2 patterns. v1 imports, decorators, or methods are forbidden.**
No defensive programming, no fallbacks, no legacy accommodations. Schemas are trusted contracts.

---

## Allowed vs Forbidden (v2 Enforcement)

| Concern                | ✅ v2 Pattern                                           | ❌ v1 Anti-Pattern              |
| ---------------------- | ------------------------------------------------------ | ------------------------------ |
| Config                 | `model_config = ConfigDict(...)`                       | `class Config:`                |
| Field validation       | `@field_validator("field")`                            | `@validator("field")`          |
| Cross-field validation | `@model_validator(mode="after")`                       | `@root_validator`              |
| Export                 | `.model_dump()`, `.model_dump_json(indent=2)`          | `.dict()`, `.json()`           |
| Parsing                | `Model.model_validate(obj)` / `.model_validate_json()` | `.parse_obj()`, `.parse_raw()` |
| Defaults               | `Field(default_factory=...)`                           | `datetime.utcnow()`            |

---

## Imports

**Rules**

* Import only from `pydantic` root.
* Allowed imports: `BaseModel`, `Field`, `ConfigDict`, `field_validator`, `model_validator`.
* No deprecated submodules.

---

## Datetime & Defaults

**Rules**

* Always use `datetime.now(timezone.utc)`; never `datetime.utcnow()`.
* Store timezone-aware datetimes only.
* Use `default_factory` for dynamic defaults (timestamps, UUIDs).

---

## Field Definition Patterns

**Rules**

* Use declarative constraints (`min_length`, `ge`, `pattern`, etc.) instead of manual checks.
* Use `Literal[...]` or enums for constrained strings.
* No sentinel values; constraints must be explicit.

---

## Validation Strategy

**Principle**: Normalize and enforce invariants, not defensive re-checks.

**Rules**

* Use `@field_validator` for trimming, coercion, normalization.
* Use `@model_validator(mode="after")` for invariants across fields.
* Do not repeat checks already enforced by typing/constraints.
* Never re-validate models manually — rely on `model_validate`.
* Raise `ValueError` for schema-level validation failures; they surface as HTTP 422.

---

## Data Export / Serialization

**Rules**

* Use `.model_dump()` for Python-native output.
* Use `.model_dump_json(indent=2)` for readable JSON; omit `indent` only when storage-sensitive.
* Use `exclude_none=True` only when omission is semantically meaningful.
* For partial updates, define explicit `Patch` schemas.

---

## Schema Composition & Organization

**Rules**

* One functional unit per file.
* Group small, cohesive variants (request/response).
* Avoid deep inheritance; prefer composition or duplication.
* Cross-model validation is **forbidden** in schemas (no DB lookups or external IO). Enforce invariants in services.

---

## Immutability

**Rules**

* Use `ConfigDict(frozen=True)` only when immutability adds real value.
* Never mutate models in place; use `.model_copy(update={...})`.

---

## Error Classification

**Rules**

* Validation errors are surfaced automatically; never wrap them.
* Business rule violations belong in services, not validators.
* Functions may return `Optional[T]` only when explicit in the signature.

---

## Any Typing

**Principle**: Contracts must be explicit.

**Rules**

* Never use `Any`.
* If absolutely unavoidable, annotate with `Any` and add `# TODO refine type`.

---

## Anti-Patterns

* Legacy v1 APIs: `@validator`, `@root_validator`, `.dict()`, `.json()`, `.parse_obj()`, `.parse_raw()`.
* Defaults using `datetime.utcnow()`.
* Bare `except Exception` in validators.
* Defensive re-checks already covered by types.
* Silent fallbacks of any kind.

---

## Quick Checklist

* [ ] Pydantic v2 only; no legacy APIs.
* [ ] Config via `ConfigDict`; no `class Config`.
* [ ] Validators enforce invariants/normalization only.
* [ ] Datetime defaults via `default_factory=datetime.now(timezone.utc)`.
* [ ] `.model_dump()` / `.model_dump_json(indent=2)` only.
* [ ] Imports only from `pydantic` root.
* [ ] Strict typing; no `Any`.
* [ ] No fallback/defensive checks.
* [ ] Cross-model validation forbidden inside schemas.
