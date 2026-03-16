# Chunk Registry

**30 chunks** — 19 native, 5 adaptation, 3 reference, 2 replacement, 1 substrate

## Summary

| Chunk | Type | Mode | Phase | Wave | Members | Fan-in | Enables | Umbrella |
|-------|------|------|-------|------|---------|--------|---------|----------|
| economy | domain | native | D | 0 | 9 | 0 | 0 |  |
| flags | utility | reference | — | 0 | 34 | 0 | 0 |  |
| imaging | utility | replacement | — | 0 | 4 | 0 | 0 |  |
| numerics | utility | native | — | 0 | 13 | 0 | 0 |  |
| string_ops | utility | reference | — | 0 | 42 | 0 | 2 |  |
| world_structure | domain | native | B | 0 | 37 | 14 | 0 | ☂ |
| state_rules | policy | native | B | 1 | 54 | 18 | 1 |  |
| attributes | policy | native | B | 2 | 45 | 12 | 0 |  |
| visibility_rules | policy | native | B | 3 | 10 | 6 | 0 |  |
| output | projection | adaptation | B | 4 | 56 | 18 | 74 |  |
| admin | infrastructure | adaptation | B | 5 | 10 | 10 | 0 |  |
| notes | domain | native | C | 5 | 10 | 0 | 0 |  |
| skills_progression | domain | native | B | 5 | 32 | 6 | 4 |  |
| entity_lookup | policy | adaptation | B | 6 | 34 | 3 | 0 |  |
| magic | domain | native | D | 6 | 6 | 1 | 0 |  |
| movement | domain | native | C | 6 | 34 | 8 | 4 |  |
| affects | domain | native | D | 7 | 88 | 5 | 4 | ☂ |
| npc_behavior | domain | native | D | 7 | 21 | 0 | 0 |  |
| pvp | domain | native | D | 7 | 6 | 0 | 0 |  |
| objects | domain | native | C | 8 | 43 | 5 | 0 | ☂ |
| display | projection | adaptation | C | 9 | 27 | 0 | 5 |  |
| persistence | infrastructure | native | D | 9 | 94 | 6 | 1 | ☂ |
| quests | domain | native | D | 9 | 16 | 0 | 1 |  |
| arg_parsing | utility | adaptation | — | 10 | 14 | 0 | 284 |  |
| clans | domain | native | D | 10 | 30 | 1 | 2 |  |
| memory | utility | reference | — | 10 | 17 | 0 | 67 |  |
| social | domain | native | C | 10 | 10 | 0 | 1 |  |
| text_editing | utility | replacement | — | 10 | 23 | 0 | 0 |  |
| combat | domain | native | D | 11 | 25 | 1 | 67 |  |
| runtime | infrastructure | substrate | — | 12 | 9 | 0 | 110 |  |

## By Implementation Mode

### Native implementation (19)

- **affects** · Phase D · ☂ umbrella
- **attributes** · Phase B
- **clans** · Phase D
- **combat** · Phase D
- **economy** · Phase D
- **magic** · Phase D
- **movement** · Phase C
- **notes** · Phase C
- **npc_behavior** · Phase D
- **numerics**
- **objects** · Phase C · ☂ umbrella
- **persistence** · Phase D · ☂ umbrella
- **pvp** · Phase D
- **quests** · Phase D
- **skills_progression** · Phase B
- **social** · Phase C
- **state_rules** · Phase B
- **visibility_rules** · Phase B
- **world_structure** · Phase B · ☂ umbrella

### Adaptation layer (5)

- **admin** · Phase B
- **arg_parsing**
- **display** · Phase C
- **entity_lookup** · Phase B
- **output** · Phase B

### Reference only (3)

- **flags**
- **memory**
- **string_ops**

### Replacement / contrib (2)

- **imaging**
- **text_editing**

### Evennia substrate (1)

- **runtime**

## By Planning Phase

### Phase B — foundational semantics (8 chunks)

- **admin** [adaptation] — Administrative and immortal utilities: bug and diagnostic logging (formatted and timestamped), broad…
- **attributes** [native] — Character stat access and derived computation: armor class calculation (base, modified, unspelled), …
- **entity_lookup** [adaptation] — In-game entity resolution: finding characters, NPCs, objects, and players by name within various sco…
- **output** [adaptation] — Message transport to player connections: dispatching formatted messages to rooms and specific target…
- **skills_progression** [native] — Skill and level progression: skill lookup by name and index, proficiency queries and updates, weapon…
- **state_rules** [native] — Character state predicates and permission guards: NPC-vs-player checks, immortal and hero tier tests…
- **visibility_rules** [native] — Visibility and perception checks: determining whether one character can see another (including in ro…
- **world_structure** [native] — World structure and spatial data: area metadata and retrieval, area player and immortal counting, ro…

### Phase C — first vertical slices (5 chunks)

- **display** [adaptation] — Information rendering and display assembly: room description and contents display, character appeara…
- **movement** [native] — Character and object movement between rooms: entering and leaving rooms, door and exit resolution, r…
- **notes** [native] — Asynchronous note and board system: composing, addressing, and attaching notes to characters, append…
- **objects** [native] — Object lifecycle and manipulation: creating objects from prototypes, cloning, extracting and destroy…
- **social** [native] — Synchronous communication and social interaction: chat channel messaging and channel membership quer…

### Phase D — heavier systemic features (9 chunks)

- **affects** [native] — Affect lifecycle management: applying, joining, and copying affects to characters, objects, and room…
- **clans** [native] — Clan organisation system: membership checks, clan power and score computation, inter-clan war initia…
- **combat** [native] — Combat round execution: single and multi-attack resolution per round, damage calculation and applica…
- **economy** [native] — Economy and currency system: gold and silver handling, currency deduction and weight computation, mo…
- **magic** [native] — Spell casting mechanics: object-triggered spell dispatch (scrolls, wands, staves, potions), saving t…
- **npc_behavior** [native] — NPC behavioural logic: MobProg program execution (driver, command processing, conditional evaluation…
- **persistence** [native] — Data serialisation, storage, and retrieval: character save/load to JSON files, pet serialisation, ob…
- **pvp** [native] — Duel and arena mechanics: duel initiation, tracking, and kill resolution, arena setup and clearing, …
- **quests** [native] — Quest system: random quest generation and target assignment, skill-quest creation (mob and object va…

## Vertical Slices (Phase C)

### Inspect & Navigate

Room exists, can move, can look, can resolve targets. First playable milestone.

- **Primary:** movement, display
- **Supporting:** world_structure, visibility_rules, output, entity_lookup

### Manipulate Objects

Can pick up, drop, wear, remove objects. Basic inventory.

- **Primary:** objects
- **Supporting:** entity_lookup, attributes, state_rules

### Communication

Chat channels, tells, notes, social actions.

- **Primary:** social, notes
- **Supporting:** output

## Implementation Order

**Wave 0:** economy (native, Ph.D) · flags (reference) · imaging (replacement) · numerics (native) · string_ops (reference) · world_structure (native, Ph.B, ☂)

**Wave 1:** state_rules (native, Ph.B)

**Wave 2:** attributes (native, Ph.B)

**Wave 3:** visibility_rules (native, Ph.B)

**Wave 4:** output (adaptation, Ph.B)

**Wave 5:** admin (adaptation, Ph.B) · notes (native, Ph.C) · skills_progression (native, Ph.B)

**Wave 6:** entity_lookup (adaptation, Ph.B) · magic (native, Ph.D) · movement (native, Ph.C)

**Wave 7:** affects (native, Ph.D, ☂) · npc_behavior (native, Ph.D) · pvp (native, Ph.D)

**Wave 8:** objects (native, Ph.C, ☂)

**Wave 9:** display (adaptation, Ph.C) · persistence (native, Ph.D, ☂) · quests (native, Ph.D)

**Wave 10:** arg_parsing (adaptation) · clans (native, Ph.D) · memory (reference) · social (native, Ph.C) · text_editing (replacement)

**Wave 11:** combat (native, Ph.D)

**Wave 12:** runtime (substrate)

---

## Chunk Details

### economy

*Native implementation · Phase D — heavier systemic features*

> Economy and currency system: gold and silver handling, currency deduction and weight computation, money object creation, shop pricing, shopkeeper location, quest-shop identification, auction participation checks, currency lookup.

| Property | Value |
|----------|-------|
| Type | domain |
| Mode | native |
| Phase | D |
| Impl wave | 0 |
| Evidence wave | 0 |
| Members | 9 |
| Fan-in (DAG) | 0 |
| Fan-in (all) | 0 |
| Fan-out (DAG) | 0 |
| Migration role | core |
| Target surfaces | economy handler + auction Script + shop rules |

**Depends on:** nothing

**Depended on by:** nothing (leaf)

**Notes:** Standalone leaf. Economy is distinct from object lifecycle even if they share Evennia surfaces. Late/optional until validated by user-story priority.

---

### flags

*Reference only*

> Bit-flag utility operations: testing, setting, and clearing individual bits, testing any/all/none-of predicates, flag-to-string conversion and name resolution for all flag domains (room, player, act, communication, wear, container, form, extra, offensive, wiz, part, censor, revoke, cgroup), flag index lookup by name, flag retrieval from database columns and JSON, object-value flag access, character cgroup flag addition and removal, flag emptiness checks.

| Property | Value |
|----------|-------|
| Type | utility |
| Mode | reference |
| Phase | — |
| Impl wave | 0 |
| Evidence wave | 0 |
| Members | 34 |
| Fan-in (DAG) | 0 |
| Fan-in (all) | 17 |
| Fan-out (DAG) | 0 |
| Migration role | support |
| Target surfaces | replaced by Evennia tags/locks system |

**Depends on:** nothing

**Depended on by:** nothing (leaf)

**Notes:** Reference-only. Do not build a flag system unless a specific legacy-visible behavior demands it. Use Evennia tags/locks.

---

### imaging

*Replacement / contrib*

> Bitmap image creation and I/O: loading and writing PNG files, querying image dimensions and per-pixel color channel values, used for worldmap tile rendering.

| Property | Value |
|----------|-------|
| Type | utility |
| Mode | replacement |
| Phase | — |
| Impl wave | 0 |
| Evidence wave | 0 |
| Members | 4 |
| Fan-in (DAG) | 0 |
| Fan-in (all) | 0 |
| Fan-out (DAG) | 0 |
| Migration role | replacement_candidate |
| Target surfaces | replaced by web-based map or contrib |

**Depends on:** nothing

**Depended on by:** nothing (leaf)

**Notes:** Defer/drop. Only resurrect if world-map presentation requires it.

---

### numerics

*Native implementation*

> Numeric utilities: pseudo-random number generation (flat range, percentage, door index, fuzzy, bit-width), dice rolling, pseudo-random distribution with failure memory, linear interpolation between level-indexed values, value clamping, power-of-two rounding, time-value scanning.

| Property | Value |
|----------|-------|
| Type | utility |
| Mode | native |
| Phase | — |
| Impl wave | 0 |
| Evidence wave | 0 |
| Members | 13 |
| Fan-in (DAG) | 0 |
| Fan-in (all) | 12 |
| Fan-out (DAG) | 0 |
| Migration role | support |
| Target surfaces | utility module |

**Depends on:** nothing

**Depended on by:** nothing (leaf)

**Notes:** Small, safe, useful utility. Keep as real chunk.

---

### string_ops

*Reference only*

> String manipulation utilities: case conversion, trimming and stripping, substring extraction and search, prefix/infix/suffix matching, string comparison (case-sensitive and insensitive), string replacement, concatenation, insertion, and erasure, centering and number-to-string conversion, ordinal formatting, time formatting, drunk-speech transformation, hex parsing, color code removal, string duplication, length computation.

| Property | Value |
|----------|-------|
| Type | utility |
| Mode | reference |
| Phase | — |
| Impl wave | 0 |
| Evidence wave | 0 |
| Members | 42 |
| Fan-in (DAG) | 0 |
| Fan-in (all) | 18 |
| Fan-out (DAG) | 0 |
| Migration role | support |
| Target surfaces | utility module (mostly replaced by Python stdlib) |

**Depends on:** nothing

**Depended on by:** nothing (leaf)

**Enables:** 2 entry points (1 commands, 1 specials)

Commands: `do_censor`

Specials: `spec_lookup`

**Notes:** Reference-only. Use Python string behavior by default; preserve legacy-specific text quirks only where they affect UX.

---

### world_structure

*Native implementation · Phase B — foundational semantics · Umbrella chunk*

> World structure and spatial data: area metadata and retrieval, area player and immortal counting, room properties (sector type, healing/mana rate, guild, ownership, name), exit topology (direction names, reverse direction, keywords, keys), room and location identity encoding, worldmap coordinate system and quadtree-based spatial lookups, calendar and time-of-day data, sector type lookup, vnum identity, mobile prototype retrieval, mobile creation and cloning, skill-quest room selection.

| Property | Value |
|----------|-------|
| Type | domain |
| Mode | native |
| Phase | B |
| Impl wave | 0 |
| Evidence wave | 0 |
| Members | 37 |
| Fan-in (DAG) | 14 |
| Fan-in (all) | 14 |
| Fan-out (DAG) | 0 |
| Migration role | core |
| Target surfaces | room/exit typeclasses + prototypes + world Scripts (weather, time, resets) |

**Depends on:** nothing

**Depended on by:** attributes, combat, display, entity_lookup, movement, npc_behavior, objects, output, persistence, pvp, quests, runtime, state_rules, visibility_rules

**Notes:** Umbrella chunk. Target-side breakup: room/exit typeclasses, prototypes/content generation, world metadata/mapping, calendar/weather. Do not let it become one giant module.

---

### state_rules

*Native implementation · Phase B — foundational semantics*

> Character state predicates and permission guards: NPC-vs-player checks, immortal and hero tier tests, position checks (awake, sleeping, standing), level and trust requirement enforcement, combat safety checks (safe rooms, PvP legality, attack-ok validation), duel and arena participation state, killer and thief flag checks, clan and war opponent status, equipment permission (clan-owned, personalised, wear slots), object sacrifice eligibility, condition monitoring (hunger, thirst, drunk), alignment and class predicates, remort tier checks, follower attachment and detachment, command group membership, wait and daze state assignment, group membership checks, character-type matching.

| Property | Value |
|----------|-------|
| Type | policy |
| Mode | native |
| Phase | B |
| Impl wave | 1 |
| Evidence wave | 1 |
| Members | 54 |
| Fan-in (DAG) | 18 |
| Fan-in (all) | 19 |
| Fan-out (DAG) | 1 |
| Migration role | support |
| Target surfaces | lock functions + permission checks in rules modules |

**Depends on:** world_structure (requires_core)

**Depended on by:** affects, attributes, combat, display, entity_lookup, magic, movement, notes, npc_behavior, objects, output, persistence, pvp, quests, runtime, skills_progression, social, visibility_rules

**Enables:** 1 entry points (1 commands)

Commands: `do_immname`

**Notes:** One of the most important early chunks. Lock functions + permission checks in rules modules.

---

### attributes

*Native implementation · Phase B — foundational semantics*

> Character stat access and derived computation: armor class calculation (base, modified, unspelled), hitroll and damroll computation, maximum hit points, mana, and stamina derivation, per-stat accessors and modifiers (strength, dexterity, constitution, intelligence, wisdom, charisma), age computation, carrying weight and count capacity, regeneration rates (HP, mana, stamina), defense modifier display, stat-to-attribute mapping, level-based saving throws, stamina deduction, title and play-time tracking, sex and rank accessors, object stat flag checks.

| Property | Value |
|----------|-------|
| Type | policy |
| Mode | native |
| Phase | B |
| Impl wave | 2 |
| Evidence wave | 2 |
| Members | 45 |
| Fan-in (DAG) | 12 |
| Fan-in (all) | 14 |
| Fan-out (DAG) | 2 |
| Migration role | support |
| Target surfaces | traits handler/contrib + derived-stat rules |

**Depends on:** state_rules (requires_policy), world_structure (requires_core)

**Depended on by:** admin, affects, combat, display, npc_behavior, objects, output, persistence, quests, runtime, skills_progression, visibility_rules

**Notes:** Foundational. Traits handler/contrib + derived-stat rules.

---

### visibility_rules

*Native implementation · Phase B — foundational semantics*

> Visibility and perception checks: determining whether one character can see another (including in room, in WHO list), object visibility, room visibility, darkness and very-dark room detection, blindness checks, room privacy, location and coordinate validity, light-level effects on perception.

| Property | Value |
|----------|-------|
| Type | policy |
| Mode | native |
| Phase | B |
| Impl wave | 3 |
| Evidence wave | 3 |
| Members | 10 |
| Fan-in (DAG) | 6 |
| Fan-in (all) | 6 |
| Fan-out (DAG) | 3 |
| Migration role | support |
| Target surfaces | return_appearance filtering + lock functions |

**Depends on:** attributes (requires_policy), state_rules (requires_policy), world_structure (requires_core)

**Depended on by:** combat, display, entity_lookup, movement, npc_behavior, output

**Notes:** Small, clean policy boundary. return_appearance filtering + lock functions.

---

### output

*Adaptation layer · Phase B — foundational semantics*

> Message transport to player connections: dispatching formatted messages to rooms and specific targets, sending text to character output buffers, descriptor output buffering and flushing, pager display, color code expansion and ANSI escape sequence handling, custom color configuration, prompt generation, terminal control (cursor positioning, screen clearing, reset), text formatting and paragraph wrapping, damage and combat message rendering, video configuration, duel and auction broadcast dispatch.

| Property | Value |
|----------|-------|
| Type | projection |
| Mode | adaptation |
| Phase | B |
| Impl wave | 4 |
| Evidence wave | 4 |
| Members | 56 |
| Fan-in (DAG) | 18 |
| Fan-in (all) | 19 |
| Fan-out (DAG) | 4 |
| Migration role | support |
| Target surfaces | msg() + appearance hooks + display helpers |

**Depends on:** attributes (requires_policy), state_rules (requires_policy), visibility_rules (requires_policy), world_structure (requires_core)

**Depended on by:** admin, affects, arg_parsing, clans, combat, display, entity_lookup, magic, movement, notes, npc_behavior, objects, persistence, quests, runtime, skills_progression, social, text_editing

**Enables:** 74 entry points (70 commands, 4 spells)

Commands: `do_addexit`, `do_alia`, `do_announce`, `do_autoassist`, `do_autoexit`, `do_autogold`, `do_autolist`, `do_autoloot`, `do_autorecall`, `do_autosac`, `do_autosplit`, `do_autotick`, `do_balance`, `do_brief`, `do_chatmode` … and 55 more

Spells: `spell_control_weather`, `spell_detect_poison`, `spell_null`, `spell_refresh`

**Notes:** Adapter chunk. Preserve user-visible messaging semantics; map to Evennia-native msg/display surfaces. Do not port legacy transport internals.

---

### admin

*Adaptation layer · Phase B — foundational semantics*

> Administrative and immortal utilities: bug and diagnostic logging (formatted and timestamped), broadcasting notifications to immortals, immortal notification configuration, character restoration to full health/mana/stamina, login/logout message management, immortal staff rank derivation and comparison, immortal-specific configuration (prefix, display name), command disable checking.

| Property | Value |
|----------|-------|
| Type | infrastructure |
| Mode | adaptation |
| Phase | B |
| Impl wave | 5 |
| Evidence wave | 5 |
| Members | 10 |
| Fan-in (DAG) | 10 |
| Fan-in (all) | 13 |
| Fan-out (DAG) | 2 |
| Migration role | support |
| Target surfaces | admin CmdSet + logging utilities |

**Depends on:** attributes (requires_policy), output (requires_projection)

**Depended on by:** affects, combat, entity_lookup, movement, npc_behavior, objects, persistence, quests, runtime, text_editing

**Notes:** Support chunk, not a core architectural driver. Admin CmdSet + logging utilities.

---

### notes

*Native implementation · Phase C — first vertical slices*

> Asynchronous note and board system: composing, addressing, and attaching notes to characters, appending notes to board lists, writing note files to disk, delivery notification, recipient checking, note removal, spool counting, note visibility filtering, last-read timestamp tracking.

| Property | Value |
|----------|-------|
| Type | domain |
| Mode | native |
| Phase | C |
| Impl wave | 5 |
| Evidence wave | 5 |
| Members | 10 |
| Fan-in (DAG) | 0 |
| Fan-in (all) | 0 |
| Fan-out (DAG) | 2 |
| Migration role | core |
| Target surfaces | Msg system or board contrib + note handler |

**Depends on:** output (requires_projection), state_rules (requires_policy)

**Depended on by:** nothing (leaf)

**Notes:** Small self-contained domain feature. Msg system or board contrib + note handler.

---

### skills_progression

*Native implementation · Phase B — foundational semantics*

> Skill and level progression: skill lookup by name and index, proficiency queries and updates, weapon skill levels, evolution tracking and eligibility, experience gain and level advancement/demotion, experience-per-level calculation, NPC level advancement, skill cost computation, practice and training session display (by group, by key), skill group completion checks, group and guild lookup, spell lookup for casting, holdable and usable level computation, random skill selection, class pose selection, remort skill list display.

| Property | Value |
|----------|-------|
| Type | domain |
| Mode | native |
| Phase | B |
| Impl wave | 5 |
| Evidence wave | 5 |
| Members | 32 |
| Fan-in (DAG) | 6 |
| Fan-in (all) | 8 |
| Fan-out (DAG) | 3 |
| Migration role | core |
| Target surfaces | traits handler + game/skills.py rules + progression handler |

**Depends on:** attributes (requires_policy), output (requires_projection), state_rules (requires_policy)

**Depended on by:** combat, display, magic, movement, objects, persistence

**Enables:** 4 entry points (3 commands, 1 spells)

Commands: `do_autopeek`, `do_groups`, `do_worth`

Spells: `spell_mass_healing`

**Notes:** Core domain system. Traits handler + skills rules + progression handler.

---

### entity_lookup

*Adaptation layer · Phase B — foundational semantics*

> In-game entity resolution: finding characters, NPCs, objects, and players by name within various scopes (room, area, world, inventory, equipment, shopkeeper stock), numbered-target resolution, extra description lookup, flag-based search across characters, objects, rooms, and players, location resolution from names, key possession checks, name expansion for disambiguation, object prototype retrieval, warp-crystal search, help entry lookup, race lookup, random prototype selection.

| Property | Value |
|----------|-------|
| Type | policy |
| Mode | adaptation |
| Phase | B |
| Impl wave | 6 |
| Evidence wave | 6 |
| Members | 34 |
| Fan-in (DAG) | 3 |
| Fan-in (all) | 5 |
| Fan-out (DAG) | 5 |
| Migration role | cross_cutting |
| Target surfaces | search functions + DefaultObject.search overrides |

**Depends on:** admin (requires_infrastructure), output (requires_projection), state_rules (requires_policy), visibility_rules (requires_policy), world_structure (requires_core)

**Depended on by:** combat, objects, persistence

**Notes:** Cross-cutting search/resolution service. Keep standalone — merging into objects would make the plan more DIKU-shaped than Evennia-shaped. Target: search functions + DefaultObject.search overrides.

---

### magic

*Native implementation · Phase D — heavier systemic features*

> Spell casting mechanics: object-triggered spell dispatch (scrolls, wands, staves, potions), saving throws against spells, spell dispelling from characters, chain-spell execution across multiple targets, spell comparison for sorting, incantation text generation.

| Property | Value |
|----------|-------|
| Type | domain |
| Mode | native |
| Phase | D |
| Impl wave | 6 |
| Evidence wave | 6 |
| Members | 6 |
| Fan-in (DAG) | 1 |
| Fan-in (all) | 1 |
| Fan-out (DAG) | 3 |
| Migration role | core |
| Target surfaces | rules module + spell handler + magic CmdSet |

**Depends on:** output (requires_projection), skills_progression (requires_core), state_rules (requires_policy)

**Depended on by:** affects

**Notes:** Small standalone chunk. Spell dispatch, saves, dispels, incantation — a real semantic seam separate from skill lookup/progression.

---

### movement

*Native implementation · Phase C — first vertical slices*

> Character and object movement between rooms: entering and leaving rooms, door and exit resolution, room access via exits, pathfinding, flee from combat, sector-based movement costs, portal and recall traversal, warp crystal destination reading, random and scatter room selection, character extraction from the game world, pet removal, room-level character addition and removal, exit inspection, object placement in rooms, duel and arena room checks, pet creation and follow establishment, tailing, flying and outdoor checks.

| Property | Value |
|----------|-------|
| Type | domain |
| Mode | native |
| Phase | C |
| Impl wave | 6 |
| Evidence wave | 6 |
| Members | 34 |
| Fan-in (DAG) | 8 |
| Fan-in (all) | 10 |
| Fan-out (DAG) | 6 |
| Migration role | core |
| Target surfaces | movement rules + exit/room typeclass hooks |

**Depends on:** admin (requires_infrastructure), output (requires_projection), skills_progression (requires_core), state_rules (requires_policy), visibility_rules (requires_policy), world_structure (requires_core)

**Depended on by:** affects, combat, display, npc_behavior, objects, pvp, quests, runtime

**Enables:** 4 entry points (4 specials)

Specials: `spec_cast_cleric`, `spec_cast_judge`, `spec_cast_mage`, `spec_cast_undead`

**Notes:** Core domain system. Movement rules + exit/room typeclass hooks.

---

### affects

*Native implementation · Phase D — heavier systemic features · Umbrella chunk*

> Affect lifecycle management: applying, joining, and copying affects to characters, objects, and rooms; removing affects by type, pattern, mark, or permanence; querying affect existence and finding specific instances; affect list iteration, sorting, deduplication, and checksum computation; attribute modification from affects; affect cache lookup and display; elemental effect propagation (cold, fire, acid, poison, shock); dispel checks on characters and objects; spell fading and undoing; remort-affect rolling, application, removal, and lookup; blank remort affect repair; gem effect compilation; blade enhancement; plague spreading; protection aura checks; room-level affect ticking; affect flag parsing, type lookup, and bit-to-type conversion; affect comparators for sorting by type, duration, mark, and permanence.

| Property | Value |
|----------|-------|
| Type | domain |
| Mode | native |
| Phase | D |
| Impl wave | 7 |
| Evidence wave | 7 |
| Members | 88 |
| Fan-in (DAG) | 5 |
| Fan-in (all) | 11 |
| Fan-out (DAG) | 6 |
| Migration role | core |
| Target surfaces | buffs handler or contrib + rules integration |

**Depends on:** admin (requires_infrastructure), attributes (requires_policy), magic (requires_core), movement (requires_core), output (requires_projection), state_rules (requires_policy)

**Depended on by:** combat, display, objects, persistence, runtime

**Enables:** 4 entry points (3 commands, 1 spells)

Commands: `do_dump`, `do_mark`, `do_visible`

Spells: `spell_darkness`

**Notes:** Umbrella chunk. Likely becomes a single handler/service in target. Do not split during planning — only split during spec writing if dossier shows clearly separate implementation surfaces.

---

### npc_behavior

*Native implementation · Phase D — heavier systemic features*

> NPC behavioural logic: MobProg program execution (driver, command processing, conditional evaluation, variable translation, keyword matching, percentage checks, string evaluation, line extraction), mob program triggers (speech, fight, death, greet, entry, give, bribe, buy, tick, act), special-function dispatch, NPC hunting AI, mob animation and summoning.

| Property | Value |
|----------|-------|
| Type | domain |
| Mode | native |
| Phase | D |
| Impl wave | 7 |
| Evidence wave | 7 |
| Members | 21 |
| Fan-in (DAG) | 0 |
| Fan-in (all) | 0 |
| Fan-out (DAG) | 7 |
| Migration role | core |
| Target surfaces | AI Script/handler + Character/Object typeclass choice + trigger hooks |

**Depends on:** admin (requires_infrastructure), attributes (requires_policy), movement (requires_core), output (requires_projection), state_rules (requires_policy), visibility_rules (requires_policy), world_structure (requires_core)

**Depended on by:** nothing (leaf)

**Notes:** Late and architecture-sensitive. Depends on chosen NPC model, Script strategy, event/trigger integration, runtime surfaces.

---

### pvp

*Native implementation · Phase D — heavier systemic features*

> Duel and arena mechanics: duel initiation, tracking, and kill resolution, arena setup and clearing, duel list management, arena selection.

| Property | Value |
|----------|-------|
| Type | domain |
| Mode | native |
| Phase | D |
| Impl wave | 7 |
| Evidence wave | 7 |
| Members | 6 |
| Fan-in (DAG) | 0 |
| Fan-in (all) | 0 |
| Fan-out (DAG) | 3 |
| Migration role | core |
| Target surfaces | PvP rules overlay + arena Script + PvP CmdSet |

**Depends on:** movement (requires_core), state_rules (requires_policy), world_structure (requires_core)

**Depended on by:** nothing (leaf)

**Notes:** Small leaf. Defer to late migration.

---

### objects

*Native implementation · Phase C — first vertical slices · Umbrella chunk*

> Object lifecycle and manipulation: creating objects from prototypes, cloning, extracting and destroying objects, transferring objects between characters, rooms, containers, lockers, and strongboxes, equipping and removing worn items, equipment generation and base stat assignment, loot name generation, gem inset, object repair, forging weapon flags, loot eligibility checks, container capacity checks, content spilling on destruction, object weight computation, object user counting, item type and liquid type lookups, anvil ownership, clan equipment disposal.

| Property | Value |
|----------|-------|
| Type | domain |
| Mode | native |
| Phase | C |
| Impl wave | 8 |
| Evidence wave | 8 |
| Members | 43 |
| Fan-in (DAG) | 5 |
| Fan-in (all) | 8 |
| Fan-out (DAG) | 9 |
| Migration role | core |
| Target surfaces | object handlers + object rules + prototypes + shop menu/cmd layer |

**Depends on:** admin (requires_infrastructure), affects (requires_core), attributes (requires_policy), entity_lookup (requires_policy), movement (requires_core), output (requires_projection), skills_progression (requires_core), state_rules (requires_policy), world_structure (requires_core)

**Depended on by:** combat, display, persistence, quests, runtime

**Notes:** Umbrella chunk. Keep separate from entity_lookup. Likely multi-spec later. Object handlers + rules + prototypes + shop layer.

---

### display

*Adaptation layer · Phase C — first vertical slices*

> Information rendering and display assembly: room description and contents display, character appearance in room (short and detailed views), object description formatting, exit listing, score and stat sheet rendering, detailed object/room/mob inspection formatting, minimap generation, affect and evolution display, war event and roster lists, weather descriptions, location and coordinate string rendering, player count for the WHO list, condition description lookup.

| Property | Value |
|----------|-------|
| Type | projection |
| Mode | adaptation |
| Phase | C |
| Impl wave | 9 |
| Evidence wave | 9 |
| Members | 27 |
| Fan-in (DAG) | 0 |
| Fan-in (all) | 2 |
| Fan-out (DAG) | 9 |
| Migration role | support |
| Target surfaces | return_appearance + get_display_* hooks + display helpers |

**Depends on:** affects (requires_core), attributes (requires_policy), movement (requires_core), objects (requires_core), output (requires_projection), skills_progression (requires_core), state_rules (requires_policy), visibility_rules (requires_policy), world_structure (requires_core)

**Depended on by:** nothing (leaf)

**Enables:** 5 entry points (5 commands)

Commands: `do_count`, `do_exlist`, `do_roomexits`, `do_time`, `do_weather`

**Notes:** Projection-only consumer. return_appearance + get_display_* hooks + display helpers.

---

### persistence

*Native implementation · Phase D — heavier systemic features · Umbrella chunk*

> Data serialisation, storage, and retrieval: character save/load to JSON files, pet serialisation, object state persistence, area-file reading (word, string, integer tokens, key-value macros), cJSON structure creation, printing, and value extraction, SQL database queries, commands, error handling, and row iteration, war table and event logging, social table persistence, note file writing, storage locker and departed-player list management, player-index updates, file append utilities, help entry insertion.

| Property | Value |
|----------|-------|
| Type | infrastructure |
| Mode | native |
| Phase | D |
| Impl wave | 9 |
| Evidence wave | 9 |
| Members | 94 |
| Fan-in (DAG) | 6 |
| Fan-in (all) | 7 |
| Fan-out (DAG) | 9 |
| Migration role | support |
| Target surfaces | AttributeHandler + SaverDict; area loading via prototypes/batch-code |

**Depends on:** admin (requires_infrastructure), affects (requires_core), attributes (requires_policy), entity_lookup (requires_policy), objects (requires_core), output (requires_projection), skills_progression (requires_core), state_rules (requires_policy), world_structure (requires_core)

**Depended on by:** arg_parsing, clans, combat, memory, social, text_editing

**Enables:** 1 entry points (1 commands)

Commands: `do_pipe`

**Notes:** Umbrella chunk. Will dissolve into multiple target-side surfaces: character/object save state, content import/area conversion, notes/social persistence, clan/war persistence, SQL integration.

---

### quests

*Native implementation · Phase D — heavier systemic features*

> Quest system: random quest generation and target assignment, skill-quest creation (mob and object variants), quest completion handling and cleanup, quest-point checks, quest information display and usage instructions, questmaster and skill-questmaster location, quest level-range evaluation, quest-object delivery processing.

| Property | Value |
|----------|-------|
| Type | domain |
| Mode | native |
| Phase | D |
| Impl wave | 9 |
| Evidence wave | 9 |
| Members | 16 |
| Fan-in (DAG) | 0 |
| Fan-in (all) | 0 |
| Fan-out (DAG) | 7 |
| Migration role | core |
| Target surfaces | quest handler + quest Script + quest rules |

**Depends on:** admin (requires_infrastructure), attributes (requires_policy), movement (requires_core), objects (requires_core), output (requires_projection), state_rules (requires_policy), world_structure (requires_core)

**Depended on by:** nothing (leaf)

**Enables:** 1 entry points (1 commands)

Commands: `do_swho`

**Notes:** Self-contained feature. Quest handler + Script + rules.

---

### arg_parsing

*Adaptation layer*

> Command-line argument tokenisation: splitting player input into tokens with quote-delimited and dot-notation handling, extracting numbered targets and quantity prefixes, type-tagged argument parsing, keyword matching and word-list checks, character name validation.

| Property | Value |
|----------|-------|
| Type | utility |
| Mode | adaptation |
| Phase | — |
| Impl wave | 10 |
| Evidence wave | 10 |
| Members | 14 |
| Fan-in (DAG) | 0 |
| Fan-in (all) | 7 |
| Fan-out (DAG) | 2 |
| Migration role | support |
| Target surfaces | utility module + Evennia utils.search / arg parsing |

**Depends on:** output (requires_projection), persistence (requires_infrastructure)

**Depended on by:** nothing (leaf)

**Enables:** 284 entry points (196 commands, 82 spells, 6 specials)

Commands: `do_accept`, `do_addapply`, `do_advance`, `do_affects`, `do_afk`, `do_alias`, `do_allow`, `do_allsave`, `do_alternate`, `do_areas`, `do_aura`, `do_autoboot`, `do_autograph`, `do_backup`, `do_bamfin` … and 181 more

Spells: `spell_age`, `spell_armor`, `spell_barrier`, `spell_bless`, `spell_blindness`, `spell_blood_blade`, `spell_blood_moon`, `spell_bone_wall`, `spell_cancellation`, `spell_change_sex` … and 72 more

Specials: `spec_cast_adept`, `spec_fido`, `spec_janitor`, `spec_nasty`, `spec_poison`, `spec_thief`

**Notes:** Adaptation layer. Capture legacy parsing quirks only where behavior matters. Not a major implementation focus.

---

### clans

*Native implementation · Phase D — heavier systemic features*

> Clan organisation system: membership checks, clan power and score computation, inter-clan war initiation, joining, resolution, war kill scoring, war victory handling, war capacity checks, war data compaction, war event recording, war power adjustments, defeat handling, clan roster counting, clan lookup by name or vnum, war lookup, clan list management (append, remove, compare for sorting), clan table persistence.

| Property | Value |
|----------|-------|
| Type | domain |
| Mode | native |
| Phase | D |
| Impl wave | 10 |
| Evidence wave | 10 |
| Members | 30 |
| Fan-in (DAG) | 1 |
| Fan-in (all) | 3 |
| Fan-out (DAG) | 2 |
| Migration role | core |
| Target surfaces | tags/locks + clan handler + global Script or model-backed state |

**Depends on:** output (requires_projection), persistence (requires_infrastructure)

**Depended on by:** combat

**Enables:** 2 entry points (2 commands)

Commands: `do_channels`, `do_exits`

**Notes:** Clean organizational system. Tags/locks + clan handler + global Script.

---

### memory

*Reference only*

> Memory lifecycle management: pooled object allocation and deallocation tracking, garbage-collection marking and deferred deletion, allocation counters, buffer capacity management, cJSON structure creation and teardown, affect cache infrastructure.

| Property | Value |
|----------|-------|
| Type | utility |
| Mode | reference |
| Phase | — |
| Impl wave | 10 |
| Evidence wave | 10 |
| Members | 17 |
| Fan-in (DAG) | 0 |
| Fan-in (all) | 5 |
| Fan-out (DAG) | 1 |
| Migration role | replacement_candidate |
| Target surfaces | not needed (Python GC) |

**Depends on:** persistence (requires_infrastructure)

**Depended on by:** nothing (leaf)

**Enables:** 67 entry points (53 commands, 14 spells)

Commands: `do_auction`, `do_bug`, `do_cedit`, `do_check`, `do_clandeposit`, `do_clanlist`, `do_clanpower`, `do_clanqp`, `do_clantalk`, `do_clanwithdraw`, `do_deputize`, `do_donate`, `do_drop`, `do_edit`, `do_finger` … and 38 more

Spells: `spell_charm_person`, `spell_create_parchment`, `spell_create_rose`, `spell_create_vial`, `spell_farsight`, `spell_gate`, `spell_identify`, `spell_nexus`, `spell_portal`, `spell_protect_container` … and 4 more

**Notes:** Reference-only. Not needed — Python GC.

---

### social

*Native implementation · Phase C — first vertical slices*

> Synchronous communication and social interaction: chat channel messaging and channel membership queries, tells and reply, say and emote, social action execution and lookup (bow, wave, etc.), social table management (insertion, removal, counting), clan channel message dispatch, offline-player ignore management, communication censorship configuration.

| Property | Value |
|----------|-------|
| Type | domain |
| Mode | native |
| Phase | C |
| Impl wave | 10 |
| Evidence wave | 10 |
| Members | 10 |
| Fan-in (DAG) | 0 |
| Fan-in (all) | 0 |
| Fan-out (DAG) | 3 |
| Migration role | core |
| Target surfaces | social CmdSet + channel contrib/handler |

**Depends on:** output (requires_projection), persistence (requires_infrastructure), state_rules (requires_policy)

**Depended on by:** nothing (leaf)

**Enables:** 1 entry points (1 commands)

Commands: `do_memory`

**Notes:** Small leaf. Social CmdSet + channel contrib/handler.

---

### text_editing

*Replacement / contrib*

> In-game line editor: editing session initialisation (descriptions, notes, help entries), line navigation and cursor positioning, line insertion, deletion, and splitting, text replacement within lines, word wrapping, undo, cancel, context-window display, line counting, range validation, blank-line detection, edit status display, buffer backup.

| Property | Value |
|----------|-------|
| Type | utility |
| Mode | replacement |
| Phase | — |
| Impl wave | 10 |
| Evidence wave | 10 |
| Members | 23 |
| Fan-in (DAG) | 0 |
| Fan-in (all) | 0 |
| Fan-out (DAG) | 3 |
| Migration role | support |
| Target surfaces | EvEditor contrib or custom editor handler |

**Depends on:** admin (requires_infrastructure), output (requires_projection), persistence (requires_infrastructure)

**Depended on by:** nothing (leaf)

**Notes:** Use EvEditor contrib unless legacy editor exposes must-preserve behaviors.

---

### combat

*Native implementation · Phase D — heavier systemic features*

> Combat round execution: single and multi-attack resolution per round, damage calculation and application, defense checks (dodge, parry, dual parry, shield block, shield evasion), defensive healing on successful block, hit/miss adjudication, fighting state transitions, death handling (corpse creation, death notification, post-death cleanup), experience distribution after kills, NPC attack behaviour, position updates during combat, special attacks (trip, fireball bash, dragon breath), war score adjustment, duel preparation, attack and weapon type lookups, wielded weapon skill resolution.

| Property | Value |
|----------|-------|
| Type | domain |
| Mode | native |
| Phase | D |
| Impl wave | 11 |
| Evidence wave | 11 |
| Members | 25 |
| Fan-in (DAG) | 1 |
| Fan-in (all) | 1 |
| Fan-out (DAG) | 13 |
| Migration role | core |
| Target surfaces | rules module + combat Script/handler + combat CmdSet |

**Depends on:** admin (requires_infrastructure), affects (requires_core), attributes (requires_policy), clans (requires_core), entity_lookup (requires_policy), movement (requires_core), objects (requires_core), output (requires_projection), persistence (requires_infrastructure), skills_progression (requires_core), state_rules (requires_policy), visibility_rules (requires_policy), world_structure (requires_core)

**Depended on by:** runtime

**Enables:** 67 entry points (48 commands, 12 spells, 7 specials)

Commands: `do_adjust`, `do_align`, `do_battle`, `do_berserk`, `do_brew`, `do_clan_recall`, `do_deny`, `do_duel`, `do_enter`, `do_envenom`, `do_familiar`, `do_firebuilding`, `do_fod`, `do_forge`, `do_goto` … and 33 more

Spells: `spell_calm`, `spell_cure_critical`, `spell_cure_light`, `spell_cure_serious`, `spell_dazzle`, `spell_divine_healing`, `spell_floating_disc`, `spell_heal`, `spell_holy_sword`, `spell_imprint` … and 2 more

Specials: `spec_breath_acid`, `spec_breath_any`, `spec_breath_fire`, `spec_breath_frost`, `spec_breath_gas`, `spec_breath_lightning`, `spec_charm`

**Notes:** Major late heavy chunk. Dependency breadth (13 chunks) makes late wave correct.

---

### runtime

*Evennia substrate*

> Core game loop and connection lifecycle: command interpreter dispatch, main tick loop (character updates, object decay, area refresh), network connection teardown, game-time and weather tick advancement, world entity list management.

| Property | Value |
|----------|-------|
| Type | infrastructure |
| Mode | substrate |
| Phase | — |
| Impl wave | 12 |
| Evidence wave | 12 |
| Members | 9 |
| Fan-in (DAG) | 0 |
| Fan-in (all) | 0 |
| Fan-out (DAG) | 9 |
| Migration role | replacement_candidate |
| Target surfaces | replaced by Evennia server core (Portal/Server, SessionHandler) |

**Depends on:** admin (requires_infrastructure), affects (requires_core), attributes (requires_policy), combat (requires_core), movement (requires_core), objects (requires_core), output (requires_projection), state_rules (requires_policy), world_structure (requires_core)

**Depended on by:** nothing (leaf)

**Enables:** 110 entry points (58 commands, 45 spells, 7 specials)

Commands: `do_at`, `do_backstab`, `do_bash`, `do_brandish`, `do_buy`, `do_cast`, `do_circle`, `do_clone`, `do_copyover`, `do_critical_blow`, `do_crush`, `do_debug`, `do_delete`, `do_dirt`, `do_disarm` … and 43 more

Spells: `spell_acid_blast`, `spell_acid_breath`, `spell_acid_rain`, `spell_animate_gargoyle`, `spell_animate_skeleton`, `spell_animate_wraith`, `spell_animate_zombie`, `spell_blizzard`, `spell_burning_hands`, `spell_call_lightning` … and 35 more

Specials: `spec_clanguard`, `spec_executioner`, `spec_guard`, `spec_mayor`, `spec_ogre_member`, `spec_patrolman`, `spec_troll_member`

**Notes:** Evennia-provided substrate. The game loop, tickers, Scripts already exist. Game-specific hooks are integration concerns attached to other chunks, not a standalone deliverable.

---
