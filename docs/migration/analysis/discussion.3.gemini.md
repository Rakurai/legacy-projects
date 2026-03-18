This analysis concludes the final architectural alignment for Wave 1. By settling the messaging signature and narrowing the vertical slice, we transition from theoretical planning to implementation-ready specifications.

-----

## Topic 1: `game_act()` Function Signature

### Decision

Adopt **Option 1 (Claude-style)**: A flat positional signature with an `Audience` bitflag.

```python
def game_act(
    template: str,
    actor: DefaultCharacter,
    obj: Optional[DefaultObject] = None,
    victim: Optional[DefaultCharacter] = None,
    audience: Audience = Audience.TO_ROOM,
    obj2: Optional[DefaultObject] = None,
) -> None:
    ...
```

### Rationale

  * **Ergonomics and Porting Velocity:** `game_act()` is the most frequently called function in the codebase[cite: 11]. Requiring a `ctx=ActContext(...)` wrapper for every call creates significant boilerplate. Positional arguments allow developers to port legacy `act()` calls with minimal modification[cite: 11].
  * **Positional Safety:** While keyword-only arguments prevent argument swapping, the order (Actor, Object, Victim) is deeply ingrained in MUD development logic. The cognitive load of using a dataclass for every single room message outweighs the safety benefits[cite: 11].
  * **Audience IntFlag:** Using an `IntFlag` (e.g., `TO_ROOM | TO_VICT`) is more expressive and allows for multi-audience routing in a single call without complex list structures[cite: 11].

### 1a. Call-site Examples

| Case | Call-site Code |
| :--- | :--- |
| **Simple Room** | `game_act("$n leaves north.", ch)` |
| **Combat Hit** | `game_act("Your $p hits $N.", ch, weapon, victim, Audience.TO_CHAR)`<br>`game_act("$n's $p hits you.", ch, weapon, victim, Audience.TO_VICT)`<br>`game_act("$n's $p hits $N.", ch, weapon, victim, Audience.TO_NOTVICT)` |
| **Spell/Wand** | `game_act("$n's $p zaps $N.", ch, wand, victim, Audience.TO_ALL)` |

### 1b. The `origin` / `recipients` Question

The explicit `origin` (room) and `recipients` list are **deferred** to a specialized internal `_dispatch_act()` function or optional keyword arguments[cite: 11]. In 95% of cases, the room is `actor.location`. For edge cases (e.g., long-distance shouts or remote scrying), the signature can support optional `**kwargs`, but they should not clutter the primary interface[cite: 11].

### 1c. The Return Value Question

**None.** Callers rarely need to know the recipient count; they only need the side effect of message delivery[cite: 11]. If a count is required for specific logic (e.g., "Your shout was heard by 5 people"), a separate utility can be used.

-----

## Topic 2: Wave 1 Vertical Slice Scope

Wave 1 is complete when a player can navigate and interact with the world using the foundational infrastructure (Stat Pipeline, Messaging, Timing)[cite: 11].

| Action | Status | Justification |
| :--- | :--- | :--- |
| **Login** | **In Scope** | Essential to enter the test environment[cite: 11]. |
| **`look`** | **In Scope** | Primary test for Messaging visibility tokens and Entity Lookup[cite: 11]. |
| **Move** | **In Scope** | Tests Position rules and basic Room/Exit typeclasses[cite: 11]. |
| **`get` / `drop`** | **In Scope** | Validates `GameItem` typeclass and Inventory handling[cite: 11]. |
| **`inventory`** | **In Scope** | Essential for item state verification[cite: 11]. |
| **`wear` / `remove`** | **In Scope** | **Critical:** Must test Stat Pipeline aggregation from equipment[cite: 11]. |
| **`say`** | **In Scope** | Simplest test for `TO_ROOM` messaging[cite: 11]. |
| **`sleep` / `wake`** | **In Scope** | Validates Command Gating and Position state persistence[cite: 11]. |
| **Entity lookup** | **In Scope** | Must support `2.sword` and partial matches per legacy parity[cite: 11]. |
| **`kill goblin`** | **Deferred** | Combat is a Wave 4 deliverable. Wave 1 should return a "Not Implemented" stub message[cite: 11]. |
| **Char Creation** | **Deferred** | Use pre-created test characters to bypass UI/State complexity[cite: 11]. |
| **Chat Channels** | **Deferred** | Global messaging is separate from the `game_act` room logic[cite: 11]. |
| **`score`** | **In Scope** | Essential to verify the Stat Pipeline's effective values[cite: 11]. |

-----

## Topic 3: Timing Alternative Analysis

### Per-System Schedulers vs. Global Runtime

The alternative of using per-system schedulers with atomic transactions presents several challenges when viewed through the lens of Evennia's architecture and MUD fidelity[cite: 9, 11]:

  * **Evennia's Transaction Model:** Evennia relies on Django's ORM, which is typically autocommit. While `transaction.atomic` can wrap complex logic, Attribute changes are often cached and saved asynchronously by Evennia's handlers[cite: 11]. A per-encounter `CombatHandler` resolving a round might still conflict with a concurrent `AffectHandler` ticking on the same character if they are in different reactor callbacks[cite: 11].
  * **The Observer Consistency Problem:** If an Area Spell resolves in one transaction and a Combat Round in another, a player in the room might receive the "Fireball hits everyone" message *between* two lines of a combat round's output[cite: 11]. In legacy Diku, these are phase-locked; the fireball happens, then the violence resolves[cite: 9]. Per-system schedulers make this ordering non-deterministic.
  * **Native Integration:** Evennia's "native" way to handle periodic tasks is through `Scripts`[cite: 11]. The Global `RuntimeScheduler`[cite: 9] is essentially a single authoritative `Script` that orchestrates other systems. This is more "Evennia-native" than multiple drifting scripts that require complex cross-transaction locking to maintain phase parity.
  * **Practical Risk:** The risk of the Global Scheduler is **latency jitter** if a single pulse (100ms) becomes too "heavy"[cite: 11]. However, modern hardware handles MUD logic loops (even for hundreds of NPCs) in sub-millisecond time. The "mismatch" is theoretical; the practical benefit of deterministic execution order outweighs the overhead of a central tick[cite: 11].
