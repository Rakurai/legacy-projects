---
id: combat
name: Combat
kind: system
layer: game_mechanic
parent: null
depends_on: [character_data, affect_system, object_system, world_system]
depended_on_by: [quests, clans_pvp, mobprog_npc_ai]
---

## Overview
<!-- section: overview | grounding: mixed -->

The Combat system resolves all violent conflict between characters. It implements a per-round attack cycle driven by `violence_update()`, processing primary attacks, secondary attacks, and dual-wield through `multi_hit()`. The system handles hit resolution, damage calculation, defensive rolls, elemental effects, death processing, group combat coordination, and escape mechanics.

## Attack Resolution
<!-- section: key_components | grounding: mixed | role: mechanism -->

- Per-round hit calculation considering weapon skill, dexterity, level difference, and situational modifiers
- Dual-wielding and secondary attack chances
- **Combat Loop**: Per-round resolution via `violence_update()` — iterates fighting characters, calls `multi_hit()` for primary attacks, secondary attacks, and dual-wield
- **Hit Resolution**: `one_hit()` performs the core attack — weapon skill check, dexterity/level modifiers, dodge/parry/shield block defensive rolls, damage type interaction with vulnerabilities/resistances
- **Position Effects**: Combat effectiveness varies by position (standing vs. sleeping vs. stunned). Position recovery after being bashed or tripped.

## Damage Pipeline
<!-- section: key_components | grounding: mixed | role: mechanism -->

- Base weapon damage modified by damroll, skill proficiency, enhanced damage, and critical hits
- Damage types (slash, bash, pierce, etc.) interact with vulnerabilities and resistances
- `damage()` applies final damage — sanctuary halving, damage type modifiers, equipment degradation from elemental effects, death threshold check, XP distribution
- **Elemental Effects**: Fire, cold, acid, and shock damage cascading to equipment and room contents. `effects.cc` handles elemental cascading. Items can be destroyed or degraded by elemental exposure.
- **Dispel Mechanics**: Spell and ability removal with level-based saving throws. `dispel.cc` handles spell/affect removal. Dispel magic, cancellation, and specific effect counterspells.

### Attack Type Tables
- **Attack Type Tables** (`attack_table`): Damage types (slash, bash, pierce, etc.), hit message nouns, and associated damage classes for melee attacks. Defined in `const.cc`.

## Death & Corpse Processing
<!-- section: key_components | grounding: mixed | role: edge_case -->

- Death processing with XP loss, corpse creation containing victim's inventory, ghost state for players, and NPC loot generation
- `raw_kill()` handles corpse creation with victim inventory, ghost state for players, NPC loot generation, group auto-loot/auto-gold splitting
- Auto-looting and auto-gold splitting for groups

## Defensive Mechanics
<!-- section: key_components | grounding: mixed | role: mechanism -->

- Dodge, parry, and shield block rolls with skill-based chances
- Special defenses like sanctuary (halves damage) and protective shield
- **Combat Readiness**: Weapon and armor statistics, combat modifiers and bonuses, status effects relevant to combat

## Group Combat
<!-- section: behaviors | grounding: mixed -->

- Group experience splitting, group assist mechanics, and group-wide combat coordination

## Flee & Recall
<!-- section: behaviors | grounding: mixed -->

- Escape mechanics with directional flee, wimpy auto-flee threshold, and recall-to-temple as emergency escape

## Battle/Arena Mode
<!-- section: behaviors | grounding: mixed | role: edge_case -->

- Global battle/arena mode with special rules for organized combat events

## Key Files
<!-- section: key_components | grounding: grounded -->

- `/src/fight.cc` — Core combat resolution (attack loop, hit/damage, death processing)
- `/src/effects.cc` — Elemental damage effects (fire, cold, acid, shock)
- `/src/dispel.cc` — Spell/affect removal mechanics
- `/src/include/Battle.hh` — Structured combat system

## Dependencies
<!-- section: dependencies | grounding: grounded -->

### Dependencies On
- **Character Data** (`character_data`): Characters are the primary actors in combat
- **Affect System** (`affect_system`): Sanctuary halving, poison DOT, stat modifiers
- **Object System** (`object_system`): Weapon damage dice, armor AC, elemental degradation
- **World System** (`world_system`): Battlefield properties and terrain effects

### Depended On By
- **Quests** (`quests`): Combat-related quest objectives
- **Clans & PvP** (`clans_pvp`): PvP rules affect combat outcomes
- **MobProg & NPC AI** (`mobprog_npc_ai`): NPC combat behaviors
