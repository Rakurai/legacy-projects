# Hierarchical System View


## Overview

This document presents a hierarchical view of the Legacy MUD system, 
organizing subsystems into logical groups based on their function and relationships.


## Hierarchy

- **Legacy MUD System**

  - **Core**

    - **Obj Char Group**

      - Spec Mprog (357 entities)

      - Read Confirm (29 entities)

      - String Operator!= (42 entities)

      - Table Color (10 entities)

      - Vnum Name (5 entities)

      - Guild Level (62 entities)

      - Operator= Extra (47 entities)

      - Obj Char (450 entities)

      - From Obj (153 entities)

      - Weather Day (111 entities)

      - Color Scan (11 entities)

      - Char Group (364 entities)

      - Array String (116 entities)

      - Garbage List (27 entities)

    - **Vnum Prototype Group**

      - Flags Act (38 entities)

      - Operator Flags (75 entities)

      - Flags Name (162 entities)

      - Bit Core (66 entities)

      - Vnum Prototype (297 entities)

      - Char Level (468 entities)

      - String Prog (27 entities)

      - Level Squestmob (57 entities)

      - War Clan (170 entities)

      - Core variable (9 entities)

  - **Support**

    - Act Dispatcher (39 entities)

  - **Data**

    - **Handle Input Group**

      - Duel Arena (50 entities)

      - Help Disabled (128 entities)

      - Handle Input (166 entities)

      - Name Loot (93 entities)

      - Race Name (99 entities)

      - Afk Pwd (12 entities)

    - **Edit Note Group**

      - Edit Note (151 entities)

      - Qtell Wizlist (34 entities)

      - Video Color (84 entities)

      - Social Departed (78 entities)

      - Color Custom (27 entities)

      - Flags T100 (43 entities)

    - Quality Keyword (4 entities)

  - **Interface**

    - **Conn:: State Group**

      - Conn:: State (61 entities)

      - Char Show (8 entities)

      - Types Constants (122 entities)

      - Handle Wimpy (20 entities)

      - Name Description (49 entities)

      - Descriptor Read (24 entities)

      - Autograph Newbiekit (5 entities)

      - Recall Reject (19 entities)

      - Room Color (80 entities)


## Subsystem Relationships

The following sections describe the relationships between subsystems.


### Core Subsystems

#### Obj Char Group

**Dependencies**:

- Char Level (349 connections)
- Obj Char (243 connections)
- String Operator!= (184 connections)
- Conn:: State (181 connections)
- Bit Core (167 connections)
- Types Constants (147 connections)
- Flags Act (125 connections)
- Vnum Prototype (95 connections)
- Handle Input (87 connections)
- Room Color (73 connections)
- Descriptor Read (56 connections)
- Char Group (42 connections)
- Guild Level (36 connections)
- Handle Wimpy (32 connections)
- Name Description (22 connections)
- From Obj (16 connections)
- Duel Arena (12 connections)
- Act Dispatcher (10 connections)
- Weather Day (9 connections)
- Read Confirm (8 connections)
- Level Squestmob (8 connections)
- War Clan (6 connections)
- Flags T100 (5 connections)
- Garbage List (5 connections)
- Operator Flags (5 connections)
- Color Scan (4 connections)
- Color Custom (4 connections)
- Help Disabled (3 connections)
- Recall Reject (3 connections)
- Edit Note (3 connections)
- Char Show (3 connections)
- Afk Pwd (2 connections)
- Video Color (2 connections)
- Flags Name (2 connections)
- Social Departed (1 connections)
- Array String (1 connections)


**Dependencies**:

- Conn:: State (47 connections)
- Handle Wimpy (4 connections)
- Descriptor Read (3 connections)
- Room Color (2 connections)
- Help Disabled (2 connections)
- Garbage List (1 connections)
- String Operator!= (1 connections)
- Handle Input (1 connections)
- Level Squestmob (1 connections)
- Color Custom (1 connections)
- Char Group (1 connections)


**Dependencies**:

- Descriptor Read (4 connections)
- Help Disabled (3 connections)
- Vnum Prototype (3 connections)
- Operator Flags (3 connections)
- Array String (1 connections)
- Obj Char (1 connections)
- Operator= Extra (1 connections)
- Char Level (1 connections)
- Char Group (1 connections)
- Act Dispatcher (1 connections)


**Dependencies**:

- Char Group (2 connections)


**Dependencies**:

- Char Level (1 connections)
- String Operator!= (1 connections)


**Dependencies**:

- Char Group (34 connections)
- Spec Mprog (24 connections)
- Char Level (15 connections)
- Obj Char (13 connections)
- Conn:: State (13 connections)
- Social Departed (11 connections)
- String Operator!= (7 connections)
- Race Name (6 connections)
- War Clan (3 connections)
- Flags Act (2 connections)
- Garbage List (2 connections)
- Weather Day (2 connections)
- Vnum Prototype (1 connections)
- Char Show (1 connections)
- Edit Note (1 connections)
- Handle Input (1 connections)


**Dependencies**:

- Vnum Prototype (60 connections)
- Obj Char (18 connections)
- Help Disabled (3 connections)
- Garbage List (3 connections)
- Conn:: State (3 connections)
- Spec Mprog (1 connections)
- Char Group (1 connections)
- String Operator!= (1 connections)
- Flags Act (1 connections)
- Guild Level (1 connections)


**Dependencies**:

- Char Level (492 connections)
- String Operator!= (228 connections)
- Spec Mprog (206 connections)
- Conn:: State (159 connections)
- Vnum Prototype (136 connections)
- Char Group (135 connections)
- From Obj (121 connections)
- Handle Input (96 connections)
- Room Color (96 connections)
- Descriptor Read (84 connections)
- Types Constants (82 connections)
- Bit Core (74 connections)
- Guild Level (63 connections)
- Handle Wimpy (42 connections)
- Name Description (35 connections)
- Level Squestmob (29 connections)
- Garbage List (27 connections)
- Read Confirm (27 connections)
- Array String (26 connections)
- Edit Note (24 connections)
- Flags Act (22 connections)
- War Clan (22 connections)
- Operator Flags (21 connections)
- Duel Arena (17 connections)
- Flags Name (14 connections)
- Weather Day (12 connections)
- Flags T100 (10 connections)
- Help Disabled (5 connections)
- Color Custom (5 connections)
- Act Dispatcher (4 connections)
- Color Scan (4 connections)
- Video Color (3 connections)
- Race Name (1 connections)
- Afk Pwd (1 connections)
- Social Departed (1 connections)
- Vnum Name (1 connections)
- Char Show (1 connections)
- Name Loot (1 connections)
- Quality Keyword (1 connections)


**Dependencies**:

- Char Level (55 connections)
- Obj Char (43 connections)
- Spec Mprog (30 connections)
- Conn:: State (29 connections)
- Char Group (23 connections)
- String Operator!= (13 connections)
- Operator Flags (12 connections)
- Bit Core (6 connections)
- Handle Input (5 connections)
- Types Constants (5 connections)
- Weather Day (5 connections)
- Guild Level (3 connections)
- Vnum Prototype (3 connections)
- Edit Note (2 connections)
- Room Color (2 connections)
- Handle Wimpy (2 connections)
- Read Confirm (1 connections)
- Duel Arena (1 connections)
- Recall Reject (1 connections)
- Flags T100 (1 connections)
- Name Description (1 connections)


**Dependencies**:

- Char Level (30 connections)
- Obj Char (20 connections)
- Vnum Prototype (19 connections)
- String Operator!= (19 connections)
- Spec Mprog (19 connections)
- Char Group (17 connections)
- Conn:: State (10 connections)
- Guild Level (10 connections)
- Handle Input (8 connections)
- Bit Core (8 connections)
- Room Color (6 connections)
- Flags Act (5 connections)
- Read Confirm (4 connections)
- Handle Wimpy (3 connections)
- From Obj (3 connections)
- Garbage List (3 connections)
- Types Constants (2 connections)
- Level Squestmob (2 connections)
- Help Disabled (2 connections)
- Name Description (1 connections)
- Act Dispatcher (1 connections)
- Duel Arena (1 connections)
- Recall Reject (1 connections)
- Qtell Wizlist (1 connections)
- Descriptor Read (1 connections)


**Dependencies**:

- Obj Char (4 connections)
- Types Constants (2 connections)
- Spec Mprog (2 connections)
- Color Custom (2 connections)
- Handle Input (2 connections)
- String Operator!= (2 connections)
- Room Color (1 connections)
- Video Color (1 connections)
- Conn:: State (1 connections)
- Table Color (1 connections)


**Dependencies**:

- Guild Level (268 connections)
- Char Level (220 connections)
- String Operator!= (157 connections)
- Conn:: State (149 connections)
- Obj Char (110 connections)
- Spec Mprog (104 connections)
- From Obj (102 connections)
- Flags Act (77 connections)
- Handle Input (76 connections)
- Read Confirm (65 connections)
- Room Color (56 connections)
- Descriptor Read (51 connections)
- Name Description (50 connections)
- Types Constants (41 connections)
- Video Color (41 connections)
- Bit Core (35 connections)
- Vnum Prototype (34 connections)
- Handle Wimpy (32 connections)
- War Clan (32 connections)
- Array String (28 connections)
- Race Name (13 connections)
- Flags Name (13 connections)
- Level Squestmob (11 connections)
- Operator Flags (10 connections)
- Color Custom (9 connections)
- Flags T100 (7 connections)
- Weather Day (5 connections)
- Afk Pwd (4 connections)
- Help Disabled (4 connections)
- Qtell Wizlist (4 connections)
- Act Dispatcher (4 connections)
- Autograph Newbiekit (3 connections)
- Social Departed (2 connections)
- Edit Note (2 connections)


**Dependencies**:

- Char Group (92 connections)
- String Operator!= (30 connections)
- Obj Char (27 connections)
- Edit Note (15 connections)
- Afk Pwd (13 connections)
- Name Description (12 connections)
- Guild Level (9 connections)
- War Clan (8 connections)
- Level Squestmob (6 connections)
- Char Level (6 connections)
- Vnum Prototype (6 connections)
- Conn:: State (5 connections)
- Color Custom (4 connections)
- Flags Act (4 connections)
- Spec Mprog (4 connections)
- Operator Flags (3 connections)
- Read Confirm (3 connections)
- Help Disabled (3 connections)
- Garbage List (2 connections)
- Room Color (2 connections)
- Qtell Wizlist (1 connections)
- Social Departed (1 connections)
- Descriptor Read (1 connections)
- Handle Input (1 connections)
- Video Color (1 connections)
- From Obj (1 connections)


**Dependencies**:

- Obj Char (4 connections)
- Conn:: State (3 connections)
- Spec Mprog (1 connections)
- Char Group (1 connections)
- String Operator!= (1 connections)
- Qtell Wizlist (1 connections)


#### Vnum Prototype Group

**Dependencies**:

- Operator Flags (22 connections)
- Bit Core (20 connections)
- Char Group (11 connections)
- Conn:: State (10 connections)
- Spec Mprog (5 connections)
- Flags T100 (4 connections)
- Room Color (2 connections)
- Garbage List (2 connections)
- Flags Name (1 connections)
- Obj Char (1 connections)


**Dependencies**:

- Vnum Prototype (11 connections)
- String Operator!= (9 connections)
- Obj Char (4 connections)
- Bit Core (4 connections)
- From Obj (2 connections)
- Spec Mprog (1 connections)


**Dependencies**:

- String Operator!= (62 connections)
- Bit Core (53 connections)
- Obj Char (35 connections)
- Spec Mprog (26 connections)
- Operator Flags (24 connections)
- Flags Act (14 connections)
- Char Group (12 connections)
- Conn:: State (10 connections)
- Vnum Prototype (9 connections)
- Char Level (8 connections)
- Handle Input (6 connections)
- Room Color (5 connections)
- Name Description (5 connections)
- From Obj (4 connections)
- Types Constants (4 connections)
- Descriptor Read (4 connections)
- Handle Wimpy (3 connections)
- Core variable (3 connections)
- War Clan (3 connections)
- Level Squestmob (3 connections)
- Read Confirm (2 connections)
- Guild Level (2 connections)
- Flags T100 (1 connections)
- Color Custom (1 connections)
- Act Dispatcher (1 connections)
- Edit Note (1 connections)


**Dependencies**:

- Flags T100 (41 connections)
- Flags Act (22 connections)
- Operator Flags (3 connections)
- Edit Note (1 connections)


**Dependencies**:

- Spec Mprog (105 connections)
- String Operator!= (89 connections)
- Obj Char (72 connections)
- Char Level (52 connections)
- Conn:: State (30 connections)
- Char Group (26 connections)
- Bit Core (23 connections)
- Descriptor Read (15 connections)
- Room Color (14 connections)
- Handle Input (11 connections)
- War Clan (10 connections)
- Guild Level (9 connections)
- Operator Flags (7 connections)
- Duel Arena (7 connections)
- Handle Wimpy (6 connections)
- Flags Act (5 connections)
- Garbage List (5 connections)
- Qtell Wizlist (4 connections)
- Flags Name (4 connections)
- Read Confirm (4 connections)
- Operator= Extra (3 connections)
- Help Disabled (3 connections)
- Types Constants (3 connections)
- Core variable (3 connections)
- Edit Note (3 connections)
- Social Departed (3 connections)
- Weather Day (2 connections)
- Flags T100 (2 connections)
- From Obj (2 connections)
- Afk Pwd (1 connections)
- Level Squestmob (1 connections)
- Name Description (1 connections)


**Dependencies**:

- Obj Char (429 connections)
- Spec Mprog (303 connections)
- Guild Level (277 connections)
- Conn:: State (263 connections)
- Char Group (194 connections)
- From Obj (179 connections)
- Room Color (172 connections)
- Bit Core (133 connections)
- Handle Input (100 connections)
- String Operator!= (96 connections)
- Flags Act (87 connections)
- Vnum Prototype (75 connections)
- Types Constants (58 connections)
- Handle Wimpy (46 connections)
- Descriptor Read (43 connections)
- Read Confirm (23 connections)
- Duel Arena (17 connections)
- Weather Day (14 connections)
- Name Description (13 connections)
- Act Dispatcher (13 connections)
- Level Squestmob (10 connections)
- Operator Flags (8 connections)
- Flags T100 (5 connections)
- War Clan (4 connections)
- Char Show (3 connections)
- Flags Name (3 connections)
- Video Color (3 connections)
- Recall Reject (2 connections)
- Core variable (2 connections)
- Race Name (1 connections)
- Help Disabled (1 connections)
- Table Color (1 connections)
- Color Custom (1 connections)


**Dependencies**:

- Vnum Prototype (9 connections)
- Act Dispatcher (8 connections)
- Obj Char (5 connections)
- Edit Note (3 connections)
- Help Disabled (3 connections)
- Conn:: State (2 connections)
- Level Squestmob (2 connections)
- String Operator!= (1 connections)
- Flags Act (1 connections)
- From Obj (1 connections)
- Char Level (1 connections)
- War Clan (1 connections)
- Operator Flags (1 connections)
- Spec Mprog (1 connections)
- Char Group (1 connections)
- Garbage List (1 connections)


**Dependencies**:

- Obj Char (85 connections)
- Char Level (61 connections)
- Spec Mprog (49 connections)
- Vnum Prototype (46 connections)
- Char Group (41 connections)
- Conn:: State (19 connections)
- Handle Input (17 connections)
- String Operator!= (16 connections)
- Guild Level (16 connections)
- Room Color (15 connections)
- Read Confirm (14 connections)
- Flags Act (14 connections)
- Bit Core (11 connections)
- Name Description (8 connections)
- Flags T100 (6 connections)
- Descriptor Read (6 connections)
- Handle Wimpy (5 connections)
- Garbage List (4 connections)
- Types Constants (3 connections)
- Char Show (2 connections)
- Weather Day (2 connections)
- Recall Reject (2 connections)
- Social Departed (2 connections)
- Act Dispatcher (2 connections)
- Video Color (2 connections)
- Core variable (2 connections)
- Operator Flags (1 connections)
- Flags Name (1 connections)
- Afk Pwd (1 connections)
- Duel Arena (1 connections)
- War Clan (1 connections)
- Color Custom (1 connections)


**Dependencies**:

- String Operator!= (81 connections)
- Conn:: State (37 connections)
- Bit Core (29 connections)
- Handle Input (29 connections)
- Handle Wimpy (24 connections)
- Room Color (24 connections)
- Descriptor Read (21 connections)
- Char Group (19 connections)
- Help Disabled (19 connections)
- Obj Char (17 connections)
- Vnum Prototype (17 connections)
- Read Confirm (15 connections)
- Spec Mprog (10 connections)
- Operator Flags (8 connections)
- Types Constants (8 connections)
- Guild Level (5 connections)
- Social Departed (4 connections)
- Qtell Wizlist (4 connections)
- Garbage List (4 connections)
- Color Custom (4 connections)
- Char Level (4 connections)
- Name Description (4 connections)
- Duel Arena (3 connections)
- Flags Act (2 connections)
- Video Color (2 connections)
- Flags Name (2 connections)
- Flags T100 (1 connections)
- From Obj (1 connections)
- Recall Reject (1 connections)


**Dependencies**:

- Types Constants (9 connections)
- Room Color (1 connections)



### Data Subsystems

#### Handle Input Group

**Dependencies**:

- Spec Mprog (28 connections)
- Vnum Prototype (21 connections)
- String Operator!= (18 connections)
- Conn:: State (12 connections)
- Obj Char (9 connections)
- Char Level (8 connections)
- War Clan (7 connections)
- Char Group (6 connections)
- Room Color (5 connections)
- Qtell Wizlist (5 connections)
- Handle Input (5 connections)
- Name Description (4 connections)
- Flags Act (3 connections)
- Read Confirm (3 connections)
- Guild Level (3 connections)
- Descriptor Read (2 connections)
- Bit Core (2 connections)
- Types Constants (2 connections)
- Flags T100 (2 connections)
- Handle Wimpy (2 connections)
- From Obj (1 connections)


**Dependencies**:

- String Operator!= (108 connections)
- Bit Core (26 connections)
- Conn:: State (17 connections)
- Descriptor Read (16 connections)
- Room Color (14 connections)
- Handle Input (13 connections)
- Operator Flags (10 connections)
- Obj Char (9 connections)
- Vnum Prototype (8 connections)
- Social Departed (7 connections)
- Char Group (6 connections)
- From Obj (5 connections)
- Name Description (5 connections)
- War Clan (4 connections)
- Spec Mprog (4 connections)
- Guild Level (4 connections)
- Garbage List (3 connections)
- Qtell Wizlist (3 connections)
- Char Level (3 connections)
- Handle Wimpy (2 connections)
- Read Confirm (1 connections)
- Duel Arena (1 connections)
- Array String (1 connections)
- Edit Note (1 connections)
- Level Squestmob (1 connections)
- Types Constants (1 connections)
- Flags Act (1 connections)
- Flags T100 (1 connections)


**Dependencies**:

- String Operator!= (293 connections)
- Conn:: State (270 connections)
- Room Color (190 connections)
- Read Confirm (148 connections)
- Bit Core (141 connections)
- Spec Mprog (125 connections)
- Descriptor Read (104 connections)
- Char Level (101 connections)
- Types Constants (100 connections)
- Obj Char (99 connections)
- Flags Act (94 connections)
- Handle Wimpy (70 connections)
- Char Group (70 connections)
- Flags T100 (67 connections)
- Name Description (65 connections)
- War Clan (58 connections)
- Garbage List (53 connections)
- Qtell Wizlist (43 connections)
- Color Custom (41 connections)
- Afk Pwd (38 connections)
- Help Disabled (31 connections)
- Vnum Prototype (27 connections)
- Video Color (26 connections)
- Recall Reject (19 connections)
- Edit Note (16 connections)
- Guild Level (14 connections)
- Social Departed (11 connections)
- Array String (9 connections)
- Level Squestmob (8 connections)
- Flags Name (8 connections)
- Autograph Newbiekit (7 connections)
- Operator Flags (6 connections)
- From Obj (6 connections)
- Weather Day (5 connections)
- Char Show (5 connections)
- Core variable (5 connections)
- Duel Arena (3 connections)
- Act Dispatcher (2 connections)
- Race Name (1 connections)


**Dependencies**:

- Obj Char (18 connections)
- From Obj (16 connections)
- Char Level (11 connections)
- String Operator!= (8 connections)
- Char Group (6 connections)
- Help Disabled (3 connections)
- Room Color (1 connections)


**Dependencies**:

- Bit Core (76 connections)
- From Obj (33 connections)
- Char Level (17 connections)
- Operator Flags (8 connections)
- String Operator!= (3 connections)
- Weather Day (1 connections)
- Char Group (1 connections)
- Spec Mprog (1 connections)


**Dependencies**:

- String Operator!= (12 connections)
- Char Group (7 connections)
- Conn:: State (3 connections)
- Help Disabled (1 connections)


#### Edit Note Group

**Dependencies**:

- String Operator!= (89 connections)
- Conn:: State (40 connections)
- Room Color (24 connections)
- Descriptor Read (19 connections)
- Bit Core (16 connections)
- Char Group (12 connections)
- Handle Input (11 connections)
- Help Disabled (11 connections)
- From Obj (8 connections)
- Obj Char (8 connections)
- Name Description (7 connections)
- Read Confirm (7 connections)
- Handle Wimpy (7 connections)
- War Clan (7 connections)
- Types Constants (6 connections)
- Flags Act (6 connections)
- Operator Flags (4 connections)
- Vnum Prototype (3 connections)
- Social Departed (2 connections)
- Level Squestmob (1 connections)
- Spec Mprog (1 connections)
- Flags T100 (1 connections)


**Dependencies**:

- Conn:: State (46 connections)
- String Operator!= (46 connections)
- Handle Input (28 connections)
- Room Color (27 connections)
- Garbage List (25 connections)
- Read Confirm (20 connections)
- Descriptor Read (18 connections)
- Types Constants (15 connections)
- Bit Core (14 connections)
- Flags Act (12 connections)
- Name Description (12 connections)
- Handle Wimpy (12 connections)
- Help Disabled (11 connections)
- Edit Note (10 connections)
- Spec Mprog (9 connections)
- Flags T100 (8 connections)
- Color Custom (8 connections)
- Char Group (6 connections)
- Char Level (6 connections)
- Video Color (5 connections)
- Social Departed (5 connections)
- Duel Arena (4 connections)
- Vnum Prototype (4 connections)
- Obj Char (4 connections)
- Level Squestmob (2 connections)
- Guild Level (2 connections)
- War Clan (2 connections)
- Act Dispatcher (1 connections)
- Operator Flags (1 connections)


**Dependencies**:

- Color Scan (41 connections)
- Bit Core (6 connections)
- Room Color (6 connections)
- String Operator!= (6 connections)
- Flags Act (2 connections)
- Descriptor Read (2 connections)
- Read Confirm (2 connections)
- Conn:: State (2 connections)
- Char Group (2 connections)
- Handle Input (1 connections)
- Flags T100 (1 connections)


**Dependencies**:

- Obj Char (43 connections)
- String Operator!= (40 connections)
- Char Level (38 connections)
- Char Group (31 connections)
- Spec Mprog (26 connections)
- Conn:: State (14 connections)
- Handle Input (14 connections)
- War Clan (13 connections)
- Room Color (10 connections)
- Duel Arena (9 connections)
- Descriptor Read (8 connections)
- Types Constants (8 connections)
- Qtell Wizlist (7 connections)
- Bit Core (6 connections)
- Color Custom (4 connections)
- Vnum Prototype (4 connections)
- From Obj (4 connections)
- Flags Act (4 connections)
- Read Confirm (3 connections)
- Guild Level (3 connections)
- Array String (3 connections)
- Recall Reject (2 connections)
- Operator Flags (2 connections)
- Help Disabled (2 connections)
- Weather Day (2 connections)
- Act Dispatcher (2 connections)
- Edit Note (2 connections)
- Level Squestmob (2 connections)
- Garbage List (2 connections)
- Name Description (1 connections)
- Flags Name (1 connections)
- Handle Wimpy (1 connections)
- Char Show (1 connections)
- Flags T100 (1 connections)
- Video Color (1 connections)


**Dependencies**:

- Room Color (20 connections)
- String Operator!= (15 connections)
- Video Color (13 connections)
- Color Scan (11 connections)
- Conn:: State (8 connections)
- Handle Input (7 connections)
- Read Confirm (6 connections)
- Bit Core (5 connections)
- Flags Act (4 connections)
- Descriptor Read (4 connections)
- Char Group (2 connections)
- Types Constants (1 connections)
- War Clan (1 connections)
- Flags T100 (1 connections)
- Obj Char (1 connections)
- Handle Wimpy (1 connections)
- From Obj (1 connections)
- Vnum Prototype (1 connections)


**Dependencies**:

- Bit Core (52 connections)
- Flags Act (12 connections)
- War Clan (6 connections)
- Types Constants (3 connections)
- Core variable (2 connections)
- Name Description (1 connections)
- Spec Mprog (1 connections)
- Level Squestmob (1 connections)
- Edit Note (1 connections)
- Video Color (1 connections)


#### Quality Keyword

No external dependencies.



### Interface Subsystems

#### Conn:: State Group

**Dependencies**:

- Handle Input (148 connections)
- Spec Mprog (62 connections)
- Obj Char (59 connections)
- Char Group (43 connections)
- Char Level (40 connections)
- String Operator!= (36 connections)
- Room Color (24 connections)
- Flags T100 (21 connections)
- Bit Core (21 connections)
- Read Confirm (20 connections)
- War Clan (20 connections)
- Qtell Wizlist (18 connections)
- Recall Reject (17 connections)
- Help Disabled (17 connections)
- Edit Note (12 connections)
- Descriptor Read (12 connections)
- Vnum Prototype (11 connections)
- Autograph Newbiekit (9 connections)
- Handle Wimpy (9 connections)
- Types Constants (7 connections)
- Garbage List (5 connections)
- Name Description (5 connections)
- Char Show (5 connections)
- Social Departed (5 connections)
- Weather Day (4 connections)
- Flags Name (4 connections)
- Level Squestmob (4 connections)
- Afk Pwd (2 connections)
- Core variable (2 connections)
- Color Custom (1 connections)
- Duel Arena (1 connections)
- Guild Level (1 connections)
- Flags Act (1 connections)
- Act Dispatcher (1 connections)
- From Obj (1 connections)
- Operator Flags (1 connections)


**Dependencies**:

- Char Level (19 connections)
- Char Group (16 connections)
- Conn:: State (16 connections)
- String Operator!= (14 connections)
- Room Color (12 connections)
- Obj Char (10 connections)
- Handle Input (10 connections)
- Bit Core (8 connections)
- Spec Mprog (8 connections)
- Read Confirm (8 connections)
- Name Description (7 connections)
- Video Color (6 connections)
- Types Constants (5 connections)
- Color Custom (5 connections)
- Descriptor Read (5 connections)
- Flags Act (4 connections)
- Handle Wimpy (4 connections)
- Guild Level (4 connections)
- War Clan (3 connections)
- Core variable (2 connections)
- Garbage List (2 connections)
- Afk Pwd (1 connections)
- Weather Day (1 connections)
- Flags T100 (1 connections)
- Level Squestmob (1 connections)
- Autograph Newbiekit (1 connections)
- Help Disabled (1 connections)


**Dependencies**:

- Qtell Wizlist (15 connections)
- Spec Mprog (5 connections)
- Conn:: State (4 connections)
- Char Group (2 connections)
- Weather Day (2 connections)
- Handle Input (1 connections)
- Char Level (1 connections)
- Bit Core (1 connections)
- Color Scan (1 connections)


**Dependencies**:

- Conn:: State (34 connections)
- String Operator!= (32 connections)
- Obj Char (29 connections)
- Descriptor Read (22 connections)
- Read Confirm (21 connections)
- Room Color (20 connections)
- Char Group (19 connections)
- Char Level (18 connections)
- Spec Mprog (17 connections)
- Handle Input (16 connections)
- Guild Level (12 connections)
- Bit Core (11 connections)
- Flags Act (10 connections)
- Array String (10 connections)
- Types Constants (10 connections)
- Name Description (9 connections)
- Help Disabled (9 connections)
- Flags T100 (8 connections)
- Garbage List (7 connections)
- Vnum Prototype (6 connections)
- Level Squestmob (6 connections)
- Color Custom (4 connections)
- Afk Pwd (4 connections)
- War Clan (3 connections)
- Weather Day (3 connections)
- Video Color (3 connections)
- Autograph Newbiekit (3 connections)
- Edit Note (2 connections)
- Recall Reject (1 connections)
- Char Show (1 connections)
- Name Loot (1 connections)
- Core variable (1 connections)
- Duel Arena (1 connections)
- Social Departed (1 connections)
- Qtell Wizlist (1 connections)


**Dependencies**:

- String Operator!= (40 connections)
- Char Group (24 connections)
- Race Name (6 connections)
- Conn:: State (5 connections)
- Bit Core (4 connections)
- From Obj (3 connections)


**Dependencies**:

- String Operator!= (37 connections)
- Conn:: State (19 connections)
- Read Confirm (7 connections)
- Room Color (7 connections)
- Handle Input (6 connections)
- Name Description (5 connections)
- Types Constants (4 connections)
- Char Group (4 connections)
- Guild Level (3 connections)
- Afk Pwd (2 connections)
- Spec Mprog (2 connections)
- Social Departed (2 connections)
- Video Color (2 connections)
- Core variable (2 connections)
- War Clan (1 connections)
- Obj Char (1 connections)
- Color Custom (1 connections)
- Bit Core (1 connections)
- Flags T100 (1 connections)
- Help Disabled (1 connections)
- Flags Act (1 connections)
- Act Dispatcher (1 connections)
- Operator Flags (1 connections)
- Flags Name (1 connections)
- Autograph Newbiekit (1 connections)
- Edit Note (1 connections)


**Dependencies**:

- Obj Char (11 connections)
- Conn:: State (6 connections)
- String Operator!= (6 connections)
- Room Color (3 connections)
- Char Level (3 connections)
- Descriptor Read (2 connections)
- Bit Core (1 connections)
- Flags Act (1 connections)
- Handle Input (1 connections)
- Handle Wimpy (1 connections)
- Flags T100 (1 connections)
- Garbage List (1 connections)


**Dependencies**:

- Spec Mprog (66 connections)
- Conn:: State (50 connections)
- Obj Char (48 connections)
- Char Level (47 connections)
- Room Color (35 connections)
- String Operator!= (35 connections)
- Handle Input (29 connections)
- Read Confirm (20 connections)
- Bit Core (19 connections)
- Descriptor Read (19 connections)
- Char Group (18 connections)
- Vnum Prototype (17 connections)
- Name Description (16 connections)
- Flags Act (13 connections)
- Flags T100 (13 connections)
- Garbage List (12 connections)
- Handle Wimpy (12 connections)
- Guild Level (11 connections)
- Types Constants (7 connections)
- War Clan (6 connections)
- Afk Pwd (6 connections)
- Video Color (6 connections)
- Color Custom (5 connections)
- Level Squestmob (3 connections)
- Duel Arena (2 connections)
- Edit Note (2 connections)
- Help Disabled (2 connections)
- Char Show (1 connections)
- Weather Day (1 connections)
- Act Dispatcher (1 connections)
- Autograph Newbiekit (1 connections)
- Social Departed (1 connections)


**Dependencies**:

- Bit Core (76 connections)
- Conn:: State (63 connections)
- String Operator!= (51 connections)
- Color Custom (49 connections)
- Video Color (39 connections)
- War Clan (25 connections)
- Flags Act (22 connections)
- Handle Input (21 connections)
- Read Confirm (20 connections)
- Flags T100 (19 connections)
- Spec Mprog (17 connections)
- Descriptor Read (15 connections)
- Char Level (13 connections)
- Obj Char (11 connections)
- Char Group (11 connections)
- Types Constants (10 connections)
- Handle Wimpy (10 connections)
- Garbage List (9 connections)
- Name Description (9 connections)
- Vnum Prototype (8 connections)
- Guild Level (8 connections)
- Color Scan (4 connections)
- Help Disabled (4 connections)
- Qtell Wizlist (4 connections)
- Afk Pwd (3 connections)
- Autograph Newbiekit (2 connections)
- Operator Flags (2 connections)
- From Obj (1 connections)
- Recall Reject (1 connections)
- Level Squestmob (1 connections)
- Weather Day (1 connections)
- Race Name (1 connections)
- Flags Name (1 connections)



### Support Subsystems

#### Act Dispatcher

**Dependencies**:

- From Obj (25 connections)
- String Operator!= (18 connections)
- Conn:: State (17 connections)
- Char Level (15 connections)
- Spec Mprog (15 connections)
- Obj Char (5 connections)
- Vnum Prototype (2 connections)
- Char Group (2 connections)
- Types Constants (1 connections)

