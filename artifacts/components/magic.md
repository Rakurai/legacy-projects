---
id: magic
name: Magic
kind: system
layer: game_mechanic
parent: null
depends_on: [character_data, affect_system, object_system, skills_progression]
depended_on_by: [combat, mobprog_npc_ai]
---

## Overview
<!-- section: overview | grounding: mixed -->

The Magic system implements spell casting, spell effects, and the complete spell library. It covers mana-cost casting with skill checks, ~200 individual spell implementations, remort prestige spells, object-based casting (wands, staves, scrolls, potions), saving throws, and verbal components.

## Spell Casting
<!-- section: key_components | grounding: mixed | role: mechanism -->

- Mana-cost casting with skill checks, interruption from damage, and position requirements
- Cast command with target parsing (self, character, object, room, direction)

## Spell Library
<!-- section: key_components | grounding: mixed -->

~200 individual spell implementations covering:
- *Offensive*: Magic missile, fireball, lightning bolt, chain lightning, etc.
- *Defensive*: Armor, shield, sanctuary, stone skin, protection evil/good
- *Healing*: Cure light/serious/critical, heal, refresh, restoration
- *Enhancement*: Giant strength, haste, bless, frenzy, holy word
- *Transportation*: Teleport, gate, word of recall, summon, portal
- *Detection*: Detect magic/evil/hidden/invis, identify, locate object
- *Affliction*: Curse, poison, plague, blind, sleep, charm
- *Utility*: Enchant weapon/armor, recharge, create food/water, continual light

## Remort Spells
<!-- section: key_components | grounding: mixed -->

High-tier spells available only after remort — sheen, focus, paralyze, and other prestige abilities.

## Object Casting
<!-- section: key_components | grounding: mixed | role: mechanism -->

Items with spell charges (wands, staves, scrolls, potions, pills) that trigger spell effects on use.

## Saves & Verbal Components
<!-- section: behaviors | grounding: mixed -->

- **Spell Saves**: Level-based saving throw system determining full/partial/no effect for offensive spells.
- **Verbal Components**: Spoken incantation display with garbled text for observers who don't know the spell.

## Key Files
<!-- section: key_components | grounding: grounded -->

- `/src/magic.cc` — Spell system implementation (~7,000 LOC, ~200 spells)
- `/src/rmagic.cc` — Remort-tier spell implementations
- `/src/include/magic.hh` — Spell system interface

## Dependencies
<!-- section: dependencies | grounding: grounded -->

### Dependencies On
- **Character Data** (`character_data`): Caster and target attributes
- **Affect System** (`affect_system`): Spell effects apply as affects
- **Object System** (`object_system`): Object casting items (wands, scrolls, etc.)
- **Skills & Progression** (`skills_progression`): Spell proficiency and learning

### Depended On By
- **Combat** (`combat`): Spells used in combat
- **MobProg & NPC AI** (`mobprog_npc_ai`): NPC casting behaviors
