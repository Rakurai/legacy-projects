# Character Data Model

Core data structures for all living entities — player characters and NPCs.
Covers attributes, player preferences, NPC templates, and stat accessors.

See [../clusters.md](../clusters.md) § Character Data Model for feature overview.

## Key Source Areas
- `Character.cc` / `include/Character.hh` — base character class
- `Player.cc` / `include/Player.hh` — player-specific data
- `MobilePrototype.cc` / `include/MobilePrototype.hh` — NPC templates
- `attribute.cc` — stat accessors and max-stat calculations
- `config.cc` — player preference toggles (colors, display options)
- `mobiles.cc` — NPC service functions (healer interaction)
- `departed.cc` / `include/DepartedPlayer.hh` — departed immortal list
