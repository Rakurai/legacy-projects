# Combat System

All mechanics for resolving violent conflict — attack resolution, damage
calculation, defensive checks, elemental effects, dispel, death processing,
and group combat.

See [../clusters.md](../clusters.md) § Combat System for feature overview.

## Key Source Areas
- `fight.cc` — core combat loop, attack/damage/death resolution
- `effects.cc` — elemental damage effects (fire, cold, acid, shock)
- `dispel.cc` — spell/affect removal mechanics
- `Battle.cc` / `include/Battle.hh` — global battle/arena state
