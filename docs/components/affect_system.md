# Affect System

Provides status effect management for characters, objects, and rooms. Handles
application, removal, stacking, caching, and the affect type registry.

See [../clusters.md](../clusters.md) § Affect System for feature overview.

## Key Source Areas
- `affect/affect.cc` — core affect application and removal
- `affect/affect_char.cc` — character-specific affect handling
- `affect/affect_obj.cc` — object-specific affect handling
- `affect/affect_room.cc` — room-specific affect handling
- `affect/affect_list.cc` — affect container operations
- `affect/affect_cache_array.cc` — stat modifier caching
- `affect/affect_table.cc` — affect type registry
- `include/affect/Affect.hh` — Affect class definition
- `include/affect/Type.hh` — affect type enum
- `include/affect/affect_list.hh` — affect list interface
