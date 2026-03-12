# Game Subsystems

This document defines the subsystem boundaries for the Legacy MUD codebase,
organized into groups suitable for independent rewrite planning. Each subsystem is
described by its features and responsibilities — not by source files.

---

## Core Infrastructure

### 1. Game Engine

The heartbeat of the server. Owns the main loop, the global tick/update cycle,
entity lifecycle management, and the `act()` message dispatch system.

**Features:**
- **Main Loop**: Accepts connections, processes input, dispatches commands, sends
  output, and sleeps until the next pulse. All timing originates here.
- **Tick System**: Periodic updates for character regeneration, object decay, NPC
  wandering, aggression checks, weather changes, area resets, auto-saving, and
  auction countdowns. Each subsystem is called at its own pulse interval.
- **Entity Lifecycle**: The factory and disposal layer for all live game objects.
  Creates Character and Object instances from prototype templates. Moves entities
  between rooms, inventories, and containers. Extracts (destroys) entities from
  the world with proper cleanup of references, affects, and group membership.
- **Message Dispatch**: The `act()` system — formats context-sensitive messages
  with pronoun/name substitution (`$n`, `$N`, `$e`, `$p`, etc.) and delivers them
  to appropriate recipients (actor, victim, bystanders, room, world) with
  visibility checks, snoop forwarding, and arena spectating support.
- **Global State**: The `Game` singleton providing access to `World`, port
  configuration, shutdown coordination, and boot-time initialization sequencing.
- **Game Time**: In-game calendar with hours, days, months, years. Day/night
  cycle affecting visibility and certain gameplay mechanics. Sunlight state
  tracking (dark, sunrise, light, sunset).

**Depends on:** Utilities, Memory & GC, Event Dispatcher
**Depended on by:** Everything

---

### 2. Networking

Manages all player connections from TCP socket to game state, including the
login/character-creation state machine.

**Features:**
- **Socket Management**: TCP listener with non-blocking I/O, connection
  acceptance, host resolution, and signal handling. IPv6 support.
- **Descriptor Lifecycle**: Each connection is a Descriptor object tracking
  input/output buffers, connection state, snoop chains, and the associated
  Character once logged in.
- **Telnet Protocol**: Option negotiation (NAWS, TTYPE, MCCP, MXP), IAC sequence
  processing, and terminal capability detection for modern MUD clients.
- **Terminal Control**: VT100 escape sequences for color, cursor positioning,
  and screen clearing. ANSI color code translation throughout output.
- **Connection State Machine**: A progression of states from initial connection
  through name entry, password verification (or new character creation with race,
  class, sex, alignment, weapon, stats, deity selection), MOTD display, and
  finally the playing state. Handles reconnection to linkdead characters and
  connection breaking for duplicate logins.
- **Input/Output Buffering**: Command queuing with history, output pagination
  (the "more" prompt), prompt generation with dynamic stat display, and bandwidth
  management.
- **Copyover**: Hot-restart capability that preserves open connections across
  server restarts by passing file descriptors to the new process.

**Depends on:** Game Engine, Character Data Model, Persistence
**Depended on by:** Command Interpreter, all player-facing systems

---

### 3. Command Interpreter

Translates player text input into game actions.

**Features:**
- **Command Dispatch**: Looks up commands by name (with abbreviation support)
  from a registered command table and invokes the handler function. Each command
  has a minimum level, position requirement, and log flag.
- **Permission Checking**: Validates that the character's level and position
  allow the command. Immortal commands are level-gated. Certain commands require
  standing, fighting, or sleeping positions.
- **Command Disabling**: Administrators can disable specific commands at runtime
  with a reason, persisted in the database. Disabled commands are blocked for
  non-immortals.
- **Alias Expansion**: Player-defined command shortcuts with positional parameter
  substitution ($1, $2, $*). Aliases are expanded before interpretation, with
  recursion protection.
- **Social Fallback**: Unrecognized commands are checked against the social
  action table before returning "Huh?".
- **Spam Throttling**: Limits command rate to prevent abuse, with warnings and
  automatic disconnection for persistent offenders.

**Depends on:** Game Engine, Networking
**Depended on by:** Every command implementation

---

### 4. Event Dispatcher

A lightweight publish-subscribe system for inter-system communication.

**Features:**
- **Event Registration**: Systems register handlers for specific event types.
- **Event Dispatch**: Events are broadcast to all registered handlers with
  contextual data (actor, target, location, etc.).
- **Safe Iteration**: Handlers can be added or removed during dispatch without
  corrupting the iteration.
- **Priority Ordering**: Handlers are invoked in priority order for critical
  events.

**Depends on:** None (standalone infrastructure)
**Depended on by:** Game Engine, Combat, various systems

---

### 5. Utilities

Shared infrastructure libraries used throughout the codebase.

**Features:**
- **Custom String Class**: Copy-on-write string with null-awareness (nullptr ≠
  empty). Lightweight alternative to std::string used everywhere.
- **Flag System**: Bitfield class supporting A-Z, a-z, 0-9 bit positions.
  Type-safe testing, setting, clearing, toggling. Serialization to/from
  human-readable letter strings. Used for act flags, affect flags, room flags,
  item flags, etc.
- **Format System**: Type-safe printf-style string formatting with buffer
  management. Custom formatters for game types.
- **Argument Parsing**: Tokenization of player input with quote handling,
  number.name format parsing, quantity extraction.
- **Entity Lookup**: Name-based searching for characters and objects in scope
  (room, inventory, world). Supports partial matching, visibility rules,
  numbered targets ("2.sword"), and fuzzy matching.
- **Random Number Generation**: Dice rolling (XdY+Z), percentage checks, range
  selection, weighted random choice. Seeded RNG.
- **Type Information**: Runtime type name resolution and type-safe casting
  utilities.
- **Logging**: Multi-severity (bug, log, error) message recording to files and
  wiznet channel. Configurable verbosity.
- **File Tail**: Real-time file watching with line buffering for admin log
  monitoring.
- **Image Utilities**: ASCII/PNG image rendering for worldmap generation.

**Depends on:** Standard library
**Depended on by:** Everything

---

### 6. Memory & Garbage Collection

Object pooling and deferred-deletion infrastructure for a long-running server.

**Features:**
- **Object Pooling** (`Pooled<T>`): Template-based memory pools for frequently
  allocated types (Character, Descriptor, Object). Reduces allocation overhead
  and memory fragmentation.
- **Garbage Collection** (`Garbage` base class): Reference-counted objects with
  mark-for-deletion semantics. Objects are not freed immediately but collected at
  safe points in the game loop.
- **Safe Container** (`GarbageCollectingList<T>`): Linked list that handles
  deferred deletion, allowing safe iteration even when elements are extracted
  during traversal.

**Depends on:** None (standalone infrastructure)
**Depended on by:** Game Engine, Character Data Model, Object System

---

### 7. Data Tables

Pure data definitions that parameterize game mechanics. In a rewrite, these could
be externalized to configuration files or a database.

**Features:**
- **Race Definitions**: Stats, abilities, size, vulnerabilities, resistances, and
  special flags for each playable and NPC race.
- **Guild/Class Definitions**: Base stat priorities, skill groups, titles by
  level, and class-specific behaviors for each character class.
- **Skill & Spell Tables**: Complete registry of every skill and spell with
  level requirements per class, mana costs, target types, damage types, and
  function pointers to implementations.
- **Skill Group Tables**: Bundles of skills that can be learned together,
  with cost-per-class ratings.
- **Attack Type Tables**: Damage types, hit messages, and associated damage
  classes for melee attacks.
- **Item Type Tables**: Properties for each object type (weapon, armor,
  container, food, etc.).
- **Weapon Type Tables**: Weapon classes with associated skill, damage type,
  and flag mappings.
- **Flag Definition Tables**: Named constants for every flag category (act,
  affect, room, object, wear location, etc.) used for serialization and display.
- **Loot Generation Tables**: Name prefixes/suffixes, base stat ranges, modifier
  pools, and rarity weights for the dynamic loot system.
- **Random Name Syllables**: Syllable tables for procedural NPC name generation.

**Depends on:** Utilities (Flags, String)
**Depended on by:** Combat, Magic, Character Progression, Object System, Admin Commands

---

## Entity Systems

### 8. Character Data Model

Core data structures and accessors for all living entities.

**Features:**
- **Character Base**: The unified type for players and NPCs. Attributes (str,
  int, wis, dex, con), hit points, mana, move, level, alignment, gold, and
  experience. Equipment slots and inventory. Position (standing, sitting,
  sleeping, fighting). Visibility flags and immunity/vulnerability/resistance
  modifiers.
- **Player Data**: Authentication (name, password hash), configuration
  preferences (color toggles, display options, ANSI color mappings),
  communication state (channels, ignore list), quest/achievement tracking,
  condition trackers (hunger, thirst, drunk), and prompt format customization.
- **NPC Templates** (Mobile Prototypes): Template definitions loaded from area
  files — base stats, descriptions, shop assignments, special function pointers,
  damage dice, wealth, and act flags. Instantiated into live Characters when
  areas reset.
- **Stat Accessors**: Max-stat calculations accounting for race, class, equipment
  bonuses, and remort bonuses. Attribute-to-apply flag mapping.
- **NPC Services**: Healer mob interactions where players purchase healing spells
  from flagged NPCs. Shop interfaces for NPC merchants.
- **Player Preferences**: The `config` command for toggling personal display
  settings — color schemes for channels/score/misc, censor mode, brief mode,
  compact mode, and auto-assist/auto-exit/auto-gold/auto-loot/auto-split.
- **Departed Immortals**: Memorial list of former immortal characters.

**Depends on:** Utilities, Memory & GC, Affect System
**Depended on by:** Everything that interacts with characters

---

### 9. Character Progression

Systems governing character advancement and specialization.

**Features:**
- **Level Advancement**: XP-based leveling with stat gains, HP/mana/move
  increases, practice/train awards, and title changes per class.
- **Skill Learning**: Practice sessions at guild trainers to improve skill
  proficiency. Gain command for acquiring new skill groups. Display of available
  and learned skills by class.
- **Remort System**: Prestige reincarnation allowing high-level characters to
  restart with permanent bonuses. Remort affects (raffects) provide persistent
  stat modifiers. Extra-class skill slots let characters learn abilities from
  other classes.
- **Skill Groups**: Bundled skill packages that can be learned as units, with
  per-class cost ratings determining how many creation points they consume.

**Depends on:** Character Data Model, Data Tables, Magic System
**Depended on by:** Combat, Quest System

---

### 10. Object System

All tangible items in the game world: weapons, armor, containers, keys, food,
furniture, and more.

**Features:**
- **Object Instances**: Created from prototype templates with properties like
  weight, cost, condition, item type, wear flags, and extra flags. Track location
  (carried, in room, in container, equipped). Support enchantments and custom
  extra descriptions.
- **Object Prototypes**: Template definitions loaded from area files. Define base
  stats, descriptions, and type-specific values. Object instances reference their
  prototype for shared static data.
- **Type-Specific Values**: Union-based property system where each item type
  (weapon, armor, container, drink, food, furniture, etc.) has its own set of
  meaningful values (damage dice, AC, capacity, liquid type, etc.).
- **Equipment & Wear**: Slot-based equipment system with wear location flags.
  Equipping/removing items modifies character stats through applies.
- **Containers & Nesting**: Objects can contain other objects with weight and
  item-count limits. Supports locked containers with key objects.
- **Gem Enhancement**: Socket-based item enhancement system where gems can be
  applied to equipment for stat bonuses.
- **Dynamic Loot Generation**: Procedural item creation using template objects,
  random affixes (prefixes/suffixes), rarity tiers, and stat rolls. Generates
  unique items with names like "Gleaming Sword of the Bear."
- **Shops**: NPC merchant system with buy/sell price calculations, item type
  restrictions, and profit margins.
- **Object State Persistence**: Ground-state objects (lying in rooms) are
  serialized across copyovers/crashes so they survive restarts.
- **Storage System**: Persistent storage lockers for player items between
  sessions.

**Depends on:** Utilities, Memory & GC, Affect System, Data Tables
**Depended on by:** Combat, Character Data Model, Persistence, Economy

---

### 11. World System

The physical structure of the game environment: areas, rooms, exits, weather,
time, and spatial mapping.

**Features:**
- **Areas**: Distinct geographical regions loaded from `.are` files. Each area
  contains rooms, object prototypes, mobile prototypes, and resets. Areas track
  age and player presence for reset scheduling.
- **Rooms**: Individual locations connected by exits. Properties include sector
  type (terrain), room flags (safe, private, no-mob, dark, indoors), light level
  tracking, and extra descriptions. Rooms can have temporary affects.
- **Room Prototypes & Instances**: Rooms are instantiated from prototypes,
  supporting multiple instances of the same template (instanced content).
- **Exits & Doors**: Directional connections between rooms (N/S/E/W/U/D). Exits
  can have doors with open/closed/locked states, key requirements, and hidden
  flags. Supports one-way connections.
- **Area Resets**: Timed respawning of NPCs, objects, and door states. Reset
  instructions specify mob/object placement, equipment loading, and room state.
  Resets fire based on area age and player presence (immortals don't count).
- **Weather Simulation**: Dynamic weather with atmospheric pressure tracking,
  seasonal patterns, and sky condition progression (clear → cloudy → rainy →
  lightning). Weather affects visibility and certain abilities.
- **World Map**: ASCII/image-based overworld map with color-coded terrain. Uses
  quadtree spatial indexing for efficient area queries. Coordinate system mapping
  areas to world positions.
- **Regions**: Named geographical regions grouping areas for thematic
  organization and map positioning.
- **Scan**: Multi-directional awareness showing characters and features in
  adjacent rooms, with distance-based detail degradation and skill modifiers.
- **Hunt/Track**: BFS pathfinding for tracking targets across the world.
  Skill-based success checks with environmental modifiers (terrain, weather).
- **Movement**: Directional movement commands consuming movement points based on
  sector type. Handles door opening, swim checks, fly requirements, and
  movement-triggered events (greet progs, aggression checks).

**Depends on:** Utilities, Game Engine, Character Data Model
**Depended on by:** Combat, Quests, MobProg, Navigation commands

---

## Game Mechanics

### 12. Combat System

All mechanics for resolving violent conflict between characters.

**Features:**
- **Attack Resolution**: Per-round hit calculation considering weapon skill,
  dexterity, level difference, and situational modifiers. Dual-wielding and
  secondary attack chances.
- **Damage Calculation**: Base weapon damage modified by damroll, skill
  proficiency, enhanced damage, and critical hits. Damage types (slash, bash,
  pierce, etc.) interact with vulnerabilities and resistances.
- **Defensive Checks**: Dodge, parry, and shield block rolls with skill-based
  chances. Special defenses like sanctuary (halves damage) and protective shield.
- **Elemental Effects**: Fire, cold, acid, and shock damage cascading to
  equipment and room contents. Items can be destroyed or degraded by elemental
  exposure.
- **Dispel Mechanics**: Spell and ability removal with level-based saving throws.
  Dispel magic, cancellation, and specific effect counterspells.
- **Death & Corpse**: Death processing with XP loss, corpse creation containing
  victim's inventory, ghost state for players, and NPC loot generation.
  Auto-looting and auto-gold splitting for groups.
- **Group Combat**: Group experience splitting, group assist mechanics, and
  group-wide combat coordination.
- **Battle State**: Global battle/arena mode with special rules for organized
  combat events.
- **Position Effects**: Combat effectiveness varies by position (standing vs.
  sleeping vs. stunned). Position recovery after being bashed or tripped.
- **Flee & Recall**: Escape mechanics with directional flee, wimpy auto-flee
  threshold, and recall-to-temple as emergency escape.

**Depends on:** Character Data Model, Affect System, Object System, Data Tables
**Depended on by:** Quest System, PvP, MobProg

---

### 13. Magic System

Spell casting, spell effects, and the complete spell library.

**Features:**
- **Spell Casting**: Mana-cost casting with skill checks, interruption from
  damage, and position requirements. Cast command with target parsing (self,
  character, object, room, direction).
- **Spell Library**: ~200 individual spell implementations covering:
  - *Offensive*: Magic missile, fireball, lightning bolt, chain lightning, etc.
  - *Defensive*: Armor, shield, sanctuary, stone skin, protection evil/good
  - *Healing*: Cure light/serious/critical, heal, refresh, restoration
  - *Enhancement*: Giant strength, haste, bless, frenzy, holy word
  - *Transportation*: Teleport, gate, word of recall, summon, portal
  - *Detection*: Detect magic/evil/hidden/invis, identify, locate object
  - *Affliction*: Curse, poison, plague, blind, sleep, charm
  - *Utility*: Enchant weapon/armor, recharge, create food/water, continual light
- **Remort Spells**: High-tier spells available only after remort — sheen, focus,
  paralyze, and other prestige abilities.
- **Object Casting**: Items with spell charges (wands, staves, scrolls, potions,
  pills) that trigger spell effects on use.
- **Spell Saves**: Level-based saving throw system determining full/partial/no
  effect for offensive spells.
- **Verbal Components**: Spoken incantation display with garbled text for
  observers who don't know the spell.

**Depends on:** Character Data Model, Affect System, Combat System (bidirectional), Data Tables
**Depended on by:** Object System (enchanting), NPC Behavior, Quest System

---

### 14. Affect System

Status effects that modify characters, objects, and rooms.

**Features:**
- **Affect Application**: Applying effects with type, duration, modifier value,
  modifier target (stat, skill, AC, hitroll, damroll, saves, etc.), and
  associated bitvector flags (invisible, detect hidden, flying, etc.).
- **Character Affects**: Temporary modifications to character stats, skills, and
  flags. Examples: strength buff, poison DOT, blindness, haste, sanctuary.
  Handles affect-on-apply and affect-on-removal callbacks.
- **Object Affects**: Enchantments on items that modify wielder stats when
  equipped. Permanent or temporary. Supports stacking rules.
- **Room Affects**: Environmental effects on rooms — darkness, silence, etc.
  Applied and removed with proper notification.
- **Affect Stacking**: Rules for what happens when the same affect is applied
  twice — replace, extend duration, increase modifier, or reject.
- **Affect Caching**: Performance-optimized stat recalculation that caches
  aggregate modifier values to avoid recomputing on every stat check.
- **Affect Table**: Registry of all affect types with display names, durations,
  and behavior flags.
- **Affect List Management**: Container for managing ordered sets of affects with
  add/remove/search operations.

**Depends on:** Utilities (Flags)
**Depended on by:** Character Data Model, Combat, Magic, Object System

---

## Content & Scripting

### 15. MobProg System

Scripting and behavior systems for NPC artificial intelligence.

**Features:**
- **Script Language**: Compact scripting language embedded in area files.
  Supports conditional logic (if/else/endif), variable substitution ($n, $i, $r,
  $t for actor/self/random/target), comparison operators (==, !=, >, <), and
  string matching.
- **Trigger Types**: Scripts fire on specific events:
  - *SPEECH_PROG*: When a player says specific keywords
  - *GREET_PROG*: When a player enters the room
  - *FIGHT_PROG*: Each combat round
  - *DEATH_PROG*: When the NPC dies
  - *HITPRCNT_PROG*: When NPC health drops below a threshold
  - *ENTRY_PROG*: When the NPC enters a new room
  - *BRIBE_PROG*: When given a specific amount of gold
  - *GIVE_PROG*: When given a specific object
  - *RAND_PROG*: Random chance each tick
  - *TIME_PROG*: At specific in-game hours
  - *ACT_PROG*: When a specific `act()` message is seen
- **Mob Commands**: NPC-only commands available in scripts — mpecho, mptransfer,
  mpforce, mpjunk, mppurge, mpgoto, mpat, mpoload, mpmload, mpkill, mpasound.
- **Script Execution**: Line-by-line interpreter with command dispatch through
  the normal command interpreter. Supports delayed execution via action lists
  queued for later processing.
- **Special Functions**: Hardcoded C++ NPC behaviors (predating MobProgs) assigned
  via function pointers. Includes: spec_cast_mage, spec_cast_cleric,
  spec_breath_fire, spec_executioner, spec_guard, spec_thief, spec_fido,
  spec_janitor, and more. Each fires during the NPC update tick.

**Depends on:** Character Data Model, Command Interpreter, World System
**Depended on by:** World System (area files), Quest System

---

### 16. Notes & Editor

In-game text editing and persistent message boards.

**Features:**
- **Line Editor**: A line-based text editor (similar to `ed`) for composing
  descriptions, notes, and help entries. Commands for insert, delete, change,
  list, wrap, format, search/replace, undo, and done/cancel.
- **Note Boards**: Multiple themed note boards (general notes, ideas, changes,
  news, immortal quests, penalties). Each board has its own file-based storage.
- **Note Composition**: Multi-recipient addressing with "to" field parsing.
  Subject lines. Editing body text via the line editor.
- **Note Reading**: Unread tracking per character. Spool browsing with
  next/previous navigation. Catchup command to mark all as read.
- **Note Persistence**: Notes stored in flat files with timestamps, expiration
  dates, and sender/recipient data. Loaded at boot.
- **Level-Gated Access**: Board visibility and posting permissions based on
  character level and role.

**Depends on:** Persistence, Character Data Model, Editor framework
**Depended on by:** Social & Communication (note notifications)

---

### 17. Help System

Searchable in-game documentation.

**Features:**
- **Help Lookup**: Keyword-based search across all help entries. Partial matching
  and multi-keyword support.
- **Level Gating**: Help entries have minimum level requirements — staff-only
  documentation is hidden from regular players.
- **Category Organization**: Help entries grouped by topic (skills, spells,
  races, classes, combat, communication, movement, building, etc.), each loaded
  from separate help files.
- **Dynamic Editing**: In-game help editing for administrators without requiring
  file access or server restarts.

**Depends on:** Utilities, Persistence (file loading)
**Depended on by:** Player-facing systems (contextual help)

---

## Player Interaction

### 18. Social & Communication

All player-to-player and player-to-world communication systems.

**Features:**
- **Chat Channels**: Themed broadcast channels — gossip, auction, music, Q&A,
  grats, flame, immtalk, wiznet, clantalk, grouptalk. Each channel has toggle
  controls, color coding, and history recall.
- **Direct Messaging**: Tell (targeted private message), reply (to last sender),
  say (room-local speech), whisper, and yell (area-wide).
- **Social/Emote Commands**: ~200 predefined social actions (bow, grin, slap,
  hug, etc.) with contextual messages for: no target, self-target, character
  target (seen by actor, target, and room). Socials can be used in channels.
- **Social Editing**: Online editing of social definitions — adding, modifying,
  and removing social commands without restarts.
- **Ignore System**: Per-player block lists preventing communication from
  specific characters. Persisted in the database. Applies to tells, channels,
  and other direct messaging.
- **Music/Jukebox**: Song playback system with music files, jukebox objects, and
  the play command. Songs update on tick with lyric broadcast to the room.
- **Marriage**: Character relationship system — proposal, acceptance, wedding
  ceremony, partner status tracking, divorce. Confers special partner commands
  and social status.
- **Pose**: Custom title/description that appears in room descriptions and who
  lists.

**Depends on:** Character Data Model, Networking, Command Interpreter
**Depended on by:** Quest System (announcements), Admin Commands (wiznet)

---

### 19. Economy

Player-to-player and player-to-NPC economic transactions.

**Features:**
- **Auction System**: Global item auction with bidding, timed countdowns (going
  once, going twice, sold), minimum bid increments, and cancellation. Auction
  state broadcasts to the auction channel. Item validation prevents auctioning
  of no-drop or personal items.
- **Banking**: Deposit, withdraw, and balance commands for gold storage across
  sessions. Clan banking for organizational funds.
- **Currency**: Gold and silver currency with exchange rates. Money-related
  commands for dropping, getting, and splitting loot.

**Depends on:** Object System, Character Data Model, Social & Communication (auction channel)
**Depended on by:** Quest System (rewards)

---

### 20. Quests

Automated and structured objectives for player engagement.

**Features:**
- **Automated Quest Generation**: Dynamic mission creation with varied objectives
  — kill target mobs, retrieve items, explore locations. Difficulty scaling based
  on player level.
- **Quest Tracking**: Active quest state with target identification, progress
  monitoring, and time limits. Quest info command shows current objectives.
- **Quest Rewards**: Quest points (QP) as alternative currency, gold, experience,
  and practice session rewards. Quest point shop for purchasing special items.
- **Quest Areas**: Designated areas with quest-specific properties and starting
  rooms for structured quest content.
- **Timed Challenges**: Countdown timers creating urgency. Failed quests have
  cooldown periods before new quests can be requested.

**Depends on:** Character Data Model, World System, Object System, Combat System
**Depended on by:** Character Progression (QP as currency)

---

### 21. Organizations & PvP

Clan management, inter-clan warfare, and structured player-versus-player combat.

**Features:**
- **Clan System**: Player organizations with leadership hierarchy, membership
  management, rank assignments, and clan-specific chat channels. Clan data
  persisted in the database with member counts and standings.
- **Clan Editing**: Administrative interface for creating, modifying, and
  disbanding clans. Member management, rank configuration, and clan property
  settings.
- **War System**: Formal inter-clan warfare with war declarations, kill tracking,
  scoring, and victory conditions. War event history with persistent records.
  Multiple war types and rules.
- **Duel System**: Structured one-on-one PvP combat with challenge/accept
  protocol, arena teleportation, special duel rules (no looting, safe death),
  wagering, and spectator support. Automatic timeout and scoring.
- **PvP Safeguards**: Safe rooms, level range restrictions, and consent
  requirements preventing unwanted PvP. Separate rules for open-PK vs.
  duel-only combat.

**Depends on:** Character Data Model, Combat System, Social & Communication
**Depended on by:** Character Data Model (clan membership)

---

## Operations

### 22. Persistence

All save/load operations for game data across server sessions.

**Features:**
- **Player Save/Load**: Complete character serialization — stats, equipment,
  inventory, affects, skills, quest state, preferences, aliases, and pet data.
  Written to individual player files in a structured text format. Auto-save on
  tick rotation.
- **SQLite Database**: Relational storage for cross-character data — ignore
  lists, disabled commands, ban lists, clan data, and player index lookups.
  Query builder with prepared statements and error handling.
- **Area File I/O**: Low-level file reading primitives (fread_string,
  fread_number, fread_flag, fread_word) used to parse the custom area file
  format at boot time.
- **Object State Serialization**: JSON-based persistence of ground-state objects
  across copyovers. Filters to only save meaningful items (no consumables, no
  timed objects, no NPC corpses).
- **Storage System**: Off-character persistent item storage. Load/save routines
  for storage locker contents.
- **Configuration Loading**: JSON config file parsing for server settings at
  boot time.
- **Note File I/O**: Load and save of note board contents in flat-file format.

**Depends on:** Utilities, Character Data Model, Object System
**Depended on by:** Networking (save on disconnect), Game Engine (auto-save tick)

---

### 23. Admin & Builder Commands

Privileged commands for server management, player moderation, content creation,
and debugging.

**Features:**
- **Player Moderation**: Freeze, noemote, noshout, nochannel, deny, ban, permit,
  revoke commands for managing player behavior. Punishment tracking and logging.
- **Entity Inspection**: Stat command showing detailed internal state of any
  character, object, or room. Flag inspection and searching tools.
- **Entity Modification**: Set command for modifying any property on characters
  (HP, stats, level, gold, skills, etc.), objects (values, flags, weight), and
  rooms (flags, descriptions). Flag command for bulk flag operations.
- **World Manipulation**: Transfer, goto, at (execute at location), restore
  (full heal), slay (instant kill), purge (remove NPCs/objects from room).
- **Content Creation**: Oload (spawn objects), mload (spawn NPCs), and addapply
  (add enchantments) for building game content. Exit auditing tools for
  validating area connections.
- **Server Control**: Reboot, shutdown, copyover (hot restart), wizlock (block
  new connections), autoboot (timed restart).
- **Security**: Ban system (site-based and character-based), permit exceptions,
  log monitoring with the tail command, trust delegation.
- **Debugging**: Memory usage display, entity counts, loot generation testing,
  weather inspection, image rendering, and various diagnostic subcommands.
- **Wiznet**: Staff notification channel for system events — logins, deaths,
  bugs, security violations, and administrative actions.

**Depends on:** Everything (admin commands touch all systems)
**Depended on by:** None (terminal consumer)

---

## Dependency Overview

```
┌─────────────────────────────────────────────────────┐
│                  Core Infrastructure                 │
│  Utilities ← Memory&GC ← Event Dispatcher           │
│       ↑           ↑            ↑                     │
│   Game Engine ← Networking ← Command Interpreter     │
│       ↑                                              │
│   Data Tables                                        │
└──────┬──────────────────────────────────────────────┘
       │
┌──────▼──────────────────────────────────────────────┐
│                  Entity Systems                      │
│  Character Data Model ←→ Object System               │
│       ↑                       ↑                      │
│  Character Progression    Affect System              │
│       ↑                       ↑                      │
│  World System (areas, rooms, exits, weather, map)    │
└──────┬──────────────────────────────────────────────┘
       │
┌──────▼──────────────────────────────────────────────┐
│                  Game Mechanics                       │
│  Combat System ←→ Magic System                       │
│       ↑               ↑                              │
│  MobProg System (NPC scripting & behavior)           │
└──────┬──────────────────────────────────────────────┘
       │
┌──────▼──────────────────────────────────────────────┐
│                Player Interaction                     │
│  Social & Communication    Economy    Quests          │
│  Organizations & PvP       Help System               │
│  Notes & Editor                                      │
└──────┬──────────────────────────────────────────────┘
       │
┌──────▼──────────────────────────────────────────────┐
│                   Operations                         │
│  Persistence          Admin & Builder Commands       │
└─────────────────────────────────────────────────────┘
```
