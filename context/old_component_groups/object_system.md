# Object System Component Documentation

## Overview

The Object System manages all tangible items in the game world other than characters, including weapons, armor, containers, furniture, keys, and more. It employs a prototype pattern where object instances are created from templates, maintaining a separation between object definitions and their instances in the game world.

### System Responsibilities
- Managing item creation, properties, and behaviors
- Handling object relationships (containment, equipment)
- Supporting object values and attributes
- Managing object-specific affects and flags
- Providing object lifecycle management

## Core Classes and Interfaces

### Object Entities
- **Object**: Represents a specific instance of an item in the game world
  - Contains core properties like weight, cost, condition
  - Manages location (carried, contained, equipped, in room)
  - Tracks affects (enchantments) on the item
  - Handles object-to-container relationships
  - Supports complex object hierarchies with nesting
  - Implements object state persistence
  - Maintains object instance uniqueness

- **ObjectPrototype**: Template for object creation
  - Stores base data for items (descriptions, stats, behaviors)
  - Used to instantiate object instances in areas
  - Contains static object properties
  - Manages object type-specific behavior rules
  - Enables efficient memory usage through shared data

- **ObjectValue**: Special values for different object types
  - Weapons: damage type, attack type
  - Containers: capacity, flags
  - Food/Drink: fullness, poison status
  - And many other specialized types
  - Provides type-safe value manipulation
  - Supports complex type-specific behaviors
  - Handles range checking and validation
  - Enables object type polymorphism

### Supporting Structures
- **ExtraDescr**: Additional descriptions for object features
  - Keyword-based descriptions for examining specific parts
  - Support for multiple special descriptions per object
  - Enhances world detail and interaction depth
  - Enables object puzzle mechanics

- **EQSocket**: Equipment socket system for item customization
  - Quality and type fields for socketing gems/upgrades
  - Socket creation and management on equipment
  - Support for different socket types and qualities
  - Integration with gem enhancement system

### Item Enhancement Systems
- **Gem System**: Framework for equipment enhancement through gems
  - Socket creation and management on items
  - Gem insertion and removal mechanics
  - Varied gem types with different bonuses
  - Quality-based enhancement calculations
  - Crafting elements for creating and improving gems

- **Loot System V2**: Enhanced treasure generation framework
  - Advanced probability distribution for item drops
  - Context-sensitive loot generation
  - Tiered rarity system with special drops
  - Custom drop tables for different scenarios
  - Specialized item generation for unique drops

## Implementation Details

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
  - **Unique Item Generation**: Extensive system in Object.cc (396 LOC) that handles random property generation with specific probability distributions
- **Gem System**: Socket-based enhancement system for objects using EQSocket
- **Loot System**: Sophisticated item generation from loot tables
  - Multi-tiered loot tables with weighted probabilities
  - Context-sensitive drops based on monster type and level
  - Special/rare item distribution control
  - Enhanced loot system (lootv2) with improved drop mechanics
- **Storage System**: Bank-like storage for player items between sessions
  - Global and area-specific storage locations
  - Capacity limits and access controls
  - Persistence between player sessions
- **Object Persistence**: System for persisting object state between server restarts
  - Preserving objects on the ground
  - Special handling for quest items
  - Modified container persistence

### Object Prototype Implementation
- **Loading**: Prototypes are loaded from area files
- **Instantiation**: Creates individual object instances when needed
- **Customization**: Some instances can be customized from the base prototype

### Object Value Implementation
- **Type-Specific Values**: Each object type uses its value array differently
- **Value Operations**: Arithmetic and bitwise operations on object values
- **Value Interpretation**: Functions to interpret raw values by object type

### Object Relationship Implementation
- **Containment**: Objects can contain other objects (containers)
- **Equipment**: Objects can be equipped in specific slots
- **Stacking**: Similar objects can sometimes stack together
- **Object-to-Character**: Objects can be carried or equipped

## Key Files and Components

### Header Files
- `Object.hh` (89 LOC) - Core object class definition
- `ObjectPrototype.hh` (47 LOC) - Object template system
- `ObjectValue.hh` (84 LOC) - Type-specific value handling
- `ExtraDescr.hh` (28 LOC) - Additional object descriptions
- `EQSocket.hh` (15 LOC) - Equipment socket system
- `gem/gem.hh` (51 LOC) - Gem enhancement system
- `lootv2.hh` (110 LOC) - Enhanced loot generation system

### Implementation Files
- `Object.cc` - Object class implementation
- `ObjectPrototype.cc` - Object prototype management
- `ObjectValue.cc` - Object value operations
- `handler.cc` (relevant sections) - Object relationship management
- `act_obj.cc` (5383 LOC) - Object interaction commands
- `gem/gem.cc` (199 LOC) - Gem socketing enhancement system
- `storage.cc` (157 LOC) - Item storage system management
- `objstate.cc` (184 LOC) - Object persistence between server restarts
- `loot_tables.cc` (1317 LOC) - Core loot distribution system
- `lootv2.cc` (556 LOC) - Enhanced loot generation system

## System Behaviors

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

## Dependencies and Relationships

### Dependencies On
- **World System**: For object placement in rooms
- **Affect System**: For magical effects on objects
- **Event System**: For object-related events

### Depended On By
- **Character System**: For equipment and inventory
- **Combat System**: For weapons and armor calculations
- **Quest System**: For quest items and objectives
- **Shop System**: For buying/selling transactions

## Open Questions and Future Improvements
- The object value system could be refactored to be more type-safe
- Additional object types could be added for special gameplay mechanics
- Object interactions could be expanded for more environmental puzzles
- The socket system could be enhanced for more crafting options

---
