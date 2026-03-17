# Candidate Chunk Review — Phase 3 Pass 2

Source: `candidate_chunks.json` (30 chunks, 114 dependency edges, 13 implementation waves)

This document is for curated review. For each chunk: accept, split, merge, or annotate. Final decisions freeze into `chunk_registry.json`.

---

## Reading Guide

- **Tier** = fan-in-based implementation priority (T0 utility → T1 foundation → T2 shared → T3 domain → T4 leaf)
- **Wave** = topological implementation order (0 = implement first, 12 = implement last)
- **Fan-in (DAG)** = how many other capability groups depend on this one (excluding utility edges)
- **Enables** = entry points that become fully available when this chunk + all transitive deps are implemented
- **Depends on** = other chunks that must be implemented first

Each chunk section ends with a **Decision** block. Mark your choice and add notes.

---

## Wave 0 — Foundations & Free Leaves

### `world_structure` — T1 foundation | 37 members | DAG fan-in 14

Rooms, exits, areas, spatial data, worldmap coordinates, calendar, sector types, mobile prototypes.

**Depends on:** nothing
**Enables:** nothing directly (everything else builds on this)
**Migration role:** core — becomes room/exit typeclasses + prototypes + world Scripts
**Notes:** Highest-priority domain chunk. Everything in waves 1–12 depends on it transitively. Clean boundary.

> **Decision:** ☐ accept ☐ split ☐ merge ☐ defer
> **Notes:**

---

### `flags` — T0 utility | 34 members | all fan-in 17

Bit-flag operations: test/set/clear, flag-to-string, flag domain resolution.

**Depends on:** nothing
**Enables:** nothing directly
**Migration role:** support — replaced by Evennia tags/locks
**Notes:** Will be mostly replaced in target system. Still needed as reference for understanding legacy behavior. Consider treating as "reference-only" rather than a real implementation chunk — or implement a thin compatibility shim.

> **Decision:** ☐ accept ☐ reference-only ☐ merge into framework utility chunk
> **Notes:**

---

### `string_ops` — T0 utility | 42 members | all fan-in 18

String manipulation: case conversion, matching, formatting, color codes, etc.

**Depends on:** nothing
**Enables:** 2 EPs (`do_censor`, `spec_lookup`)
**Migration role:** support — mostly replaced by Python stdlib
**Notes:** Nearly everything calls into this. Like `flags`, consider whether this needs a real chunk or just a reference mapping to Python equivalents.

> **Decision:** ☐ accept ☐ reference-only ☐ merge into framework utility chunk
> **Notes:**

---

### `numerics` — T0 utility | 13 members | all fan-in 12

RNG, dice rolling, interpolation, clamping.

**Depends on:** nothing
**Enables:** nothing directly
**Migration role:** support — utility module
**Notes:** Small, clean, mechanical. Good candidate for early "utility module" implementation.

> **Decision:** ☐ accept ☐ merge into framework utility chunk
> **Notes:**

---

### `imaging` — T0 utility | 4 members | all fan-in 0

PNG loading/writing for worldmap tile rendering.

**Depends on:** nothing
**Enables:** nothing directly
**Migration role:** replacement candidate — web-based map or contrib
**Notes:** Completely isolated. Zero fan-in. Only 4 functions. May not need a chunk at all if the target uses a different map approach.

> **Decision:** ☐ accept ☐ defer ☐ drop
> **Notes:**

---

### `economy` — T4 leaf | 9 members | DAG fan-in 0, fan-out 0

Gold/silver handling, shop pricing, auction participation.

**Depends on:** nothing (no DAG edges in or out)
**Enables:** nothing directly (attributed 0 EPs — but 6 EPs become available once economy + its transitive deps are done)
**Migration role:** core — economy handler + auction Script + shop rules
**Warning:** ⚠ ORPHAN — no dependency edges at all. This means `economy` functions are called only via utility-typed edges or aren't called by other capability groups. Verify whether it genuinely has no dependencies, or whether the call graph missed implicit coupling (e.g. through shop/auction commands calling economy + other systems).

> **Decision:** ☐ accept ☐ defer ☐ merge into objects
> **Notes:**

---

## Wave 1

### `state_rules` — T1 foundation | 54 members | DAG fan-in 18

Character state predicates: is-NPC, position checks, safety checks, permission guards, group membership, daze/wait.

**Depends on:** `world_structure`
**Enables:** 1 EP (`do_immname`)
**Migration role:** support — lock functions + permission checks
**Notes:** Second-highest fan-in after `output`. Nearly everything consults state_rules before acting. Clean policy boundary. 54 members is moderate — could be split into "character predicates" and "permission guards" but probably not worth it at this stage.

> **Decision:** ☐ accept ☐ split (character predicates / permission guards)
> **Notes:**

---

## Wave 2

### `attributes` — T1 foundation | 45 members | DAG fan-in 12

Stat accessors, derived computation (AC, hitroll, regen), carrying capacity, saving throws.

**Depends on:** `state_rules`, `world_structure`
**Enables:** nothing directly
**Migration role:** support — traits handler/contrib + derived-stat rules
**Notes:** Another universal dependency. Clean separation from state_rules (predicates vs. computed values). 45 members is manageable.

> **Decision:** ☐ accept ☐ split
> **Notes:**

---

## Wave 3

### `visibility_rules` — T2 shared | 10 members | DAG fan-in 6

Can-see checks for characters, objects, rooms. Darkness, blindness, privacy.

**Depends on:** `attributes`, `state_rules`, `world_structure`
**Enables:** nothing directly
**Migration role:** support — return_appearance filtering + lock functions
**Notes:** Small (10 members), clean policy boundary. Six chunks depend on it. Good standalone chunk.

> **Decision:** ☐ accept
> **Notes:**

---

## Wave 4

### `output` — T1 foundation | 56 members | DAG fan-in 18

Message dispatch, color handling, prompt generation, pager, damage messages, broadcast.

**Depends on:** `attributes`, `state_rules`, `visibility_rules`, `world_structure`
**Enables:** 74 EPs (70 commands, 4 spells) — first major unlock of user-visible behavior
**Migration role:** support — msg() + appearance hooks + display helpers
**Notes:** Tied for highest fan-in. 56 members is borderline large but internally coherent (it's all "get text to the player"). This is the chunk that unlocks the first big wave of simple commands (config toggles, channel commands, basic info).

> **Decision:** ☐ accept ☐ split (core messaging / formatting / combat messages)
> **Notes:**

---

## Wave 5

### `admin` — T1 foundation | 10 members | DAG fan-in 10

Logging, immortal broadcasts, restoration, rank derivation, command disable.

**Depends on:** `attributes`, `output`
**Enables:** nothing directly
**Migration role:** support — admin CmdSet + logging
**Notes:** Small, clean, mechanical. 10 consumers. Straightforward.

> **Decision:** ☐ accept
> **Notes:**

---

### `skills_progression` — T2 shared | 32 members | DAG fan-in 6

Skill/spell lookup, proficiency, XP/level advancement, practice/training, class/guild resolution.

**Depends on:** `attributes`, `output`, `state_rules`
**Enables:** 4 EPs (`do_autopeek`, `do_groups`, `do_worth`, `spell_mass_healing`)
**Migration role:** core — traits handler + skills rules + progression handler
**Notes:** Core domain system. 32 members is reasonable. Clean dependency on the policy foundation.

> **Decision:** ☐ accept ☐ split
> **Notes:**

---

### `notes` — T4 leaf | 10 members | DAG fan-in 0

Board/note system: compose, deliver, remove, spool.

**Depends on:** `output`, `state_rules`
**Enables:** nothing directly (3 EPs attributed at higher wave)
**Migration role:** core — Msg system or board contrib
**Notes:** Small (10 members), clean leaf. Zero fan-in. Self-contained domain feature. Good candidate for early domain-feature implementation after the foundation is in place.

> **Decision:** ☐ accept
> **Notes:**

---

## Wave 6

### `entity_lookup` — T2 shared | 34 members | DAG fan-in 3

Find characters/objects/players by name, scoped search, extra-description lookup, disambiguation.

**Depends on:** `admin`, `output`, `state_rules`, `visibility_rules`, `world_structure`
**Enables:** nothing directly
**Migration role:** cross-cutting — search functions + DefaultObject.search overrides
**Bundle suggestion:** ⚡ Only 2 domain consumers via DAG edges: `combat` and `objects`. Consider bundling into `objects` (the more general consumer) rather than keeping standalone.

> **Decision:** ☐ accept standalone ☐ merge into objects ☐ merge into combat
> **Notes:**

---

### `magic` — T3 domain | 6 members | DAG fan-in 1

Spell dispatch (scroll/wand/staff/potion), saving throws, dispel, chain-spell, incantation.

**Depends on:** `output`, `skills_progression`, `state_rules`
**Enables:** nothing directly
**Migration role:** core — rules module + spell handler + magic CmdSet
**Notes:** Very small (6 members). The casting *framework* — not the spells themselves (those are entry points distributed across many capabilities). Consider whether this should stand alone or merge with `skills_progression` since both deal with the skill/spell lookup pipeline.

> **Decision:** ☐ accept ☐ merge into skills_progression
> **Notes:**

---

### `movement` — T2 shared | 34 members | DAG fan-in 8

Room traversal, doors, pathfinding, flee, portal/recall, warp crystal, extraction, pet creation.

**Depends on:** `admin`, `output`, `skills_progression`, `state_rules`, `visibility_rules`, `world_structure`
**Enables:** 4 EPs (4 spec_cast_* specials)
**Migration role:** core — movement rules + exit/room typeclass hooks
**Notes:** High fan-in (8 DAG consumers). Core domain system. 34 members. Clean boundary.

> **Decision:** ☐ accept
> **Notes:**

---

## Wave 7

### `affects` — T2 shared | 88 members | DAG fan-in 5

Affect lifecycle: apply, remove, query, sort, elemental effects, dispel, remort affects, gem effects, room affects.

**Depends on:** `admin`, `attributes`, `magic`, `movement`, `output`, `state_rules`
**Enables:** 4 EPs (`do_dump`, `do_mark`, `do_visible`, `spell_darkness`)
**Migration role:** core — buffs handler or contrib + rules integration
**Warning:** ⚠ LARGE — 88 members. Consider whether this can be split:
  - Core affect lifecycle (apply/remove/query/iterate) — the engine
  - Elemental/damage effects (cold, fire, acid, poison, shock) — domain-specific
  - Remort affects — feature-specific
  - Gem effects — feature-specific

> **Decision:** ☐ accept as-is ☐ split (lifecycle / elemental / remort / gem)
> **Notes:**

---

### `npc_behavior` — T4 leaf | 21 members | DAG fan-in 0

MobProg execution, triggers (speech/fight/death/greet/etc.), spec_fun dispatch, hunting AI.

**Depends on:** `admin`, `attributes`, `movement`, `output`, `state_rules`, `visibility_rules`, `world_structure`
**Enables:** nothing directly
**Migration role:** core — AI Script/handler + trigger hooks
**Notes:** Zero fan-in (pure consumer). 7 outgoing deps means it needs a lot of infrastructure in place. 21 members is fine. Self-contained behavior system.

> **Decision:** ☐ accept
> **Notes:**

---

### `pvp` — T4 leaf | 6 members | DAG fan-in 0

Duel initiation/tracking, arena setup, kill resolution.

**Depends on:** `movement`, `state_rules`, `world_structure`
**Enables:** nothing directly
**Migration role:** core — PvP rules overlay + arena Script
**Notes:** Small (6 members), clean leaf. Could be deferred to late in the migration.

> **Decision:** ☐ accept ☐ defer
> **Notes:**

---

## Wave 8

### `objects` — T2 shared | 43 members | DAG fan-in 5

Object creation, cloning, extraction, transfer, equip/remove, loot generation, gem inset, repair, forging.

**Depends on:** `admin`, `affects`, `attributes`, `entity_lookup`, `movement`, `output`, `skills_progression`, `state_rules`, `world_structure`
**Enables:** nothing directly
**Migration role:** core — object handlers + rules + prototypes + shop layer
**Notes:** Wide dependency surface (9 chunks). 43 members is moderate. Core domain system. If `entity_lookup` is merged in, this becomes 77 members — borderline. If kept separate, clean.

> **Decision:** ☐ accept ☐ absorb entity_lookup (43+34=77 members)
> **Notes:**

---

## Wave 9

### `display` — T4 leaf | 27 members | DAG fan-in 0 (DAG) / 2 (all)

Room/character/object description rendering, score sheet, minimap, affect display, exit listing.

**Depends on:** `affects`, `attributes`, `movement`, `objects`, `output`, `skills_progression`, `state_rules`, `visibility_rules`, `world_structure`
**Enables:** 5 EPs (`do_count`, `do_exlist`, `do_roomexits`, `do_time`, `do_weather`)
**Migration role:** support — return_appearance + get_display_* hooks
**Notes:** Wide deps (9 chunks) but zero DAG fan-in. Pure projection consumer. This is essentially "the look command and friends" — assembles text from many systems. Good late-stage chunk.

> **Decision:** ☐ accept
> **Notes:**

---

### `persistence` — T2 shared | 94 members | DAG fan-in 6

Save/load, area-file reading, JSON/SQL, war tables, social persistence, note files, player index.

**Depends on:** `admin`, `affects`, `attributes`, `entity_lookup`, `objects`, `output`, `skills_progression`, `state_rules`, `world_structure`
**Enables:** 1 EP (`do_pipe`)
**Migration role:** support — AttributeHandler + SaverDict + batch-code
**Warning:** ⚠ LARGE — 94 members. Likely splits:
  - Character save/load (JSON serialization)
  - Area file parsing (legacy format readers)
  - SQL layer (queries, commands, row iteration)
  - Miscellaneous persistence (war tables, socials, notes)

Area file parsing may be a one-time migration concern (convert to Evennia prototypes/batch-code) rather than a runtime chunk.

> **Decision:** ☐ accept as-is ☐ split (char save / area parse / SQL / misc)
> **Notes:**

---

### `quests` — T4 leaf | 16 members | DAG fan-in 0

Quest generation, skill-quests, completion, quest-point tracking, quest info display.

**Depends on:** `admin`, `attributes`, `movement`, `objects`, `output`, `state_rules`, `world_structure`
**Enables:** 1 EP (`do_swho`)
**Migration role:** core — quest handler + Script + rules
**Notes:** Zero fan-in leaf. 16 members. Clean self-contained feature.

> **Decision:** ☐ accept
> **Notes:**

---

## Wave 10

### `clans` — T3 domain | 30 members | DAG fan-in 1

Clan membership, power/score, inter-clan wars, roster, clan table persistence.

**Depends on:** `output`, `persistence`
**Enables:** 2 EPs (`do_channels`, `do_exits`)
**Migration role:** core — tags/locks + clan handler + global Script
**Notes:** Only 1 DAG consumer (combat, which checks clan/war status). 30 members. Clean organizational system.

> **Decision:** ☐ accept
> **Notes:**

---

### `social` — T4 leaf | 10 members | DAG fan-in 0

Chat channels, tells, say/emote, social actions (bow, wave), social table management.

**Depends on:** `output`, `persistence`, `state_rules`
**Enables:** 1 EP (`do_memory`)
**Migration role:** core — social CmdSet + channel contrib/handler
**Notes:** Small leaf. Clean communication system.

> **Decision:** ☐ accept
> **Notes:**

---

### `arg_parsing` — T0 utility | 14 members | all fan-in 7

Argument tokenization, numbered targets, quantity prefixes, keyword matching.

**Depends on:** `output`, `persistence`
**Enables:** 284 EPs (196 cmd, 82 spell, 6 spec) — **largest single enablement**
**Migration role:** support — utility module + Evennia arg parsing
**Notes:** The entry-point enablement number is misleading — it's the "last dependency" for 284 EPs simply because it sits at wave 10 after almost everything else. In the target system, Evennia provides its own argument parsing, so this may be reference-only. However, legacy-specific parsing quirks (dot-notation, numbered targets, quantity prefixes) may need a compatibility layer.

> **Decision:** ☐ accept ☐ reference-only ☐ merge into framework utility chunk
> **Notes:**

---

### `memory` — T0 utility | 17 members | all fan-in 5

Pooled allocation, garbage collection, buffer management, cJSON teardown, affect cache.

**Depends on:** `persistence`
**Enables:** 67 EPs (53 cmd, 14 spell)
**Migration role:** replacement candidate — not needed (Python GC)
**Notes:** Like `arg_parsing`, the enablement number is a wave-ordering artifact. None of these functions will exist in the target system. This is a pure reference chunk.

> **Decision:** ☐ reference-only ☐ drop
> **Notes:**

---

### `text_editing` — T0 utility | 23 members | all fan-in 0

In-game line editor: init, navigation, insert/delete, word wrap, undo.

**Depends on:** `admin`, `output`, `persistence`
**Enables:** nothing directly
**Migration role:** support — EvEditor contrib or custom editor handler
**Notes:** Zero fan-in. Evennia has EvEditor built in, so this maps to using a contrib rather than porting. Reference-only unless the legacy editor has unique features worth preserving.

> **Decision:** ☐ accept ☐ reference-only ☐ use EvEditor contrib
> **Notes:**

---

## Wave 11

### `combat` — T3 domain | 25 members | DAG fan-in 1

Combat mechanics, damage calculation, battle state management.

**Depends on:** `admin`, `affects`, `attributes`, `clans`, `entity_lookup`, `movement`, `objects`, `output`, `persistence`, `skills_progression`, `state_rules`, `visibility_rules`, `world_structure` (13 dependencies)
**Enables:** 6 EPs (1 cmd, 5 spells)
**Migration role:** core — combat handler + rules module + combat CmdSet
**Notes:** Widest dependency surface (13 chunks). Only 25 members though — this is the combat *engine*, not everything combat-adjacent. Late wave makes sense given its dependency breadth. The 1 DAG consumer is `runtime` (combat rounds are tick-driven).

> **Decision:** ☐ accept
> **Notes:**

---

## Wave 12

### `runtime` — T4 leaf | 9 members | DAG fan-in 0

Tick/event systems, game loop integration, dynamic dispatch.

**Depends on:** `admin`, `affects`, `attributes`, `combat`, `movement`, `objects`, `output`, `state_rules`, `world_structure` (9 dependencies)
**Enables:** nothing (or rather: enables continuous game operation — tick-driven affects, combat rounds, NPC AI, weather, etc.)
**Migration role:** infrastructure — Evennia's own loop + Scripts
**Notes:** Last wave. This is the "glue" that makes everything run continuously. In Evennia, most of this maps to Scripts + tickerhandler. 9 members is tiny — it's mostly dispatch code.

> **Decision:** ☐ accept ☐ reference-only (Evennia provides this)
> **Notes:**

---

## Cross-Cutting Decisions

### 1. Utility consolidation

Seven utility chunks exist: `flags`, `string_ops`, `numerics`, `imaging`, `arg_parsing`, `memory`, `text_editing`.

Some of these map to Python stdlib or Evennia built-ins and may not need real implementation chunks. Options:

- **A)** Keep all 7 as separate chunks (maximizes traceability, some may be reference-only)
- **B)** Merge into a single "framework utilities" chunk (simpler plan, less overhead)
- **C)** Keep `numerics` + `arg_parsing` as real chunks; mark `flags`, `string_ops`, `memory` as reference-only; defer `imaging` and `text_editing`

> **Decision:** ☐ A (separate) ☐ B (merge) ☐ C (mixed)
> **Notes:**

### 2. Large chunk splitting

Two chunks exceed 60 members:
- `affects` (88 members)
- `persistence` (94 members)

Split or accept? See individual chunk decisions above.

### 3. `entity_lookup` placement

`entity_lookup` (34 members) has only 2 domain consumers via DAG edges: `combat` and `objects`. Options:

- **A)** Keep standalone (cleaner boundary, used by `persistence` too)
- **B)** Merge into `objects` (77 total members — borderline)
- **C)** Merge into a new "entity resolution" chunk with related visibility_rules

> **Decision:** ☐ A ☐ B ☐ C
> **Notes:**

### 4. `economy` orphan

`economy` has zero DAG edges in any direction. Verify:
- Is it genuinely independent (called only from entry points, not from other capability groups)?
- Should it be merged with `objects` (shops are about items)?
- Should it be its own late-stage feature chunk?

> **Decision:** ☐ accept as standalone leaf ☐ merge into objects ☐ investigate
> **Notes:**

---

## Summary Table

| Wave | Chunk | Tier | Members | DAG Fan-in | Deps | Enables | Status |
|------|-------|------|---------|------------|------|---------|--------|
| 0 | world_structure | T1 | 37 | 14 | 0 | 0 | |
| 0 | flags | T0 | 34 | 0 | 0 | 0 | |
| 0 | string_ops | T0 | 42 | 0 | 0 | 2 | |
| 0 | numerics | T0 | 13 | 0 | 0 | 0 | |
| 0 | imaging | T0 | 4 | 0 | 0 | 0 | |
| 0 | economy | T4 | 9 | 0 | 0 | 0 | ⚠ orphan |
| 1 | state_rules | T1 | 54 | 18 | 1 | 1 | |
| 2 | attributes | T1 | 45 | 12 | 2 | 0 | |
| 3 | visibility_rules | T2 | 10 | 6 | 3 | 0 | |
| 4 | output | T1 | 56 | 18 | 4 | 74 | |
| 5 | admin | T1 | 10 | 10 | 2 | 0 | |
| 5 | skills_progression | T2 | 32 | 6 | 3 | 4 | |
| 5 | notes | T4 | 10 | 0 | 2 | 0 | |
| 6 | entity_lookup | T2 | 34 | 3 | 5 | 0 | ⚡ bundle? |
| 6 | magic | T3 | 6 | 1 | 3 | 0 | |
| 6 | movement | T2 | 34 | 8 | 6 | 4 | |
| 7 | affects | T2 | 88 | 5 | 6 | 4 | ⚠ large |
| 7 | npc_behavior | T4 | 21 | 0 | 7 | 0 | |
| 7 | pvp | T4 | 6 | 0 | 3 | 0 | |
| 8 | objects | T2 | 43 | 5 | 9 | 0 | |
| 9 | display | T4 | 27 | 0 | 9 | 5 | |
| 9 | persistence | T2 | 94 | 6 | 9 | 1 | ⚠ large |
| 9 | quests | T4 | 16 | 0 | 7 | 1 | |
| 10 | clans | T3 | 30 | 1 | 2 | 2 | |
| 10 | social | T4 | 10 | 0 | 3 | 1 | |
| 10 | arg_parsing | T0 | 14 | 0 | 2 | 284 | |
| 10 | memory | T0 | 17 | 0 | 1 | 67 | |
| 10 | text_editing | T0 | 23 | 0 | 3 | 0 | |
| 11 | combat | T3 | 25 | 1 | 13 | 6 | |
| 12 | runtime | T4 | 9 | 0 | 9 | 0 | |
