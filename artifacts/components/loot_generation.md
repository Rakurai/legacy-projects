---
id: loot_generation
name: Loot Generation
kind: system
layer: game_mechanic
parent: null
depends_on: [object_system, character_data]
depended_on_by: [combat]
---

## Overview
<!-- section: overview | grounding: mixed -->

The Loot Generation system implements enhanced treasure generation using advanced probability distributions, context-sensitive item creation, a tiered rarity system, and template-based item generation with random modifiers. It uses template objects (vnums 24355–24379) and loot tables to produce dynamically varied equipment drops.

## Loot Tables & Probability
<!-- section: key_components | grounding: mixed | role: mechanism -->

- Advanced probability distribution for item drops
- Context-sensitive loot generation based on monster type and level
- Tiered rarity system with special drops
- Custom drop tables for different scenarios
- Specialized item generation for unique drops
- **Loot Generation Tables**: Name prefixes/suffixes, base stat ranges, modifier pools, and rarity weights defined in `loot_tables.cc`

## Template Item Generation
<!-- section: implementation | grounding: mixed | role: mechanism -->

- Multi-tiered tables with weighted probabilities
- Special/rare item distribution control
- Random attribute modifiers based on probability distributions
- Special weapon properties (flaming, frost, vampiric, etc.)
- Condition and quality variations
- Random prefixes and suffixes for special items

## Key Files
<!-- section: key_components | grounding: grounded -->

- `/src/loot_tables.cc` — Core loot distribution system (1317 LOC)
- `/src/lootv2.cc` — Enhanced loot generation system (556 LOC)
- `/src/include/lootv2.hh` — Enhanced loot generation system (110 LOC)

## Dependencies
<!-- section: dependencies | grounding: grounded -->

### Dependencies On
- **Object System** (`object_system`): Object prototypes and creation
- **Character Data** (`character_data`): Monster level and type for context-sensitive drops

### Depended On By
- **Combat** (`combat`): NPC death triggers loot generation
