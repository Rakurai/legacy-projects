# SQLMODEL.md — Best Practices

Concise rules for SQLModel usage in PoC backends.
Voice: imperative, rule-based. Audience: expert coding agent.

References:

* [PATTERNS.md] for type safety, fail-fast, no fallbacks, testing.
* [INTERFACES.md] for API contracts.

---

## Core Principles

* Models define **database tables only** — no business logic.
* Services orchestrate repositories; repositories handle DB access.
* Transactions are explicit and owned by the service layer.
* All models must be strictly typed (`mypy --strict` compliant).
* No legacy accommodations, migrations, or temporary bridging code.

---

## Model Definitions

**Principle**: Tables are explicit, minimal, and fully typed.

**Rules**

* Use `SQLModel` with `table=True` for tables.
* Use base classes only for common fields (timestamps, ownership).
* Always declare `id: str = Field(default_factory=uuid4, primary_key=True)`.
* Explicitly type all fields; no `Any`.
* Use `default_factory` or explicit `nullable=False`; never implicit defaults.
* Apply Pydantic v2 validation for constraints; avoid property hacks.

---

## Relationships

**Principle**: Define explicit, shallow relationships.

**Rules**

* Use `Relationship` where navigation is required.
* Always keep foreign keys explicit.
* Define both sides of relationships when needed.
* Use forward refs (`"Collection"`) for type hints to break circular imports.
* Avoid deep relationship loading in endpoints; services must orchestrate.

---

## Repository Pattern

**Principle**: Encapsulate persistence in repositories.

**Rules**

* Each table has a repository (`CollectionRepository`).
* Repositories expose CRUD + simple queries.
* Repositories never own transactions or commit.
* Explicitly annotate all repository signatures.
* Return `Model | None` only when annotated.
* No fallback queries, no silent error masking.

**Correct Example**

```python
class CollectionRepository(BaseRepository[Collection]):
    def get_by_name(self, name: str, session: Session) -> Collection | None:
        return session.exec(select(Collection).where(Collection.name == name)).first()
```

---

## Service Layer & Transactions

**Principle**: Services own lifecycle and transaction scope.

**Rules**

* Services call repositories inside explicit session contexts.
* Services decide commit/rollback.
* Use `async with db_manager.session() as session:` for scoping.
* Fail fast on integrity errors; never swallow exceptions.

---

## Complex Query Pattern (Join + Aggregate)

**Principle**: Push heavy lifting into SQL, not Python loops.

**Example**

```python
from sqlmodel import select, func

class MediaStats(SQLModel):
    collection_id: str
    video_count: int

class MediaRepository(BaseRepository[Media]):
    def counts_by_collection(self, session: Session) -> list[MediaStats]:
        stmt = (
            select(Media.collection_id, func.count(Media.id).label("video_count"))
            .group_by(Media.collection_id)
        )
        rows = session.exec(stmt).all()
        return [MediaStats(collection_id=c, video_count=v) for c, v in rows]
```

**Rules**

* Use SQL aggregation (`func.count`, `func.sum`) instead of in-Python counting.
* Return typed DTOs/structs instead of raw tuples when shapes differ.
* Keep joins explicit; never rely on lazy-loading in tight loops.

---

## Indexing & Performance

**Principle**: Index only what you query.

**Rules**

* Define indexes for high-frequency lookups (`user_id`, `collection_id`).
* Avoid premature optimization — add only if queries require it.
* No ORM-level caching layers in PoC.

---

## Discriminated Union Fields

**Principle**: Store typed Pydantic unions as JSON while preserving type safety.

**Use Case**: Polymorphic configuration that requires both persistence and validation.

**Pattern**

```python
# 1. Extend base models with discriminator
class ConfigA(BaseConfig):
    kind: Literal["a"] = "a"

class ConfigB(BaseConfig):
    kind: Literal["b"] = "b"

# 2. Union + TypeAdapter for validation  
ConfigUnion = Annotated[ConfigA | ConfigB, Field(discriminator="kind")]
_CONFIG_ADAPTER = TypeAdapter[ConfigUnion]

# 3. SQLModel with JSON backing + property interface
class Entity(SQLModel, table=True):
    config_json: dict = Field(sa_column=Column("config", JSON))
    
    @property
    def config(self) -> ConfigUnion:
        return _CONFIG_ADAPTER.validate_python({"kind": self.type, **self.config_json})
    
    @config.setter
    def config(self, value: ConfigUnion | dict) -> None:
        if isinstance(value, dict):
            value = _CONFIG_ADAPTER.validate_python(value)
        self.config_json = value.model_dump()
```

**Benefits**: Typed interface, automatic serialization, Pydantic validation, polymorphic storage.

---

## Anti-Patterns

* Returning ORM objects directly in API responses.
* Embedding business logic in models.
* Repositories committing or managing sessions.
* Using `Any` for fields.
* Deep/eager relationship loading in endpoints.
* Legacy migrations, temporary code, or defensive checks.

---

## Out-of-Scope (PoC Deferral)

The following are explicitly out of PoC scope — do not implement:

* Alembic migrations.
* Read replicas / multi-writer setups.
* Sharding or partitioning.
* Query/result caching.
* Bulk ingestion pipelines.
* SQLAlchemy event hooks beyond trivial timestamping.

---

## Quick Checklist

* [ ] Models use `SQLModel` with `table=True`.
* [ ] UUID primary keys via `default_factory`.
* [ ] Explicit typing everywhere; no `Any`.
* [ ] Relationships explicit and shallow.
* [ ] Repositories encapsulate DB access, never commit.
* [ ] Services own transaction boundaries.
* [ ] Queries explicit; no ORM loops for aggregation.
* [ ] Indexes only for active queries.
* [ ] No ORM objects returned in API.
* [ ] No out-of-scope scaling features.
