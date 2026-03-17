# Semantic Clustering Report

# Semantic Clustering Report

## Overview

Total clusters: 26

Total entities: 4549

Topic method: nmf

Number of topics: 15

Silhouette score: 0.26596701391273797


## Topics

1. Topic 0: character function player message command

2. Topic 1: flag bit flags bit flag entity

3. Topic 2: json item cjson memory data

4. Topic 3: constant game consistent identifier clear

5. Topic 4: object constructor copy new assignment

6. Topic 5: string case string object case insensitive insensitive

7. Topic 6: color slot color slot visual terminal

8. Topic 7: affect effect effects affects remort

9. Topic 8: damage resistance effects spell damage type

10. Topic 9: list linked linked list pointer node

11. Topic 10: room area location rooms world

12. Topic 11: variable player game variable exists rationale variable

13. Topic 12: clan war event clans events

14. Topic 13: destructor class derived virtual cleanup

15. Topic 14: skill character level combat attack


## Cluster Analysis

### Cluster 0

**Size**: 94 nodes

**Representative nodes**:

- `void spell_poison(skill::type sn, int level, Character *ch, void *vo, int target, int evolution)` (member)
- `bool HAS_RAFF(Character *ch, int flag)` (member)
- `void roll_raffects(Character *ch, Character *victim)` (member)
- `affect_checksum` (member)
- `void affect::remove_matching_from_char(Character *ch, comparator comp, const Affect *pattern)` (member)
- `void spell_holy_word(skill::type sn, int level, Character *ch, void *vo, int target, int evolution)` (member)
- `void do_visible(Character *ch, String argument)` (member)
- `void acid_effect(void *vo, int level, int dam, int target, int evolution)` (member)
- `size` (member)
- `bool is_blinded(const Character *ch)` (member)
- *...and 84 more*


### Cluster 1

**Size**: 36 nodes

**Representative nodes**:

- `const String room_bit_name(const Flags &flags)` (member)
- `cached_room_flags` (member)
- `ROOM_LAW` (member)
- `ROOM_NEWBIES_ONLY` (member)
- `FIELD_ROOM` (member)
- `ROOM_NOPORTAL` (member)
- `ENTITY_VR` (member)
- `ROOM_NOWHERE` (member)
- `ROOM_DARK` (member)
- `PLR_PRIVATE` (member)
- *...and 26 more*


### Cluster 2

**Size**: 25 nodes

**Representative nodes**:

- `void load_war_events()` (member)
- `int count_clans()` (member)
- `Object * vape_ceq_recursive(Character *ch, Object *obj, int depth)` (member)
- `previous` (member)
- `void rec_event(War *war, int type, const String &astr, const String &bstr, int number)` (member)
- `war_table_tail` (member)
- `war_table_head` (member)
- `next` (member)
- `void load_war_table()` (member)
- `void save_war_events()` (member)
- *...and 15 more*


### Cluster 3

**Size**: 358 nodes

**Representative nodes**:

- `wiznet_table` (member)
- `sex_table` (member)
- `GET_ATTR_AGE` (member)
- `Type` (member)
- `int weapon_lookup(const String &name)` (member)
- `vnum` (member)
- `suffixes_allowed` (member)
- `weapon_eq_rolls` (member)
- `vnum` (member)
- `Msyl2` (member)
- *...and 348 more*


### Cluster 4

**Size**: 228 nodes

**Representative nodes**:

- `FLAGS_NBITS` (member)
- `const String MobProg::type_to_name(Flags::Bit)` (member)
- `_as_flags` (member)
- `Flags::Flags(const Bit &b)` (member)
- `ObjectValue & ObjectValue::operator^=(const Flags &rhs)` (member)
- `form_flags` (member)
- `censor_flags` (member)
- `IS_THIEF` (member)
- `bool operator==(const Flags &lhs, const Flags &rhs)` (member)
- `flag_fields` (member)
- *...and 218 more*


### Cluster 5

**Size**: 85 nodes

**Representative nodes**:

- `void show_string(Descriptor *d, bool clear_remainder)` (member)
- `departed_list_line` (member)
- `chan_table` (member)
- `void do_send_announce(Character *ch, String argument)` (member)
- `bool worldmap::MapColor::operator==(const MapColor &rhs) const` (member)
- `void do_channels(Character *ch, String argument)` (member)
- `void quest_usage(Character *ch)` (member)
- `color_sector_map` (member)
- `const String wrap_string(const String &s, unsigned long wrap_len)` (member)
- `void worldmap::MapColor::precompute()` (member)
- *...and 75 more*


### Cluster 6

**Size**: 185 nodes

**Representative nodes**:

- `void spell_enchant_armor(skill::type sn, int level, Character *ch, void *vo, int target, int evolution)` (member)
- `vnum` (member)
- `Object * create_object(ObjectPrototype *pObjIndex, int level)` (member)
- `Object * generate_skillquest_obj(Character *ch, int level)` (member)
- `worldmap::Coordinate::Coordinate(int nx, int ny)` (member)
- `extra_flags` (member)
- `void spell_identify(skill::type sn, int level, Character *ch, void *vo, int target, int evolution)` (member)
- `extra_flags` (member)
- `Note::Note()` (member)
- `int count_items(const Object *obj)` (member)
- *...and 175 more*


### Cluster 7

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


### Cluster 8

**Size**: 547 nodes

**Representative nodes**:

- `DECLARE_DO_FUN` (member)
- `void mprog_tick_trigger(Character *mob)` (member)
- `void mprog_act_trigger(const char *buf, Character *mob, Character *ch, Object *obj, void *vo)` (member)
- `int deity_lookup(const String &name)` (member)
- `void do_buy(Character *ch, String argument)` (member)
- `void do_gossip(Character *ch, String argument)` (member)
- `void kill_off(Character *ch, Character *victim)` (member)
- `char * get_multi_command(Descriptor *d, const String &argument)` (member)
- `void update_pc_index(const Character *ch, bool remove)` (member)
- `static bool check_line(Character *ch, int line)` (member)
- *...and 537 more*


### Cluster 9

**Size**: 352 nodes

**Representative nodes**:

- `const Flags operator+(const Flags::Bit &lhs, const Flags::Bit &rhs)` (member)
- `ARG_1` (member)
- `bit` (member)
- `flag` (member)
- `bool Flags::has(const Flags::Bit &b) const` (member)
- `bit` (member)
- `Bit` (member)
- `bit` (member)
- `AFF_DETECT_MAGIC` (member)
- `ACT_PRACTICE` (member)
- *...and 342 more*


### Cluster 10

**Size**: 110 nodes

**Representative nodes**:

- `void do_rotate(Character *ch, String argument)` (member)
- `bool spec_squestmaster(Character *ch)` (member)
- `minimum_position` (member)
- `void do_brew(Character *ch, String argument)` (member)
- `bool check_blur(Character *ch, Character *victim, skill::type attack_skill, int attack_type)` (member)
- `void group_add(Character *ch, const String &name, bool deduct)` (member)
- `bool spec_cast_mage(Character *ch)` (member)
- `void do_critical_blow(Character *ch, String argument)` (member)
- `void do_scribe(Character *ch, String argument)` (member)
- `thac0_32` (member)
- *...and 100 more*


### Cluster 11

**Size**: 219 nodes

**Representative nodes**:

- `area` (member)
- `bool worldmap::Coordinate::is_valid() const` (member)
- `defprep` (member)
- `void do_open(Character *ch, String argument)` (member)
- `void do_sacrifice(Character *ch, String argument)` (member)
- `void update_handler()` (member)
- `void do_mpecho(Character *ch, String argument)` (member)
- `void spell_encampment(skill::type sn, int level, Character *ch, void *vo, int target, int evolution)` (member)
- `void do_east(Character *ch, String argument)` (member)
- `void death_cry(Character *ch)` (member)
- *...and 209 more*


### Cluster 12

**Size**: 126 nodes

**Representative nodes**:

- `next` (member)
- `void load_storage_list()` (member)
- `void obj_from_locker(Object *obj)` (member)
- `storage_list_head` (member)
- `disabled_first` (member)
- `object_list` (member)
- `MobProg::MobProg(FILE *fp)` (member)
- `void insert_departed(const String &name)` (member)
- `iterator & GarbageCollectingList< T >::iterator::operator++()` (member)
- `const Affect * affect::list_char(Character *ch)` (member)
- *...and 116 more*


### Cluster 13

**Size**: 492 nodes

**Representative nodes**:

- `_height` (member)
- `mud_exp` (member)
- `group` (member)
- `questloc` (member)
- `mod_plr` (member)
- `rolepoints` (member)
- `open_hour` (member)
- `confirmNewPass` (member)
- `dex_app` (member)
- `act` (member)
- *...and 482 more*


### Cluster 14

**Size**: 104 nodes

**Representative nodes**:

- `void cJSON_AddItemReferenceToObject(cJSON *object, const char *string, cJSON *item)` (member)
- `cJSON * cJSON_CreateTrue()` (member)
- `void cJSON_AddItemReferenceToArray(cJSON *array, cJSON *item)` (member)
- `cJSON * fwrite_player(Character *ch)` (member)
- `void cJSON_AddItemToObject(cJSON *object, const char *string, cJSON *item)` (member)
- `FLAGKEY` (member)
- `cJSON_AddTrueToObject` (member)
- `static const char * parse_number(cJSON *item, const char *num)` (member)
- `cJSON * cJSON_CreateNumber(double num)` (member)
- `cJSON * cJSON_CreateIntArray(const int *numbers, int count)` (member)
- *...and 94 more*


### Cluster 15

**Size**: 149 nodes

**Representative nodes**:

- `bool String::has_exact_words(const String &wordlist) const` (member)
- `const char * strchr(const String &str, int ch)` (member)
- `int strcmp(const String &astr, const String &bstr)` (member)
- `int Format::sprintf(String &str, const String &fmt, Params &&... params)` (member)
- `const char * strstr(const String &astr, const String &bstr)` (member)
- `const String print_bit_names(const std::vector< flag_type > &flag_table, const Flags &flags)` (member)
- `const String cgroup_bit_name(const Flags &flags)` (member)
- `String print_defense_modifiers(Character *ch, int where)` (member)
- `String Format::format(const String &fmt, Params &&... params)` (member)
- `void act(const String &format, Character *actor, const Actable *arg1, const Actable &arg2, int type, int min_pos=POS_RESTING, bool censor=false, Room *room=nullptr)` (member)
- *...and 139 more*


### Cluster 16

**Size**: 157 nodes

**Representative nodes**:

- `void do_mppurge(Character *ch, String argument)` (member)
- `void spell_gas_breath(skill::type sn, int level, Character *ch, void *vo, int target, int evolution)` (member)
- `void QuestArea::init()` (member)
- `int Location::to_int() const` (member)
- `room_prototypes` (member)
- `bool Room::is_dark() const` (member)
- `room_flags` (member)
- `void World::create_exits()` (member)
- `vnum` (member)
- `void spell_faerie_fog(skill::type sn, int level, Character *ch, void *vo, int target, int evolution)` (member)
- *...and 147 more*


### Cluster 17

**Size**: 117 nodes

**Representative nodes**:

- `Dispatcher & event::Dispatcher::operator=(const Dispatcher &)` (member)
- `Exit & Exit::operator=(const Exit &)` (member)
- `GarbageCollectingList< T >::GarbageCollectingList(const GarbageCollectingList &)` (member)
- `worldmap::Region::Region(const Region &)` (member)
- `Edit & Edit::operator=(const Edit &)` (member)
- `Clan & Clan::operator=(const Clan &)` (member)
- `World & World::operator=(const World &)` (member)
- `Tail::Tail()` (member)
- `Location & Location::operator=(const Location &l)` (member)
- `event::Handler::Handler()` (member)
- *...and 107 more*


### Cluster 18

**Size**: 146 nodes

**Representative nodes**:

- `day_names` (member)
- `self_msg` (member)
- `name` (member)
- `name` (member)
- `name` (member)
- `motd` (member)
- `material` (member)
- `player_name` (member)
- `others_auto` (member)
- `female` (member)
- *...and 136 more*


### Cluster 19

**Size**: 138 nodes

**Representative nodes**:

- `level` (member)
- `void spell_barrier(skill::type sn, int level, Character *ch, void *vo, int target, int evolution)` (member)
- `void affect::join_to_char(Character *ch, Affect *paf)` (member)
- `void spell_detect_evil(skill::type sn, int level, Character *ch, void *vo, int target, int evolution)` (member)
- `CAN_FLY` (member)
- `void spell_frenzy(skill::type sn, int level, Character *ch, void *vo, int target, int evolution)` (member)
- `void affect::iterate_over_obj(Object *obj, affect_fn fn, void *data)` (member)
- `void rem_raff_affect(Character *ch, int index)` (member)
- `where` (member)
- `void spell_protection_good(skill::type sn, int level, Character *ch, void *vo, int target, int evolution)` (member)
- *...and 128 more*


### Cluster 20

**Size**: 105 nodes

**Representative nodes**:

- `area_maxvnum` (member)
- `bool clan_in_war(Clan *clan, War *war, bool onlycurrent)` (member)
- `void do_iclantalk(Character *ch, String argument)` (member)
- `bool is_clan(Character *ch)` (member)
- `bool char_at_war(Character *ch)` (member)
- `inviters` (member)
- `bool can_see_room(const Character *ch, const Room *room)` (member)
- `questpoints_donated` (member)
- `clanname` (member)
- `void do_rank(Character *ch, String argument)` (member)
- *...and 95 more*


### Cluster 21

**Size**: 239 nodes

**Representative nodes**:

- `accessory_eq_rolls` (member)
- `armor_eq_rolls` (member)
- `ARMOR_HOLD` (member)
- `OBJ_VNUM_PORTAL` (member)
- `QUEST_OBJQUEST5` (member)
- `OBJ_VNUM_LEGS` (member)
- `ITEM_SCROLL` (member)
- `ITEM_CONTAINER` (member)
- `WIELD_EXOTIC` (member)
- `ITEM_FOOD` (member)
- *...and 229 more*


### Cluster 22

**Size**: 83 nodes

**Representative nodes**:

- `void spell_chill_touch(skill::type sn, int level, Character *ch, void *vo, int target, int evolution)` (member)
- `GET_ATTR_DAMROLL` (member)
- `void spell_dispel_good(skill::type sn, int level, Character *ch, void *vo, int target, int evolution)` (member)
- `void spell_fire_breath(skill::type sn, int level, Character *ch, void *vo, int target, int evolution)` (member)
- `todam` (member)
- `void spell_acid_breath(skill::type sn, int level, Character *ch, void *vo, int target, int evolution)` (member)
- `void spell_harm(skill::type sn, int level, Character *ch, void *vo, int target, int evolution)` (member)
- `void spell_burning_hands(skill::type sn, int level, Character *ch, void *vo, int target, int evolution)` (member)
- `void spell_heat_metal(skill::type sn, int level, Character *ch, void *vo, int target, int evolution)` (member)
- `void spell_shocking_grasp(skill::type sn, int level, Character *ch, void *vo, int target, int evolution)` (member)
- *...and 73 more*


### Cluster 23

**Size**: 213 nodes

**Representative nodes**:

- `void do_steal(Character *ch, String argument)` (member)
- `void check_protection_aura(Character *ch, Character *victim)` (member)
- `void say_spell(Character *ch, skill::type sn)` (member)
- `remort_guild` (member)
- `void spell_cure_light(skill::type sn, int level, Character *ch, void *vo, int target, int evolution)` (member)
- `bool spec_breath_any(Character *ch)` (member)
- `void spell_sleep(skill::type sn, int level, Character *ch, void *vo, int target, int evolution)` (member)
- `void prac_by_group(Character *ch, const String &argument)` (member)
- `void do_pstat(Character *ch, String argument)` (member)
- `bool HAS_RAFF_GROUP(Character *ch, int flag)` (member)
- *...and 203 more*


### Cluster 24

**Size**: 113 nodes

**Representative nodes**:

- `red` (member)
- `const String get_custom_color_name(Character *ch, int slot)` (member)
- `void set_color(Character *ch, int color, int bold)` (member)
- `green` (member)
- `color` (member)
- `void config_color(Character *ch, String argument)` (member)
- `lastcolor` (member)
- `_computed` (member)
- `const MapColor worldmap::Region::get_color(unsigned int x, unsigned int y) const` (member)
- `const String get_color_code(int color, int bold)` (member)
- *...and 103 more*


### Cluster 25

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

