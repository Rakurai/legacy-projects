# Round 3: Closing Decisions

---

## Topic 1: `game_act()` Function Signature

### Decision

**Option 1 (flat positional arguments), with two modifications: rename `victim` to `target` for accuracy, and add a `$t` text parameter.** No dataclass wrapper, no return value, no `origin`/`recipients` in the base signature.

### Rationale

#### 1a. Call-site frequency

`game_act()` will be called 500+ times. Every extra keyword, every dataclass construction, every named parameter is boilerplate multiplied hundreds of times. The dominant use cases are simple — the signature must optimize for them.

**Three call-site examples under each option:**

**Simple room message: "Warrior leaves north."**

```python
# Option 1 (flat)
game_act("$n leaves $t.", actor, audience=Audience.TO_ROOM, text="north")

# Option 2 (dataclass)
game_act("$n leaves $t.", ctx=ActContext(actor=actor, text="north"), mode=AudienceMode.TO_ROOM)
```

**Combat hit with actor, victim, weapon (three audiences):**

```python
# Option 1 (flat) — three calls, one per audience
game_act("Your slash hits $N.", actor, target=victim, audience=Audience.TO_CHAR)
game_act("$n's slash hits you.", actor, target=victim, audience=Audience.TO_VICT)
game_act("$n's slash hits $N.", actor, target=victim, audience=Audience.TO_ROOM)

# Option 2 (dataclass) — same three calls but with ctx construction
ctx = ActContext(actor=actor, target=victim)
game_act("Your slash hits $N.", ctx=ctx, mode=AudienceMode.TO_CHAR)
game_act("$n's slash hits you.", ctx=ctx, mode=AudienceMode.TO_VICT)
game_act("$n's slash hits $N.", ctx=ctx, mode=AudienceMode.TO_ROOM)
```

**Spell message with caster, target, and object: "Warrior's wand zaps the goblin."**

```python
# Option 1 (flat)
game_act("$n's $p zaps $N.", actor, obj=wand, target=goblin, audience=Audience.TO_ROOM)

# Option 2 (dataclass)
game_act("$n's $p zaps $N.", ctx=ActContext(actor=actor, target=goblin, obj1=wand), mode=AudienceMode.TO_ROOM)
```

Option 1 is shorter in every case. The dataclass adds a construction step that provides no benefit — the fields are the same, just wrapped. In the combat case, the dataclass *can* be reused across the three calls, which saves repeating `actor` and `target`. But that's a minor win at 500+ call sites where most calls are single-audience.

Note that in the combat case with legacy `act()`, the three audience variants are typically three separate `act()` calls with different format strings, because the actor sees "You hit..." while the room sees "Warrior hits..." — these are *different templates*, not one template with audience routing. This is the legacy pattern and the natural porting pattern. One call per audience, different template per audience.

#### 1b. The `origin` / `recipients` question

**`origin` (explicit room):** The room should be derived from `actor.location` in 99%+ of cases. The exceptions are: (a) messages sent to a room the actor is not in (e.g., "You hear a scream from the north" sent to an adjacent room), and (b) messages during room transitions where the actor has already moved. These are rare — maybe 10-20 call sites out of 500+. They don't belong in the base signature. For those cases, a separate helper function (`game_act_to_room(room, format_str, ...)`) or an optional `room` kwarg is sufficient.

**`recipients` (override list):** Used for snoop forwarding and arena spectating, both of which are deferred. No current use case. Don't add it to the base signature. When snoop/spectating are specced, they extend the delivery mechanism internally, not via caller-supplied recipient lists.

Neither `origin` nor `recipients` belongs in the base signature.

#### 1c. The return value question

No caller needs the recipient count. A caller that sends a combat message doesn't branch on how many people received it. A caller that needs to know "did anyone hear this?" is doing something unusual enough to warrant its own query (`any(can_see(char, actor) for char in room.contents)`). Return `None`.

#### 1d. Committed signature

```python
from enum import IntFlag
from typing import Optional


class Audience(IntFlag):
    TO_CHAR  = 1   # actor only
    TO_VICT  = 2   # target only
    TO_ROOM  = 4   # all in room except actor and target
    TO_ALL   = 7   # everyone in room


def game_act(
    format_str: str,
    actor: "LivingMixin",
    target: "LivingMixin | None" = None,
    obj: "GameItem | None" = None,
    obj2: "GameItem | None" = None,
    text: str | None = None,
    audience: Audience = Audience.TO_ROOM,
) -> None:
    """
    Format and deliver a legacy-compatible act() message.

    Tokens resolved per-recipient:
        $n → actor name (or "someone" if invisible to recipient)
        $N → target name (or "someone" if invisible)
        $e/$E → subject pronoun for actor/target (he/she/it)
        $m/$M → object pronoun (him/her/it)
        $s/$S → possessive pronoun (his/her/its)
        $p → obj short description (or "something" if invisible)
        $P → obj2 short description (or "something" if invisible)
        $t → text (literal string, no visibility check)
        $% → verb suffix ("s" for third-person, "" for second-person "you")

    Audience routing:
        TO_CHAR → actor receives ($n → "you", verbs adjusted via $%)
        TO_VICT → target receives ($N → "you")
        TO_ROOM → all in actor.location except actor and target

    Visibility:
        Per-recipient: can_see(recipient, entity) checked for each $n/$N/$p/$P.
        If invisible → name replaced with "someone"/"something".
        If actor invisible to room recipient → message suppressed entirely
        for that recipient (TO_ROOM only).
    """
```

**Parameter ordering rationale:** `format_str` and `actor` are always needed. `target`, `obj`, `obj2`, and `text` are positional optionals in rough order of frequency — combat messages have targets more often than objects. `audience` is last because it defaults to the most common mode (TO_ROOM).

### Risks

The positional API could lead to argument-order mistakes when `target` and `obj` are both present (e.g., accidentally passing an object as `target`). Mitigation: type annotations catch this at static analysis time (`LivingMixin` vs `GameItem`). In practice, legacy `act()` has the same positional pattern and thousands of call sites manage it without issue.

The lack of `origin` means the ~10-20 cross-room messaging call sites need a separate helper. That's acceptable — a `game_act_to_room(room, format_str, ...)` variant is trivial to add when those call sites are encountered in Wave 3+.

---

## Topic 2: Wave 1 Vertical Slice Scope

### Decision

| Action | Status | Justification |
|--------|--------|---------------|
| Connect and log in (pre-created test character) | **In scope** | Baseline for all testing. Simplified flow — admin-created characters, no full creation wizard. |
| `look` (room description, exits, contents, characters) | **In scope** | Core navigation proof. Tests messaging layer, display hooks, visibility. |
| Move through exits (`north`, `south`, etc.) | **In scope** | Core navigation proof. Tests room/exit typeclasses, position enforcement (must be standing). |
| `get` / `drop` (pick up and drop items) | **In scope** | Core object interaction proof. Tests entity lookup, GameItem typeclass, messaging. |
| `inventory` (list carried items) | **In scope** | Trivial once `get` works. Validates inventory display formatting. |
| `wear` / `remove` (equip and unequip) | **Deferred** | Requires the equipment handler to actually modify stat aggregation — which pulls in stat pipeline integration beyond the Wave 1 contract proof. The stat pipeline is *implemented* in Wave 1, but full equipment↔stat integration is Wave 2/3 territory. `get`/`drop` is sufficient for the object interaction proof. |
| `say` (local room speech) | **In scope** | Trivially simple (`game_act("$n says '$t'", actor, text=message, audience=Audience.TO_ROOM)`). Proves messaging for communication, not just action descriptions. |
| `sleep` / `wake` (position changes + command gating) | **In scope** | Proves the position system contract: `sleep` → position changes → `north` fails with "You can't do that while sleeping." → `wake` → movement succeeds. This is explicitly what the position infrastructure is for. |
| Entity lookup: `get 2.sword`, partial matching | **In scope** | Proves the entity lookup adapter. Must work for the object interaction proof to be meaningful. |
| `kill goblin` (what response?) | **In scope as stub** | Command exists but returns: "You can't do that yet." Clear dev-mode message. Not partial combat. Not "command not found" (which would suggest it was never planned). |
| Full character creation flow | **Deferred** | Separate mini-spec. Wave 1 uses admin-created test characters. The legacy creation state machine (race, class, stat rolling, skill group selection) is its own dossier. |
| Chat channels (gossip, etc.) | **Deferred** | Requires channel infrastructure. `say` covers the messaging proof for Wave 1. |
| `score` (character stat display) | **In scope** | Validates stat pipeline integration. The player should see their base stats, HP/mana/move, and other derived values. This is the most direct proof that the stat pipeline *works* — a player types `score` and sees numbers that match what the legacy system would show for the same character configuration. If `score` shows wrong values, the stat pipeline contract is broken. |

**Additional actions that must be in Wave 1:**

| Action | Justification |
|--------|---------------|
| `exits` (list available exits) | Trivial companion to `look`. Many players use `exits` more than reading the room description for navigation. |
| `who` (list online players) | Simple query against connected sessions. Proves the Account/Character relationship is working. Minimal effort. |

### Summary

Wave 1 proves: login → navigate → inspect → interact with objects → see other entities → position enforcement → stat display → basic communication. This validates all seven infrastructure contracts in a player-visible way.

Wave 1 does NOT prove: combat, affects, equipment stat modification, spells, skills, NPC behavior, resets, channels, economy, quests, character creation.

### Risk

Including `score` creates a risk that the stat pipeline display format becomes a time sink (legacy `score` output is heavily formatted with alignment, color codes, and derived calculations). Mitigation: Wave 1 `score` shows correct *values* in a simplified format. Legacy-matching `score` display formatting is a Wave 2 refinement.

---

## Topic 3: Timing Alternative Analysis (Advisory)

### How Evennia's transaction model works in practice

Evennia uses Django's ORM backed by a database (default SQLite, configurable to PostgreSQL). Django transactions wrap database operations — `@transaction.atomic` blocks, or the ORM's default autocommit mode where each `.save()` is its own transaction. Evennia's `AttributeHandler` adds a caching layer: Attributes are loaded into memory on first access and subsequent reads hit the cache, not the database. Writes go to both cache and database.

A `Script.at_repeat()` callback runs inside Twisted's reactor thread. It is *not* automatically wrapped in a database transaction — it runs in autocommit mode by default, meaning each individual Attribute write is its own transaction. To get atomicity for a full combat round, you'd need to explicitly wrap the resolution in `@transaction.atomic`. This is possible but not the default.

**Can we guarantee atomicity of a full round resolution?** Yes, if we explicitly wrap it: `with transaction.atomic(): handler.resolve_round()`. All Attribute writes within that block become a single transaction. If an exception occurs, the database state rolls back. However, the *in-memory cache* does not roll back — Evennia's `AttributeHandler` cache is updated immediately, not transactionally. This means a partial failure could leave in-memory state inconsistent with the database, requiring a cache invalidation/reload. This is a real implementation concern, not a theoretical one.

### The observer problem concretely

**Scenario:** Room A has 3 NPCs fighting a player. An NPC in adjacent Room B casts an area spell affecting Room A.

**With the global scheduler:** The violence phase processes all encounters. Room A's combat round resolves. Then (in the same tick or a subsequent phase), Room B's NPC AI fires and casts the area spell. The order is deterministic: combat in A completes before the spell from B applies. The player sees a coherent sequence — first their combat round output, then the spell effect.

**With per-system schedulers:** Room A's CombatHandler and Room B's NPC AI handler are independent timers (or independent `at_repeat()` callbacks). If both fire in the same reactor iteration, Twisted provides no ordering guarantee. The player might see the area spell damage interleaved with their combat round output. Worse, if the area spell kills the player during a combat round that's concurrently resolving, the combat handler operates on stale state.

The "disjoint entity sets" argument works when encounters truly don't overlap. But MUD gameplay regularly produces overlap: area-of-effect spells, characters fleeing between rooms, NPCs that assist from adjacent rooms, `yell` commands heard across areas. The overlap cases are not rare edge cases — they're normal gameplay that a system planning assumption can't hand-wave away.

### Would per-system scheduling integrate better with Evennia?

In one sense, yes — Evennia's Script system is designed for per-object or per-system timers, and the `TickerHandler` is built for independent subscriptions. A global scheduler is an alien concept in Evennia's architecture. It's not that Evennia *prevents* it (a Script ticking at 100ms is just a Script), but it bypasses the patterns that Evennia developers expect: per-object scripts, hook-driven behavior, async-native design.

In another sense, the integration is fine. The global scheduler is one Script. It ticks. It calls handlers. Those handlers use Evennia's handler pattern (`@lazy_property` handlers on typeclasses) for all state management. The scheduler doesn't replace Evennia's infrastructure — it coordinates it. It's the same role that Diku's `game_loop_unix()` plays relative to its subsystems: a thin orchestrator that calls into domain-specific code.

The specific Evennia mechanisms it could conflict with:

- **Script persistence and restart.** Evennia Scripts survive server restarts and resume automatically. A global scheduler Script must handle restart gracefully — re-registering all active encounters, resetting the pulse counter to a consistent state. This is solvable but must be explicitly designed.
- **`utils.delay()` and `TickerHandler` interactions.** If any game code uses Evennia's built-in timing utilities (which new developers contributing to the project will instinctively reach for), those timers are independent of the global scheduler and will violate the ordering guarantees. This requires documentation discipline: "all periodic game behavior must go through the scheduler, never through raw `delay()` or `TickerHandler`."
- **Portal/Server separation.** Evennia runs two processes: a Portal (handles connections) and a Server (runs game logic). The global scheduler runs in the Server process. This is fine — all game logic runs there — but hot-reload (`@reload`) restarts the Server process, and the scheduler must survive this.

### Practical risk of the global scheduler

The risk is **moderate but manageable.** The global scheduler does not conflict with any Evennia mechanism in a way that prevents it from working. The risks are:

1. **Developer confusion.** Evennia's documentation and community tutorials all teach per-object Scripts and `TickerHandler`. A global scheduler is unfamiliar. New contributors will reach for the wrong tools. Mitigation: clear documentation, code review standards, and a "timing rules" section in the project contributing guide.

2. **100ms tick overhead.** The scheduler ticks 10 times per second even when nothing is happening. Each tick checks `pulse_count % N` for each phase — trivially cheap, but it's work that a demand-driven system wouldn't do. For a MUD with 50-100 concurrent players and a few hundred NPCs, this overhead is negligible. It would only matter if the game scaled to thousands of concurrent entities, which is not the target.

3. **Restart/reload correctness.** The scheduler must reconstruct its state after a server restart or `@reload`. Encounter membership, pulse counter, area ages — all must be either persisted or reconstructable. This is additional engineering work that per-system independent timers wouldn't require (each Script persists its own state independently).

4. **Testability.** A global scheduler is harder to unit test than independent handlers because you can't tick one subsystem without ticking all of them. Mitigation: the scheduler calls phase entrypoints that are independently testable. Integration tests tick the scheduler; unit tests call handlers directly.

### Assessment

The global scheduler is the safer choice for fidelity. The per-system alternative could work in theory, but the observer overlap problem is real and the engineering cost of solving it (locks, transaction boundaries, ordering protocols between independent schedulers) exceeds the cost of running a simple global tick. The global scheduler's risks are all manageable with discipline and documentation.

If the global scheduler turns out to integrate poorly with Evennia during Wave 1 implementation — specifically, if Script restart behavior is unreliable or the 100ms tick causes measurable performance issues — the per-encounter CombatHandler fallback (from my Round 2 proposal) remains viable for combat specifically, since combat encounters *are* mostly disjoint. But the global scheduler should be the first implementation attempt because it solves the ordering problem by construction rather than by engineering around it.