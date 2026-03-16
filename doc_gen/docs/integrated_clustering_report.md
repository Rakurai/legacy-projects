# Integrated Clustering Report

# Integrated Clustering Report

## Overview

Total clusters: 26

Total entities: 4549


## Integration Weights

- structural: 0.50

- semantic: 0.30

- usage: 0.20


## Agreement Between Clustering Approaches

- structural_semantic: 0.3048


## Cluster Analysis

### Cluster 0

**Size**: 598 nodes

**Representative nodes**:

- `const char * strchr(const String &str, int ch)` (member)
- `day_names` (member)
- `DECLARE_DO_FUN` (member)
- `int deity_lookup(const String &name)` (member)
- `int strcmp(const String &astr, const String &bstr)` (member)
- `int Format::sprintf(String &str, const String &fmt, Params &&... params)` (member)
- `const char * strstr(const String &astr, const String &bstr)` (member)
- `void do_sacrifice(Character *ch, String argument)` (member)
- `void do_gossip(Character *ch, String argument)` (member)
- `const String get_custom_color_name(Character *ch, int slot)` (member)
- *...and 588 more*


### Cluster 1

**Size**: 518 nodes

**Representative nodes**:

- `void do_rotate(Character *ch, String argument)` (member)
- `bool spec_squestmaster(Character *ch)` (member)
- `void check_protection_aura(Character *ch, Character *victim)` (member)
- `void say_spell(Character *ch, skill::type sn)` (member)
- `minimum_position` (member)
- `level` (member)
- `void spell_gas_breath(skill::type sn, int level, Character *ch, void *vo, int target, int evolution)` (member)
- `void spell_cure_light(skill::type sn, int level, Character *ch, void *vo, int target, int evolution)` (member)
- `void spell_barrier(skill::type sn, int level, Character *ch, void *vo, int target, int evolution)` (member)
- `bool spec_breath_any(Character *ch)` (member)
- *...and 508 more*


### Cluster 2

**Size**: 163 nodes

**Representative nodes**:

- `void spell_enchant_armor(skill::type sn, int level, Character *ch, void *vo, int target, int evolution)` (member)
- `vnum` (member)
- `Object * create_object(ObjectPrototype *pObjIndex, int level)` (member)
- `Object * generate_skillquest_obj(Character *ch, int level)` (member)
- `extra_flags` (member)
- `void spell_identify(skill::type sn, int level, Character *ch, void *vo, int target, int evolution)` (member)
- `Note::Note()` (member)
- `_as_flags` (member)
- `int count_items(const Object *obj)` (member)
- `worldmap::Quadtree< T >::Quadtree(unsigned int capacity)` (member)
- *...and 153 more*


### Cluster 3

**Size**: 92 nodes

**Representative nodes**:

- `Dispatcher & event::Dispatcher::operator=(const Dispatcher &)` (member)
- `Type` (member)
- `worldmap::Region::Region(const Region &)` (member)
- `Clan & Clan::operator=(const Clan &)` (member)
- `Tail::Tail()` (member)
- `Location & Location::operator=(const Location &l)` (member)
- `event::Handler::Handler()` (member)
- `Flags & Flags::operator=(const Flags &f)` (member)
- `Reset & Reset::operator=(const Reset &)` (member)
- `worldmap::Worldmap::Worldmap(const Worldmap &)` (member)
- *...and 82 more*


### Cluster 4

**Size**: 200 nodes

**Representative nodes**:

- `vnum` (member)
- `suffixes_allowed` (member)
- `vnum` (member)
- `Msyl2` (member)
- `const String get_legendary_name(int eq_type)` (member)
- `Fsyl2` (member)
- `vnum` (member)
- `MagT_table` (member)
- `legendary_base_pool_table` (member)
- `silver_weight` (member)
- *...and 190 more*


### Cluster 5

**Size**: 275 nodes

**Representative nodes**:

- `void do_steal(Character *ch, String argument)` (member)
- `void obj_from_locker(Object *obj)` (member)
- `open_hour` (member)
- `void do_buy(Character *ch, String argument)` (member)
- `int weapon_lookup(const String &name)` (member)
- `affect_checksum` (member)
- `object_list` (member)
- `name` (member)
- `void do_get(Character *ch, String argument)` (member)
- `int objstate_load_items()` (member)
- *...and 265 more*


### Cluster 6

**Size**: 103 nodes

**Representative nodes**:

- `next` (member)
- `void affect::join_to_char(Character *ch, Affect *paf)` (member)
- `void affect::iterate_over_obj(Object *obj, affect_fn fn, void *data)` (member)
- `void affect::clear_list(Affect **list_head)` (member)
- `int set_tail(Character *ch, Character *victim, Flags tail_flags)` (member)
- `void affect::modify_room(Room *room, const Affect *paf, bool fAdd)` (member)
- `void affect::iterate_over_room(Room *room, affect_fn fn, void *data)` (member)
- `void affect::modify_char(void *owner, const Affect *paf, bool fAdd)` (member)
- `bool affect::parse_flags(char letter, Affect *paf, Flags &bitvector)` (member)
- `void affect::remove_type_from_obj(Object *obj, ::affect::type type)` (member)
- *...and 93 more*


### Cluster 7

**Size**: 83 nodes

**Representative nodes**:

- `dispel_table` (member)
- `affect_table` (member)
- `weapon_affects` (member)
- `RAFF_RES_BLUNT` (member)
- `APPLY_FORGE_UNIQUE` (member)
- `RAFF_RES_DROWNING` (member)
- `APPLY_CHR` (member)
- `RAFF_RES_NEGATIVE` (member)
- `RAFF_MAGEREGEN` (member)
- `RAFF_LAUGHTERGOD` (member)
- *...and 73 more*


### Cluster 8

**Size**: 108 nodes

**Representative nodes**:

- `weapon_eq_rolls` (member)
- `eq_meta_table` (member)
- `eq_rolls` (member)
- `accessory_eq_rolls` (member)
- `armor_eq_rolls` (member)
- `ARMOR_HOLD` (member)
- `OBJ_VNUM_LEGS` (member)
- `WIELD_EXOTIC` (member)
- `OBJ_VNUM_WIELD_BOW` (member)
- `OBJ_VNUM_FEET` (member)
- *...and 98 more*


### Cluster 9

**Size**: 498 nodes

**Representative nodes**:

- `wiznet_table` (member)
- `void mprog_tick_trigger(Character *mob)` (member)
- `void mprog_act_trigger(const char *buf, Character *mob, Character *ch, Object *obj, void *vo)` (member)
- `void mprog_random_trigger(Character *mob)` (member)
- `const String MobProg::type_to_name(Flags::Bit)` (member)
- `_num_players` (member)
- `void death_cry(Character *ch)` (member)
- `MobProg::MobProg(FILE *fp)` (member)
- `extra_flags` (member)
- `void do_channels(Character *ch, String argument)` (member)
- *...and 488 more*


### Cluster 10

**Size**: 301 nodes

**Representative nodes**:

- `remort_guild` (member)
- `sex_table` (member)
- `FLAGS_NBITS` (member)
- `GET_ATTR_AGE` (member)
- `void kill_off(Character *ch, Character *victim)` (member)
- `void roll_raffects(Character *ch, Character *victim)` (member)
- `const String print_bit_names(const std::vector< flag_type > &flag_table, const Flags &flags)` (member)
- `void prac_by_group(Character *ch, const String &argument)` (member)
- `cJSON * fwrite_player(Character *ch)` (member)
- `const String cgroup_bit_name(const Flags &flags)` (member)
- *...and 291 more*


### Cluster 11

**Size**: 78 nodes

**Representative nodes**:

- `void spell_poison(skill::type sn, int level, Character *ch, void *vo, int target, int evolution)` (member)
- `bool HAS_RAFF(Character *ch, int flag)` (member)
- `void affect::remove_matching_from_char(Character *ch, comparator comp, const Affect *pattern)` (member)
- `void spell_holy_word(skill::type sn, int level, Character *ch, void *vo, int target, int evolution)` (member)
- `size` (member)
- `bool is_blinded(const Character *ch)` (member)
- `void spell_invis(skill::type sn, int level, Character *ch, void *vo, int target, int evolution)` (member)
- `void spell_bless(skill::type sn, int level, Character *ch, void *vo, int target, int evolution)` (member)
- `const String roll_mod(Object *obj, int eq_type, const std::multimap< int, affect::type > &mods_allowed)` (member)
- `void affect::free_cache(Character *ch)` (member)
- *...and 68 more*


### Cluster 12

**Size**: 89 nodes

**Representative nodes**:

- `void load_storage_list()` (member)
- `departed_list_line` (member)
- `storage_list_head` (member)
- `void insert_departed(const String &name)` (member)
- `char_no_arg` (member)
- `top_reset` (member)
- `void do_departedlist(Character *ch, String argument)` (member)
- `void save_line(FILE *fp, StoredPlayer *sd)` (member)
- `void save_storage_list()` (member)
- `others_auto` (member)
- *...and 79 more*


### Cluster 13

**Size**: 334 nodes

**Representative nodes**:

- `area` (member)
- `questloc` (member)
- `defprep` (member)
- `void do_open(Character *ch, String argument)` (member)
- `Exit & Exit::operator=(const Exit &)` (member)
- `void QuestArea::init()` (member)
- `void do_east(Character *ch, String argument)` (member)
- `bool Room::is_dark() const` (member)
- `area` (member)
- `room_flags` (member)
- *...and 324 more*


### Cluster 14

**Size**: 123 nodes

**Representative nodes**:

- `bool String::has_exact_words(const String &wordlist) const` (member)
- `static bool check_line(Character *ch, int line)` (member)
- `static char * next_line(char *current_line)` (member)
- `last_roleplay` (member)
- `Edit & Edit::operator=(const Edit &)` (member)
- `void update_read(Character *ch, Note *pnote)` (member)
- `static void edit_split(Character *ch, String argument)` (member)
- `char * strcat(char *dest, const String &src)` (member)
- `note_list` (member)
- `next` (member)
- *...and 113 more*


### Cluster 15

**Size**: 45 nodes

**Representative nodes**:

- `virtual Exit::~Exit()` (member)
- `virtual Weather::~Weather()` (member)
- `virtual GarbageCollectingList< T >::~GarbageCollectingList()` (member)
- `virtual ExitPrototype::~ExitPrototype()` (member)
- `virtual Vnum::~Vnum()` (member)
- `virtual War::Opponent::~Opponent()` (member)
- `virtual Duel::~Duel()` (member)
- `War::~War()` (member)
- `virtual ObjectValue::~ObjectValue()` (member)
- `virtual Auction::~Auction()` (member)
- *...and 35 more*


### Cluster 16

**Size**: 78 nodes

**Representative nodes**:

- `GarbageCollectingList< T >::GarbageCollectingList(const GarbageCollectingList &)` (member)
- `void update_handler()` (member)
- `World & World::operator=(const World &)` (member)
- `iterator & GarbageCollectingList< T >::iterator::operator++()` (member)
- `mmhg` (member)
- `Weather::Weather(const GameTime &t)` (member)
- `GameTime::GameTime(std::time_t system_time)` (member)
- `list` (member)
- `str_boot_time` (member)
- `World::World(const World &)` (member)
- *...and 68 more*


### Cluster 17

**Size**: 206 nodes

**Representative nodes**:

- `void update_pc_index(const Character *ch, bool remove)` (member)
- `help_greeting` (member)
- `area_maxvnum` (member)
- `disabled_first` (member)
- `String Format::format(const String &fmt, Params &&... params)` (member)
- `bool clan_in_war(Clan *clan, War *war, bool onlycurrent)` (member)
- `song_table` (member)
- `int Format::printf(const String &fmt, Params &&... params)` (member)
- `bool is_clan(Character *ch)` (member)
- `void load_war_events()` (member)
- *...and 196 more*


### Cluster 18

**Size**: 16 nodes

**Representative nodes**:

- `void do_mppurge(Character *ch, String argument)` (member)
- `Location::Location(int value)` (member)
- `void do_addexit(Character *ch, String argument)` (member)
- `void do_mpasound(Character *ch, String argument)` (member)
- `const String name_expand(Character *ch)` (member)
- `void do_peace(Character *ch, String argument)` (member)
- `void do_purge(Character *ch, String argument)` (member)
- `ROOM_VNUM_MORGUE` (member)
- `ROOM_VNUM_HONOR` (member)
- `ROOM_VNUM_DEMISE` (member)
- *...and 6 more*


### Cluster 19

**Size**: 71 nodes

**Representative nodes**:

- `red` (member)
- `green` (member)
- `color` (member)
- `void config_color(Character *ch, String argument)` (member)
- `_computed` (member)
- `const MapColor worldmap::Region::get_color(unsigned int x, unsigned int y) const` (member)
- `const String get_color_code(int color, int bold)` (member)
- `const String get_custom_color_code(Character *ch, int slot)` (member)
- `const String get_color_name(int color, int bold)` (member)
- `color_table` (member)
- *...and 61 more*


### Cluster 20

**Size**: 80 nodes

**Representative nodes**:

- `void show_string(Descriptor *d, bool clear_remainder)` (member)
- `chan_table` (member)
- `void do_send_announce(Character *ch, String argument)` (member)
- `bool worldmap::MapColor::operator==(const MapColor &rhs) const` (member)
- `void quest_usage(Character *ch)` (member)
- `color_sector_map` (member)
- `const String wrap_string(const String &s, unsigned long wrap_len)` (member)
- `void worldmap::MapColor::precompute()` (member)
- `csetting_table` (member)
- `void do_fyi(Character *ch, String argument)` (member)
- *...and 70 more*


### Cluster 21

**Size**: 172 nodes

**Representative nodes**:

- `mud_exp` (member)
- `group` (member)
- `mod_plr` (member)
- `rolepoints` (member)
- `dex_app` (member)
- `act` (member)
- `can_cancel` (member)
- `parts` (member)
- `max_prefixes` (member)
- `remort_level` (member)
- *...and 162 more*


### Cluster 22

**Size**: 145 nodes

**Representative nodes**:

- `_height` (member)
- `bool worldmap::Coordinate::is_valid() const` (member)
- `bool World::valid() const` (member)
- `worldmap::Coordinate::Coordinate(int nx, int ny)` (member)
- `int Location::to_int() const` (member)
- `room_prototypes` (member)
- `void Logging::bugf(const String &fmt, Params... params)` (member)
- `maptree` (member)
- `mob_prototypes` (member)
- `_height` (member)
- *...and 135 more*


### Cluster 23

**Size**: 1 nodes

**Representative nodes**:

- `EventTypes` (compound)


### Cluster 24

**Size**: 117 nodes

**Representative nodes**:

- `void cJSON_AddItemReferenceToObject(cJSON *object, const char *string, cJSON *item)` (member)
- `cJSON * cJSON_CreateTrue()` (member)
- `void cJSON_AddItemReferenceToArray(cJSON *array, cJSON *item)` (member)
- `void cJSON_AddItemToObject(cJSON *object, const char *string, cJSON *item)` (member)
- `cJSON_AddTrueToObject` (member)
- `global_ep` (member)
- `static const char * parse_number(cJSON *item, const char *num)` (member)
- `cJSON * cJSON_CreateNumber(double num)` (member)
- `cJSON * cJSON_CreateIntArray(const int *numbers, int count)` (member)
- `void cJSON_DeleteItemFromObject(cJSON *object, const char *string)` (member)
- *...and 107 more*


### Cluster 25

**Size**: 55 nodes

**Representative nodes**:

- `int fsearch_mobile(Character *ch, int fieldptr, const Flags &marked)` (member)
- `void do_flagsearch(Character *ch, String argument)` (member)
- `void do_flag(Character *ch, String argument)` (member)
- `bool Flags::has_all_of(const Flags &f) const` (member)
- `int fsearch_player(Character *ch, int fieldptr, const Flags &marked)` (member)
- `void fsearch_char(Character *ch, int fieldptr, const Flags &marked, bool mobile, bool player)` (member)
- `int flag_index_lookup(const String &name, const std::vector< flag_type > &flag_table)` (member)
- `FIELD_ROOM` (member)
- `CAND_OBJ` (member)
- `FIELD_COMM` (member)
- *...and 45 more*

