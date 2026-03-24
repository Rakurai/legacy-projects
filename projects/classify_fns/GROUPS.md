# Capability Group Audit

Audit of all 30 capability groups against their locked function lists.
Functions flagged below have documentation that suggests a different group.

---

## Utility

### imaging (utility)
Bitmap image creation and I/O: loading and writing PNG files, querying image dimensions and per-pixel color channel values, used for worldmap tile rendering.

No suspects.

### numerics (utility)
Numeric utilities: pseudo-random number generation (flat range, percentage, door index, fuzzy, bit-width), dice rolling, pseudo-random distribution with failure memory, linear interpolation between level-indexed values, value clamping, power-of-two rounding, time-value scanning.

No suspects.

### arg_parsing (utility)
Command-line argument tokenisation: splitting player input into tokens with quote-delimited and dot-notation handling, extracting numbered targets and quantity prefixes, type-tagged argument parsing, keyword matching and word-list checks, character name validation.

| Function | Brief | Suggested group |
|----------|-------|-----------------|
| `help_char_search` | SQL search + formatted display of help entries | → NEW: help_system — DB query + pagination, not tokenisation |
| `swearcheck` | Checks input for predefined offensive words | → social — content censorship filter, not argument parsing |

### memory (utility)
Memory lifecycle management: pooled object allocation and deallocation tracking, garbage-collection marking and deferred deletion, allocation counters, buffer capacity management, cJSON structure creation and teardown, affect cache infrastructure.

| `cJSON_*` | json parsing | -> persistence |

### text_editing (utility)
In-game line editor: editing session initialisation (descriptions, notes, help entries), line navigation and cursor positioning, line insertion, deletion, and splitting, text replacement within lines, word wrapping, undo, cancel, context-window display, line counting, range validation, blank-line detection, edit status display, buffer backup.

No suspects.

### flags (utility)
Bit-flag utility operations: testing, setting, and clearing individual bits, testing any/all/none-of predicates, flag-to-string conversion and name resolution for all flag domains, flag index lookup by name, flag retrieval from database columns and JSON, object-value flag access, character cgroup flag addition and removal, flag emptiness checks.

<-- need to look at this, usages of flags belong with the domain, not the utility group.  object and character flag accessors in here currently? -->

### string_ops (utility)
String manipulation utilities: case conversion, trimming and stripping, substring extraction and search, prefix/infix/suffix matching, string comparison, string replacement, concatenation, insertion, and erasure, centering and number-to-string conversion, ordinal formatting, time formatting, drunk-speech transformation, hex parsing, color code removal, string duplication, length computation.

| Function | Brief | Suggested group |
|----------|-------|-----------------|
| `next_line` | Returns pointer to start of next line in text buffer | → text_editing — references `ed` editing session global; core line-navigation primitive for the editor |
| `cJSON_strdup` | Creates a duplicate of input string with cJSON_malloc | → persistence — uses cJSON custom allocator; all other `cJSON_*` lifecycle functions go to persistence |
| `make_drunk` | drunk-speech transformation | → social - this is a speech effect used in do_say |

---

## Infrastructure

### runtime (infrastructure)
Core game loop and connection lifecycle: command interpreter dispatch, main tick loop (character updates, object decay, area refresh), network connection teardown, game-time and weather tick advancement, world entity list management.

<-- need to look at this, the actual code for character updates, object decay, etc probably doesn't belong here, but the loop driving those updates does belong here -->

### admin (infrastructure)
Administrative and immortal utilities: bug and diagnostic logging (formatted and timestamped), broadcasting notifications to immortals, immortal notification configuration, character restoration to full health/mana/stamina, login/logout message management, immortal staff rank derivation and comparison, immortal-specific configuration, command disable checking.

<-- look into this, some of these sound like game interactions.  "admin" is a suspicious capability grouping.  all "wiznet" functionality could probably be its own group -->

### persistence (infrastructure)
Data serialisation, storage, and retrieval: character save/load to JSON files, pet serialisation, object state persistence, area-file reading, cJSON structure creation/printing/value extraction, SQL database queries/commands/error handling/row iteration, war table and event logging, social table persistence, note file writing, storage locker and departed-player list management, player-index updates, file append utilities, help entry insertion.

| Function | Brief | Suggested group |
|----------|-------|-----------------|
| `is_worth_saving` | Checks whether an object is suitable for saving based on type and state | → state_rules — evaluates object properties (item type, level, timer, reset config), not serialization |
| `lookup_storage_data` | Searches for a StoredPlayer by name in linked list | → entity_lookup — classic name-based entity resolution pattern |

---

## Policy

### visibility_rules (policy)
Visibility and perception checks: determining whether one character can see another (including in room, in WHO list), object visibility, room visibility, darkness and very-dark room detection, blindness checks, room privacy, location and coordinate validity, light-level effects on perception.

| Function | Brief | Suggested group |
|----------|-------|-----------------|
| `can_see_room` | Checks room access based on rank, remort, gender, clan restrictions | → state_rules — permission guard (rank/clan/gender gating), not perception/lighting |
| `Room::is_private` | Checks room privacy by ownership, flags, and occupancy | → world_structure — room-state predicate about access control, not visual perception |

<-- location and coordinate validity probably doesn't belong here -->

### entity_lookup (policy)
In-game entity resolution: finding characters, NPCs, objects, and players by name within various scopes (room, area, world, inventory, equipment, shopkeeper stock), numbered-target resolution, extra description lookup, flag-based search, location resolution from names, key possession checks, name expansion, object prototype retrieval, warp-crystal search, help entry lookup, race lookup, random prototype selection.

| Function | Brief | Suggested group |
|----------|-------|-----------------|
| `quest_where` | Provides last known location details of quest items/mobs to a character | → quests — reads `ch->pcdata->questloc`, sends quest-hint message; not general entity resolution |

### attributes (policy)
Character stat access and derived computation: armor class calculation, hitroll and damroll computation, maximum HP/mana/stamina derivation, per-stat accessors and modifiers, age computation, carrying weight and count capacity, regeneration rates, defense modifier display, stat-to-attribute mapping, level-based saving throws, stamina deduction, title and play-time tracking, sex and rank accessors, object stat flag checks.

| Function | Brief | Suggested group |
|----------|-------|-----------------|
| `print_defense_modifiers` | Generates a formatted string of defense modifiers for a category | → display — builds a display-ready string, not a stat computation |

### state_rules (policy)
Character state predicates and permission guards: NPC-vs-player checks, immortal and hero tier tests, position checks, level and trust enforcement, combat safety checks, duel and arena participation state, killer and thief flag checks, clan and war opponent status, equipment permission, condition monitoring, alignment and class predicates, remort tier checks, follower attachment/detachment, command group membership, wait and daze state assignment, group membership checks, character-type matching.

| Function | Brief | Suggested group |
|----------|-------|-----------------|
| `align` | Attempts to change a character's alignment using stamina and skill | → skills_progression — full skill execution (deducts stamina, rolls skill, calls check_improve) |
| `check_pulse` | Checks and updates HP-based position: death, incap, stun, recovery | → combat — HP→death state machine, corpse location messaging, Die Hard recovery |
| `check_all_cond` | Checks and damages/destroys all worn equipment based on conditions | → objects — equipment durability/degradation management |
| `CAN_WEAR` | Checks if an object has a specific wear flag set | → flags — object wear_flags bitfield check |

---

## Projection

### display (projection)
Information rendering and display assembly: room description and contents display, character appearance in room, object description formatting, exit listing, score and stat sheet rendering, detailed inspection formatting, minimap generation, affect and evolution display, war event and roster lists, weather descriptions, location and coordinate string rendering, player count for WHO list, condition description lookup.

| Function | Brief | Suggested group |
|----------|-------|-----------------|
| `Room::description` | Retrieves descriptive text from room prototype | → world_structure — pure const getter on room data, zero rendering |
| `Room::extra_descr` | Retrieves extra description pointer from room prototype | → world_structure — pure data accessor, no formatting |
| `RoomID::to_string` | Converts RoomID to formatted string showing validity and vnums | → string_ops — ID-to-string conversion, no display context or character awareness |

### output (projection)
Message transport to player connections: dispatching formatted messages to rooms and targets, sending text to character output buffers, descriptor output buffering and flushing, pager display, color code expansion and ANSI handling, custom color configuration, prompt generation, terminal control, text formatting and paragraph wrapping, damage and combat message rendering, video configuration, duel and auction broadcast dispatch.

| Function | Brief | Suggested group |
|----------|-------|-----------------|
| `send_to_query` | Sends message to all characters in sender's query list | → social — social channel dispatch; output avoid list excludes "social channel" |
| `channel_who` | Displays players with a specific communication channel enabled | → social — channel membership listing; output avoid list excludes "social channel" |
| `Format::printf` | Formats and writes a string to stdout | → string_ops — generic printf wrapper to stdout, not player connections |
| `Format::sprintf` | Formats a string into a buffer via std::sprintf | → string_ops — thin sprintf wrapper, no connection to descriptors or output buffers |
| `Format::format` | Returns a formatted String from printf-style args | → string_ops — general-purpose string construction utility |
| `listline` | Formats a line with number/markers for editor listing | → text_editing — references `ed->edit_line` and `ed->edit_nlines`; part of editor display |

---

## Domain

### pvp (domain)
Duel and arena mechanics: duel initiation, tracking, and kill resolution, arena setup and clearing, duel list management, arena selection.

No suspects.

### magic (domain)
Spell casting mechanics: object-triggered spell dispatch (scrolls, wands, staves, potions), saving throws against spells, spell dispelling from characters, chain-spell execution across multiple targets, spell comparison for sorting, incantation text generation.

| Function | Brief | Suggested group |
|----------|-------|-----------------|
| `dispel_char` | Attempts to dispel/cancel effects on a character by level and operation type | → affects — iterates dispel table removing active effects; affect lifecycle management, not spell casting |

### economy (domain)
Economy and currency system: gold and silver handling, currency deduction and weight computation, money object creation, shop pricing, shopkeeper location, quest-shop identification, auction participation checks, currency lookup.

No suspects.

### social (domain)
Synchronous communication and social interaction: chat channel messaging and channel membership queries, tells and reply, say and emote, social action execution and lookup, social table management, clan channel message dispatch, offline-player ignore management, communication censorship configuration.

No suspects.

### notes (domain)
Asynchronous note and board system: composing, addressing, and attaching notes to characters, appending notes to board lists, writing note files to disk, delivery notification, recipient checking, note removal, spool counting, note visibility filtering, last-read timestamp tracking.

| Function | Brief | Suggested group |
|----------|-------|-----------------|
| `save_notes` | Saves all notes of a category to designated file | → persistence — pure disk serialization (open file, iterate list, fprintf, close) |

### quests (domain)
Quest system: random quest generation and target assignment, skill-quest creation, quest completion and cleanup, quest-point checks, quest information display, questmaster location, quest level-range evaluation, quest-object delivery processing.

| Function | Brief | Suggested group |
|----------|-------|-----------------|
| `find_questmaster` | Finds questmaster NPC in same room as character | → entity_lookup — classic room-occupant scan by spec_fun filter |
| `find_squestmaster` | Finds skill-quest master NPC in same room as character | → entity_lookup — identical pattern to `find_questmaster` |

### npc_behavior (domain)
NPC behavioural logic: MobProg program execution (driver, command processing, conditional evaluation, variable translation, keyword matching, percentage checks, string evaluation, line extraction), mob program triggers, special-function dispatch, NPC hunting AI, mob animation and summoning.

| Function | Brief | Suggested group |
|----------|-------|-----------------|
| `create_mobile` | Creates and initialises a new mobile character from a prototype | → world_structure — general-purpose entity factory; world_structure already has mobile prototype retrieval |
| `animate_mob` | Creates and summons a creature as pet/servant for a character | → magic — implements summoning spell effects (charm affect, pet setup, room restriction checks) |

### combat (domain)
Combat round execution: single and multi-attack resolution, damage calculation, defense checks, hit/miss adjudication, fighting state transitions, death handling, experience distribution, NPC attack behaviour, position updates, special attacks, war score adjustment, duel preparation, attack and weapon type lookups, wielded weapon skill resolution.

| Function | Brief | Suggested group |
|----------|-------|-----------------|
| `war_score_adjust` | Adjusts clan war score and handles defeat conditions | → clans — clan-war state management; `defeat_clan`, `war_kill`, `war_power_adjust` are all in clans |
| `prepare_char` | Prepares character for duel by relocating, clearing effects, resetting stats | → pvp — duel arena setup and preparation |

### clans (domain)
Clan organisation system: membership checks, clan power and score computation, inter-clan war initiation/joining/resolution, war kill scoring, war victory handling, war capacity checks, war data compaction, war event recording, war power adjustments, defeat handling, clan roster counting, clan lookup, war lookup, clan list management, clan table persistence.

| Function | Brief | Suggested group |
|----------|-------|-----------------|
| `save_clan_table` | Saves all clans to database via SQL INSERT/UPDATE | → persistence — pure ORM-style database serialization |
| `count_clan_members` | Counts clan members via SQL query with optional role filter | → persistence — constructs and executes SQL query, returns count |

### skills_progression (domain)
Skill and level progression: skill lookup by name and index, proficiency queries and updates, weapon skill levels, evolution tracking and eligibility, experience gain and level advancement/demotion, experience-per-level calculation, NPC level advancement, skill cost computation, practice and training session display, skill group completion checks, group and guild lookup, spell lookup for casting, holdable and usable level computation, random skill selection, class pose selection, remort skill list display.

| Function | Brief | Suggested group |
|----------|-------|-----------------|
| `evolve_list` | Displays formatted list of evolvable skills with costs and levels | → display — builds multi-column output, calls page_to_char; pure rendering |
| `list_extraskill` | Displays formatted list of remort skills with affordability indicators | → display — builds formatted output and paginates; pure rendering |

### movement (domain)
Character and object movement between rooms: entering and leaving rooms, door and exit resolution, room access via exits, pathfinding, flee from combat, sector-based movement costs, portal and recall traversal, warp crystal destination reading, random and scatter room selection, character extraction from game world, pet removal, room-level character addition/removal, exit inspection, object placement in rooms, duel and arena room checks, pet creation and follow establishment, tailing, flying and outdoor checks.

| Function | Brief | Suggested group |
|----------|-------|-----------------|
| `Area::remove_char` | Removes character from area, updates player/immortal counts | → world_structure — symmetric to `Area::add_char` already in world_structure |
| `Exit::rev_dir` | Calculates reverse direction index | → world_structure — "reverse direction" explicitly in world_structure desc |
| `Exit::keyword` | Retrieves keyword associated with an Exit object | → world_structure — "keywords" explicitly in world_structure desc |
| `get_position` | Determines character position with combat special-casing | → state_rules — state/position accessor, not room-to-room movement |
| `scan_list` | Iterates room characters, displays those visible to scanner | → visibility_rules — perception/visibility checks + display |
| `checkexits` | Lists one-way connections crossing an area boundary | → world_structure — exit topology analysis, admin inspection tool |
| `checkexitstoroom` | Lists one-way exits from one room to another | → world_structure — exit topology analysis |
| `room_pair` | Formats string showing connection between two rooms | → display — pure formatting helper for room connectivity |
| `World::remove_char` | Removes character from world's active list, marks for GC | → memory — world-list detachment and GC lifecycle |

### world_structure (domain)
World structure and spatial data: area metadata and retrieval, area player and immortal counting, room properties (sector type, healing/mana rate, guild, ownership, name), exit topology (direction names, reverse direction, keywords, keys), room and location identity encoding, worldmap coordinate system and quadtree-based spatial lookups, calendar and time-of-day data, sector type lookup, vnum identity, mobile prototype retrieval, mobile creation and cloning, skill-quest room selection.

No suspects.

### objects (domain)
Object lifecycle and manipulation: creating objects from prototypes, cloning, extracting and destroying objects, transferring objects between characters/rooms/containers/lockers/strongboxes, equipping and removing worn items, equipment generation and base stat assignment, loot name generation, gem inset, object repair, forging weapon flags, loot eligibility checks, container capacity checks, content spilling on destruction, object weight computation, object user counting, item type and liquid type lookups, anvil ownership, clan equipment disposal.

| Function | Brief | Suggested group |
|----------|-------|-----------------|
| `obj_to_keeper` | Adds object to shopkeeper inventory with duplicate/cost handling | → economy — shop-specific stock management (duplicate detection, ITEM_INVENTORY, cost updates) |
| `has_modified_contents` | Checks if object contents deviate from reset configuration | → persistence — reset/save-state consistency verification |

### affects (domain)
Affect lifecycle management: applying, joining, and copying affects to characters, objects, and rooms; removing affects by type, pattern, mark, or permanence; querying affect existence and finding specific instances; affect list iteration, sorting, deduplication, and checksum computation; attribute modification from affects; affect cache lookup and display; elemental effect propagation; dispel checks; spell fading and undoing; remort-affect rolling, application, removal, and lookup; blank remort affect repair; gem effect compilation; blade enhancement; plague spreading; protection aura checks; room-level affect ticking; affect flag parsing, type lookup, and bit-to-type conversion; affect comparators for sorting.

No suspects.

---

## Split / Merge Candidates

**movement → split consideration**: 9 of 34 locked functions flagged. The group conflates three distinct concerns: (a) actual room-to-room character movement, (b) exit/room data accessors that belong in world_structure, and (c) miscellaneous functions (visibility scanning, position queries, GC). After removing the flagged functions, the remaining 25 form a tight "character traversal" group.

**output → split consideration**: The group mixes three layers: (a) low-level transport (`write_to_buffer`, `process_output`, `stc`, `cwtb`), (b) general-purpose string formatting (`Format::printf/sprintf/format`) that is used everywhere, and (c) domain-specific dispatch (`send_to_query`, `channel_who`, `listline`). The Format:: functions are especially problematic — they have no connection to player output and are used across the entire codebase.

**persistence + domain save functions → merge or convention**: Several domain groups contain save/serialization functions (`save_notes` in notes, `save_clan_table` and `count_clan_members` in clans). These are pure I/O routines with no domain logic. Either they all belong in persistence, or the convention should be explicit that domain groups own their own serialization.

**world_structure + movement exit accessors**: The movement group contains 5 functions (`Exit::rev_dir`, `Exit::keyword`, `checkexits`, `checkexitstoroom`, `Area::remove_char`) that match the world_structure description more precisely than the movement description. Moving them would make both groups more cohesive.

**entity_lookup is a magnet**: Multiple domain groups contain functions that are structurally entity-lookup operations with a domain-specific filter predicate (`find_questmaster`, `find_squestmaster`, `find_keeper`, `lookup_storage_data`). The pattern is always "iterate list, match by name/type, return pointer." Convention should decide whether these live with their domain or with entity_lookup.
