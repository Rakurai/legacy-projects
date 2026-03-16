# Structural Clustering Report

# Structural Clustering Report

## Overview

Total clusters: 26

Total entities: 4153

Algorithm: leiden

Modularity: N/A


## Cluster Analysis

### Cluster 0

**Size**: 733 nodes

**Representative nodes**:

- `void do_mppurge(Character *ch, String argument)` (member)
- `void show_string(Descriptor *d, bool clear_remainder)` (member)
- `const char * strchr(const String &str, int ch)` (member)
- `day_names` (member)
- `int deity_lookup(const String &name)` (member)
- `int strcmp(const String &astr, const String &bstr)` (member)
- `int Format::sprintf(String &str, const String &fmt, Params &&... params)` (member)
- `const char * strstr(const String &astr, const String &bstr)` (member)
- `void do_sacrifice(Character *ch, String argument)` (member)
- `void do_gossip(Character *ch, String argument)` (member)
- *...and 723 more*


### Cluster 1

**Size**: 526 nodes

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
- *...and 516 more*


### Cluster 2

**Size**: 506 nodes

**Representative nodes**:

- `mud_exp` (member)
- `remort_guild` (member)
- `sex_table` (member)
- `FLAGS_NBITS` (member)
- `rolepoints` (member)
- `GET_ATTR_AGE` (member)
- `void kill_off(Character *ch, Character *victim)` (member)
- `dex_app` (member)
- `act` (member)
- `void roll_raffects(Character *ch, Character *victim)` (member)
- *...and 496 more*


### Cluster 3

**Size**: 495 nodes

**Representative nodes**:

- `void do_rotate(Character *ch, String argument)` (member)
- `bool spec_squestmaster(Character *ch)` (member)
- `void check_protection_aura(Character *ch, Character *victim)` (member)
- `void say_spell(Character *ch, skill::type sn)` (member)
- `void spell_poison(skill::type sn, int level, Character *ch, void *vo, int target, int evolution)` (member)
- `level` (member)
- `bool HAS_RAFF(Character *ch, int flag)` (member)
- `void spell_gas_breath(skill::type sn, int level, Character *ch, void *vo, int target, int evolution)` (member)
- `void spell_cure_light(skill::type sn, int level, Character *ch, void *vo, int target, int evolution)` (member)
- `void spell_barrier(skill::type sn, int level, Character *ch, void *vo, int target, int evolution)` (member)
- *...and 485 more*


### Cluster 4

**Size**: 440 nodes

**Representative nodes**:

- `void spell_enchant_armor(skill::type sn, int level, Character *ch, void *vo, int target, int evolution)` (member)
- `void do_steal(Character *ch, String argument)` (member)
- `void obj_from_locker(Object *obj)` (member)
- `open_hour` (member)
- `void do_buy(Character *ch, String argument)` (member)
- `int weapon_lookup(const String &name)` (member)
- `vnum` (member)
- `Object * create_object(ObjectPrototype *pObjIndex, int level)` (member)
- `Object * generate_skillquest_obj(Character *ch, int level)` (member)
- `suffixes_allowed` (member)
- *...and 430 more*


### Cluster 5

**Size**: 345 nodes

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
- *...and 335 more*


### Cluster 6

**Size**: 224 nodes

**Representative nodes**:

- `void update_pc_index(const Character *ch, bool remove)` (member)
- `help_greeting` (member)
- `area_maxvnum` (member)
- `disabled_first` (member)
- `Clan & Clan::operator=(const Clan &)` (member)
- `String Format::format(const String &fmt, Params &&... params)` (member)
- `bool clan_in_war(Clan *clan, War *war, bool onlycurrent)` (member)
- `song_table` (member)
- `int Format::printf(const String &fmt, Params &&... params)` (member)
- `bool is_clan(Character *ch)` (member)
- *...and 214 more*


### Cluster 7

**Size**: 205 nodes

**Representative nodes**:

- `_height` (member)
- `bool worldmap::Coordinate::is_valid() const` (member)
- `red` (member)
- `worldmap::Region::Region(const Region &)` (member)
- `bool World::valid() const` (member)
- `worldmap::Coordinate::Coordinate(int nx, int ny)` (member)
- `int Location::to_int() const` (member)
- `room_prototypes` (member)
- `void Logging::bugf(const String &fmt, Params... params)` (member)
- `maptree` (member)
- *...and 195 more*


### Cluster 8

**Size**: 124 nodes

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
- *...and 114 more*


### Cluster 9

**Size**: 107 nodes

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
- *...and 97 more*


### Cluster 10

**Size**: 104 nodes

**Representative nodes**:

- `next` (member)
- `void affect::join_to_char(Character *ch, Affect *paf)` (member)
- `void affect::remove_matching_from_char(Character *ch, comparator comp, const Affect *pattern)` (member)
- `void affect::iterate_over_obj(Object *obj, affect_fn fn, void *data)` (member)
- `void affect::clear_list(Affect **list_head)` (member)
- `int set_tail(Character *ch, Character *victim, Flags tail_flags)` (member)
- `void affect::modify_room(Room *room, const Affect *paf, bool fAdd)` (member)
- `void affect::iterate_over_room(Room *room, affect_fn fn, void *data)` (member)
- `void affect::modify_char(void *owner, const Affect *paf, bool fAdd)` (member)
- `void affect::free_cache(Character *ch)` (member)
- *...and 94 more*


### Cluster 11

**Size**: 82 nodes

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
- *...and 72 more*


### Cluster 12

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


### Cluster 13

**Size**: 57 nodes

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
- *...and 47 more*


### Cluster 14

**Size**: 33 nodes

**Representative nodes**:

- `_as_flags` (member)
- `bool operator!=(const ObjectValue &lhs, const ObjectValue &rhs)` (member)
- `ObjectValue & ObjectValue::operator^=(const Flags &rhs)` (member)
- `int Format::to_c(ObjectValue &v)` (member)
- `ObjectValue & ObjectValue::operator-=(int rhs)` (member)
- `const ObjectValue ObjectValue::operator-(int rhs)` (member)
- `_value` (member)
- `ObjectValue & ObjectValue::operator+=(const ObjectValue &rhs)` (member)
- `bool operator==(const ObjectValue &lhs, const ObjectValue &rhs)` (member)
- `ObjectValue::ObjectValue()` (member)
- *...and 23 more*


### Cluster 15

**Size**: 27 nodes

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
- *...and 17 more*


### Cluster 16

**Size**: 26 nodes

**Representative nodes**:

- `Msyl2` (member)
- `Fsyl2` (member)
- `MagT_table` (member)
- `void generate_skillquest_mob(Character *ch, Character *questman, int level, int type)` (member)
- `Fsyl3` (member)
- `CleT_table` (member)
- `Msyl3` (member)
- `Msyl1` (member)
- `ThiT_table` (member)
- `Fsyl1` (member)
- *...and 16 more*


### Cluster 17

**Size**: 10 nodes

**Representative nodes**:

- `Type` (member)
- `virtual void event::Handler::notify(Type, Args &)=0` (member)
- `Handler & event::Handler::operator=(const Handler &)` (member)
- `void event::Dispatcher::fire(Type type, Args args)` (member)
- `event::Handler::Handler(const Handler &)` (member)
- `void event::Dispatcher::unsubscribe(Type type, Handler *s)` (member)
- `subscribers` (member)
- `Args` (member)
- `void event::Dispatcher::subscribe(Type type, Handler *s)` (member)
- `event::Handler` (compound)


### Cluster 18

**Size**: 10 nodes

**Representative nodes**:

- `necromancer_poses` (member)
- `mage_poses` (member)
- `paladin_poses` (member)
- `new_pose_table` (member)
- `bard_poses` (member)
- `warrior_poses` (member)
- `cleric_poses` (member)
- `ranger_poses` (member)
- `thief_poses` (member)
- `new_pose_struct` (compound)


### Cluster 19

**Size**: 4 nodes

**Representative nodes**:

- `Battle::Battle(const Battle &)` (member)
- `battle` (member)
- `Battle & Battle::operator=(const Battle &)` (member)
- `Battle` (compound)


### Cluster 20

**Size**: 4 nodes

**Representative nodes**:

- `virtual const std::string Character::identifier() const` (member)
- `virtual const std::string String::identifier() const` (member)
- `virtual const std::string Actable::identifier() const =0` (member)
- `virtual const std::string Object::identifier() const` (member)


### Cluster 21

**Size**: 3 nodes

**Representative nodes**:

- `Game::Game(const Game &)` (member)
- `Game & Game::operator=(const Game &)` (member)
- `Game` (compound)


### Cluster 22

**Size**: 3 nodes

**Representative nodes**:

- `Dispatcher & event::Dispatcher::operator=(const Dispatcher &)` (member)
- `event::Dispatcher::Dispatcher(const Dispatcher &)` (member)
- `event::Dispatcher` (compound)


### Cluster 23

**Size**: 3 nodes

**Representative nodes**:

- `spell_fun` (member)
- `SPELL_FUN` (member)
- `DECLARE_SPELL_FUN` (member)


### Cluster 24

**Size**: 2 nodes

**Representative nodes**:

- `quality_table` (member)
- `gem::quality_st` (compound)


### Cluster 25

**Size**: 2 nodes

**Representative nodes**:

- `DECLARE_DO_FUN` (member)
- `DO_FUN` (member)

