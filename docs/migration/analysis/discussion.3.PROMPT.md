# Discussion Round 3: Closing the Last Open Decisions

> **For:** A third-round review session. You have access to the full discussion
> history (R1 prompt + 3 responses, R2 prompt + 3 responses) and the new
> `CONSENSUS.md` document recording what has been locked down.
>
> **What happened:** Rounds 1–2 settled the workflow, ordering, typeclass
> strategy, object strategy, messaging concept, spell approach, contract registry
> format, fidelity definition, stub rules, and spec granularity. The timing
> architecture was resolved by human decision between rounds: **single global
> scheduler** (see CONSENSUS.md §3.5). See CONSENSUS.md for the full record.
>
> **What remains open:** One architectural decision (`game_act()` signature) and
> one scope question (Wave 1 acceptance criteria), and one advisory topic
> (timing alternative). This round closes the first two; the third is for
> discussion only.

---

## Settled Decisions (do not re-argue)

Everything in CONSENSUS.md §1–§4 is locked. In particular:

- LivingMixin + PlayerCharacter/NPC split
- Single GameItem typeclass with typed payloads
- Custom `game_act()` with legacy token vocabulary (not FuncParser)
- **Global RuntimeScheduler as the working assumption** — one tick at pulse
  quantum, subsystem phases in fixed legacy order, encounter handlers invoked by
  scheduler. See CONSENSUS.md §3.5 for the alternative under consideration.
- Framework + pattern catalog for spells
- Contract registry as versioned YAML in `contracts/`
- Stat pipeline, messaging, and timing must be implemented (not stubbed) before
  downstream game-system specs
- Five-wave migration ordering
- Fidelity = player-visible parity with exact formulas/text/timing

---

## Topic 1: `game_act()` Function Signature

Two competing signatures from Round 2:

**Option 1 (Claude):** Flat positional arguments, IntFlag for audience.
```python
def game_act(
    format_str: str,
    actor: DefaultCharacter,
    obj: Optional[DefaultObject] = None,
    victim: Optional[DefaultCharacter] = None,
    audience: Audience = Audience.TO_ROOM,
    obj2: Optional[DefaultObject] = None,
) -> None
```

**Option 2 (GPT):** Context dataclass, keyword-only arguments, returns count.
```python
def game_act(
    template: str,
    *,
    ctx: ActContext,
    mode: AudienceMode,
    origin: GameRoom | None = None,
    recipients: Iterable[DefaultObject] | None = None,
    msg_type: str = "action",
) -> int
```

The behavioral contract is agreed (see CONSENSUS.md §3.4). The question is
purely about the call-site ergonomics and extensibility of the API.

Address:

### 1a. Call-site frequency

`game_act()` will be called hundreds of times across the codebase — every
command, every spell, every combat message. The signature directly affects how
much boilerplate each call site requires. Which signature produces cleaner call
sites for the common cases?

Show 3 concrete call-site examples:
- A simple room message: "Warrior leaves north."
- A combat hit message with actor, victim, and weapon: "Your slash hits the goblin."
  (three audiences: actor, victim, room)
- A spell message with caster, target, and object: "Warrior's wand zaps the goblin."

### 1b. The `origin` / `recipients` question

GPT's signature includes `origin` (explicit room) and `recipients` (override
recipient list). Claude's derives room from `actor.location` implicitly. Are
there real use cases where the room or recipient list must be overridden? If so,
which — and are they common enough to be in the base signature vs. a separate
function?

### 1c. The return value question

Claude returns None. GPT returns recipient count. Does any caller actually need
the count? If not, None is simpler.

### 1d. Commit to one signature.

---

## Topic 2: Wave 1 Vertical Slice Scope

CONSENSUS.md lists this as needing resolution. The three responses mostly agree
but differ on edge inclusions.

Commit to a specific list of player actions that must work for Wave 1 to be
considered complete. For each, state "in scope" or "deferred":

| Action | Status? |
|--------|---------|
| Connect and log in (to a pre-created test character) | |
| `look` (room description, exits, contents, other characters) | |
| Move through exits (`north`, `south`, etc.) | |
| `get` / `drop` (pick up and drop items) | |
| `inventory` (list carried items) | |
| `wear` / `remove` (equip and unequip) | |
| `say` (local room speech) | |
| `sleep` / `wake` (position changes + command gating) | |
| Entity lookup: `get 2.sword`, partial matching | |
| `kill goblin` (what response?) | |
| Full character creation flow (race/class/stats) | |
| Chat channels (gossip, etc.) | |
| `score` (character stat display) | |

If there are actions not listed that you think must be in Wave 1, add them.

---

## Topic 3: Timing Alternative — Per-System Schedulers with Atomic Transactions (Advisory)

> **This topic does not need a decision this round.** The global RuntimeScheduler
> is the working assumption for spec writing. This topic asks for analysis that
> will inform whether we revisit the decision during Wave 1 implementation.

CONSENSUS.md §3.5 notes an alternative to the global scheduler: since Evennia
operates on atomic database transactions, race conditions in interaction systems
could potentially be solved without a global tick. A per-encounter CombatHandler
could resolve a full round within a single atomic transaction. Concurrent
encounters touching disjoint entity sets wouldn't conflict.

The identified problem is **observer management**: each system-local scheduler
must know the complete set of entities that could observe or be affected by its
actions. Overlapping schedulers must not produce inconsistent state for shared
observers (e.g., a character at the boundary of two concurrent encounters,
area-wide effects that touch entities managed by different local schedulers).

Address:

- **How does Evennia's transaction model actually work in practice?** Django ORM
  transactions, Twisted's async reactor, and Evennia's attribute caching layer
  all interact. Is a CombatHandler's `at_repeat()` already running in a
  transaction? Can we guarantee atomicity of a full round resolution?

- **The observer problem concretely:** A room has 3 NPCs fighting a player. An
  NPC in the adjacent room casts an area spell that affects the combat room.
  With a global scheduler, both the combat round and the area spell resolve in
  the same tick in a defined order. With per-system schedulers, the combat
  handler and the NPC AI handler are independent — who resolves first? What does
  the player see?

- **Would per-system scheduling actually integrate better with Evennia?** The
  global scheduler is essentially reimplementing Diku's main loop inside
  Twisted's reactor. Is there a more Evennia-native way to achieve the same
  guarantees?

- **What is the practical risk of the global scheduler approach?** Is there a
  real chance it "doesn't integrate gracefully" with Evennia, or is that a
  theoretical concern? What specific Evennia mechanisms might it conflict with?

Do not propose a new design. Provide analysis that helps evaluate whether the
alternative is worth prototyping during Wave 1.

---

## Output Format

For Topic 1: provide **Decision**, **Rationale** (brief), **Contract
shape** (actual code), and **Risks**.

For Topic 2: provide the filled-in table with brief justifications for any
non-obvious choices.

For Topic 3: provide analysis only — no decision required.

Do not revisit settled decisions from CONSENSUS.md.
