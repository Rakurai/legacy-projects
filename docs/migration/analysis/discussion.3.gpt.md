## Topic 1: `game_act()` function signature

### Decision

Use a **flat, positional core signature** with an optional keyword-only escape hatch for rare overrides.

This is the one to standardize on:

```python
from enum import IntFlag, auto
from typing import Optional, Iterable
from evennia.objects.objects import DefaultCharacter, DefaultObject, DefaultRoom


class Audience(IntFlag):
    TO_CHAR = auto()
    TO_VICT = auto()
    TO_ROOM = auto()
    TO_NOTVICT = auto()
    TO_ALL = TO_CHAR | TO_VICT | TO_ROOM


def game_act(
    template: str,
    actor: Optional[DefaultCharacter],
    obj: Optional[DefaultObject] = None,
    victim: Optional[DefaultCharacter] = None,
    audience: Audience = Audience.TO_ROOM,
    obj2: Optional[DefaultObject] = None,
    *,
    origin: Optional[DefaultRoom] = None,
    recipients: Optional[Iterable[DefaultObject]] = None,
    msg_type: str = "action",
) -> None:
    """
    Render and deliver a legacy-compatible act() message.

    Core tokens:
        $n/$N  actor/victim name
        $e/$E  subject pronoun
        $m/$M  object pronoun
        $s/$S  possessive pronoun
        $p/$P  obj/obj2 short description
        $t     optional free-text insertion if supported later

    Audience routing:
        TO_CHAR, TO_VICT, TO_ROOM, TO_NOTVICT, TO_ALL

    Notes:
        - visibility filtering is internal
        - room defaults to actor.location unless origin is provided
        - recipients overrides audience-derived recipient discovery if provided
        - returns None
    """
    ...
```

This keeps the common call sites short while preserving the two rare escape hatches (`origin`, `recipients`) without forcing a context dataclass at every call site. That is consistent with the already-settled requirement that `game_act()` remain a legacy-shaped compatibility layer with one call per audience mode and internal routing/filtering. 

### Rationale

The remaining open item is the exact signature, not the behavior. That is explicitly what `CONSENSUS.md` leaves unresolved.

For this specific function, call-site density matters more than theoretical extensibility. `game_act()` will sit on hundreds of hot, repetitive call sites. A dataclass-heavy shape adds friction everywhere to solve edge cases that are uncommon. The Round 2 material already converged on a legacy-style compact call surface as the minimal viable messaging substrate.

The right compromise is:

* **positional core** for the 95% case,
* **keyword-only overrides** for the rare non-actor-location or custom-recipient case,
* **no return value**, because delivery count is not part of the behavioral contract and no downstream design depends on it. `CONSENSUS.md` defines exact message routing and visibility behavior, not counting semantics. 

### 1a. Call-site frequency

#### Example 1: simple room message — “Warrior leaves north.”

```python
game_act("$n leaves north.", actor=warrior, audience=Audience.TO_ROOM)
```

With a dataclass/context form, the same call becomes noisier:

```python
game_act(
    "$n leaves north.",
    ctx=ActContext(actor=warrior),
    mode=AudienceMode.TO_ROOM,
)
```

#### Example 2: combat hit message — actor, victim, weapon; three audiences

Actor view:

```python
game_act("Your slash with $p hits $N.", actor=warrior, obj=sword, victim=goblin, audience=Audience.TO_CHAR)
```

Victim view:

```python
game_act("$n's slash with $p hits you.", actor=warrior, obj=sword, victim=goblin, audience=Audience.TO_VICT)
```

Room view:

```python
game_act("$n's slash with $p hits $N.", actor=warrior, obj=sword, victim=goblin, audience=Audience.TO_NOTVICT)
```

#### Example 3: spell/wand message — caster, target, object

```python
game_act("$n's $p zaps $N.", actor=warrior, obj=wand, victim=goblin, audience=Audience.TO_NOTVICT)
game_act("Your $p zaps $N.", actor=warrior, obj=wand, victim=goblin, audience=Audience.TO_CHAR)
game_act("$n's $p zaps you.", actor=warrior, obj=wand, victim=goblin, audience=Audience.TO_VICT)
```

These are exactly the kind of repetitive call sites where extra `ctx=ActContext(...)` noise buys little.

### 1b. The `origin` / `recipients` question

Yes, there are real uses for both, but they are **edge cases**, not core arguments.

`origin` is useful for:

* messages emitted by room/area systems without a natural actor,
* reset/lifecycle announcements,
* trap/door/room-affect messages where the logical origin is the room, not a character.

`recipients` is useful for:

* tightly scoped custom deliveries,
* later admin/snoop/spectator extensions,
* temporary system-specific recipient sets that do not map cleanly to standard audience modes.

Those are real, but not common enough to justify a dataclass-first base API. They belong as keyword-only escape hatches.

### 1c. The return value question

Return `None`.

Recipient count is not part of the compatibility target, and there is no evidence in the settled contracts that callers need it. The messaging contract is about exact output, routing, and visibility, not observability of delivery counts. 

If diagnostics are needed later, expose them via logging or a debug wrapper, not the base API.

### Risks

The main risk is gradual signature creep: too many keyword-only extras turn the flat signature into an awkward hybrid. Mitigation: keep only `origin`, `recipients`, and `msg_type`; anything more should go into a separate helper, not the base function.

---

## Topic 2: Wave 1 vertical slice scope

`CONSENSUS.md` leaves only a few edge inclusions open: `wear/remove`, `say`, and character creation.

Here is the Wave 1 scope to lock:

| Action                                                       | Status                                                                                      |
| ------------------------------------------------------------ | ------------------------------------------------------------------------------------------- |
| Connect and log in (to a pre-created test character)         | **In scope**                                                                                |
| `look` (room description, exits, contents, other characters) | **In scope**                                                                                |
| Move through exits (`north`, `south`, etc.)                  | **In scope**                                                                                |
| `get` / `drop` (pick up and drop items)                      | **In scope**                                                                                |
| `inventory` (list carried items)                             | **In scope**                                                                                |
| `wear` / `remove` (equip and unequip)                        | **Deferred**                                                                                |
| `say` (local room speech)                                    | **In scope**                                                                                |
| `sleep` / `wake` (position changes + command gating)         | **In scope**                                                                                |
| Entity lookup: `get 2.sword`, partial matching               | **In scope**                                                                                |
| `kill goblin` (what response?)                               | **Deferred** — command absent or explicit dev message: “That command is not available yet.” |
| Full character creation flow (race/class/stats)              | **Deferred**                                                                                |
| Chat channels (gossip, etc.)                                 | **Deferred**                                                                                |
| `score` (character stat display)                             | **Deferred**                                                                                |

### Justification for the non-obvious choices

`wear/remove` → **Deferred**
Even though equipment is foundational longer-term, Wave 1 is supposed to validate the navigable world plus basic object manipulation, not the effective-stat/equipment integration path. `CONSENSUS.md` already treats exact Wave 1 edge details as still open, and the strongest prior Wave 2 vertical-slice definition did not require equip/unequip for acceptance.

`say` → **In scope**
This should be included because it is the cheapest live proof that `game_act()` works for a core local social message, and Wave 2 explicitly includes minimal communication after Wave 1 infrastructure. 

`score` → **Deferred**
It is tempting because the stat pipeline exists, but `score` invites premature decisions about final formatting, field selection, and legacy display parity. It is useful, but not necessary to prove the Wave 1 substrate.

### Add these two actions

| Action                               | Status       |
| ------------------------------------ | ------------ |
| `look <object>` / `look <character>` | **In scope** |
| `exits`                              | **In scope** |

Those are part of the actual “navigable world” proof and align with the stronger Round 2 Wave 1 sequence.

---

## Topic 3: Timing alternative — per-system schedulers with atomic transactions

### How Evennia’s transaction model actually works in practice

The important practical point is this: Evennia runs on Twisted’s event loop and uses Django’s ORM underneath. That does **not** automatically mean every `at_repeat()` callback gives you a strong, game-wide atomic round boundary.

A per-encounter `at_repeat()` can be made internally consistent for its own database writes if coded carefully, but that is weaker than the global-scheduler guarantee you already locked:

* one callback’s ORM work may be atomic at the DB level,
* but callback ordering across independent Scripts scheduled “at the same time” is not a gameplay contract,
* and Evennia’s object/Attribute caching means the code path can observe stale-in-memory assumptions unless access patterns are disciplined.

So the alternative is not “free atomic rounds.” It is “many local atomic-ish updates with cross-callback ordering still unspecified.”

### The observer problem concretely

Your example shows the actual weakness.

Case:

* room A: player + 3 NPCs in combat,
* adjacent room B: NPC casts an area spell affecting room A.

With the global scheduler, both events resolve in one authoritative tick order:

1. command flush,
2. violence phase,
3. character update,
4. object update,
5. area/system effects,
6. output flush, or whatever exact phase order you lock. 

With per-system schedulers:

* combat handler callback and NPC AI/spell callback are independent,
* whichever callback runs first becomes the de facto truth,
* the player-visible result can differ:

  * did the player take the combat hit before the area spell,
  * or after,
  * or did one effect kill a target before the other callback ran?

That is not just an implementation detail. It is observable parity drift.

The real issue is not only shared mutable entities. It is also **shared observers and shared transcripts**:

* who receives which messages first,
* whether “you are blasted by fire” appears before or after “the goblin hits you,”
* whether a bystander sees a consistent room-state snapshot.

### Would per-system scheduling integrate better with Evennia?

Superficially, yes:

* Evennia likes localized Scripts/handlers,
* local systems are easier to reason about in isolation,
* you avoid building something that looks like a classic Diku main loop.

But that advantage is mostly architectural aesthetics unless the global scheduler proves painful in practice.

The actual integration question is narrower: does one authoritative scheduler conflict with Evennia’s normal object model? I do not see strong evidence that it does. `CONSENSUS.md` already frames the chosen scheduler as a thin phase dispatcher, not a god-object owning all game logic. 

So the trade is:

* per-system schedulers are more idiomatic locally,
* global scheduling is more faithful globally.

For this project, fidelity pressure is stronger than idiomatic purity.

### What is the practical risk of the global scheduler approach?

There is some real risk, but it looks manageable rather than existential.

The practical risks are:

**1. It may feel like reimplementing Diku inside Evennia.**
That is mostly a maintainability/style concern, not a correctness blocker.

**2. It may interact awkwardly with built-in Evennia timers/scripts already expecting autonomous timing.**
If a subsystem quietly introduces its own timers, you can get split-brain timing. That is a governance problem: forbid authoritative gameplay timing outside the scheduler.

**3. Performance and bookkeeping complexity.**
A sloppy global scheduler that scans the whole world every pulse would be bad. But that is not the design you settled. The settled design is a global authoritative clock invoking subsystem-owned handlers, not centralizing all behavior itself. 

**4. Debugging phase-order bugs can be subtle.**
Because everything is intentionally phase-coupled, mistakes in queueing or flush boundaries can create hard-to-see order errors.

### Bottom line on the alternative

The alternative is worth **prototype evaluation**, but only as a stress test for implementation ergonomics, not as a likely replacement on first principles.

The strongest argument against it is not “transactions are weak.” It is:

* local atomicity does not solve **cross-system ordering**,
* and cross-system ordering is one of the explicit load-bearing fidelity requirements already captured in the consensus. 

The strongest argument for prototyping it is:

* it may reveal a narrower implementation of the global-scheduler idea that integrates more cleanly with Evennia’s Script machinery without giving up authoritative phase order.
