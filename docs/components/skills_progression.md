---
id: skills_progression
name: Skills & Progression
kind: system
layer: game_mechanic
parent: null
depends_on: [character_data, affect_system]
depended_on_by: [combat, magic, quests]
---

## Overview
<!-- section: overview | grounding: mixed -->

The Skills & Progression system handles character advancement mechanics including skill practice, level advancement, the remort prestige system, and the skill/spell table registry. It manages how characters learn, improve, and gain new abilities over the course of gameplay.

## Practice & Gain
<!-- section: key_components | grounding: mixed | role: mechanism -->

- `skills.cc`: Skill system implementation — practice sessions at guild trainers, gain command for acquiring skill groups, proficiency tracking
- **Skill Groups**: Bundled skill packages that can be learned as units, with per-class cost ratings

### Skill & Ability Status
- Known skills and spells with proficiency levels
- Practice and training status information
- Prerequisite and advancement paths

## Level Advancement
<!-- section: key_components | grounding: mixed | role: mechanism -->

- XP-based leveling with stat gains, HP/mana/move increases, practice/train awards, and title changes per class
- Experience and progression tracking: experience points, level information, training points and options

## Remort System
<!-- section: key_components | grounding: mixed | role: mechanism -->

- Prestige reincarnation allowing high-level characters to restart with permanent bonuses
- Remort affects (raffects) provide persistent stat modifiers
- Extra-class skill slots let characters learn abilities from other classes

## Skill & Spell Tables
<!-- section: key_components | grounding: grounded -->

Static lookup tables in `const.cc`, `tables.cc`, and `merc.hh`:
- **Skill & Spell Tables** (`skill_table`): Complete registry of every skill and spell with level requirements per class, mana costs, target types, minimum positions, damage nouns, and function pointers to implementations.
- **Skill Group Tables** (`group_table`): Bundles of skills that can be learned together, with per-class cost ratings.

## Key Files
<!-- section: key_components | grounding: grounded -->

- `/src/skills.cc` — Skill system implementation (1783 LOC)
- `/src/set-stat.cc` — Attribute modification system (2197 LOC)
- `/src/remort.cc` — Remort system, raffects, extra-class skill slots

## Dependencies
<!-- section: dependencies | grounding: grounded -->

### Dependencies On
- **Character Data** (`character_data`): Character attributes and class/race data
- **Affect System** (`affect_system`): Skill effects applied as affects

### Depended On By
- **Combat** (`combat`): Weapon skills, defensive skills
- **Magic** (`magic`): Spell proficiency and learning
- **Quests** (`quests`): Quest point rewards, advancement objectives
