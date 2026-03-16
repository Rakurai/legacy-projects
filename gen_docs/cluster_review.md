# Cluster Review — Phase 3 Pass 1

Generated from `build_chunks.py` output. 35 clusters from agglomerative Ward
clustering on typed weighted IDF-cosine similarity (domain 0.60, policy 0.20,
projection 0.10, infrastructure 0.10, utility excluded).

Silhouette: 0.625 at k=35.

---

## Reading guide

Each cluster shows:
- **Size** and **wave range** of its members
- **Character** — what makes this cluster distinct
- **Dominant domain caps** — domain capabilities present in >50% of members
- **Members** — grouped by entry-point type (command / spell / special)
- **Assessment** — editorial note on quality and recommended action

---

## Well-separated clusters (clear intent)

### C14 — Config/toggle commands (71 eps, waves 4–10)

No domain capabilities. Purely flags + output + state_rules + string_ops.

Commands (69): do_addexit, do_alia, do_alias, do_announce, do_autoassist,
do_autoexit, do_autogold, do_autolist, do_autoloot, do_autorecall, do_autosac,
do_autosplit, do_autotick, do_bamfin, do_bamfout, do_brief, do_chatmode,
do_clear, do_color, do_combine, do_commands, do_compact, do_convert,
do_copyove, do_ctest, do_deaf, do_defensive, do_delet, do_departed,
do_description, do_fingerinfo, do_grouplist, do_huh, do_load, do_motd,
do_mpclearmoney, do_noloot, do_nosummon, do_notify, do_pet, do_pipe, do_prefi,
do_prefix, do_private, do_prompt, do_query, do_qui, do_quiet, do_reboo,
do_remexit, do_rename, do_replay, do_scroll, do_send_announce, do_show,
do_showlast, do_showlost, do_showraff, do_shutdow, do_sla, do_smote,
do_socials, do_superwiz, do_typelist, do_unalias, do_video, do_vnum,
do_wizhelp, do_wiznet

Spells (2): spell_detect_poison, spell_null

**Assessment:** Clean config/preference cluster. Some admin commands mixed in
(do_load, do_shutdow, do_reboo, do_superwiz) — may want to split an
"admin-control" sub-group out. Otherwise good as a "player preferences &
settings" use case.

---

### C3 — Notes system (10 eps, waves 10–10)

Distinctive cap: **notes**. All members are note/bulletin-board commands.

Commands (10): do_changes, do_idea, do_immquest, do_next, do_note,
do_old_next, do_personal, do_roleplay, do_trade, do_unread

**Assessment:** Extremely clean. Maps directly to a "notes & bulletin boards"
use case. Good standalone chunk.

---

### C17 — World queries & communication (17 eps, waves 4–10)

Distinctive cap: **world_structure** (without other domain caps).

Commands (16): do_areas, do_gtell, do_heed, do_mfind, do_mlevel, do_noreply,
do_ofind, do_olevel, do_pocket, do_qtell, do_roomlist, do_rwhere,
do_spousetalk, do_time, do_vlist, do_zecho

Spells (1): spell_control_weather

**Assessment:** Mostly world-query commands (do_mfind, do_ofind, do_areas,
do_roomlist, do_vlist). Some communication commands mixed in (do_gtell,
do_qtell, do_spousetalk, do_heed, do_noreply) — these use world_structure
for character lookup but are functionally "tell/chat" commands. Consider
splitting into "world queries" vs "directed communication."

---

### C28 — Healing / combat support spells (6 eps, waves 11–11)

Distinctive cap: **combat** only.

Commands (1): do_peace

Spells (5): spell_cure_critical, spell_cure_light, spell_cure_serious,
spell_divine_healing, spell_heal

**Assessment:** Clean healing-spell cluster. do_peace is admin combat-reset,
semantically different. Consider moving do_peace elsewhere.

---

### C1 — Skills inspection (6 eps, waves 5–10)

Distinctive cap: **skills_progression** only.

Commands (4): do_autopeek, do_groups, do_slookup, do_worth

Spells (1): spell_mass_healing

Specials (1): spec_cast_judge

**Assessment:** Primarily "inspect your skills/stats" commands.
spell_mass_healing and spec_cast_judge are strays — they touch
skills_progression but serve different intents (healing / NPC casting).

---

### C2 — Level progression (7 eps, waves 6–10)

Distinctive caps: **movement + skills_progression**.

Commands (4): do_eremort, do_evolve, do_levels, do_mark

Specials (3): spec_cast_cleric, spec_cast_mage, spec_cast_undead

**Assessment:** Level/evolution commands cluster well. The spec_cast_*
specials are NPC casting routines that share the skills_progression
dependency — they're not truly about leveling. Consider separating.

---

### C19 — Affect-only (4 eps, waves 7–10)

Distinctive cap: **affects** alone.

Commands (2): do_dump, do_visible

Spells (2): spell_darkness, spell_farsight

**Assessment:** Small but coherent — commands that primarily manipulate
visibility/affect state. Might merge into a broader "buff/debuff" chunk.

---

### C16 — Room exits / weather (3 eps, waves 9–9)

Distinctive caps: **movement + world_structure + display**.

Commands (3): do_exlist, do_roomexits, do_weather

**Assessment:** Clean "room display" cluster. Small enough to merge into
a broader movement/navigation chunk.

---

## The "everything" cluster

### C18 — General commands (184 eps, waves 10–10) ⚠️

Every non-utility capability at 100% frequency. This is the catch-all for
entry points whose capability profiles are indistinguishable at the typed
weighted similarity level.

Commands (132): do_accept, do_advance, do_affects, do_afk, do_allow,
do_allsave, do_alternate, do_aura, do_autoboot, do_backup, do_ban, do_bonus,
do_breakup, do_bug, do_canmakebag, do_close, do_compare, do_consider,
do_credits, do_departedlist, do_disable, do_divorce, do_edit, do_email,
do_equipment, do_evoset, do_extraset, do_file, do_fill, do_flag, do_fly,
do_follow, do_followerlist, do_freeze, do_fry, do_fyi, do_gain, do_gamein,
do_gameout, do_group, do_hbb, do_hbi, do_hedit, do_help, do_immapp, do_imotd,
do_inventory, do_invis, do_land, do_leader, do_loadhelps, do_lock, do_log,
do_lower, do_lurk, do_marry, do_master, do_mpasound, do_mpecho,
do_mpechoaround, do_mpechoat, do_mpstat, do_mset, do_mwhere, do_newlock,
do_newpasswd, do_nofollow, do_ooc, do_open, do_owner, do_page, do_paintbow,
do_pardon, do_password, do_pecho, do_permit, do_pk, do_pmote, do_pose,
do_pour, do_practice, do_printhelps, do_propose, do_protect, do_pstat,
do_punish, do_qpconv, do_raffset, do_rank, do_reject, do_remort, do_reply,
do_report, do_revoke, do_ridea, do_rppaward, do_rset, do_rules, do_save,
do_scon, do_setgamein, do_setgameout, do_showflags, do_skillpoint, do_snoop,
do_sockets, do_split, do_sset, do_storage, do_story, do_string, do_switch,
do_tail, do_tell, do_testpose, do_title, do_touch, do_train, do_typo,
do_undeny, do_unlock, do_wake, do_wbb, do_wbi, do_where, do_whisper,
do_whois, do_wizgroup, do_wizlist, do_wizlock, do_work, do_yell

Spells (48): spell_armor, spell_barrier, spell_bless, spell_blood_blade,
spell_blood_moon, spell_bone_wall, spell_channel, spell_dazzling_light,
spell_detect_evil, spell_detect_good, spell_detect_hidden, spell_detect_invis,
spell_detect_magic, spell_divine_regeneration, spell_faerie_fire,
spell_fireproof, spell_flame_blade, spell_flameshield, spell_fly,
spell_focus, spell_force, spell_frenzy, spell_frost_blade, spell_full_heal,
spell_giant_strength, spell_hex, spell_infravision, spell_invis,
spell_ironskin, spell_know_alignment, spell_light_of_truth,
spell_locate_object, spell_mass_invis, spell_midnight, spell_pass_door,
spell_protection_evil, spell_protection_good, spell_rayban,
spell_regeneration, spell_remove_invis, spell_sanctuary, spell_scry,
spell_sheen, spell_shield, spell_shock_blade, spell_steel_mist,
spell_stone_skin, spell_talon

Specials (4): spec_cast_adept, spec_nasty, spec_poison, spec_thief

**Assessment:** This cluster needs sub-clustering. Eyeballing the contents,
there are at least these intent families inside:

**Admin/immortal commands** — do_advance, do_allow, do_ban, do_flag, do_freeze,
do_fry, do_invis, do_log, do_mset, do_newlock, do_newpasswd, do_pardon,
do_permit, do_punish, do_snoop, do_sockets, do_switch, do_wizgroup,
do_wizlist, do_wizlock, do_sset, do_rset, do_string, do_pstat, do_owner,
do_undeny, do_revoke, etc.

**Player info/display** — do_affects, do_equipment, do_inventory, do_report,
do_score (in C23), do_whois, do_where, do_credits, do_help, do_rules,
do_showflags

**Communication** — do_tell, do_reply, do_whisper, do_yell, do_ooc, do_page,
do_pecho, do_pmote, do_mpecho, do_mpechoaround, do_mpechoat

**Object interaction** — do_close, do_open, do_lock, do_unlock, do_fill,
do_pour, do_compare

**Social/relationship** — do_marry, do_divorce, do_propose, do_breakup,
do_accept, do_reject

**Player progression** — do_practice, do_train, do_gain, do_remort

**MobProg commands** — do_mpasound, do_mpecho, do_mpechoaround, do_mpechoat,
do_mpstat

**Buff/enhancement spells** — spell_armor, spell_bless, spell_shield,
spell_sanctuary, spell_stone_skin, spell_giant_strength, spell_fly,
spell_haste (in C21), spell_ironskin, spell_flameshield, spell_barrier

**Detection spells** — spell_detect_evil, spell_detect_good, spell_detect_hidden,
spell_detect_invis, spell_detect_magic, spell_know_alignment, spell_infravision,
spell_farsight (in C19)

**Weapon enhancement spells** — spell_flame_blade, spell_frost_blade,
spell_shock_blade, spell_blood_blade, spell_talon

**Miscellaneous** — do_bug, do_typo, do_work, do_fyi, do_ridea (feedback/meta),
do_save, do_backup, do_allsave (persistence), do_fly, do_land (movement mode)

---

## Combat-centric clusters

### C30 — Full combat + damage spells (79 eps, waves 10–12)

All 30 capabilities at near-100%. Distinguished from C18 by: **combat, magic,
clans, economy, pvp, social, persistence, runtime, display** all present.
This is the "maximum dependency" cluster.

Commands (34): do_auction, do_backstab, do_bash, do_brandish, do_buy,
do_cast, do_circle, do_clanwithdraw, do_critical_blow, do_crush, do_debug,
do_delete, do_dirt, do_disarm, do_drag, do_eat, do_flee, do_give, do_kick,
do_kill, do_mpkill, do_push, do_quaff, do_quest, do_quit, do_rage,
do_recite, do_riposte, do_shadow, do_shoot, do_slay, do_steal, do_trip,
do_zap

Spells (39): spell_acid_blast, spell_acid_breath, spell_acid_rain,
spell_blizzard, spell_burning_hands, spell_call_lightning,
spell_cause_critical, spell_cause_light, spell_cause_serious,
spell_chain_lightning, spell_chill_touch, spell_colour_spray,
spell_demonfire, spell_dispel_evil, spell_dispel_good, spell_earthquake,
spell_energy_drain, spell_fire_breath, spell_fireball, spell_firestorm,
spell_flamestrike, spell_frost_breath, spell_gas_breath,
spell_general_purpose, spell_harm, spell_heat_metal, spell_high_explosive,
spell_holy_word, spell_lightning_bolt, spell_lightning_breath,
spell_magic_missile, spell_pain, spell_power_word, spell_quick,
spell_ray_of_truth, spell_sap, spell_shocking_grasp, spell_sunray,
spell_wrath

Specials (6): spec_clanguard, spec_executioner, spec_guard, spec_ogre_member,
spec_patrolman, spec_troll_member

**Assessment:** Core combat cluster. Clean: damage spells, melee skills,
combat commands. do_buy/do_auction/do_quest/do_quit/do_delete are non-combat
strays pulled in by their maximal dependency profiles. The 39 damage spells
are a coherent sub-family. Consider splitting into:
- Melee combat (bash, kick, backstab, disarm, trip, etc.)
- Damage spells (fireball, lightning, acid, etc.)
- Commerce (buy, auction, give — economy-driven)
- NPC guards (spec_guard, spec_executioner, etc.)

---

### C27 — Combat + skills commands (24 eps, waves 11–11)

Combat + all non-economic domain caps.

Commands (15): do_adjust, do_align, do_berserk, do_deny, do_envenom,
do_familiar, do_hammerstrike, do_hide, do_lay_on_hands, do_lore, do_peek,
do_pick, do_restore, do_sneak, do_wizify

Spells (2): spell_calm, spell_dazzle

Specials (7): spec_breath_acid, spec_breath_any, spec_breath_fire,
spec_breath_frost, spec_breath_gas, spec_breath_lightning, spec_charm

**Assessment:** Mixed bag. do_berserk, do_envenom, do_hammerstrike are
combat skills. do_hide, do_sneak, do_peek, do_pick are rogue skills.
spec_breath_* are dragon breath specials. do_deny, do_wizify, do_adjust,
do_restore are admin commands. Needs splitting.

---

### C25 — Navigation + combat (15 eps, waves 11–11)

Combat + magic + movement all present.

Commands (14): do_enter, do_fod, do_goto, do_hunt, do_look, do_mpcast,
do_mpgoto, do_mppurge, do_mptransfer, do_relocate, do_return, do_sing,
do_transfer, do_violate

Spells (1): spell_word_of_recall

**Assessment:** Primarily movement/teleportation commands (do_goto, do_enter,
do_transfer, do_relocate, do_mptransfer, do_mpgoto, spell_word_of_recall).
do_look is the core "inspect room" command. do_hunt is movement toward a
target. do_fod/do_violate are admin destruction. Should split into:
- Navigation/teleportation
- Room inspection (do_look)
- Admin destruction

---

### C24 — PvP / clan combat (10 eps, waves 11–12)

Distinguished by **pvp** cap.

Commands (9): do_battle, do_clan_recall, do_duel, do_join, do_recall,
do_rescue, do_rotate, do_spell, do_unjoin

Spells (1): spell_polymorph

**Assessment:** PvP and group-combat commands. Clean use-case family.

---

## Economy / object clusters

### C23 — Economy + objects (17 eps, waves 4–10)

Distinctive cap: **economy**.

Commands (13): do_balance, do_check, do_deposit, do_drop, do_get,
do_identify, do_invite, do_list, do_score, do_stat, do_value,
do_weddingring, do_withdraw

Spells (4): spell_create_parchment, spell_create_rose, spell_create_vial,
spell_protect_container

**Assessment:** Economy/inventory cluster. do_get, do_drop are object
manipulation; do_balance, do_deposit, do_withdraw are banking; do_list,
do_value, do_buy (in C30) are commerce. do_score/do_stat are strays
(info display). Consider splitting into:
- Object manipulation (get, drop, identify)
- Banking (balance, deposit, withdraw)
- Information display (score, stat)

---

### C22 — Object creation/manipulation (36 eps, waves 10–10)

Distinctive cap: **objects** (vs C18 which lacks it at clustering resolution).

Commands (23): do_chown, do_create, do_drink, do_hone, do_inset, do_junk,
do_locker, do_mpjunk, do_mpoload, do_newbiekit, do_oclone, do_oload,
do_outfit, do_pit, do_put, do_reload, do_remove, do_rest, do_sacrifice,
do_sit, do_sleep, do_stand, do_strongbox

Spells (11): spell_continual_light, spell_create_food, spell_create_sign,
spell_create_spring, spell_create_water, spell_encampment,
spell_enchant_armor, spell_enchant_weapon, spell_recharge, spell_shrink,
spell_teleport_object

Specials (2): spec_fido, spec_janitor

**Assessment:** Object creation/loading + position commands. do_rest,
do_sit, do_sleep, do_stand are position changes — not object commands.
Consider splitting into:
- Object creation/loading (create, oload, newbiekit, enchant)
- Object placement (put, junk, sacrifice, pit, locker)
- Character position (rest, sit, sleep, stand)

---

### C26 — Crafting / healing services (10 eps, waves 11–11)

Commands (8): do_brew, do_firebuilding, do_forge, do_heal, do_repair,
do_scribe, do_sell, do_smite

Spells (2): spell_imprint, spell_remove_alignment

**Assessment:** Crafting and NPC-service commands. Coherent "crafting &
trade services" use case.

---

### C35 — Equipment / object use (7 eps, waves 10–11)

Commands (4): do_donate, do_exits, do_second, do_wear

Spells (3): spell_floating_disc, spell_holy_sword, spell_identify

**Assessment:** Equipment management. do_exits is a stray (room display).

---

## Social / communication clusters

### C32 — Clan chat & channels (14 eps, waves 10–10)

Distinctive caps: **clans + social**.

Commands (14): do_clandeposit, do_clanqp, do_clantalk, do_flame,
do_globalsocial, do_gossip, do_grats, do_ic, do_immtalk, do_memory,
do_music, do_pray, do_question, do_qwest

**Assessment:** Communication channels and clan interaction. do_memory is a
stray (admin/debug). Otherwise clean "channels & clan" use case.

---

### C33 — Clan admin & search (16 eps, waves 10–10)

Distinctive cap: **clans**.

Commands (15): do_cedit, do_channels, do_clanlist, do_clanpower,
do_deputize, do_finger, do_flagsearch, do_guild, do_iclantalk,
do_oldscan, do_owhere, do_scan, do_scatter, do_war, do_who

Spells (1): spell_locate_life

**Assessment:** Clan administration + player-finding commands. do_scan,
do_who, do_finger, do_flagsearch are "find/inspect players" — could be
a separate "player directory" family.

---

### C31 — Social interaction & admin force (13 eps, waves 10–12)

Distinctive cap: **social**.

Commands (13): do_at, do_config, do_doas, do_emote, do_engrave, do_for,
do_force, do_ignore, do_mpat, do_mpforce, do_order, do_say, do_sedit

**Assessment:** Mixed. do_emote, do_say are social/RP commands. do_at,
do_for, do_force, do_mpat, do_mpforce, do_order are admin control.
do_config, do_sedit are configuration. Needs splitting into:
- Social/RP (say, emote, engrave)
- Admin force (at, for, force, order, mpat, mpforce)
- Config (config, sedit)

---

## Magic clusters

### C21 — Debuff / status-change spells (35 eps, waves 10–12)

Distinctive cap: **magic**.

Commands (8): do_clone, do_mload, do_morph, do_mpmload, do_skills,
do_spells, do_splat, do_warp

Spells (27): spell_age, spell_animate_gargoyle, spell_animate_skeleton,
spell_animate_wraith, spell_animate_zombie, spell_blindness,
spell_cancellation, spell_change_sex, spell_cure_blindness,
spell_cure_disease, spell_cure_poison, spell_curse, spell_dispel_magic,
spell_faerie_fog, spell_fear, spell_haste, spell_paralyze, spell_plague,
spell_poison, spell_remove_curse, spell_resurrect, spell_sleep, spell_slow,
spell_starve, spell_summon, spell_ventriloquate, spell_weaken

**Assessment:** Mostly status-effect spells (blindness, curse, poison, sleep,
slow, fear, etc.) + cure/remove spells. The do_clone/do_mload/do_mpmload
are admin creation commands — strays. do_skills/do_spells are info display.
Consider splitting admin commands out.

---

### C34 — Teleportation / summoning spells (9 eps, waves 10–10)

Distinctive caps: **clans + magic**.

Commands (1): do_spousegate

Spells (8): spell_charm_person, spell_gate, spell_nexus, spell_portal,
spell_smokescreen, spell_summon_object, spell_teleport, spell_vision

**Assessment:** Clean "teleportation / summoning" spell family.

---

## Infrastructure / system clusters

### C29 — System / directional movement (14 eps, waves 12–12)

All capabilities at 100% including **runtime + display + persistence**.

Commands (13): do_copyover, do_disconnect, do_down, do_east, do_fuckoff,
do_linkload, do_north, do_purge, do_reboot, do_shutdown, do_south, do_up,
do_west

Specials (1): spec_mayor

**Assessment:** Surprising mix. Cardinal movement commands (north, south,
east, west, up, down) clustered with server control (reboot, shutdown,
copyover, purge). They share the wave-12 "touches everything" profile.
Needs splitting into:
- Cardinal movement
- Server administration

---

## Small / singleton clusters

### C4 — Attribute display + config (9 eps, waves 4–10)

Commands (8): do_claninfo, do_echo, do_flaglist, do_relevel, do_secure,
do_set, do_wimpy

Spells (1): spell_refresh

**Assessment:** "Display/set attributes" cluster. do_echo/do_recho are
output commands. Small enough to merge into C14 (config) or split.

### C20 — World-object inspection (7 eps, waves 9–10)

Commands (7): do_addapply, do_autograph, do_despell, do_examine, do_oset,
do_play, do_swho

**Assessment:** Object inspection and modification. Coherent.

### Singletons: C5 (do_count), C6 (do_censor), C15 (do_immname)

Merge into config/admin cluster.

### Stub specials: C7–C13

spec_blacksmith, spec_fight_clanguard, spec_lookup, spec_name,
spec_questmaster, spec_sage, spec_squestmaster — empty or near-empty
special functions. Mark as stubs.

---

## Summary of recommended actions

| Action | Clusters | Rationale |
|---|---|---|
| **Accept as-is** | C3 (notes), C24 (pvp), C26 (crafting), C34 (teleport spells) | Clean, coherent use-case families |
| **Accept with minor cleanup** | C14 (config), C17 (world queries), C28 (healing), C32 (channels), C33 (clan admin) | Remove 2–3 strays each |
| **Sub-cluster required** | C18 (184 eps), C30 (79 eps) | Too broad — need secondary clustering or manual triage |
| **Split by intent** | C22 (objects+position), C25 (nav+admin), C27 (combat+rogue+admin), C29 (movement+server), C31 (social+admin) | Mixed intent families that capability similarity can't separate |
| **Merge singletons** | C5, C6, C15, C4 → into C14 | Too small to be standalone |
| **Mark as stubs** | C7–C13 | Empty special functions |

### The C18 problem

The 184-entry-point catch-all needs secondary analysis. Options:
1. **Sub-cluster on doc-brief embeddings** — use generated function
   documentation to separate by semantic intent rather than capability overlap.
2. **Name-heuristic split** — group by command name patterns (spell_* = buff
   spells, do_mp* = mobprog, etc.) then cluster residual.
3. **Manual triage** — assign families by inspection using the intent
   groupings listed in the C18 assessment above.

Recommended: approach (1) for automated candidate generation, validated
against the manual groupings in (3).
