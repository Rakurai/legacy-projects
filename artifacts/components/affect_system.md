---
id: affect_system
name: Affect System
kind: system
layer: game_mechanic
parent: null
depends_on: [character_data, object_system]
depended_on_by: [combat, magic, skills_progression, world_system]
---

## Overview
<!-- section: overview | grounding: mixed -->

The Affect System manages status effects that modify characters, objects, and rooms. It handles affect application, stacking rules, duration tracking, modifier caching for performance, and the registry of all affect types. Affects are the primary mechanism through which spells, skills, and environmental conditions modify game entities.

## Affect Application & Removal
<!-- section: key_components | grounding: mixed | role: mechanism -->

- Applying effects with type, duration, modifier value, modifier target (stat, skill, AC, hitroll, damroll, saves, etc.), and associated bitvector flags (invisible, detect hidden, flying, etc.)
- Handles affect-on-apply and affect-on-removal callbacks

## Character Affects
<!-- section: key_components | grounding: mixed -->

- Temporary modifications to character stats, skills, and flags
- Examples: strength buff, poison DOT, blindness, haste, sanctuary

### Condition Monitoring
- Current effects and their durations
- Beneficial and harmful condition tracking
- Recovery rates and estimated durations
- Status effect stacking and interaction display

## Object Affects
<!-- section: key_components | grounding: mixed -->

- Enchantments on items that modify wielder stats when equipped
- Permanent or temporary
- Supports stacking rules

## Room Affects
<!-- section: key_components | grounding: mixed -->

- Environmental effects on rooms — darkness, silence, etc.
- Applied and removed with proper notification

## Stacking & Caching
<!-- section: implementation | grounding: mixed | role: mechanism -->

- **Affect Stacking**: Rules for what happens when the same affect is applied twice — replace, extend duration, increase modifier, or reject.
- **Affect Caching**: Performance-optimized stat recalculation that caches aggregate modifier values to avoid recomputing on every stat check.
- **Affect List Management**: Container for managing ordered sets of affects with add/remove/search operations.

## Affect Table
<!-- section: key_components | grounding: grounded -->

Registry of all affect types with display names, durations, and behavior flags.

## Key Files
<!-- section: key_components | grounding: grounded -->

### Header Files
- `/src/include/affect/Affect.hh` — Affect class definition
- `/src/include/affect/Type.hh` — Affect type enum
- `/src/include/affect/affect_list.hh` — Affect list interface

### Implementation Files
- `/src/affect/affect.cc` — Core affect application and removal
- `/src/affect/affect_char.cc` — Character-specific affect handling
- `/src/affect/affect_obj.cc` — Object-specific affect handling
- `/src/affect/affect_room.cc` — Room-specific affect handling
- `/src/affect/affect_list.cc` — Affect container operations
- `/src/affect/affect_cache_array.cc` — Stat modifier caching
- `/src/affect/affect_table.cc` — Affect type registry

## Dependencies
<!-- section: dependencies | grounding: grounded -->

### Dependencies On
- **Character Data** (`character_data`): Characters are the primary targets for affects
- **Object System** (`object_system`): Objects can have enchantment affects

### Depended On By
- **Combat** (`combat`): Sanctuary, poison, stat modifiers during combat
- **Magic** (`magic`): Spells apply affects
- **Skills & Progression** (`skills_progression`): Skill effects as affects
- **World System** (`world_system`): Room affects
