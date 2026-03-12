# Data Tables

Pure data definitions parameterizing game mechanics. Race, class, skill, spell,
attack, weapon, item type, and flag definition tables. In a rewrite, candidates
for externalization to config files or a database.

See [../clusters.md](../clusters.md) § Data Tables for feature overview.

## Key Source Areas
- `const.cc` — race_table, guild_table, skill_table, group_table, attack_table, weapon_table, item_table
- `tables.cc` — flag tables, random name syllables, lookup helpers
- `loot_tables.cc` — loot generation data (name prefixes/suffixes, stat ranges, mod pools)
- `skill/skill_table.cc` — skill type definitions
- `include/constants.hh` — constant value definitions
- `include/merc.hh` — core type definitions and struct layouts for table entries
- `include/tables.hh` — table structure declarations
