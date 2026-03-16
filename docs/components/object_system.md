---
id: object_system
name: Object System
kind: system
layer: data_model
parent: null
depends_on: [world_system, affect_system]
depended_on_by: [combat, magic, economy, quests, character_data, persistence, admin_tools, builder_tools]
---

## Overview
<!-- section: overview | grounding: mixed -->
The Object System manages all tangible items in the game world other than characters, including weapons, armor, containers, furniture, keys, and more. It employs a prototype pattern where object instances are created from templates, maintaining a separation between object definitions and their instances in the game world. This system is fundamental to gameplay as it provides the items that characters interact with, equip, trade, and use to affect the world.

## Responsibilities
<!-- section: responsibilities | grounding: mixed -->

- Managing item creation, properties, and behaviors
- Handling object relationships (containment, equipment)
- Supporting object values and attributes
- Managing object-specific affects and flags
- Providing object lifecycle management
- Implementing specialized systems for loot, storage, and enhancement

## Object Entities
<!-- section: key_components | grounding: grounded -->

- `Object`: Represents a specific instance of an item in the game world
  - Contains core properties like weight, cost, condition
  - Manages location (carried, contained, equipped, in room)
  - Tracks affects (enchantments) on the item
  - Handles object-to-container relationships
  - Supports complex object hierarchies with nesting
  - Implements object state persistence
  - Maintains object instance uniqueness

- `ObjectPrototype`: Template for object creation
  - Stores base data for items (descriptions, stats, behaviors)
  - Used to instantiate object instances in areas
  - Contains static object properties
  - Manages object type-specific behavior rules
  - Enables efficient memory usage through shared data

- `ObjectValue`: Type-specific value handling
  - Weapons: damage type, attack type
  - Containers: capacity, flags
  - Food/Drink: fullness, poison status
  - And many other specialized types
  - Provides type-safe value manipulation
  - Supports complex type-specific behaviors
  - Handles range checking and validation
  - Enables object type polymorphism

### Supporting Structures
- `ExtraDescr`: Additional descriptions for object features
  - Keyword-based descriptions for examining specific parts
  - Support for multiple special descriptions per object
  - Enhances world detail and interaction depth
  - Enables object puzzle mechanics

- `EQSocket`: Equipment socket system for item customization
  - Quality and type fields for socketing gems/upgrades
  - Socket creation and management on equipment
  - Support for different socket types and qualities
  - Integration with gem enhancement system

## Item Enhancement
<!-- section: key_components | grounding: mixed -->

### Item Enhancement Systems
- **Gem System**: Framework for equipment enhancement through gems
  - Socket creation and management on items
  - Gem insertion and removal mechanics
  - Varied gem types with different bonuses
  - Quality-based enhancement calculations
  - Crafting elements for creating and improving gems

- **Loot System V2**: Enhanced treasure generation framework
  > **Note:** Loot generation is documented in [loot_generation.md](loot_generation.md). Cross-reference only.

### Shop System
> **Note:** Shop mechanics are documented in [economy.md](economy.md) as the canonical owner. Brief reference here.

## Data Tables
<!-- section: key_components | grounding: grounded -->

Static lookup tables in `const.cc`, `tables.cc`, and `merc.hh` that parameterize object mechanics.
- **Attack Type Tables** (`attack_table`): Damage types (slash, bash, pierce, etc.), hit message nouns, and associated damage classes for melee attacks.
- **Item Type Tables** (`type_table`): Names and properties for each object type — weapon, armor, container, food, drink, scroll, wand, staff, potion, pill, furniture, etc.
- **Weapon Type Tables** (`weapon_table`): Weapon classes (sword, dagger, mace, axe, etc.) mapped to associated weapon skill, default damage type, and flag sets.
- **Flag Definition Tables**: Named constants for every flag category (act flags, affect flags, room flags, object extra flags, wear location flags, etc.) used for serialization, display, and OLC editing.
- **Loot Generation Tables**: Name prefixes/suffixes, base stat ranges, modifier pools, and rarity weights for the dynamic loot system. See [loot_generation.md](loot_generation.md) for details.

## Implementation Details
<!-- section: implementation | grounding: mixed -->

### Object Implementation
- **Creation and Initialization**: Objects are created from prototypes
- **State Management**: Objects track condition, ownership, and location
- **Attribute System**: Objects have values that vary by type
- **Uniqueness**: Some objects can be tagged as unique across the world
- **Randomization**: System for creating unique items with varied properties
  - Random attribute modifiers based on probability distributions
  - Special weapon properties (flaming, frost, vampiric, etc.)
  - Condition and quality variations
  - Random prefixes and suffixes for special items

### Item Systems
- **Gem System**: Socket-based enhancement system using EQSocket
- **Loot System**: Sophisticated item generation from loot tables
  - Multi-tiered tables with weighted probabilities
  - Context-sensitive drops based on monster type and level
  - Special/rare item distribution control
- **Storage System**: Bank-like storage for player items between sessions
  - Global and area-specific storage locations
  - Capacity limits and access controls
  - Persistence between player sessions
- **Object Persistence**: System for persisting object state between server restarts
  - Preserving objects on the ground
  - Special handling for quest items
  - Modified container persistence

### Object Relationship Implementation
- **Containment**: Objects can contain other objects (containers)
- **Equipment**: Objects can be equipped in specific slots
- **Stacking**: Similar objects can sometimes stack together
- **Object-to-Character**: Objects can be carried or equipped

## Key Files
<!-- section: key_components | grounding: grounded -->

### Header Files
- `/src/include/Object.hh` - Core object class definition (89 LOC)
- `/src/include/ObjectPrototype.hh` - Object template system (47 LOC)
- `/src/include/ObjectValue.hh` - Type-specific value handling (84 LOC)
- `/src/include/ExtraDescr.hh` - Additional object descriptions (28 LOC)
- `/src/include/EQSocket.hh` - Equipment socket system (15 LOC)
- `/src/include/gem/gem.hh` - Gem enhancement system (51 LOC)
- `/src/include/lootv2.hh` - Enhanced loot generation system (110 LOC)

### Implementation Files
- `/src/Object.cc` - Object class implementation with unique item generation (396 LOC)
- `/src/ObjectPrototype.cc` - Object prototype management and loading
- `/src/ObjectValue.cc` - Object value operations and type interpretations
- `/src/handler.cc` - Object relationship management
- `/src/act_obj.cc` - Object interaction commands (5383 LOC)
- `/src/gem/gem.cc` - Gem socketing enhancement system (199 LOC)
- `/src/storage.cc` - Item storage system management (157 LOC)
- `/src/objstate.cc` - Object persistence between server restarts (184 LOC)
- `/src/loot_tables.cc` - Core loot distribution system (1317 LOC)
- `/src/lootv2.cc` - Enhanced loot generation system (556 LOC)
- `/src/const.cc` - Attack type, item type, weapon type, and flag definition tables
- `/src/include/tables.hh` - Table structure declarations
- `/src/tables.cc` - Table serialization and lookup helpers
- `/src/include/merc.hh` - Item type and weapon type struct definitions

## System Behaviors
<!-- section: behaviors | grounding: mixed -->

### Core Behaviors
- **Object Types**: Different types behave differently (weapons, containers, etc.)
- **Object States**: Items can deteriorate, break, or be repaired
- **Light Sources**: Objects can emit light with duration
- **Container Logic**: Objects can contain other objects with capacity limits
- **Lock System**: Objects can be locked/unlocked with keys

### Special Features
- **Magical Items**: Objects can have spell effects or magical properties
- **Cursed Items**: Some objects resist being removed once equipped
- **Trap System**: Objects can be trapped with harmful effects
- **Object Programs**: Some objects can trigger events on certain actions
- **Unique Items**: Special objects that only exist in one instance

## Dependencies
<!-- section: dependencies | grounding: grounded -->

### Dependencies On
- **World System** (`world_system`): For object placement in rooms and environmental context
- **Affect System** (`affect_system`): For magical effects and enchantments on objects

### Depended On By
- **Combat** (`combat`): For weapons, armor, and combat calculations
- **Magic** (`magic`): For spell-casting objects (wands, scrolls, etc.)
- **Economy** (`economy`): For buying, selling, and item transactions
- **Quests** (`quests`): For quest items, tokens, and objective tracking
- **Character Data** (`character_data`): For equipment, inventory, and carried items
- **Persistence** (`persistence`): For item state storage
- **Admin Tools** (`admin_tools`): For item manipulation commands
- **Builder Tools** (`builder_tools`): For item creation and editing
