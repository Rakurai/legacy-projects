DIAGNOSTIC — locked functions vs group descriptions
Groups: 30  Total locked: 851  Overall mean sim: 0.518
Sorted by group mean similarity (ascending — weakest groups first)
================================================================================
[domain] world_structure  (stability: likely_split)
  desc: World structure and spatial data: area metadata and retrieval, area player and immortal counting, room properties (secto…
  locked: 37 functions, 37 with embeddings
  sim to desc — mean: 0.388  min: 0.265  max: 0.530

  0.530  generate_skillquest_room                 — Selects and returns a suitable room for a skill quest based on specifi
    /**
     * @fn Room * generate_skillquest_room(Character *ch, int level)
     *
     * @brief Selects and returns a suitable room for a skill quest based on specified level constraints.
     *
     * @details This function iterates through all rooms in the game world to find a room that meets specific criteria suitable for a skill quest at the given level. It performs up to two passes: the first to count eligible rooms, and the second to randomly select one based on a previously chosen index. Criteria exclude rooms in certain areas, with specific flags, or associated with certain guilds or names. It also avoids pet shops and restricted areas. If no suitable room is found, it returns nullptr.
     *
     * @param ch Pointer to the Character attempting to find a skill quest room; used to check visibility and access permissions.
     * @param level Integer representing the desired level range for the quest room; used to filter rooms based on their area's level range.
     * @return A pointer to the selected Room object suitable for the skill quest, or nullptr if no appropriate room is found.
     */

  0.506  World::get_area                          — Retrieves the area associated with a given virtual number (vnum).
    /**
     * @fn Area * World::get_area(const Vnum &) const
     *
     * @brief Retrieves the area associated with a given virtual number (vnum).
     *
     * @details This function searches for an area within the World object that contains the specified virtual number (vnum). It attempts to find the area by looking up a range that matches the given vnum. If an area is found, it returns a pointer to it; otherwise, it returns nullptr. The function assumes that the number of areas is relatively small, so it uses a simple lookup instead of a more efficient search algorithm.
     *
     * @param vnum The virtual number (vnum) used to identify and locate the corresponding area.
     * @return A pointer to the Area object that contains the specified vnum, or nullptr if no such area exists.
     */

  0.497  World::get_room                          — Retrieves a Room object based on a given Location.
    /**
     * @fn Room * World::get_room(const Location &)
     *
     * @brief Retrieves a Room object based on a given Location.
     *
     * @details This function attempts to find and return a Room object that corresponds to the provided Location. It first checks if the Location's coordinate is valid and uses it to retrieve the Room from a quadtree structure. If the coordinate is invalid, it checks the validity of the room identifier and searches through available areas to find the Room. If neither method succeeds, it returns nullptr.
     *
     * @param location The Location object containing either a coordinate or a room identifier to locate the Room.
     * @return A pointer to the Room object associated with the given Location, or nullptr if no such Room exists.
     */

  0.474  Room::sector_type                        — Retrieves the sector type of the room.
    /**
     * @fn Sector Room::sector_type() const
     *
     * @brief Retrieves the sector type of the room.
     *
     * @details This function returns the sector type of the room by accessing the sector type from the room's prototype. It provides information about the category or classification of the room based on predefined sector types.
     *
     * @return The sector type of the room, represented as a value from the Sector enumeration.
     */

  0.474  Area::get_mob_prototype                  — Retrieves a mobile prototype by its virtual number.
    /**
     * @fn MobilePrototype * Area::get_mob_prototype(const Vnum &)
     *
     * @brief Retrieves a mobile prototype by its virtual number.
     *
     * @details This function searches for a mobile prototype within the 'mob_prototypes' collection using the provided virtual number (vnum). If a prototype with the specified vnum exists, it returns a pointer to the MobilePrototype. If no such prototype is found, it returns a null pointer.
     *
     * @param vnum The virtual number of the mobile prototype to be retrieved.
     * @return A pointer to the MobilePrototype associated with the given vnum, or nullptr if no such prototype exists.
     */

  0.462  World::get_mob_prototype                 — Retrieves a mobile prototype by its virtual number.
    /**
     * @fn MobilePrototype * World::get_mob_prototype(const Vnum &)
     *
     * @brief Retrieves a mobile prototype by its virtual number.
     *
     * @details This function attempts to find and return a MobilePrototype object associated with the given virtual number (vnum). It first retrieves the Area object that contains the specified vnum using the get_area function. If the area is found, it then attempts to retrieve the MobilePrototype from that area. If no prototype is found and the game is in the booting phase, a bug report is logged. The function returns a pointer to the MobilePrototype if found, or nullptr if no such prototype exists.
     *
     * @param vnum The virtual number used to identify and locate the mobile prototype.
     * @return A pointer to the MobilePrototype associated with the given vnum, or nullptr if no such prototype exists.
     */

  0.460  Room::area                               — Retrieves the area associated with the room.
    /**
     * @fn Area & Room::area() const
     *
     * @brief Retrieves the area associated with the room.
     *
     * @details This function returns a reference to the Area object associated with the Room instance. It accesses the area member of the prototype object, which is assumed to be a part of the Room's internal data structure. This function is a const member function, indicating that it does not modify the state of the Room object.
     *
     * @return A reference to the Area object associated with the Room.
     */

  0.460  worldmap::Worldmap::get_sector           — Retrieves the sector type at a given coordinate.
    /**
     * @fn const Sector worldmap::Worldmap::get_sector(const Coordinate &coord) const
     *
     * @brief Retrieves the sector type at a given coordinate.
     *
     * @details This function checks if the provided Coordinate object is valid and within the bounds of the Worldmap's dimensions. If the coordinate is valid and within bounds, it retrieves the sector type from the internal map representation at the specified coordinate. The sector type is returned as an enumeration value of type Sector.
     *
     * @param coord A constant reference to a Coordinate object representing the 2D position on the Worldmap.
     * @return The sector type at the specified coordinate, represented as a value of the Sector enumeration. If the coordinate is invalid or out of bounds, it returns a default sector type corresponding to the value 0.
     */

  0.448  Area::add_char                           — Adds a character to the area, updating counts for players and immortal
    /**
     * @fn void Area::add_char(Character *ch)
     *
     * @brief Adds a character to the area, updating counts for players and immortals.
     *
     * @details This function processes a Character object to determine if it should be added to the area. If the character is an NPC (i.e., 'is_npc' returns true), the function exits without making changes. For player characters, it increments the appropriate counter: '_num_imms' if the character is an immortal, or '_num_players' otherwise. This function does not return a value but modifies internal state counters based on the character's attributes.
     *
     * @param ch Pointer to the Character object to be added to the area.
     * @return None. The function updates internal counters for the number of players and immortals in the area.
     */

  0.441  Room::mana_rate                          — Retrieves the mana regeneration rate of the room.
    /**
     * @fn int Room::mana_rate() const
     *
     * @brief Retrieves the mana regeneration rate of the room.
     *
     * @details This function returns the mana regeneration rate associated with the room by accessing the 'mana_rate' member of the 'prototype' object. It is a constant member function, indicating that it does not modify the state of the Room object.
     *
     * @return An integer representing the mana regeneration rate of the room.
     */

  0.436  Room::heal_rate                          — Retrieves the healing rate of the room.
    /**
     * @fn int Room::heal_rate() const
     *
     * @brief Retrieves the healing rate of the room.
     *
     * @details This function returns the healing rate associated with the room by accessing the heal_rate property of the room's prototype. It is a constant member function, indicating that it does not modify the state of the Room object.
     *
     * @return The healing rate of the room, as an integer, which is derived from the room's prototype.
     */

  0.429  Room::guild                              — Retrieves the guild value from the room's prototype.
    /**
     * @fn int Room::guild() const
     *
     * @brief Retrieves the guild value from the room's prototype.
     *
     * @details This function returns the guild value associated with the room's prototype. It provides a way to access the guild information stored within the prototype object of the Room class. The function does not modify any member variables and can be called on a constant Room object.
     *
     * @return The guild value from the room's prototype, represented as an integer.
     */

  0.421  QuestArea::area                          — Retrieves the area associated with the QuestArea.
    /**
     * @fn const Area & QuestArea::area() const
     *
     * @brief Retrieves the area associated with the QuestArea.
     *
     * @details This function returns a constant reference to the Area object associated with the QuestArea. It accesses the startroom member, which is expected to be a pointer to a Room object, and calls its area() method to obtain the Area reference. This function is const, indicating that it does not modify the state of the QuestArea object.
     *
     * @return A constant reference to the Area object associated with the QuestArea.
     */

  0.401  Area::num_players                        — Returns the number of players.
    /**
     * @fn int Area::num_players() const
     *
     * @brief Returns the number of players.
     *
     * @details This function retrieves the current number of players in the context where it is called. It is a constant member function, indicating that it does not modify any member variables of the class.
     *
     * @return The number of players as an integer.
     */

  0.399  create_mobile                            — Creates and initializes a mobile character instance from a given proto
    /**
     * @fn Character * create_mobile(MobilePrototype *pMobIndex)
     *
     * @brief Creates and initializes a mobile character instance from a given prototype.
     *
     * @details Creates and initializes a new mobile character instance based on a given prototype.
    This function constructs a new Character object based on the provided MobilePrototype. It initializes various attributes of the character, such as name, description, wealth, and combat statistics, using data from the prototype. The function also applies racial and class-based modifiers to the character's attributes and sets up initial stamina, hit points, and mana. Finally, the character is added to the game world and the prototype's count is incremented.
     *
     * @param pMobIndex Pointer to the MobilePrototype object containing the template data for the mobile character.
     * @return A pointer to the newly created Character object representing the mobile, or nullptr if creation failed.
     */

  0.398  Game::world                              — Provides access to the singleton instance of the World object.
    /**
     * @fn World & Game::world()
     *
     * @brief Provides access to the singleton instance of the World object.
     *
     * @details This function returns a reference to a static instance of the World class, ensuring that only one instance of World exists throughout the application's lifecycle. It is used to access the global game world state managed by the Game class.
     *
     * @return A reference to the singleton instance of the World object.
     */

  0.395  clone_mobile                             — Clones a non-player character (NPC) mobile, excluding its inventory.
    /**
     * @fn void clone_mobile(Character *parent, Character *clone)
     *
     * @brief Clones a non-player character (NPC) mobile, excluding its inventory.
     *
     * @details Clones the attributes and affects of a parent NPC character to a clone character.
    This function duplicates the attributes of a parent NPC character to a clone character, effectively creating a copy of the parent NPC. The function does not copy the inventory of the parent. It initializes various attributes of the clone with the corresponding values from the parent, such as name, descriptions, attributes, and other character-specific properties. All affects are removed from the clone before copying the affects from the parent. The function only operates if both the parent and clone pointers are valid and the parent is an NPC.
     *
     * @param parent A pointer to the Character object that serves as the template for cloning. Must be a non-player character (NPC).
     * @param clone A pointer to the Character object that will receive the cloned attributes and affects from the parent.
     * @return This function does not return a value.
     */

  0.388  RoomID::get_vnum                         — Retrieves the virtual number (vnum) of the RoomID.
    /**
     * @fn const Vnum RoomID::get_vnum() const
     *
     * @brief Retrieves the virtual number (vnum) of the RoomID.
     *
     * @details This function returns the virtual number associated with the RoomID object. It first checks if the RoomID is valid using the is_valid() method. If the RoomID is not valid, it returns a default Vnum initialized to zero. If the RoomID is valid, it returns a Vnum constructed with the vnum_data of the RoomID.
     *
     * @return A Vnum object representing the virtual number of the RoomID. If the RoomID is not valid, a Vnum initialized to zero is returned.
     */

  0.373  RoomID::to_int                           — Serializes the RoomID into an integer representation.
    /**
     * @fn int RoomID::to_int() const
     *
     * @brief Serializes the RoomID into an integer representation.
     *
     * @details This function converts the RoomID into an integer by encoding its components into specific bit positions. The leftmost bit indicates the validity of the RoomID, determined by the is_valid() method. If the RoomID is not valid, the function returns -1. Otherwise, it shifts the number_data by the number of bits specified by num_bits_vnum() and combines it with vnum_data using a bitwise OR operation. The resulting integer encodes the RoomID's validity, number, and virtual number.
     *
     * @return An integer representing the serialized RoomID. If the RoomID is invalid, returns -1. Otherwise, returns an integer with the leftmost bit indicating validity, followed by the number and virtual number encoded in the remaining bits.
     */

  0.369  Room::name                               — Retrieves the name of the room.
    /**
     * @fn const String & Room::name() const
     *
     * @brief Retrieves the name of the room.
     *
     * @details This function returns a constant reference to the name of the room, which is stored in the prototype object. It provides access to the room's name without allowing modification.
     *
     * @return A constant reference to a String object representing the room's name.
     */

  0.364  sector_lookup                            — Retrieves the name of a sector based on its type.
    /**
     * @fn String sector_lookup(Sector type)
     *
     * @brief Retrieves the name of a sector based on its type.
     *
     * @details This function searches through a predefined table of sectors to find a matching sector type. If a match is found, it returns the corresponding sector name. If no match is found, it returns the string 'unknown'. The function is case-insensitive and relies on a global or externally defined 'sector_table' that maps sector types to their names.
     *
     * @param type The sector type to look up in the sector table.
     * @return The name of the sector corresponding to the given type, or 'unknown' if the type is not found in the sector table.
     */

  0.360  Room::owner                              — Retrieves the owner of the room.
    /**
     * @fn const String & Room::owner() const
     *
     * @brief Retrieves the owner of the room.
     *
     * @details This function returns a reference to the owner of the room, which is stored in the prototype object. It provides access to the owner's information without modifying it.
     *
     * @return A constant reference to a String object representing the owner of the room.
     */

  0.360  Room::is_on_map                          — Determines if the room is located on a valid map coordinate.
    /**
     * @fn bool Room::is_on_map() const
     *
     * @brief Determines if the room is located on a valid map coordinate.
     *
     * @details This function checks whether the room's location is on a valid map coordinate by invoking the is_valid method of the Coordinate object associated with the room's location. It returns true if the coordinate is valid, indicating that the room is on the map, and false otherwise.
     *
     * @return A boolean value indicating whether the room is on a valid map coordinate. Returns true if the coordinate is valid, false otherwise.
     */

  0.359  worldmap::Worldmap::width                — Retrieves the width value.
    /**
     * @fn unsigned int worldmap::Worldmap::width() const
     *
     * @brief Retrieves the width value.
     *
     * @details This function returns the current width value stored in the object. It is a constant member function, indicating that it does not modify the state of the object.
     *
     * @return The width value as an unsigned integer.
     */

  0.356  worldmap::Worldmap::height               — Retrieves the height value.
    /**
     * @fn unsigned int worldmap::Worldmap::height() const
     *
     * @brief Retrieves the height value.
     *
     * @details This function returns the current height stored in the object. It is a constant member function, indicating that it does not modify the state of the object.
     *
     * @return The height as an unsigned integer, representing the current height value of the object.
     */

  0.352  Location::is_valid                       — Checks if either the coordinate or the room ID is valid.
    /**
     * @fn bool Location::is_valid() const
     *
     * @brief Checks if either the coordinate or the room ID is valid.
     *
     * @details This function determines the validity of an object by checking if either the 'coord' or 'room_id' member is in a valid state. It calls the 'is_valid' method on both 'coord' and 'room_id'. The function returns true if at least one of these components is valid, meaning 'coord' has a non-negative 'x' value or 'room_id' has a non-negative 'number_data'. This is useful for ensuring that the object is in a usable state before performing operations that depend on valid coordinates or room identifiers.
     *
     * @return A boolean value indicating the validity of the object. Returns true if either 'coord' or 'room_id' is valid, false otherwise.
     */

  0.347  Location::to_int                         — Serializes the object into an integer representation.
    /**
     * @fn int Location::to_int() const
     *
     * @brief Serializes the object into an integer representation.
     *
     * @details This function attempts to serialize the object into an integer representation by first checking if the 'coord' (coordinate) is valid. If 'coord' is valid, it returns the integer representation of 'coord' using 'coord.to_int()'. If 'coord' is not valid, it returns the integer representation of 'room_id' using 'room_id.to_int()'. This function is useful for storing the object in various data structures or for serialization purposes.
     *
     * @return An integer representation of the object. If 'coord' is valid, it returns the integer representation of 'coord'. Otherwise, it returns the integer representation of 'room_id'.
     */

  0.344  RoomID::is_valid                         — Checks if the RoomID has been initialized correctly.
    /**
     * @fn bool RoomID::is_valid() const
     *
     * @brief Checks if the RoomID has been initialized correctly.
     *
     * @details This function determines whether the RoomID is valid by checking if the internal number_data is non-negative. It returns true if number_data is zero or positive, indicating a valid RoomID, and false if it is negative, indicating an uninitialized or invalid RoomID.
     *
     * @return A boolean value: true if the RoomID is valid (number_data is non-negative), false otherwise.
     */

  0.340  >::get                                   — Retrieves the data associated with a given coordinate in the quadtree.
    /**
     * @fn T * worldmap::Quadtree< T >::get(const Coordinate &coord) const
     *
     * @brief Retrieves the data associated with a given coordinate in the quadtree.
     *
     * @details This function attempts to retrieve the data stored at a specific 2D coordinate within the quadtree. If the quadtree's capacity is 1, it directly returns the stored data. Otherwise, it calculates the appropriate child index for the given coordinate using the get_child_index function. If the corresponding child node exists, it recursively calls get on the child node with the coordinate adjusted to the child's local space. If the child node does not exist, it returns nullptr.
     *
     * @param coord The Coordinate object representing the 2D point for which data is to be retrieved.
     * @return A pointer to the data of type T associated with the given coordinate, or nullptr if no data exists at that coordinate.
     */

  0.338  RoomID::get_number                       — Retrieves the room number associated with the RoomID.
    /**
     * @fn const int RoomID::get_number() const
     *
     * @brief Retrieves the room number associated with the RoomID.
     *
     * @details This function returns the room number if the RoomID is valid. It first checks the validity of the RoomID using the is_valid() method. If the RoomID is not valid, it returns 0. If valid, it performs a bitwise operation on number_data to ensure the correct room number is returned, incremented by 1.
     *
     * @return An integer representing the room number if the RoomID is valid, or 0 if the RoomID is invalid.
     */

  0.326  worldmap::Coordinate::is_valid           — Checks if the object is in a valid state.
    /**
     * @fn bool worldmap::Coordinate::is_valid() const
     *
     * @brief Checks if the object is in a valid state.
     *
     * @details This function determines whether the object is considered valid by checking if the member variable 'x' is non-negative. It returns true if 'x' is zero or positive, indicating a valid state, and false if 'x' is negative, indicating an invalid state.
     *
     * @return A boolean value indicating the validity of the object. Returns true if 'x' is non-negative, false otherwise.
     */

  0.310  GameTime::month_name                     — Retrieves the name of the current month in the game's calendar.
    /**
     * @fn const String & GameTime::month_name() const
     *
     * @brief Retrieves the name of the current month in the game's calendar.
     *
     * @details This function returns a reference to a String object representing the name of the current month in the game's custom calendar system. The month names are predefined and stored in a static array. The function uses the current month index to access the corresponding month name.
     *
     * @return A reference to a String containing the name of the current month.
     */

  0.309  worldmap::Coordinate::to_int             — Serializes the coordinate to an integer representation.
    /**
     * @fn int worldmap::Coordinate::to_int() const
     *
     * @brief Serializes the coordinate to an integer representation.
     *
     * @details This function converts the coordinate object into an integer format. The integer is structured such that the leftmost bit indicates the validity of the coordinate, followed by a bit that is always set to 1. The next 15 bits represent the x-coordinate, and the last 15 bits represent the y-coordinate. If the coordinate is not valid, the function returns -1.
     *
     * @return An integer representation of the coordinate, or -1 if the coordinate is invalid.
     */

  0.295  GameTime::day_name                       — Retrieves the name of the current day in the game.
    /**
     * @fn const String & GameTime::day_name() const
     *
     * @brief Retrieves the name of the current day in the game.
     *
     * @details This function returns the name of the current day based on an internal day index. The days are represented by a fixed array of strings, each corresponding to a specific day name in the game's week cycle. The function uses the modulo operation to ensure the day index wraps around within the range of available day names.
     *
     * @return A reference to a String object representing the name of the current day in the game's week cycle.
     */

  0.294  >::get_child_index                       — Calculates the child index for a given coordinate.
    /**
     * @fn unsigned int worldmap::Quadtree< T >::get_child_index(const Coordinate &coord) const
     *
     * @brief Calculates the child index for a given coordinate.
     *
     * @details This function determines the child index of a given coordinate within a quadtree node. The coordinate is divided by the node's capacity to determine its position relative to the node's center. The x and y components are used to compute the index, which indicates the quadrant of the node that contains the coordinate.
     *
     * @param coord The Coordinate object representing the 2D point for which the child index is calculated.
     * @return An unsigned integer representing the child index, where 0 corresponds to the northwest quadrant, 1 to the northeast, 2 to the southwest, and 3 to the southeast.
     */

  0.275  Exit::key                                — Retrieves the key associated with the Exit object.
    /**
     * @fn int Exit::key() const
     *
     * @brief Retrieves the key associated with the Exit object.
     *
     * @details This function returns the key value stored within the Exit object. It accesses the 'prototype' member of the Exit class and returns its 'key' attribute. This function is a constant member function, indicating that it does not modify the state of the Exit object.
     *
     * @return An integer representing the key associated with the Exit object.
     */

  0.265  Vnum::value                              — Retrieves the current value stored in the object.
    /**
     * @fn int Vnum::value() const
     *
     * @brief Retrieves the current value stored in the object.
     *
     * @details This function returns the value of the private member variable '_value'. It is a constant member function, meaning it does not modify any member variables of the object. The function provides read-only access to the '_value' member, allowing users to obtain the current state of this value.
     *
     * @return The current integer value stored in the '_value' member variable.
     */


================================================================================
[infrastructure] persistence  (stability: stable)
  desc: Data serialisation, storage, and retrieval: character save/load to JSON files, pet serialisation, object state persisten…
  locked: 94 functions, 87 with embeddings
  sim to desc — mean: 0.413  min: 0.273  max: 0.681
  ⚠ missing from pool: cJSON_Array, cJSON_False, cJSON_NULL, cJSON_Number, cJSON_Object, cJSON_String, cJSON_True

  0.681  save_char_obj                            — Serializes a Character object and its inventory into a JSON file for p
    /**
     * @fn void save_char_obj(Character *ch)
     *
     * @brief Serializes a Character object and its inventory into a JSON file for persistent storage.
     *
     * @details Serializes a Character object and its related data into a JSON file for persistent storage.
    This function saves the state of a given Character object, including its inventory, locker, strongbox, and pet data if present, into a JSON file within the designated player directory. It first checks if the character is valid and not an NPC, then handles cases where the character is possessed or controlled by a descriptor. The function creates a JSON object, populates it with version info and serialized character data, inventory, locker, strongbox, and pet information, then writes this JSON to a temporary file before renaming it to the character's save file. It also updates the player character index in the database after saving. Error handling includes logging and perror calls if file operations fail.
     *
     * @param ch Pointer to the Character object to be saved. The function serializes this character's data and related objects into a JSON file.
     * @return This function has no return value; it performs file I/O and database update operations as side effects.
     */

  0.652  fwrite_player                            — Serializes a Character object into a cJSON object representing the pla
    /**
     * @fn cJSON * fwrite_player(Character *ch)
     *
     * @brief Serializes a Character object into a cJSON object representing the player's data.
     *
     * @details The function fwrite_player takes a Character object and serializes its player-specific data into a cJSON object. This includes various attributes and properties such as aliases, conditions, colors, skills, and more. The function iterates over the character's data, converting it into JSON format using cJSON functions and custom JSON utility functions. The resulting JSON object can be used for saving or transmitting the player's data in a structured format.
     *
     * @param ch A pointer to the Character object whose data is to be serialized.
     * @return A pointer to a cJSON object containing the serialized player data. This object represents the player's attributes and properties in JSON format.
     */

  0.641  fwrite_pet                               — Serializes a Character object representing a pet into a JSON object.
    /**
     * @fn cJSON * fwrite_pet(Character *pet)
     *
     * @brief Serializes a Character object representing a pet into a JSON object.
     *
     * @details This function creates a JSON representation of a pet Character by first serializing common character attributes using fwrite_char. It then adds specific pet-related attributes such as Vnum, Save, Hit, and Dam to the JSON object if their current values differ from default or base values. The resulting JSON object can be used for saving or transmitting pet data in a structured format.
     *
     * @param pet Pointer to the Character object representing the pet to be serialized.
     * @return A pointer to a cJSON object containing the serialized pet data, including attributes, effects, and status flags.
     */

  0.627  load_char_obj                            — Loads a character and their inventory from a JSON file into a new char
    /**
     * @fn bool load_char_obj(Descriptor *d, const String &name)
     *
     * @brief Loads a character and their inventory from a JSON file into a new character structure.
     *
     * @details Loads a character object from a saved JSON file, initializing its attributes, inventory, and related data.
    This function initializes a new Character object with default attributes and loads character data, inventory, locker, strongbox, and pet information from a JSON file corresponding to the given character name. It reads the JSON data, applies version-specific fixes, and sets up the character's race, skills, group memberships, and other attributes. If the character's room is not specified, it assigns a default room. It also handles racial effects, remort effects, and restores character conditions based on last logoff time. The function returns true if the character data was successfully loaded, false otherwise.
     *
     * @param d Pointer to the Descriptor object representing the network connection associated with the character.
     * @param name The String containing the character's name used to locate and load the saved data.
     * @return A boolean indicating whether the character data was successfully loaded and initialized (true) or not (false).
     */

  0.623  objstate_save_items                      — Saves all objects lying on the ground to disk.
    /**
     * @fn int objstate_save_items()
     *
     * @brief Saves all objects lying on the ground to disk.
     *
     * @details Saves the current state of game objects to a JSON file.
    This function iterates through the list of objects in the game world and saves those that are deemed worth saving to a JSON file on disk. It creates a JSON representation of the objects, writes this data to a temporary file, and then renames the file to a permanent location. This function is called occasionally from update_handler and selectively from some parts of get_obj and drop_obj.
     *
     * @return Returns 0 upon completion, indicating the function executed without errors.
     */

  0.618  fwrite_char                              — Generates a JSON representation of a Character object, including attri
    /**
     * @fn cJSON * fwrite_char(Character *ch)
     *
     * @brief Generates a JSON representation of a Character object, including attributes, affects, and various status flags.
     *
     * @details This function serializes the provided Character object into a cJSON structure, capturing its flags, attributes, affects, status, and other relevant data. It creates nested JSON objects and arrays to represent complex data such as affects and attributes, and conditionally includes fields based on the character's properties (e.g., clan, description, bank gold). The resulting JSON object can be used for saving character state, debugging, or network transmission. It handles various character properties, including position, experience, equipment, and flags, ensuring a comprehensive snapshot of the character's current state.
     *
     * @param ch Pointer to the Character object to be serialized into JSON.
     * @return A pointer to a cJSON object representing the serialized character data.
     */

  0.605  fread_objects                            — Reads a list of objects from a JSON structure and associates them with
    /**
     * @fn void fread_objects(Character *ch, cJSON *json, void(*obj_to)(Object *, Character *), int version)
     *
     * @brief Reads a list of objects from a JSON structure and associates them with a character.
     *
     * @details This function processes a JSON list of game objects, creating and initializing each object using the fread_obj function. It then associates each object with a character using the provided obj_to function pointer. If an object's prototype cannot be found, its contents are processed and the object is removed from the game world.
     *
     * @param ch A pointer to the Character with which the objects will be associated.
     * @param contains A pointer to the cJSON object that represents the list of objects to be read.
     * @param obj_to A function pointer used to associate each initialized Object with the Character.
     * @param version An integer representing the version of the object format, influencing how fields are processed.
     * @return This function does not return a value.
     */

  0.604  fwrite_obj                               — Serializes a game object and its contents into a JSON object.
    /**
     * @fn cJSON * fwrite_obj(Object *obj)
     *
     * @brief Serializes a game object and its contents into a JSON object.
     *
     * @details Serializes a game object into a JSON representation.
    The function fwrite_obj takes a game object represented by the Object structure and serializes its attributes and contents into a JSON object using the cJSON library. It compares the current state of the object's attributes with their default values from the object's index data and only includes those attributes in the JSON object that differ from their defaults. Additionally, it checks if the object is enchanted and includes its affect list if applicable. Extra descriptions, flags, and other relevant attributes are also serialized. The function handles nested objects by recursively serializing contained objects and gems.
     *
     * @param obj A pointer to the Object structure to be serialized into a JSON object.
     * @return A pointer to a cJSON object representing the serialized state of the input game object, or NULL if memory allocation fails.
     */

  0.603  fread_player                             — Parses a JSON object to populate a Character's data fields during play
    /**
     * @fn void fread_player(Character *ch, cJSON *json, int version)
     *
     * @brief Parses a JSON object to populate a Character's data fields during player loading.
     *
     * @details This function reads a cJSON structure representing a player's saved data and updates the corresponding fields in the Character object. It handles various categories of data such as aliases, conditions, skills, group memberships, and other player-specific attributes. The function iterates through each key-value pair in the JSON, matches keys to known data fields, and assigns values accordingly, performing necessary conversions and lookups. It also manages version-dependent data and logs warnings for unknown keys. The function does not return a value but modifies the Character object directly to reflect the loaded data.
     *
     * @param ch Pointer to the Character object to be populated with data from JSON.
     * @param json Pointer to the cJSON object containing the player's saved data.
     * @param version Integer representing the data format version to handle version-specific parsing.
     * @return Void; the function updates the Character object directly based on the JSON data.
     */

  0.598  fread_char                               — Loads character data from a JSON object into a Character instance.
    /**
     * @fn void fread_char(Character *ch, cJSON *json, int version)
     *
     * @brief Loads character data from a JSON object into a Character instance.
     *
     * @details The function fread_char reads character attributes and affects from a JSON object and populates the corresponding fields in a Character instance. It handles both player characters (PC) and non-player characters (NPC), with specific fields being loaded conditionally based on the character type. The function logs the loading process and reports any unknown keys encountered in the JSON data.
     *
     * @param ch A pointer to the Character object that will be populated with data from the JSON object.
     * @param json A pointer to the cJSON object containing the character data to be read. If this is null, the function returns immediately.
     * @param version An integer representing the version of the data format being read, which may affect how certain fields are processed.
     * @return This function does not return a value.
     */

  0.576  backup_char_obj                          — Creates a backup of a character's data by copying and compressing its 
    /**
     * @fn void backup_char_obj(Character *ch)
     *
     * @brief Creates a backup of a character's data by copying and compressing its save file.
     *
     * @details Creates a backup of a Character object by saving its data and compressing the backup file.
    This function serializes the specified Character object into persistent storage, then constructs file paths based on the character's name, converting it to lowercase and capitalizing the first letter. It copies the character's save file from the main directory to a backup directory and subsequently compresses the backup file using gzip. The process involves system calls to execute shell commands for copying and compressing files, ensuring a backup of the character's data is maintained.
     *
     * @param ch Pointer to the Character object to be backed up.
     * @return This function has no return value; it performs file I/O and system operations to create a backup.
     */

  0.567  fread_pet                                — Loads a pet character from a JSON object, initializing its attributes 
    /**
     * @fn void fread_pet(Character *ch, cJSON *json, int version)
     *
     * @brief Loads a pet character from a JSON object, initializing its attributes and linking it to the owner character.
     *
     * @details This function reads pet data from a cJSON object and creates a new Character instance based on a mobile prototype identified by a vnum. It handles missing or invalid vnum entries by defaulting to a specific prototype and logs bugs accordingly. After creation, it removes non-permanent affects from the pet, loads character data from JSON, and sets the pet's leader and master to the owner character. It also adjusts the pet's hit points, mana, and stamina based on the time elapsed since the owner's last logoff, provided the owner is not affected by poison or plague.
     *
     * @param ch Pointer to the owner Character object who is summoning or owning the pet.
     * @param json Pointer to the cJSON object containing the pet's data to be loaded.
     * @param version Integer indicating the data format version, which may influence how data is read.
     * @return This function does not return a value; it initializes and links the pet character within the game environment.
     */

  0.542  save_storage_list                        — Saves the list of stored players to a file.
    /**
     * @fn void save_storage_list()
     *
     * @brief Saves the list of stored players to a file.
     *
     * @details This function opens the STORAGE_FILE for writing and saves the current list of stored players to it. It first writes the total number of stored characters, as determined by count_stored_characters(), to the file. Then, it iterates over the linked list of StoredPlayer objects, starting from storage_list_head->next and ending before storage_list_tail, writing each player's information to the file using save_line(). If the file cannot be opened, a bug is logged and the function returns early.
     *
     * @return This function does not return a value.
     */

  0.534  save_line                                — Writes player information to a file stream.
    /**
     * @fn void save_line(FILE *, StoredPlayer *)
     *
     * @brief Writes player information to a file stream.
     *
     * @details The function 'save_line' writes the name, the identifier of who stored the player, and the date of storage of a StoredPlayer object to a specified file stream. Each piece of information is followed by a tilde and a newline character. This function is used to persist player data in a structured format to a file.
     *
     * @param fp A pointer to a FILE object that identifies the output stream where the player information will be written.
     * @param sd A pointer to a StoredPlayer object containing the player information to be written to the file.
     * @return This function does not return a value.
     */

  0.516  fread_obj                                — Reads and initializes a game object from a JSON representation.
    /**
     * @fn Object * fread_obj(cJSON *json, int version)
     *
     * @brief Reads and initializes a game object from a JSON representation.
     *
     * @details This function processes a JSON object to create and initialize a game object, potentially including its contents. It first attempts to retrieve the object prototype using a virtual number (vnum) from the JSON data. If the prototype is found, a new object is created based on this prototype. If not, or if the vnum is missing, a dummy object is created. The function then iterates over the JSON data to set various attributes of the object, such as affects, description, and contained items. Special handling is included for weapon flags and affects based on the version of the object format.
     *
     * @param json A pointer to the cJSON object representing the game object to be read.
     * @param version An integer representing the version of the object format, which influences how certain fields are processed.
     * @return A pointer to the newly created and initialized Object, or a dummy Object if the prototype could not be found.
     */

  0.506  fwrite_objects                           — Creates a JSON array from a linked list of game objects.
    /**
     * @fn cJSON * fwrite_objects(Object *head)
     *
     * @brief Creates a JSON array from a linked list of game objects.
     *
     * @details This function iterates over a linked list of game objects, represented by the 'Object' structure, and converts each object into a cJSON item using the 'fwrite_obj' function. These items are inserted into a cJSON array in reverse order, ensuring that the original order is preserved when the array is later processed. If an object cannot be converted into a cJSON item (e.g., due to pruning), it is skipped. If no objects are successfully converted, the function returns a null pointer.
     *
     * @param head A pointer to the head of a linked list of 'Object' structures to be converted into a JSON array.
     * @return A pointer to a cJSON array containing the JSON representations of the game objects, or null if no objects were successfully converted.
     */

  0.500  save_war_table                           — Saves the current state of the war table to a file.
    /**
     * @fn void save_war_table()
     *
     * @brief Saves the current state of the war table to a file.
     *
     * @details This function opens a file specified by the concatenation of WAR_DIR and WAR_FILE for writing. It iterates over the war entries in the war table, writing the details of each war to the file. For each war, it writes the challenger and defender information, including their names, clan names, participation status, and scores. If the file cannot be opened, a bug report is logged.
     *
     * @return This function does not return a value.
     */

  0.484  save_social                              — Saves the details of a Social object to a file stream.
    /**
     * @fn void save_social(const Social *s, FILE *fp)
     *
     * @brief Saves the details of a Social object to a file stream.
     *
     * @details The function 'save_social' writes the attributes of a Social object to the specified file stream. Each attribute is processed to replace any occurrences of the tilde character '~' with a hyphen '-' before being written. This ensures that the output does not contain any tilde characters, which might be reserved for special purposes in the file format.
     *
     * @param s A pointer to a Social object whose details are to be saved.
     * @param fp A pointer to a FILE object representing the file stream where the Social object's details will be written.
     * @return This function does not return a value.
     */

  0.475  update_text_file                         — Appends a formatted string to a specified file for in-game text loggin
    /**
     * @fn void update_text_file(Character *ch, const String &file, const String &str)
     *
     * @brief Appends a formatted string to a specified file for in-game text logging.
     *
     * @details This function appends a formatted string to a specified file, typically used for logging in-game text files. It first checks if the character is a non-player character (NPC) or if the string to append is empty. If either condition is true, the function returns immediately without performing any action. Otherwise, it formats the string with the current date, the character's location, and name, and then appends this formatted string to the specified file.
     *
     * @param ch A pointer to the Character object, used to determine if the character is an NPC and to retrieve the character's name and location.
     * @param file A constant reference to a String object representing the name of the file to which the string will be appended.
     * @param str A constant reference to a String object representing the string to append to the file. If this string is empty, the function does nothing.
     * @return This function does not return a value.
     */

  0.473  save_war_events                          — Saves the events of each war to individual files.
    /**
     * @fn void save_war_events()
     *
     * @brief Saves the events of each war to individual files.
     *
     * @details The function iterates over a list of War instances, saving the events of each war to a uniquely named file in a specified directory. For each war, it creates a temporary file, writes the events in a formatted manner, and then renames the temporary file to a permanent file based on the war's index. If the temporary file cannot be opened, it logs an error message.
     *
     * @return This function does not return a value.
     */

  0.471  cJSON_Print                              — Converts a cJSON item to a formatted JSON string.
    /**
     * @fn char * cJSON_Print(cJSON *item)
     *
     * @brief Converts a cJSON item to a formatted JSON string.
     *
     * @details Converts a cJSON item into a formatted text representation.
    This function takes a cJSON item and renders it into a human-readable JSON string. The output string is formatted with indentation and newlines to enhance readability. This function is useful for debugging or displaying JSON data in a user-friendly format.
     *
     * @param item A pointer to the cJSON item that needs to be converted into a text representation.
     * @return A pointer to a character array containing the formatted text representation of the cJSON item. Returns null if memory allocation fails.
     */

  0.471  load_war_table                           — Loads war data from a file into a doubly linked list.
    /**
     * @fn void load_war_table()
     *
     * @brief Loads war data from a file into a doubly linked list.
     *
     * @details This function opens a file specified by the constants WAR_DIR and WAR_FILE to read war data. It reads a series of War objects from the file, each containing information about challengers and defenders. For each War object, it reads the names, clan names, and scores of up to four challengers and defenders, as well as the ongoing status of the war. The War objects are appended to a doubly linked list. If the file cannot be opened, a bug is logged.
     *
     * @return This function does not return a value.
     */

  0.466  is_worth_saving                          — Determines if an object is worth saving to the list.
    /**
     * @fn bool is_worth_saving(Object *obj)
     *
     * @brief Determines if an object is worth saving to the list.
     *
     * @details This function evaluates whether a given object should be saved based on its location, type, and state. It checks if the object is in a room and not carried or contained within another object. It excludes certain item types such as potions, scrolls, and NPC corpses, which typically have timers or are not worth saving. Additionally, it ensures that objects of a high level or those with active timers are not saved, unless they are player corpses. If the object resets on the ground, it is only saved if its contents have been modified.
     *
     * @param obj A pointer to the Object being evaluated for saving.
     * @return Returns true if the object is deemed worth saving based on its location, type, and state; otherwise, returns false.
     */

  0.464  cJSON_Parse                              — Parses a JSON string into a cJSON structure using default options.
    /**
     * @fn cJSON * cJSON_Parse(const char *value)
     *
     * @brief Parses a JSON string into a cJSON structure using default options.
     *
     * @details Parses a JSON string into a cJSON object.
    This function takes a C-style string containing JSON data and parses it into a cJSON structure. It uses default options, meaning it does not require the JSON string to be null-terminated and does not provide a pointer to the end of the parsed data. This function is a simplified interface to cJSON_ParseWithOpts, suitable for most use cases where these additional options are not needed.
     *
     * @param value A pointer to the C-style string containing the JSON data to be parsed.
     * @return A pointer to the newly created cJSON structure representing the parsed JSON data, or NULL if parsing fails or memory allocation fails.
     */

  0.451  save_social_table                        — Saves the social table to a file.
    /**
     * @fn void save_social_table()
     *
     * @brief Saves the social table to a file.
     *
     * @details This function opens a file specified by SOCIAL_FILE for writing and saves the details of all social entries from a linked list to this file. It first writes the total number of social entries, then iterates through the list, saving each entry's details using the save_social function. If the file cannot be opened, it logs an error message and exits without saving.
     *
     * @return This function does not return a value.
     */

  0.447  cJSON_StringIsConst                     
    /**
     * @def cJSON_StringIsConst
     *
     */

  0.447  update_pc_index                          — Updates the player character index in the database.
    /**
     * @fn void update_pc_index(const Character *ch, bool remove)
     *
     * @brief Updates the player character index in the database.
     *
     * @details This function updates the database entry for a player character in the 'pc_index' table. It first deletes any existing entry for the character based on their name. If the 'remove' flag is false, it inserts a new entry with the character's details, including their name, title, deity, cleaned deity name, group flags, level, remort count, clan name, and rank. The function uses SQL commands to perform these operations and ensures that special characters in strings are properly escaped for MySQL.
     *
     * @param ch A pointer to a Character object containing the player's details to be updated in the database.
     * @param remove A boolean flag indicating whether to remove the character's entry from the database. If true, the entry is deleted and not reinserted.
     * @return This function does not return a value.
     */

  0.443  cJSON_ParseWithOpts                      — Parses a JSON string into a cJSON structure with optional end pointer 
    /**
     * @fn cJSON * cJSON_ParseWithOpts(const char *value, const char **return_parse_end, int require_null_terminated)
     *
     * @brief Parses a JSON string into a cJSON structure with optional end pointer and termination check.
     *
     * @details Parses a JSON string into a cJSON structure with optional null-termination check.
    This function takes a JSON-formatted C-style string and attempts to parse it into a cJSON structure. It creates a new cJSON root item and populates it with the parsed data. The function can optionally return a pointer to the end of the parsed string and check if the JSON string is null-terminated, ensuring no additional characters follow the JSON data.
     *
     * @param value A pointer to the input string containing the JSON data to be parsed.
     * @param return_parse_end A pointer to a const char pointer where the function will store the position of the last parsed byte, or the error position if parsing fails.
     * @param require_null_terminated An integer flag indicating whether the JSON string must be null-terminated (non-zero value) or not (zero value).
     * @return A pointer to a newly created cJSON structure representing the parsed JSON data, or NULL if parsing fails or memory allocation fails.
     */

  0.427  add_help                                 — Adds a help entry to the database with specified attributes.
    /**
     * @fn void add_help(int group, int order, int level, const String &keywords, const String &text)
     *
     * @brief Adds a help entry to the database with specified attributes.
     *
     * @details This function inserts a new help entry into the database with the given group, order, level, keywords, and text. If the keywords are 'GREETING', it updates the game's greeting message. The function constructs an SQL query to insert the data, escaping special characters in the keywords and text to prevent SQL injection. It then executes the query using the db_command function.
     *
     * @param group The group identifier for the help entry.
     * @param order The order in which the help entry should appear.
     * @param level The level of detail or access required for the help entry.
     * @param keywords A string of keywords associated with the help entry. If 'GREETING', updates the game's greeting message.
     * @param text The actual help text to be stored in the database.
     * @return This function does not return a value.
     */

  0.423  cJSON_GetErrorPtr                        — Retrieves the pointer to the last error that occurred during JSON pars
    /**
     * @fn const char * cJSON_GetErrorPtr(void)
     *
     * @brief Retrieves the pointer to the last error that occurred during JSON parsing.
     *
     * @details Retrieves a pointer to the last parse error.
    This function returns a pointer to a string that describes the last error encountered during JSON parsing operations. It is useful for debugging and understanding why a JSON parsing function failed. The error pointer is updated each time a parsing error occurs, and it remains valid until the next parsing operation.
     *
     * @return A pointer to the character in the JSON input where the last parse error occurred, or 0 if the last call to cJSON_Parse() was successful.
     */

  0.413  save_departed_list                       — Saves the list of departed players to a file.
    /**
     * @fn void save_departed_list()
     *
     * @brief Saves the list of departed players to a file.
     *
     * @details This function writes the names of departed players to a file specified by DEPARTED_FILE. It opens the file in write mode and iterates through the list of departed players, writing each player's name followed by a newline character. If the file cannot be opened, it logs a bug message and exits the function. After writing all player names, it writes a '#' character followed by a newline to signify the end of the list, and then closes the file.
     *
     * @return This function does not return a value.
     */

  0.412  cJSON_GetObjectItem                      — Retrieves a JSON object item by its string key.
    /**
     * @fn cJSON * cJSON_GetObjectItem(cJSON *object, const char *string)
     *
     * @brief Retrieves a JSON object item by its string key.
     *
     * @details Retrieves a JSON item from an object by its string key, case-insensitively.
    This function searches for a child item within a given JSON object that matches the specified string key, using a case-insensitive comparison. It traverses the linked list of child items of the provided JSON object until it finds a match or reaches the end of the list.
     *
     * @param object The cJSON object from which to retrieve the item.
     * @param string The key string to search for within the object's children, case-insensitively.
     * @return A pointer to the cJSON item that matches the given string key, or NULL if no match is found.
     */

  0.406  print_object                             — Converts a cJSON object into its text representation.
    /**
     * @fn static char * print_object(cJSON *item, int depth, int fmt, printbuffer *p)
     *
     * @brief Converts a cJSON object into its text representation.
     *
     * @details This function generates a text representation of a cJSON object, optionally formatted for readability. It handles both empty and non-empty objects, using a printbuffer if provided, or dynamically allocating memory if not. The function iterates over the object's children, converting each into a string and appending it to the output. If formatting is enabled, it adds indentation and newlines to enhance readability.
     *
     * @param item A pointer to the cJSON object to be converted into a text representation.
     * @param depth The current depth in the JSON structure, used for formatting purposes.
     * @param fmt An integer flag indicating whether the output should be formatted (pretty-printed).
     * @param p A pointer to a printbuffer structure where the output will be written if provided. If null, dynamic memory allocation is used.
     * @return A pointer to a character array containing the text representation of the cJSON object, or null if memory allocation fails.
     */

  0.403  INTKEY                                  
    /**
     * @def INTKEY
     *
     */

  0.402  cJSON_IsReference                       
    /**
     * @def cJSON_IsReference
     *
     */

  0.402  lookup_storage_data                      — Looks up a stored player by name in a linked list.
    /**
     * @fn StoredPlayer * lookup_storage_data(const String &name)
     *
     * @brief Looks up a stored player by name in a linked list.
     *
     * @details This function searches through a linked list of StoredPlayer objects to find a player whose name matches the given String object. It starts from the node following the head of the list and continues until it reaches the tail. The comparison is case-insensitive, utilizing the strcasecmp function from the String class.
     *
     * @param name The name of the player to search for, encapsulated in a String object.
     * @return A pointer to the StoredPlayer object if a matching name is found; otherwise, nullptr if no match is found.
     */

  0.398  count_stored_characters                  — Counts the number of stored characters in a linked list.
    /**
     * @fn int count_stored_characters()
     *
     * @brief Counts the number of stored characters in a linked list.
     *
     * @details This function traverses a linked list of StoredPlayer objects, starting from the node after storage_list_head and ending at storage_list_tail, counting each node encountered. It assumes that storage_list_head and storage_list_tail are sentinel nodes marking the beginning and end of the list, respectively.
     *
     * @return The total number of StoredPlayer nodes between storage_list_head and storage_list_tail, exclusive.
     */

  0.398  STRKEY                                  
    /**
     * @def STRKEY
     *
     */

  0.393  load_war_events                          — Loads war events from files and populates the war event list.
    /**
     * @fn void load_war_events()
     *
     * @brief Loads war events from files and populates the war event list.
     *
     * @details This function iterates over a list of War instances and attempts to load associated event data from files. For each War instance, it constructs a filename based on the war's index and attempts to open the file. If the file is successfully opened, it reads event data until an 'END' marker is encountered. Each event is read from the file, parsed, and added to the War instance's event list. If the file cannot be opened, a bug is logged. The function handles the creation and linking of War::Event objects to the War instance's event list.
     *
     * @return This function does not return a value.
     */

  0.392  db_queryf                                — Executes a formatted SQL query and logs the function context.
    /**
     * @fn int db_queryf(const String &func, const String &query, Params... params)
     *
     * @brief Executes a formatted SQL query and logs the function context.
     *
     * @details The db_queryf function formats a SQL query string using the provided parameters and executes it within the context of a specified function. It leverages the Format::format function to insert parameters into the query string, and then calls db_query to execute the formatted query. This function is useful for executing parameterized SQL queries while maintaining a log of the function context for debugging or auditing purposes.
     *
     * @param func The name of the function where the query is being executed, used for logging purposes.
     * @param query A format string that specifies the SQL query to be executed, with placeholders for parameters.
     * @param params Variadic template parameters that are inserted into the query format string.
     * @return Returns SQL_OK if the query is successfully prepared and executed, otherwise returns SQL_ERROR.
     */

  0.388  parse_value                              — Parses a JSON value from a string and stores it in a cJSON item.
    /**
     * @fn static const char * parse_value(cJSON *item, const char *value, const char **ep)
     *
     * @brief Parses a JSON value from a string and stores it in a cJSON item.
     *
     * @details This function examines the input string 'value' and determines the type of JSON value it represents. It then parses the value accordingly and stores the result in the provided cJSON item. The function handles JSON literals such as 'null', 'true', and 'false', as well as strings, numbers, arrays, and objects. If the input does not match any valid JSON value, the function sets the error pointer 'ep' to the position of the failure and returns null.
     *
     * @param item A pointer to a cJSON structure where the parsed value will be stored.
     * @param value A pointer to the input string containing the JSON value to be parsed.
     * @param ep A pointer to a const char pointer that will be set to the position in the string where parsing failed, if applicable.
     * @return A pointer to the character in the input string immediately following the parsed value, or null if parsing fails.
     */

  0.384  print_string                             — Converts a cJSON item's string value to an escaped string.
    /**
     * @fn static char * print_string(cJSON *item, printbuffer *p)
     *
     * @brief Converts a cJSON item's string value to an escaped string.
     *
     * @details This function invokes the print_string_ptr function on a cJSON item to convert its string value into an escaped format suitable for printing. It utilizes a printbuffer for memory allocation if provided, otherwise, it defaults to dynamic memory allocation.
     *
     * @param item A pointer to the cJSON item whose string value is to be converted.
     * @param p A pointer to a printbuffer structure used for memory allocation of the output string. If null, dynamic memory allocation is used.
     * @return A pointer to the newly allocated escaped string, or null if memory allocation fails.
     */

  0.383  db_commandf                              — Executes a formatted SQL command and checks for successful execution.
    /**
     * @fn int db_commandf(const String &func, const String &query, Params... params)
     *
     * @brief Executes a formatted SQL command and checks for successful execution.
     *
     * @details The db_commandf function formats an SQL query string using the provided parameters and executes it. It combines the functionality of formatting a query string with executing it against a database. This function is useful for executing parameterized SQL commands, ensuring that the query is correctly formatted before execution. It logs the function name for debugging and tracking purposes.
     *
     * @param func The name of the function calling db_commandf, used for logging purposes.
     * @param query A constant reference to a String object that specifies the SQL query format.
     * @param params Variadic parameters used to format the SQL query string.
     * @return Returns SQL_OK if the command is successfully executed and the next row is available, otherwise returns SQL_ERROR if an error occurs.
     */

  0.378  JSON::get_short                          — Retrieves an integer value from a JSON object and stores it in a targe
    /**
     * @fn void JSON::get_short(cJSON *obj, void *target, const String &key)
     *
     * @brief Retrieves an integer value from a JSON object and stores it in a target location.
     *
     * @details This function searches for a JSON object item specified by the key within the given JSON object. If the item is found and is not null, it extracts the integer value from the JSON item and stores it in the memory location pointed to by the target pointer. The key is provided as a String object, which is converted to a C-style string for the search.
     *
     * @param obj The JSON object from which to retrieve the integer value.
     * @param target A pointer to the memory location where the retrieved integer value will be stored.
     * @param key The key string used to search for the corresponding JSON object item.
     * @return This function does not return a value.
     */

  0.376  print_value                              — Converts a cJSON item into its text representation.
    /**
     * @fn static char * print_value(cJSON *item, int depth, int fmt, printbuffer *p)
     *
     * @brief Converts a cJSON item into its text representation.
     *
     * @details This function takes a cJSON item and converts it into a string representation based on its type. It handles various JSON types such as null, boolean, number, string, array, and object. The function can either use a provided printbuffer for output or allocate memory dynamically if no buffer is provided. The output is formatted according to the specified depth and formatting flag.
     *
     * @param item A pointer to the cJSON item to be converted into a text representation.
     * @param depth The current depth in the JSON structure, used for formatting purposes.
     * @param fmt An integer flag indicating whether the output should be formatted (pretty-printed).
     * @param p A pointer to a printbuffer structure where the output will be written if provided. If null, dynamic memory allocation is used.
     * @return A pointer to a character array containing the text representation of the cJSON item, or null if memory allocation fails.
     */

  0.375  JSON::read_file                          — Reads a JSON file and parses its contents into a cJSON object.
    /**
     * @fn cJSON * JSON::read_file(const String &filename)
     *
     * @brief Reads a JSON file and parses its contents into a cJSON object.
     *
     * @details This function attempts to open a file specified by the filename parameter, reads its entire contents into a dynamically allocated buffer, and parses it as a JSON object using the cJSON library. If any step fails, such as opening the file, reading its contents, or parsing the JSON, the function logs an error message and returns nullptr. The function ensures that resources are properly released in case of errors.
     *
     * @param filename A constant reference to a String object representing the path to the JSON file to be read.
     * @return A pointer to a cJSON object representing the parsed JSON data if successful, or nullptr if an error occurs during file operations or JSON parsing.
     */

  0.375  cJSON_AddStringToObject                 
    /**
     * @def cJSON_AddStringToObject
     *
     */

  0.374  insert_storagedata                       — Inserts a new StoredPlayer into a sorted linked list.
    /**
     * @fn void insert_storagedata(StoredPlayer *newdata)
     *
     * @brief Inserts a new StoredPlayer into a sorted linked list.
     *
     * @details This function inserts a new StoredPlayer object into a linked list that is sorted based on the player's name in a case-insensitive manner. It traverses the list starting from the head, comparing the new player's name with existing players using a case-insensitive comparison. The new player is inserted in the correct position to maintain the sorted order. If the correct position is not found before reaching the tail, the new player is inserted just before the tail.
     *
     * @param newdata A pointer to the StoredPlayer object to be inserted into the linked list.
     * @return This function does not return a value.
     */

  0.374  parse_object                             — Parses a JSON object from a string and stores it in a cJSON item.
    /**
     * @fn static const char * parse_object(cJSON *item, const char *value, const char **ep)
     *
     * @brief Parses a JSON object from a string and stores it in a cJSON item.
     *
     * @details This function takes a JSON-formatted string starting with an opening brace '{' and attempts to parse it into a cJSON object structure. It processes key-value pairs within the object, creating new cJSON items for each pair. The function handles whitespace and expects keys to be strings followed by a colon and a value. It continues parsing until it encounters a closing brace '}'. If the input string is not a valid JSON object or if memory allocation fails, the function returns an error.
     *
     * @param item A pointer to a cJSON structure where the parsed object will be stored.
     * @param value A pointer to the input string containing the JSON object to be parsed.
     * @param ep A pointer to a const char pointer that will be set to the position in the string where parsing failed, if applicable.
     * @return A pointer to the character in the input string immediately following the parsed object, or null if parsing fails.
     */

  0.372  SKIPKEY                                 
    /**
     * @def SKIPKEY
     *
     */

  0.371  JSON::addStringToObject                  — Adds a string to a JSON object.
    /**
     * @fn void JSON::addStringToObject(cJSON *obj, const String &key, const String &str)
     *
     * @brief Adds a string to a JSON object.
     *
     * @details This function adds a key-value pair to a JSON object, where the key and value are both strings. The key and value are provided as String objects, which are converted to C-style strings for compatibility with the cJSON library.
     *
     * @param obj A pointer to the cJSON object to which the string will be added.
     * @param key The key for the string entry, provided as a String object.
     * @param str The string value to be added, provided as a String object.
     * @return This function does not return a value.
     */

  0.365  db_get_column_str                        — Retrieves a text value from a specified column in the current database
    /**
     * @fn const char * db_get_column_str(int index)
     *
     * @brief Retrieves a text value from a specified column in the current database row.
     *
     * @details Retrieves a text value from a database query result column.
    This function accesses the result set of a database query and returns the text value of the column at the specified index. It assumes that the query has been executed and the result set is available. The function casts the result to a const char pointer, which points to the UTF-8 encoded text of the column. The caller must ensure that the index is within the bounds of the result set's columns.
     *
     * @param index The zero-based index of the column from which to retrieve the text value.
     * @return A pointer to a constant character string representing the text value of the specified column. If the column value is NULL, the return value is also NULL.
     */

  0.363  db_esc                                   — Escapes special characters in a string for use in a MySQL query.
    /**
     * @fn String db_esc(const String &str)
     *
     * @brief Escapes special characters in a string for use in a MySQL query.
     *
     * @details Escapes single quotes in a string for database queries.
    This function takes a string and escapes special characters to make it safe for inclusion in a MySQL query. Specifically, it doubles single quote characters to prevent SQL injection attacks. The function does not handle double quotes, as they are not typically used in MySQL queries. The input string is processed character by character, and an escaped version is returned.
     *
     * @param str The input String that needs to be escaped.
     * @return A new String with single quotes doubled for safe use in database queries.
     */

  0.362  db_query                                 — Executes a SQL query and stores the result.
    /**
     * @fn int db_query(const String &func, const String &query)
     *
     * @brief Executes a SQL query and stores the result.
     *
     * @details Executes an SQL query on the database.
    This function prepares and executes a SQL query using the provided function name and query string. It ensures that a database connection is open and that any previous query results are finalized before executing the new query. If the query preparation fails, it logs the error and returns an error code.
     *
     * @param func The name of the function calling db_query, used for logging purposes.
     * @param query The SQL query string to be executed.
     * @return Returns SQL_OK if the query is successfully prepared and executed, otherwise returns SQL_ERROR if an error occurs.
     */

  0.361  JSON::get_long                           — Extracts a long integer value from a JSON object using a specified key
    /**
     * @fn void JSON::get_long(cJSON *obj, long *target, const String &key)
     *
     * @brief Extracts a long integer value from a JSON object using a specified key.
     *
     * @details This function retrieves a JSON object item corresponding to the provided key from the given JSON object. If the item is found, it assigns the integer value of the JSON item to the target long integer pointer. The function uses a case-sensitive key for lookup.
     *
     * @param obj The cJSON object from which to retrieve the item.
     * @param target A pointer to a long integer where the retrieved value will be stored if the key is found.
     * @param key The key string used to search for the corresponding JSON item within the object.
     * @return This function does not return a value.
     */

  0.361  fread_word                               — Reads a single word from a file stream.
    /**
     * @fn String fread_word(FILE *fp)
     *
     * @brief Reads a single word from a file stream.
     *
     * @details Reads a word from a file stream.
    This function reads a word from the provided file stream, defined as a sequence of non-whitespace characters. It handles quoted words by treating the quote as a delimiter. The word is read into a static buffer and returned as a String object. If the word exceeds the buffer size, a bug is reported via the Logging::bug function.
     *
     * @param fp A pointer to a FILE object that specifies the input file stream from which the word is to be read.
     * @return A String object containing the word read from the file stream. If the word is too long, an empty string is returned.
     */

  0.359  db_countf                                — Executes a formatted SQL COUNT query and returns the count of matching
    /**
     * @fn int db_countf(const String &func, const String &query, Params... params)
     *
     * @brief Executes a formatted SQL COUNT query and returns the count of matching rows.
     *
     * @details The db_countf function formats a SQL query string using the provided parameters and executes it to count the number of rows that match the query. It is a convenience wrapper around the db_count function, allowing for formatted query strings. The function is useful for logging and debugging purposes, as it includes the name of the calling function in its parameters.
     *
     * @param func The name of the function calling db_countf, used for logging purposes.
     * @param query A format string that specifies the SQL COUNT query to be executed.
     * @param params Variadic parameters that are used to format the query string.
     * @return Returns the count of rows matching the formatted query: 0 if no rows match, a positive integer if rows are found, or -1 if an error occurs during query execution.
     */

  0.358  JSON::get_string                         — Retrieves a string value from a JSON object and assigns it to a target
    /**
     * @fn void JSON::get_string(cJSON *obj, String *target, const String &key)
     *
     * @brief Retrieves a string value from a JSON object and assigns it to a target String.
     *
     * @details This function searches for a JSON object item using a specified key. If the item is found and is not null, it assigns the item's string value to the provided target String object. The function uses cJSON_GetObjectItem to locate the item within the JSON object.
     *
     * @param obj The JSON object from which to retrieve the string value.
     * @param target A pointer to the String object where the retrieved string value will be assigned.
     * @param key The key string used to search for the corresponding JSON object item.
     * @return This function does not return a value.
     */

  0.358  cJSON_GetArraySize                       — Returns the number of items in a JSON array.
    /**
     * @fn int cJSON_GetArraySize(cJSON *array)
     *
     * @brief Returns the number of items in a JSON array.
     *
     * @details Calculates the number of items in a JSON array or object.
    This function calculates and returns the number of elements present in a JSON array. It iterates through the linked list of child elements of the given cJSON array object, counting each element until it reaches the end of the list.
     *
     * @param array A pointer to a cJSON object representing a JSON array or object whose size is to be determined.
     * @return The total number of items in the specified JSON array or object.
     */

  0.357  remove_storagedata                       — Removes a stored player from the linked list.
    /**
     * @fn void remove_storagedata(StoredPlayer *olddata)
     *
     * @brief Removes a stored player from the linked list.
     *
     * @details This function searches for a StoredPlayer object in a linked list that matches the name of the given 'olddata' parameter. It performs a case-insensitive comparison of the names using the 'strcasecmp' function. If a match is found, the function removes the matching StoredPlayer from the list by adjusting the pointers of the neighboring nodes and then deletes the matched node.
     *
     * @param olddata A pointer to a StoredPlayer object whose name is used to find and remove a matching player from the linked list.
     * @return This function does not return a value.
     */

  0.357  db_command                               — Executes an SQL command and checks for successful execution.
    /**
     * @fn int db_command(const String &func, const String &query)
     *
     * @brief Executes an SQL command and checks for successful execution.
     *
     * @details Executes an SQL command and advances to the next row in the result set.
    This function performs an SQL command by executing the provided query string on the database. It first calls db_query to execute the query, and if successful, it advances to the next row in the result set using db_next_row. The function is used when the query does not expect a result set to be processed, and it returns a status indicating the success or failure of the operation.
     *
     * @param func The name of the function calling db_command, used for logging purposes.
     * @param query The SQL query string to be executed.
     * @return Returns SQL_OK if the query is successfully executed and a new row is available, otherwise returns SQL_ERROR if an error occurs during query execution or row advancement.
     */

  0.353  db_count                                 — Executes a SQL COUNT query and returns the count of matching rows.
    /**
     * @fn int db_count(const String &func, const String &query)
     *
     * @brief Executes a SQL COUNT query and returns the count of matching rows.
     *
     * @details Executes an SQL query and retrieves an integer from the first column of the result.
    This function takes a complete SQL query string that includes a COUNT operation, such as SELECT COUNT(*), and executes it against the database. It does not return the result set itself, but rather an integer representing the count of rows that match the query. The function is useful for quickly determining the number of entries that satisfy a given condition without retrieving the actual data.
     *
     * @param func The name of the function calling db_count, used for logging purposes.
     * @param query The SQL query string to be executed.
     * @return The integer value from the first column of the result set if the query is successful, otherwise 0.
     */

  0.351  parse_string                             — Parses a JSON string and converts it into a cJSON item.
    /**
     * @fn static const char * parse_string(cJSON *item, const char *str, const char **ep)
     *
     * @brief Parses a JSON string and converts it into a cJSON item.
     *
     * @details This function takes a JSON string starting with a double quote and parses it into a cJSON item, handling escape sequences and UTF-16 surrogate pairs. It allocates memory for the parsed string and stores it in the cJSON item. The function ensures that the string is properly terminated and handles errors such as invalid escape sequences or incomplete surrogate pairs.
     *
     * @param item A pointer to a cJSON structure where the parsed string will be stored.
     * @param str A pointer to the JSON string to be parsed, which must start with a double quote.
     * @param ep A pointer to a const char* that will be set to the error position if parsing fails.
     * @return A pointer to the character following the closing double quote of the parsed string, or 0 if parsing fails.
     */

  0.345  cJSON_AddNumberToObject                 
    /**
     * @def cJSON_AddNumberToObject
     *
     */

  0.345  fread_string                             — Reads a string from a file until a specified character is encountered.
    /**
     * @fn String fread_string(FILE *fp, char to_char)
     *
     * @brief Reads a string from a file until a specified character is encountered.
     *
     * @details This function reads characters from the given file pointer 'fp' and constructs a String object until the specified 'to_char' character is encountered or EOF is reached. It skips initial whitespace characters and handles carriage return characters by ignoring them. If EOF is reached before 'to_char', a bug is logged using Logging::bug.
     *
     * @param fp A pointer to a FILE object from which characters are read.
     * @param to_char The character that signifies the end of the string to be read.
     * @return A String object containing the characters read from the file up to, but not including, the 'to_char' character.
     */

  0.339  cJSON_AddItemToObject                    — Adds a cJSON item to a cJSON object with a specified key.
    /**
     * @fn void cJSON_AddItemToObject(cJSON *object, const char *string, cJSON *item)
     *
     * @brief Adds a cJSON item to a cJSON object with a specified key.
     *
     * @details Adds a cJSON item to an object with a specified key.
    This function adds a cJSON item to a given cJSON object using a specified key. If the item already has a string key, it is freed and replaced with a duplicate of the provided string key. The item is then added to the object using the cJSON_AddItemToArray function. This function is useful for constructing JSON objects by associating keys with their corresponding values.
     *
     * @param object A pointer to the cJSON object to which the item will be added.
     * @param string The key with which the item will be associated in the object.
     * @param item A pointer to the cJSON item that will be added to the object.
     * @return This function does not return a value.
     */

  0.332  db_error                                 — Logs an error message related to a database operation and handles crit
    /**
     * @fn void db_error(const String &func, const String &query)
     *
     * @brief Logs an error message related to a database operation and handles critical boot-time errors.
     *
     * @details Logs a database error and handles critical failure during boot.
    This function logs a formatted error message indicating a failure in a database operation. It uses the provided function name and query to construct the message. If the query is not empty, it includes the query in the log message. The function also checks if the application is in the booting phase. If so, it closes the database connection and terminates the program with an exit code of 1, indicating a critical error during startup.
     *
     * @param func The name of the function where the error occurred, used for logging purposes.
     * @param query The SQL query that was being executed when the error occurred, used for logging purposes if not empty.
     * @return This function does not return a value.
     */

  0.330  JSON::get_int                            — Retrieves an integer value from a JSON object by key.
    /**
     * @fn void JSON::get_int(cJSON *obj, int *target, const String &key)
     *
     * @brief Retrieves an integer value from a JSON object by key.
     *
     * @details This function searches for a JSON object item within the given cJSON object using the specified key. If the item is found and is not null, it assigns the integer value of the item to the target integer pointer. The function assumes that the JSON item associated with the key is of integer type.
     *
     * @param obj The cJSON object from which to retrieve the integer value.
     * @param target A pointer to an integer where the retrieved value will be stored if found.
     * @param key The key string used to search for the JSON object item within the cJSON object.
     * @return This function does not return a value.
     */

  0.329  print_number                             — Converts a numeric value from a cJSON item into a formatted string.
    /**
     * @fn static char * print_number(cJSON *item, printbuffer *p)
     *
     * @brief Converts a numeric value from a cJSON item into a formatted string.
     *
     * @details This function takes a cJSON item containing a numeric value and renders it into a human-readable string format. It handles special cases such as zero, integers, and floating-point numbers, including checks for NaN and infinity. The function uses a printbuffer if provided, or allocates memory dynamically if not, to ensure there is enough space for the formatted string.
     *
     * @param item A pointer to the cJSON item containing the numeric value to be rendered.
     * @param p A pointer to a printbuffer structure used to manage the output buffer, or null if dynamic allocation is preferred.
     * @return A pointer to a character array containing the formatted string representation of the number, or null if memory allocation fails.
     */

  0.328  print_array                              — Renders a cJSON array to a text representation.
    /**
     * @fn static char * print_array(cJSON *item, int depth, int fmt, printbuffer *p)
     *
     * @brief Renders a cJSON array to a text representation.
     *
     * @details This function converts a cJSON array into a formatted text string. It handles both formatted and unformatted output based on the 'fmt' parameter. If a printbuffer is provided, it writes directly into the buffer; otherwise, it allocates memory for the output string. The function iterates over the array's elements, converting each to a string and appending it to the result. It manages memory allocation and ensures the buffer has sufficient space for the output.
     *
     * @param item A pointer to the cJSON object representing the array to be rendered.
     * @param depth The current depth in the JSON structure, used for formatting purposes.
     * @param fmt An integer flag indicating whether the output should be formatted (pretty-printed).
     * @param p A pointer to a printbuffer structure where the output will be written if provided.
     * @return A pointer to a character array containing the text representation of the JSON array, or null if memory allocation fails.
     */

  0.328  insert_departed                          — Inserts a new departed player into a sorted list.
    /**
     * @fn void insert_departed(const String &name)
     *
     * @brief Inserts a new departed player into a sorted list.
     *
     * @details Inserts a departed player into a sorted list based on their name.
    This function adds a new DepartedPlayer object, initialized with the given name, into a doubly linked list of departed players. The list is sorted in case-insensitive lexicographical order based on player names. The function traverses the list to find the correct insertion point for the new player, ensuring the list remains sorted. If the list is empty or the new player should be inserted at the end, the function handles these cases appropriately.
     *
     * @param name The name of the departed player to be inserted into the list.
     * @return This function does not return a value.
     */

  0.327  db_open                                  — Opens a connection to the database.
    /**
     * @fn void db_open()
     *
     * @brief Opens a connection to the database.
     *
     * @details This function attempts to open a connection to the database specified by DB_FILE. If the database connection (_db) is already open, it logs a bug report indicating that the database is not nullptr but proceeds to open it anyway. It uses sqlite3_open_v2 to open the database in read-write mode. If the operation fails, it logs a database error using the db_error function.
     *
     * @return This function does not return a value.
     */

  0.324  parse_array                              — Parses a JSON array from a string and constructs a cJSON array item.
    /**
     * @fn static const char * parse_array(cJSON *item, const char *value, const char **ep)
     *
     * @brief Parses a JSON array from a string and constructs a cJSON array item.
     *
     * @details This function takes a JSON-formatted string and attempts to parse it as a JSON array. It constructs a cJSON object representing the array, with each element of the array being a child cJSON object. The function handles whitespace and expects the input string to start with a '[' character, indicating the beginning of a JSON array. It continues parsing until it encounters a ']' character, which signifies the end of the array. If the array is empty, it returns immediately after the opening bracket. The function also manages memory allocation for new cJSON items and links them as siblings in the array.
     *
     * @param item A pointer to a cJSON object where the parsed array will be stored.
     * @param value A pointer to the input string containing the JSON array to be parsed.
     * @param ep A pointer to a const char pointer that will be set to the position in the string where parsing failed, if applicable.
     * @return A pointer to the position in the input string immediately following the parsed array, or NULL if parsing fails.
     */

  0.324  has_departed                             — Checks if a player with the given name has departed.
    /**
     * @fn bool has_departed(const String &name)
     *
     * @brief Checks if a player with the given name has departed.
     *
     * @details This function iterates through a linked list of departed players to determine if a player with the specified name exists in the list. It performs a case-insensitive comparison of the given name against each player's name in the list using the strcasecmp function.
     *
     * @param name The name of the player to check for in the departed players list.
     * @return Returns true if a player with the given name is found in the departed list, otherwise returns false.
     */

  0.324  cJSON_AddItemToArray                     — Adds a cJSON item to an array or object.
    /**
     * @fn void cJSON_AddItemToArray(cJSON *array, cJSON *item)
     *
     * @brief Adds a cJSON item to an array or object.
     *
     * @details Appends an item to a cJSON array or object.
    This function appends a cJSON item to the end of an existing array or object. If the array or object is empty, the item becomes the first child. The function ensures that the item is correctly linked into the existing structure.
     *
     * @param array A pointer to the cJSON array or object to which the item will be appended.
     * @param item A pointer to the cJSON item to be appended to the array or object.
     * @return This function does not return a value.
     */

  0.322  parse_number                             — Parses a numeric value from a string and stores it in a cJSON item.
    /**
     * @fn static const char * parse_number(cJSON *item, const char *num)
     *
     * @brief Parses a numeric value from a string and stores it in a cJSON item.
     *
     * @details This function takes a string representing a number and parses it to extract the numeric value. It handles optional signs, integer and fractional parts, and scientific notation. The parsed number is stored in the provided cJSON item as both a double and an integer, and the item's type is set to cJSON_Number.
     *
     * @param item A pointer to a cJSON structure where the parsed number will be stored.
     * @param num A pointer to a string containing the numeric value to be parsed.
     * @return A pointer to the character in the string immediately following the parsed number.
     */

  0.309  suffix_object                            — Appends an item to the end of a cJSON linked list.
    /**
     * @fn static void suffix_object(cJSON *prev, cJSON *item)
     *
     * @brief Appends an item to the end of a cJSON linked list.
     *
     * @details This function links a new cJSON item to the end of an existing cJSON linked list. It sets the 'next' pointer of the last item in the list to point to the new item, and the 'prev' pointer of the new item to point back to the last item. This effectively appends the new item to the list.
     *
     * @param prev A pointer to the last cJSON item in the current list.
     * @param item A pointer to the cJSON item to be appended to the list.
     * @return This function does not return a value.
     */

  0.307  print_string_ptr                         — Converts a C-style string to an escaped version suitable for printing.
    /**
     * @fn static char * print_string_ptr(const char *str, printbuffer *p)
     *
     * @brief Converts a C-style string to an escaped version suitable for printing.
     *
     * @details This function takes a C-style string and converts it into a new string where special characters are escaped, making it safe for printing. If the input string contains characters that need escaping (such as quotes, backslashes, or control characters), they are replaced with their corresponding escape sequences. The function allocates memory for the new string, either using a provided printbuffer or dynamically if no buffer is provided.
     *
     * @param str A pointer to the C-style string that needs to be converted to an escaped format.
     * @param p A pointer to a printbuffer structure used for allocating memory for the output string. If null, dynamic memory allocation is used.
     * @return A pointer to the newly allocated escaped string, or null if memory allocation fails.
     */

  0.307  fappend                                  — Appends a string to a specified file.
    /**
     * @fn void fappend(const String &file, const String &str)
     *
     * @brief Appends a string to a specified file.
     *
     * @details Appends a string to a file.
    This function appends the contents of a given string to the end of a specified file. If the string is empty, the function returns immediately without performing any operations. If the file cannot be opened for appending, a bug report message is logged indicating the failure.
     *
     * @param file The name of the file to which the string will be appended.
     * @param str The string content to append to the file.
     * @return This function does not return a value.
     */

  0.306  fgetf                                    — Reads a string from a file stream into a buffer.
    /**
     * @fn char * fgetf(char *s, int n, register FILE *iop)
     *
     * @brief Reads a string from a file stream into a buffer.
     *
     * @details The function reads characters from the specified file stream 'iop' into the buffer 's' until either 'n-1' characters have been read, a null character is encountered, or EOF is reached. The buffer is null-terminated. If EOF is encountered before any characters are read, a null pointer is returned.
     *
     * @param s A pointer to the buffer where the read string will be stored.
     * @param n The maximum number of characters to read, including the null terminator.
     * @param iop A pointer to the file stream from which characters are read.
     * @return A pointer to the buffer 's' if successful, or nullptr if EOF is encountered before any characters are read.
     */

  0.294  remove_departed                          — Removes a departed player from the list by name.
    /**
     * @fn void remove_departed(const String &name)
     *
     * @brief Removes a departed player from the list by name.
     *
     * @details This function searches through a linked list of departed players and removes the player whose name matches the given name, ignoring case. It updates the pointers of the adjacent nodes to maintain the list structure and deallocates the memory for the removed player.
     *
     * @param name The name of the departed player to be removed from the list.
     * @return This function does not return a value.
     */

  0.288  fread_number                             — Reads an integer from a file stream.
    /**
     * @fn int fread_number(FILE *fp)
     *
     * @brief Reads an integer from a file stream.
     *
     * @details This function reads characters from the given file stream to construct an integer. It handles optional leading '+' or '-' signs and skips any leading whitespace. If a non-digit character is encountered after any optional sign, a bug is reported using Logging::bug, and zero is returned. The function also supports recursive reading if a '|' character is encountered, adding the result of the recursive call to the current number. If a non-space character is encountered that is not part of the number, it is pushed back onto the stream.
     *
     * @param fp A pointer to a FILE object that specifies the input file stream from which the number is read.
     * @return The integer value read from the file stream, or zero if the format is invalid.
     */

  0.283  db_get_column_int                        — Retrieves an integer value from a specified column in the current data
    /**
     * @fn int db_get_column_int(int index)
     *
     * @brief Retrieves an integer value from a specified column in the current database result row.
     *
     * @details Retrieves an integer value from a specified column in the current database query result.
    This function accesses the current row of a database query result and retrieves the integer value from the column specified by the given index. It uses the sqlite3_column_int function to perform this operation, which is part of the SQLite C API. The function assumes that the query has been executed and the result set is ready for reading.
     *
     * @param index The zero-based index of the column from which to retrieve the integer value.
     * @return The integer value from the specified column of the current row in the result set.
     */

  0.282  db_rows_affected                         — Retrieves the number of rows affected by the last executed SQL stateme
    /**
     * @fn int db_rows_affected()
     *
     * @brief Retrieves the number of rows affected by the last executed SQL statement.
     *
     * @details This function returns the number of database rows that were changed, inserted, or deleted by the most recent SQL statement executed on the database connection represented by '_db'. It utilizes the sqlite3_changes function from the SQLite library to obtain this information. This function is useful for determining the impact of data modification queries such as INSERT, UPDATE, or DELETE.
     *
     * @return The number of rows affected by the last SQL statement executed on the database connection.
     */

  0.279  cJSON_InsertItemInArray                  — Inserts a cJSON item into a specified position in an array.
    /**
     * @fn void cJSON_InsertItemInArray(cJSON *array, int which, cJSON *newitem)
     *
     * @brief Inserts a cJSON item into a specified position in an array.
     *
     * @details This function inserts a new cJSON item into an existing cJSON array at the specified index. If the index is beyond the current size of the array, the new item is added to the end of the array. The function updates the linked list pointers to maintain the integrity of the array structure.
     *
     * @param array A pointer to the cJSON array where the new item will be inserted.
     * @param which The zero-based index at which the new item should be inserted. If this index is greater than the number of items, the item is appended.
     * @param newitem A pointer to the cJSON item that will be inserted into the array.
     * @return This function does not return a value.
     */

  0.276  db_close                                 — Closes the database connection if it is open.
    /**
     * @fn void db_close()
     *
     * @brief Closes the database connection if it is open.
     *
     * @details This function checks if the database connection, represented by the pointer _db, is currently open (i.e., not null). If the connection is open, it closes the database using sqlite3_close and sets the _db pointer to null to indicate that the connection is no longer active.
     *
     * @return This function does not return a value.
     */

  0.273  db_next_row                              — Advances to the next row in the SQLite query result.
    /**
     * @fn int db_next_row()
     *
     * @brief Advances to the next row in the SQLite query result.
     *
     * @details Advances to the next row in the result set of an SQLite query.
    This function attempts to move to the next row of the result set from a previously executed SQLite statement. It uses sqlite3_step to advance the result set cursor. If a row is available, it returns SQL_OK. If the end of the result set is reached or an error occurs, it returns SQL_ERROR.
     *
     * @return Returns SQL_OK if a new row is available, otherwise returns SQL_ERROR.
     */


================================================================================
[utility] memory  (stability: stable)
  desc: Memory lifecycle management: pooled object allocation and deallocation tracking, garbage-collection marking and deferred…
  locked: 17 functions, 17 with embeddings
  sim to desc — mean: 0.417  min: 0.305  max: 0.530

  0.530  >::pool_allocated                        — Provides access to a static counter of allocated resources.
    /**
     * @fn static unsigned int & Pooled< T >::pool_allocated()
     *
     * @brief Provides access to a static counter of allocated resources.
     *
     * @details This function returns a reference to a static unsigned integer that tracks the number of resources allocated by a pool. The static variable 'allocated' is initialized to zero on the first call and retains its value across subsequent calls. This function can be used to monitor or modify the count of allocated resources.
     *
     * @return A reference to a static unsigned integer representing the number of allocated resources.
     */

  0.499  cJSON_Delete                             — Deletes a cJSON structure and its children.
    /**
     * @fn void cJSON_Delete(cJSON *c)
     *
     * @brief Deletes a cJSON structure and its children.
     *
     * @details Deletes a cJSON entity and all its subentities.
    This function recursively deletes a cJSON structure and all of its child elements. It frees any dynamically allocated memory associated with the cJSON object, including strings and child nodes, unless they are marked as references or constant strings. The function ensures that all memory used by the cJSON structure is properly released.
     *
     * @param c A pointer to the cJSON structure to be deleted. This structure and its children will be recursively freed.
     * @return This function does not return a value.
     */

  0.493  >::pool_free                             — Returns the number of free objects in the pool.
    /**
     * @fn static unsigned int Pooled< T >::pool_free()
     *
     * @brief Returns the number of free objects in the pool.
     *
     * @details This static function provides the current count of free objects available in the pool by accessing the static free list. It is useful for monitoring the pool's capacity and understanding how many objects are available for allocation without creating new ones.
     *
     * @return The number of free objects currently available in the pool, represented as an unsigned integer.
     */

  0.480  CACHE_SIZE                              
    /**
     * @def CACHE_SIZE
     *
     */

  0.469  >::free_list                             — Provides access to a static list of free objects of type T.
    /**
     * @fn static std::vector< T * > & Pooled< T >::free_list()
     *
     * @brief Provides access to a static list of free objects of type T.
     *
     * @details This function returns a reference to a static vector that holds pointers to objects of type T. The vector is intended to be used as a free list, which can store and manage unused objects for reuse, thereby optimizing memory usage by avoiding frequent allocations and deallocations.
     *
     * @return A reference to a static vector containing pointers to objects of type T, representing the free list.
     */

  0.455  cJSON_New_Item                           — Creates a new cJSON item.
    /**
     * @fn static cJSON * cJSON_New_Item(void)
     *
     * @brief Creates a new cJSON item.
     *
     * @details This function allocates memory for a new cJSON item and initializes it to zero. It is an internal constructor used to create a new node in a JSON tree structure.
     *
     * @return A pointer to a newly allocated and zero-initialized cJSON item, or NULL if memory allocation fails.
     */

  0.439  >::remove                                — Marks the object pointed to by ptr as garbage.
    /**
     * @fn void GarbageCollectingList< T >::remove(T ptr)
     *
     * @brief Marks the object pointed to by ptr as garbage.
     *
     * @details This function calls the make_garbage() method on the object pointed to by ptr, effectively marking it for garbage collection or indicating that it is no longer in use. The function assumes that ptr is a valid pointer to an object that implements the make_garbage() method.
     *
     * @param ptr A pointer to an object that has a make_garbage() method.
     * @return This function does not return a value.
     */

  0.439  cJSON_CreateObject                       — Creates a new cJSON object.
    /**
     * @fn cJSON * cJSON_CreateObject(void)
     *
     * @brief Creates a new cJSON object.
     *
     * @details This function allocates and initializes a new cJSON item representing a JSON object. It uses cJSON_New_Item to allocate memory for the item and sets its type to cJSON_Object. If memory allocation fails, the function returns NULL.
     *
     * @return A pointer to a newly allocated cJSON object, or NULL if memory allocation fails.
     */

  0.427  GET_CACHE                               
    /**
     * @def GET_CACHE
     *
     */

  0.410  >::delete_garbage                        — Removes and deletes garbage objects from a container.
    /**
     * @fn void GarbageCollectingList< T >::delete_garbage()
     *
     * @brief Removes and deletes garbage objects from a container.
     *
     * @details This function iterates through a container of pointers, checking each object to determine if it is considered 'garbage' by calling the is_garbage() method on each object. If an object is identified as garbage, it is deleted, and the corresponding pointer is removed from the container. The function ensures that only non-garbage objects remain in the container after execution.
     *
     * @return This function does not return a value.
     */

  0.389  Garbage::is_garbage                      — Checks if the object is marked as garbage.
    /**
     * @fn bool Garbage::is_garbage() const
     *
     * @brief Checks if the object is marked as garbage.
     *
     * @details This function returns a boolean value indicating whether the object is considered garbage. It checks the internal state of the object by returning the value of the private member variable '_garbage'. This function does not modify any state and can be used to determine if the object should be discarded or ignored.
     *
     * @return A boolean value where 'true' indicates the object is marked as garbage, and 'false' indicates it is not.
     */

  0.388  >::add                                   — Adds an element to the front of the container and marks it as not garb
    /**
     * @fn void GarbageCollectingList< T >::add(T ptr)
     *
     * @brief Adds an element to the front of the container and marks it as not garbage.
     *
     * @details This function inserts the given pointer 'ptr' at the front of the container. After insertion, it calls the 'not_garbage' method on the object pointed to by 'ptr' to mark it as active or valid. This function assumes that 'ptr' is a valid pointer and that the object it points to has a 'not_garbage' method.
     *
     * @param ptr A pointer to the object to be added to the container. The object must have a 'not_garbage' method.
     * @return This function does not return a value.
     */

  0.362  cJSON_CreateNumber                       — Creates a cJSON item representing a number.
    /**
     * @fn cJSON * cJSON_CreateNumber(double num)
     *
     * @brief Creates a cJSON item representing a number.
     *
     * @details This function allocates and initializes a new cJSON item to represent a numeric value. It sets the type of the item to cJSON_Number and assigns the provided double value to both the valuedouble and valueint fields of the cJSON structure. The valueint field is set to the integer part of the double value.
     *
     * @param num The numeric value to be stored in the cJSON item.
     * @return A pointer to a newly created cJSON item representing the number, or NULL if memory allocation fails.
     */

  0.354  cJSON_CreateArray                        — Creates a new cJSON array item.
    /**
     * @fn cJSON * cJSON_CreateArray(void)
     *
     * @brief Creates a new cJSON array item.
     *
     * @details This function allocates and initializes a new cJSON item representing a JSON array. It uses cJSON_New_Item to allocate memory for the new item and sets its type to cJSON_Array. If memory allocation fails, the function returns NULL.
     *
     * @return A pointer to a newly allocated cJSON array item, or NULL if memory allocation fails.
     */

  0.340  cJSON_CreateString                       — Creates a cJSON string item from a C-style string.
    /**
     * @fn cJSON * cJSON_CreateString(const char *string)
     *
     * @brief Creates a cJSON string item from a C-style string.
     *
     * @details This function allocates and initializes a new cJSON item of type string. It duplicates the input C-style string and assigns it to the cJSON item. If memory allocation for the cJSON item or the string duplication fails, the function cleans up any allocated resources and returns NULL.
     *
     * @param string The C-style string to be duplicated and stored in the cJSON item.
     * @return A pointer to a newly created cJSON string item, or NULL if memory allocation fails.
     */

  0.306  cJSON_CreateIntArray                     — Creates a cJSON array from an array of integers.
    /**
     * @fn cJSON * cJSON_CreateIntArray(const int *numbers, int count)
     *
     * @brief Creates a cJSON array from an array of integers.
     *
     * @details This function takes an array of integers and creates a cJSON array, where each integer is represented as a cJSON number item. It iterates over the input array, creating a cJSON number for each integer and appending it to the cJSON array. If memory allocation fails at any point, the function deletes any allocated cJSON items and returns NULL.
     *
     * @param numbers A pointer to the first element of an array of integers to be converted into a cJSON array.
     * @param count The number of integers in the array to be included in the cJSON array.
     * @return A pointer to a cJSON array containing the integer elements, or NULL if memory allocation fails.
     */

  0.305  ensure                                   — Ensures the printbuffer has enough space for additional data.
    /**
     * @fn static char * ensure(printbuffer *p, int needed)
     *
     * @brief Ensures the printbuffer has enough space for additional data.
     *
     * @details This function checks if the printbuffer 'p' has enough space to accommodate 'needed' additional bytes. If the current buffer is insufficient, it allocates a new buffer with a size that is the smallest power of two greater than or equal to the required size. The existing data is copied to the new buffer, and the old buffer is freed. The function updates the buffer pointer and its length in the printbuffer structure.
     *
     * @param p A pointer to the printbuffer structure that contains the buffer and its metadata.
     * @param needed The number of additional bytes required in the buffer.
     * @return A pointer to the location in the buffer where new data can be written, or null if the buffer could not be allocated.
     */


================================================================================
[utility] arg_parsing  (stability: stable)
  desc: Command-line argument tokenisation: splitting player input into tokens with quote-delimited and dot-notation handling, e…
  locked: 14 functions, 8 with embeddings
  sim to desc — mean: 0.422  min: 0.336  max: 0.496
  ⚠ missing from pool: _entity_argument, _mult_argument, _number_argument, _one_argument, check_parse_name, swearcheck

  0.496  one_argument                             — Extracts the first argument from a String and returns the remainder.
    /**
     * @fn const char * one_argument(const String &argument, String &arg)
     *
     * @brief Extracts the first argument from a String and returns the remainder.
     *
     * @details This function takes a String object containing a sequence of arguments and extracts the first argument, storing it in the provided String reference 'arg'. It handles quoted arguments correctly. The function returns a pointer to the remainder of the input string after the first argument has been extracted, with leading whitespace removed.
     *
     * @param argument The input String from which the first argument is to be extracted.
     * @param arg A reference to a String where the extracted first argument will be stored.
     * @return A pointer to the remainder of the input string after the first argument has been extracted, with leading whitespace removed.
     */

  0.488  number_argument                          — Extracts a numeric prefix from a String and returns the number and rem
    /**
     * @fn int number_argument(const String &argument, String &arg)
     *
     * @brief Extracts a numeric prefix from a String and returns the number and remaining suffix.
     *
     * @details Extracts a numeric prefix from a String and returns the number and the remaining string.
    This function takes an input String expected to contain a numeric prefix followed by a dot and a suffix. It extracts the numeric prefix, converts it to an integer, and assigns the remaining suffix to the provided String reference. If no valid numeric prefix is found, it defaults to returning 1.
     *
     * @param argument The input String expected to contain a numeric prefix followed by a dot and a suffix.
     * @param arg A String reference where the suffix of the input string will be copied after the numeric prefix and dot.
     * @return The numeric value extracted from the prefix of the input string, or 1 if no valid numeric prefix is found.
     */

  0.486  entity_argument                          — Parses an entity type from a string argument and modifies the argument
    /**
     * @fn Flags::Bit entity_argument(const String &argument, String &arg)
     *
     * @brief Parses an entity type from a string argument and modifies the argument.
     *
     * @details This function takes a String object representing an input argument and parses it to identify an entity type or variant. The identified entity type is returned as a Flags::Bit enumeration value. The function also modifies the provided output String reference to exclude the entity type or variant prefix, effectively storing the remaining part of the argument. It internally uses a character buffer to facilitate this operation.
     *
     * @param argument A constant reference to a String object containing the input string with the entity type and possibly a numeric prefix.
     * @param arg A reference to a String object where the modified argument, excluding the entity type or variant prefix, will be stored.
     * @return A Flags::Bit enumeration value representing the identified entity type or variant type from the argument.
     */

  0.457  mult_argument                            — Parses a String to extract a number and a substring after a '*' charac
    /**
     * @fn int mult_argument(const String &argument, String &arg)
     *
     * @brief Parses a String to extract a number and a substring after a '*' character.
     *
     * @details This function takes a String object containing an input in the format 'number*substring'. It extracts the integer number before the '*' character and assigns the substring after '*' to the provided String reference 'arg'. If no '*' is present, the entire input is treated as a number and 'arg' is set to an empty string.
     *
     * @param argument A String object containing the input to be parsed.
     * @param arg A reference to a String where the substring after '*' will be stored.
     * @return The integer value of the number before the '*' character, or 1 if no '*' is present.
     */

  0.393  one_keyword                              — Extracts a single keyword from a string of keywords.
    /**
     * @fn const char * one_keyword(const char *keywords, char *word)
     *
     * @brief Extracts a single keyword from a string of keywords.
     *
     * @details This function extracts the next keyword from a given string of keywords, skipping any leading whitespace and ignoring characters enclosed in single or double quotes. The extracted keyword is copied into the provided buffer 'word', and the function returns a pointer to the position in the original string immediately following the extracted keyword. The function also skips any trailing whitespace after the keyword.
     *
     * @param keywords A pointer to a null-terminated string containing the keywords.
     * @param word A pointer to a buffer where the extracted keyword will be stored.
     * @return A pointer to the position in the 'keywords' string immediately after the extracted keyword, with any trailing whitespace skipped.
     */

  0.379  help_char_search                         — Searches for help entries matching a keyword and sends the results to 
    /**
     * @fn void help_char_search(Character *ch, const String &arg)
     *
     * @brief Searches for help entries matching a keyword and sends the results to a character.
     *
     * @details The function performs a search for help entries in the database that match the specified keyword argument. It constructs a SQL query to find entries with keywords that match or contain the provided argument. The results are formatted and sent to the character's output buffer. If no entries are found, a message is sent to inform the character. The function handles SQL query execution and result processing, ensuring that only entries with keywords containing the argument are considered.
     *
     * @param ch A pointer to the Character object representing the recipient of the help search results.
     * @param arg A constant reference to a String object representing the keyword to search for in help entries.
     * @return This function does not return a value.
     */

  0.339  String::has_words                        — Determines if all words in a given wordlist are present in the current
    /**
     * @fn bool String::has_words(const String &wordlist, bool exact=false) const
     *
     * @brief Determines if all words in a given wordlist are present in the current String.
     *
     * @details The function checks if each word in the provided 'wordlist' is present in the current String object. It first removes specified leading and trailing characters from both the current String and the 'wordlist'. The function then parses the 'wordlist' to extract individual words, handling quoted strings appropriately. For each word, it checks if it is present in the current String. If 'exact' is true, the words must match exactly; otherwise, the words in the 'wordlist' can be prefixes of words in the current String. The function returns true only if all words in the 'wordlist' are found in the current String.
     *
     * @param wordlist A String object containing the list of words to be checked against the current String.
     * @param exact A boolean flag indicating whether the words in the 'wordlist' must match exactly (true) or can be prefixes (false).
     * @return Returns true if all words in 'wordlist' are found in the current String according to the 'exact' matching criteria; otherwise, returns false.
     */

  0.336  String::has_exact_words                  — Checks if all words in the given wordlist are present in the current S
    /**
     * @fn bool String::has_exact_words(const String &wordlist) const
     *
     * @brief Checks if all words in the given wordlist are present in the current String with exact matching.
     *
     * @details This function determines whether all the words contained in the provided 'wordlist' String are present in the current String object. It uses exact matching, meaning each word in the 'wordlist' must match exactly with words in the current String, without considering prefixes or partial matches.
     *
     * @param wordlist A String object containing the list of words to be checked against the current String.
     * @return Returns true if all words in 'wordlist' are found in the current String with exact matching; otherwise, returns false.
     */


================================================================================
[utility] string_ops  (stability: stable)
  desc: String manipulation utilities: case conversion, trimming and stripping, substring extraction and search, prefix/infix/su…
  locked: 41 functions, 41 with embeddings
  sim to desc — mean: 0.438  min: 0.325  max: 0.550

  0.550  makedrunk                                — Transforms a string to simulate drunken speech based on the character'
    /**
     * @fn String makedrunk(Character *ch, const String &string)
     *
     * @brief Transforms a string to simulate drunken speech based on the character's drunkenness level.
     *
     * @details The function 'makedrunk' takes a character and a string as input and returns a modified version of the string that simulates how the character would speak if they were drunk. If the character is an NPC or their drunkenness level is 10 or below, the original string is returned unchanged. Otherwise, the function alters the string by replacing certain characters with random replacements based on the character's drunkenness level. The replacements are defined in a static structure that specifies how each letter can be altered. Numbers in the string are randomly changed to other digits.
     *
     * @param ch A pointer to the Character object whose drunkenness level influences the transformation.
     * @param string The input string to be transformed into drunken speech.
     * @return A String object representing the transformed version of the input string, simulating drunken speech.
     */

  0.528  String::capitalize                       — Capitalizes the first alphanumeric character of the string.
    /**
     * @fn const String String::capitalize() const
     *
     * @brief Capitalizes the first alphanumeric character of the string.
     *
     * @details This function creates a copy of the current string and capitalizes the first alphanumeric character found, skipping any leading whitespace or non-alphanumeric characters. The function does not modify the original string and returns a new string with the modification applied.
     *
     * @return A new string with the first alphanumeric character capitalized, if any.
     */

  0.513  strcasecmp                               — Performs a case-insensitive comparison of two String objects.
    /**
     * @fn int strcasecmp(const String &astr, const String &bstr)
     *
     * @brief Performs a case-insensitive comparison of two String objects.
     *
     * @details This function compares two String objects in a case-insensitive manner by converting them to C-style strings and using the standard strcasecmp function. It effectively extends the functionality of std::string to allow for case-insensitive comparisons, leveraging the additional capabilities of the custom String class.
     *
     * @param astr The first String object to be compared.
     * @param bstr The second String object to be compared.
     * @return An integer less than, equal to, or greater than zero if astr is found, respectively, to be less than, to match, or be greater than bstr, ignoring case.
     */

  0.509  String::replace                          — Replaces some or all occurrences of a substring with another substring
    /**
     * @fn const String String::replace(const String &what, const String &with, int times=-1) const
     *
     * @brief Replaces some or all occurrences of a substring with another substring.
     *
     * @details This function creates a new string by replacing occurrences of the specified substring 'what' with the substring 'with'. The number of replacements is controlled by the 'times' parameter. If 'times' is -1, all occurrences are replaced. The search for 'what' starts from the beginning of the string and proceeds forward. If 'what' is an empty string, the function returns the original string unchanged.
     *
     * @param what The substring to be replaced within the current string.
     * @param with The substring to replace 'what' with.
     * @param times The maximum number of replacements to perform. If -1, all occurrences are replaced.
     * @return A new String object with the specified replacements made.
     */

  0.492  String::lowercase                        — Converts the string to lowercase.
    /**
     * @fn const String String::lowercase() const
     *
     * @brief Converts the string to lowercase.
     *
     * @details This function creates a new string that is a lowercase version of the original string. It iterates over each character of the string, and if the character is an uppercase letter, it converts it to its lowercase equivalent using the tolower function. The function does not modify the original string and returns a new string with all characters converted to lowercase.
     *
     * @return A new String object that is the lowercase version of the original string.
     */

  0.488  String::lstrip                           — Removes specified characters from the beginning of the String.
    /**
     * @fn const String String::lstrip(const String &chars=" \t\n\r") const
     *
     * @brief Removes specified characters from the beginning of the String.
     *
     * @details The lstrip function removes all leading characters from the current String object that are present in the provided 'chars' String. It searches for the first character not in 'chars' and returns a substring starting from that position to the end of the String. If all characters are stripped, it returns an empty String.
     *
     * @param chars A String containing characters to be removed from the start of the current String.
     * @return A new String object with the specified leading characters removed.
     */

  0.481  String::substr                           — Extracts a substring from the current String object.
    /**
     * @fn const String String::substr(std::size_t pos=0, std::size_t count=npos) const
     *
     * @brief Extracts a substring from the current String object.
     *
     * @details This function returns a new String object that represents a substring of the current String. The substring starts at the specified position 'pos' and spans 'count' characters. The original String object remains unchanged, adhering to the immutable paradigm.
     *
     * @param pos The starting position of the substring within the current String.
     * @param count The number of characters to include in the substring.
     * @return A new String object containing the specified substring.
     */

  0.481  String::has_infix                        — Determines if the current string is an infix of another string with a 
    /**
     * @fn bool String::has_infix(const String &str, std::size_t min_chars=1) const
     *
     * @brief Determines if the current string is an infix of another string with a minimum character constraint.
     *
     * @details This function checks whether the current string is an infix of the provided 'str' object, given that both strings have at least 'min_chars' characters. It utilizes the 'is_infix_of' method of the 'String' class to perform this check. The function is useful for determining substring relationships with additional constraints on string length.
     *
     * @param str The string in which to search for the current string as an infix.
     * @param min_chars The minimum number of characters that both the current string and 'str' must have for the search to proceed.
     * @return Returns true if the current string is an infix of 'str' and both strings meet the minimum character requirement; otherwise, returns false.
     */

  0.480  String::find                             — Finds the first occurrence of a substring starting from a given positi
    /**
     * @fn std::size_t String::find(const String &str, std::size_t start_pos=0) const
     *
     * @brief Finds the first occurrence of a substring starting from a given position.
     *
     * @details This function searches for the first occurrence of the specified substring 'str' within the current string, starting the search from the position 'start_pos'. The search is case-insensitive. If the substring is found, the function returns the position of the first character of the first occurrence. If the substring is not found, or if 'start_pos' is beyond the possible starting positions for a match, the function returns std::string::npos.
     *
     * @param str The substring to search for within the current string.
     * @param start_pos The position in the current string from which to start the search.
     * @return The position of the first character of the first occurrence of the substring, or std::string::npos if the substring is not found.
     */

  0.476  ordinal_string                           — Converts an integer to its corresponding ordinal string representation
    /**
     * @fn char * ordinal_string(int n)
     *
     * @brief Converts an integer to its corresponding ordinal string representation.
     *
     * @details This function takes an integer 'n' and returns a string representing the ordinal form of the number. For example, 1 becomes 'first', 2 becomes 'second', 3 becomes 'third', and numbers ending in 1, 2, or 3 (except for 11, 12, 13) are suffixed with 'st', 'nd', or 'rd', respectively. All other numbers are suffixed with 'th'. The returned string may come from a static buffer, so it should be copied before the function is called again to avoid overwriting.
     *
     * @param n The integer to be converted to its ordinal string representation.
     * @return A pointer to a character array containing the ordinal string representation of the input integer.
     */

  0.475  cJSON_strcasecmp                         — Performs a case-insensitive comparison of two strings.
    /**
     * @fn static int cJSON_strcasecmp(const char *s1, const char *s2)
     *
     * @brief Performs a case-insensitive comparison of two strings.
     *
     * @details This function compares two strings, s1 and s2, in a case-insensitive manner. It iterates over each character of the strings, converting them to lowercase, and compares them. The comparison stops when a difference is found or the end of the strings is reached. If both strings are identical in a case-insensitive manner, the function returns 0.
     *
     * @param s1 The first string to be compared.
     * @param s2 The second string to be compared.
     * @return Returns 0 if the strings are equal ignoring case, a negative value if s1 is less than s2, or a positive value if s1 is greater than s2.
     */

  0.474  String::is_prefix_of                     — Checks if the current String is a prefix of another String.
    /**
     * @fn bool String::is_prefix_of(const String &str, std::size_t min_chars=1) const
     *
     * @brief Checks if the current String is a prefix of another String.
     *
     * @details This function determines whether the current String object is a prefix of the given String 'str'. It requires that the current String has at least 'min_chars' characters. The function returns true if the current String matches the beginning of 'str' up to its own length, and both Strings meet the minimum character requirement.
     *
     * @param str The String object to compare against.
     * @param min_chars The minimum number of characters that the current String must have to be considered a prefix.
     * @return Returns true if the current String is a prefix of 'str' and both Strings meet the minimum character requirement; otherwise, returns false.
     */

  0.473  strncmp                                  — Performs a case-sensitive comparison of two String objects up to a spe
    /**
     * @fn int strncmp(const String &astr, const String &bstr, size_t n)
     *
     * @brief Performs a case-sensitive comparison of two String objects up to a specified number of characters.
     *
     * @details This function compares up to 'n' characters of two String objects, 'astr' and 'bstr', in a case-sensitive manner. It utilizes the standard library function std::strncmp to perform the comparison on the underlying C-style strings of the String objects. The function is useful for determining the lexicographical order of the strings or checking for equality up to a certain length.
     *
     * @param astr The first String object to be compared.
     * @param bstr The second String object to be compared.
     * @param n The maximum number of characters to compare.
     * @return An integer less than, equal to, or greater than zero if 'astr' is found, respectively, to be less than, to match, or be greater than 'bstr'.
     */

  0.471  parse_deity                              — Parses a string to find the index of a deity name.
    /**
     * @fn int parse_deity(const String &dstring)
     *
     * @brief Parses a string to find the index of a deity name.
     *
     * @details Parses a string to find a valid deity index.
    This function takes a String object representing a deity name, removes any color codes, and searches for the first occurrence of this name in the deity_table. If the name is found, it returns the index of the deity in the table. If the string is empty or the name is not found, it returns -1.
     *
     * @param dstring The input string representing a deity, which may contain color codes.
     * @return The index of the deity in the deity table if found, otherwise -1.
     */

  0.469  String::has_suffix                       — Determines if the current String is a suffix of another String.
    /**
     * @fn bool String::has_suffix(const String &str, std::size_t min_chars=1) const
     *
     * @brief Determines if the current String is a suffix of another String.
     *
     * @details This function checks whether the current String object is a suffix of the provided String object 'str'. It also ensures that the current String has at least 'min_chars' characters to be considered a valid suffix. The function utilizes the 'is_suffix_of' method of the 'String' class to perform this check.
     *
     * @param str The String object to check against for a suffix match.
     * @param min_chars The minimum number of characters the current String must have to be considered as a potential suffix.
     * @return Returns true if the current String is a suffix of 'str' and meets the minimum character requirement; otherwise, returns false.
     */

  0.465  strlen                                   — Calculates the length of a given string.
    /**
     * @fn size_t strlen(const String &str)
     *
     * @brief Calculates the length of a given string.
     *
     * @details This function returns the number of characters in the provided String object by calling its size() method. It is an inline function, which suggests that it is intended for use in performance-critical code where function call overhead should be minimized.
     *
     * @param str The String object whose length is to be calculated.
     * @return The length of the string, represented as a size_t, which is the number of characters in the String object.
     */

  0.457  String::is_suffix_of                     — Checks if the current String is a suffix of the given String.
    /**
     * @fn bool String::is_suffix_of(const String &str, std::size_t min_chars=1) const
     *
     * @brief Checks if the current String is a suffix of the given String.
     *
     * @details This function determines whether the current String object is a suffix of the specified String object 'str'. It requires that the current String is not shorter than 'min_chars' and that 'str' is at least as long as the current String. If these conditions are met, it checks if the current String matches the end of 'str'.
     *
     * @param str The String object to check against for a suffix match.
     * @param min_chars The minimum number of characters the current String must have to be considered as a potential suffix.
     * @return Returns true if the current String is a suffix of 'str' and meets the minimum character requirement; otherwise, returns false.
     */

  0.456  String::rstrip                           — Removes trailing characters from the String.
    /**
     * @fn const String String::rstrip(const String &chars=" \t\n\r") const
     *
     * @brief Removes trailing characters from the String.
     *
     * @details This function returns a new String object with all trailing characters that are present in the 'chars' parameter removed from the current String object. It searches from the end of the String and stops at the first character not in 'chars'.
     *
     * @param chars A String containing characters to be removed from the end of the current String.
     * @return A new String object with the trailing characters specified in 'chars' removed.
     */

  0.454  String::is_infix_of                      — Checks if the current string is an infix of the given string with a mi
    /**
     * @fn bool String::is_infix_of(const String &str, std::size_t min_chars=1) const
     *
     * @brief Checks if the current string is an infix of the given string with a minimum character constraint.
     *
     * @details This function determines whether the current string is a substring (infix) of the provided string 'str', starting the search from the beginning of 'str'. It also ensures that both the current string and 'str' meet a minimum character length requirement specified by 'min_chars'. If the current string is shorter than 'min_chars' or if 'str' is shorter than the current string, the function immediately returns false. Otherwise, it checks if the current string is found within 'str'.
     *
     * @param str The string in which to search for the current string as an infix.
     * @param min_chars The minimum number of characters that both the current string and 'str' must have for the search to proceed.
     * @return Returns true if the current string is an infix of 'str' and both strings meet the minimum character requirement; otherwise, returns false.
     */

  0.454  atoi                                     — Converts a String object to an integer.
    /**
     * @fn int atoi(const String &astr)
     *
     * @brief Converts a String object to an integer.
     *
     * @details This function takes a String object, extracts its C-style string representation using c_str(), and converts it to an integer using the standard atoi function. It is useful for converting numeric strings stored in a String object to integer values.
     *
     * @param astr The String object containing the numeric string to be converted.
     * @return The integer value obtained by converting the numeric string contained in the String object.
     */

  0.451  parse_hex4                               — Parses a 4-character hexadecimal string into an unsigned integer.
    /**
     * @fn static unsigned parse_hex4(const char *str)
     *
     * @brief Parses a 4-character hexadecimal string into an unsigned integer.
     *
     * @details This function takes a pointer to a string representing a 4-character hexadecimal number and converts it into an unsigned integer. The string should contain only valid hexadecimal digits (0-9, A-F, a-f). If the string contains any invalid characters, the function returns 0.
     *
     * @param str A pointer to a null-terminated string containing exactly 4 hexadecimal characters.
     * @return The unsigned integer value of the 4-character hexadecimal string, or 0 if the string contains invalid characters.
     */

  0.447  String::strip                            — Removes specified characters from both the beginning and end of the St
    /**
     * @fn const String String::strip(const String &chars=" \t\n\r") const
     *
     * @brief Removes specified characters from both the beginning and end of the String.
     *
     * @details The strip function creates a new String object by removing all characters specified in the 'chars' parameter from both the start and end of the current String. It first applies the lstrip function to remove leading characters and then applies the rstrip function to remove trailing characters. This function is useful for cleaning up strings by removing unwanted characters from both ends.
     *
     * @param chars A String containing characters to be removed from both the start and end of the current String.
     * @return A new String object with the specified leading and trailing characters removed.
     */

  0.439  String::center                           — Centers the string within a specified total length using whitespace.
    /**
     * @fn const String String::center(std::size_t total_len) const
     *
     * @brief Centers the string within a specified total length using whitespace.
     *
     * @details This function centers the current String object within a given total length by adding whitespace on both sides. If the uncolored size of the string exceeds the specified total length, the string is truncated from the end until it fits. The function ignores any color formatting when calculating the size for centering.
     *
     * @param total_len The total length within which the string should be centered, including whitespace.
     * @return A new String object that represents the original string centered within the specified total length using whitespace.
     */

  0.435  strstr                                   — Finds the first occurrence of a substring within a string.
    /**
     * @fn const char * strstr(const String &astr, const String &bstr)
     *
     * @brief Finds the first occurrence of a substring within a string.
     *
     * @details This function searches for the first occurrence of the substring represented by 'bstr' within the string represented by 'astr'. It utilizes the C-style std::strstr function by converting the String objects to C-style strings using the c_str() method.
     *
     * @param astr The string in which to search for the substring.
     * @param bstr The substring to search for within 'astr'.
     * @return A pointer to the first occurrence of 'bstr' within 'astr', or nullptr if 'bstr' is not found.
     */

  0.431  String::lsplit                           — Splits the string at the first occurrence of any character in the give
    /**
     * @fn const String String::lsplit(const String &chars=" ") const
     *
     * @brief Splits the string at the first occurrence of any character in the given set.
     *
     * @details This function searches the string for the first occurrence of any character from the provided 'chars' string. It splits the original string at this position. The portion before the split is returned as a new String object. If the original string starts with any character from 'chars', those characters are trimmed from the beginning, and the function returns the first word found after the trim. The remainder of the string after the split is stored in the provided reference String.
     *
     * @param chars A String containing the set of characters to split the original string on.
     * @return A String containing the first word found before the split point.
     */

  0.431  strcmp                                   — Compares two strings for lexicographical order.
    /**
     * @fn int strcmp(const String &astr, const String &bstr)
     *
     * @brief Compares two strings for lexicographical order.
     *
     * @details This function compares two String objects by converting them to C-style strings using the c_str() method and then using the standard library function std::strcmp to perform the comparison. It returns an integer indicating the relationship between the two strings: negative if the first string is less than the second, zero if they are equal, and positive if the first string is greater than the second.
     *
     * @param astr The first String object to compare.
     * @param bstr The second String object to compare.
     * @return An integer less than, equal to, or greater than zero if astr is found, respectively, to be less than, to match, or be greater than bstr.
     */

  0.428  String::has_prefix                       — Determines if the current String has the specified String as a prefix.
    /**
     * @fn bool String::has_prefix(const String &str, std::size_t min_chars=1) const
     *
     * @brief Determines if the current String has the specified String as a prefix.
     *
     * @details This function checks if the current String object is a prefix of the given String 'str'. It utilizes the 'is_prefix_of' method of the String class to perform this check. The function requires that both the current String and the 'str' have at least 'min_chars' characters to be considered for the prefix check. If the current String is a prefix of 'str' and both Strings meet the minimum character requirement, the function returns true; otherwise, it returns false.
     *
     * @param str The String object to compare against to determine if it is a prefix.
     * @param min_chars The minimum number of characters that both Strings must have to be considered for the prefix check.
     * @return Returns true if the current String is a prefix of 'str' and both Strings meet the minimum character requirement; otherwise, returns false.
     */

  0.418  String::erase                            — Erases a portion of the string, ignoring out-of-bounds positions.
    /**
     * @fn String & String::erase(size_t pos=0, size_t len=npos)
     *
     * @brief Erases a portion of the string, ignoring out-of-bounds positions.
     *
     * @details This function attempts to erase a substring from the current String object starting at the specified position 'pos' and spanning 'len' characters. If 'pos' is greater than or equal to the size of the string, the function does nothing, thus preventing out-of-bounds errors. This provides a convenient way to erase parts of the string without manually checking bounds.
     *
     * @param pos The starting position from which to begin erasing characters.
     * @param len The number of characters to erase from the string.
     * @return Returns a reference to the modified String object.
     */

  0.413  String::uncolor                          — Removes color codes from the string.
    /**
     * @fn const String String::uncolor() const
     *
     * @brief Removes color codes from the string.
     *
     * @details This function iterates over the characters of the string and constructs a new string by excluding color codes. A color code is identified by a pair of curly braces '{}'. If a single '{' is encountered, it checks the next character. If the next character is also '{', it adds a single '{' to the result. Otherwise, it skips the characters inside the braces, effectively removing the color code.
     *
     * @return A new String object with all color codes removed.
     */

  0.408  strchr                                   — Finds the first occurrence of a character in a string.
    /**
     * @fn const char * strchr(const String &str, int ch)
     *
     * @brief Finds the first occurrence of a character in a string.
     *
     * @details This function searches for the first occurrence of the character 'ch' in the given String object 'str'. It utilizes the standard C library function std::strchr to perform the search on the underlying C-style string of the String object.
     *
     * @param str The String object in which to search for the character.
     * @param ch The character to locate within the string.
     * @return A pointer to the first occurrence of the character in the string, or nullptr if the character is not found.
     */

  0.395  Format::sprintf                          — Formats and stores a series of characters and values in a buffer.
    /**
     * @fn int Format::sprintf(char *buf, const String &fmt, Params &&... params)
     *
     * @brief Formats and stores a series of characters and values in a buffer.
     *
     * @details This function formats a string according to the specified format and stores the result in the provided buffer. It uses the C++ standard library's std::sprintf function to perform the formatting. The format string is passed as a String object, and the function supports a variadic number of parameters, which are forwarded using Format::to_c to preserve their value categories. This allows both lvalues and rvalues to be correctly formatted and inserted into the resulting string.
     *
     * @param buf A pointer to the character array where the formatted string will be stored.
     * @param fmt A constant reference to a String object that specifies the format of the output.
     * @param params A variadic template parameter pack representing the values to be formatted according to the format string.
     * @return The number of characters written to the buffer, excluding the null terminator.
     */

  0.384  String::insert                           — Inserts a string at a specified position within the current String obj
    /**
     * @fn const String String::insert(const String &what, std::size_t pos) const
     *
     * @brief Inserts a string at a specified position within the current String object.
     *
     * @details This function inserts the given string 'what' into the current String object at the specified position 'pos'. If 'pos' is greater than the size of the current String, the insertion occurs at the end of the String. The function returns a new String object with the inserted content.
     *
     * @param what The String object to be inserted.
     * @param pos The position within the current String where the insertion should occur.
     * @return A new String object containing the original content with 'what' inserted at the specified position.
     */

  0.382  String::find_nth                         — Finds the nth occurrence of a substring starting from a given position
    /**
     * @fn std::size_t String::find_nth(std::size_t nth, const String &str, std::size_t start_pos=0) const
     *
     * @brief Finds the nth occurrence of a substring starting from a given position.
     *
     * @details This function searches for the nth occurrence of a specified substring within the current string, beginning the search from a given starting position. It uses a recursive approach to find each subsequent occurrence by adjusting the starting position after each successful find. If the nth occurrence is found, the position of its first character is returned. If the substring does not occur nth times, the function returns std::string::npos.
     *
     * @param nth The occurrence number of the substring to find.
     * @param str The substring to search for within the current string.
     * @param start_pos The position in the current string from which to start the search.
     * @return The position of the first character of the nth occurrence of the substring, or std::string::npos if the substring does not occur nth times.
     */

  0.379  strcat                                   — Concatenates a C-style string with a String object.
    /**
     * @fn char * strcat(char *dest, const String &src)
     *
     * @brief Concatenates a C-style string with a String object.
     *
     * @details This function appends the contents of a String object to a C-style string (char array). It uses the standard library function std::strcat to perform the concatenation. The destination string must have enough space to hold the resulting concatenated string, including the null terminator.
     *
     * @param dest A pointer to the destination C-style string where the contents of src will be appended.
     * @param src A String object whose contents will be appended to the destination string.
     * @return A pointer to the destination string, which now contains the concatenated result.
     */

  0.373  next_line                                — Finds the start of the next line in a string.
    /**
     * @fn static char * next_line(char *current_line)
     *
     * @brief Finds the start of the next line in a string.
     *
     * @details This function searches for the next newline character ('
    ') in the given string starting from 'current_line'. If a newline character is found, it returns a pointer to the character immediately following the newline. If no newline is found before the end of the string or the maximum string length, it returns the original 'current_line' pointer.
     *
     * @param current_line A pointer to the current position in the string from which to search for the next line.
     * @return A pointer to the start of the next line if a newline character is found, otherwise the original 'current_line' pointer.
     */

  0.368  strcpy                                   — Copies a C++ String object to a C-style string.
    /**
     * @fn char * strcpy(char *dest, const String &src)
     *
     * @brief Copies a C++ String object to a C-style string.
     *
     * @details This function copies the contents of a C++ String object into a C-style string (character array). It uses the standard library function std::strcpy to perform the copy operation. The destination buffer must be large enough to hold the contents of the source string, including the null terminator.
     *
     * @param dest A pointer to the destination character array where the content will be copied.
     * @param src A reference to the source String object whose content is to be copied.
     * @return A pointer to the destination character array (dest).
     */

  0.358  cJSON_strdup                             — Duplicates a string using dynamic memory allocation.
    /**
     * @fn static char * cJSON_strdup(const char *str)
     *
     * @brief Duplicates a string using dynamic memory allocation.
     *
     * @details This function creates a duplicate of the given C-style string by allocating memory for the copy and copying the contents of the original string into it. It uses cJSON_malloc to allocate memory and memcpy to perform the copy. The function ensures that the duplicated string is null-terminated.
     *
     * @param str The original C-style string to be duplicated.
     * @return A pointer to the newly allocated string that is a duplicate of the input string, or NULL if memory allocation fails.
     */

  0.356  skip                                     — Skips over whitespace and carriage return/line feed characters in a st
    /**
     * @fn static const char * skip(const char *in)
     *
     * @brief Skips over whitespace and carriage return/line feed characters in a string.
     *
     * @details This function takes a C-style string as input and advances the pointer past any leading whitespace characters, including spaces, tabs, carriage returns, and line feeds. It continues to increment the pointer until a non-whitespace character is encountered or the end of the string is reached. The function is useful for preprocessing strings to ignore leading whitespace.
     *
     * @param in A pointer to the input C-style string that needs to be processed.
     * @return A pointer to the first non-whitespace character in the input string, or a pointer to the null terminator if the string contains only whitespace.
     */

  0.345  String::is_number                        — Checks if the string is a numeric value.
    /**
     * @fn bool String::is_number() const
     *
     * @brief Checks if the string is a numeric value.
     *
     * @details This function determines whether the entire string represents a numeric value. It considers an optional leading '+' or '-' sign, followed by digits. If the string is empty or contains any non-digit characters (excluding the initial sign), the function returns false.
     *
     * @return Returns true if the string is a valid numeric value, otherwise returns false.
     */

  0.330  comp_groupnames                          — Compares group names for sorting purposes.
    /**
     * @fn int comp_groupnames(const void *gn1, const void *gn2)
     *
     * @brief Compares group names for sorting purposes.
     *
     * @details This function is used as a comparison function for qsort to sort group numbers based on their associated group names. It dereferences the integer pointers to access indices in the group_table array, retrieves the group names, and compares them using the strcmp function.
     *
     * @param gn1 A pointer to the first group number to compare, which is an index into the group_table array.
     * @param gn2 A pointer to the second group number to compare, which is an index into the group_table array.
     * @return An integer less than, equal to, or greater than zero if the group name at the index pointed to by gn1 is found, respectively, to be less than, to match, or be greater than the group name at the index pointed to by gn2.
     */

  0.325  dizzy_ctime                              — Converts a time_t value to a human-readable string representation.
    /**
     * @fn const char * dizzy_ctime(time_t *timep)
     *
     * @brief Converts a time_t value to a human-readable string representation.
     *
     * @details The function takes a pointer to a time_t object and converts it to a string representation of the local time. It formats the time into a fixed format string that includes the day of the week, month, day of the month, time, and year. The formatted string is stored in a static buffer and returned as a C-style string.
     *
     * @param timep A pointer to a time_t object representing the time to be converted.
     * @return A pointer to a static character buffer containing the formatted date and time string.
     */


================================================================================
[infrastructure] admin  (stability: stable)
  desc: Administrative and immortal utilities: bug and diagnostic logging (formatted and timestamped), broadcasting notification…
  locked: 10 functions, 10 with embeddings
  sim to desc — mean: 0.439  min: 0.291  max: 0.647

  0.647  config_immortal                          — Configures immortal options for a character based on provided argument
    /**
     * @fn void config_immortal(Character *ch, String argument)
     *
     * @brief Configures immortal options for a character based on provided arguments.
     *
     * @details The function config_immortal allows a character to configure their immortal options, such as 'immprefix' and 'immname'. When called without arguments, it displays the current settings. If 'help' or '?' is provided as an argument, it displays help information. The function processes specific options based on the argument provided, allowing the character to set or remove their 'immprefix' or 'immname'. The function handles input validation, such as ensuring the 'immprefix' includes the character's name and does not exceed a certain length.
     *
     * @param ch A pointer to the Character object whose immortal options are being configured.
     * @param argument A String containing the arguments specifying which immortal option to configure and any additional parameters.
     * @return This function does not return a value.
     */

  0.631  wiznet                                   — Broadcasts a message to all eligible immortal characters via the wizne
    /**
     * @fn void wiznet(const String &string, Character *ch, Object *obj, const Flags &flag, const Flags &flag_skip, int min_rank)
     *
     * @brief Broadcasts a message to all eligible immortal characters via the wiznet system.
     *
     * @details Dispatches a notification message to all eligible immortal characters with specific flags set, excluding certain flags and characters.
    The function iterates over all descriptors in the descriptor list and sends a message to those that meet specific criteria: the descriptor must be in the playing state, associated with an immortal character, have the WIZ_ON flag set, match any of the specified flags, not match any of the flags to be skipped, have a rank greater than or equal to the specified minimum rank, and not be the character specified by 'ch'. If the WIZ_PREFIX flag is set, a prefix is added to the message before it is sent.
     *
     * @param string The message content to be sent, possibly containing placeholders for dynamic content.
     * @param ch Pointer to the Character who initiated the message, excluded from receiving the message.
     * @param obj Object associated with the message context, used for substitution in the message.
     * @param flag Flags indicating the set of criteria characters must meet to receive the message.
     * @param flag_skip Flags indicating criteria that, if present, exclude characters from receiving the message.
     * @param min_rank Minimum rank level a character must have to receive the message.
     * @return This function has no return value; it performs side effects by dispatching messages to eligible characters.
     */

  0.474  config_wiznet                            — Configures the wiznet options for a character.
    /**
     * @fn void config_wiznet(Character *ch, String argument)
     *
     * @brief Configures the wiznet options for a character.
     *
     * @details This function allows a character to configure their wiznet options, which determine the types of notifications they receive. The function processes a command argument to toggle specific wiznet flags, display help information, or show the current status of wiznet options. It supports commands to turn wiznet on or off, display help, and list available options. The function also handles numeric and string-based flag selection.
     *
     * @param ch A pointer to the Character object whose wiznet options are being configured.
     * @param argument A String containing the command and arguments for configuring wiznet options.
     * @return This function does not return a value.
     */

  0.464  restore_char                             — Restores a character's health, mana, stamina, and removes specific neg
    /**
     * @fn void restore_char(Character *ch, Character *victim)
     *
     * @brief Restores a character's health, mana, stamina, and removes specific negative affects.
     *
     * @details This function removes various detrimental affects such as plague, poison, blindness, dirt kicking, fire breath, sleep, curse, and fear from the specified victim character. It then resets the victim's hit points, mana, and stamina to their maximum values, and updates the character's position accordingly. Finally, it sends a notification message to the victim indicating they have been restored, originating from the character 'ch'. This function performs all modifications as side effects without returning a value.
     *
     * @param ch Pointer to the Character object who is restoring the victim.
     * @param victim Pointer to the Character object who is being restored.
     * @return This function does not return a value; it performs in-place modifications and sends a notification message.
     */

  0.438  setgameinout                             — Sets or clears a game message for a specified player character based o
    /**
     * @fn void setgameinout(Character *ch, String argument, const String &entryexit, char flag)
     *
     * @brief Sets or clears a game message for a specified player character based on input arguments.
     *
     * @details This function processes input arguments to identify a target player character in the game world and assigns or clears a specific game message string related to game entry ('in') or exit ('out') events. It validates the target's existence, handles message length restrictions, and provides feedback to the initiating character. The function modifies the victim's pcdata->gamein or pcdata->gameout string depending on the flag ('I' for 'in', otherwise 'out'). If no message is provided, it clears the existing message. It also enforces a maximum message length of 70 characters after uncoloring. The function performs message dispatching to inform the actor of success or failure.
     *
     * @param ch Pointer to the Character object initiating the command.
     * @param argument String containing the command arguments, including target name and message.
     * @param entryexit String indicating whether the message is for 'in' or 'out' (e.g., 'entry' or 'exit').
     * @param flag Character flag ('I' for 'in', other characters for 'out') to determine which message string to modify.
     * @return This function has no return value; it performs side effects such as modifying player data and sending messages to characters.
     */

  0.415  Logging::bug                             — Reports a bug by logging a formatted message.
    /**
     * @fn void Logging::bug(const String &str, int param)
     *
     * @brief Reports a bug by logging a formatted message.
     *
     * @details This function formats a bug report message with a specified string and parameter, logs it with a timestamp, and sends it to a wizard notification system. The message is prefixed with '[*****] BUG: ' to indicate its nature as a bug report.
     *
     * @param str The String object containing the bug description to be reported.
     * @param param An integer parameter used in the formatting of the bug report message.
     * @return This function does not return a value.
     */

  0.372  Logging::bugf                            — Logs a formatted bug report message.
    /**
     * @fn void Logging::bugf(const String &fmt, Params... params)
     *
     * @brief Logs a formatted bug report message.
     *
     * @details The function 'bugf' formats a message using the provided format string and parameters, then logs it as a bug report with a default parameter of 0. It utilizes the 'Format::format' function to create the formatted message and 'Logging::bug' to report it.
     *
     * @param fmt A constant reference to a String object that specifies the format of the bug report message.
     * @param params A variadic list of parameters used to format the message according to the format string.
     * @return This function does not return a value.
     */

  0.357  act_bug                                  — Logs a formatted bug report message with specific variable and format 
    /**
     * @fn void act_bug(const String &var, char letter, const String fmt)
     *
     * @brief Logs a formatted bug report message with specific variable and format details.
     *
     * @details The function 'act_bug' logs a bug report message using the 'Logging::bugf' function. It formats the message to indicate a missing variable for a specific placeholder in a format string. The function ensures that any dollar signs ('$') in the format string are doubled to prevent unintended behavior in the logging system. The message includes the variable name, the placeholder character, and the modified format string.
     *
     * @param var The name of the variable that is missing, which will be included in the bug report message.
     * @param letter The character representing the placeholder in the format string that is missing a corresponding variable.
     * @param fmt The format string that is used to construct the bug report message. Dollar signs in this string are replaced with double dollar signs.
     * @return This function does not return a value.
     */

  0.299  Logging::logf                            — Logs a formatted message with a timestamp.
    /**
     * @fn void Logging::logf(const String &fmt, Params... params)
     *
     * @brief Logs a formatted message with a timestamp.
     *
     * @details This function formats a message using the specified format string and parameters, and then logs the formatted message with a timestamp to the standard error stream. It utilizes the Format::format function to create the formatted message and Logging::log to output it.
     *
     * @param fmt A constant reference to a String object that specifies the format of the output message.
     * @param params A variadic list of parameters to be used in the format string.
     * @return This function does not return a value.
     */

  0.291  Logging::log                             — Logs a string with a timestamp to the standard error stream.
    /**
     * @fn void Logging::log(const String &str)
     *
     * @brief Logs a string with a timestamp to the standard error stream.
     *
     * @details This function writes a given string to the standard error stream, prefixed with the current time. It formats the output as 'timestamp :: string', where 'timestamp' is the current time obtained from the system, and 'string' is the input parameter. The timestamp is formatted using the ctime function and the newline character at the end is replaced with a null terminator to ensure proper formatting. The formatted message is then written to the standard error stream using Format::fprintf.
     *
     * @param str The String object to be logged, representing the message or information to be output.
     * @return This function does not return a value.
     */


================================================================================
[utility] imaging  (stability: stable)
  desc: Bitmap image creation and I/O: loading and writing PNG files, querying image dimensions and per-pixel color channel valu…
  locked: 4 functions, 4 with embeddings
  sim to desc — mean: 0.441  min: 0.386  max: 0.538

  0.538  util::Image::load                        — Loads an image from a file in PNG format.
    /**
     * @fn bool util::Image::load(const String &filename)
     *
     * @brief Loads an image from a file in PNG format.
     *
     * @details This function attempts to load an image from the specified file, interpreting it as a PNG. It initializes the necessary PNG structures, reads the image information, and processes the image data to ensure it is in a consistent format (8-bit depth, RGBA). The function updates the image's width and height properties and allocates memory for storing the image data. If any step fails, the function returns false.
     *
     * @param filename The path to the PNG file to be loaded.
     * @return Returns true if the image is successfully loaded and processed, otherwise returns false.
     */

  0.451  util::Image::value                       — Retrieves the value of a specific color channel at a given position in
    /**
     * @fn unsigned int util::Image::value(Channel rgb, unsigned int x, unsigned int y) const
     *
     * @brief Retrieves the value of a specific color channel at a given position in the image.
     *
     * @details This function accesses the pixel data of an image to return the value of a specified color channel at the coordinates (x, y). It first checks if the image data is valid and if the coordinates are within the image bounds. If the data is invalid or the coordinates are out of bounds, it returns 0. Otherwise, it calculates the position in the data array and returns the value of the specified channel.
     *
     * @param rgb The color channel to retrieve, represented by util::Image::Channel.
     * @param x The x-coordinate of the pixel.
     * @param y The y-coordinate of the pixel.
     * @return The value of the specified color channel at the given coordinates, or 0 if the coordinates are out of bounds or the image data is invalid.
     */

  0.390  util::Image::height                      — Retrieves the height value.
    /**
     * @fn unsigned int util::Image::height() const
     *
     * @brief Retrieves the height value.
     *
     * @details This function returns the height of an object. It accesses the private member variable '_height' and returns its value. The function is marked as 'const', indicating that it does not modify any member variables of the class.
     *
     * @return The height of the object as an unsigned integer.
     */

  0.386  util::Image::width                       — Retrieves the width of the object.
    /**
     * @fn unsigned int util::Image::width() const
     *
     * @brief Retrieves the width of the object.
     *
     * @details This function returns the width of the object as an unsigned integer. It accesses the private member variable '_width' and provides its value to the caller. The function does not modify any member variables and is marked as a const member function, indicating it does not alter the state of the object.
     *
     * @return The width of the object as an unsigned integer.
     */


================================================================================
[domain] social  (stability: stable)
  desc: Synchronous communication and social interaction: chat channel messaging and channel membership queries, tells and reply…
  locked: 10 functions, 10 with embeddings
  sim to desc — mean: 0.469  min: 0.361  max: 0.603

  0.603  check_channel_social                     — Checks if a social channel command matches a social action and dispatc
    /**
     * @fn bool check_channel_social(Character *ch, Flags::Bit channel, int custom, const String &command, const String &argument)
     *
     * @brief Checks if a social channel command matches a social action and dispatches appropriate messages to involved characters.
     *
     * @details This function verifies whether the provided command corresponds to a social action defined in the social table. If it does, it checks the character's communication flags for restrictions, and then processes the command argument to identify a target character (victim). It then dispatches context-specific messages to the actor, victim, and other characters in the room based on whether the argument is empty, the victim is present, or the victim is the actor themselves. The function also manages color settings for output and respects ignore and communication flags. It returns true if the command matches a social action and messages are dispatched; otherwise, it returns false.
     *
     * @param ch Pointer to the Character initiating the social command.
     * @param channel Bit flag representing the communication channel used for the social action.
     * @param custom Integer representing color customization settings for message output.
     * @param command The social command string issued by the character, used to identify the social action.
     * @param argument Additional arguments provided with the command, typically specifying a target character.
     * @return Boolean value indicating whether the command matched a social action and messages were dispatched (true) or not (false).
     */

  0.577  channel                                  — Handles communication through various channels for a character, includ
    /**
     * @fn void channel(Character *ch, const String &argument, int channel)
     *
     * @brief Handles communication through various channels for a character, including toggling, messaging, and visibility checks.
     *
     * @details This function manages the sending and toggling of communication channels for a character in the game. It verifies permissions, clan membership, and channel restrictions before allowing messages to be sent or channels to be toggled on/off. When toggling, it updates the character's communication flags and provides feedback. When sending messages, it processes special cases such as 'who' queries, immortal channels, and censorship, then dispatches messages to appropriate recipients based on visibility, ignoring status, and channel-specific rules. The function also handles special formatting for immortal talk and ensures messages are only sent to eligible characters, respecting their preferences and restrictions.
     *
     * @param ch Pointer to the Character initiating the channel command.
     * @param argument The message or command argument string provided by the character.
     * @param channel Integer representing the specific communication channel to be used.
     * @return Void; the function performs message dispatching and status updates without returning a value.
     */

  0.550  check_social                             — Checks if a social command matches the input and executes correspondin
    /**
     * @fn bool check_social(Character *ch, const String &command, const String &argument)
     *
     * @brief Checks if a social command matches the input and executes corresponding social interactions if applicable.
     *
     * @details This function searches the social table for a command that matches the given input prefix. If a match is found, it verifies the character's current state (e.g., dead, incapacitated, sleeping) and whether they are allowed to perform social actions. Depending on the presence and target of the argument, it performs appropriate social actions such as emotes or interactions with other characters in the room. It also handles special cases like sleeping characters and NPC behaviors, including random reactions. If the character is VT100 compatible, it clears the line and resets the cursor position after executing the social. The function returns true if a social command was processed, otherwise false.
     *
     * @param ch Pointer to the Character executing the social command.
     * @param command The social command string issued by the character.
     * @param argument Additional arguments provided with the command, typically target names.
     * @return Boolean indicating whether a social command was recognized and processed (true) or not (false).
     */

  0.498  send_to_clan                             — Sends a message to all members of a specified clan.
    /**
     * @fn void send_to_clan(Character *ch, Clan *target, const String &text)
     *
     * @brief Sends a message to all members of a specified clan.
     *
     * @details This function iterates through all active descriptors and sends a given text message to each character that belongs to the specified clan. If the target clan is null, it notifies the sender that no such clan exists. If the text message is empty, it prompts the sender to provide a message. The function utilizes the 'stc' function to send the message to each character's output buffer.
     *
     * @param ch A pointer to the Character object representing the sender of the message.
     * @param target A pointer to the Clan object representing the target clan to which the message will be sent.
     * @param text A String object containing the message to be sent to the clan members.
     * @return This function does not return a value.
     */

  0.478  config_censor                            — Configures censorship settings for a character based on input argument
    /**
     * @fn void config_censor(Character *ch, String argument)
     *
     * @brief Configures censorship settings for a character based on input arguments.
     *
     * @details The function 'config_censor' allows a character to configure their censorship settings by specifying an option number or name. If no argument is provided, it displays the current censorship settings for channels and spam. If 'help' or '?' is provided, it gives an overview of the censorship feature. For specific options, it toggles the censorship state or provides detailed help or a list of censored words. The function handles options for channels and spam, allowing the character to customize what content they wish to filter.
     *
     * @param ch A pointer to the Character object whose censorship settings are being configured.
     * @param argument A String object containing the input arguments that specify the censorship option to be configured.
     * @return This function does not return a value.
     */

  0.459  ignore_offline                           — Toggles the ignore status of a character based on the provided name.
    /**
     * @fn void ignore_offline(Character *, const String &)
     *
     * @brief Toggles the ignore status of a character based on the provided name.
     *
     * @details This function checks if a character, specified by the argument 'arg', is currently ignored by the character 'ch'. It queries the database to find a matching character name and group. If the character is found and belongs to a specific group, a message is sent to 'ch' indicating that the ignore action cannot be performed. If the character is not found, a message is sent to 'ch' indicating that there is no one by that name to ignore. If the character is found and can be ignored, the function toggles the ignore status: if the character is currently ignored, they are removed from the ignore list; otherwise, they are added to it. Appropriate messages are sent to 'ch' to indicate the change in ignore status.
     *
     * @param ch A pointer to the Character object that is attempting to ignore or stop ignoring another character.
     * @param arg A reference to a String object containing the name of the character to be ignored or unignored.
     * @return This function does not return a value.
     */

  0.411  social_lookup                            — Finds a social interaction by its name.
    /**
     * @fn Social * social_lookup(const String &name)
     *
     * @brief Finds a social interaction by its name.
     *
     * @details This function searches through a linked list of Social objects to find one with a name that matches the provided String. It starts from the first social in the list and iterates through each element until it finds a match or reaches the end of the list. If a matching Social object is found, it is returned; otherwise, the function returns nullptr.
     *
     * @param name The name of the social interaction to search for, provided as a String object.
     * @return A pointer to the Social object with the matching name, or nullptr if no match is found.
     */

  0.378  count_socials                            — Counts the number of social objects in a linked list.
    /**
     * @fn int count_socials()
     *
     * @brief Counts the number of social objects in a linked list.
     *
     * @details Counts the number of social entries in a linked list.
    This function iterates through a linked list of social objects, starting from the node following 'social_table_head' and ending at 'social_table_tail'. It counts each node in the list and returns the total count. The function assumes that 'social_table_head' and 'social_table_tail' are global pointers defining the bounds of the list.
     *
     * @return The total number of social entries in the linked list, as an integer.
     */

  0.376  remove_social                            — Removes a social entry from the social table by name.
    /**
     * @fn void remove_social(const String &)
     *
     * @brief Removes a social entry from the social table by name.
     *
     * @details This function searches for a social entry in the social table that matches the given name, ignoring case. If a matching entry is found, it is removed from the linked list and its memory is deallocated. The function assumes that the social table is implemented as a doubly linked list with head and tail sentinels.
     *
     * @param name The name of the social entry to be removed, compared in a case-insensitive manner.
     * @return This function does not return a value.
     */

  0.361  insert_social                            — Inserts a Social object into a sorted list alphabetically.
    /**
     * @fn void insert_social(Social *)
     *
     * @brief Inserts a Social object into a sorted list alphabetically.
     *
     * @details This function inserts a Social object into a doubly linked list that is sorted alphabetically by the name of the Social objects. It traverses the list to find the correct position based on a case-insensitive comparison of names and inserts the new Social object at that position. If the list is empty, the function will append the Social object at the end of the list.
     *
     * @param s The Social object to be inserted into the list.
     * @return This function does not return a value.
     */


================================================================================
[infrastructure] runtime  (stability: stable)
  desc: Core game loop and connection lifecycle: command interpreter dispatch, main tick loop (character updates, object decay, …
  locked: 9 functions, 9 with embeddings
  sim to desc — mean: 0.479  min: 0.312  max: 0.595

  0.595  char_update                              — Updates the state of all characters, including NPCs and players, handl
    /**
     * @fn void char_update(void)
     *
     * @brief Updates the state of all characters, including NPCs and players, handling effects, conditions, and cleanup.
     *
     * @details This function performs a comprehensive update cycle for all characters in the game world. It increments the save counter, manages character timers for link-dead detection, processes effects such as plague and poison, updates health, mana, and stamina regeneration, handles special conditions like necromancy, familiar status, and guild-specific abilities, manages light objects, triggers mob programs, and handles character death or removal. It also manages effects wearing off, applies damage from effects like plague and poison, and performs autosave and autoquit operations for characters based on their connection status and timers. The function ensures proper progression of character states and effects each game tick, maintaining game consistency and flow.
     *
     * @param void No parameters; operates on global game state and character list.
     * @return Void; the function performs side effects such as updating character states, applying effects, and managing game world conditions without returning a value.
     */

  0.541  World::update                            — Updates the world state by processing areas and cleaning up garbage.
    /**
     * @fn void World::update()
     *
     * @brief Updates the world state by processing areas and cleaning up garbage.
     *
     * @details The update function manages the periodic update of areas within the world and performs garbage collection on the character list. It decrements a static counter to determine when to update the areas. Once the counter reaches zero, it resets the counter and iterates over all areas, calling their update method. After updating the areas, it invokes the delete_garbage method on the character list to remove and delete any garbage objects.
     *
     * @return This function does not return a value.
     */

  0.524  obj_update                               — Updates the state of all objects in the game world.
    /**
     * @fn void obj_update(void)
     *
     * @brief Updates the state of all objects in the game world.
     *
     * @details This function iterates over all objects in the game world, updating their state based on their affects and timers. It handles the expiration of affects, decrements timers, and removes objects from the game world when their timers expire. The function also manages the transfer of contents from objects that are being removed, ensuring that items are not lost when their container decays. Special handling is included for objects involved in auctions to prevent their decay.
     *
     * @return This function does not return a value.
     */

  0.511  interpret                                — Main command interpreter for processing player and NPC commands, inclu
    /**
     * @fn void interpret(Character *ch, String argument)
     *
     * @brief Main command interpreter for processing player and NPC commands, including logging, command validation, and execution.
     *
     * @details Parses and executes a command or social interaction for a character based on input arguments.
    This function 'interpret' processes an input string 'argument' from a character 'ch', parsing the command, checking permissions and conditions, logging the command, and executing the corresponding command function from the command table. It handles special cases such as frozen players, command prefix parsing, social commands, disabled commands, and position restrictions. Additionally, it manages visual output adjustments for VT100 terminals and supports recursive invocation for commands like 'at', 'order', and 'force'.
     *
     * @param ch Pointer to the Character executing the command.
     * @param argument String containing the full command input to be interpreted.
     * @return This function has no return value; it performs command interpretation and execution side effects.
     */

  0.510  Weather::update                          — Updates the weather conditions and notifies characters of changes.
    /**
     * @fn void Weather::update()
     *
     * @brief Updates the weather conditions and notifies characters of changes.
     *
     * @details The update function simulates changes in weather conditions based on the current month and atmospheric pressure (mmhg). It adjusts the pressure and determines the current sky condition, potentially transitioning between states such as Cloudless, Cloudy, Raining, and Lightning. If the sky condition changes, a message is generated and sent to all awake, outdoor, non-NPC characters with the appropriate flags set.
     *
     * @return This function does not return a value.
     */

  0.499  GameTime::update                         — Updates the game time and notifies characters of time changes.
    /**
     * @fn void GameTime::update()
     *
     * @brief Updates the game time and notifies characters of time changes.
     *
     * @details The GameTime::update function increments the in-game hour and adjusts the day, month, and year accordingly when thresholds are reached. It changes the state of sunlight based on the current hour and constructs a message to notify characters of significant time changes, such as sunrise, sunset, and the start of a new day. The function sends these notifications to characters who are outside, awake, and have the appropriate flags set.
     *
     * @return This function does not return a value.
     */

  0.438  close_socket                             — Closes a network connection and handles associated character cleanup.
    /**
     * @fn void close_socket(Descriptor *dclose)
     *
     * @brief Closes a network connection and handles associated character cleanup.
     *
     * @details This function closes a network connection associated with a given Descriptor object. It processes any remaining output, handles snooping descriptors, logs the disconnection, and manages the character's state if they are linked to the descriptor. If the character is playing, it notifies others in the room of the disconnection and updates character flags. If the character is an NPC with morph flags, it manages their room transitions. The function also ensures the descriptor is removed from the global descriptor list and deletes the descriptor object.
     *
     * @param dclose A pointer to the Descriptor object representing the network connection to be closed.
     * @return This function does not return a value.
     */

  0.375  World::add_char                          — Adds a Character object to the world's character list.
    /**
     * @fn void World::add_char(Character *)
     *
     * @brief Adds a Character object to the world's character list.
     *
     * @details This function inserts the specified Character pointer into the world's character list by calling the add method of the character list. It effectively registers the character within the world, making it part of the managed collection. The function does not return a value and assumes that the provided Character pointer is valid.
     *
     * @param ch Pointer to the Character object to be added to the world's character list.
     * @return This function does not return a value.
     */

  0.312  check_disabled                           — Checks if a given command is disabled.
    /**
     * @fn bool check_disabled(const struct cmd_type *command)
     *
     * @brief Checks if a given command is disabled.
     *
     * @details Checks if a command is disabled.
    This function iterates through a list of disabled commands and checks if the provided command is in the list by comparing the function pointers. If a command is disabled, any command with the same function pointer will also be considered disabled.
     *
     * @param command A pointer to a cmd_type structure representing the command to check.
     * @return Returns true if the command is found in the disabled list, indicating it is disabled; otherwise, returns false.
     */


================================================================================
[projection] output  (stability: stable)
  desc: Message transport to player connections: dispatching formatted messages to rooms and specific targets, sending text to c…
  locked: 56 functions, 56 with embeddings
  sim to desc — mean: 0.486  min: 0.326  max: 0.671

  0.671  act                                      — Dispatches a formatted message to characters within a room or specific
    /**
     * @fn void act(const String &format, Character *ch, const Actable *arg1, const Actable *arg2, int type, int min_pos=POS_RESTING, bool censor=false, Room *room=nullptr)
     *
     * @brief Dispatches a formatted message to characters within a room or specific targets based on context and visibility rules.
     *
     * @details Dispatches a formatted message to characters and objects within a specified context based on parameters.
    This function acts as a wrapper around act_parse, preparing and passing the appropriate arguments to format and send messages to characters in a game environment. It takes a message format string, an actor, optional target entities, message type, minimum position for recipients, and a censor flag. The function casts the generic Actable pointers to specific Character or Object pointers as needed and calls act_parse to handle the actual message dispatching, ensuring that messages are delivered according to visibility, position, and censoring rules within the specified room context.
     *
     * @param format A string containing the message format with placeholders for dynamic content.
     * @param actor Pointer to the Character initiating the action or message.
     * @param arg1 First actable entity, used for substitution and context (can be Character, Object, or String).
     * @param arg2 Second actable entity, used for substitution and context (can be Character, Object, or String).
     * @param type Integer indicating the message target type (e.g., TO_CHAR, TO_ROOM).
     * @param min_pos Minimum position required for recipients to see the message (e.g., POS_SNEAK).
     * @param censor Boolean flag indicating whether to censor messages for NPCs.
     * @param room Pointer to the Room where the message is dispatched; may be null to default to actor's room.
     * @return This function has no return value; it performs message dispatching as a side effect.
     */

  0.652  stc                                      — Sends a string to a character's output buffer with optional color proc
    /**
     * @fn void stc(const String &txt, Character *ch)
     *
     * @brief Sends a string to a character's output buffer with optional color processing.
     *
     * @details The function 'stc' appends a given string to the output buffer of a character's descriptor, applying color processing based on the character's settings. If the input string is empty or the character's descriptor is null, the function returns immediately without performing any action. If the character is not an NPC and has the VIDEO_CODES_SHOW flag set, the string is written directly to the buffer. If the character has the PLR_COLOR2 flag set, color codes in the string are expanded to ANSI escape sequences before being written to the buffer. Otherwise, color codes are removed from the string before writing it to the buffer.
     *
     * @param txt The String object containing the text to be sent to the character.
     * @param ch A pointer to the Character object representing the recipient of the text.
     * @return This function does not return a value.
     */

  0.648  global_act                               — Sends an ACT-type message to all characters in the game, respecting vi
    /**
     * @fn void global_act(Character *ch, const String &message, int despite_invis, int color, const Flags &nocomm_bits)
     *
     * @brief Sends an ACT-type message to all characters in the game, respecting visibility and communication flags.
     *
     * @details Dispatches a message to all appropriate characters in the descriptor list, considering visibility and communication flags.
    This function iterates over all active descriptors in the game and sends a formatted message to each character, excluding the source character if specified. It considers communication restrictions via 'nocomm_bits' flags and visibility conditions, such as whether the recipient can see the sender or if the sender is invisible. The message is displayed with specified color and formatting, and the recipient's color settings are temporarily adjusted during message delivery.
     *
     * @param ch Pointer to the source Character initiating the message; can be null if no source is specified.
     * @param message The formatted message string to be dispatched to recipients.
     * @param despite_invis Flag indicating whether to ignore invisibility restrictions when determining visibility.
     * @param color Integer representing the color code for message display.
     * @param nocomm_bits Flags object containing communication restriction bits; characters with matching bits will not receive the message.
     * @return This function has no return value; it performs message dispatching as a side effect.
     */

  0.637  bust_a_prompt                            — Generates and displays a customizable prompt for a character based on 
    /**
     * @fn void bust_a_prompt(Character *ch)
     *
     * @brief Generates and displays a customizable prompt for a character based on their current state and prompt settings.
     *
     * @details This function constructs a dynamic prompt string for the specified character, incorporating various character attributes, room information, and custom prompt codes. It handles special sequences such as color codes, direction indicators, health, mana, stamina, experience, location, quest status, and other character-specific data. If the character has an empty prompt, a default prompt with health, mana, stamina, and prefix is shown. If the character is marked as AFK, an AFK indicator is displayed. The function processes each character in the prompt string, expanding format codes (prefixed with '') into relevant data, and handles color codes (prefixed with '{') by passing them through for further processing. The resulting prompt string is sent to the character's output buffer, optionally followed by the character's prefix if set. This function is primarily used to provide players with real-time status updates in a customizable format.
     *
     * @param ch Pointer to the Character object for whom the prompt is to be generated and displayed.
     * @return This function does not return a value; it outputs the constructed prompt directly to the character's output buffer.
     */

  0.633  page_to_char                             — Sends a string to a character's output buffer for display.
    /**
     * @fn void page_to_char(const String &txt, Character *ch)
     *
     * @brief Sends a string to a character's output buffer for display.
     *
     * @details This function appends the given string to the output buffer of a character's descriptor and then triggers the display of this buffer. If the string is empty or the character's descriptor is null, the function exits without performing any action. The function ensures that the text is added to the descriptor's buffer and displayed without clearing the remaining text.
     *
     * @param txt The string to be sent to the character's output buffer.
     * @param ch A pointer to the Character object whose descriptor's output buffer will be modified.
     * @return This function does not return a value.
     */

  0.632  act_parse                                — Formats and dispatches a message to characters in a room or specific t
    /**
     * @fn void act_parse(String format, Character *actor, Room *room, const Character *vch1, const Character *vch2, const String *str1, const String *str2, const Object *obj1, const Object *obj2, int type, int min_pos, bool censor)
     *
     * @brief Formats and dispatches a message to characters in a room or specific targets based on context and visibility rules.
     *
     * @details The function act_parse processes a message format string and sends the formatted message to appropriate characters within a room or environment, considering various conditions such as recipient type, position, visibility, and special states like sneaking or censorship. It handles different target types (e.g., TO_CHAR, TO_ROOM, TO_VICT, TO_WORLD) and manages special cases such as channel visibility and tailing relationships. The function also supports room-based viewing for arena scenarios and manages message formatting for tailers. It ensures that messages are only sent to characters who meet the specified criteria, applying necessary checks for position, NPC status, and other flags. The function is integral to in-game communication, providing contextual and conditional message delivery based on game state and character attributes.
     *
     * @param format A string containing the message format, which may include placeholders for dynamic content.
     * @param actor Pointer to the Character initiating the action or message.
     * @param room Pointer to the Room where the action occurs; may be null, in which case it defaults based on actor or object.
     * @param vch1 Pointer to the first target Character involved in the message, used for specific recipient targeting.
     * @param vch2 Pointer to the second target Character involved, currently unused in this implementation.
     * @param str1 Pointer to a String used for placeholder substitution within the message.
     * @param str2 Pointer to a String for additional placeholder substitution, such as door descriptions.
     * @param obj1 Pointer to the first Object involved, used for visibility and substitution.
     * @param obj2 Pointer to the second Object involved, used similarly for visibility and substitution.
     * @param type Integer indicating the message target type (e.g., TO_CHAR, TO_ROOM, TO_VICT, etc.).
     * @param min_pos Minimum position required for recipients to see the message; can be POS_SNEAK or other position constants.
     * @param censor Boolean flag indicating whether to censor messages for NPCs.
     * @return This function does not return a value; it dispatches formatted messages to appropriate characters based on the specified criteria.
     */

  0.618  talk_auction                             — Broadcasts an auction message to all eligible characters.
    /**
     * @fn void talk_auction(const String &argument)
     *
     * @brief Broadcasts an auction message to all eligible characters.
     *
     * @details The function iterates over all descriptors in the descriptor list and sends an auction message to characters who are currently playing and have not opted out of auction messages. It first checks if the message contains offensive words and skips sending to characters who have censorship enabled. If the character is eligible to receive the message, it sets the appropriate text color for auction messages, sends the formatted auction message, and then resets the text color.
     *
     * @param argument A String object containing the auction message to be broadcasted.
     * @return This function does not return a value.
     */

  0.618  ptc                                      — Sends a formatted message to a character.
    /**
     * @fn void ptc(Character *ch, const String &fmt, Params &&... params)
     *
     * @brief Sends a formatted message to a character.
     *
     * @details The function 'ptc' formats a message using the specified format string and parameters, and then sends the formatted message to the given character. It utilizes the 'Format::format' function to create the formatted string and 'stc' to send the message.
     *
     * @param ch A pointer to the Character object that will receive the formatted message.
     * @param fmt A constant reference to a String object that specifies the format of the output message.
     * @param params A variadic template parameter pack representing the values to be formatted into the output message.
     * @return This function does not return a value.
     */

  0.613  gameinout                                — Displays a game entry or exit message for a character or specified pla
    /**
     * @fn void gameinout(Character *ch, const String &mortal, const String &entryexit, char inout)
     *
     * @brief Displays a game entry or exit message for a character or specified player, with support for message customization and pronoun adjustments.
     *
     * @details This function sends a personalized entry ('I') or exit ('O') message related to game activities for a character or a specified player. It first verifies that the character is not an NPC; if it is, it outputs a message indicating mobs do not have such messages and exits. If a mortal name is provided, it attempts to locate that player in the game world; if not found, it notifies the character. Depending on the 'inout' parameter ('I' for entry, others for exit), it retrieves the corresponding message template from the victim's pcdata. If no message is set, it informs the character accordingly. When sending the message, if the victim is the same as the character initiating the action, it directly displays the message. Otherwise, it modifies the message template by replacing pronoun placeholders ('$n', '$e', '$m', '$s') with their third-person equivalents ('$N', '$E', '$M', '$S') and then dispatches the message to the character, addressing the victim in third person. The function ensures proper message formatting and context-sensitive delivery based on the involved characters.
     *
     * @param ch Pointer to the Character initiating the message or action.
     * @param mortal The name of the player character to find and send the message to; can be empty to target 'ch'.
     * @param entryexit The message template or description to be used for entry or exit actions.
     * @param inout A character indicating whether the message is for entry ('I') or exit (any other character).
     * @return The function has no return value; it performs message dispatching as a side effect.
     */

  0.601  set_color                                — Sets the text color for a character's output.
    /**
     * @fn void set_color(Character *ch, int color, int bold)
     *
     * @brief Sets the text color for a character's output.
     *
     * @details Sets the color and boldness for a character's output.
    This function sets the text color for a character's output buffer using ANSI escape codes. If the character has the PLR_COLOR flag set, it formats and sends the escape code to the character's output buffer. For non-player characters, it also updates the last used color and boldness in the character's data structure.
     *
     * @param ch A pointer to the Character object for which the color and boldness are being set.
     * @param color An integer representing the color code to be set for the character's output.
     * @param bold An integer representing the boldness level to be set for the character's output.
     * @return This function does not return a value.
     */

  0.600  act_format                               — Formats and sends a message to a character, with support for dynamic c
    /**
     * @fn void act_format(const String &format, Character *actor, const Character *vch1, const Character *vch2, const String *str1, const String *str2, const Object *obj1, const Object *obj2, Character *observer, bool snooper, int vis)
     *
     * @brief Formats and sends a message to a character, with support for dynamic content substitution.
     *
     * @details The act_format function constructs a formatted message string by substituting placeholders in the provided format string with corresponding values based on the provided characters, objects, and strings. It supports various placeholder codes that correspond to different entities such as characters and objects, and it handles visibility checks and gender-specific pronouns. The resulting message is sent to the observer character, and if applicable, triggers a mobile program action.
     *
     * @param format A constant reference to a String object that specifies the format of the message, containing placeholders for dynamic content.
     * @param actor A pointer to the Character object representing the primary actor in the message.
     * @param vch1 A pointer to the first Character object involved in the message, used for placeholder substitution.
     * @param vch2 A pointer to the second Character object involved in the message, currently unused in this function.
     * @param str1 A pointer to a String object used for substitution of specific placeholders in the format string.
     * @param str2 A pointer to a String object used for substitution of specific placeholders in the format string, such as door descriptions.
     * @param obj1 A pointer to the first Object involved in the message, used for visibility checks and substitution.
     * @param obj2 A pointer to the second Object involved in the message, used for visibility checks and substitution.
     * @param observer A pointer to the Character object who will receive the formatted message.
     * @param snooper A boolean indicating whether the message is being snooped, which affects the message formatting.
     * @param vis An integer representing the visibility level, used to determine how characters are described in the message.
     * @return This function does not return a value.
     */

  0.599  dam_message                              — Generates and dispatches an appropriate damage message to characters b
    /**
     * @fn void dam_message(Character *ch, Character *victim, int dam, skill::type attack_skill, int attack_type, bool immune, bool sanc_immune)
     *
     * @brief Generates and dispatches an appropriate damage message to characters based on damage amount, attack type, and immunity status.
     *
     * @details This function constructs and sends contextual damage messages to the attacker, victim, and room occupants, reflecting the damage dealt, attack type, and immunity conditions. It selects a damage descriptor string based on the damage amount, determines the attack noun from either a specified skill or attack table, and formats messages accordingly. It handles special cases such as immunity and sanctuary immunity, providing appropriate messages for each. The function also sets text colors for the attacker and victim during message dispatching. It does not return a value but performs side effects by sending messages to relevant characters and room.
     *
     * @param ch Pointer to the Character initiating the attack or damage source.
     * @param victim Pointer to the Character receiving the damage.
     * @param dam Integer representing the amount of damage dealt.
     * @param attack_skill Skill::type indicating the specific skill used for damage, if known.
     * @param immune Boolean indicating whether the victim is immune to the attack.
     * @param sanc_immune Boolean indicating whether the victim's sanctuary immunity applies.
     * @return This function has no return value; it performs message dispatching as a side effect.
     */

  0.596  write_smack                              — Displays a warning message to a character with optional color formatti
    /**
     * @fn void write_smack(Character *victim)
     *
     * @brief Displays a warning message to a character with optional color formatting.
     *
     * @details The function 'write_smack' sends a predefined warning message to the specified character, 'victim'. If the character has the 'PLR_COLOR' flag set, the message is displayed with various color and style effects. Otherwise, the message is sent without any color formatting. The message consists of a humorous warning followed by an ASCII art representation of the word 'SMACK'.
     *
     * @param victim A pointer to the Character object that will receive the warning message.
     * @return This function does not return a value.
     */

  0.577  scan_char                                — Displays information about a character at a certain distance and direc
    /**
     * @fn void scan_char(Character *victim, Character *ch, int depth, int door)
     *
     * @brief Displays information about a character at a certain distance and direction.
     *
     * @details The function 'scan_char' provides a formatted message to the character 'ch' about another character 'victim', indicating their presence at a specified distance and direction. It adjusts the text color based on whether the victim is a non-player character (NPC) or a player. The message includes the victim's name, their distance from 'ch', and the direction if applicable. The text color is reset to white after the message is displayed.
     *
     * @param victim A pointer to the Character object representing the target character whose information is being displayed.
     * @param ch A pointer to the Character object that will receive the formatted message about the 'victim'.
     * @param depth An integer representing the distance of the 'victim' from 'ch', used to index into the 'distance' array.
     * @param door An integer representing the direction index, used to retrieve the direction name if 'depth' is non-zero.
     * @return This function does not return a value.
     */

  0.576  duel_announce                            — Announces a duel message to all eligible players.
    /**
     * @fn void duel_announce(char *buf, Duel *duel)
     *
     * @brief Announces a duel message to all eligible players.
     *
     * @details The function formats a duel announcement message and sends it to all players who are currently playing, except for the duel's challenger and defender, and who have not opted out of announcements. The message is formatted with a specific prefix and color codes, and is sent to each eligible player's character.
     *
     * @param buf A pointer to a character array containing the message to be announced.
     * @param duel A pointer to a Duel object representing the current duel, containing the challenger and defender.
     * @return This function does not return a value.
     */

  0.569  process_output                           — Processes and outputs data for a network descriptor, handling prompts 
    /**
     * @fn bool process_output(Descriptor *d, bool fPrompt)
     *
     * @brief Processes and outputs data for a network descriptor, handling prompts and VT100 terminal features.
     *
     * @details This function manages the output process for a given network descriptor. It handles VT100 terminal features, such as saving and restoring the cursor position and displaying a status bar. If the descriptor is in a playing state and the character has VT100 video flags enabled, it adjusts the cursor position accordingly. The function also generates prompts based on the character's state, including battle prompts if the character is engaged in combat. It checks if the character can see their opponent and provides a description of the opponent's condition. If the descriptor's output buffer is not empty, the function writes the buffer's contents to the descriptor, handling any snooping connections by duplicating the output to the snooper. The function clears the output buffer after writing.
     *
     * @param d A pointer to the Descriptor object for which output is being processed.
     * @param fPrompt A boolean indicating whether a prompt should be displayed.
     * @return Returns true if the output was successfully written to the descriptor, otherwise returns false if an error occurred during writing.
     */

  0.567  format_mstat                             — Formats and sends detailed status information about a character to ano
    /**
     * @fn void format_mstat(Character *ch, Character *victim)
     *
     * @brief Formats and sends detailed status information about a character to another character.
     *
     * @details The function format_mstat generates a comprehensive status report for a given character (victim) and sends it to another character (ch). It includes information such as the victim's room, level, attributes, health, mana, stamina, race, guild, and various flags. For non-player characters (NPCs), it also includes specific NPC-related data like damage and special procedures. The function handles both player characters and NPCs, adjusting the output based on the type of character. It also includes details about the character's affects, defense modifiers, and remort affects if applicable.
     *
     * @param ch A pointer to the Character object that will receive the formatted status information.
     * @param victim A pointer to the Character object whose status information is being formatted and sent.
     * @return This function does not return a value.
     */

  0.565  send_to_query                            — Sends a message to characters in a query list who are online and not i
    /**
     * @fn void send_to_query(Character *ch, const char *string)
     *
     * @brief Sends a message to characters in a query list who are online and not ignoring the sender.
     *
     * @details This function iterates over all characters in the game world and checks if they are eligible to receive a message from the sender. A character is eligible if they are not an NPC, do not have the COMM_NOQUERY flag set, and are not ignoring the sender. If eligible, the function checks if the character's name is in the sender's query list. If so, it sets the character's text color, sends the message, and then resets the color.
     *
     * @param ch A pointer to the Character object representing the sender of the message.
     * @param string A constant character pointer to the message string to be sent to eligible characters.
     * @return This function does not return a value.
     */

  0.540  channel_who                              — Displays a list of players who have a specific communication channel e
    /**
     * @fn void channel_who(Character *ch, const String &channelname, const Flags::Bit &channel, int custom)
     *
     * @brief Displays a list of players who have a specific communication channel enabled.
     *
     * @details Displays a list of players who have a specified communication channel enabled, filtered by visibility and permissions.
    This function outputs the names of all characters currently connected and actively using the specified channel, provided they meet visibility and permission criteria. It first checks if the calling character is a non-player character (NPC) and exits if so. It then sets the output color based on the custom parameter and informs the caller about the channel being listed. The function iterates through all active descriptors, filtering out those who are not in the same clan (if applicable), not visible, or have disabled the channel or are in quiet mode. For the 'no flame' channel, it additionally checks for censorship flags. Characters passing all filters are listed by name in the caller's output.
     *
     * @param ch Pointer to the Character initiating the command, used to determine visibility and permissions.
     * @param channelname String representing the name of the communication channel, used in the header message.
     * @param channel Bit flag indicating the specific communication channel to filter and display.
     * @param custom Integer representing the color slot for output text, influencing text appearance.
     * @return Void; the function performs output operations and does not return a value.
     */

  0.535  new_color                                — Sets the color for a character's text output based on their settings o
    /**
     * @fn void new_color(Character *ch, int slot)
     *
     * @brief Sets the color for a character's text output based on their settings or defaults.
     *
     * @details This function determines the appropriate text color and boldness for a character's output. If the character is a player character (PC) and has a custom color setting for the specified slot, it uses that setting. Otherwise, it applies a default color and boldness from a predefined table. The function ensures that the character's text output is visually consistent with their preferences or the game's defaults.
     *
     * @param ch A pointer to the Character object for which the text color is being set.
     * @param slot An integer representing the color slot to be used for determining the color and boldness settings.
     * @return This function does not return a value.
     */

  0.525  show_string                              — Displays a portion of a string to a descriptor's output buffer, with o
    /**
     * @fn void show_string(Descriptor *d, bool clear_remainder)
     *
     * @brief Displays a portion of a string to a descriptor's output buffer, with optional clearing of remaining text.
     *
     * @details The function 'show_string' manages the display of text to a descriptor's output buffer. If 'clear_remainder' is true, it clears any remaining text in the descriptor's buffer. Otherwise, it calculates the length of the text to display based on the character's line settings, extracts that portion from the descriptor's buffer, and sends it to the character's output buffer. If no character is associated with the descriptor, it appends the text directly to the descriptor's output buffer.
     *
     * @param d A pointer to the Descriptor object whose output buffer will be modified.
     * @param clear_remainder A boolean flag indicating whether to clear the remaining text in the descriptor's buffer.
     * @return This function does not return a value.
     */

  0.523  clear_window                             — Clears the output window for a character.
    /**
     * @fn void clear_window(Character *ch)
     *
     * @brief Clears the output window for a character.
     *
     * @details This function sends a command to clear the output window of the specified character by utilizing the stc function with a predefined control sequence for clearing the window. It is used to refresh or reset the display for the character in the user interface.
     *
     * @param ch A pointer to the Character object whose output window is to be cleared.
     * @return This function does not return a value.
     */

  0.512  cwtb                                     — Appends color-expanded text to a descriptor's output buffer.
    /**
     * @fn void cwtb(Descriptor *d, const String &txt)
     *
     * @brief Appends color-expanded text to a descriptor's output buffer.
     *
     * @details This function takes a descriptor and a string, expands any color codes in the string to their corresponding ANSI escape sequences using the character's settings, and appends the resulting text to the descriptor's output buffer. If the input string is empty, the function returns immediately without modifying the buffer.
     *
     * @param d A pointer to the Descriptor object whose output buffer will be modified.
     * @param txt The String object containing the text to be expanded and appended to the output buffer.
     * @return This function does not return a value.
     */

  0.511  config_video                             — Configures video display options for a character.
    /**
     * @fn void config_video(Character *ch, String argument)
     *
     * @brief Configures video display options for a character.
     *
     * @details This function allows a character to configure their video display settings, such as flashing text, dark mode, color codes, and VT100 emulation. It provides a list of options if no arguments are given, and detailed help for each option if 'help' or '?' is specified. The function also toggles specific video settings based on the provided arguments.
     *
     * @param ch A pointer to the Character object whose video settings are being configured.
     * @param argument A String object containing the command arguments specifying which video option to configure or request help for.
     * @return This function does not return a value.
     */

  0.511  reset_terminal                           — Resets the terminal settings for a character.
    /**
     * @fn void reset_terminal(Character *ch)
     *
     * @brief Resets the terminal settings for a character.
     *
     * @details Resets the terminal display settings for a character.
    This function sends a reset command to the terminal associated with the specified character. It utilizes the stc function to send a predefined reset sequence, ensuring that the character's terminal settings are restored to their default state. This is typically used to clear any custom formatting or colors that may have been applied during the character's session.
     *
     * @param ch A pointer to the Character object whose terminal display settings are to be reset.
     * @return This function does not return a value.
     */

  0.499  goto_line                                — Moves the cursor to a specified position on the character's output scr
    /**
     * @fn void goto_line(Character *ch, int row, int column)
     *
     * @brief Moves the cursor to a specified position on the character's output screen.
     *
     * @details Moves the cursor to a specified position on a character's output screen.
    The function constructs an ANSI escape sequence to move the cursor to the specified row and column on the terminal screen of the character. It formats the escape sequence using the Format::sprintf function and sends it to the character's output buffer using the stc function. This is typically used in text-based interfaces to control cursor positioning.
     *
     * @param ch A pointer to the Character object representing the recipient of the cursor movement command.
     * @param row An integer specifying the row number to move the cursor to.
     * @param column An integer specifying the column number to move the cursor to.
     * @return This function does not return a value.
     */

  0.479  config_color                             — Configures color settings for a character based on input arguments.
    /**
     * @fn void config_color(Character *ch, String argument)
     *
     * @brief Configures color settings for a character based on input arguments.
     *
     * @details The function allows a character to configure their color settings by providing an argument that specifies the desired option. If no argument is provided, it lists the available color options. The function supports toggling general color and crazy color settings, configuring specific categories like channels, score, and miscellaneous, and resetting to default color settings. It also provides help information for each option when requested.
     *
     * @param ch A pointer to the Character object whose color settings are being configured.
     * @param argument A String containing the arguments for configuring color settings, which may include a color name, 'reset', or 'help'.
     * @return This function does not return a value.
     */

  0.474  HCOL_TEXT                               
    /**
     * @def HCOL_TEXT
     *
     */

  0.472  get_custom_color_code                    — Retrieves a custom color code for a character based on a specified slo
    /**
     * @fn String get_custom_color_code(Character *ch, int slot)
     *
     * @brief Retrieves a custom color code for a character based on a specified slot.
     *
     * @details This function determines the appropriate color and boldness settings for a character based on whether the character is a non-player character (NPC) or a player character (PC). If the character is a PC and has a custom color setting for the given slot, it uses those settings. Otherwise, it defaults to a predefined setting from the csetting_table. The function then retrieves the corresponding color code using these settings.
     *
     * @param ch A pointer to the Character object for which the color code is being retrieved.
     * @param slot An integer representing the slot index for which the color settings are being queried.
     * @return A String containing the color code corresponding to the determined color and boldness settings.
     */

  0.471  write_to_buffer                          — Appends text to a descriptor's output buffer.
    /**
     * @fn void write_to_buffer(Descriptor *d, const String &txt)
     *
     * @brief Appends text to a descriptor's output buffer.
     *
     * @details Writes text to a descriptor's output buffer.
    This function appends the given text to the output buffer of a Descriptor object. If the buffer is initially empty and no command flag is set, it prepends a newline and carriage return to the buffer before appending the text. This ensures proper formatting of the output buffer.
     *
     * @param d A pointer to the Descriptor object whose output buffer is to be written to.
     * @param txt A String object containing the text to be appended to the descriptor's output buffer.
     * @return This function does not return a value.
     */

  0.458  PERS                                    
    /**
     * @def PERS
     *
     */

  0.458  config_color_func                        — Configures color settings for a character based on input arguments.
    /**
     * @fn void config_color_func(Character *ch, String argument, int type)
     *
     * @brief Configures color settings for a character based on input arguments.
     *
     * @details The function config_color_func allows a character to configure their color settings for different types of outputs, such as channels, score, or miscellaneous items. It takes a character pointer, an argument string, and a type identifier to determine which color settings to modify. The function supports listing current settings, resetting to defaults, and setting new colors based on provided names. It handles invalid inputs by providing appropriate feedback to the user.
     *
     * @param ch A pointer to the Character object whose color settings are being configured.
     * @param argument A String containing the arguments for configuring color settings, which may include a color name or 'reset'.
     * @param type An integer representing the type of color setting to configure, where specific values correspond to different categories like channels, score, or miscellaneous.
     * @return This function does not return a value.
     */

  0.457  update                                  
    /**
     * @fn static int update(printbuffer *p)
     *
     */

  0.447  get_custom_color_name                    — Retrieves a custom color name for a character based on their settings 
    /**
     * @fn String get_custom_color_name(Character *ch, int slot)
     *
     * @brief Retrieves a custom color name for a character based on their settings or defaults.
     *
     * @details Retrieves the custom color name for a character based on a specified slot.
    This function determines the color and boldness settings for a given character and slot, and retrieves the corresponding color name. If the character is a non-player character (NPC) or the specific color setting is not defined, it defaults to a predefined setting from 'csetting_table'. The function then uses these settings to obtain the color name using 'get_color_name'.
     *
     * @param ch A pointer to the Character object for which the color name is being retrieved.
     * @param slot An integer representing the slot index from which to retrieve the color settings.
     * @return A String representing the name of the color based on the character's settings or the default settings if no custom settings are found.
     */

  0.443  interpret_color_code                     — Interprets a color code character and returns the corresponding color 
    /**
     * @fn String interpret_color_code(Character *ch, char a)
     *
     * @brief Interprets a color code character and returns the corresponding color escape sequence.
     *
     * @details This function takes a character representing a color code and a Character object, and returns a String containing the appropriate ANSI escape sequence for that color. The function handles various color codes, including both foreground and background colors, and considers character-specific settings such as video flags and last used colors. It provides default colors when the Character object is null or lacks specific data.
     *
     * @param ch A pointer to a Character object that may contain personal color settings and video flags.
     * @param a A character representing the color code to interpret.
     * @return A String object containing the ANSI escape sequence for the specified color code.
     */

  0.433  format_page                              — Formats a page of text by splitting it into paragraphs, wrapping each,
    /**
     * @fn const String format_page(const String &orig_page, int wrap_len)
     *
     * @brief Formats a page of text by splitting it into paragraphs, wrapping each, and combining them into a single output.
     *
     * @details The function takes an original page of text and processes it by splitting it into paragraphs based on double newline delimiters. Each paragraph is then formatted and wrapped to a specified length, taking into account color codes. The resulting paragraphs are combined into a single String object, with each paragraph separated by a newline character. Initial and additional newlines are preserved to maintain the structure of the input text.
     *
     * @param orig_page The original String object representing the page of text to be formatted.
     * @param wrap_len The maximum length of text (excluding color codes) before wrapping occurs for each paragraph.
     * @return A formatted String object containing the wrapped paragraphs, with each paragraph separated by a newline character.
     */

  0.425  expand_color_codes                       — Expands color codes in a string to their corresponding ANSI escape seq
    /**
     * @fn String expand_color_codes(Character *ch, const String &str)
     *
     * @brief Expands color codes in a string to their corresponding ANSI escape sequences.
     *
     * @details This function processes a given string, replacing color code sequences enclosed in curly braces with their corresponding ANSI escape sequences. It iterates over each character in the input string, and when a '{' character is encountered, it interprets the following character as a color code. The function uses the 'interpret_color_code' function to convert this color code into an ANSI escape sequence, taking into account any personal color settings and video flags from the provided Character object. The resulting string with expanded color codes is returned.
     *
     * @param ch A pointer to a Character object that may contain personal color settings and video flags, used for interpreting color codes.
     * @param str The input string containing color codes to be expanded.
     * @return A String object containing the input string with all color codes expanded to their corresponding ANSI escape sequences.
     */

  0.411  write_to_descriptor                      — Writes a block of text to a specified file descriptor.
    /**
     * @fn bool write_to_descriptor(int desc, const String &txt, int length)
     *
     * @brief Writes a block of text to a specified file descriptor.
     *
     * @details This function attempts to write the contents of a String object to a given file descriptor in blocks. It handles potential errors during the write operation and adjusts the block size if necessary to avoid errors with very long blocks. The function uses a loop to write the text in chunks of up to 4096 bytes until the entire text is written or an error occurs.
     *
     * @param desc The file descriptor to which the text will be written.
     * @param txt The String object containing the text to be written.
     * @param length The number of characters from the String to write. If less than or equal to zero, the function calculates the length using String::strlen.
     * @return Returns true if the entire text is successfully written to the file descriptor, otherwise returns false if an error occurs during writing.
     */

  0.410  format_string                            — Formats a string by wrapping its content into paragraphs.
    /**
     * @fn String format_string(const String &s)
     *
     * @brief Formats a string by wrapping its content into paragraphs.
     *
     * @details Formats a string by wrapping its paragraphs to a specified length.
    This function takes a String object and formats it by wrapping its content into paragraphs with a maximum line length of 77 characters. It utilizes the format_page function to perform the wrapping and ensures that each paragraph is separated by a newline character. The function is useful for preparing text for display where line length is constrained.
     *
     * @param s The original String object representing the text to be formatted.
     * @return A formatted String object containing the wrapped paragraphs, with each paragraph separated by a newline character.
     */

  0.400  wrap_string                              — Wraps a line of text while being aware of color codes.
    /**
     * @fn const String wrap_string(const String &s, unsigned long wrap_len)
     *
     * @brief Wraps a line of text while being aware of color codes.
     *
     * @details This function takes a String object and a wrap length, and returns a new String where the input text is wrapped at the specified length. The function is aware of color codes denoted by double curly braces '{{' and ensures that these codes do not interfere with the wrapping process. The text is wrapped at spaces, and any color codes are preserved in their original positions relative to the text.
     *
     * @param s The input String object containing the text to be wrapped.
     * @param wrap_len The maximum length of text (excluding color codes) before wrapping occurs.
     * @return A new String object containing the wrapped text, with lines separated by newline characters.
     */

  0.395  HCOL_LEVEL                              
    /**
     * @def HCOL_LEVEL
     *
     */

  0.392  Format::printf                           — Prints a formatted string to the standard output.
    /**
     * @fn int Format::printf(const String &fmt, Params &&... params)
     *
     * @brief Prints a formatted string to the standard output.
     *
     * @details This function takes a format string and a variable number of parameters, formats them according to the format specifiers in the string, and outputs the result to the standard output using the C standard library's printf function. The parameters are forwarded to the C-style printf function using Format::to_c to preserve their value categories.
     *
     * @param fmt The format string containing format specifiers.
     * @param params A variadic list of parameters to be formatted and printed according to the format string.
     * @return The number of characters printed, or a negative value if an error occurs.
     */

  0.392  make_bar                                 — Creates a formatted string representing a bar with specified colors an
    /**
     * @fn String make_bar(const String &bgcolor, const String &fgcolor, long info, int numbg, bool imm)
     *
     * @brief Creates a formatted string representing a bar with specified colors and information.
     *
     * @details The function constructs a string that visually represents a bar with background and foreground colors. It formats the string based on whether the 'imm' flag is true or false. If 'imm' is true, it includes the 'info' value in the formatted string. The function then appends a formatted foreground color string at a specified position within the bar.
     *
     * @param bgcolor The background color to be used in the bar's format string.
     * @param fgcolor The foreground color to be used in the bar's format string.
     * @param info A long integer value to be included in the bar if 'imm' is true.
     * @param numbg An integer specifying the position offset for inserting the foreground color string.
     * @param imm A boolean flag indicating whether the 'info' value should be included in the bar.
     * @return A String object representing the formatted bar with the specified colors and optional information.
     */

  0.381  get_color_code                           — Retrieves the color code for a given color and boldness.
    /**
     * @fn String get_color_code(int color, int bold)
     *
     * @brief Retrieves the color code for a given color and boldness.
     *
     * @details This function searches through a predefined color table to find a matching entry based on the specified color and boldness parameters. If a match is found, it returns the corresponding color code as a String. If no match is found, it returns an empty String.
     *
     * @param color The integer representing the color to search for in the color table.
     * @param bold The integer representing the boldness level to search for in the color table.
     * @return A String containing the color code if a matching entry is found, or an empty String if no match is found.
     */

  0.378  gem::get_short_string                    — Generates a formatted short string representation of an object's setti
    /**
     * @fn const String gem::get_short_string(Object *eq)
     *
     * @brief Generates a formatted short string representation of an object's settings.
     *
     * @details This function constructs a short string representation of an object's settings, specifically for display purposes. It takes into account the number of settings in the object and the gems it contains. Each gem is represented by a specific symbol and color code, while empty settings are represented by a different symbol and color. The resulting string is enclosed in colored brackets.
     *
     * @param eq A pointer to an Object whose settings and gems are to be represented in the short string.
     * @return A String object containing the formatted short string representation of the object's settings, including symbols for gems and empty settings, enclosed in colored brackets.
     */

  0.377  dam_type_name                            — Returns the name of a damage type based on its integer code.
    /**
     * @fn String dam_type_name(int type)
     *
     * @brief Returns the name of a damage type based on its integer code.
     *
     * @details Returns the ASCII name of a specified damage type.
    This function takes an integer representing a damage type and returns a corresponding string name. It uses a switch statement to match the integer code to predefined damage types, such as 'fire', 'cold', or 'acid'. If the provided type does not match any known damage types, it logs a bug report using the Logging::bug function and returns '(unknown)'.
     *
     * @param type An integer representing the damage type for which the ASCII name is requested.
     * @return A String object containing the ASCII name of the specified damage type, or "(unknown)" if the type is not recognized.
     */

  0.369  get_color_name                           — Retrieves the name of a color based on its code and boldness.
    /**
     * @fn String get_color_name(int color, int bold)
     *
     * @brief Retrieves the name of a color based on its code and boldness.
     *
     * @details This function searches through a predefined color table to find a matching color entry based on the provided color code and boldness flag. If a match is found, it returns the corresponding color name as a String. If no match is found, it returns an empty String.
     *
     * @param color The integer code representing the color to search for.
     * @param bold An integer flag indicating whether the color is bold (typically 1 for bold, 0 for non-bold).
     * @return A String containing the name of the color if a match is found; otherwise, an empty String.
     */

  0.368  HCOL_GROUP                              
    /**
     * @def HCOL_GROUP
     *
     */

  0.363  listline                                 — Formats and appends a line of text with line number information to a S
    /**
     * @fn static void listline(String &dbuf, int lineno, char *line)
     *
     * @brief Formats and appends a line of text with line number information to a String buffer.
     *
     * @details The function 'listline' formats a line of text with its corresponding line number and appends it to the provided String buffer 'dbuf'. It distinguishes between the current line being edited, lines within the editable range, and lines beyond the current content. Special markers are added for the top and end of the content. The function uses a buffer to format the line number and appends the line content, handling newline and null characters appropriately.
     *
     * @param dbuf A reference to a String object where the formatted line will be appended.
     * @param lineno An integer representing the line number to be formatted and displayed.
     * @param line A pointer to a character array representing the line content to be formatted and appended.
     * @return This function does not return a value.
     */

  0.362  Format::format                           — Formats a string using the specified format and parameters.
    /**
     * @fn String Format::format(const String &fmt, Params &&... params)
     *
     * @brief Formats a string using the specified format and parameters.
     *
     * @details This function takes a format string and a variadic list of parameters, formats them according to the specified format, and returns the resulting string. It utilizes the Format::sprintf function to perform the formatting operation, storing the result in a temporary String object which is then returned.
     *
     * @param fmt A constant reference to a String object that specifies the format of the output.
     * @return A String object containing the formatted output.
     */

  0.360  HCOL_ORDER                              
    /**
     * @def HCOL_ORDER
     *
     */

  0.359  Format::fprintf                          — Writes formatted output to the specified file stream.
    /**
     * @fn int Format::fprintf(FILE *fp, const String &fmt, Params &&... params)
     *
     * @brief Writes formatted output to the specified file stream.
     *
     * @details This function writes formatted data to the given file stream 'fp' using the format string 'fmt' and a variable number of additional parameters. It utilizes the C++ standard library function 'std::fprintf' for formatting and output. The 'Format::to_c' function is used to forward each parameter, preserving its value category (lvalue or rvalue).
     *
     * @param fp A pointer to a FILE object that identifies the output stream.
     * @param fmt A constant reference to a String object that contains the format string.
     * @param params A variadic template parameter pack representing the arguments to be formatted and printed according to 'fmt'.
     * @return The total number of characters written to the file stream, or a negative value if an error occurs.
     */

  0.356  HCOL_ID                                 
    /**
     * @def HCOL_ID
     *
     */

  0.345  HCOL_KEYS                               
    /**
     * @def HCOL_KEYS
     *
     */

  0.341  HTABLE                                  
    /**
     * @def HTABLE
     *
     */

  0.326  format_paragraph                         — Transforms a block of newline-separated text into a single formatted l
    /**
     * @fn const String format_paragraph(const String &orig_paragraph)
     *
     * @brief Transforms a block of newline-separated text into a single formatted line.
     *
     * @details This function takes a paragraph of text, removes internal newlines, and formats it into a single line. It strips leading and trailing whitespace, removes double spaces, and ensures proper spacing and capitalization after sentence-ending punctuation. The function also adjusts spacing around parentheses and adds indentation to the resulting formatted paragraph.
     *
     * @param orig_paragraph The original paragraph of text to be formatted.
     * @return A formatted String object representing the paragraph as a single line with proper spacing and capitalization.
     */


================================================================================
[domain] notes  (stability: stable)
  desc: Asynchronous note and board system: composing, addressing, and attaching notes to characters, appending notes to board l…
  locked: 10 functions, 10 with embeddings
  sim to desc — mean: 0.496  min: 0.411  max: 0.606

  0.606  parse_note                               — Handles various note-related commands for a character.
    /**
     * @fn void parse_note(Character *ch, String argument, int type)
     *
     * @brief Handles various note-related commands for a character.
     *
     * @details The function parse_note processes commands related to notes for a character in a game. It allows characters to read, list, remove, delete, forward, repost, move, and manage notes. The function also supports creating and editing notes, setting recipients, subjects, and posting notes to different boards. It handles both player and non-player characters, with specific restrictions for NPCs and certain commands limited to characters with specific privileges.
     *
     * @param ch A pointer to the Character object representing the character executing the note command.
     * @param argument A String object containing the command and its arguments to be processed.
     * @param type An integer representing the type of note board being accessed or modified.
     * @return This function does not return a value.
     */

  0.547  notify_note_post                         — Notifies characters of a new note post based on their affiliations and
    /**
     * @fn void notify_note_post(Note *pnote, Character *vch, int type)
     *
     * @brief Notifies characters of a new note post based on their affiliations and settings.
     *
     * @details This function iterates over all characters in the game world and sends a notification about a new note post to eligible characters. It constructs a message indicating the type of note and its sender, and appends additional information based on the character's affiliations, such as guild membership or personal relevance. Notifications are sent unless the character is the author of the note or has disabled notifications.
     *
     * @param pnote A pointer to the Note object representing the note that has been posted.
     * @param vch A pointer to the Character object representing the character who posted the note, used to avoid notifying the author.
     * @param type An integer representing the type of board the note was posted on, used to retrieve the board's name.
     * @return This function does not return a value.
     */

  0.525  append_note                              — Appends a note to the appropriate list and writes it to a file.
    /**
     * @fn void append_note(Note *pnote)
     *
     * @brief Appends a note to the appropriate list and writes it to a file.
     *
     * @details This function takes a pointer to a Note object and appends it to the corresponding list based on the note's type. It then writes the note's details to a file associated with that type. The function handles different types of notes, each associated with a specific file and list. If the list is empty, the note becomes the first element. Otherwise, it is added to the end of the list. The function writes the note's sender, date, timestamp, recipient list, subject, and text to the file, replacing any occurrences of the tilde character ('~') with a hyphen ('-') in certain fields to avoid formatting issues.
     *
     * @param pnote A pointer to the Note object to be appended and written to a file.
     * @return This function does not return a value.
     */

  0.503  note_attach                              — Attaches a new note to a character if none exists.
    /**
     * @fn void note_attach(Character *ch, int type)
     *
     * @brief Attaches a new note to a character if none exists.
     *
     * @details This function checks if the given character already has a note attached. If not, it creates a new Note object, assigns the sender based on whether the character is an NPC or not, sets the note type, and attaches it to the character. The function ensures that a character can only have one note attached at a time.
     *
     * @param ch A pointer to the Character object to which the note will be attached.
     * @param type An integer representing the type of the note to be attached.
     * @return This function does not return a value.
     */

  0.480  is_note_to                               — Determines if a note is addressed to a specific character.
    /**
     * @fn bool is_note_to(Character *ch, Note *pnote)
     *
     * @brief Determines if a note is addressed to a specific character.
     *
     * @details This function checks if a given note is intended for a specific character by evaluating various conditions such as the note's subject, recipient list, and the character's attributes. It first ensures the note is not a forwarded message to the character. It then checks if the note is addressed to followers, specific individuals, groups, or clans, and verifies if the character meets the criteria to receive the note based on their status, clan, or other attributes.
     *
     * @param ch A pointer to the Character object representing the character to check the note against.
     * @param pnote A pointer to the Note object representing the note to be checked.
     * @return Returns true if the note is addressed to the character according to the specified conditions; otherwise, returns false.
     */

  0.476  hide_note                                — Determines if a note should be hidden from a character.
    /**
     * @fn bool hide_note(Character *ch, Note *pnote)
     *
     * @brief Determines if a note should be hidden from a character.
     *
     * @details The function checks whether a note should be hidden from a given character based on several conditions. It first checks if the character is a non-player character (NPC), in which case the note is hidden. It then checks the type of the note and compares the note's timestamp with the character's last read timestamp for that note type. If the note is older or equal to the last read timestamp, it is hidden. Additionally, if the character is the sender of the note or if the note is not addressed to the character, the note is also hidden.
     *
     * @param ch A pointer to the Character object representing the character for whom the note visibility is being checked.
     * @param pnote A pointer to the Note object representing the note whose visibility is being determined.
     * @return Returns true if the note should be hidden from the character based on the specified conditions; otherwise, returns false.
     */

  0.474  note_remove                              — Removes a note or a recipient from a note for a character.
    /**
     * @fn void note_remove(Character *ch, Note *pnote, bool del)
     *
     * @brief Removes a note or a recipient from a note for a character.
     *
     * @details This function handles the removal of a note or a recipient from a note for a given character. If the 'del' parameter is false, it attempts to remove the character as a recipient from the note's recipient list. If the character is not the sender and there are other recipients, the note is updated with the new recipient list. If 'del' is true or the note is to be completely removed, the note is removed from the appropriate list based on its type, and the note is deleted. The function also logs an error if the note is not found in the list.
     *
     * @param ch A pointer to the Character object representing the character performing the removal.
     * @param pnote A pointer to the Note object that is to be removed or modified.
     * @param del A boolean indicating whether the entire note should be deleted (true) or just the character removed from the recipient list (false).
     * @return This function does not return a value.
     */

  0.468  update_read                              — Updates the character's last read timestamp for a specific type of not
    /**
     * @fn void update_read(Character *ch, Note *pnote)
     *
     * @brief Updates the character's last read timestamp for a specific type of note.
     *
     * @details This function updates the last read timestamp for a character based on the type of note they have read. It compares the note's timestamp with the character's current last read timestamp for that note type and updates it if the note's timestamp is more recent. The function handles various types of notes, including general notes, ideas, roleplay notes, immquest notes, changes, personal notes, and trade notes. If the character is an NPC, the function returns immediately without making any updates.
     *
     * @param ch A pointer to the Character object whose note read timestamps are to be updated.
     * @param pnote A pointer to the Note object that contains the timestamp and type of the note being read.
     * @return This function does not return a value.
     */

  0.466  count_spool                              — Counts the number of visible messages for a character in a message lis
    /**
     * @fn int count_spool(Character *ch, Note *spool)
     *
     * @brief Counts the number of visible messages for a character in a message list.
     *
     * @details This function iterates through a linked list of Note objects, referred to as a spool, and counts how many of these notes are visible to a given Character. Visibility is determined by the hide_note function, which checks specific conditions to decide if a note should be hidden from the character. The function returns the total count of notes that are visible to the character.
     *
     * @param ch A pointer to the Character object for whom the visibility of notes is being checked.
     * @param spool A pointer to the first Note object in the linked list of notes to be checked.
     * @return The number of notes in the spool that are visible to the character.
     */

  0.411  save_notes                               — Saves notes of a specified type to a corresponding file.
    /**
     * @fn void save_notes(int type)
     *
     * @brief Saves notes of a specified type to a corresponding file.
     *
     * @details The function 'save_notes' writes all notes of a specified type to a file associated with that type. It selects the appropriate file and note list based on the 'type' parameter, opens the file for writing, and iterates through the list of notes, writing each note's details to the file using formatted output. If the file cannot be opened, an error message is printed using 'perror'.
     *
     * @param type An integer representing the type of notes to save. Each type corresponds to a specific file and list of notes.
     * @return This function does not return a value.
     */


================================================================================
[policy] state_rules  (stability: stable)
  desc: Character state predicates and permission guards: NPC-vs-player checks, immortal and hero tier tests, position checks (a…
  locked: 54 functions, 54 with embeddings
  sim to desc — mean: 0.505  min: 0.347  max: 0.673

  0.673  is_safe_char                             — Determines whether it is safe for a character to attack a victim based
    /**
     * @fn bool is_safe_char(Character *ch, Character *victim, bool showmsg)
     *
     * @brief Determines whether it is safe for a character to attack a victim based on game rules and context.
     *
     * @details Determines whether a character is safe to attack or engage with, considering game rules and context.
    This function evaluates various conditions to decide if 'ch' can safely attack 'victim'. It considers immortality status, current fighting state, NPC and player-specific restrictions, ownership and charm effects, and player-kill flags. It also prevents attacking shopkeepers, trainers, healers, pets, and charmed creatures unless appropriate conditions are met. The function optionally displays messages to 'ch' explaining why an attack is unsafe. It returns true if the attack is unsafe (should be prevented), and false if it is safe to proceed.
     *
     * @param ch Pointer to the Character initiating the action, used to determine attacker status and messaging.
     * @param victim Pointer to the Character being targeted, whose safety status is evaluated.
     * @param showmsg Boolean flag indicating whether to display a message to 'ch' when the attack is disallowed.
     * @return Returns true if the attack is considered unsafe (i.e., the action should be prevented), and false if it is safe to proceed.
     */

  0.666  is_safe                                  — Determines whether an attack from one character to another is consider
    /**
     * @fn bool is_safe(Character *ch, Character *victim, bool showmsg)
     *
     * @brief Determines whether an attack from one character to another is considered safe according to game rules.
     *
     * @details Determines if a character is in a safe location where combat is restricted.
    This function evaluates if it is safe for 'ch' to attack 'victim' based on their current locations and game state. It checks if either character is in a null room, if the victim is in a safe room, in an arena, or in a quest area with PvP enabled. If any of these conditions are met, it returns true (attack is unsafe or disallowed). Otherwise, it delegates the safety check to 'is_safe_char', which applies additional game-specific safety rules. If 'showmsg' is true, it may display messages to 'ch' when an attack is disallowed due to safe room conditions.
     *
     * @param ch A pointer to the Character object representing the potential attacker.
     * @param victim A pointer to the Character object representing the potential victim.
     * @param showmsg A boolean indicating whether to display a message to the attacker if the location is safe.
     * @return Returns true if the location is considered safe and combat is restricted; otherwise, returns false.
     */

  0.658  is_safe_spell                            — Determines if casting a spell on a target character is safe.
    /**
     * @fn bool is_safe_spell(Character *ch, Character *victim, bool area)
     *
     * @brief Determines if casting a spell on a target character is safe.
     *
     * @details Determines if casting a spell on a target is safe.
    This function evaluates various conditions to determine if it is safe for a character (ch) to cast a spell on a target character (victim). It considers factors such as the room's safety status, the characters' roles (NPC or player), their group affiliations, and specific game mechanics like invisibility levels, charm effects, and ongoing battles. The function is designed to prevent illegal or unintended interactions, such as attacking in safe zones or targeting non-opponents in a duel arena.
     *
     * @param ch A pointer to the Character object representing the caster of the spell.
     * @param victim A pointer to the Character object representing the target of the spell.
     * @param area A boolean indicating if the spell affects an area rather than a single target.
     * @return Returns true if casting the spell is considered safe according to the game's rules, otherwise returns false.
     */

  0.638  is_safe_drag                             — Checks whether it is safe to push or drag a victim character in the cu
    /**
     * @fn bool is_safe_drag(Character *ch, Character *victim)
     *
     * @brief Checks whether it is safe to push or drag a victim character in the current game context.
     *
     * @details This function evaluates various conditions to determine if a 'push' or 'drag' action involving the specified victim character is permitted according to game rules. It first verifies that both characters are in valid rooms. It then checks if either character is currently fighting, disallowing action if so. The function prevents self-interaction and interactions with immortal characters, providing appropriate messages. It considers room safety flags and sector types, allowing or disallowing actions based on these conditions. Additionally, it permits such actions in duel arena rooms and within the same quest area if the 'PK' (player-kill) flag is active. If none of these conditions explicitly allow or disallow the action, it defaults to calling 'is_safe_char' to perform a final safety check based on broader game rules.
     *
     * @param ch Pointer to the Character initiating the push/drag action.
     * @param victim Pointer to the Character being pushed or dragged.
     * @return Returns true if the action is considered unsafe or disallowed based on the evaluated conditions; otherwise, returns false, indicating it is safe to proceed.
     */

  0.619  check_attack_ok                          — Checks whether a character can initiate an attack on a victim based on
    /**
     * @fn bool check_attack_ok(Character *ch, Character *victim)
     *
     * @brief Checks whether a character can initiate an attack on a victim based on game rules and conditions.
     *
     * @details This function evaluates multiple game-specific conditions to determine if a character ('ch') is permitted to attack another character ('victim'). It verifies if the attack occurs in an arena that hasn't started, if the attacker is a morphed NPC attempting to attack a player or pet, if the attacker is under fear effects, if the attacker is attempting to attack themselves, if the location is safe, if the victim is already fighting someone else outside the attacker's group, or if the attacker is charmed and loyal to the victim. If any condition fails, it provides appropriate feedback messages and returns false; otherwise, it returns true, indicating the attack is permissible.
     *
     * @param ch Pointer to the Character initiating the attack.
     * @param victim Pointer to the Character being targeted for attack.
     * @return Boolean value indicating whether the attack is allowed (true) or not (false).
     */

  0.607  char_at_war                              — Determines if a character is engaged in any ongoing wars.
    /**
     * @fn bool char_at_war(Character *ch)
     *
     * @brief Determines if a character is engaged in any ongoing wars.
     *
     * @details Checks if a character is currently involved in a war.
    This function checks if a given character is currently involved in any ongoing wars. It first verifies if the character is a non-player character (NPC) by calling the is_npc() method. If the character is an NPC, the function returns false, as NPCs are not considered to be at war. Next, it checks if the character is associated with a clan. If the character does not belong to any clan, the function returns false. Finally, it checks if the character's clan is currently at war by calling the clan_at_war() function. If the clan is at war, the function returns true; otherwise, it returns false.
     *
     * @param ch A pointer to the Character object being checked for participation in any ongoing wars.
     * @return Returns true if the character is participating in an ongoing war, and false otherwise.
     */

  0.590  clan_eq_ok                               — Determines if a character can interact with a clan-owned object.
    /**
     * @fn bool clan_eq_ok(Character *ch, Object *obj, const String &action)
     *
     * @brief Determines if a character can interact with a clan-owned object.
     *
     * @details This function checks whether a character is permitted to perform an action on a given object based on clan ownership and leadership rules. If the character is an immortal, they are always allowed to interact with the object. If the object belongs to a clan different from the character's, the character is informed of the ownership conflict, the object is destroyed, and the function returns false. If the object is designated as leader-only equipment and the character is not a leader, the object is extracted, and the function returns false. Otherwise, the function returns true, indicating the character can interact with the object.
     *
     * @param ch A pointer to the Character object attempting to interact with the object.
     * @param obj A pointer to the Object that the character is attempting to interact with.
     * @param action A constant reference to a String object describing the action the character is attempting to perform on the object.
     * @return Returns true if the character is allowed to interact with the object; otherwise, returns false.
     */

  0.590  check_killer                             — Checks and updates a character's status to become a killer based on co
    /**
     * @fn void check_killer(Character *ch, Character *victim)
     *
     * @brief Checks and updates a character's status to become a killer based on combat interactions and game conditions.
     *
     * @details Checks whether an attack by a character justifies assigning the KILLER flag to them.
    This function evaluates whether a character (ch) should be flagged as a killer after an attack on a victim. It first resolves charm effects to identify the true attacker, then applies several game rules to determine if the attack is considered hostile, including NPC status, player flags (killer, thief), arena conditions, ongoing wars, and quest area flags. If the attack qualifies as hostile and the attacker is not immune or already flagged, the function sets the attacker’s killer status, updates relevant flags, saves the character state, and notifies the attacker. It also handles special cases such as charm effects, NPCs, immortals, and recent combat conditions to prevent false positives.
     *
     * @param ch Pointer to the Character object representing the attacker.
     * @param victim Pointer to the Character object representing the target of the attack.
     * @return Void; the function performs side effects such as setting flags, removing affects, and logging, without returning a value.
     */

  0.590  IS_SPECIAL                               — Determines if a character is considered 'special'.
    /**
     * @fn bool IS_SPECIAL(Character *ch)
     *
     * @brief Determines if a character is considered 'special'.
     *
     * @details This function checks if a given character is 'special', which allows them to bypass certain restrictions typically associated with head and imp flags. It was created by Outsider to replace the IS_SPECIAL macro from merc.h. The function identifies specific characters by name who are considered special, allowing them access to all commands regardless of their rank.
    Explanation: this is a hack. it is not a back door, it is a means to get around the head and imp flags for coders. just because they don't carry the rank of imp or head does not mean they don't need all commands.  Montrey
     *
     * @param ch A pointer to the Character object being evaluated.
     * @return Returns true if the character is special, meaning they are not an NPC and their name is one of the predefined special names. Returns false otherwise.
     */

  0.587  check_all_cond                           — Checks and updates the condition of all equipment worn by a character,
    /**
     * @fn void check_all_cond(Character *ch)
     *
     * @brief Checks and updates the condition of all equipment worn by a character, unless certain effects are active.
     *
     * @details This function iterates through all equipment slots of the specified character, verifying the presence and condition of each item. If an item exists and its condition is valid, it invokes 'check_cond' to assess and potentially modify the item's state, which may include destroying the item. The function skips processing if the character is an NPC, is immortal, or has the 'sheen' affect active, ensuring only relevant characters have their equipment conditions checked.
     *
     * @param ch Pointer to the Character object whose equipment conditions are to be checked.
     * @return Void; the function performs in-place checks and updates without returning a value.
     */

  0.583  Character::is_npc                        — Determines if the character is a non-player character (NPC).
    /**
     * @fn bool Character::is_npc() const
     *
     * @brief Determines if the character is a non-player character (NPC).
     *
     * @details This function checks whether the character is an NPC by verifying if the 'pcdata' member is null. If 'pcdata' is null, it indicates that the character is not a player character, thus it is an NPC.
     *
     * @return Returns true if the character is an NPC (i.e., 'pcdata' is null), otherwise returns false.
     */

  0.577  char_in_darena                           — Checks if a character is in a duel arena.
    /**
     * @fn bool char_in_darena(Character *ch)
     *
     * @brief Checks if a character is in a duel arena.
     *
     * @details Checks if a character is currently in a duel arena.
    This function determines whether a given character is currently in a duel arena by checking the status of their associated duel. It first retrieves the duel associated with the character using the get_duel function. If the character is not in a duel, the function returns false. If the character is in a duel, it checks the duel's accept_timer and prep_timer. If both timers are zero, it indicates that the duel is active and the character is in the duel arena, returning true. Otherwise, it returns false.
     *
     * @param ch A pointer to the Character object for which the duel arena status is being checked.
     * @return Returns true if the character is in an active duel within the duel arena (both accept_timer and prep_timer are zero), otherwise returns false.
     */

  0.564  is_same_clan                             — Determines if two characters belong to the same clan.
    /**
     * @fn bool is_same_clan(Character *ch, Character *victim)
     *
     * @brief Determines if two characters belong to the same clan.
     *
     * @details This function checks if both characters, represented by the pointers 'ch' and 'victim', belong to the same clan. It first ensures that neither character nor their clan pointers are null. If either character is part of an independent clan and is not immortal, the function returns false. Otherwise, it returns true if both characters belong to the same clan.
     *
     * @param ch A pointer to the first Character object to be compared.
     * @param victim A pointer to the second Character object to be compared.
     * @return Returns true if both characters belong to the same clan, false otherwise.
     */

  0.561  help_mob                                 — Checks if a character is improperly assisting or hindering a mobile.
    /**
     * @fn bool help_mob(Character *ch, Character *victim)
     *
     * @brief Checks if a character is improperly assisting or hindering a mobile.
     *
     * @details The function 'help_mob' determines whether a character is attempting to assist or hinder a mobile (non-player character) inappropriately during combat. It checks if the character is not in the same group as the mobile's current opponent and if the mobile is not a pet. If these conditions are met, it sends a message to the character and logs the attempt via the wiznet system, indicating a potential cheating action.
     *
     * @param ch A pointer to the Character object representing the character attempting to assist or hinder.
     * @param victim A pointer to the Character object representing the mobile being assisted or hindered.
     * @return Returns true if the character is attempting to assist or hinder the mobile illegally, otherwise returns false.
     */

  0.560  IS_IMMORTAL                             
    /**
     * @def IS_IMMORTAL
     *
     */

  0.559  check_pulse                              — Checks and updates a character's status during a pulse, handling death
    /**
     * @fn bool check_pulse(Character *victim)
     *
     * @brief Checks and updates a character's status during a pulse, handling death, incapacitation, and recovery scenarios.
     *
     * @details This function evaluates the current health and status of the specified victim character during each pulse. It ensures that immortal characters with negative health are restored to minimal health, provides a chance for characters with the 'Die Hard' skill to recover some health if they are dying, updates their position accordingly, and outputs appropriate messages based on their new status. The function returns true if the character is still alive or recoverable, and false if the character has died. It also manages messaging to the character and the room, and performs skill improvement checks where applicable.
     *
     * @param victim Pointer to the Character object whose status is being checked and potentially updated.
     * @return A boolean value indicating whether the character is still alive or recoverable (true), or has died (false).
     */

  0.549  Character::has_cgroup                    — Checks if the character has any of the specified cgroup flags set.
    /**
     * @fn bool Character::has_cgroup(const Flags &cg) const
     *
     * @brief Checks if the character has any of the specified cgroup flags set.
     *
     * @details This function determines whether a character has any of the flags specified in the 'cg' parameter set in their cgroup flags. If the character is a non-player character (NPC), the function returns false, as NPCs do not have cgroup flags. For player characters, it checks the player's cgroup flags against the provided Flags object.
     *
     * @param cg A Flags object containing the cgroup flags to check against the character's cgroup flags.
     * @return Returns true if the character is a player character and has at least one of the specified cgroup flags set; otherwise, returns false.
     */

  0.546  char_opponents                           — Determines if two characters are opponents in an ongoing war.
    /**
     * @fn bool char_opponents(Character *charA, Character *charB)
     *
     * @brief Determines if two characters are opponents in an ongoing war.
     *
     * @details This function checks if two characters, charA and charB, are engaged in an ongoing war and are on opposing sides. It first verifies if each character is participating in any war by using the char_at_war function. If both characters are at war, it then checks if their respective clans are opponents using the clan_opponents function. The function returns true if both conditions are met, indicating that the characters are opponents in the same war.
     *
     * @param charA A pointer to the first Character object being checked for opposition in an ongoing war.
     * @param charB A pointer to the second Character object being checked for opposition in an ongoing war.
     * @return Returns true if charA and charB are participating in the same ongoing war and are on opposing sides. Returns false if they are not in the same war or are on the same side.
     */

  0.542  char_in_duel                             — Determines if a character is currently engaged in a duel.
    /**
     * @fn bool char_in_duel(Character *ch)
     *
     * @brief Determines if a character is currently engaged in a duel.
     *
     * @details Checks if a character is currently engaged in a duel.
    This function checks if the given character is actively participating in a duel by retrieving the duel associated with the character. If the character is in a duel and the duel's accept timer is zero, it indicates that the duel is active, and the function returns true. Otherwise, it returns false.
     *
     * @param ch A pointer to the Character object for which the duel status is to be checked.
     * @return Returns true if the character is in an active duel (i.e., the duel's accept_timer is zero), otherwise returns false.
     */

  0.531  pers_eq_ok                               — Checks if a character can legitimately use a personalized object.
    /**
     * @fn bool pers_eq_ok(Character *ch, Object *obj, const String &action)
     *
     * @brief Checks if a character can legitimately use a personalized object.
     *
     * @details This function verifies whether a given object is personalized to someone other than the character attempting to use it. If the object is not personalized or is personalized to the character, the function returns true, indicating that the character can use the object. If the object is personalized to someone else, the function sends a denial message to the character, detailing the attempted action and the rightful owner of the object, and returns false. Special handling is provided for immortal characters, allowing them to bypass the ownership restriction.
     *
     * @param ch A pointer to the Character object representing the player attempting to use the object.
     * @param obj A pointer to the Object being checked for personalization.
     * @param action A constant reference to a String object describing the action the character is attempting to perform with the object.
     * @return Returns true if the character can use the object, otherwise returns false.
     */

  0.531  CAN_WEAR                                
    /**
     * @def CAN_WEAR
     *
     */

  0.529  CAN_USE_RSKILL                           — Determines if a character can use a remort skill.
    /**
     * @fn bool CAN_USE_RSKILL(Character *ch, skill::type sn)
     *
     * @brief Determines if a character can use a remort skill.
     *
     * @details This function checks whether a given character is allowed to use a specified remort skill. It first checks if the character is a non-player character (NPC) and if the skill is recognized. For player characters, it verifies if the character is immortal, a remort, and belongs to a guild. It also checks if the character has the required skill level and if the skill belongs to the character's guild or is an extra class skill.
     *
     * @param ch A pointer to the Character object being checked for skill usage.
     * @param sn The skill::type enumeration value representing the skill to be checked.
     * @return Returns true if the character can use the specified remort skill, otherwise returns false.
     */

  0.526  IS_HERO                                 
    /**
     * @def IS_HERO
     *
     */

  0.513  IS_KILLER                               
    /**
     * @def IS_KILLER
     *
     */

  0.512  is_ignoring                              — Checks if a character is ignoring another character.
    /**
     * @fn bool is_ignoring(Character *ch, Character *victim)
     *
     * @brief Checks if a character is ignoring another character.
     *
     * @details This function determines whether the character 'ch' is ignoring the character 'victim'. It first checks if either character is null, returning false if so. It also returns false if the 'victim' is an immortal character. If 'ch' is a player character (not an NPC), it checks the player's ignore list to see if 'victim's name is present. If the name is found in the ignore list, the function returns true, indicating that 'ch' is ignoring 'victim'. Otherwise, it returns false.
     *
     * @param ch The character who may be ignoring another character.
     * @param victim The character who may be ignored by 'ch'.
     * @return Returns true if 'ch' is ignoring 'victim', otherwise returns false.
     */

  0.508  IS_THIEF                                
    /**
     * @def IS_THIEF
     *
     */

  0.506  HAS_RAFF_GROUP                           — Checks if a character has a specific raffect group.
    /**
     * @fn bool HAS_RAFF_GROUP(Character *ch, int flag)
     *
     * @brief Checks if a character has a specific raffect group.
     *
     * @details This function determines whether a given character possesses a raffect that belongs to a specified group. It first checks if the character is a non-player character (NPC) by calling the 'is_npc' method. If the character is an NPC, the function returns false immediately. For player characters, it iterates through the character's raffects, which are determined by the character's remort count divided by 10 plus one. For each raffect, it uses 'raff_lookup' to find the index of the raffect and checks if its group matches the specified flag. If a match is found, the function returns true.
     *
     * @param ch A pointer to the Character object being checked.
     * @param flag An integer representing the raffect group to check for.
     * @return Returns true if the character has a raffect belonging to the specified group, otherwise returns false.
     */

  0.506  gain_condition                           — Adjusts a character's condition based on the specified type and value.
    /**
     * @fn void gain_condition(Character *ch, int iCond, int value)
     *
     * @brief Adjusts a character's condition based on the specified type and value.
     *
     * @details The function modifies the condition of a character, such as hunger, thirst, or drunkenness, by a specified value. It checks if the character is an NPC or immortal, in which case it either returns immediately or sets the condition to a default value. For mortal characters, it adjusts the condition within a valid range and sends a notification if the condition reaches zero, unless the character is in chat mode.
     *
     * @param ch A pointer to the Character object whose condition is to be modified.
     * @param iCond An integer representing the type of condition to be modified (e.g., hunger, thirst, drunkenness).
     * @param value An integer representing the amount by which the condition should be adjusted.
     * @return This function does not return a value.
     */

  0.493  can_drop_obj                             — Determines if a character can drop a specified object.
    /**
     * @fn bool can_drop_obj(Character *ch, Object *obj)
     *
     * @brief Determines if a character can drop a specified object.
     *
     * @details This function checks whether a character is allowed to drop a given object. It first checks if the object has the ITEM_NODROP status, which would normally prevent it from being dropped. If the object does not have this status, the function returns true, allowing the drop. If the object does have the ITEM_NODROP status, the function then checks if the character is immortal. Immortal characters are allowed to drop any object regardless of its status, so the function returns true in this case as well. Otherwise, the function returns false, indicating that the character cannot drop the object.
     *
     * @param ch A pointer to the Character attempting to drop the object.
     * @param obj A pointer to the Object that the character is attempting to drop.
     * @return Returns true if the character can drop the object, otherwise false.
     */

  0.486  IS_HEROIC                               
    /**
     * @def IS_HEROIC
     *
     */

  0.483  align                                    — Changes a character's alignment if conditions are met.
    /**
     * @fn void align(Character *ch, int new_align, char *align_str)
     *
     * @brief Changes a character's alignment if conditions are met.
     *
     * @details The align function attempts to change the alignment of a character to a new specified value. It first checks if the character has enough stamina to perform the alignment change. If stamina is sufficient, it then determines success based on the character's skill level and a random percentile check. On success, the character's alignment is updated, and a success message is sent to the character. On failure, a failure message is sent. In both cases, the function checks and potentially improves the character's alignment skill. The function also imposes a wait state on the character after attempting the alignment change.
     *
     * @param ch A pointer to the Character object whose alignment is being changed.
     * @param new_align An integer representing the new alignment value to be set for the character.
     * @param align_str A pointer to a character array containing the string representation of the new alignment.
     * @return This function does not return a value.
     */

  0.480  HAS_EXTRACLASS                           — Checks if a character has access to an extra class skill.
    /**
     * @fn bool HAS_EXTRACLASS(Character *ch, skill::type sn)
     *
     * @brief Checks if a character has access to an extra class skill.
     *
     * @details The function determines whether a given character has access to a specific extra class skill. It first checks if the skill type is 'unknown' or if the character is a non-player character (NPC), returning false in these cases. For player characters, it calculates the number of extra class slots available based on the character's remort count and checks if the specified skill type is present in the character's extra class skills.
     *
     * @param ch A pointer to the Character object being checked.
     * @param sn The skill::type enumeration value representing the skill to check for.
     * @return Returns true if the character has the specified extra class skill, otherwise returns false.
     */

  0.475  acceptable_sac                           — Determines if an object is an acceptable sacrifice for a character.
    /**
     * @fn bool acceptable_sac(Character *ch, Object *obj)
     *
     * @brief Determines if an object is an acceptable sacrifice for a character.
     *
     * @details This function evaluates whether a given object can be considered an acceptable sacrifice by a character. It checks if the character can see the object, if the object is a player corpse with contents, and if the object has specific attributes that make it unacceptable as a sacrifice. If any of these conditions are met, the function sends an appropriate message to the character and returns false. Otherwise, it returns true, indicating the object is an acceptable sacrifice.
     *
     * @param ch A pointer to the Character object that is evaluating the object for sacrifice.
     * @param obj A pointer to the Object being evaluated as a potential sacrifice.
     * @return Returns true if the object is an acceptable sacrifice for the character; otherwise, returns false.
     */

  0.470  DAZE_STATE                              
    /**
     * @def DAZE_STATE
     *
     */

  0.469  CAN_FLY                                 
    /**
     * @def CAN_FLY
     *
     */

  0.468  IS_REMORT                               
    /**
     * @def IS_REMORT
     *
     */

  0.468  is_same_group                            — Determines if two characters belong to the same group.
    /**
     * @fn bool is_same_group(Character *ach, Character *bch)
     *
     * @brief Determines if two characters belong to the same group.
     *
     * @details This function checks if two Character objects, 'ach' and 'bch', are in the same group by comparing their leaders. If either character is null, the function returns false. If a character has a leader, the function considers the leader as the representative of the group. The function returns true if both characters have the same leader or are the same character, ensuring the equivalence relation properties.
     *
     * @param ach A pointer to the first Character object to compare.
     * @param bch A pointer to the second Character object to compare.
     * @return Returns true if both characters are in the same group, otherwise returns false.
     */

  0.463  WAIT_STATE                              
    /**
     * @def WAIT_STATE
     *
     */

  0.455  IS_AWAKE                                
    /**
     * @def IS_AWAKE
     *
     */

  0.452  CHARTYPE_TEST                           
    /**
     * @def CHARTYPE_TEST
     *
     */

  0.449  Descriptor::is_playing                   — Checks if the descriptor is currently in the playing state.
    /**
     * @fn bool Descriptor::is_playing() const
     *
     * @brief Checks if the descriptor is currently in the playing state.
     *
     * @details This function determines whether the descriptor is in the 'playing' state by checking if the 'state' member is equal to the 'playing' state of the 'conn::State' and if the 'character' member is not a null pointer. It is used to verify if the descriptor is actively engaged in a session.
     *
     * @return Returns true if the descriptor is in the playing state and has a valid character, otherwise returns false.
     */

  0.442  IS_NEUTRAL                              
    /**
     * @def IS_NEUTRAL
     *
     */

  0.435  IS_EVIL                                 
    /**
     * @def IS_EVIL
     *
     */

  0.432  CHARTYPE_MATCH                          
    /**
     * @def CHARTYPE_MATCH
     *
     */

  0.429  is_room_owner                            — Checks if the specified character is the owner of the given room.
    /**
     * @fn bool is_room_owner(Character *ch, Room *room)
     *
     * @brief Checks if the specified character is the owner of the given room.
     *
     * @details This function determines whether the provided character 'ch' is the owner of the specified 'room'. It first verifies if the room has an owner by checking if the owner's name string is non-empty. If the room has no owner, the function returns false. Otherwise, it checks if the character's name matches the owner's name by searching for the character's name within the owner's name string, using a word-based matching criteria. The function returns true if the character's name is found within the owner's name, indicating ownership; otherwise, it returns false.
     *
     * @param ch Pointer to the Character object representing the character to check ownership for.
     * @param room Pointer to the Room object representing the room in question.
     * @return A boolean value indicating whether the character 'ch' is the owner of the 'room'. Returns true if 'ch' is the owner; otherwise, false.
     */

  0.428  from_box_ok                              — Determines if an object can be taken from a specified container by a c
    /**
     * @fn bool from_box_ok(Character *ch, Object *obj, char *box_type)
     *
     * @brief Determines if an object can be taken from a specified container by a character.
     *
     * @details This function checks whether a character can take an object from a specified container type. It verifies that the object exists, can be taken, and that the character has the capacity to carry both the number and weight of the object. If any condition fails, an appropriate message is sent to the character, and the function returns false.
     *
     * @param ch A pointer to the Character attempting to take the object.
     * @param obj A pointer to the Object being checked for removal from the container.
     * @param box_type A string representing the type of container from which the object is being taken.
     * @return Returns true if the character can take the object from the container; otherwise, returns false.
     */

  0.420  IS_IMM_GROUP                            
    /**
     * @def IS_IMM_GROUP
     *
     */

  0.411  IS_GOOD                                 
    /**
     * @def IS_GOOD
     *
     */

  0.408  add_follower                             — Assigns a new follower to a character, establishing a master-follower 
    /**
     * @fn void add_follower(Character *ch, Character *master)
     *
     * @brief Assigns a new follower to a character, establishing a master-follower relationship.
     *
     * @details Assigns a new follower (master) to a character if they are not already following someone.
    This function sets the specified character 'ch' to follow the 'master' character. It first checks if 'ch' already has a master; if so, it logs a bug message and exits. Otherwise, it assigns 'master' as 'ch's master and clears 'ch's leader. If the master can see 'ch', it sends a message to the master indicating that 'ch' now follows them. Additionally, it notifies 'ch' that they are now following the master. The function does not return a value.
     *
     * @param ch Pointer to the Character object to be assigned as a follower.
     * @param master Pointer to the Character object who will become the new master.
     * @return This function has no return value; it performs side effects such as updating follower relationships and sending messages.
     */

  0.403  die_follower                             — Handles the process of a character dying and properly removing all fol
    /**
     * @fn void die_follower(Character *ch)
     *
     * @brief Handles the process of a character dying and properly removing all follower and pet associations.
     *
     * @details Handles the process of a character dying and properly updating follower and master relationships.
    This function manages the cleanup when a character dies by removing the character from any follower or pet relationships. It checks if the character has a master, and if so, clears the character from the master's pet or special entity pointers (such as skeleton, zombie, wraith, gargoyle). It then calls 'stop_follower' to cease following behavior and clears the character's leader pointer. Additionally, it iterates through all characters in the game world, stopping any followers that have the dying character as their master, and resets leader pointers for characters who follow the dying character, effectively removing all associations related to the character's death.
     *
     * @param ch Pointer to the Character object representing the character that is dying and whose follower relationships are to be cleaned up.
     * @return Void; the function performs side effects such as updating relationships and stopping followers without returning a value.
     */

  0.383  OUTRANKS                                
    /**
     * @def OUTRANKS
     *
     */

  0.371  IS_IMP                                  
    /**
     * @def IS_IMP
     *
     */

  0.352  RANK                                    
    /**
     * @def RANK
     *
     */

  0.347  IS_HEAD                                 
    /**
     * @def IS_HEAD
     *
     */


================================================================================
[projection] display  (stability: provisional)
  desc: Information rendering and display assembly: room description and contents display, character appearance in room (short a…
  locked: 27 functions, 26 with embeddings
  sim to desc — mean: 0.508  min: 0.302  max: 0.657
  ⚠ missing from pool: show_list_to_char

  0.657  format_rstat                             — Formats and displays detailed information about a specified room to a 
    /**
     * @fn void format_rstat(Character *ch, Room *location)
     *
     * @brief Formats and displays detailed information about a specified room to a character.
     *
     * @details This function generates a comprehensive report of a room's properties, including its name, area, sector type, lighting, healing and mana rates, clan and guild affiliations, description, extra descriptions, flags, occupants, objects, exits, and active affects. It outputs this information to the character's output buffer using formatted text, providing a structured overview suitable for in-game inspection or debugging. The function accesses various room attributes and related entities, and iterates through lists of characters, objects, exits, and affects to include their details in the report.
     *
     * @param ch Pointer to the Character object receiving the formatted room information.
     * @param location Pointer to the Room object representing the room to be described.
     * @return Void; the function outputs the formatted room status directly to the character's output buffer.
     */

  0.600  format_obj_to_char                       — Formats an object's description for display to a character.
    /**
     * @fn String format_obj_to_char(Object *obj, Character *ch, bool fShort)
     *
     * @brief Formats an object's description for display to a character.
     *
     * @details This function generates a formatted string representation of an object's description as perceived by a character. It includes various visual indicators based on the object's properties, such as invisibility, magical auras, and temporary weapon effects. The function also considers the character's abilities to detect certain properties and adjusts the description accordingly. If the character is on a quest involving the object, a special target marker is added. The function can return either a short or full description based on the 'fShort' parameter. Additionally, if the character has a specific flag set, the function appends a relative power level indicator comparing the object's level to the character's usable level.
     *
     * @param obj A pointer to the Object whose description is being formatted.
     * @param ch A pointer to the Character for whom the object's description is being formatted.
     * @param fShort A boolean indicating whether to return the short description (true) or the full description (false) of the object.
     * @return A String object containing the formatted description of the object, including any relevant status indicators and power level comparisons.
     */

  0.598  list_exits                               — Generates a string listing the exits visible to a character in a room.
    /**
     * @fn const String list_exits(Character *ch, bool fAuto)
     *
     * @brief Generates a string listing the exits visible to a character in a room.
     *
     * @details This function constructs a string that lists all the visible exits from the room a character is currently in. The format of the output depends on whether the function is called in 'auto' mode or not. In 'auto' mode, the exits are listed in a compact format, while in non-auto mode, additional details such as room names and statuses (e.g., closed, too dark) are included. The function checks each possible exit direction and determines if the character can see the room beyond the exit. It also considers the character's abilities, such as night vision, and the room's properties, such as darkness, to determine what information to display.
     *
     * @param ch A pointer to the Character object for whom the exits are being listed.
     * @param fAuto A boolean flag indicating whether to use the compact 'auto' format for the output.
     * @return A String object containing the formatted list of exits visible to the character, based on the specified format.
     */

  0.589  show_char_to_char                        — Displays characters in a room to a specified character.
    /**
     * @fn void show_char_to_char(Character *list, Character *ch)
     *
     * @brief Displays characters in a room to a specified character.
     *
     * @details This function iterates over a list of characters in a room and displays each character to a specified character (ch), except for the character itself. If the specified character can see another character, detailed information about that character is shown. If the room is dark but not very dark, and the other character has the night vision affect, a message indicating glowing eyes is sent to the specified character.
     *
     * @param list A pointer to the first Character object in the list of characters present in the room.
     * @param ch A pointer to the Character object representing the character to whom the information is being displayed.
     * @return This function does not return a value.
     */

  0.583  show_char_to_char_0                      — Displays detailed information about a character to another character.
    /**
     * @fn void show_char_to_char_0(Character *victim, Character *ch)
     *
     * @brief Displays detailed information about a character to another character.
     *
     * @details The function 'show_char_to_char_0' constructs and sends a formatted string describing the 'victim' character's status and attributes to the 'ch' character. It checks various conditions such as whether the victim is an NPC, their current status effects, and their position, appending appropriate tags and descriptions to the output string. The function also handles color settings for the output based on the character's attributes and status.
     *
     * @param victim A pointer to the Character object representing the character being described.
     * @param ch A pointer to the Character object representing the character receiving the description.
     * @return This function does not return a value.
     */

  0.581  scan_room                                — Displays a description and contents of a specified room to a character
    /**
     * @fn void scan_room(Room *room, Character *ch, int depth, int door, Exit *pexit)
     *
     * @brief Displays a description and contents of a specified room to a character.
     *
     * @details This function outputs information about a given room to the specified character, including the direction or location indicator, the room's name, and its sector type. It checks if the exit in the specified direction is closed or if the character can see inside the room (considering darkness or visibility conditions). If the exit is closed, it indicates so; if the room is too dark to see, it notifies the character accordingly. Otherwise, it displays the room's name and sector type, and proceeds to scan and list visible characters within the room. The function uses helper functions to retrieve direction names, check exit flags, determine visibility, and look up sector names, and it outputs formatted text to the character's output buffer.
     *
     * @param room Pointer to the Room object representing the room to be examined.
     * @param ch Pointer to the Character object who is receiving the description.
     * @param depth Integer indicating the depth level for scanning characters within the room.
     * @param door Integer representing the direction index; used to identify the exit direction.
     * @param pexit Pointer to an Exit object associated with the room, used to check exit flags.
     * @return Void; the function performs output operations to the character's buffer without returning a value.
     */

  0.579  format_ostat                             — Formats and displays detailed information about a game object to a cha
    /**
     * @fn void format_ostat(Character *ch, Object *obj)
     *
     * @brief Formats and displays detailed information about a game object to a character.
     *
     * @details The function 'format_ostat' generates a comprehensive report of an object's attributes, including its identifiers, descriptions, values, and associated affects. It sends this information to a specified character's output buffer. The report includes object-specific details such as extra descriptions, ownership, weight, and type-specific attributes like weapon damage or armor class. Additionally, it lists any affects or settings the object has, and details about any gems contained within the object.
     *
     * @param ch A pointer to the Character object that will receive the formatted object information.
     * @param obj A pointer to the Object whose details are to be formatted and displayed.
     * @return This function does not return a value.
     */

  0.579  score_new                                — Displays a detailed score sheet for a character.
    /**
     * @fn void score_new(Character *ch)
     *
     * @brief Displays a detailed score sheet for a character.
     *
     * @details The function 'score_new' generates and displays a comprehensive score sheet for a given character, detailing various attributes, statistics, and status information. It formats the output with specific color codes and aligns text to create a visually structured display. The score sheet includes the character's name, title, level, age, attributes, health, mana, stamina, wealth, carrying capacity, armor class, combat statistics, quest points, skill points, alignment, experience, and position. If the character is not an NPC, it also shows player-kill records and arena statistics. Additionally, if the character has the 'COMM_SHOW_AFFECTS' flag set, it displays active affects.
     *
     * @param ch A pointer to the Character object for whom the score sheet is being generated and displayed.
     * @return This function does not return a value.
     */

  0.567  print_new_affects                        — Displays the active affects on a character.
    /**
     * @fn void print_new_affects(Character *ch)
     *
     * @brief Displays the active affects on a character.
     *
     * @details The function print_new_affects gathers and formats information about the various affects currently influencing a given character, including spells, equipment spells, racial abilities, and remort affects. It organizes these affects into categories, formats them with color codes, and outputs the result to the character's display buffer. If no affects are present, it informs the character that they are not affected by any spells.
     *
     * @param ch A pointer to the Character object whose affects are to be displayed.
     * @return This function does not return a value.
     */

  0.565  World::get_minimap                       — Generates a minimap representation centered around a character's curre
    /**
     * @fn void World::get_minimap(Character *ch, std::vector< String > &v) const
     *
     * @brief Generates a minimap representation centered around a character's current location.
     *
     * @details This function constructs a textual minimap of the surrounding area for a given character, based on the character's current room location. It populates the provided vector with strings, each representing a line of the map. The map includes terrain types, other characters visible to the character, and highlights the character's current position. It accounts for map boundaries and only displays valid map areas, using specific symbols and colors to denote different terrain and entities. The function does not return a value but modifies the input vector to contain the visual map lines.
     *
     * @param ch Pointer to the Character object for whom the minimap is generated; used to determine the center position and visibility.
     * @param vec Reference to a vector of String objects where each string represents a line of the generated minimap.
     * @return Void; the function populates the provided vector with the minimap lines based on the character's surroundings.
     */

  0.562  show_char_to_char_1                      — Displays detailed information about a character to another character, 
    /**
     * @fn void show_char_to_char_1(Character *victim, Character *ch)
     *
     * @brief Displays detailed information about a character to another character, including appearance, status, equipment, and optional inventory peek.
     *
     * @details This function outputs a comprehensive view of a victim character to a viewing character, including their description, condition, kill statistics, deity, age, equipped items, and optionally their inventory if the viewer has the 'peek' skill and conditions are met. It handles visibility checks, color formatting, and special cases for NPCs and players, providing a formatted and colored report suitable for in-game character inspection.
     *
     * @param victim Pointer to the Character being inspected.
     * @param ch Pointer to the Character who is inspecting or viewing the victim.
     * @return Void; the function outputs information directly to the character's output buffer and does not return a value.
     */

  0.552  show_affect_to_char                      — Displays the details of an affect to a character.
    /**
     * @fn void show_affect_to_char(const affect::Affect *paf, Character *ch)
     *
     * @brief Displays the details of an affect to a character.
     *
     * @details The function 'show_affect_to_char' constructs a formatted string describing the properties of a given affect and sends it to a character's output buffer. It includes the affect's type, location, modifier, level, duration, and any associated bit flags. The output is tailored based on the affect's attributes and the character's status, such as being an immortal.
     *
     * @param paf A pointer to an affect::Affect object representing the affect whose details are to be displayed.
     * @param ch A pointer to a Character object representing the recipient of the affect details.
     * @return This function does not return a value.
     */

  0.515  Weather::describe                        — Describes the current weather conditions.
    /**
     * @fn const String Weather::describe() const
     *
     * @brief Describes the current weather conditions.
     *
     * @details This function generates a description of the current weather by selecting a phrase that describes the sky's appearance and the prevailing wind conditions. The description is formatted into a complete sentence using the Format::format function. The sky's appearance is determined by an index into a predefined array of strings, which may vary based on compile-time conditions such as the SEASON_CHRISTMAS macro. The wind description is chosen based on the value of the 'change' variable, indicating whether the wind is warm or cold.
     *
     * @return A String object containing a formatted description of the current weather conditions, including the sky's appearance and the wind's nature.
     */

  0.504  Room::description                        — Retrieves the description of the room.
    /**
     * @fn const String & Room::description() const
     *
     * @brief Retrieves the description of the room.
     *
     * @details This function returns a constant reference to the description of the room, which is stored in the prototype object. It provides a way to access the room's description without modifying it.
     *
     * @return A constant reference to a String object representing the room's description.
     */

  0.501  Room::extra_descr                        — Retrieves the extra description associated with the room.
    /**
     * @fn const ExtraDescr * Room::extra_descr() const
     *
     * @brief Retrieves the extra description associated with the room.
     *
     * @details This function returns a pointer to an ExtraDescr object that contains additional descriptive data for the room. It accesses the extra description from the room's prototype, providing a way to obtain extended information about the room's characteristics or features.
     *
     * @return A pointer to an ExtraDescr object representing the additional descriptive data for the room, or nullptr if no extra description is available.
     */

  0.501  count_players                            — Counts the number of characters a given character can see in the WHO l
    /**
     * @fn char * count_players(Character *ch)
     *
     * @brief Counts the number of characters a given character can see in the WHO list.
     *
     * @details This function iterates over a global list of descriptors to count how many characters are currently playing and visible to the specified character. It then formats a message indicating the number of visible characters and compares it to the record number of players since the last reboot. The message is stored in a static buffer and returned.
     *
     * @param ch The character for whom the visible player count is being determined.
     * @return A pointer to a static character buffer containing a formatted message about the number of visible characters and the record number since last reboot.
     */

  0.497  evolve_info                              — Displays a list of currently evolvable skills and spells for a charact
    /**
     * @fn void evolve_info(Character *ch)
     *
     * @brief Displays a list of currently evolvable skills and spells for a character.
     *
     * @details The function constructs a formatted string that lists all skills and spells that can currently be evolved by the character, categorized by guild. It calculates the potential evolution points for each guild and displays them in a tabular format. The resulting information is then sent to the character's output buffer for display.
     *
     * @param ch A pointer to the Character object for whom the evolvable skills and spells are being displayed.
     * @return This function does not return a value.
     */

  0.491  format_war_list                          — Formats and displays a list of clans involved in a war to a character.
    /**
     * @fn void format_war_list(Character *ch, War *war, bool current)
     *
     * @brief Formats and displays a list of clans involved in a war to a character.
     *
     * @details This function generates a formatted list of clans participating in a war, including their names and scores, and sends this list to a specified character's output buffer. It handles both the challenging and defending clans, ensuring that the display is balanced and visually aligned. The function checks for the number of clans on each side, logs errors if the war is one-sided or has too many clans, and uses formatted strings to create a visually appealing output.
     *
     * @param ch A pointer to the Character object whose output buffer will receive the formatted war list.
     * @param war A pointer to the War object containing the state and details of the war, including the clans involved.
     * @param current A boolean indicating whether to use the current scores of the clans (if true) or their final scores (if false).
     * @return This function does not return a value.
     */

  0.480  RoomID::to_string                        — Converts the RoomID to a string representation.
    /**
     * @fn const String RoomID::to_string(bool short_loc=true) const
     *
     * @brief Converts the RoomID to a string representation.
     *
     * @details This function generates a string representation of the RoomID. If the RoomID is invalid, it returns the string '(null)'. For a valid RoomID, it constructs a string that includes the room number and virtual number (vnum). The format of the string depends on the 'short_loc' parameter: if 'short_loc' is true, the room number and vnum are formatted with minimal padding; otherwise, they are formatted with additional padding for alignment.
     *
     * @param short_loc Determines the formatting style of the output string. If true, the output is more compact; if false, it includes additional padding for alignment.
     * @return A String object representing the RoomID. It returns '(null)' if the RoomID is invalid, or a formatted string containing the room number and vnum if the RoomID is valid.
     */

  0.476  format_war_events                        — Formats and sends a list of war events to a character's output buffer.
    /**
     * @fn void format_war_events(Character *ch, War *war)
     *
     * @brief Formats and sends a list of war events to a character's output buffer.
     *
     * @details This function iterates over the events of a given war and formats each event into a human-readable string. It first formats and displays a list of clans involved in the war, then processes each event in the war's event history. Depending on the type of event, it constructs a specific message using the event's data, such as the time of the event or the participants involved. These messages are accumulated into an output string, which is then sent to the specified character's output buffer for display.
     *
     * @param ch A pointer to the Character object whose output buffer will receive the formatted war events.
     * @param war A pointer to the War object containing the state and details of the war, including the events to be formatted.
     * @return This function does not return a value.
     */

  0.438  Location::to_string                      — Converts the object to a string representation based on its validity.
    /**
     * @fn const String Location::to_string(bool short_loc=true) const
     *
     * @brief Converts the object to a string representation based on its validity.
     *
     * @details This function attempts to convert the object to a string representation. It first checks if the 'coord' object is valid. If 'coord' is valid, it returns the string representation of the coordinate using 'coord.to_string'. If 'coord' is not valid, it returns the string representation of the 'room_id' using 'room_id.to_string'. The format of the output string is determined by the 'short_loc' parameter, which specifies whether the output should be compact or padded.
     *
     * @param short_loc Determines the format of the output string. If true, the output is more compact; if false, it includes additional padding for alignment.
     * @return A String object representing the formatted coordinates if 'coord' is valid, or the RoomID if 'coord' is not valid. Returns '(null)' if both are invalid.
     */

  0.435  Exit::description                        — Retrieves the description of the exit.
    /**
     * @fn const String & Exit::description() const
     *
     * @brief Retrieves the description of the exit.
     *
     * @details This function returns a reference to the description of the exit, which is stored in the prototype object. It provides a way to access the descriptive text associated with the exit without modifying it.
     *
     * @return A constant reference to a String object representing the description of the exit.
     */

  0.358  worldmap::Coordinate::to_string          — Converts the coordinate to a string representation.
    /**
     * @fn const String worldmap::Coordinate::to_string(bool short_loc=true) const
     *
     * @brief Converts the coordinate to a string representation.
     *
     * @details This function returns a string representation of the Coordinate object. If the coordinate is invalid (i.e., 'x' is negative), it returns the string '(null)'. Otherwise, it formats the coordinate values 'x' and 'y' into a string. The format of the string depends on the 'short_loc' parameter: if 'short_loc' is true, the coordinates are formatted without padding; if false, they are formatted with padding to ensure a width of 4 characters for each coordinate.
     *
     * @param short_loc Determines the format of the output string. If true, the coordinates are formatted without padding; if false, they are formatted with padding.
     * @return A String object representing the formatted coordinates, or '(null)' if the coordinate is invalid.
     */

  0.356  condition_lookup                         — Determines the condition description based on a numeric condition valu
    /**
     * @fn String condition_lookup(int condition)
     *
     * @brief Determines the condition description based on a numeric condition value.
     *
     * @details Determines the condition description based on a numeric value.
    This function takes an integer representing a condition and returns a corresponding string description. The condition value is evaluated against predefined thresholds to categorize it into one of several descriptive states such as 'perfect', 'good', 'average', etc. The function handles both positive and negative condition values, providing a specific description for each range.
     *
     * @param condition An integer representing the condition value to be evaluated.
     * @return A String object containing the condition description, such as 'perfect', 'good', 'average', 'worn', 'damaged', 'broken', 'ruined', 'indestructable', or 'unknown'.
     */

  0.339  GameTime::day_string                     — Returns the current day of the game as a string with an ordinal suffix
    /**
     * @fn const String GameTime::day_string() const
     *
     * @brief Returns the current day of the game as a string with an ordinal suffix.
     *
     * @details The function calculates the current day of the game, adjusting for 0-based indexing, and appends the appropriate ordinal suffix ('st', 'nd', 'rd', 'th') based on English grammar rules. It then formats this information into a string using the Format::format function.
     *
     * @return A String object representing the current day of the game with an ordinal suffix, formatted as a string.
     */

  0.302  Exit::dir_name                           — Retrieves the name of a direction based on its index, optionally rever
    /**
     * @fn const String & Exit::dir_name(unsigned int dir, bool reverse=false)
     *
     * @brief Retrieves the name of a direction based on its index, optionally reversing it.
     *
     * @details This function returns the name of a direction corresponding to a given index. The direction can be optionally reversed using the 'reverse' parameter. The function supports six primary directions: north, east, south, west, up, and down. The index is normalized to ensure it is within the valid range of 0 to 5. If 'reverse' is true, the function uses Exit::rev_dir to find the reverse direction before returning the name.
     *
     * @param dir An unsigned integer representing the direction index to be converted to a name.
     * @param reverse A boolean flag indicating whether to reverse the direction before retrieving its name.
     * @return A constant reference to a String object representing the name of the direction, potentially reversed.
     */


================================================================================
[domain] objects  (stability: likely_split)
  desc: Object lifecycle and manipulation: creating objects from prototypes, cloning, extracting and destroying objects, transfe…
  locked: 43 functions, 43 with embeddings
  sim to desc — mean: 0.517  min: 0.296  max: 0.629

  0.629  vape_ceq_recursive                       — Recursively vaporizes clan equipment objects, removing them from the g
    /**
     * @fn Object * vape_ceq_recursive(Character *ch, Object *obj, int depth)
     *
     * @brief Recursively vaporizes clan equipment objects, removing them from the game world and returning the surviving contents.
     *
     * @details This function performs a recursive traversal starting from the specified object, processing linked objects in the contents, gems, and next_content lists. It destroys objects identified as clan equipment based on their vnum range relative to the character's clan area, optionally notifying the character of explosions. It handles special cases such as money items, which are converted into the character's currency and then removed. The function updates ownership references, removes objects from the game with extract_obj, and reconstructs the object lists to exclude destroyed items, ultimately returning the list of surviving objects that remain after vaporization.
     *
     * @param ch Pointer to the Character object performing the vaporization, used for notifications and currency updates.
     * @param obj Pointer to the Object to be processed and potentially vaporized.
     * @param depth Integer representing the current recursion depth, used to control explosion effects and processing logic.
     * @return A pointer to the list of surviving objects after vaporization, which may be null if all objects are destroyed.
     */

  0.612  obj_to_char                              — Transfers an object to a character's inventory.
    /**
     * @fn void obj_to_char(Object *obj, Character *ch)
     *
     * @brief Transfers an object to a character's inventory.
     *
     * @details Assigns an object to a character's inventory.
    This function takes an object and assigns it to a character's inventory. It updates the object's pointers to reflect its new state, indicating that it is now carried by the specified character. The function sets the object's location pointers to null, indicating it is no longer in a locker, strongbox, room, or another object. Additionally, the object's clean timer is reset to zero.
     *
     * @param obj The object to be assigned to the character's inventory.
     * @param ch The character who will receive the object.
     * @return This function does not return a value.
     */

  0.611  obj_repair                               — Repairs a specified object, either by a character in the room or via a
    /**
     * @fn void obj_repair(Character *ch, Object *obj)
     *
     * @brief Repairs a specified object, either by a character in the room or via an NPC blacksmith, restoring its condition.
     *
     * @details This function allows a character to repair a game object, restoring its condition to maximum or a specified level. If an NPC with the 'spec_blacksmith' special function is present in the room, the repair is performed by that NPC, consuming stamina and possibly improving the skill. If no such NPC is present, the character can repair the object directly if they have the required repair skill and sufficient stamina, with a chance of failure that may damage the object further or destroy it. If the character lacks the skill or stamina, or does not have enough money for repairs, the process is aborted. The function updates the object's condition, handles destruction if the object is fully damaged, and provides appropriate feedback messages to the character and room.
     *
     * @param ch Pointer to the Character performing the repair, either directly or via NPC assistance.
     * @param obj Pointer to the Object to be repaired.
     * @return This function has no return value; it performs side effects such as updating object condition, deducting stamina and currency, and sending messages to characters.
     */

  0.606  wear_obj                                 — Handles the process of wearing, wielding, or holding an object by a ch
    /**
     * @fn void wear_obj(Character *ch, Object *obj, bool fReplace)
     *
     * @brief Handles the process of wearing, wielding, or holding an object by a character, including checks for class, level, restrictions, and equipment slots.
     *
     * @details Handles the process of wearing, wielding, or holding an object by a character, including permission checks and equipment management.
    Attempts to equip a character with a specified object.
    This function attempts to equip a specified object onto a character, performing various validation checks such as clan and personal equipment restrictions, level requirements, class restrictions, and item-specific conditions (e.g., rings, weapons, shields). It manages the removal of existing items if necessary, provides appropriate messaging to the character and room, and updates the character's equipment slots accordingly. If the object cannot be equipped due to restrictions or lack of free slots, it aborts the operation. The function also handles special item types like wedding rings, lights, and weapons, with specific logic for each. If 'fReplace' is true, it allows replacing existing equipment; otherwise, it prevents overwriting.
     *
     * @param ch Pointer to the Character object attempting to wear or wield the item.
     * @param obj Pointer to the Object to be equipped or used.
     * @param fReplace Boolean indicating whether to replace existing equipment if the slot is occupied.
     * @return Void; the function performs equipment actions and messaging without returning a value.
     */

  0.605  generate_eq                              — Generates and initializes a new equipment object based on specified le
    /**
     * @fn Object * generate_eq(int objlevel)
     *
     * @brief Generates and initializes a new equipment object based on specified level.
     *
     * @details This function creates a new game equipment object by determining its item level, quality, and type through a series of random rolls. It selects an appropriate object prototype, assigns a name, and adds base statistics and modifications based on the object's quality and type. The function handles unique and set items differently by selecting prototypes with specific keywords and adjusting the object's name accordingly. The final object is returned with its attributes set, ready for use in the game.
     *
     * @param objlevel An integer representing the level at which the equipment object is generated, influencing its item level and properties.
     * @return A pointer to the newly created Object, or nullptr if an error occurs during creation.
     */

  0.604  vape_ceq                                 — Vaporizes a character's carried clan equipment objects recursively.
    /**
     * @fn void vape_ceq(Character *ch)
     *
     * @brief Vaporizes a character's carried clan equipment objects recursively.
     *
     * @details This function initiates the vaporization process of all clan equipment objects carried by the specified character. It updates the character's carrying list by removing vaporized objects and replacing it with the list of surviving objects returned by vape_ceq_recursive. The process handles nested objects and ensures proper removal of clan equipment from the game world, reflecting any changes in the character's inventory after vaporization.
     *
     * @param ch Pointer to the Character object whose carried clan equipment is to be vaporized.
     * @return This function has no return value; it modifies the character's carrying list directly.
     */

  0.588  forge_flag                               — Handles forging of weapon flags on a weapon object by a character, inc
    /**
     * @fn void forge_flag(Character *ch, const String &argument, Object *anvil)
     *
     * @brief Handles forging of weapon flags on a weapon object by a character, including validation, resource deduction, and applying effects.
     *
     * @details This function allows a character to forge special flags onto a weapon object, such as poison, sharpness, or elemental enhancements, using an anvil. It first verifies that the character is wielding a weapon and that the weapon meets level requirements. It then parses the input argument to identify the desired flag type and checks if the weapon already has conflicting or maximum allowed flags. Based on the character's evolution level and ownership status of the anvil, it calculates the quest point cost, deducts it, and attempts to apply the new flag with a chance of success. On success, it applies the effect to the weapon, possibly transforming it (e.g., making it two-handed or exploding it if forging fails). The function provides appropriate feedback messages throughout and updates the weapon's state accordingly.
     *
     * @param ch Pointer to the Character performing the forging action.
     * @param argument String containing the name of the flag to forge onto the weapon.
     * @param anvil Object representing the anvil used for forging, affecting cost calculations.
     * @return This function has no return value; it performs side effects such as modifying the weapon, deducting quest points, and sending messages to characters and room.
     */

  0.584  add_base_stats                           — Adds base statistics to an Object based on its type, level, and qualit
    /**
     * @fn void add_base_stats(Object *obj, int ilevel, int item_qual)
     *
     * @brief Adds base statistics to an Object based on its type, level, and quality.
     *
     * @details This function modifies an Object's attributes by setting its base statistics according to its item type, level, and quality. For armor items, it adjusts the armor class values based on predefined ranges and quality modifiers. For weapon items, it sets damage dice values based on the item's level and quality. Additionally, the function applies random base attributes such as hit points, mana, stamina, hitroll, and damroll to the object with specified chances, using the object's level to determine the range of these attributes.
     *
     * @param obj A pointer to the Object whose base statistics are being modified.
     * @param ilevel An integer representing the level category of the item, which determines the range of base statistics.
     * @param item_qual An integer representing the quality of the item, which affects the modification of base statistics.
     * @return This function does not return a value.
     */

  0.580  create_object                            — Creates and initializes a new game object from a prototype.
    /**
     * @fn Object * create_object(ObjectPrototype *pObjIndex, int level)
     *
     * @brief Creates and initializes a new game object from a prototype.
     *
     * @details Creates a new game object from a given prototype.
    This function creates an instance of an Object using the provided ObjectPrototype and initializes its properties based on the prototype's attributes. It handles memory allocation and checks for errors, logging any issues encountered. The function also adjusts specific object properties based on the item type and applies any affects from the prototype to the new object. Finally, the object is added to the world's object list, and the prototype's count is incremented.
     *
     * @param pObjIndex A pointer to the ObjectPrototype from which the new Object will be created. It must not be null.
     * @param level An integer representing the level of the object, which may influence its properties or behavior.
     * @return A pointer to the newly created Object, or null if the creation fails due to a null prototype or memory allocation error.
     */

  0.576  equip_char                               — Equips an object to a character at a specified wear location.
    /**
     * @fn void equip_char(Character *ch, Object *obj, int iWear)
     *
     * @brief Equips an object to a character at a specified wear location.
     *
     * @details Equips a character with a specified object at a given wear location.
    This function attempts to equip a given object to a character at a specified wear location. It first checks if another object is already equipped at that location and logs a bug if so, without equipping the new object. If no other object is equipped, it adjusts the character's armor class based on the object's properties and applies any affects associated with the object to the character. If the object is a light source and has a non-zero light value, it increases the light level in the character's current room.
     *
     * @param ch A pointer to the Character who is being equipped with the object.
     * @param obj A pointer to the Object that is to be equipped on the character.
     * @param iWear An integer representing the wear location on the character where the object should be equipped.
     * @return This function does not return a value.
     */

  0.571  clone_object                             — Duplicates an object, excluding its contents.
    /**
     * @fn void clone_object(Object *parent, Object *clone)
     *
     * @brief Duplicates an object, excluding its contents.
     *
     * @details Clones the attributes and affects of a parent object to a clone object.
    This function creates an exact duplicate of a given object, copying all attributes from the parent object to the clone, except for its contents. It initializes the clone's attributes such as name, description, item type, and other properties. It also duplicates the affect list and extended descriptions from the parent object to the clone. Any existing affects on the clone are removed before copying new ones from the parent.
     *
     * @param parent A pointer to the Object that serves as the source of attributes and affects to be cloned.
     * @param clone A pointer to the Object that will receive the cloned attributes and affects from the parent.
     * @return This function does not return a value.
     */

  0.557  obj_to_strongbox                         — Adds an object to a character's strongbox.
    /**
     * @fn void obj_to_strongbox(Object *obj, Character *ch)
     *
     * @brief Adds an object to a character's strongbox.
     *
     * @details This function places a given object into the strongbox of a character. It first checks if the character is a non-player character (NPC). If the character is an NPC, it logs a bug message and exits without performing any operations. If the character is not an NPC, the object is added to the character's strongbox, and its location pointers are updated to reflect its new position in the strongbox.
     *
     * @param obj A pointer to the Object that is to be added to the character's strongbox.
     * @param ch A pointer to the Character whose strongbox the object will be added to.
     * @return This function does not return a value.
     */

  0.555  obj_to_keeper                            — Inserts an object into a character's inventory, handling duplicates ap
    /**
     * @fn void obj_to_keeper(Object *obj, Character *ch)
     *
     * @brief Inserts an object into a character's inventory, handling duplicates appropriately.
     *
     * @details This function places an object into the specified character's inventory. It checks for duplicates by comparing the object's index data and short description with those of existing items in the inventory. If a duplicate is found and the item is marked as unlimited (ITEM_INVENTORY), the new object is removed. Otherwise, the new object is inserted into the inventory, maintaining the cost of the existing item if a duplicate is found. The object's pointers are updated to reflect its new location in the character's inventory.
     *
     * @param obj A pointer to the Object that is to be inserted into the character's inventory.
     * @param ch A pointer to the Character whose inventory the object is being inserted into.
     * @return This function does not return a value.
     */

  0.553  extract_obj                              — Removes an object and its contents from the game world.
    /**
     * @fn void extract_obj(Object *obj)
     *
     * @brief Removes an object and its contents from the game world.
     *
     * @details Removes an object from the game world.
    The function extract_obj is responsible for completely removing an object from the game world. It first determines the current location of the object, whether it is in a room, carried by a character, inside another object, in a locker, or in a strongbox, and removes it from that location. It then recursively removes any objects contained within the object. After handling the contents, it removes the object from the global object list maintained by the game world. If the object is the donation pit, it sets the donation pit to null. Finally, it decrements the count of the object's index data and deletes the object.
     *
     * @param obj A pointer to the Object that is to be removed from the game world.
     * @return This function does not return a value.
     */

  0.553  obj_to_locker                            — Adds an object to a character's locker.
    /**
     * @fn void obj_to_locker(Object *obj, Character *ch)
     *
     * @brief Adds an object to a character's locker.
     *
     * @details This function places a given object into the locker of a specified character. If the character is a non-player character (NPC), it logs a bug message and exits without performing any action. For player characters, the object is added to the front of the locker list, and its location pointers are updated to reflect its new position in the locker.
     *
     * @param obj A pointer to the Object that is to be added to the character's locker.
     * @param ch A pointer to the Character whose locker the object will be added to.
     * @return This function does not return a value.
     */

  0.553  get_locker_number                        — Calculates the total number of objects in a character's locker.
    /**
     * @fn int get_locker_number(Character *ch)
     *
     * @brief Calculates the total number of objects in a character's locker.
     *
     * @details This function computes the total number of objects stored in the locker of a given character. It first checks if the character is a non-player character (NPC) by using the is_npc() method. If the character is an NPC, the function returns 0, as NPCs do not have lockers. For player characters, it iterates through the objects in the character's locker, using the get_obj_number function to count the total number of objects contained within each object, and accumulates this count.
     *
     * @param ch A pointer to the Character whose locker contents are to be counted.
     * @return The total number of objects contained within the character's locker. Returns 0 if the character is an NPC.
     */

  0.552  spill_contents                           — Distributes the contents of an object to appropriate locations.
    /**
     * @fn void spill_contents(Object *obj, Object *contents)
     *
     * @brief Distributes the contents of an object to appropriate locations.
     *
     * @details The function 'spill_contents' takes the contents of a given object and distributes them based on the current state of the object. If the object is contained within another object, the contents are moved to that container. If the object is carried by a character, the contents may be added to the character's inventory or dropped into the room, depending on several conditions, including a random chance and the type of room. If the object is in a room, the contents are placed in the room. If none of these conditions are met, the contents are removed from the game world.
     *
     * @param obj A pointer to the Object whose contents are being spilled.
     * @param contents A pointer to the first Object in the list of contents to be distributed.
     * @return This function does not return a value.
     */

  0.546  obj_to_obj                               — Moves an object into another object, handling special cases for the do
    /**
     * @fn void obj_to_obj(Object *obj, Object *obj_to)
     *
     * @brief Moves an object into another object, handling special cases for the donation pit.
     *
     * @details Moves an object into another object.
    This function transfers an object into another object, updating their relationships. If the destination object is the donation pit, it sets the object's cost to zero and records the donation time. It also ensures that the donation pit does not exceed a maximum number of items by removing the oldest item if necessary. The function then updates the object's pointers to reflect its new container.
     *
     * @param obj The object to be moved.
     * @param obj_to The destination object into which 'obj' will be placed.
     * @return None
     */

  0.546  get_obj                                  — Handles the process of a character picking up an object, including val
    /**
     * @fn void get_obj(Character *ch, Object *obj, Object *container)
     *
     * @brief Handles the process of a character picking up an object, including validation, inventory management, and special quest considerations.
     *
     * @details Handles the process of a character attempting to pick up an object, including validation, inventory management, and special quest logic.
    This function allows a character to pick up an object from a room or container, performing checks for item takeability, capacity limits, and loot permissions. It manages the transfer of the object from its current location to the character's inventory, updates quest progress if applicable, and handles special cases such as money objects with auto-splitting among group members. The function also verifies if the object is currently in use by another character and prevents looting of certain items based on game rules.
     *
     * @param ch Pointer to the Character attempting to pick up the object.
     * @param obj Pointer to the Object being picked up.
     * @param container Pointer to the Object container from which the object is being taken; can be null if the object is in the room.
     * @return Void; the function performs side effects such as updating inventories, handling quest progress, and sending messages, with no return value.
     */

  0.539  destroy_obj                              — Destroys a game object and handles its contents.
    /**
     * @fn void destroy_obj(Object *obj)
     *
     * @brief Destroys a game object and handles its contents.
     *
     * @details Destroys an object while preserving its contents.
    This function is responsible for destroying a game object by first distributing its contents and gems to appropriate locations using the spill_contents function. After all contents have been handled, the object itself is removed from the game world using the extract_obj function. This ensures that no resources or items are lost when an object is destroyed.
     *
     * @param obj A pointer to the Object that is to be destroyed. The contents of this object will be preserved.
     * @return This function does not return a value.
     */

  0.537  can_loot                                 — Determines if a character can loot a specific object.
    /**
     * @fn bool can_loot(Character *ch, Object *obj)
     *
     * @brief Determines if a character can loot a specific object.
     *
     * @details This function checks whether a given character is allowed to loot a specified object. The function first allows looting if the character is immortal or if the object has no owner. If the object has an owner, it searches the world's character list to find the owner. If the character is the owner, or if the owner is a non-player character with the PLR_CANLOOT flag set, or if the character and the owner are in the same group, the function allows looting. Otherwise, looting is not permitted.
     *
     * @param ch A pointer to the Character object attempting to loot the object.
     * @param obj A pointer to the Object that the character is attempting to loot.
     * @return Returns true if the character is allowed to loot the object based on the specified conditions; otherwise, returns false.
     */

  0.530  remove_obj                               — Removes an object from a character's equipment at a specified wear loc
    /**
     * @fn bool remove_obj(Character *ch, int iWear, bool fReplace)
     *
     * @brief Removes an object from a character's equipment at a specified wear location.
     *
     * @details Attempts to remove an equipment item from a character, considering replace permissions and item properties.
    This function attempts to remove an object worn by the character at the given wear location (iWear). It first retrieves the object using get_eq_char. If no object is found, the function returns true, indicating no removal was necessary. If an object is found and fReplace is false, the removal is not performed, and the function returns false. If the object has the ITEM_NOREMOVE status, the removal is prevented, and a message is displayed to the character, with the function returning false. Otherwise, the object is unequipped from the character using unequip_char, and appropriate messages are sent to the character and the room. The function returns true if the removal was successful.
     *
     * @param ch Pointer to the Character from whom the object is to be removed.
     * @param iWear Integer representing the equipment slot to check and remove the object from.
     * @param fReplace Boolean flag indicating whether to proceed with removal if the slot is occupied.
     * @return Boolean value indicating whether the removal was successful (true) or not (false).
     */

  0.529  recursive_clone                          — Recursively clones an object and all its contained objects, creating d
    /**
     * @fn void recursive_clone(Character *ch, Object *obj, Object *clone)
     *
     * @brief Recursively clones an object and all its contained objects, creating deep copies of the entire object hierarchy.
     *
     * @details This function performs a deep clone of the specified object 'obj' and all objects contained within it. For each contained object, it creates a new object instance, copies its attributes from the original, and inserts it into the clone. The process is recursive, ensuring that nested containment structures are duplicated at all levels. The 'clone' parameter serves as the parent container for the cloned objects, and the function modifies the object hierarchy rooted at 'clone' to mirror that of 'obj'. If an error occurs during object creation, a bug report is logged, and the recursion terminates at that branch.
     *
     * @param ch The character performing the cloning operation, used for context or permissions (not directly used in this implementation).
     * @param obj The original object whose entire containment hierarchy is to be cloned.
     * @param clone The target object that will serve as the parent for the cloned contained objects.
     * @return This function does not return a value; it modifies the 'clone' object by adding deep copies of 'obj's contained objects.
     */

  0.525  setup_obj                                — Configures a game object based on its type and an optional argument.
    /**
     * @fn bool setup_obj(Character *ch, Object *obj, String argument)
     *
     * @brief Configures a game object based on its type and an optional argument.
     *
     * @details The function 'setup_obj' is intended to initialize or configure a game object ('obj') based on its type and an optional argument provided as a string. It first extracts the first argument from the provided 'argument' string. Depending on the type of the object, it may perform specific setup actions. Currently, the detailed setup logic is commented out for ITEM_TOKEN, but the function is structured to handle various item types. If the object type matches any of the predefined item types, the function processes it accordingly. For ITEM_TOKEN, the function would set the object's name, short description, and value based on the extracted argument if the logic were active. For other item types, the function does not perform any specific actions and simply returns true.
     *
     * @param ch A pointer to the Character object associated with the setup operation.
     * @param obj A pointer to the Object that is to be configured.
     * @param argument A String containing an optional argument that may influence the object's setup.
     * @return Returns true if the object setup is successful or if no specific setup is required for the object's type. Returns false if the setup fails due to invalid arguments (currently only applicable to ITEM_TOKEN if the logic were active).
     */

  0.521  unequip_char                             — Unequips an object from a character, updating attributes and environme
    /**
     * @fn void unequip_char(Character *ch, Object *obj)
     *
     * @brief Unequips an object from a character, updating attributes and environment.
     *
     * @details Unequips an object from a character.
    This function removes an object from a character's equipped items, updating the character's armor class and attributes accordingly. It also adjusts the light level in the character's current room if the object is a light source. The function ensures that the object is currently equipped before proceeding with the unequip process.
     *
     * @param ch A pointer to the Character from whom the object is being unequipped.
     * @param obj A pointer to the Object that is being unequipped from the character.
     * @return This function does not return a value.
     */

  0.512  obj_from_char                            — Removes an object from the character's possession.
    /**
     * @fn void obj_from_char(Object *obj)
     *
     * @brief Removes an object from the character's possession.
     *
     * @details Removes an object from the character carrying it.
    This function detaches an Object from the Character it is currently associated with. If the object is equipped, it will first be unequipped using the unequip_char function. The function then updates the linked list of objects carried by the character to exclude the specified object. If the object is not found in the character's possession, a bug is logged. The function ensures that the object's carried_by and next_content pointers are set to nullptr after removal.
     *
     * @param obj A pointer to the Object that is to be removed from the character.
     * @return This function does not return a value.
     */

  0.510  gem::inset                               — Moves a gem object into another object.
    /**
     * @fn void gem::inset(Object *gem, Object *obj)
     *
     * @brief Moves a gem object into another object.
     *
     * @details This function transfers a gem from its current location to be contained within another object. It updates the gem's pointers to reflect its new location, setting its 'in_obj' to the target object and clearing its 'in_room' and 'carried_by' pointers. The gem is added to the beginning of the target object's gem list.
     *
     * @param gem The gem object to be moved.
     * @param obj The target object into which the gem will be inserted.
     * @return This function does not return a value.
     */

  0.509  count_users                              — Counts the number of users interacting with a specific object.
    /**
     * @fn int count_users(Object *obj)
     *
     * @brief Counts the number of users interacting with a specific object.
     *
     * @details Counts the number of people on a specified object.
    This function iterates through the list of characters present in the same room as the given object and counts how many of them are currently interacting with the object. It returns the total count of such characters. If the object is not located in any room, the function returns zero.
     *
     * @param obj A pointer to the Object for which the number of people on it is to be counted.
     * @return The number of characters currently on the specified object. Returns 0 if the object is not in any room.
     */

  0.493  obj_from_strongbox                       — Removes an object from a character's strongbox.
    /**
     * @fn void obj_from_strongbox(Object *obj)
     *
     * @brief Removes an object from a character's strongbox.
     *
     * @details This function removes a specified object from the strongbox of a character. It first checks if the object is associated with a valid character and ensures the character is not a non-player character (NPC). If the object is the first in the strongbox, it updates the strongbox pointer to the next object. Otherwise, it traverses the list to find and remove the object. If the object is not found, a bug is logged.
     *
     * @param obj A pointer to the Object that is to be removed from the strongbox.
     * @return This function does not return a value.
     */

  0.489  will_fit                                 — Determines if an object can fit inside a container.
    /**
     * @fn bool will_fit(Object *obj, Object *container)
     *
     * @brief Determines if an object can fit inside a container.
     *
     * @details This function checks whether a given object can be placed inside a specified container based on weight constraints. It calculates the total weight of the object using the get_obj_weight function and compares it against the container's maximum allowable weight for a single item and the total weight capacity. The container's capacity is determined by its type and level, with special rules for non-takeable items.
     *
     * @param obj A pointer to the Object that is being checked for fitting inside the container.
     * @param container A pointer to the Object representing the container into which the obj is to be placed.
     * @return Returns true if the object can fit inside the container without exceeding weight limits; otherwise, returns false.
     */

  0.485  get_owner                                — Retrieves the owner description of a specified object for a character.
    /**
     * @fn String get_owner(Character *ch, Object *obj)
     *
     * @brief Retrieves the owner description of a specified object for a character.
     *
     * @details Retrieves the name of the owner of the specified object.
    This function checks if the given object has an extra description labeled as the owner. If such a description exists and the character can see the object, it returns the owner's description. If the character cannot see the object, it returns 'someone'. If no owner description is found, it returns '(none)'.
     *
     * @param ch A pointer to the Character object whose perspective is used to determine visibility of the object's owner.
     * @param obj A pointer to the Object for which the owner's name is being retrieved.
     * @return Returns a String containing the owner's name if available and visible to the character, 'someone' if the owner is not visible, or '(none)' if no ownership information is present.
     */

  0.482  obj_from_locker                          — Removes an object from a character's locker.
    /**
     * @fn void obj_from_locker(Object *obj)
     *
     * @brief Removes an object from a character's locker.
     *
     * @details This function removes a specified object from the locker of a character. It first checks if the object is associated with a valid character and logs an error if not. If the character is a non-player character (NPC), it logs an error and exits. If the object is the first item in the locker, it updates the locker to point to the next item. Otherwise, it searches through the locker list to find and remove the object. If the object is not found in the locker, it logs an error. Finally, it clears the object's locker-related pointers.
     *
     * @param obj A pointer to the Object to be removed from the character's locker.
     * @return This function does not return a value.
     */

  0.480  get_legendary_name                       — Generates a legendary name based on the equipment type.
    /**
     * @fn const String get_legendary_name(int eq_type)
     *
     * @brief Generates a legendary name based on the equipment type.
     *
     * @details This function constructs a legendary name by selecting a random base name from a pool and appending a random name associated with the given equipment type. The legendary name is formatted as 'BaseName Name{x'. The function utilizes a random number generator to select elements from the base pool and the equipment-specific name list.
     *
     * @param eq_type The type of equipment for which to generate a legendary name, used to retrieve the corresponding name list.
     * @return A String representing the generated legendary name, formatted as 'BaseName Name{x'.
     */

  0.479  get_obj_number                           — Calculates the total number of objects contained within a given object
    /**
     * @fn int get_obj_number(Object *obj)
     *
     * @brief Calculates the total number of objects contained within a given object.
     *
     * @details This function computes the total number of objects contained within the specified object, including the object itself unless it is a container, money, or token type. It recursively traverses the linked list of contained objects, summing up their counts. The function adjusts the count based on the object's type and properties, specifically excluding containers and certain item types from the initial count.
     *
     * @param obj A pointer to the Object whose contained objects are to be counted.
     * @return The total number of objects contained within the specified object, adjusted based on the object's type and properties.
     */

  0.450  get_true_weight                          — Calculates the true weight of an object, including all contained objec
    /**
     * @fn int get_true_weight(Object *obj)
     *
     * @brief Calculates the true weight of an object, including all contained objects.
     *
     * @details Calculates the true weight of an object, including its contents.
    This function computes the total weight of a given Object by summing its own weight with the weights of all objects it contains. It iterates through each contained object, recursively calculating their weights using the get_obj_weight function, and adds these to the total weight. This function is useful for determining the cumulative weight of an object and its contents in a hierarchical structure.
     *
     * @param obj A pointer to the Object whose total weight, including its contents, is to be calculated.
     * @return The total weight of the object, including the weights of all contained objects.
     */

  0.449  get_obj_weight                           — Calculates the total weight of an object, including its contents.
    /**
     * @fn int get_obj_weight(Object *obj)
     *
     * @brief Calculates the total weight of an object, including its contents.
     *
     * @details This function computes the total weight of a given Object by summing its own weight and the adjusted weights of all objects it contains. The adjustment for contained objects' weights is determined by a multiplier specific to the parent object. The function recursively traverses all contained objects to ensure their weights are included in the total calculation.
     *
     * @param obj A pointer to the Object whose total weight is to be calculated.
     * @return The total weight of the object, including the adjusted weights of all contained objects.
     */

  0.427  obj_from_obj                             — Removes an object from its containing object.
    /**
     * @fn void obj_from_obj(Object *obj)
     *
     * @brief Removes an object from its containing object.
     *
     * @details This function detaches an object from the object it is contained within. It first checks if the object is inside another object. If not, it logs a bug message and returns. It then attempts to remove the object from the 'contains' list of the container object. If not found, it tries to remove it from the 'gems' list. If the object is not found in either list, it logs a bug message. Upon successful removal, it clears the object's 'next_content' and 'in_obj' pointers.
     *
     * @param obj A pointer to the Object that is to be removed from its containing object.
     * @return This function does not return a value.
     */

  0.420  is_anvil_owner                           — Determines if the specified character is the owner of the anvil.
    /**
     * @fn int is_anvil_owner(Character *ch, Object *anvil)
     *
     * @brief Determines if the specified character is the owner of the anvil.
     *
     * @details This function checks if the name of the character matches the owner's name of the given anvil object. It retrieves the owner's name from the anvil using the 'anvil_owner_name' function and then checks if the character's name is exactly present in the owner's name using the 'has_exact_words' method.
     *
     * @param ch A pointer to the Character object whose ownership of the anvil is being verified.
     * @param anvil A pointer to the Object representing the anvil whose ownership is being checked.
     * @return Returns an integer value of 1 if the character's name matches the anvil's owner's name exactly; otherwise, returns 0.
     */

  0.413  get_base_name                            — Retrieves a base name string for a given equipment type and level.
    /**
     * @fn const String get_base_name(int eq_type, int ilevel)
     *
     * @brief Retrieves a base name string for a given equipment type and level.
     *
     * @details This function searches a multimap for base names associated with a specified equipment type ('eq_type'). It first counts the number of entries matching 'eq_type'. If no entries are found, it logs a bug message and returns an empty string. If entries are found, it limits the search to a valid range based on 'ilevel', retrieves the appropriate base name, and returns it.
     *
     * @param eq_type The equipment type used to search for base names in the multimap.
     * @param ilevel The level used to determine which base name to retrieve from the list of matches.
     * @return A String object representing the base name associated with the specified equipment type and level. Returns an empty string if no base names are found.
     */

  0.406  item_type_name                           — Retrieves the name of an item's type based on the object's item type.
    /**
     * @fn String item_type_name(Object *obj)
     *
     * @brief Retrieves the name of an item's type based on the object's item type.
     *
     * @details Returns the ASCII name of an item's type.
    This function takes an Object pointer and returns a String representing the name of the item's type. It uses a switch statement to match the item's type to a predefined set of constants, each corresponding to a specific item type name. If the item's type does not match any known type, it logs a bug report with the unknown type value and returns "(unknown)".
     *
     * @param obj A pointer to an Object whose item_type is used to determine the corresponding ASCII name.
     * @return A String representing the ASCII name of the item's type, or "(unknown)" if the type is not recognized.
     */

  0.403  has_modified_contents                    — Checks if an object contains modified contents.
    /**
     * @fn bool has_modified_contents(Object *obj)
     *
     * @brief Checks if an object contains modified contents.
     *
     * @details This function iterates over the contents of the given object to determine if any of the contained objects do not match their expected 'put' reset state. It returns true if any contained object is either missing a reset, has a reset command other than 'P', or has a reset argument that does not match the parent object's index data. This is used to identify objects with contents that have been altered from their default reset state.
     *
     * @param obj A pointer to the Object whose contents are to be checked for modifications.
     * @return Returns true if the object contains any modified contents that do not match their 'put' reset state; otherwise, returns false.
     */

  0.352  anvil_owner_name                         — Retrieves the owner's name from a private anvil object.
    /**
     * @fn String anvil_owner_name(Object *anvil)
     *
     * @brief Retrieves the owner's name from a private anvil object.
     *
     * @details This function checks if the given anvil object is marked as private by examining a specific value in the object's data. If the anvil is private, it verifies that the anvil's name begins with the prefix 'anvil private '. If the prefix is present, the function extracts and returns the owner's name, which follows the prefix in the anvil's name. If the anvil is not private or the name does not have the correct prefix, an empty string is returned. Additionally, if the anvil is private but the name is incorrectly formatted, a bug report is logged.
     *
     * @param anvil A pointer to the Object representing the anvil whose owner's name is to be retrieved.
     * @return A String containing the owner's name if the anvil is private and correctly named; otherwise, an empty String.
     */

  0.296  ObjectValue::value                       — Retrieves the stored integer value.
    /**
     * @fn const int ObjectValue::value() const
     *
     * @brief Retrieves the stored integer value.
     *
     * @details This function returns the integer value stored in the private member variable '_value'. It is a constant member function, indicating that it does not modify the state of the object.
     *
     * @return The integer value stored in the private member variable '_value'.
     */


================================================================================
[domain] movement  (stability: stable)
  desc: Character and object movement between rooms: entering and leaving rooms, door and exit resolution, room access via exits…
  locked: 34 functions, 34 with embeddings
  sim to desc — mean: 0.525  min: 0.302  max: 0.655

  0.655  move_char                                — Handles moving a character from one room to another within the game en
    /**
     * @fn void move_char(Character *ch, int door, bool follow)
     *
     * @brief Handles moving a character from one room to another within the game environment, including checks, messaging, and follow-up actions.
     *
     * @details This function moves a specified character 'ch' through a designated exit 'door' to an adjacent room, performing various validation checks such as door validity, room visibility, privacy, guild restrictions, and environmental hazards like water or flying conditions. It manages stamina costs, applies effects like haste or slow, and updates the character's position and room. Additionally, it handles messaging to the character and others in the room, triggers special behaviors like guard scripts, and manages followers who may follow the character through the move. The function also ensures proper state updates and triggers appropriate game events post-movement.
     *
     * @param ch Pointer to the Character object representing the character to be moved.
     * @param door Integer index of the exit door used for movement, must be within 0-5.
     * @param follow Boolean indicating whether followers should automatically follow the character through the move.
     * @return Void; the function performs the move operation and side effects without returning a value.
     */

  0.651  access_room                              — Determines the accessible room via a specified exit.
    /**
     * @fn static Room * access_room(HUNT_CONDITIONS *cond, Exit *ex)
     *
     * @brief Determines the accessible room via a specified exit.
     *
     * @details This function evaluates whether a room can be accessed through a given exit based on specific conditions. It checks if the exit and the target room are valid, whether the room is in the same area as specified by the conditions, if the exit is not closed when doors are not allowed, and if the character can see the room. If all conditions are met, it returns the accessible room; otherwise, it returns nullptr.
     *
     * @param cond A pointer to a HUNT_CONDITIONS structure containing the conditions that must be met for accessing the room.
     * @param ex A pointer to an Exit object representing the exit through which access is attempted.
     * @return A pointer to the Room object that is accessible via the exit if all conditions are met, or nullptr if the room cannot be accessed.
     */

  0.638  get_scatter_room                         — Selects a suitable random room for scattering a character within the g
    /**
     * @fn Room * get_scatter_room(Character *ch)
     *
     * @brief Selects a suitable random room for scattering a character within the game world.
     *
     * @details This function iterates through all rooms in the game world to find a random room that the character can see and enter, excluding certain areas, room types, and conditions such as quest areas, specific area names, sector types, and room flags. It performs up to two passes: the first to count and select a random candidate, and the second to return the chosen room based on the previous selection. If no suitable room is found, it returns nullptr.
     *
     * @param ch Pointer to the Character object for which a scatter room is being determined.
     * @return A pointer to a Room object representing the selected scatter location, or nullptr if no suitable room is found.
     */

  0.637  exits_in                                 — Displays rooms and portals with exits leading into the current room.
    /**
     * @fn void exits_in(Character *ch)
     *
     * @brief Displays rooms and portals with exits leading into the current room.
     *
     * @details The function 'exits_in' examines all rooms and portals in the game world to find those that have exits leading into the room where the specified character is currently located. It constructs a formatted string listing these rooms and portals and sends this information to the character's output buffer. If no such rooms or portals are found, it informs the character accordingly.
     *
     * @param ch A pointer to the Character object whose current room is being examined for incoming exits and portals.
     * @return This function does not return a value.
     */

  0.634  get_random_room                          — Selects and returns a random suitable room for a character, based on s
    /**
     * @fn Room * get_random_room(Character *ch)
     *
     * @brief Selects and returns a random suitable room for a character, based on specific visibility and area criteria.
     *
     * @details Selects and returns a random suitable room for a character, based on visibility and area constraints.
    This function iterates through all rooms in all areas within the game world to find a random room that the character can see and enter, excluding rooms in certain areas, with specific flags, or associated with clans or guilds. It performs up to two passes: the first to count and select a random candidate, and the second to return the selected room. If no suitable room is found, it returns nullptr.
     *
     * @param ch Pointer to the Character object for whom a random room is being selected.
     * @return A pointer to a Room object that is randomly selected from the pool of suitable rooms, or nullptr if no such room exists.
     */

  0.615  obj_to_room                              — Places an object into a specified room, handling special cases like fl
    /**
     * @fn void obj_to_room(Object *obj, Room *room)
     *
     * @brief Places an object into a specified room, handling special cases like floating rooms.
     *
     * @details Moves an object into a specified room.
    This function inserts the given Object into the specified Room. If the room is null, it logs a bug and exits. For rooms with an air sector type and certain conditions (such as the object being takable and having a downward exit), the object may 'float' through multiple connected air-sector rooms. During this process, appropriate messages are dispatched to characters in the current and new rooms to indicate the object's movement. After resolving floating, the object is added to the room's contents list, and its in-room and carried-by pointers are updated accordingly.
     *
     * @param obj A pointer to the Object to be moved into the room.
     * @param room A pointer to the Room where the object is to be placed.
     * @return This function does not return a value.
     */

  0.609  find_exit                                — Determines the exit door index in a room based on a given direction or
    /**
     * @fn int find_exit(Character *ch, const String &arg)
     *
     * @brief Determines the exit door index in a room based on a given direction or keyword.
     *
     * @details Determines the door index corresponding to a given direction or keyword in the character's current room.
    This function searches for an exit door in the character's current room that matches the specified argument, which can be a direction ('n', 'east', etc.) or a keyword. It first checks for standard direction abbreviations and names, returning the corresponding door index if found. If the argument does not match a direction, it searches through all doors in the room for one that has the 'EX_ISDOOR' flag set and whose keyword matches the argument words. If a matching door is found, its index is returned; otherwise, an appropriate message is sent to the character, and -1 is returned to indicate failure. The function ensures that the door exists before returning its index, providing a way to identify and interact with room exits based on user input.
     *
     * @param ch Pointer to the Character object representing the actor attempting to find the exit.
     * @param arg A String containing the direction or keyword used to identify the exit.
     * @return An integer representing the door index (0-5) if a matching exit is found; otherwise, -1 indicating no such door exists or was found.
     */

  0.609  char_to_room                             — Moves a character into a specified room, handling null checks and fall
    /**
     * @fn void char_to_room(Character *ch, Room *room)
     *
     * @brief Moves a character into a specified room, handling null checks and fallback to a default location if necessary.
     *
     * @details This function attempts to place the given character into the specified room. If the character pointer is null, the function performs no action. If the target room is null, it logs a bug message, then retrieves the default temple room from the game world and recursively calls itself to move the character there. When a valid room is provided, it adds the character to that room's occupant list and updates related room data accordingly. The function modifies the character's location and the room's occupant list as side effects.
     *
     * @param ch Pointer to the Character object to be moved into the room.
     * @param room Pointer to the target Room object where the character should be placed; may be null.
     * @return Void; the function performs side effects by modifying the character's location and the room's occupant list.
     */

  0.603  find_path                                — Finds the shortest path from a starting room to a target room and retu
    /**
     * @fn static int find_path(HUNT_CONDITIONS *cond)
     *
     * @brief Finds the shortest path from a starting room to a target room and returns the direction of the first step.
     *
     * @details This function calculates the shortest path from a starting room (cond->from_room) to a target room (cond->to_room) within a specified area. It uses a breadth-first search approach, expanding outwards from the starting room and exploring all possible exits. If the target room is found, the function backtracks to determine the first step direction. If the path cannot be found within a certain number of steps, or if there are issues with backtracking, it returns specific error codes.
     *
     * @param cond A pointer to a HUNT_CONDITIONS structure containing the starting room, target room, and other search parameters.
     * @return The direction of the first step towards the target room, or an error code: -1 if the path is not found, -2 if too many steps are taken, -3 if backtracking dead ends, -4 if backtracking loops, -5 if backtracking doesn't return to origin, -6 if the starting room does not lead to the second room.
     */

  0.577  char_from_room                           — Removes a character from its current room and updates associated room 
    /**
     * @fn void char_from_room(Character *ch)
     *
     * @brief Removes a character from its current room and updates associated room state.
     *
     * @details Removes a character from its current room.
    This function removes the specified character from its current room. It first checks if the character pointer is null, returning immediately if so. If the character's current room pointer is null, it logs a bug message indicating an unexpected null room. Otherwise, it calls the room's remove_char method to detach the character from the room, which updates the room's occupant list and related state accordingly.
     *
     * @param ch A pointer to the Character object that is to be removed from its current room.
     * @return This function does not return a value.
     */

  0.562  Room::add_char                           — Adds a character to the room and updates related area and status infor
    /**
     * @fn void Room::add_char(Character *ch)
     *
     * @brief Adds a character to the room and updates related area and status information.
     *
     * @details This function inserts the specified Character pointer into the room's linked list of occupants, updates the character's current room pointer, and registers the character within the associated area. It also checks if the character is wearing a light source item with a non-zero value, incrementing the room's light counter accordingly. Additionally, it searches for any plague affect on the character and, if found, propagates the plague to other characters in the room based on a spreading mechanism.
     *
     * @param ch Pointer to the Character object to be added to the room.
     * @return Void; the function performs side effects by modifying the room's occupant list, area data, light count, and potentially spreading a plague affect.
     */

  0.553  checkexitstoroom                         — Generates a formatted string for exits between a room and a destinatio
    /**
     * @fn String checkexitstoroom(Room *room, Room *dest)
     *
     * @brief Generates a formatted string for exits between a room and a destination room.
     *
     * @details This function examines each exit of the given 'room' to determine if it leads to or from the specified 'dest' room, but not both. It constructs a formatted string representing these one-way exits using the 'room_pair' function. The function iterates over all possible exits of the 'room', checking if each exit leads to the 'dest' room or originates from it. If an exit is found that meets the criteria, it is added to the result string with the appropriate directional indicator.
     *
     * @param room A pointer to the Room object whose exits are being checked.
     * @param dest A pointer to the Room object that is the destination for the exits being checked.
     * @return A String object containing formatted representations of the one-way exits between 'room' and 'dest'.
     */

  0.551  find_door                                — Determines the door index corresponding to a given direction or door k
    /**
     * @fn int find_door(Character *ch, const String &arg)
     *
     * @brief Determines the door index corresponding to a given direction or door keyword in the character's current room.
     *
     * @details This function attempts to identify a door in the character's current room based on the input argument 'arg'. It first checks if 'arg' is a prefix of standard direction words ('north', 'east', 'south', 'west', 'up', 'down') and assigns the corresponding door index (0-5). If not a direction, it searches through all doors in the room's exits to find one whose keyword matches 'arg' and has the 'EX_ISDOOR' flag set. If a matching door is found, its index is returned. If no door matches, an appropriate message is sent to the character, and -1 is returned to indicate failure. The function also verifies that the identified exit exists and is indeed a door before returning the index.
     *
     * @param ch Pointer to the Character object representing the actor performing the action, used to access the current room and to send messages.
     * @param arg Constant reference to a String object containing the direction or door keyword to identify.
     * @return Returns the integer index (0-5) of the door if found and valid; returns -1 if no matching door exists or if the specified exit is not a door.
     */

  0.550  char_in_duel_room                        — Checks if a character is in a duel room.
    /**
     * @fn bool char_in_duel_room(Character *ch)
     *
     * @brief Checks if a character is in a duel room.
     *
     * @details This function determines whether a given character is currently located in a duel room. It iterates through a linked list of duel arenas and checks if the character's current room matches any of the preparation rooms or falls within the range of valid room numbers for any arena. If the character's room matches any of these conditions, the function returns true, indicating the character is in a duel room.
     *
     * @param ch A pointer to the Character object whose location is being checked.
     * @return Returns true if the character is in a duel room, otherwise returns false.
     */

  0.546  char_in_darena_room                      — Checks if a character is in a duel arena room.
    /**
     * @fn bool char_in_darena_room(Character *ch)
     *
     * @brief Checks if a character is in a duel arena room.
     *
     * @details This function determines whether the given character is currently located in a room that is part of a duel arena. It iterates through the linked list of duel arenas and checks if the character's current room's virtual number (vnum) falls within the range of any arena's minimum and maximum vnum. If the character's room is within any arena's range, the function returns true; otherwise, it returns false.
     *
     * @param ch A pointer to the Character object whose current room is being checked.
     * @return Returns true if the character is in a room that is part of a duel arena, otherwise returns false.
     */

  0.545  room_pair                                — Generates a formatted string representing the relationship between two
    /**
     * @fn String room_pair(Room *left, Room *right, exit_status ex)
     *
     * @brief Generates a formatted string representing the relationship between two rooms based on exit status.
     *
     * @details This function constructs a formatted string that describes the relationship between two rooms, 'left' and 'right', based on the provided 'exit_status'. It determines the appropriate symbol to represent the exit status and formats the room names and locations accordingly. The room names are stripped of color codes, and the locations are converted to strings with padding for alignment. The resulting string includes the formatted names, locations, and exit status symbol.
     *
     * @param left A pointer to the Room object representing the left room in the pair.
     * @param right A pointer to the Room object representing the right room in the pair.
     * @param ex An exit_status value indicating the relationship between the two rooms (e.g., exit_from, exit_to, exit_both).
     * @return A String object containing the formatted representation of the two rooms and their relationship, including names, locations, and exit status.
     */

  0.541  checkexits                               — Generates a string listing all exits of a given room that lead to or f
    /**
     * @fn String checkexits(Room *room, const Area *pArea)
     *
     * @brief Generates a string listing all exits of a given room that lead to or from a specified area but not both.
     *
     * @details This function iterates through all possible exits (up to six) of the provided 'room' and checks whether each exit connects to the specified 'pArea'. It identifies exits that either originate from 'pArea' and lead outside, or lead into 'pArea' from outside, but not both directions. For each such exit, it appends a formatted representation of the room pair and their relationship (one-way or two-way) to the output string. The function returns a concatenated string of all such exits, effectively highlighting boundary connections between 'room' and 'pArea'.
     *
     * @param room Pointer to the Room object whose exits are being checked.
     * @param pArea Pointer to the Area object used as the reference area for filtering exits.
     * @return A String object containing formatted representations of all exits connected to or from 'pArea' that are not bidirectional, indicating their relationship and involved rooms.
     */

  0.528  IS_FLYING                               
    /**
     * @def IS_FLYING
     *
     */

  0.526  scan_list                                — Iterates through all characters in a specified room and displays infor
    /**
     * @fn void scan_list(Room *scan_room, Character *ch, int depth, int door)
     *
     * @brief Iterates through all characters in a specified room and displays information about visible characters to the given character.
     *
     * @details This function scans all occupants of the provided 'scan_room' and, for each character other than 'ch', checks if 'ch' can see them using 'can_see_char'. If visibility is confirmed, it calls 'scan_char' to display detailed information about the character at the specified 'depth' and 'door' direction. The function handles null room pointers gracefully and does not return a value.
     *
     * @param scan_room Pointer to the Room object representing the room to be scanned.
     * @param ch Pointer to the Character object who is performing the scan.
     * @param depth Integer indicating the distance level from 'ch' for the scan, used in 'scan_char'.
     * @param door Integer representing the direction index, used to determine direction name in 'scan_char' when 'depth' is non-zero.
     * @return Void; the function performs its operation by side effects, displaying information about visible characters in the room.
     */

  0.526  obj_from_room                            — Removes an Object from its current Room.
    /**
     * @fn void obj_from_room(Object *obj)
     *
     * @brief Removes an Object from its current Room.
     *
     * @details Removes an object from its current room.
    This function detaches an Object from the Room it is currently in. It first checks if the Object is in a Room, logging an error if not. It then updates any Characters in the Room that are interacting with the Object, setting their interaction to null. The function proceeds to remove the Object from the Room's contents list, ensuring the list remains intact. If the Object is not found in the Room's contents, an error is logged. Finally, the Object's room reference and next content pointer are cleared.
     *
     * @param obj A pointer to the Object that is to be removed from its current room.
     * @return This function does not return a value.
     */

  0.510  recall                                   — Handles the recall process for a character, teleporting them to a desi
    /**
     * @fn void recall(Character *ch, bool clan)
     *
     * @brief Handles the recall process for a character, teleporting them to a designated location with various checks and conditions.
     *
     * @details This function manages the recall action for a character, allowing players or pets to teleport to specific locations such as clan recall points or temple. It performs multiple checks including room validity, duel status, cooldown timers, and restrictions like no-recall zones or curses. It handles special cases such as arena and clan arena sectors, including potential combat consequences and experience loss. The function also manages visual and message effects, including prayer animations, arrival and departure messages, and recursive recall for pets. It updates the character's position, handles associated effects, and ensures proper game state updates throughout the process.
     *
     * @param ch Pointer to the Character object performing the recall action.
     * @param clan Boolean indicating whether the recall is for a clan (true) or general (false).
     * @return Void; performs side effects such as moving the character, sending messages, and updating game state.
     */

  0.506  extract_char                             — Removes a character from the game world, handling cleanup of followers
    /**
     * @fn void extract_char(Character *ch, bool fPull)
     *
     * @brief Removes a character from the game world, handling cleanup of followers, pets, inventory, and room placement.
     *
     * @details Removes a character from the game world, handling cleanup of relationships, inventory, and associated data.
    This function extracts a character from the game environment, performing necessary cleanup such as removing pets and followers, stopping combat, clearing inventory objects, and updating room and world state. If 'fPull' is true, the character is moved to a designated death or altar room; otherwise, they are returned to their clan recall location or a default location. It also handles special cases for NPCs, player characters, and original body return, and ensures all references to the character are properly cleared from the game world and other characters' reply fields.
     *
     * @param ch Pointer to the Character object to be extracted from the game world.
     * @param fPull Boolean flag indicating whether to move the character to a default location (true) or perform a full extraction (false).
     * @return Void; the function performs cleanup and removal operations without returning a value.
     */

  0.503  IS_OUTSIDE                              
    /**
     * @def IS_OUTSIDE
     *
     */

  0.496  Room::remove_char                        — Removes a character from the room and updates associated area and ligh
    /**
     * @fn void Room::remove_char(Character *ch)
     *
     * @brief Removes a character from the room and updates associated area and lighting state.
     *
     * @details This function removes the specified Character pointer from the current Room, updating the room's linked list of occupants and adjusting the area's character count if necessary. It first verifies that the character is present in the room, then checks if the character is wearing a light source to decrement the room's light level accordingly. The character's in-room pointers are reset to null, and the character's association with the room is cleared. This operation ensures consistency in the room's occupant list and related state variables.
     *
     * @param ch Pointer to the Character object to be removed from the room.
     * @return Void; the function does not return a value but modifies the room's occupant list, the character's room association, and possibly the room's light level.
     */

  0.489  get_warp_loc_string                      — Retrieves the warp location description from an object.
    /**
     * @fn const String get_warp_loc_string(const Object *obj)
     *
     * @brief Retrieves the warp location description from an object.
     *
     * @details This function checks if the provided object is a warp crystal and attempts to retrieve its warp location description. It first searches the object's extra descriptions for a keyword 'warp_loc'. If not found, it checks the object's prototype data for the same keyword. If a matching description is found, it is returned; otherwise, an empty string is returned.
     *
     * @param obj A pointer to the Object from which to retrieve the warp location description.
     * @return A String containing the warp location description if found, otherwise an empty String.
     */

  0.477  get_position                             — Determines the current position of a character.
    /**
     * @fn int get_position(Character *ch)
     *
     * @brief Determines the current position of a character.
     *
     * @details This function checks the position of a character and returns it. If the character is engaged in fighting and their position is at least POS_STANDING, it returns POS_FIGHTING. If the character pointer is null, it returns -1.
     *
     * @param ch A pointer to the Character object whose position is being determined.
     * @return The function returns an integer representing the character's position. It returns -1 if the character pointer is null, 'POS_FIGHTING' if the character is fighting and standing, or the character's actual position otherwise.
     */

  0.467  set_tail                                 — Sets or clears a tailing relationship between characters, optionally a
    /**
     * @fn int set_tail(Character *ch, Character *victim, Flags tail_flags)
     *
     * @brief Sets or clears a tailing relationship between characters, optionally affecting all characters if the victim is null.
     *
     * @details Sets or clears tailing relationships between characters in the game.
    This function manages tailing relationships between characters in the game. If the victim parameter is null, it attempts to clear tailing from all characters that have tail data, effectively untailing everyone. When tail_flags do not include TAIL_NONE, it initiates or updates a tailing relationship from ch to victim, creating a new Tail data object if necessary, and adds the specified flags. If tail_flags include TAIL_NONE, it removes the tailing relationship set by ch from the victim, deleting the corresponding Tail data object. The function returns the number of tailing relationships affected, or zero if no changes occur.
     *
     * @param ch Pointer to the Character initiating or stopping the tailing action.
     * @param victim Pointer to the Character being tailed or null for global untail operation.
     * @param tail_flags Flags indicating tailing options; TAIL_NONE to stop tailing.
     * @return Returns an integer count of how many tailing actions were successfully initiated or stopped.
     */

  0.465  nuke_pets                                — Removes a character's pet and any associated followers from the game w
    /**
     * @fn void nuke_pets(Character *ch)
     *
     * @brief Removes a character's pet and any associated followers from the game world.
     *
     * @details Removes a character's pet from the game world, stopping its following behavior and handling cleanup.
    This function 'nuke_pets' targets the specified character's pet, if any, and performs cleanup by stopping its following behavior, displaying a fade-away message in the current room, and extracting the pet from the game world. It also clears the pet pointer in the character to prevent dangling references. The function ensures that the pet and any related follow relationships are properly terminated, effectively removing the pet entity from gameplay.
     *
     * @param ch Pointer to the Character whose pet is to be nuked.
     * @return Void; the function performs side effects such as stopping follow behavior, messaging, and character extraction without returning a value.
     */

  0.457  Area::remove_char                        — Removes a character from the area, updating NPC counts accordingly.
    /**
     * @fn void Area::remove_char(Character *ch)
     *
     * @brief Removes a character from the area, updating NPC counts accordingly.
     *
     * @details This function removes a specified character from the area. If the character is an NPC, the function exits immediately without making changes. For player characters, it decrements the count of mortal or immortal players in the area, ensuring the counts do not become negative. The function assumes the character is currently present in the area and updates internal counters to reflect its removal.
     *
     * @param ch Pointer to the Character object to be removed from the area.
     * @return Void; the function does not return a value but modifies internal state counters within the Area object.
     */

  0.406  World::remove_char                       — Removes a character from the world's character list.
    /**
     * @fn void World::remove_char(Character *)
     *
     * @brief Removes a character from the world's character list.
     *
     * @details This function removes the specified Character pointer from the world's internal character list, effectively detaching it from the world's management. It does not delete the character object itself, only removes it from the list. The caller is responsible for managing the character's memory if necessary.
     *
     * @param ch Pointer to the Character object to be removed from the world's character list.
     * @return This function has no return value.
     */

  0.405  make_pet                                 — Creates a pet character and establishes it as a follower of a master c
    /**
     * @fn void make_pet(Character *ch, Character *pet)
     *
     * @brief Creates a pet character and establishes it as a follower of a master character.
     *
     * @details This function transforms the specified character 'pet' into a pet by setting its act_flags to include ACT_PET, then establishes a follower relationship with the master character 'ch' by invoking add_follower. It sets the pet's leader pointer to 'ch' and assigns the pet to the master's pet pointer, effectively linking the pet to its owner within the game's character hierarchy.
     *
     * @param ch Pointer to the Character object that will become the master of the pet.
     * @param pet Pointer to the Character object that will be turned into a pet and assigned to the master.
     * @return This function does not return a value.
     */

  0.377  stop_follower                            — Stops a character from following their current master and clears relat
    /**
     * @fn void stop_follower(Character *ch)
     *
     * @brief Stops a character from following their current master and clears related affect states.
     *
     * @details This function terminates the following relationship of the specified character by removing charm affects, updating master and pet references, and notifying involved characters if visible. It first checks if the character has a master; if not, it logs a bug and exits. If the character is affected by charm, that affect is removed. If the master can see the character, appropriate messages are displayed to both parties. If the character is a pet of the master, the pet reference is cleared. Finally, the character's master and leader pointers are set to null, effectively stopping the follow behavior.
     *
     * @param ch Pointer to the Character object who is stopping to follow their master.
     * @return This function has no return value; it performs side effects to update the follower relationship and dispatch messages.
     */

  0.342  Exit::rev_dir                            — Returns the reverse direction for a given direction index.
    /**
     * @fn unsigned int Exit::rev_dir(unsigned int dir)
     *
     * @brief Returns the reverse direction for a given direction index.
     *
     * @details This function takes an unsigned integer representing a direction index and returns the corresponding reverse direction index. The function uses a static array to map each direction to its reverse. The input index is taken modulo 6 to ensure it is within the valid range of the array.
     *
     * @param dir An unsigned integer representing the direction index to be reversed.
     * @return The reverse direction index corresponding to the input direction.
     */

  0.302  Exit::keyword                            — Retrieves the keyword associated with the Exit object.
    /**
     * @fn const String & Exit::keyword() const
     *
     * @brief Retrieves the keyword associated with the Exit object.
     *
     * @details This function returns a constant reference to the keyword string stored within the Exit object. The keyword is part of the prototype structure, which is a member of the Exit class. This function provides read-only access to the keyword, ensuring that the caller cannot modify the underlying string.
     *
     * @return A constant reference to a String object representing the keyword associated with the Exit object.
     */


================================================================================
[domain] combat  (stability: stable)
  desc: Combat round execution: single and multi-attack resolution per round, damage calculation and application, defense checks…
  locked: 25 functions, 25 with embeddings
  sim to desc — mean: 0.526  min: 0.408  max: 0.661

  0.661  multi_hit                                — Performs multiple attack actions for a character during combat, includ
    /**
     * @fn void multi_hit(Character *ch, Character *victim, skill::type attack_skill)
     *
     * @brief Performs multiple attack actions for a character during combat, including handling dual-wielding, special attacks, and combat effects.
     *
     * @details Executes multiple attack hits for a character against a victim, considering skills, effects, and special conditions.
    This function manages the attack sequence for a character ('ch') against a victim ('victim') using a specified attack skill ('attack_skill'). It resets the combat timer if the character is not an NPC, executes an initial attack, and then performs additional attacks based on character skills, effects, and equipment, such as dual-wielding, haste, slow, and special remort effects. It also checks for combat-related effects like clumsiness and weapon dropping due to remort abilities. The function dispatches attack messages, applies effects, and updates combat state accordingly, but does not return a value.
     *
     * @param ch Pointer to the attacking Character initiating the attack sequence.
     * @param victim Pointer to the target Character being attacked.
     * @param attack_skill The skill::type representing the attack type or skill used in the attack sequence.
     * @return Void; performs attack actions and side effects without returning a value.
     */

  0.634  one_hit                                  — Performs a single attack action from one character to another, calcula
    /**
     * @fn void one_hit(Character *ch, Character *victim, skill::type attack_skill, bool secondary)
     *
     * @brief Performs a single attack action from one character to another, calculating hit chance, damage, and applying special effects based on weapons and skills.
     *
     * @details This function executes a single combat hit from the attacker (ch) to the victim, considering weapon type, attack skill, character attributes, and situational modifiers. It determines attack type, calculates hit probability using THAC0 and armor class, and if successful, computes damage with weapon dice, skills, and bonuses. It also handles special weapon effects, such as poison or elemental damage, and applies additional spell effects like blindness or curses based on weapon attributes and attack context. The function manages different attack modes, including shadow form and riposte, and includes chance-based effects like berserker strikes. It ensures proper validation of characters' states and positions before executing the attack, and logs or applies effects accordingly.
     *
     * @param ch Pointer to the attacking Character initiating the hit.
     * @param victim Pointer to the target Character being attacked.
     * @param attack_skill The skill::type representing the attack type or skill used.
     * @param secondary Boolean indicating if the attack is from the secondary weapon slot.
     * @return Void; the function performs the attack and applies effects without returning a value.
     */

  0.630  damage                                   — Calculates and applies damage from an attack to a victim, considering 
    /**
     * @fn bool damage(Character *ch, Character *victim, int dam, skill::type attack_skill, int attack_type, int dam_type, bool show, bool spell)
     *
     * @brief Calculates and applies damage from an attack to a victim, considering various effects, defenses, and messaging.
     *
     * @details Inflicts damage from a hit on a victim, applying various modifiers, effects, and messaging.
    This function handles damage calculation and application in combat scenarios. It accounts for spell effects, damage modifications based on character attributes, armor, and special effects like sanctuary, barrier, and elemental auras. It also manages defensive checks such as dodge, parry, shield block, and blur, and applies damage reductions from various effects. The function updates the victim's hit points, triggers death if necessary, and sends appropriate damage messages. It also handles special cases like healing effects from divine attributes and link-dead character handling. The function performs side effects such as logging, messaging, and state updates, and returns a boolean indicating whether the victim survived or was killed.
     *
     * @param ch Pointer to the attacking or damaging Character object.
     * @param victim Pointer to the Character object receiving damage.
     * @param dam Integer amount of damage to be inflicted.
     * @param attack_skill Skill type used for the attack, influencing damage and effects.
     * @param dam_type Damage type, used for resistances and effects.
     * @param show Boolean indicating whether to display damage messages.
     * @param spell Boolean indicating if the damage is from a spell, affecting damage calculations.
     * @return Boolean indicating whether the damage resulted in the victim's death or incapacitation (false if dead, true otherwise).
     */

  0.625  mob_hit                                  — Handles attack actions for a mobile character, including single and mu
    /**
     * @fn void mob_hit(Character *ch, Character *victim, skill::type attack_skill)
     *
     * @brief Handles attack actions for a mobile character, including single and multiple strikes, special attacks, and combat maneuvers.
     *
     * @details This function orchestrates the attack behavior of a non-player character (mob) during combat. It initiates a primary attack, potentially performs a secondary attack if conditions are met, executes area attacks if enabled, and applies effects such as haste or fast flags. It also randomly selects and performs special combat maneuvers like bash, berserk, disarm, kick, dirt kick, trip, or crush, depending on the mob's offensive flags. The function ensures that attack sequences respect combat state, character conditions, and skill levels, and it prevents infinite loops by checking attack skill types. It interacts with other combat-related functions to perform hits, apply effects, and manage combat state.
     *
     * @param ch Pointer to the attacking Character (mob) performing the attack sequence.
     * @param victim Pointer to the target Character being attacked.
     * @param attack_skill The skill::type representing the primary attack skill used in this attack cycle.
     * @return Void; the function performs attack actions and side effects without returning a value.
     */

  0.567  set_fighting                             — Initiates combat between two characters.
    /**
     * @fn void set_fighting(Character *ch, Character *victim)
     *
     * @brief Initiates combat between two characters.
     *
     * @details This function sets a character to start fighting a specified victim. If the character is already engaged in combat, it logs a bug and exits. If the character is affected by sleep, the sleep affect is removed. The character's fighting target is set to the victim. If the character is not waiting and is not standing, their position is set to standing. If the character's starting position is flying and they can fly, their position is set to flying.
     *
     * @param ch A pointer to the Character object that is initiating combat.
     * @param victim A pointer to the Character object that is the target of the combat.
     * @return This function does not return a value.
     */

  0.565  fireball_bash                            — Calculates and applies a fireball bash effect that may knock a victim 
    /**
     * @fn void fireball_bash(Character *ch, Character *victim, int level, int evolution, bool spread)
     *
     * @brief Calculates and applies a fireball bash effect that may knock a victim to the ground based on various combat factors.
     *
     * @details This function computes the chance of a fireball bash effect successfully knocking a victim down, considering factors such as size, strength, level differences, effects like haste or fast flags, stamina, dodge skill, visibility, and specific resistances like pass door. It adjusts the chance based on whether the attack is spread or performed by a mage, and accounts for the victim's standfast skill, which can reduce the chance. If the random roll succeeds, it sends appropriate messages to involved characters, dazes the victim for a calculated duration, and sets their position to resting. If the effect fails and the victim has standfast, it may improve that skill.
     *
     * @param ch Pointer to the Character initiating the attack.
     * @param victim Pointer to the Character being affected by the bash.
     * @param level Integer representing the attacker's level influencing the chance.
     * @param evolution Integer indicating evolution stage affecting the effect's strength.
     * @param spread Boolean indicating if the attack is spread, reducing the chance.
     * @return This function has no return value; it performs side effects such as messaging, dazing the victim, and changing their position.
     */

  0.553  dragon                                   — Executes a dragon's special attack if conditions are met.
    /**
     * @fn bool dragon(Character *ch, skill::type sn)
     *
     * @brief Executes a dragon's special attack if conditions are met.
     *
     * @details This function determines if a dragon character can perform a special attack on a victim during combat. It first checks if the dragon is in a fighting position. It then iterates through potential victims in the same room to find one that the dragon can see and is currently fighting the dragon. A pseudo-random check is performed to decide if the attack should proceed. If a suitable victim is found and the dragon has sufficient mana, the function executes the skill associated with the specified skill type on the victim.
     *
     * @param ch A pointer to the Character object representing the dragon attempting the special attack.
     * @param sn The skill::type enumeration value representing the type of skill or spell the dragon is attempting to use.
     * @return Returns true if the dragon successfully executes the special attack on a victim, otherwise returns false.
     */

  0.551  check_dual_parry                         — Checks for a successful dual-wield parry from the off-hand and handles
    /**
     * @fn bool check_dual_parry(Character *ch, Character *victim, skill::type attack_skill, int attack_type)
     *
     * @brief Checks for a successful dual-wield parry from the off-hand and handles associated combat effects.
     *
     * @details This function determines whether a character successfully parries an attack using their off-hand weapon, considering various conditions such as paralysis effects, skill levels, equipment, visibility, and character evolution stages. It calculates the chance of parry based on skills and weapon types, performs the roll, and if successful, displays appropriate combat messages. It also handles special counterattacks like hilt strikes, including dodge, blur, and shield block checks, and applies damage and healing effects accordingly. The function updates skill improvements and manages visual effects, providing a comprehensive response to dual parry attempts during combat.
     *
     * @param ch Pointer to the attacking Character performing the attack.
     * @param victim Pointer to the defending Character attempting to parry with the off-hand weapon.
     * @param attack_skill The skill::type representing the attack's skill type, used for damage message lookup.
     * @return Boolean value indicating whether the parry was successful (true) or not (false).
     */

  0.550  raw_kill                                 — Handles the death of a character by stopping combat, triggering death 
    /**
     * @fn void raw_kill(Character *victim)
     *
     * @brief Handles the death of a character by stopping combat, triggering death effects, creating a corpse if applicable, and performing cleanup and saving operations.
     *
     * @details This function manages the process of killing a character in the game. It first stops any fighting involving the victim and triggers death-related mob programs. If the victim is marked as garbage, the function exits early. Otherwise, it checks the victim's location; if not in an arena, quest area, or duel room, it creates a corpse object. For NPCs, it increments their kill count and fully extracts them from the game. For player characters, it resets their PK timer, removes all affects, and depending on their location, either fully extracts them or relocates them to an altar room, resetting their armor. It then resets the victim's position and health/mana/stamina to minimal values, saves their character data, and saves ground items. The function performs side effects such as removing the character from the game world, creating corpses, and updating persistent data, but does not return a value.
     *
     * @param victim Pointer to the Character object representing the character to be killed.
     * @return Void; the function performs side effects such as removing the character, creating a corpse, and saving data, without returning a value.
     */

  0.541  check_dodge                              — Checks whether a character successfully dodges an attack, considering 
    /**
     * @fn bool check_dodge(Character *ch, Character *victim, skill::type attack_skill, int attack_type)
     *
     * @brief Checks whether a character successfully dodges an attack, considering various factors and possibly triggering a defensive heal.
     *
     * @details This function evaluates if the 'victim' character successfully dodges an attack from 'ch' based on their dodge skill level, size, attributes, active effects (such as haste or slow), visibility, and level difference. It incorporates randomness via a chance roll and adjusts the dodge probability accordingly. If the dodge succeeds, it outputs appropriate messages to both characters, possibly triggers a healing effect if certain conditions are met, and updates skill improvement. The function returns true if the dodge occurs, false otherwise. It also accounts for special effects like paralysis, and logs bugs if attack types are invalid.
     *
     * @param ch Pointer to the attacking Character object.
     * @param victim Pointer to the defending Character object attempting to dodge.
     * @param attack_skill The skill::type representing the attack's skill type, used for damage message lookup.
     * @return Boolean value indicating whether the dodge was successful (true) or not (false).
     */

  0.529  stop_fighting                            — Stops a character from fighting and updates their position.
    /**
     * @fn void stop_fighting(Character *ch, bool fBoth)
     *
     * @brief Stops a character from fighting and updates their position.
     *
     * @details Stops the fighting for a character and optionally for their opponent.
    This function iterates over all characters in the game world and stops the specified character, 'ch', from fighting. If 'fBoth' is true, it also stops any character currently fighting 'ch'. The fighting status is cleared, and the character's position is reset based on whether they are an NPC or not. The position is updated using the 'update_pos' function.
     *
     * @param ch A pointer to the Character object whose fighting status is to be stopped.
     * @param fBoth A boolean flag indicating whether to stop the fighting for both the specified character and their opponent.
     * @return This function does not return a value.
     */

  0.529  check_parry                              — Checks whether a character successfully parries an attack and executes
    /**
     * @fn bool check_parry(Character *ch, Character *victim, skill::type attack_skill, int attack_type)
     *
     * @brief Checks whether a character successfully parries an attack and executes related effects.
     *
     * @details This function determines if the victim character successfully parries an incoming attack based on their skill level, equipped weapon, visibility, and level difference. It accounts for special conditions such as paralysis effects, weapon types, and whether the attacker is visible. Upon a successful parry, it displays appropriate messages, possibly triggers a riposte if the victim can use such skills, and applies defensive healing effects like Montrey's Grace. The function also updates skill improvement chances and handles special effects for NPCs and players. It returns true if the parry occurs, otherwise false.
     *
     * @param ch Pointer to the attacking character initiating the attack.
     * @param victim Pointer to the character attempting to parry the attack.
     * @param attack_skill The skill type used in the attack, influencing damage message selection.
     * @return Boolean value indicating whether the parry was successful (true) or not (false).
     */

  0.522  kill_off                                 — Handles the death of a character, including logging, experience distri
    /**
     * @fn void kill_off(Character *ch, Character *victim)
     *
     * @brief Handles the death of a character, including logging, experience distribution, corpse management, and kill statistics.
     *
     * @details Handles the death of a character, including logging, experience distribution, corpse creation, looting, and updating kill/death statistics.
    This function manages the process when a character (victim) is killed by another character (ch). It logs the death event, broadcasts notifications, awards experience points, handles corpse looting and auto-sacrifice, updates kill counts and war status, and performs cleanup such as removing the victim from the game world. Special considerations are made for NPC and player characters, including experience adjustments and arena-related rewards. The function also manages the creation of loot and handles potential suicide cases.
     *
     * @param ch Pointer to the Character object performing the kill or causing death.
     * @param victim Pointer to the Character object who is being killed.
     * @return Void; the function performs side effects such as logging, experience distribution, corpse handling, and updating character statistics, without returning a value.
     */

  0.518  check_shblock                            — Checks if a character successfully blocks an attack with a shield and 
    /**
     * @fn bool check_shblock(Character *ch, Character *victim, skill::type attack_skill, int attack_type)
     *
     * @brief Checks if a character successfully blocks an attack with a shield and applies related effects.
     *
     * @details This function determines whether the victim character successfully performs a shield block against an attack from another character. It considers the victim's shield skill level, current effects such as paralysis, and compares a calculated chance against a random percentage. If successful, it displays appropriate messages, restores some health or mana based on attributes, and may trigger additional effects like healing from Montrey's Grace. It also updates the victim's condition and skill improvement status accordingly. The function returns true if the shield block occurs, otherwise false.
     *
     * @param ch Pointer to the attacking Character object.
     * @param victim Pointer to the defending Character object attempting to block.
     * @param attack_skill The skill::type representing the attack's skill type; used for damage message lookup.
     * @return Boolean value indicating whether the shield block was successful (true) or not (false).
     */

  0.509  trip                                     — Attempts to trip a victim character, applying effects and damage if su
    /**
     * @fn bool trip(Character *ch, Character *victim, int chance, skill::type attack_skill)
     *
     * @brief Attempts to trip a victim character, applying effects and damage if successful.
     *
     * @details This function calculates the chance to trip a victim based on size differences, attributes, speed, and level differences between the attacker and victim. It modifies the chance based on various conditions such as haste effects and size, then performs a skill check against a random percentile. If successful, it dazes and knocks the victim down, inflicts bash damage, and updates the victim's state accordingly. It also checks and possibly improves the victim's 'standfast' skill if applicable. The function returns true if the trip succeeds, otherwise false, and performs side effects such as damage application and state changes.
     *
     * @param ch Pointer to the attacker Character performing the trip.
     * @param victim Pointer to the victim Character being targeted for the trip.
     * @param chance Initial chance percentage for the trip attempt, modified within the function.
     * @param attack_skill The skill::type representing the attack skill used for damage calculation.
     * @return Boolean value indicating whether the trip was successful (true) or not (false).
     */

  0.506  update_pos                               — Updates the position of a character based on their hit points.
    /**
     * @fn void update_pos(Character *victim)
     *
     * @brief Updates the position of a character based on their hit points.
     *
     * @details Updates the position of a character based on their current hit points.
    This function adjusts the position of a character ('victim') according to their current hit points. If the character's hit points are greater than zero, their position is set to standing if they are currently stunned or worse. If the character is an NPC and their hit points are less than one, or if their hit points are less than or equal to -11, their position is set to dead. For hit points between -10 and -6, the position is set to mortal. For hit points between -5 and -3, the position is set to incapacitated. Otherwise, the position is set to stunned.
     *
     * @param victim A pointer to the Character object whose position is to be updated based on their hit points.
     * @return This function does not return a value.
     */

  0.490  defense_heal                             — Applies a defensive heal to a character based on a chance and percenta
    /**
     * @fn bool defense_heal(Character *victim, int chance, int percent)
     *
     * @brief Applies a defensive heal to a character based on a chance and percentage.
     *
     * @details The function attempts to heal a character by a specified percentage of their maximum hit points, mana, and stamina. The healing occurs only if a random chance check, determined by the 'chance' parameter, is successful. This function is primarily designed for use with Montrey's Grace 5-piece set bonus but can be adapted for other skills or bonuses. The healing amount is calculated as a percentage of the character's maximum attributes.
     *
     * @param victim A pointer to the Character object that is the target of the defensive heal.
     * @param chance An integer representing the percentage chance that the heal will occur.
     * @param percent An integer representing the percentage of the character's maximum attributes to heal.
     * @return Returns true if the heal is successfully applied, otherwise returns false.
     */

  0.489  check_blur                               — Checks whether a character successfully evades an attack using the 'bl
    /**
     * @fn bool check_blur(Character *ch, Character *victim, skill::type attack_skill, int attack_type)
     *
     * @brief Checks whether a character successfully evades an attack using the 'blur' skill, applying visual and healing effects if successful.
     *
     * @details This function evaluates the chance for a victim character to evade an attack through the 'blur' skill, considering factors such as paralysis, skill level, size, attributes, speed effects, visibility, and level differences. It computes a chance percentage, compares it against a random roll, and determines success or failure. On success, it displays appropriate messages to the attacker and victim, and may trigger a healing effect if the victim has a specific grace attribute. The function also attempts to improve the victim's skill proficiency based on the outcome. It returns true if the evasion is successful, otherwise false.
     *
     * @param ch Pointer to the attacker character attempting the attack.
     * @param victim Pointer to the defending character attempting to evade via blur.
     * @param attack_skill The skill type used for the attack, influencing the damage message.
     * @return Boolean value indicating whether the victim successfully evaded the attack using blur (true) or not (false).
     */

  0.485  prepare_char                             — Prepares a character for a duel by relocating them to the appropriate 
    /**
     * @fn void prepare_char(Character *ch, Duel *duel)
     *
     * @brief Prepares a character for a duel by relocating them to the appropriate preparation room, clearing effects, and resetting vital stats.
     *
     * @details This function handles the setup of a character prior to a duel. It removes the character from their current room, moves them to the designated challenger or defender preparation room based on their role in the duel, clears all non-permanent affects/spells from the character, resets their hit points, mana, and stamina to maximum values, and performs an automatic 'look' command to update their view of the environment. It ensures the character is in a clean state and correctly positioned for the upcoming duel.
     *
     * @param ch Pointer to the Character object to be prepared for the duel.
     * @param duel Pointer to the Duel object containing duel metadata and arena information.
     * @return Void; the function does not return a value but modifies the character's state and position.
     */

  0.479  xp_compute                               — Calculates experience points (XP) for a character after a kill and adj
    /**
     * @fn int xp_compute(Character *gch, Character *victim, int total_levels, int diff_classes)
     *
     * @brief Calculates experience points (XP) for a character after a kill and adjusts the killer's alignment.
     *
     * @details This function computes the experience points (XP) awarded to a character (gch) for defeating a victim character. The XP calculation is influenced by the level difference between the characters, the character's remort status, and various remort affect flags. Additionally, the function adjusts the killer's alignment based on the victim's alignment and other conditions. The function also applies modifiers based on the character's age, remort affects, and group dynamics, ensuring a balanced XP distribution among group members.
     *
     * @param gch A pointer to the Character object representing the killer whose XP and alignment are being calculated and adjusted.
     * @param victim A pointer to the Character object representing the defeated character.
     * @param total_levels The total levels of all characters in the group, used for XP distribution.
     * @param diff_classes The number of different classes in the group, used to calculate group XP bonuses.
     * @return The calculated experience points (XP) awarded to the character for the kill.
     */

  0.473  group_gain                               — Calculates and distributes experience points among group members after
    /**
     * @fn int group_gain(Character *ch, Character *victim)
     *
     * @brief Calculates and distributes experience points among group members after defeating a victim, adjusting their levels and handling related effects.
     *
     * @details This function computes experience points (XP) for each member of the group involved in defeating a victim, considering group composition, levels, and class variations. It updates each character's XP, handles level-up notifications, and manages item alignment restrictions. It also tracks the lowest XP awarded within the group for potential further processing. The function accounts for special room sectors and quest-related conditions, ensuring XP is only awarded under appropriate circumstances.
     *
     * @param ch Pointer to the Character initiating the group gain calculation, typically the attacker.
     * @param victim Pointer to the Character that was defeated, whose death triggers XP distribution.
     * @return Returns an integer representing the lowest experience points awarded to any group member during this gain calculation.
     */

  0.457  war_score_adjust                         — Adjusts the score of a clan in a war and handles defeat conditions.
    /**
     * @fn void war_score_adjust(War *war, Character *ch, Character *victim, int amount)
     *
     * @brief Adjusts the score of a clan in a war and handles defeat conditions.
     *
     * @details This function modifies the score of a victim's clan by subtracting a specified amount. If the resulting score is less than 1, it announces the defeat of the victim's clan, adjusts the clan's power, and handles any ongoing war conditions. It also updates the clan and war tables to reflect the changes. The function ensures that the war's state is consistent with the new scores and handles any necessary announcements or adjustments.
     *
     * @param war A pointer to the War object representing the current war.
     * @param ch A pointer to the Character object representing the participant who is adjusting the score.
     * @param victim A pointer to the Character object representing a member of the clan whose score is being adjusted.
     * @param amount An integer representing the amount by which the victim's clan score is to be decreased.
     * @return This function does not return a value.
     */

  0.443  death_cry                                — Handles the death cry event for a character, including messaging and o
    /**
     * @fn void death_cry(Character *ch)
     *
     * @brief Handles the death cry event for a character, including messaging and optional object creation.
     *
     * @details This function generates a death cry message for the specified character, potentially creates a related object (such as guts, head, or limbs) based on random selection and character's body parts, and broadcasts appropriate messages to surrounding rooms. It also manages object creation, formatting, and placement within the game world, and ensures messages are sent to adjacent rooms to simulate a realistic death event.
     *
     * @param ch Pointer to the Character object who has died, triggering the death cry and related effects.
     * @return Void; the function performs side effects such as messaging, object creation, and room notifications without returning a value.
     */

  0.431  get_weapon_skill                         — Determines the skill type associated with the weapon a character is wi
    /**
     * @fn skill::type get_weapon_skill(Character *ch, bool secondary)
     *
     * @brief Determines the skill type associated with the weapon a character is wielding.
     *
     * @details This function evaluates the weapon a character is wielding, either primary or secondary, and returns the corresponding skill type. It checks the character's equipment at the specified wear location to identify the weapon type. If no weapon is found or the item is not a weapon, it defaults to hand-to-hand combat skill. The function supports various weapon types such as sword, dagger, spear, and others, mapping each to a specific skill type.
     *
     * @param ch A pointer to the Character whose weapon skill is being determined.
     * @param secondary A boolean indicating whether to check the secondary weapon slot (true) or the primary weapon slot (false).
     * @return The skill::type enumeration value representing the skill associated with the weapon being wielded, or hand-to-hand if no weapon is wielded.
     */

  0.408  make_corpse                              — Creates a corpse object from a character, transferring relevant attrib
    /**
     * @fn void make_corpse(Character *ch)
     *
     * @brief Creates a corpse object from a character, transferring relevant attributes and items, and places it in the game world.
     *
     * @details This function generates a corpse object based on whether the character is an NPC or a player. It initializes the corpse with appropriate timers, ownership, and description, and transfers the character's inventory items to the corpse, handling special item types and decay timers. It also removes the character's equipped weapon before creating the corpse. The corpse is then placed in a location determined by the character's war status, level, or default morgue room. The function ensures proper cleanup and item handling to simulate death in the game environment.
     *
     * @param ch Pointer to the Character object that is to be turned into a corpse.
     * @return Void; the function performs side effects such as creating and placing a corpse object in the game world.
     */


================================================================================
[domain] skills_progression  (stability: stable)
  desc: Skill and level progression: skill lookup by name and index, proficiency queries and updates, weapon skill levels, evolu…
  locked: 31 functions, 31 with embeddings
  sim to desc — mean: 0.539  min: 0.299  max: 0.659

  0.659  get_learned                              — Retrieves the learned level of a skill for a character.
    /**
     * @fn int get_learned(const Character *ch, skill::type sn)
     *
     * @brief Retrieves the learned level of a skill for a character.
     *
     * @details Retrieves the learned level of a specified skill for a character.
    This function checks if the given character is a non-player character (NPC) or if the skill type is unknown. If either condition is true, it returns 0, indicating that the skill is not learned. Otherwise, it returns the learned level of the specified skill type for the character, which is stored in the character's 'pcdata' structure.
     *
     * @param ch A pointer to the Character object for which the learned skill level is being queried.
     * @param sn The skill type enumeration value representing the skill whose learned level is to be retrieved.
     * @return An integer representing the learned level of the specified skill for the character. Returns 0 if the character is an NPC or if the skill type is unknown.
     */

  0.644  get_evolution                            — Calculates the evolution level of a character for a given skill type.
    /**
     * @fn int get_evolution(const Character *ch, skill::type type)
     *
     * @brief Calculates the evolution level of a character for a given skill type.
     *
     * @details Determines the evolution level of a character for a given skill type.
    This function determines the evolution level of a character based on whether the character is a non-player character (NPC) or a player character (PC). If the character is an NPC, the evolution level is set to 1. For player characters, the evolution level is retrieved from the character's 'pcdata' structure for the specified skill type and is clamped between 1 and 4 using the URANGE macro.
     *
     * @param ch A pointer to the Character object whose evolution level is being determined.
     * @param type The skill type for which the evolution level is being queried.
     * @return Returns an integer representing the evolution level of the character for the specified skill type. The value is 1 for NPCs and between 1 and 4 for player characters, based on their evolution data.
     */

  0.622  get_weapon_learned                       — Calculates the weapon skill level for a character.
    /**
     * @fn int get_weapon_learned(Character *ch, skill::type sn)
     *
     * @brief Calculates the weapon skill level for a character.
     *
     * @details Calculates the learned skill level for a weapon based on character type and skill type.
    This function determines the weapon skill level for a given character based on whether the character is a non-player character (NPC) or a player character (PC). For NPCs, the skill level is calculated using predefined formulas based on the character's level and the skill type. For PCs, the skill level is determined using the get_skill_level function. The resulting skill level is bounded between 0 and 100.
     *
     * @param ch A pointer to the Character object for which the weapon skill level is being calculated.
     * @param sn The skill::type enumeration value representing the weapon skill whose level is to be determined.
     * @return An integer representing the learned skill level for the specified weapon, adjusted for character type and bounded between 0 and 100.
     */

  0.622  get_skill_level                          — Calculates the skill level for a character based on skill type and cha
    /**
     * @fn int get_skill_level(const Character *ch, skill::type sn)
     *
     * @brief Calculates the skill level for a character based on skill type and character attributes.
     *
     * @details Calculates the skill level for a given character and skill type.
    This function determines the effective skill level for a given character and skill type. It considers whether the character is a player or a non-player character (NPC), the character's level, guild, and various flags that may affect skill proficiency. For player characters, it checks if the skill is usable at the character's level and retrieves the learned skill level. For NPCs, it uses predefined rules based on skill type and character flags. The function also adjusts the skill level based on the character's daze status and drunkenness condition, ensuring the final skill level is within a range of 0 to 100.
     *
     * @param ch A pointer to the Character object for which the skill level is being calculated.
     * @param sn The skill::type enumeration value representing the skill whose level is to be determined.
     * @return An integer representing the calculated skill level for the specified character and skill type, constrained between 0 and 100.
     */

  0.613  prac_by_key                              — Displays a list of skills and spells sorted by percentage or name for 
    /**
     * @fn void prac_by_key(Character *ch, const String &key, const char *argument)
     *
     * @brief Displays a list of skills and spells sorted by percentage or name for a character.
     *
     * @details The function 'prac_by_key' generates and displays a list of skills and spells known by the specified character, sorted according to the given key. The list is filtered based on the character's level, guild, and whether they can use remort skills. The skills are displayed in columns, with each skill's name and learned percentage. The function also shows the number of practice sessions the character has left.
     *
     * @param ch A pointer to the Character object for whom the skills and spells are being listed.
     * @param key A String object that determines the sorting criteria, either by percentage ('') or by name.
     * @param argument A C-style string representing additional arguments, from which the first argument is extracted and used as a filter for skill names.
     * @return This function does not return a value.
     */

  0.606  evolve_list                              — Generates and displays a list of skills and spells that a character ca
    /**
     * @fn void evolve_list(Character *ch)
     *
     * @brief Generates and displays a list of skills and spells that a character can evolve.
     *
     * @details This function constructs a formatted list of skills and spells that the specified character can potentially evolve. It iterates over all skills in the skill table, checking if each skill is known and evolvable by the character. For each skill, it appends a formatted line to the output buffer, indicating the skill name, learned percentage, current evolution level, and the cost for the next evolution if applicable. The function concludes by displaying the total skill points available to the character and sends the complete formatted output to the character's output buffer for display.
     *
     * @param ch A pointer to the Character object for whom the evolvable skills and spells list is being generated.
     * @return This function does not return a value.
     */

  0.605  set_evolution                            — Sets the evolution level for a specific skill type for a character.
    /**
     * @fn void set_evolution(Character *ch, skill::type sn, int value)
     *
     * @brief Sets the evolution level for a specific skill type for a character.
     *
     * @details Sets the evolution level of a skill for a character.
    This function assigns an evolution level to a specific skill type for a character, provided the character is not a non-player character (NPC) and the skill type is known. The evolution level is constrained between 1 and 4. If the character is an NPC or the skill type is unknown, the function exits without making any changes.
     *
     * @param ch A pointer to the Character object for which the skill evolution level is being set.
     * @param sn The skill::type enumeration value representing the skill whose evolution level is to be set.
     * @param value The desired evolution level for the skill, which will be clamped between 1 and 4.
     * @return This function does not return a value.
     */

  0.591  get_random_skill                         — Selects a random skill or spell that the character can use.
    /**
     * @fn skill::type get_random_skill(Character *ch)
     *
     * @brief Selects a random skill or spell that the character can use.
     *
     * @details This function iterates over the available skills and spells in the skill_table to find one that the specified character can use. It checks each skill to ensure the character has a valid skill level (between 1 and 99), can use remort skills if applicable, and meets the level requirements. If no usable skills are found, it returns an unknown skill type. Otherwise, it randomly selects one of the usable skills.
     *
     * @param ch A pointer to the Character object for which a random usable skill or spell is being selected.
     * @return A skill::type enumeration value representing a randomly selected skill or spell that the character can use, or skill::type::unknown if no such skill is available.
     */

  0.583  can_evolve                               — Determines if a character can evolve a specified skill type.
    /**
     * @fn int can_evolve(Character *ch, skill::type type)
     *
     * @brief Determines if a character can evolve a specified skill type.
     *
     * @details This function checks whether a character, represented by a pointer to a Character object, can evolve a given skill type. It considers various conditions such as the character's immortality status, the skill's evolution cost, and the character's current evolution and learned levels for the skill. The function returns different values based on these conditions, indicating whether the skill is evolvable, already at maximum evolution, or not evolvable.
     *
     * @param ch A pointer to the Character object for which the evolution capability is being checked.
     * @param type The skill type enumeration value representing the skill whose evolvability is being determined.
     * @return Returns 1 if the skill is evolvable, 0 if it is already at maximum evolution, and -1 if it is not evolvable.
     */

  0.575  skill::num_skills                        — Returns the number of skills available.
    /**
     * @fn int skill::num_skills()
     *
     * @brief Returns the number of skills available.
     *
     * @details This function calculates and returns the number of skills by accessing the skill_table, which is assumed to be a container holding skill data. The function returns the size of this container minus one, possibly indicating that the container includes an extra element that should not be counted as a skill.
     *
     * @return The number of skills available, calculated as the size of the skill_table minus one.
     */

  0.570  prac_by_group                            — Displays a list of skills and spells known by the character, sorted by
    /**
     * @fn void prac_by_group(Character *ch, const String &argument)
     *
     * @brief Displays a list of skills and spells known by the character, sorted by group.
     *
     * @details The function 'prac_by_group' generates and sends a formatted list of skills and spells that the character knows, organized by their respective groups. It iterates through all available groups, checking if the character knows the group and if it is relevant to their class. For each group, it lists the skills and spells that the character has learned and are within their usable level. The output is formatted into columns and includes a header for each group. Finally, it appends the number of practice sessions the character has left and sends the complete output to the character's display buffer.
     *
     * @param ch A pointer to the Character object for whom the skills and spells list is being generated.
     * @param argument A String object representing an optional prefix to filter the groups by name.
     * @return This function does not return a value.
     */

  0.565  get_skill_cost                           — Calculates the mana cost for a given skill type for a character.
    /**
     * @fn int get_skill_cost(Character *ch, skill::type type)
     *
     * @brief Calculates the mana cost for a given skill type for a character.
     *
     * @details Calculates the mana cost for a character to use a specified skill.
    This function determines the mana cost required for a character to use a specified skill type. The cost is initially based on the minimum mana required for the skill. If the skill is not a spell (i.e., its spell function is 'spell_null') and the character's level is 50 or below, the cost is adjusted based on the character's level relative to the skill's usable level. For non-player characters (NPCs), additional adjustments are made based on remort affect flags: 'RAFF_COSTLYSPELLS' increases the cost, while 'RAFF_CHEAPSPELLS' decreases it.
     *
     * @param ch A pointer to the Character object for which the skill cost is being calculated.
     * @param type The skill::type enumeration value representing the skill for which the cost is being calculated.
     * @return The mana cost required for the character to use the specified skill.
     */

  0.562  find_spell                               — Finds a spell that the character can cast based on a prefix match.
    /**
     * @fn skill::type find_spell(Character *ch, const String &name)
     *
     * @brief Finds a spell that the character can cast based on a prefix match.
     *
     * @details Finds a spell that a character can cast based on a prefix match.
    This function attempts to find a spell that a given character can cast by matching the provided name prefix against the skill names in the skill_table. If the character is a non-player character (NPC), it directly returns the skill type based on the prefix match. For player characters, it iterates through the skill_table, checking if the name is a prefix of any skill name. If a match is found and the character has a non-zero skill level for that skill, the function returns the corresponding skill type. If no such skill is found, it returns the first matching skill type or skill::type::unknown if no matches are found.
     *
     * @param ch A pointer to the Character object for which the spell is being searched.
     * @param name The String object representing the prefix to match against skill names.
     * @return The skill::type corresponding to the first skill whose name matches the given prefix and the character can cast, or skill::type::unknown if no such skill is found.
     */

  0.550  set_learned                              — Sets the learned value of a skill for a character.
    /**
     * @fn void set_learned(Character *ch, skill::type sn, int value)
     *
     * @brief Sets the learned value of a skill for a character.
     *
     * @details This function assigns a learning value to a specific skill for a given character. It first checks if the character is a non-player character (NPC) or if the skill type is unknown. If either condition is true, the function returns without making any changes. Otherwise, it sets the learned value of the specified skill to the provided value, constrained between 0 and 100.
     *
     * @param ch A pointer to the Character object whose skill learning value is to be set.
     * @param sn The skill type enumeration value representing the skill to be modified.
     * @param value The desired learning value for the specified skill, which will be clamped between 0 and 100.
     * @return This function does not return a value.
     */

  0.549  list_extraskill                          — Displays a list of extraclass remort skills for a character.
    /**
     * @fn void list_extraskill(Character *ch)
     *
     * @brief Displays a list of extraclass remort skills for a character.
     *
     * @details This function generates and sends a formatted list of extraclass remort skills available to a character, excluding those from the character's own guild unless the character is immortal. It iterates over all guilds and skills, checking conditions such as the character's immortality status and skill usability. The formatted list is then sent to the character's output buffer for display.
     *
     * @param ch A pointer to the Character object for whom the extraclass remort skills are being listed.
     * @return This function does not return a value.
     */

  0.543  npc_advance_level                        — Advances the level of a non-player character (NPC).
    /**
     * @fn void npc_advance_level(Character *ch)
     *
     * @brief Advances the level of a non-player character (NPC).
     *
     * @details This function is used to advance the level of a non-player character (NPC), specifically a pet. It is typically called immediately after the advance_level() function. The function increases the NPC's base attributes: hit points, mana, and stamina, based on the character's constitution, intelligence, and strength attributes, respectively. If the character is not an NPC, the function returns without making any changes.
     *
     * @param ch A pointer to the Character object whose level is to be advanced.
     * @return This function does not return a value.
     */

  0.530  completed_group                          — Checks whether a character has completed a specified skill group or al
    /**
     * @fn bool completed_group(Character *ch, int gn)
     *
     * @brief Checks whether a character has completed a specified skill group or all skills within it.
     *
     * @details This function determines if a given character has either already acquired the entire skill group identified by 'gn' or has learned all individual skills contained within that group. It first verifies that the character belongs to a valid guild; if not, it returns false. If the character has already known the group, it returns true. Otherwise, it iterates through each spell in the group's spell list, resolving nested groups via 'group_lookup' and recursively checking their completion status. For individual skills, it uses 'skill::lookup' and 'get_learned' to verify if the character has learned each skill at a level greater than zero. The function returns true only if all conditions for completion are met, otherwise false.
     *
     * @param ch Pointer to the Character object representing the player whose group completion status is being checked.
     * @param gn Integer index identifying the skill group in 'group_table' to verify for completion.
     * @return A boolean value indicating whether the character has completed the specified group or all skills within it (true) or not (false).
     */

  0.525  group_add                                — Adds a specified skill or group to a character, optionally deducting p
    /**
     * @fn void group_add(Character *ch, const String &name, bool deduct)
     *
     * @brief Adds a specified skill or group to a character, optionally deducting points.
     *
     * @details Adds a specified skill or group to a character's known skills or groups, optionally deducting points.
    This function processes the addition of a skill or group identified by name to the given character. It first checks if the character is a non-player character (NPC) or has no guild, in which case it exits early. If the name corresponds to a known skill, it ensures the character does not already know it, then sets the skill as learned and initializes its evolution level. If the 'deduct' flag is true, it increases the character's points based on the skill's rating for the character's guild. If the name does not match a skill, it attempts to find a group with the given name. If found and the group is not already known, it marks the group as known and optionally deducts points based on the group's rating. It then ensures all skills within the group are recognized by calling 'gn_add'.
     *
     * @param ch Pointer to the Character object to which the skill or group will be added.
     * @param name The String object representing the name of the skill or group to add.
     * @param deduct Boolean flag indicating whether to deduct points from the character's points pool when adding the skill or group.
     * @return Void; the function modifies the character's attributes directly and does not return a value.
     */

  0.525  demote_level                             — Demotes a character's level by reducing their attributes and skills.
    /**
     * @fn void demote_level(Character *ch)
     *
     * @brief Demotes a character's level by reducing their attributes and skills.
     *
     * @details Demotes a character by reducing their attributes and resources.
    This function reduces a character's hit points, mana, stamina, practice points, and training points as part of a level demotion process. The reductions are based on the character's attributes and guild-specific rules. The function also updates the character's last level playing time and sends a formatted message to the character detailing the losses incurred.
     *
     * @param ch A pointer to the Character object that is being demoted.
     * @return This function does not return a value.
     */

  0.522  get_usable_level                         — Calculates the usable level of a character.
    /**
     * @fn int get_usable_level(Character *ch)
     *
     * @brief Calculates the usable level of a character.
     *
     * @details This function determines the effective level of a character based on their status. If the character is immortal, it returns a level of 1000. For non-player characters (NPCs), it returns their current level. For player characters, it adjusts the level based on whether they are a remort character, adding a bonus based on their remort count. The result is capped at LEVEL_HERO.
     *
     * @param ch A pointer to the Character object whose usable level is being calculated.
     * @return The effective level of the character, adjusted for immortality, NPC status, and remort status, capped at LEVEL_HERO.
     */

  0.517  check_improve                            — Checks and improves a character's skill based on success and condition
    /**
     * @fn void check_improve(Character *ch, skill::type type, bool success, int multiplier)
     *
     * @brief Checks and improves a character's skill based on success and conditions.
     *
     * @details Checks and updates a character's skill improvement based on success or failure of an action.
    This function evaluates whether a character, who is not an NPC and belongs to a guild, can improve a specified skill. It checks various conditions such as the character's level, guild, and current learned level of the skill. If the character is eligible, it calculates the chance of improvement based on the character's intelligence, skill rating, and other factors. If successful, the character's skill level is increased, and they gain experience points. The function handles both successful and unsuccessful attempts to use the skill, providing feedback to the character in both cases.
     *
     * @param ch Pointer to the Character object performing the skill attempt.
     * @param type The skill::type enumeration indicating which skill is being improved.
     * @param success Boolean indicating whether the skill attempt was successful.
     * @param multiplier An integer affecting the chance calculation; -1 indicates auto success.
     * @return This function has no return value; it modifies the character's skill level and experience directly.
     */

  0.514  get_holdable_level                       — Calculates the holdable level for a character.
    /**
     * @fn int get_holdable_level(Character *ch)
     *
     * @brief Calculates the holdable level for a character.
     *
     * @details This function determines the holdable level of a character based on their status. If the character is immortal, it returns a fixed level of 1000. For non-player characters (NPCs), it returns their current level. For player characters, it calculates the level based on whether they are remort (a character that has been reincarnated or reset) or not, adding a bonus to their current level based on their remort count or a fixed value.
     *
     * @param ch A pointer to the Character object for which the holdable level is being calculated.
     * @return The holdable level of the character, which is an integer value representing the effective level the character can hold items or perform actions at.
     */

  0.506  select_pose                              — Selects a pose for a character based on their class and level.
    /**
     * @fn int select_pose(Character *ch)
     *
     * @brief Selects a pose for a character based on their class and level.
     *
     * @details This function determines an appropriate pose for a character based on their guild membership and level. It first checks if the character is a non-player character (NPC) or lacks a guild, in which case it sends an appropriate message to the character and returns -1. If the character's guild has no poses implemented, it also returns -1. Otherwise, it calculates the maximum possible pose index based on the character's level and the number of poses available for their guild, and selects a random pose within this range.
     *
     * @param ch A pointer to the Character object for which the pose is being selected.
     * @return An integer representing the index of the selected pose, or -1 if the character cannot pose.
     */

  0.505  advance_level                            — Advances a character's level, updating their attributes and notifying 
    /**
     * @fn void advance_level(Character *ch)
     *
     * @brief Advances a character's level, updating their attributes and notifying them of the gains.
     *
     * @details Advances the level of a character, updating their attributes and notifying them of the changes.
    This function is responsible for advancing a character's level by updating their hit points, mana, stamina, practice points, and training points based on their attributes and guild-specific rules. It calculates the additional values for each attribute using random ranges and attribute modifiers, then applies these to the character's current stats. Finally, it sends a formatted message to the character detailing the gains in each attribute.
     *
     * @param ch A pointer to the Character object whose level is being advanced.
     * @return This function does not return a value.
     */

  0.502  skill::lookup                            — Looks up the skill type based on a prefix match with the skill name.
    /**
     * @fn type skill::lookup(const String &name)
     *
     * @brief Looks up the skill type based on a prefix match with the skill name.
     *
     * @details This function searches through the global skill_table to find a skill type whose name matches the given prefix. The function iterates over each entry in the skill_table, checking if the provided name is a prefix of the skill's name. If a match is found, it returns the corresponding skill type. If no match is found, it returns skill::type::unknown.
     *
     * @param name The String object representing the prefix to match against skill names in the skill_table.
     * @return The skill::type corresponding to the first skill whose name matches the given prefix, or skill::type::unknown if no match is found.
     */

  0.501  gn_add                                   — Recursively adds a group and its associated spells to a character's kn
    /**
     * @fn void gn_add(Character *ch, int gn)
     *
     * @brief Recursively adds a group and its associated spells to a character's known groups.
     *
     * @details Adds a specified group to the character's known groups and grants associated spells.
    This function marks the specified group identified by its index as known to the character by setting the corresponding entry in 'group_known' to true. It then iterates through all spells associated with the group in 'group_table' and adds each spell to the character's known skills using the 'group_add' function, without deducting points. The process effectively grants the character access to the entire group and its spells, modifying the character's attributes directly. It does not return a value.
     *
     * @param ch Pointer to the Character object to which the group is being added.
     * @param gn Integer index representing the group to be added.
     * @return Void; the function modifies the character's state directly and does not return a value.
     */

  0.490  skill::from_int                          — Converts an integer to a corresponding skill type.
    /**
     * @fn skill::type skill::from_int(int)
     *
     * @brief Converts an integer to a corresponding skill type.
     *
     * @details This function takes an integer and attempts to find a matching skill type in the global skill_table. It iterates over the skill_table, comparing each skill type's integer representation with the provided integer. If a match is found, it returns the corresponding skill type. If no match is found, it returns skill::type::unknown.
     *
     * @param sn The integer representation of a skill type to be converted.
     * @return The skill type corresponding to the given integer, or skill::type::unknown if no match is found.
     */

  0.482  exp_per_level                            — Calculates the experience points required per level for a character.
    /**
     * @fn int exp_per_level(Character *ch, int points)
     *
     * @brief Calculates the experience points required per level for a character.
     *
     * @details This function computes the experience points needed for a character to level up based on their status as a player or non-player character (NPC), their current points, and their guild affiliation. For NPCs, the experience required is a constant 1000. For player characters, the calculation is more complex and depends on the number of points and the character's guild. The function also considers a multiplier based on the character's race and guild combination.
     *
     * @param ch A pointer to the Character object for which the experience points are being calculated.
     * @param points An integer representing the base points used to calculate the experience required for leveling up.
     * @return The calculated experience points required for the character to level up.
     */

  0.426  guild_lookup                             — Looks up a guild by name using a prefix match.
    /**
     * @fn Guild guild_lookup(const String &name)
     *
     * @brief Looks up a guild by name using a prefix match.
     *
     * @details Finds the guild corresponding to the given name.
    This function searches through a list of guilds to find one whose name matches the given prefix. It iterates over all available guilds, checking if the provided 'name' is a prefix of any guild's name in the 'guild_table'. If a match is found, the corresponding Guild enumeration value is returned. If no match is found, the function returns 'Guild::none'.
     *
     * @param name The name of the guild to look up, provided as a String object.
     * @return The Guild enum value corresponding to the matched guild name, or Guild::none if no match is found.
     */

  0.413  gain_exp                                 — Increases a character's experience points and handles level progressio
    /**
     * @fn void gain_exp(Character *ch, int gain)
     *
     * @brief Increases a character's experience points and handles level progression, including level-up notifications and rewards.
     *
     * @details This function adds experience points to the specified character, ensuring that NPCs are unaffected and that characters already at or above the hero level do not gain experience. When sufficient experience is accumulated, the character levels up, triggering level-up messages, notifications to all players, and potential group or status updates such as hero or avatar groups. If the character reaches the hero level, special fireworks and congratulatory messages are broadcasted. Additionally, if the character has a pet, the pet may also gain a level based on the character's level increase. The function updates the character's experience, manages level transitions, and persists changes by saving the character's data.
     *
     * @param ch Pointer to the Character object whose experience is being gained and potentially leveled up.
     * @param gain Integer amount of experience points to add to the character.
     * @return This function has no return value; it performs in-place updates to the character's experience, level, and related states.
     */

  0.299  group_lookup                             — Finds the index of a group by its name.
    /**
     * @fn int group_lookup(const String &name)
     *
     * @brief Finds the index of a group by its name.
     *
     * @details This function searches through a list of groups to find the index of a group that matches the given name. It performs a case-insensitive comparison using the String class's capabilities. If a match is found, the index of the group is returned. If no match is found, the function returns -1.
     *
     * @param name The name of the group to search for in the group_table.
     * @return The index of the group with the matching name if found, otherwise -1.
     */


================================================================================
[utility] numerics  (stability: stable)
  desc: Numeric utilities: pseudo-random number generation (flat range, percentage, door index, fuzzy, bit-width), dice rolling,…
  locked: 13 functions, 13 with embeddings
  sim to desc — mean: 0.544  min: 0.326  max: 0.656

  0.656  number_door                              — Generates a random door number between 0 and 5.
    /**
     * @fn int number_door(void)
     *
     * @brief Generates a random door number between 0 and 5.
     *
     * @details Generates a random door number.
    This function repeatedly generates a pseudo-random number using the number_mm function and applies a bitwise AND operation with 7 (8 - 1) to limit the range. It continues this process until the result is a number between 0 and 5, inclusive. The function ensures that the returned value is always within this range, simulating a random selection of a door number.
     *
     * @return An integer representing a random door number between 0 and 5.
     */

  0.654  number_percent                           — Generates a pseudo-random percentage between 1 and 100.
    /**
     * @fn int number_percent(void)
     *
     * @brief Generates a pseudo-random percentage between 1 and 100.
     *
     * @details Generates a random percentile value.
    This function repeatedly generates a pseudo-random number using the number_mm function, masking it to fit within the range of 0 to 127. It continues to generate numbers until one falls within the range of 0 to 99, ensuring a uniform distribution of results. The function then returns this number incremented by 1, resulting in a final range of 1 to 100, simulating a percentage.
     *
     * @return An integer between 1 and 100 inclusive, representing a random percentile value.
     */

  0.599  number_range                             — Generates a random number within a specified range.
    /**
     * @fn int number_range(int from, int to)
     *
     * @brief Generates a random number within a specified range.
     *
     * @details This function generates a pseudo-random number between the specified 'from' and 'to' values, inclusive. It uses a bit manipulation technique to efficiently generate numbers within the desired range. The function first calculates the range size and adjusts it to be a power of two for efficient random number generation. It then uses a loop to ensure the generated number falls within the specified range.
     *
     * @param from The lower bound of the range, inclusive.
     * @param to The upper bound of the range, inclusive.
     * @return A pseudo-random integer within the inclusive range [from, to].
     */

  0.589  number_mm                                — Generates a pseudo-random number.
    /**
     * @fn long number_mm(void)
     *
     * @brief Generates a pseudo-random number.
     *
     * @details This function returns a pseudo-random number by calling the standard library function rand() and right-shifting the result by 6 bits. This effectively reduces the range of the generated number.
     *
     * @return A long integer representing a pseudo-random number generated by shifting the result of rand() by 6 bits.
     */

  0.586  number_fuzzy                             — Adjusts a number by a small random amount.
    /**
     * @fn int number_fuzzy(int number)
     *
     * @brief Adjusts a number by a small random amount.
     *
     * @details Applies a small random adjustment to a given number.
    The function takes an integer and randomly adjusts it by either decreasing it by 1, increasing it by 1, or leaving it unchanged. The adjustment is determined by generating a random number with 2 bits. If the random number is 0, the input number is decreased by 1. If the random number is 3, the input number is increased by 1. Otherwise, the number remains unchanged. The function ensures that the returned value is at least 1.
     *
     * @param number The integer to which a small random adjustment will be applied.
     * @return The adjusted number, which is guaranteed to be at least 1.
     */

  0.583  number_bits                              — Generates a pseudo-random number with a specified bit width.
    /**
     * @fn int number_bits(int width)
     *
     * @brief Generates a pseudo-random number with a specified bit width.
     *
     * @details This function generates a pseudo-random number by calling the number_mm function and then reduces the result to fit within a specified number of bits. The width parameter determines how many bits the resulting number will have, effectively limiting the range of the pseudo-random number.
     *
     * @param width The number of bits to include in the generated pseudo-random number. It determines the range of the output.
     * @return A pseudo-random number with a maximum of 'width' bits.
     */

  0.582  dice                                     — Simulates rolling a specified number of dice with a given number of si
    /**
     * @fn int dice(int number, int size)
     *
     * @brief Simulates rolling a specified number of dice with a given number of sides.
     *
     * @details The function calculates the sum of rolling 'number' dice, each with 'size' sides. If the size is 0, it returns 0, representing an invalid dice. If the size is 1, it returns the number of dice, as each roll would always result in 1. For other sizes, it uses the number_range function to generate random results for each die roll and sums them up.
     *
     * @param number The number of dice to roll.
     * @param size The number of sides on each die.
     * @return The total sum of the dice rolls, or a specific value based on the size of the dice.
     */

  0.576  roll_chance                              — Determines if a random chance is successful based on a given percentag
    /**
     * @fn int roll_chance(int percent)
     *
     * @brief Determines if a random chance is successful based on a given percentage.
     *
     * @details Determines if a random chance falls within a specified percentage.
    This function simulates a chance roll by generating a pseudo-random percentage and comparing it to the provided threshold. If the generated percentage is less than or equal to the specified percent, the function returns true, indicating a successful roll. Otherwise, it returns false.
     *
     * @param percent The percentage chance (1 to 100) that the event should occur.
     * @return Returns 1 (true) if the random percentage is less than or equal to the specified percent, indicating the event occurs; otherwise, returns 0 (false).
     */

  0.529  URANGE                                  
    /**
     * @def URANGE
     *
     */

  0.518  interpolate                              — Performs linear interpolation between two values based on a given leve
    /**
     * @fn int interpolate(int level, int value_00, int value_32)
     *
     * @brief Performs linear interpolation between two values based on a given level.
     *
     * @details Performs linear interpolation between two values.
    This function calculates an interpolated value between two integers, value_00 and value_32, based on a specified level. The level parameter determines the position between value_00 and value_32, where 0 corresponds to value_00 and 32 corresponds to value_32. The interpolation is linear, meaning the change between values is uniform across the range.
     *
     * @param level An integer representing the interpolation level, ranging from 0 to 32.
     * @param value_00 The starting integer value for interpolation, corresponding to level 0.
     * @param value_32 The ending integer value for interpolation, corresponding to level 32.
     * @return The interpolated integer value based on the specified level.
     */

  0.516  prd_chance                               — Determines success based on a pseudo-random chance and failure history
    /**
     * @fn bool prd_chance(int *prev_fails, int p)
     *
     * @brief Determines success based on a pseudo-random chance and failure history.
     *
     * @details Determines if an event occurs based on a probability and previous failures.
    This function calculates the probability of success based on a given chance percentage and the number of previous failures. It adjusts the chance of success using a predefined probability distribution table (prd_table) and the number of consecutive failures. If the generated random percentage is less than the calculated chance, the function returns true indicating success, and resets the failure count. Otherwise, it increments the failure count and returns false.
     *
     * @param prev_fails A pointer to an integer tracking the number of consecutive failures prior to this function call. It is updated based on the success or failure of the event.
     * @param p An integer representing the base probability of the event occurring, clamped between 0 and 100.
     * @return A boolean value indicating whether the event was successful (true) or not (false).
     */

  0.363  pow2gt                                   — Finds the smallest power of two greater than or equal to a given integ
    /**
     * @fn static int pow2gt(int x)
     *
     * @brief Finds the smallest power of two greater than or equal to a given integer.
     *
     * @details This function calculates the smallest power of two that is greater than or equal to the input integer x. It uses bit manipulation techniques to efficiently determine this value. The function assumes that x is a non-negative integer.
     *
     * @param x The integer for which to find the smallest power of two greater than or equal to it.
     * @return The smallest power of two that is greater than or equal to the input integer x.
     */

  0.326  dizzy_scantime                           — Decodes a time string formatted by dizzy_ctime into a time_t value.
    /**
     * @fn time_t dizzy_scantime(const String &ctime)
     *
     * @brief Decodes a time string formatted by dizzy_ctime into a time_t value.
     *
     * @details Converts a formatted date-time string into a time_t value.
    This function takes a time string formatted by dizzy_ctime and parses it into its constituent components such as day, month, year, hour, minute, and second. It then converts these components into a time_t value representing the same point in time. The function also logs errors if the input string is malformed or contains an invalid month.
     *
     * @param ctime A String object containing the date-time information to be parsed.
     * @return A 'time_t' value representing the parsed date and time, or the current time if parsing fails.
     */


================================================================================
[domain] economy  (stability: stable)
  desc: Economy and currency system: gold and silver handling, currency deduction and weight computation, money object creation,…
  locked: 9 functions, 9 with embeddings
  sim to desc — mean: 0.547  min: 0.365  max: 0.656

  0.656  gold_weight                             
    /**
     * @def gold_weight
     *
     */

  0.650  create_money                             — Creates a new game object representing a specified amount of money.
    /**
     * @fn Object * create_money(int gold, int silver)
     *
     * @brief Creates a new game object representing a specified amount of money.
     *
     * @details Creates a money object representing a specified amount of gold and silver.
    This function initializes a new Object representing a specified amount of gold and silver coins. It formats the object's name, short description, long description, and material based on the amount of money. If the total amount of money is zero or negative, it logs a bug and adjusts the values to ensure at least one coin is created. The function uses a prototype to create the object and assigns appropriate values to its attributes, such as name, description, material, value, cost, and weight.
     *
     * @param gold The number of gold coins to include in the money object.
     * @param silver The number of silver coins to include in the money object.
     * @return A pointer to the newly created Object representing the money, or nullptr if the object creation fails.
     */

  0.636  silver_weight                           
    /**
     * @def silver_weight
     *
     */

  0.580  find_money                               — Updates the banked gold and silver for a player character based on ela
    /**
     * @fn void find_money(Character *ch)
     *
     * @brief Updates the banked gold and silver for a player character based on elapsed time.
     *
     * @details Updates the banked gold and silver for a player character based on interest.
    The function 'find_money' calculates interest on a player character's banked gold and silver if more than a day has passed since the last update. It applies a 2% interest for each day elapsed. The function also ensures that the banked amounts do not exceed the maximum allowed based on the character's remort count. If the character is a non-player character (NPC), the function returns immediately without making any changes.
     *
     * @param ch A pointer to the Character object whose banked money is to be updated.
     * @return This function does not return a value.
     */

  0.564  deduct_cost                              — Deducts a specified cost from a character's currency.
    /**
     * @fn bool deduct_cost(Character *ch, int cost)
     *
     * @brief Deducts a specified cost from a character's currency.
     *
     * @details This function attempts to deduct a specified cost from the character's available silver and gold. If the cost is negative, it acts as a refund, adding the equivalent amount of silver and gold to the character's currency. If the character does not have enough total currency to cover the cost, the function returns false without making any deductions. Otherwise, it deducts the appropriate amount of silver and gold and returns true.
     *
     * @param ch A pointer to the Character object from which the cost will be deducted.
     * @param cost The amount of currency to be deducted. If negative, it is treated as a refund.
     * @return Returns true if the cost was successfully deducted or refunded. Returns false if the character does not have enough currency to cover the cost.
     */

  0.545  get_cost                                 — Calculates the cost of an object in a shop transaction.
    /**
     * @fn int get_cost(Character *keeper, Object *obj, bool fBuy)
     *
     * @brief Calculates the cost of an object in a shop transaction.
     *
     * @details This function determines the cost of an object when interacting with a shopkeeper, either for buying or selling. The cost is influenced by the shop's profit margins, the object's attributes, and its condition. Special conditions apply for quest items and items with specific statuses. The function also considers the shopkeeper's inventory to adjust the cost based on item availability.
     *
     * @param keeper A pointer to the Character representing the shopkeeper involved in the transaction.
     * @param obj A pointer to the Object whose cost is being calculated.
     * @param fBuy A boolean flag indicating whether the transaction is a purchase (true) or a sale (false).
     * @return The calculated cost of the object in the transaction, adjusted for shop profit margins and object attributes. Returns 0 if the object or shop data is invalid.
     */

  0.497  find_keeper                              — Finds an appropriate shopkeeper NPC in the character's current room fo
    /**
     * @fn Character * find_keeper(Character *ch)
     *
     * @brief Finds an appropriate shopkeeper NPC in the character's current room for trading purposes.
     *
     * @details This function searches the current room of the specified character to locate an NPC who is designated as a shopkeeper (i.e., has an associated Shop data). It skips over morphing NPCs and verifies shop hours and visibility conditions. If a suitable shopkeeper is found and the character is permitted to trade (not a killer or thief, if applicable), the function returns a pointer to the shopkeeper character; otherwise, it sends appropriate messages to the character and returns null.
     *
     * @param ch Pointer to the Character object initiating the shopping interaction; used to identify the current room and to send messages.
     * @return Pointer to the Character object representing the shopkeeper NPC if found and accessible; null if no suitable shopkeeper is present or conditions are not met.
     */

  0.431  Shop::is_questshop                       — Checks if the shop is a quest shop.
    /**
     * @fn bool Shop::is_questshop() const
     *
     * @brief Checks if the shop is a quest shop.
     *
     * @details This function determines whether the current shop is designated as a quest shop by checking if the first element of the 'buy_type' array is equal to 'ITEM_QUESTSHOP'. It is a constant member function, indicating that it does not modify any member variables of the class.
     *
     * @return Returns true if the shop is a quest shop, otherwise returns false.
     */

  0.365  Auction::is_participant                  — Checks if the given object is the item being auctioned.
    /**
     * @fn bool Auction::is_participant(Object *obj) const
     *
     * @brief Checks if the given object is the item being auctioned.
     *
     * @details This function determines whether the specified object is the current item in the auction. It checks if the auction has an item and if the provided object matches this item.
     *
     * @param obj A pointer to the Object that is being checked against the auctioned item.
     * @return Returns true if the auction has an item and the provided object is the same as the auctioned item; otherwise, returns false.
     */


================================================================================
[utility] text_editing  (stability: stable)
  desc: In-game line editor: editing session initialisation (descriptions, notes, help entries), line navigation and cursor posi…
  locked: 23 functions, 23 with embeddings
  sim to desc — mean: 0.553  min: 0.339  max: 0.648

  0.648  edit_status                              — Displays the current editing status to a character.
    /**
     * @fn static void edit_status(Character *ch, const String &argument)
     *
     * @brief Displays the current editing status to a character.
     *
     * @details This function provides feedback to a character about their current editing session. It checks if the character is editing anything and provides appropriate messages based on the editing context, such as notes, descriptions, or help text. It also lists available editing commands and displays the current line number and total lines being edited. If the character is not editing anything, it suggests actions they can take to start editing.
     *
     * @param ch A pointer to the Character object for whom the editing status is being displayed.
     * @param argument A constant reference to a String object representing any additional arguments passed to the function, though it is not used within this function.
     * @return This function does not return a value.
     */

  0.598  list_window                              — Displays a window of lines around the current edit line to the charact
    /**
     * @fn static void list_window(Character *ch)
     *
     * @brief Displays a window of lines around the current edit line to the character's output.
     *
     * @details The function 'list_window' checks if the character is currently editing a buffer. If not, it sends a message indicating that no editing is in progress. If the edit buffer is empty, it notifies the character of this state. Otherwise, it calculates a range of lines centered around the current edit line and calls 'edit_list1' to format and display these lines to the character's output buffer.
     *
     * @param ch A pointer to the Character object whose output buffer will receive the formatted lines.
     * @return This function does not return a value.
     */

  0.592  edit_insert                              — Inserts a string into the current editing buffer at a specified line.
    /**
     * @fn static void edit_insert(Character *ch, const String &argument)
     *
     * @brief Inserts a string into the current editing buffer at a specified line.
     *
     * @details The function inserts the given string argument into the editing buffer of a character at a specified line number. If the line number is not provided, it defaults to inserting after the current editing line. The function checks if the line number is valid and if the insertion would exceed the maximum allowed edit length. If the insertion is valid, it creates a backup of the current edit string, inserts the new text, and updates the line count. The character's current editing line is then set to the line after the insertion.
     *
     * @param ch A pointer to the Character object whose editing buffer is being modified.
     * @param argument The String object containing the text to be inserted into the editing buffer.
     * @return This function does not return a value.
     */

  0.592  edit_desc                                — Initializes the editing process for a character's description.
    /**
     * @fn static void edit_desc(Character *ch, const String &argument)
     *
     * @brief Initializes the editing process for a character's description.
     *
     * @details This function begins the editing process for a character's description. If the character is already editing something, it notifies the character and displays the current editing status. Otherwise, it initializes a new Edit object, sets the edit type to description, copies the character's long description into the edit string, creates a backup, counts the number of lines in the edit string, sets the current editing line to the first line, and displays the editing status.
     *
     * @param ch A pointer to the Character object whose description is to be edited.
     * @param argument A constant reference to a String object representing any additional arguments passed to the function, though it is not used within this function.
     * @return This function does not return a value.
     */

  0.589  edit_wrap                                — Wraps text in the editing buffer to fit within a specified width.
    /**
     * @fn static void edit_wrap(Character *ch, const String &argument)
     *
     * @brief Wraps text in the editing buffer to fit within a specified width.
     *
     * @details The function edit_wrap reformats text in the editing buffer of a character to ensure that lines do not exceed a predefined width (WRAP_WIDTH). It operates on either the current paragraph or a specified range of lines, adjusting line breaks to maintain readability. If no numeric arguments are provided, it wraps the paragraph containing the current editing line. If numeric arguments are present, it wraps the text between the specified line numbers. The function handles word boundaries and ensures that words are not split across lines unless they exceed the wrap width. It also maintains the original formatting by preserving blank lines before and after the wrapped text.
     *
     * @param ch A pointer to the Character object whose text is being wrapped.
     * @param argument A reference to a String object containing any additional arguments for the wrapping operation.
     * @return This function does not return a value.
     */

  0.586  edit_goto1                               — Sets the current editing line for a character.
    /**
     * @fn static void edit_goto1(Character *ch, int lineno)
     *
     * @brief Sets the current editing line for a character.
     *
     * @details This function updates the current line number for a character's editing session. If the provided line number is outside the valid range, it is clamped to the nearest valid value. The valid range is from 0 to the total number of lines available in the editing session.
     *
     * @param ch A pointer to the Character object whose editing line is to be set.
     * @param lineno The desired line number to set as the current editing line.
     * @return This function does not return a value.
     */

  0.585  edit_note                                — Initializes the note editing process for a character.
    /**
     * @fn static void edit_note(Character *ch, const String &argument)
     *
     * @brief Initializes the note editing process for a character.
     *
     * @details This function begins the note editing process for a character by setting up the necessary editing environment. If the character is already editing something, it informs the character and displays the current editing status. If the character has not started writing a note, it notifies the character of this fact. Otherwise, it initializes a new Edit object, sets the editing type to note, copies the current note text into the editing string, creates a backup, counts the number of lines in the note, sets the current editing line to the first line, and displays the editing status.
     *
     * @param ch A pointer to the Character object for whom the note editing process is being initialized.
     * @param argument A constant reference to a String object representing any additional arguments passed to the function, though it is not used within this function.
     * @return This function does not return a value.
     */

  0.579  edit_list                                — Formats and displays a specified range of lines from an edit buffer.
    /**
     * @fn static void edit_list(Character *ch, const String &argument)
     *
     * @brief Formats and displays a specified range of lines from an edit buffer.
     *
     * @details The function edit_list processes a command to display lines from an edit buffer associated with a character. It first checks if the numeric arguments are empty. If they are, it defaults to displaying all lines in the buffer. If numeric arguments are present, it uses check_range to validate and adjust the line numbers. If the range is valid, it calls edit_list1 to format and display the specified range of lines.
     *
     * @param ch A pointer to the Character object whose output buffer will receive the formatted lines.
     * @param argument A constant reference to a String object containing the arguments for the edit command.
     * @return This function does not return a value.
     */

  0.572  edit_change                              — Modifies a specific line in a character's edit buffer by replacing a s
    /**
     * @fn static void edit_change(Character *ch, String argument)
     *
     * @brief Modifies a specific line in a character's edit buffer by replacing a substring.
     *
     * @details The function 'edit_change' allows a character to modify a specific line in their edit buffer by replacing a specified substring with another. It first checks if a specific line number is provided and valid, then navigates to that line. It extracts two arguments from the input: the substring to search for and the replacement string. If the replacement string is longer than the original and exceeds the maximum edit length, an error message is sent to the character. The function searches for the substring in the current line, and if found, replaces it with the new string. If the substring is not found, an error message is sent. The function also ensures that changes do not exceed the buffer limits and creates a backup before making modifications.
     *
     * @param ch A pointer to the Character object whose edit buffer is being modified.
     * @param argument A String object containing the arguments for the change operation, including the search and replacement strings.
     * @return This function does not return a value.
     */

  0.569  edit_undo                                — Reverts the most recent change made during character editing.
    /**
     * @fn static void edit_undo(Character *ch, const String &junk)
     *
     * @brief Reverts the most recent change made during character editing.
     *
     * @details This function allows a character to undo their most recent edit action if it has not already been undone. It checks if an undo is permissible, and if so, it restores the editing string from a backup, updates the line count, and adjusts the current editing line if necessary. A message is sent to the character indicating the result of the undo operation.
     *
     * @param ch A pointer to the Character object for whom the undo operation is being performed.
     * @param junk A reference to a String object that is not used in this function.
     * @return This function does not return a value.
     */

  0.564  edit_split                               — Splits the current editing line at a specified token.
    /**
     * @fn static void edit_split(Character *ch, String argument)
     *
     * @brief Splits the current editing line at a specified token.
     *
     * @details The function 'edit_split' takes a character object and a string argument, and attempts to split the current line being edited at the first occurrence of a specified token within the string. If a numeric argument is provided, it checks the validity of the line number and sets it as the current line to edit. If the token is found, the line is split at that point, and the remainder of the line is moved to the next line. If the token is not found, an error message is sent to the character. The function updates the number of lines in the edit buffer after the split.
     *
     * @param ch A pointer to the Character object whose editing line is to be split.
     * @param argument A String object containing the token to split the current line at.
     * @return This function does not return a value.
     */

  0.562  edit_goto                                — Sets the current editing line for a character if the line number is va
    /**
     * @fn static void edit_goto(Character *ch, const String &argument)
     *
     * @brief Sets the current editing line for a character if the line number is valid.
     *
     * @details This function attempts to set the current editing line for a character based on the provided argument. It first checks if the line number, derived from the argument, is within the valid range using the check_line function. If the line number is valid, it proceeds to set the current editing line using the edit_goto1 function.
     *
     * @param ch A pointer to the Character object whose editing line is to be set.
     * @param argument A String object representing the line number to be set as the current editing line.
     * @return This function does not return a value.
     */

  0.561  edit_done                                — Finalizes the editing process for a character.
    /**
     * @fn static void edit_done(Character *ch, const String &argument)
     *
     * @brief Finalizes the editing process for a character.
     *
     * @details This function completes the editing session for a character by saving the edited content based on the type of edit being performed. It handles different edit types such as notes, descriptions, and help text, providing appropriate feedback to the character. If the edit type is unknown or none, it logs a bug and informs the character. For valid edit types, it saves the edited content and provides feedback. The function also cleans up the editing session by deleting the edit object and resetting the character's edit pointer.
     *
     * @param ch A pointer to the Character object that is completing the editing session.
     * @param argument A constant reference to a String object representing additional arguments, though it is not used in this function.
     * @return This function does not return a value.
     */

  0.556  edit_list1                               — Formats and displays a range of lines from an edit buffer to a charact
    /**
     * @fn static void edit_list1(Character *ch, int fromline, int toline)
     *
     * @brief Formats and displays a range of lines from an edit buffer to a character's output.
     *
     * @details The function 'edit_list1' takes a range of line numbers from an edit buffer and formats each line with its line number, appending the result to a string buffer. It then sends the formatted string to a character's output buffer for display. The function ensures that the specified line range is within valid bounds of the edit buffer. If the starting line is zero, it appends an empty line with line number zero before processing the specified range.
     *
     * @param ch A pointer to the Character object whose output buffer will receive the formatted lines.
     * @param fromline The starting line number of the range to be formatted and displayed. It is adjusted to be within valid bounds of the edit buffer.
     * @param toline The ending line number of the range to be formatted and displayed. It is adjusted to be within valid bounds of the edit buffer.
     * @return This function does not return a value.
     */

  0.554  edit_help                                — Initiates the editing of a help entry for a character.
    /**
     * @fn static void edit_help(Character *ch, const String &argument)
     *
     * @brief Initiates the editing of a help entry for a character.
     *
     * @details The function allows a character to begin editing a help entry specified by a numeric ID. If the character is already editing something, it notifies them and displays the current editing status. If the argument is not a valid numeric ID, it prompts the character to specify a valid help ID. Upon successful retrieval of the help entry from the database, it sets up the editing environment, including backing up the current edit string, counting lines, and setting the initial editing line. If the help entry cannot be retrieved, it informs the character of the failure.
     *
     * @param ch A pointer to the Character object who is attempting to edit a help entry.
     * @param argument A constant reference to a String object representing the help ID to be edited.
     * @return This function does not return a value.
     */

  0.547  check_line                               — Checks if a given line number is within the valid range for editing.
    /**
     * @fn static bool check_line(Character *ch, int line)
     *
     * @brief Checks if a given line number is within the valid range for editing.
     *
     * @details This function verifies whether the specified line number is within the valid range of lines that can be edited. If the line number is invalid, it formats an error message indicating the invalid line number and sends it to the specified character. If the line number is valid, the function simply returns true.
     *
     * @param ch A pointer to the Character object that will receive the error message if the line number is invalid.
     * @param line The line number to be checked against the valid range of editable lines.
     * @return Returns true if the line number is within the valid range; otherwise, returns false after sending an error message to the character.
     */

  0.545  edit_cancel                              — Cancels the current editing session for a character.
    /**
     * @fn static void edit_cancel(Character *ch, const String &argument)
     *
     * @brief Cancels the current editing session for a character.
     *
     * @details This function terminates the editing session for the specified character by deleting the current editor object and setting the character's edit pointer to null. It then sends a message to the character indicating that the editing session has been aborted and no changes have been made.
     *
     * @param ch A pointer to the Character object whose editing session is to be canceled.
     * @param argument A reference to a String object, which is not used in this function.
     * @return This function does not return a value.
     */

  0.529  count_lines                              — Counts the number of lines in the current editing string.
    /**
     * @fn int count_lines()
     *
     * @brief Counts the number of lines in the current editing string.
     *
     * @details This function iterates over the lines in the string being edited, counting each line until the end of the string is reached. It uses the 'next_line' function to find the start of each subsequent line. If no editing string is available, it logs a bug and returns zero.
     *
     * @return The number of lines in the current editing string. Returns 0 if there is no string being edited.
     */

  0.525  find_line                                — Finds the starting position of a specified line number in the edit str
    /**
     * @fn static char * find_line(int lineno)
     *
     * @brief Finds the starting position of a specified line number in the edit string.
     *
     * @details This function searches for the starting position of the line specified by 'lineno' in the global edit string 'ed->edit_string'. It returns a pointer to the beginning of the specified line. If 'lineno' is less than 1, it logs a bug and returns the start of the edit string. If 'lineno' is greater than the total number of lines plus one, it logs a bug indicating the line is out of range and returns the start of the edit string. The function uses 'next_line' to traverse lines in the string.
     *
     * @param lineno The line number to find in the edit string. Must be greater than 0 and less than or equal to the total number of lines plus one.
     * @return A pointer to the start of the specified line in the edit string, or the start of the edit string if the line number is out of range.
     */

  0.510  check_range                              — Checks and adjusts the range of line numbers for editing.
    /**
     * @fn static bool check_range(Character *ch, int *fromline, int *toline)
     *
     * @brief Checks and adjusts the range of line numbers for editing.
     *
     * @details This function verifies and sets the range of line numbers for editing based on the presence of numeric arguments. If both ARG_1 and ARG_2 are present, it checks if the specified line numbers are valid and adjusts them if necessary. If only ARG_1 is present, it sets both the start and end line numbers to the specified line. If no numeric arguments are present, it defaults to the current edit line. The function also sends messages to the character if adjustments are made or if the line numbers are out of sequence.
     *
     * @param ch A pointer to the Character object that will receive messages if line numbers are invalid or adjusted.
     * @param fromline A pointer to an integer where the starting line number will be stored.
     * @param toline A pointer to an integer where the ending line number will be stored.
     * @return Returns true if the line numbers are valid and set successfully; otherwise, returns false if the line numbers are invalid or out of sequence.
     */

  0.503  backup                                   — Creates a backup of the current edit string.
    /**
     * @fn static void backup(void)
     *
     * @brief Creates a backup of the current edit string.
     *
     * @details The function 'backup' copies the current content of the edit string into the edit backup buffer and marks the undo operation as permissible. It uses the 'strcpy' function to perform the copy operation from the source string to the destination character array.
     *
     * @return This function does not return a value.
     */

  0.502  edit_delete                              — Deletes a range of lines from the current edit string.
    /**
     * @fn static void edit_delete(Character *ch, const String &argument)
     *
     * @brief Deletes a range of lines from the current edit string.
     *
     * @details This function deletes a specified range of lines from the current edit string associated with a character. It first checks and adjusts the range of line numbers to ensure they are valid. If the starting line is 0, it sends an error message to the character and exits. Otherwise, it finds the starting position of the line to be deleted, creates a backup of the current edit string, and then deletes the lines by shifting the remaining lines up. The number of lines in the edit string is updated, and the current edit line is adjusted accordingly.
     *
     * @param ch A pointer to the Character object that is performing the edit operation.
     * @param argument A reference to a String object containing the command arguments, which may include line numbers to delete.
     * @return This function does not return a value.
     */

  0.339  is_blank_line                            — Checks if a given line is blank.
    /**
     * @fn static bool is_blank_line(char *line)
     *
     * @brief Checks if a given line is blank.
     *
     * @details This function determines whether a given line of text is considered blank. A line is considered blank if it consists solely of whitespace characters or is empty. The function iterates through the characters of the line until it reaches the end of the line or a newline character, returning false if any non-whitespace character is found.
     *
     * @param line A pointer to a null-terminated string representing the line to be checked.
     * @return Returns true if the line is blank or consists only of whitespace characters; otherwise, returns false.
     */


================================================================================
[policy] attributes  (stability: stable)
  desc: Character stat access and derived computation: armor class calculation (base, modified, unspelled), hitroll and damroll …
  locked: 45 functions, 45 with embeddings
  sim to desc — mean: 0.556  min: 0.414  max: 0.732

  0.732  get_max_stat                             — Retrieves the maximum allowable stat value for a character.
    /**
     * @fn int get_max_stat(const Character *ch, int stat)
     *
     * @brief Retrieves the maximum allowable stat value for a character.
     *
     * @details Calculates the maximum stat value for a given character and stat.
    This function calculates the maximum stat value a character can have based on several factors, including whether the character is an NPC, their race, guild affiliation, and any bonuses from familiars. For NPCs, the maximum is determined by the base attribute plus a fixed bonus. For player characters, the maximum is influenced by race-specific maximums, guild bonuses, and additional bonuses if the character has a familiar. Human characters receive an additional bonus to their maximum stat.
     *
     * @param ch A pointer to the Character object for which the maximum stat is being calculated.
     * @param stat An integer representing the stat identifier for which the maximum value is being determined.
     * @return The maximum possible value for the specified stat, constrained between 3 and 25.
     */

  0.670  GET_ATTR_AC                              — Calculates the armor class attribute for a character.
    /**
     * @fn int GET_ATTR_AC(Character *ch)
     *
     * @brief Calculates the armor class attribute for a character.
     *
     * @details This function computes the armor class (AC) attribute for a given character. The base AC is determined by the character's current attributes and is modified based on their state and specific conditions. If the character is awake, their dexterity defensive bonus is added. For non-player characters with remort levels, the AC is reduced based on their remort count and level. Additionally, if the character is a non-player character and has a paladin grace attribute of 3 or more, the AC is increased by 20%.
     *
     * @param ch A pointer to the Character object for which the armor class is being calculated.
     * @return The calculated armor class value for the character, which is an integer representing their defensive capability.
     */

  0.665  GET_AC                                   — Calculates the total armor class for a character based on type.
    /**
     * @fn int GET_AC(Character *ch, int type)
     *
     * @brief Calculates the total armor class for a character based on type.
     *
     * @details This function computes the total armor class for a given character by adding the base armor class of a specified type to the character's calculated armor class attribute. It is used to determine the character's defensive capability against attacks.
     *
     * @param ch A pointer to the Character object for which the armor class is being calculated.
     * @param type An integer representing the type of armor class to be considered from the character's base armor class array.
     * @return The total armor class value for the character, which is an integer representing their overall defensive capability.
     */

  0.661  get_unspelled_damroll                    — Calculates the unspelled damage roll of a character.
    /**
     * @fn int get_unspelled_damroll(Character *ch)
     *
     * @brief Calculates the unspelled damage roll of a character.
     *
     * @details Calculates the unspelled damage roll for a character.
    This function computes the unspelled damage roll for a given character by subtracting any spell-induced modifications from the character's base damage roll attribute. It iterates over all objects carried by the character that are currently worn, and for each object, it checks for affects that modify the damage roll. These affects are added to the sum to account for non-spell-related modifications.
     *
     * @param ch A pointer to the Character whose unspelled damage roll is to be calculated.
     * @return The total unspelled damage roll for the character, which includes base damage roll and modifiers from equipped objects, excluding spell effects.
     */

  0.661  GET_ATTR_HITROLL                        
    /**
     * @def GET_ATTR_HITROLL
     *
     */

  0.659  get_unspelled_hitroll                    — Calculates a character's hitroll excluding spell effects.
    /**
     * @fn int get_unspelled_hitroll(Character *ch)
     *
     * @brief Calculates a character's hitroll excluding spell effects.
     *
     * @details Calculates the unspelled hitroll value for a character.
    This function computes the hitroll value for a given character by considering only their inherent attributes and equipped items, excluding any spell effects. It iterates over the character's carried objects, checking for equipped items that contribute to the hitroll through their affects. This is particularly useful for determining adjustments for abilities like hammerstrike and berserk, which rely on non-spell-based hitroll values.
     *
     * @param ch A pointer to the Character whose unspelled hitroll is to be calculated.
     * @return The unspelled hitroll value, which is the character's base hitroll adjusted for any non-spell-related modifiers from worn objects.
     */

  0.656  get_unspelled_ac                         — Calculates the unmodified armor class (AC) of a character based on wor
    /**
     * @fn int get_unspelled_ac(Character *ch, int type)
     *
     * @brief Calculates the unmodified armor class (AC) of a character based on worn armor.
     *
     * @details Calculates the unmodified armor class (AC) for a character.
    This function computes the armor class (AC) of a character by summing the AC contributions of all worn armor items. It does not consider any modifications from dexterity or spells. The function iterates over all possible wear locations, retrieves the object worn at each location, and applies the AC value of the object to the total AC if the object is present.
     *
     * @param ch A pointer to the Character whose unmodified AC is being calculated.
     * @param type An integer index used to specify which AC value to access from each object's value array.
     * @return The calculated unmodified AC value for the character, starting from a base of 100 and reduced by the AC contributions of worn objects.
     */

  0.655  get_max_train                            — Calculates the maximum trainable value for a given character's statist
    /**
     * @fn int get_max_train(Character *ch, int stat)
     *
     * @brief Calculates the maximum trainable value for a given character's statistic.
     *
     * @details Calculates the maximum training score for a character's stat.
    This function determines the maximum value to which a character can train a specific statistic. If the character is a non-player character (NPC) or an immortal, the maximum is set to 25. For player characters, the maximum is determined based on the character's race and guild. If the character's guild has a prime statistic that matches the given statistic, the maximum is increased by 2, or by 3 if the character is human. The final maximum value is capped at 25.
     *
     * @param ch A pointer to the Character object for which the maximum training score is being calculated.
     * @param stat The specific stat index for which the maximum training score is being determined.
     * @return The maximum training score for the specified stat, capped at 25.
     */

  0.644  GET_ATTR_DAMROLL                        
    /**
     * @def GET_ATTR_DAMROLL
     *
     */

  0.627  stam_gain                                — Calculates the stamina gain for a character based on various condition
    /**
     * @fn int stam_gain(Character *ch)
     *
     * @brief Calculates the stamina gain for a character based on various conditions.
     *
     * @details The function computes the amount of stamina a character gains over time, taking into account whether the character is an NPC or a player, their current position, room healing rate, and various affects such as poison or regeneration. The gain is adjusted based on the character's attributes, guild, and conditions like hunger and thirst. The final stamina gain is constrained by the character's maximum stamina.
     *
     * @param ch A pointer to the Character object for which the stamina gain is being calculated.
     * @return The function returns an integer representing the calculated stamina gain for the character, capped by the character's maximum stamina.
     */

  0.616  can_carry_w                              — Calculates the maximum weight a character can carry.
    /**
     * @fn int can_carry_w(Character *ch)
     *
     * @brief Calculates the maximum weight a character can carry.
     *
     * @details This function determines the carrying capacity of a character based on their attributes and status. If the character is immortal, it returns a very high carrying capacity. If the character is a non-player character (NPC) and is flagged as a pet, it returns zero, indicating that pets cannot carry items. For other characters, it calculates the carrying capacity based on the character's strength attribute and level.
     *
     * @param ch A pointer to the Character object for which the carry capacity is being calculated.
     * @return An integer representing the maximum weight the character can carry. This value is influenced by the character's immortality status, NPC status, pet flag, strength attribute, and level.
     */

  0.612  GET_MAX_STAM                             — Calculates the maximum stamina for a character.
    /**
     * @fn int GET_MAX_STAM(Character *ch)
     *
     * @brief Calculates the maximum stamina for a character.
     *
     * @details This function computes the maximum stamina value for a given character based on their stamina attribute. It ensures that the stamina value is within the bounds of 1 and 30000. If the stamina attribute is less than 1, the function returns 1. If it exceeds 30000, it returns 30000. Otherwise, it returns the base stamina attribute value.
     *
     * @param ch A pointer to the Character object for which the maximum stamina is being calculated.
     * @return The maximum stamina value for the character, constrained between 1 and 30000.
     */

  0.611  GET_MAX_HIT                              — Calculates the maximum hit points for a character.
    /**
     * @fn int GET_MAX_HIT(Character *ch)
     *
     * @brief Calculates the maximum hit points for a character.
     *
     * @details This function computes the maximum hit points (HP) for a given character based on their attributes. It ensures that the HP is within a valid range, applying specific rules such as a minimum of 1 HP and a maximum of 30000 HP. If the character has a paladin grace level of 4 or higher, a 20% bonus is applied to the base HP, capped at 30000.
     *
     * @param ch A pointer to the Character object whose maximum hit points are being calculated.
     * @return The maximum hit points for the character, adjusted according to their attributes and specific rules.
     */

  0.608  get_age                                  — Calculates the age of a character in MUD years.
    /**
     * @fn int get_age(Character *ch)
     *
     * @brief Calculates the age of a character in MUD years.
     *
     * @details Calculates the age of a character in the game.
    This function computes the age of a character in the game world, expressed in MUD years. The base age is determined by the character's race if the character is a player character (PC). The function then adds additional age based on the character's playing time and any age modifiers. The conversion from playing time to MUD years is based on a predefined time scale where 178.5 hours equates to one MUD year.
     *
     * @param ch A pointer to the Character object whose age is to be calculated.
     * @return The calculated age of the character as an integer.
     */

  0.608  can_carry_n                              — Calculates the maximum number of items a character can carry.
    /**
     * @fn int can_carry_n(Character *ch)
     *
     * @brief Calculates the maximum number of items a character can carry.
     *
     * @details This function determines the carrying capacity of a character based on their attributes and status. If the character is an immortal, it returns a large constant value, allowing them to carry an unlimited number of items. If the character is a non-player character (NPC) and is flagged as a pet, it returns zero, indicating that pets cannot carry items. For all other characters, the carrying capacity is calculated based on the character's dexterity attribute and level, in addition to a base value.
     *
     * @param ch A pointer to the Character object whose carry capacity is being calculated.
     * @return An integer representing the maximum number of items the character can carry.
     */

  0.602  hit_gain                                 — Calculates the hit point regeneration gain for a character.
    /**
     * @fn int hit_gain(Character *ch)
     *
     * @brief Calculates the hit point regeneration gain for a character.
     *
     * @details This function determines the amount of hit points a character regenerates over time based on various conditions such as whether the character is an NPC, their current position, and any active affects. The gain is adjusted by the room's healing rate and other factors like hunger, thirst, and specific affects. The function ensures that the gain does not exceed the character's maximum hit points.
     *
     * @param ch A pointer to the Character object for which the hit point gain is being calculated.
     * @return The calculated hit point gain for the character, adjusted for various conditions and bounded by the character's maximum hit points.
     */

  0.595  GET_DEFENSE_MOD                         
    /**
     * @def GET_DEFENSE_MOD
     *
     */

  0.593  apply_ac                                 — Calculates the armor class contribution of an object based on its wear
    /**
     * @fn int apply_ac(Object *obj, int iWear, int type)
     *
     * @brief Calculates the armor class contribution of an object based on its wear location.
     *
     * @details Calculates the armor class (AC) value of an object based on its wear position.
    This function determines the armor class (AC) contribution of an object when worn at a specific location on a character. It checks if the object is of type ITEM_ARMOR and returns the appropriate AC value based on the wear location specified by iWear. The type parameter is used to index into the object's value array to retrieve the base AC value, which is then adjusted according to the wear location.
     *
     * @param obj A pointer to the Object whose AC value is to be calculated.
     * @param iWear An integer representing the position where the object is worn, such as WEAR_BODY or WEAR_HEAD.
     * @param type An integer index used to access the specific AC value from the object's value array.
     * @return The calculated AC value for the object at the specified wear position. Returns 0 if the object is not of type ITEM_ARMOR or if the wear position does not modify the AC value.
     */

  0.583  GET_MAX_MANA                             — Calculates the maximum mana for a character.
    /**
     * @fn int GET_MAX_MANA(Character *ch)
     *
     * @brief Calculates the maximum mana for a character.
     *
     * @details This function determines the maximum mana a character can have based on their mana attribute. It ensures that the mana value is at least 1 and does not exceed 30000. If the character's mana attribute is less than 1, the function returns 1. If the mana attribute exceeds 30000, it returns 30000. Otherwise, it returns the base mana attribute value.
     *
     * @param ch A pointer to the Character object whose maximum mana is being calculated.
     * @return The maximum mana value for the character, constrained between 1 and 30000.
     */

  0.583  mana_gain                                — Calculates the mana gain for a character based on various conditions.
    /**
     * @fn int mana_gain(Character *ch)
     *
     * @brief Calculates the mana gain for a character based on various conditions.
     *
     * @details This function computes the amount of mana a character gains over time, taking into account whether the character is an NPC or a player, their current position, skill levels, and various conditions affecting them. The mana gain is influenced by the character's attributes, skill in meditation, guild-specific mana regeneration rates, and conditions such as hunger, thirst, and various affects like poison or divine regeneration. The final mana gain is adjusted by the room's mana regeneration rate and any furniture the character might be using.
     *
     * @param ch A pointer to the Character object for which the mana gain is being calculated.
     * @return The function returns an integer representing the calculated mana gain for the character, constrained by the character's maximum mana and adjusted for various conditions and attributes.
     */

  0.576  print_defense_modifiers                  — Generates a string describing a character's defense modifiers based on
    /**
     * @fn String print_defense_modifiers(Character *ch, int where)
     *
     * @brief Generates a string describing a character's defense modifiers based on a specified category.
     *
     * @details Generates a string describing the character's defense modifiers based on the specified category.
    This function examines a character's defense modifiers and constructs a string that lists the applicable modifiers for a given category, such as absorption, immunity, resistance, or vulnerability. It iterates over possible damage types and checks if the character's defense modifier for each type meets the criteria for the specified category. If so, it appends the damage type name and the modifier percentage to the result string. The function handles different categories by adjusting the criteria for inclusion and the format of the modifier percentage.
     *
     * @param ch A pointer to the Character object whose defense modifiers are being evaluated.
     * @param where An integer specifying the category of defense modifiers to consider, such as absorption, immunity, resistance, or vulnerability.
     * @return A String object containing a space-separated list of damage types and their corresponding modifier percentages for the specified category, or an empty string if no relevant modifiers are found.
     */

  0.569  get_carry_weight                         — Calculates the total carrying weight of a character.
    /**
     * @fn int get_carry_weight(Character *ch)
     *
     * @brief Calculates the total carrying weight of a character.
     *
     * @details This function computes the total weight that a character is carrying by summing the weights of all objects in their possession, including the weight of gold and silver. It iterates through each object the character is carrying, using the get_obj_weight function to determine the weight of each object, and adds the weight of the character's gold and silver. The result is clamped between 0 and 9999 to prevent overflow or negative values.
     *
     * @param ch A pointer to the Character whose carrying weight is to be calculated.
     * @return The total carrying weight of the character, adjusted to be within the range of 0 to 9999.
     */

  0.567  get_play_seconds                         — Calculates the total play time in seconds for a character.
    /**
     * @fn int get_play_seconds(Character *ch)
     *
     * @brief Calculates the total play time in seconds for a character.
     *
     * @details Retrieves the playing time of a character in seconds.
    This function determines the total play time in seconds for a given character. If the character is a non-player character (NPC), the function returns 0, as NPCs do not have play time data. For player characters, it returns the value stored in the 'played' field of the character's 'pcdata' structure.
     *
     * @param ch A pointer to the Character object whose playing time is to be retrieved.
     * @return The playing time of the character in seconds. Returns 0 if the character is an NPC.
     */

  0.567  stat_to_attr                             — Converts a stat identifier to its corresponding attribute identifier.
    /**
     * @fn int stat_to_attr(int stat)
     *
     * @brief Converts a stat identifier to its corresponding attribute identifier.
     *
     * @details This function maps a given stat identifier to its corresponding attribute identifier. The mapping is based on predefined constants for stats and attributes. Stats are expected to be in the range of 0-5, while attributes correspond to specific apply flags that range from 1-5 and 26. If an invalid stat is provided, a bug log is generated, and a default attribute is returned.
     *
     * @param stat An integer representing the stat identifier to be converted.
     * @return An integer representing the corresponding attribute identifier. Defaults to APPLY_STR if the stat identifier is invalid.
     */

  0.540  get_play_hours                           — Calculates the total play hours for a character.
    /**
     * @fn int get_play_hours(Character *ch)
     *
     * @brief Calculates the total play hours for a character.
     *
     * @details Retrieves the playing time of a character in hours.
    This function computes the total number of hours a character has played. If the character is a non-player character (NPC), it returns 0, as NPCs do not have playtime data. For player characters, it divides the total playtime in seconds by 3600 to convert it to hours.
     *
     * @param ch A pointer to the Character object whose playing time is to be retrieved.
     * @return The playing time of the character in hours. Returns 0 if the character is an NPC.
     */

  0.539  IS_OBJ_STAT                             
    /**
     * @def IS_OBJ_STAT
     *
     */

  0.534  deduct_stamina                           — Deducts stamina from a character for using a specified skill.
    /**
     * @fn bool deduct_stamina(Character *ch, skill::type type)
     *
     * @brief Deducts stamina from a character for using a specified skill.
     *
     * @details Deducts stamina from a character for using a skill.
    This function checks if a character has enough stamina to use a specified skill and deducts the appropriate amount of stamina if possible. It first verifies if the skill is a spell by checking if its associated function is not 'spell_null'. If the skill requires no mana, it returns true immediately. The function calculates the stamina cost using 'get_skill_cost' and applies any relevant reductions based on character attributes or equipment bonuses. If the character's current stamina is less than the calculated cost, a message is sent to the character indicating they are too tired, and the function returns false. Otherwise, the stamina is deducted, and the function returns true.
     *
     * @param ch A pointer to the Character object whose stamina is being checked and potentially deducted.
     * @param type The skill::type enumeration value representing the skill for which stamina is being deducted.
     * @return Returns true if the character has enough stamina and the cost is successfully deducted; otherwise, returns false.
     */

  0.531  GET_ATTR_WIS                            
    /**
     * @def GET_ATTR_WIS
     *
     */

  0.527  get_locker_weight                        — Calculates the total weight of items in a character's locker.
    /**
     * @fn int get_locker_weight(Character *ch)
     *
     * @brief Calculates the total weight of items in a character's locker.
     *
     * @details This function computes the total weight of all objects stored in a character's locker. It first checks if the character is a non-player character (NPC) by using the Character::is_npc method. If the character is an NPC, the function returns 0, as NPCs do not have lockers. For player characters, it iterates over each object in the locker, using the get_obj_weight function to calculate the weight of each object, including its contents, and sums these weights to determine the total locker weight.
     *
     * @param ch A pointer to the Character whose locker weight is to be calculated.
     * @return The total weight of all objects in the character's locker. Returns 0 if the character is an NPC.
     */

  0.523  get_carry_number                         — Calculates the total number of objects a character is carrying.
    /**
     * @fn int get_carry_number(Character *ch)
     *
     * @brief Calculates the total number of objects a character is carrying.
     *
     * @details This function iterates over all objects that a character is carrying and calculates the total number of contained objects by summing up the number of objects within each carried object. It utilizes the get_obj_number function to determine the number of objects contained within each individual object.
     *
     * @param ch A pointer to the Character whose carried objects are to be counted.
     * @return The total number of objects carried by the character, including all objects contained within the carried objects.
     */

  0.516  GET_ATTR_SEX                            
    /**
     * @def GET_ATTR_SEX
     *
     */

  0.508  GET_ATTR_AGE                            
    /**
     * @def GET_ATTR_AGE
     *
     */

  0.506  GET_ATTR_CHR                            
    /**
     * @def GET_ATTR_CHR
     *
     */

  0.504  GET_ATTR_SAVES                          
    /**
     * @def GET_ATTR_SAVES
     *
     */

  0.487  level_save                               — Determines if a saving throw is successful based on level difference.
    /**
     * @fn bool level_save(int dis_level, int save_level)
     *
     * @brief Determines if a saving throw is successful based on level difference.
     *
     * @details Determines if a level-based saving throw is successful.
    This function calculates a saving throw chance based on the difference between a character's saving level and the difficulty level. It computes a save percentage, ensuring it is within the range of 5 to 95, and then uses this percentage to determine if the saving throw is successful by calling roll_chance.
     *
     * @param dis_level The difficulty level of the challenge.
     * @param save_level The saving level of the entity attempting the save.
     * @return Returns true if the saving throw is successful, indicating the entity overcomes the challenge; otherwise, returns false.
     */

  0.480  GET_RANK                                
    /**
     * @def GET_RANK
     *
     */

  0.479  GET_ATTR_MOD                            
    /**
     * @def GET_ATTR_MOD
     *
     */

  0.463  GET_ATTR_DEX                            
    /**
     * @def GET_ATTR_DEX
     *
     */

  0.435  ATTR_BASE                               
    /**
     * @def ATTR_BASE
     *
     */

  0.434  GET_ATTR                                
    /**
     * @def GET_ATTR
     *
     */

  0.428  WEIGHT_MULT                             
    /**
     * @def WEIGHT_MULT
     *
     */

  0.428  GET_ATTR_CON                            
    /**
     * @def GET_ATTR_CON
     *
     */

  0.426  set_title                                — Sets the title of a character.
    /**
     * @fn void set_title(Character *ch, const String &title)
     *
     * @brief Sets the title of a character.
     *
     * @details This function assigns a new title to a character, ensuring that the title is properly formatted. If the character is a non-player character (NPC), the function logs a bug and exits without setting a title. For player characters, if the title does not start with a punctuation mark ('.', ',', '!', or '?'), a space is prepended to the title before assignment. The title is then copied to the character's title field.
     *
     * @param ch A pointer to the Character object whose title is to be set.
     * @param title A reference to the String object containing the new title to be assigned to the character.
     * @return This function does not return a value.
     */

  0.414  GET_ATTR_INT                            
    /**
     * @def GET_ATTR_INT
     *
     */

  0.414  GET_ATTR_STR                            
    /**
     * @def GET_ATTR_STR
     *
     */


================================================================================
[policy] entity_lookup  (stability: stable)
  desc: In-game entity resolution: finding characters, NPCs, objects, and players by name within various scopes (room, area, wor…
  locked: 34 functions, 34 with embeddings
  sim to desc — mean: 0.562  min: 0.433  max: 0.684

  0.684  get_mob_world                            — Finds a mobile (NPC) character in the world based on search criteria.
    /**
     * @fn Character * get_mob_world(Character *ch, const String &argument, int vis)
     *
     * @brief Finds a mobile (NPC) character in the world based on search criteria.
     *
     * @details Finds a mobile (NPC) in the game world based on search criteria.
    This function searches for a non-player character (NPC) within the game world that matches the specified search criteria. It first attempts to find the NPC in the same room as the character 'ch' using the 'get_mob_here' function. If not found, it searches the entire world. The search criteria can include an entity type, a numeric prefix, or a specific name. The function also considers visibility conditions specified by 'vis' to determine if the character 'ch' can see the NPC.
     *
     * @param ch A pointer to the Character object representing the character performing the search.
     * @param argument A String object containing the search criteria, which may include an entity type, a numeric prefix, or a specific name.
     * @param vis An integer representing the visibility condition to apply when determining if the character 'ch' can see the NPC.
     * @return A pointer to the Character object representing the found NPC if it matches the search criteria and visibility conditions; otherwise, returns null.
     */

  0.664  get_char_world                           — Finds a character in the game world based on search criteria.
    /**
     * @fn Character * get_char_world(Character *ch, const String &argument, int vis)
     *
     * @brief Finds a character in the game world based on search criteria.
     *
     * @details Finds a character in the world based on search criteria.
    This function searches for a character in the game world that matches the specified search criteria. It first attempts to find the character in the same room as the specified character. If not found, it searches the entire world. The search can be restricted to only non-player characters (NPCs) or only players, based on the visibility constraints provided. The search criteria can include an entity type, a character name, or a numeric prefix. The function returns the first matching character that meets the criteria and visibility constraints.
     *
     * @param ch A pointer to the Character object from whose perspective the search is conducted.
     * @param argument A String object containing the search criteria, which may include an entity type or character name.
     * @param vis An integer flag indicating the visibility constraints to apply during the search (e.g., VIS_PLR for players, VIS_CHAR for characters).
     * @return A pointer to the Character object that matches the search criteria, or nullptr if no matching character is found.
     */

  0.659  get_mob_here                             — Finds a mobile (NPC) in the same room as the specified character.
    /**
     * @fn Character * get_mob_here(Character *ch, const String &argument, int vis)
     *
     * @brief Finds a mobile (NPC) in the same room as the specified character.
     *
     * @details Finds a non-player character (NPC) in the same room as the given character.
    This function searches for a non-player character (NPC) within the same room as the given character 'ch'. It processes the input 'argument' to determine the type of entity to search for and any specific criteria such as a numeric prefix or exact name matching. The function checks visibility conditions based on the 'vis' parameter to determine if the character 'ch' can see the NPC. If the specified NPC is found according to the criteria, it is returned; otherwise, the function returns null.
     *
     * @param ch A pointer to the Character object representing the character searching for the NPC.
     * @param argument A String object containing the search criteria, which may include a numeric prefix, entity type, or specific name.
     * @param vis An integer representing the visibility condition to apply when determining if 'ch' can see the NPC.
     * @return A pointer to the Character object representing the found NPC, or nullptr if no matching NPC is found.
     */

  0.649  get_obj_here                             — Finds an object in the room or in the character's possession.
    /**
     * @fn Object * get_obj_here(Character *ch, const String &argument)
     *
     * @brief Finds an object in the room or in the character's possession.
     *
     * @details Finds an object that is present in the character's current environment.
    This function searches for an object that matches the given argument, first checking the objects in the room, then the character's inventory, and finally the objects worn by the character. It returns the first object that matches the search criteria and is accessible to the character.
     *
     * @param ch A pointer to the Character object whose environment is being searched for the object.
     * @param argument A String containing the search criteria, which may include a numeric prefix to specify which occurrence of the object to find.
     * @return A pointer to the Object that matches the search criteria and is found in the character's current room, inventory, or worn items, or nullptr if no such object is found.
     */

  0.639  get_player_world                         — Finds a player character in the game world based on a given name.
    /**
     * @fn Character * get_player_world(Character *ch, const String &argument, int vis)
     *
     * @brief Finds a player character in the game world based on a given name.
     *
     * @details Finds a player character in the game world based on a given name or keyword.
    This function searches for a player character in the game world whose name matches the given argument. It does not support numbered player names (e.g., '2.Elrac'). If the argument is 'self', it returns the character passed as the first parameter. The function also considers visibility constraints based on the 'vis' parameter, which determines whether the search should respect character visibility rules.
     *
     * @param ch A pointer to the Character object that is searching for another player.
     * @param argument A String representing the name or keyword to search for in the game world.
     * @param vis An integer representing the visibility level used to determine if 'ch' can see other characters.
     * @return A pointer to the Character object that matches the search criteria, or nullptr if no match is found.
     */

  0.635  get_char_here                            — Finds a character in the same room as the specified character.
    /**
     * @fn Character * get_char_here(Character *ch, const String &argument, int vis)
     *
     * @brief Finds a character in the same room as the specified character.
     *
     * @details Finds a character in the same room as the specified character based on search criteria.
    This function searches for a character in the same room as the given character 'ch'. It can filter the search based on whether the target is a mobile or a player, and can also consider visibility constraints. The search is conducted using the provided 'argument', which can specify an entity type or a specific character name. The function supports searching for a specific instance of a character if multiple instances are present, using a numeric prefix in the argument.
     *
     * @param ch A pointer to the Character object that is performing the search.
     * @param argument A String containing the search criteria, which may include an entity type and a numeric prefix.
     * @param vis An integer specifying the visibility condition to apply when searching for the character.
     * @return A pointer to the Character object that matches the search criteria and visibility conditions, or null if no such character is found.
     */

  0.633  get_obj_world                            — Finds an object in the game world accessible to a character.
    /**
     * @fn Object * get_obj_world(Character *ch, const String &argument)
     *
     * @brief Finds an object in the game world accessible to a character.
     *
     * @details This function searches for an object that a character can access, either in their current location or globally within the game world. It first attempts to locate the object in the character's immediate vicinity using the provided search criteria. If not found locally, it searches through the global list of objects in the game world. The search criteria may include a numeric prefix to specify a particular occurrence of the object. The function returns the object if found and accessible, or nullptr if no matching object is found.
     *
     * @param ch A pointer to the Character who is attempting to find the object.
     * @param argument A String containing the search criteria, which may include a numeric prefix to specify a particular occurrence of the object.
     * @return A pointer to the Object that matches the search criteria and is accessible to the character, or nullptr if no such object is found.
     */

  0.628  get_warp_crystal                         — Searches for an exact match of a warp crystal by its description.
    /**
     * @fn const Object * get_warp_crystal(const String &str)
     *
     * @brief Searches for an exact match of a warp crystal by its description.
     *
     * @details Finds a warp crystal object matching the given string.
    This function iterates through the list of objects in the game world, searching for an object whose warp location description matches the provided string. The comparison is performed after removing any color codes from both the object's description and the input string. If a match is found, the function returns a pointer to the corresponding object. If no match is found, it returns a null pointer.
     *
     * @param str A String object representing the warp location description to match against objects in the game world.
     * @return A pointer to the Object whose warp location description matches the provided string, or nullptr if no such object is found.
     */

  0.624  get_obj_list                             — Finds an object in a list that a character can see and matches a given
    /**
     * @fn Object * get_obj_list(Character *ch, const String &argument, Object *list)
     *
     * @brief Finds an object in a list that a character can see and matches a given argument.
     *
     * @details Retrieves a specific object from a list that a character can see.
    This function searches through a linked list of objects to find an object that a character can see and whose name matches a specified argument. The argument may include a numeric prefix to specify which occurrence of the matching object to find. The function uses case-insensitive word matching to determine if the object's name contains the words specified in the argument. If the character can see the object and the object's name matches the argument, the function returns the nth occurrence of such an object, where n is specified by the numeric prefix in the argument.
     *
     * @param ch A pointer to the Character object whose perspective is used to determine visibility of objects.
     * @param argument A String object containing the search criteria, possibly including a numeric prefix to specify which occurrence to find.
     * @param list A pointer to the first Object in a linked list of objects to search through.
     * @return A pointer to the Object that matches the search criteria and is visible to the character, or nullptr if no such object is found.
     */

  0.619  get_char_area                            — Finds a character in the same area as the specified character.
    /**
     * @fn Character * get_char_area(Character *ch, const String &argument, int vis)
     *
     * @brief Finds a character in the same area as the specified character.
     *
     * @details Finds a character in the same area as the specified character based on search criteria.
    This function searches for a character within the same area as the given character 'ch'. It first attempts to find the character in the same room using 'get_char_here'. If not found, it iterates over all characters in the game world, checking if they are in the same area as 'ch' and match the search criteria specified by 'argument'. The search can be restricted to visible players or characters based on the 'vis' parameter. The function supports searching by entity type and ensures the character's name contains the specified words. It returns the first matching character based on the specified numeric prefix or the first match if no prefix is provided.
     *
     * @param ch A pointer to the Character object initiating the search.
     * @param argument A String object containing the search criteria, including an entity type and name pattern.
     * @param vis An integer flag indicating the visibility constraints to apply during the search.
     * @return A pointer to the Character object that matches the search criteria within the same area, or nullptr if no matching character is found.
     */

  0.611  find_location                            — Finds and returns the Room associated with a given location, character
    /**
     * @fn Room * find_location(Character *ch, const String &arg)
     *
     * @brief Finds and returns the Room associated with a given location, character, or object in the game world.
     *
     * @details Locates and returns the Room associated with a given location, character, or object.
    This function attempts to locate a Room object based on the provided argument. It first interprets the argument as a Location and retrieves the corresponding Room. If unsuccessful, it searches for a character matching the argument within the game world; if found, it returns the Room where that character is located. If still not found, it searches for an object matching the argument accessible to the character 'ch'; if found, it returns the Room containing that object. If none of these searches succeed, it returns nullptr, indicating that the location could not be determined.
     *
     * @param ch Pointer to the Character initiating the search, used for context in object and character searches.
     * @param arg String representing the location, character name, or object identifier to locate.
     * @return Pointer to the Room object corresponding to the specified location, character, or object; nullptr if no matching Room is found.
     */

  0.604  get_char_room                            — Searches for a character in a specified room based on various criteria
    /**
     * @fn Character * get_char_room(Character *ch, Room *room, const String &argument, int vis)
     *
     * @brief Searches for a character in a specified room based on various criteria and visibility conditions.
     *
     * @details Retrieves a character from a specified room based on given criteria and visibility conditions.
    This function searches through the list of characters present in the given room to find a character that matches the specified argument and visibility conditions. It considers entity type (such as NPC or specific vnum), name matching, and whether the character is the 'self' character. The search respects visibility constraints determined by 'can_see_char' and 'can_see_who' functions based on the 'vis' parameter. It returns the character that matches the criteria at the specified occurrence number, or nullptr if no match is found.
     *
     * @param ch The character attempting to find another character in the room.
     * @param room The room in which to search for the character.
     * @param argument A string specifying the target character, possibly including entity type, name, and number.
     * @param vis An integer flag indicating the visibility context (e.g., player or character visibility).
     * @return A pointer to the Character object that matches the search criteria and visibility conditions, or nullptr if no such character is found.
     */

  0.593  random_prototype                         — Selects a random object prototype VNUM based on a keyword.
    /**
     * @fn int random_prototype(String key)
     *
     * @brief Selects a random object prototype VNUM based on a keyword.
     *
     * @details This function searches through all object prototypes in the game world to find those whose names contain the specified keyword. It performs two passes: the first pass counts all eligible prototypes, and the second pass selects one at random from the counted prototypes and returns its VNUM. If no prototypes match the keyword, the function returns 0.
     *
     * @param key A String object representing the keyword to search for in object prototype names.
     * @return The VNUM of a randomly selected object prototype whose name contains the specified keyword, or 0 if no such prototype exists.
     */

  0.587  fsearch_char                             — Searches for characters or NPCs with specific flags and outputs the re
    /**
     * @fn void fsearch_char(Character *ch, int fieldptr, const Flags &marked, bool mobile, bool player)
     *
     * @brief Searches for characters or NPCs with specific flags and outputs the results to a character.
     *
     * @details The function fsearch_char performs a search for either players or NPCs (or both) in the game world that match a given set of flags. It utilizes the fsearch_mobile function to search for NPCs and the fsearch_player function to search for players. The results of these searches are formatted into a string and sent to the specified character's output buffer. If the number of matches exceeds 500, only 500 are shown. The function provides feedback on the number of matches found or indicates if no matches were found.
     *
     * @param ch A pointer to the Character object that will receive the search results.
     * @param fieldptr An integer representing the specific field of flags to check against the 'marked' flags.
     * @param marked A Flags object containing the flags to be checked against each character's or NPC's flags.
     * @param mobile A boolean indicating whether to search for NPCs.
     * @param player A boolean indicating whether to search for players.
     * @return This function does not return a value.
     */

  0.578  name_expand                              — Expands a character's name to uniquely identify them within a room.
    /**
     * @fn const String name_expand(Character *ch)
     *
     * @brief Expands a character's name to uniquely identify them within a room.
     *
     * @details This function generates a unique identifier for a character within their current room by expanding their name. If the character is a non-player character (NPC), it counts how many characters with the same name exist in the room and appends this count as a prefix to the name. This helps in distinguishing between multiple characters with the same name, such as guards or other NPCs. If the character is a player character (PC), their full name is returned as is.
     *
     * @param ch A pointer to the Character object whose name is to be expanded.
     * @return A String object representing the expanded name of the character, which includes a count prefix if necessary to ensure uniqueness within the room.
     */

  0.578  get_obj_wear                             — Finds an object worn by the player based on a given argument.
    /**
     * @fn Object * get_obj_wear(Character *ch, const String &argument)
     *
     * @brief Finds an object worn by the player based on a given argument.
     *
     * @details Retrieves an object worn by a character based on a specified argument.
    This function searches through the equipment worn by a character to find an object that matches the specified argument. The search considers objects that are visible to the character and checks if the object's name contains the words specified in the argument. The function supports finding a specific occurrence of such objects by using a numeric prefix in the argument.
     *
     * @param ch A pointer to the Character object whose worn items are being searched.
     * @param argument A String object containing the search criteria, which may include a numeric prefix to specify a particular instance of matching objects.
     * @return A pointer to the Object that matches the search criteria and is worn by the character, or nullptr if no such object is found.
     */

  0.577  get_obj_carry                            — Finds an object in a character's inventory based on a given argument.
    /**
     * @fn Object * get_obj_carry(Character *ch, const String &argument)
     *
     * @brief Finds an object in a character's inventory based on a given argument.
     *
     * @details Retrieves an object carried by a character based on a given argument.
    This function searches through the inventory of a character to find an object that matches the specified argument. The argument can include a numeric prefix to specify which occurrence of the object to find. The function checks if the object is not worn, is visible to the character, and matches the name criteria specified in the argument. If the object is found, it is returned; otherwise, the function returns null.
     *
     * @param ch A pointer to the Character whose carried objects are being searched.
     * @param argument A String containing the search criteria, including an optional numeric prefix and the name of the object.
     * @return A pointer to the Object that matches the search criteria, or nullptr if no such object is found.
     */

  0.568  get_obj_keeper                           — Retrieve an object from a shopkeeper's inventory based on a character'
    /**
     * @fn Object * get_obj_keeper(Character *ch, Character *keeper, const String &argument)
     *
     * @brief Retrieve an object from a shopkeeper's inventory based on a character's request.
     *
     * @details This function searches through a shopkeeper's inventory to find an object that matches the specified criteria in the argument. It checks if the object is visible to both the shopkeeper and the requesting character, and if the object's name contains the words specified in the argument. The function supports selecting a specific instance of an object if multiple objects with the same name exist, using a numeric prefix in the argument.
     *
     * @param ch A pointer to the Character object representing the person requesting the object.
     * @param keeper A pointer to the Character object representing the shopkeeper whose inventory is being searched.
     * @param argument A String object containing the criteria for selecting the object, including an optional numeric prefix to specify which instance of the object to retrieve.
     * @return A pointer to the Object that matches the specified criteria, or nullptr if no such object is found.
     */

  0.559  fsearch_mobile                           — Searches for NPCs in the game world that match specified flags and are
    /**
     * @fn int fsearch_mobile(Character *ch, int fieldptr, const Flags &marked)
     *
     * @brief Searches for NPCs in the game world that match specified flags and are visible to a character.
     *
     * @details The function iterates over all characters in the game world, checking if they are NPCs and visible to the specified character. It then compares the NPCs' flags against a set of specified flags. If an NPC matches the criteria, it formats information about the NPC and appends it to an output string. The function limits the output to a maximum of 500 matches and sends the formatted string to the character's output buffer if any matches are found.
     *
     * @param ch A pointer to the Character object that is performing the search and will receive the output.
     * @param fieldptr An integer representing the specific flag field to compare against the marked flags.
     * @param marked A Flags object containing the set of flags to match against the NPCs' flags.
     * @return The number of NPCs that matched the specified flags and were visible to the character.
     */

  0.531  fsearch_obj                              — Searches for objects based on specified flags and outputs their detail
    /**
     * @fn void fsearch_obj(Character *ch, int fieldptr, const Flags &marked)
     *
     * @brief Searches for objects based on specified flags and outputs their details.
     *
     * @details The function fsearch_obj iterates through a list of objects in the game world, checking each object against specified flags. If an object matches the criteria, it formats and stores information about the object, such as its location and description, into a buffer. The function limits the output to a maximum of 500 objects to prevent excessive data from being sent. The results are then sent to the specified character's output buffer. If no objects match the criteria, a message indicating no matches is sent instead.
     *
     * @param ch A pointer to the Character object that will receive the search results.
     * @param fieldptr An integer representing the field of the object to be checked against the specified flags.
     * @param marked A Flags object containing the flags to be matched against the objects' flags.
     * @return This function does not return a value.
     */

  0.530  race_lookup                              — Finds the index of a race by its name.
    /**
     * @fn int race_lookup(const String &name)
     *
     * @brief Finds the index of a race by its name.
     *
     * @details Finds the race number corresponding to a given name.
    This function searches through a predefined race table to find a race whose name matches the given input name. The comparison is case-insensitive and checks if the input name is a prefix of any race name in the table. If a match is found, the index of the race in the table is returned.
     *
     * @param name The name of the race to look up, provided as a String.
     * @return The index of the race in the race table if a match is found; otherwise, 0.
     */

  0.524  fsearch_player                           — Searches for players with specific flags set and outputs the results.
    /**
     * @fn int fsearch_player(Character *ch, int fieldptr, const Flags &marked)
     *
     * @brief Searches for players with specific flags set and outputs the results.
     *
     * @details The function iterates over all characters in the game world, checking if they are visible to the specified character and if they are in a visible room. It then compares the specified field of each character's flags against the provided 'marked' flags. If all the 'marked' flags are set in the character's flags, the character is counted and their information is formatted and added to the output string. The function limits the output to a maximum of 500 characters. If any characters are found, the formatted output is sent to the specified character's output buffer.
     *
     * @param ch A pointer to the Character object performing the search.
     * @param fieldptr An integer representing the specific field of flags to check against the 'marked' flags.
     * @param marked A Flags object containing the flags to be checked against each character's flags.
     * @return The number of characters found with the specified flags set.
     */

  0.520  fsearch_room                             — Searches for rooms visible to a character that match specified flag cr
    /**
     * @fn void fsearch_room(Character *ch, int fieldptr, const Flags &marked)
     *
     * @brief Searches for rooms visible to a character that match specified flag criteria.
     *
     * @details The function iterates over all rooms in the game world, checking if each room is visible to the specified character and if it matches the given flag criteria. It collects up to 500 matching rooms and formats their details into a string, which is then sent to the character's output buffer. If no rooms match the criteria, a message is sent indicating no matches were found.
     *
     * @param ch A pointer to the Character object representing the character performing the search.
     * @param fieldptr An integer representing the field to be checked in each room, determining which flags to compare.
     * @param marked A constant reference to a Flags object containing the flags to be matched against each room's flags.
     * @return This function does not return a value.
     */

  0.510  liq_lookup                               — Finds the index of a liquid whose name matches the given prefix.
    /**
     * @fn int liq_lookup(const String &name)
     *
     * @brief Finds the index of a liquid whose name matches the given prefix.
     *
     * @details Finds the index of a liquid in the table by matching its name.
    This function searches through a table of liquids to find the index of the first liquid whose name starts with the same character as the given 'name' and for which 'name' is a prefix. The search is case-insensitive, meaning it does not distinguish between uppercase and lowercase letters. If a match is found, the index of the liquid in the table is returned. If no match is found, the function returns -1.
     *
     * @param name The String object representing the name to search for in the liquid table.
     * @return Returns the index of the liquid in the table if a match is found; otherwise, returns -1.
     */

  0.504  quest_where                              — Provides information about the location of a specified item or mob for
    /**
     * @fn void quest_where(Character *ch, char *what)
     *
     * @brief Provides information about the location of a specified item or mob for a character.
     *
     * @details The function 'quest_where' is used to inform a character about the last known location of a specified item or mob. It checks if the character's quest location is valid and logs a bug report if it is not. If the character is in a room, it retrieves the room associated with the character's quest location and sends a formatted message to the character, indicating the area and possibly the specific room where the item or mob was last seen.
     *
     * @param ch A pointer to the Character object that will receive the location information.
     * @param what A C-style string representing the item or mob for which the location information is sought.
     * @return This function does not return a value.
     */

  0.504  get_eq_char                              — Retrieves the object worn by a character at a specified location.
    /**
     * @fn Object * get_eq_char(Character *ch, int iWear)
     *
     * @brief Retrieves the object worn by a character at a specified location.
     *
     * @details Finds an object worn by a character at a specific wear location.
    This function searches through the list of objects carried by a character to find an object that is worn at a specified location. If the character is null or no object is found at the specified location, the function returns null.
     *
     * @param ch A pointer to the Character whose equipment is being searched.
     * @param iWear An integer representing the specific wear location to search for an object.
     * @return A pointer to the Object found at the specified wear location, or nullptr if no such object exists.
     */

  0.501  get_extra_descr                          — Searches for an ExtraDescr with a matching keyword.
    /**
     * @fn const ExtraDescr * get_extra_descr(const String &name, const ExtraDescr *ed)
     *
     * @brief Searches for an ExtraDescr with a matching keyword.
     *
     * @details Retrieves an extra description matching a given name from a list.
    This function iterates through a linked list of ExtraDescr objects, checking each one's keyword for a match with the provided name. The comparison is case-insensitive, leveraging the String class's capabilities. If a match is found, the function returns a pointer to the corresponding ExtraDescr; otherwise, it returns nullptr.
     *
     * @param name The name to search for within the keywords of the ExtraDescr objects.
     * @param ed A pointer to the first ExtraDescr object in the list to be searched.
     * @return A pointer to the ExtraDescr object whose keyword matches the given name, or nullptr if no match is found.
     */

  0.499  weapon_lookup                            — Finds the index of a weapon by its name.
    /**
     * @fn int weapon_lookup(const String &name)
     *
     * @brief Finds the index of a weapon by its name.
     *
     * @details This function searches through a predefined weapon table to find a weapon whose name matches the given input name. The comparison is case-insensitive and checks if the input name is a prefix of any weapon name in the table. If a match is found, the index of the weapon in the table is returned.
     *
     * @param name The name of the weapon to look up. It is a case-insensitive string that is checked as a prefix against weapon names in the table.
     * @return The index of the weapon in the weapon table if found; otherwise, returns -1 if no matching weapon is found.
     */

  0.499  attack_lookup                            — Finds the index of an attack by its name.
    /**
     * @fn int attack_lookup(const String &name)
     *
     * @brief Finds the index of an attack by its name.
     *
     * @details This function searches through the attack_table to find an attack whose name matches the given name, ignoring case. It checks if the provided name is a prefix of any attack name in the table. If a match is found, it returns the index of the attack in the table. If no match is found, it returns 0.
     *
     * @param name The name of the attack to look up, provided as a String object.
     * @return The index of the attack in the attack table if found; otherwise, returns 0.
     */

  0.489  help                                     — Processes a help request by querying the database for help text based 
    /**
     * @fn void help(Character *ch, const String &argument)
     *
     * @brief Processes a help request by querying the database for help text based on keywords.
     *
     * @details Executes the internal help command to retrieve and display help text for a character.
    This function constructs a SQL query to search for help text in the database using the provided keywords. It formats the query to match any help entries where the keywords are found in the specified column. If a matching entry is found, the help text is retrieved and sent to the specified character. If no entry is found or if the text is null, an error is logged.
     *
     * @param ch A pointer to the Character object representing the recipient of the help text.
     * @param argument A constant reference to a String object containing the keywords used to search for the help entry.
     * @return This function does not return a value.
     */

  0.473  Area::get_obj_prototype                  — Retrieves the object prototype associated with a given virtual number.
    /**
     * @fn ObjectPrototype * Area::get_obj_prototype(const Vnum &)
     *
     * @brief Retrieves the object prototype associated with a given virtual number.
     *
     * @details This function searches for an ObjectPrototype within the Area's collection of object prototypes using the provided Vnum. If a prototype with the specified Vnum exists, it returns a pointer to that ObjectPrototype. If no such prototype is found, it returns a null pointer.
     *
     * @param vnum The virtual number used to identify and locate the corresponding ObjectPrototype.
     * @return A pointer to the ObjectPrototype associated with the given Vnum, or nullptr if no such prototype exists.
     */

  0.465  has_key                                  — Checks if a character possesses a specific key.
    /**
     * @fn bool has_key(Character *ch, int key)
     *
     * @brief Checks if a character possesses a specific key.
     *
     * @details This function iterates through the list of objects that a character is carrying to determine if any of these objects match a specified key identifier. It returns true if the character has an object with the matching key, and false otherwise.
     *
     * @param ch A pointer to the Character whose inventory is being checked.
     * @param key An integer representing the unique identifier of the key to search for.
     * @return Returns true if the character possesses an object with the specified key identifier, otherwise returns false.
     */

  0.440  World::get_obj_prototype                 — Retrieves the object prototype for a given virtual number.
    /**
     * @fn ObjectPrototype * World::get_obj_prototype(const Vnum &)
     *
     * @brief Retrieves the object prototype for a given virtual number.
     *
     * @details This function attempts to find and return the ObjectPrototype associated with the specified virtual number (vnum). It first retrieves the Area object that contains the vnum using the get_area function. If the area is found, it then calls the area's get_obj_prototype method to obtain the ObjectPrototype. If no prototype is found and the game is currently booting, a bug report is logged. The function returns a pointer to the ObjectPrototype if found, or nullptr if no such prototype exists.
     *
     * @param vnum The virtual number used to identify and locate the corresponding ObjectPrototype.
     * @return A pointer to the ObjectPrototype associated with the given vnum, or nullptr if no such prototype exists.
     */

  0.433  get_weapon_type                          — Determines the weapon type based on the given name.
    /**
     * @fn int get_weapon_type(const String &name)
     *
     * @brief Determines the weapon type based on the given name.
     *
     * @details This function searches through a predefined weapon table to find a weapon type that matches the given name. It performs a case-insensitive comparison of the first character and checks if the provided name is a prefix of any weapon name in the table. If a match is found, it returns the corresponding weapon type. If no match is found, it returns a default value indicating an exotic weapon type.
     *
     * @param name The name of the weapon to look up, provided as a String object.
     * @return The integer value representing the weapon type if a match is found, or WEAPON_EXOTIC if no match is found.
     */


================================================================================
[domain] quests  (stability: stable)
  desc: Quest system: random quest generation and target assignment, skill-quest creation (mob and object variants), quest compl…
  locked: 16 functions, 16 with embeddings
  sim to desc — mean: 0.578  min: 0.460  max: 0.728

  0.728  generate_skillquest                      — Generates a skill quest for a character by creating quest objects or m
    /**
     * @fn void generate_skillquest(Character *ch, Character *questman)
     *
     * @brief Generates a skill quest for a character by creating quest objects or mobs based on random chance.
     *
     * @details This function initializes a skill quest for the specified character by setting countdown and quest giver information. It then randomly determines the type of quest to generate: a 40% chance to create a skill quest object and assign it to a room, with corresponding narrative messages; a 66% chance to generate a quest mob; or a 20% chance to generate both a quest object and a quest mob, linking their locations. The function handles object and room creation, assigns quest details to the character, and outputs relevant quest narrative messages. It logs bugs if object or room generation fails.
     *
     * @param ch Pointer to the Character for whom the skill quest is being generated.
     * @param questman Pointer to the Character acting as the quest giver, used for messaging and quest assignment.
     * @return Void; the function performs side effects such as creating quest objects/mobs, setting quest locations, and sending messages, without returning a value.
     */

  0.723  generate_skillquest_mob                  — Generates a skill quest mobile character and associated quest details 
    /**
     * @fn void generate_skillquest_mob(Character *ch, Character *questman, int level, int type)
     *
     * @brief Generates a skill quest mobile character and associated quest details in the game world.
     *
     * @details This function creates a quest-related mobile character (mob) with randomized attributes such as sex, name, title, and role, then places it in a suitable quest room. Depending on the quest type, it may also generate a quest object and assign it to the mob, while providing narrative messages via the questman character. The function updates the player's quest data with the created mob and logs errors if creation or placement fails. It handles different quest types, including mob-only quests and object-to-mob quests, ensuring proper placement and descriptive setup for the quest scenario.
     *
     * @param ch Pointer to the Character initiating the quest, used to determine quest level and assign the generated mob.
     * @param questman Pointer to the Character acting as the quest giver, used to deliver quest-related messages.
     * @param level Integer representing the level at which the quest is generated, influencing attributes of the quest mob and object.
     * @param type Integer indicating the quest type: 1 for mob quest, 2 for object-to-mob quest.
     * @return Void; the function performs side effects such as creating and placing quest characters and objects, and sending messages, without returning a value.
     */

  0.718  generate_quest                           — Generates a quest for a character by selecting a suitable victim and a
    /**
     * @fn void generate_quest(Character *ch, Character *questman)
     *
     * @brief Generates a quest for a character by selecting a suitable victim and assigning quest objectives.
     *
     * @details This function creates a quest for the specified character by selecting an appropriate victim NPC from the game world, considering various criteria such as level, area, and status flags. It performs a two-pass selection process to ensure the victim is suitably aligned with the character's morality. Depending on a random chance, it assigns either a 'recover item' quest by creating and placing a quest item in the victim's room or a 'kill mob' quest with narrative instructions. It also sets relevant quest data in the character's profile, such as quest location, target, and countdown timer. If no suitable victim is found, it informs the quest giver and resets the quest state.
     *
     * @param ch Pointer to the Character object who is receiving the quest.
     * @param questman Pointer to the Character object who is assigning the quest.
     * @return This function does not return a value; it modifies the character's quest data and may output messages to the game environment.
     */

  0.653  generate_skillquest_obj                  — Generates a skill quest object for a character at a specified level.
    /**
     * @fn Object * generate_skillquest_obj(Character *ch, int level)
     *
     * @brief Generates a skill quest object for a character at a specified level.
     *
     * @details This function creates and initializes a new skill quest object for the given character, based on a random selection from a predefined table of quest items. The object's attributes, such as name, short description, and long description, are set according to the selected item. The function also sets a timer for the object and links an extra description to it. The created object is then assigned to the character's skill quest object data.
     *
     * @param ch A pointer to the Character for whom the skill quest object is being generated.
     * @param level An integer representing the level at which the object is created, potentially influencing its properties.
     * @return A pointer to the newly created Object, or nullptr if an error occurs during creation.
     */

  0.611  IS_QUESTOR                              
    /**
     * @def IS_QUESTOR
     *
     */

  0.588  squest_info                              — Displays information about the current skill quest for a character.
    /**
     * @fn void squest_info(Character *ch)
     *
     * @brief Displays information about the current skill quest for a character.
     *
     * @details This function provides detailed information about the skill quest assigned to the specified character. It checks if the character is currently on a skill quest, verifies the quest giver's existence, and retrieves relevant quest data such as associated objects and mobs. Depending on the quest's progress and the available data, it outputs descriptive messages to the character, including quest objectives, locations, and completion status. If inconsistencies or missing data are detected, it logs bugs and performs cleanup operations to maintain game state integrity.
     *
     * @param ch Pointer to the Character object whose skill quest information is to be displayed.
     * @return Void; the function outputs quest information or performs cleanup without returning a value.
     */

  0.576  squestobj_to_squestmob                   — Handles the completion of a skill quest when a character returns a que
    /**
     * @fn void squestobj_to_squestmob(Character *ch, Object *obj, Character *mob)
     *
     * @brief Handles the completion of a skill quest when a character returns a quest object to a quest mob.
     *
     * @details This function manages the process when a character returns a quest object to the quest mob, including social interactions, messaging, object removal, and quest state updates. It checks for social commands, thanks the character, removes the quest object from the game, communicates quest progress to the character and the game log, and finally removes the quest mob from the game world while updating the character's quest status.
     *
     * @param ch Pointer to the Character who is returning the quest object.
     * @param obj Pointer to the Object representing the quest item being returned.
     * @param mob Pointer to the Character (quest mob) who is receiving the returned object.
     * @return Void; the function performs side effects such as messaging, object and character removal, and quest state updates without returning a value.
     */

  0.573  quest_info                               — Provides quest-related information to a character.
    /**
     * @fn void quest_info(Character *ch)
     *
     * @brief Provides quest-related information to a character.
     *
     * @details The function checks the quest status of a character and provides relevant information based on the current quest state. It handles different scenarios such as the character not being on a quest, the quest giver being invalid, and the quest objectives being either a mobile or an object. It also logs errors if inconsistencies are found in the quest data.
     *
     * @param ch A pointer to the Character object for whom the quest information is being retrieved.
     * @return This function does not return a value.
     */

  0.547  IS_SQUESTOR                             
    /**
     * @def IS_SQUESTOR
     *
     */

  0.526  quest_usage                              — Displays usage information for QUEST commands to a character.
    /**
     * @fn void quest_usage(Character *ch)
     *
     * @brief Displays usage information for QUEST commands to a character.
     *
     * @details The quest_usage function provides a character with a list of available QUEST commands. It sets the text color to yellow and bold before displaying the commands. If the character is immortal, additional commands are shown. The function concludes by instructing the character to type 'HELP QUEST' for more information, and then resets the text color to white and non-bold.
     *
     * @param ch A pointer to the Character object to whom the QUEST command usage information will be displayed.
     * @return This function does not return a value.
     */

  0.518  find_squestmaster                        — Finds the special quest master character in the current room.
    /**
     * @fn Character * find_squestmaster(Character *ch)
     *
     * @brief Finds the special quest master character in the current room.
     *
     * @details This function searches through the characters present in the room of the given character 'ch' to find a special quest master. It iterates over each character in the room, checking if they are a non-player character (NPC) and if their special function matches 'spec_squestmaster'. If such a character is found, additional checks are performed to ensure the quest master has valid data and is not currently engaged in combat. If all conditions are met, the quest master character is returned.
     *
     * @param ch A pointer to the Character object representing the player or entity searching for the quest master.
     * @return A pointer to the quest master Character if found and valid; otherwise, returns nullptr.
     */

  0.512  quest_cleanup                            — Resets the quest-related data for a character.
    /**
     * @fn void quest_cleanup(Character *ch)
     *
     * @brief Resets the quest-related data for a character.
     *
     * @details The function quest_cleanup is responsible for resetting all quest-related fields in the given character's data structure. This includes removing the questor flag, clearing the quest giver, and resetting countdown, questmob, questobj, questobf, and questloc to their default states. It is typically used when a character's quest is completed or aborted, ensuring that the character is ready for a new quest.
     *
     * @param ch A pointer to the Character whose quest data is to be reset.
     * @return This function does not return a value.
     */

  0.506  sq_cleanup                               — Cleans up and resets quest-related data for a character, removing asso
    /**
     * @fn void sq_cleanup(Character *ch)
     *
     * @brief Cleans up and resets quest-related data for a character, removing associated quest objects and mobs.
     *
     * @details Performs cleanup of a Character's quest-related data and removes associated objects and entities from the game world.
    This function resets the quest flags and counters for the specified character, removes the quest object from the game world if it exists, and extracts the quest mob if present and not marked as garbage. It also clears references to the quest object and mob, ensuring the character's quest state is properly reset and no residual quest entities remain in the game world.
     *
     * @param ch Pointer to the Character object whose quest data and related entities are to be cleaned up.
     * @return Void; the function performs cleanup operations without returning a value.
     */

  0.505  find_questmaster                         — Finds a questmaster character in the same room as the given character.
    /**
     * @fn Character * find_questmaster(Character *ch)
     *
     * @brief Finds a questmaster character in the same room as the given character.
     *
     * @details This function searches for a non-player character (NPC) in the same room as the specified character that has the special function 'spec_questmaster'. It iterates through all characters in the room and checks if they are NPCs and have the 'spec_questmaster' special function. If such a character is found, it further checks if the character's pIndexData is not null and that the character is not currently fighting. If all conditions are met, the questmaster character is returned. Otherwise, appropriate messages are logged or sent to the character, and null is returned.
     *
     * @param ch A pointer to the Character object representing the character whose room is being searched for a questmaster.
     * @return A pointer to the questmaster Character if found and valid; otherwise, returns null.
     */

  0.498  has_enough_qps                           — Checks if a character has enough quest points.
    /**
     * @fn int has_enough_qps(Character *ch, int number_of)
     *
     * @brief Checks if a character has enough quest points.
     *
     * @details This function determines whether a given character has a sufficient number of quest points. It first checks if the character is a non-player character (NPC) using the 'is_npc' method. If the character is an NPC, the function returns 0, indicating they do not have enough quest points. If the character is not an NPC, it checks if the character's quest points are greater than or equal to the specified number or if the character is immortal. If either condition is true, the function returns 1, indicating the character has enough quest points. Otherwise, it returns 0.
     *
     * @param ch A pointer to the Character object whose quest points are being checked.
     * @param number_of The number of quest points required.
     * @return Returns 1 if the character has enough quest points or is immortal, otherwise returns 0.
     */

  0.460  quest_level_diff                         — Determines if the character and monster levels are within the same ran
    /**
     * @fn bool quest_level_diff(int clevel, int mlevel)
     *
     * @brief Determines if the character and monster levels are within the same range.
     *
     * @details This function checks if the character's level (clevel) and the monster's level (mlevel) fall within predefined level ranges. If both levels are within the same range, the function returns true, indicating that the levels are compatible for a quest. The ranges are divided into several brackets, such as 1-5, 6-15, and so on, up to levels greater than 85.
     *
     * @param clevel The level of the character, used to determine the appropriate level range.
     * @param mlevel The level of the monster, used to determine the appropriate level range.
     * @return Returns true if both the character's level and the monster's level are within the same predefined range, otherwise returns false.
     */


================================================================================
[domain] npc_behavior  (stability: likely_split)
  desc: NPC behavioural logic: MobProg program execution (driver, command processing, conditional evaluation, variable translati…
  locked: 21 functions, 21 with embeddings
  sim to desc — mean: 0.588  min: 0.342  max: 0.714

  0.714  mprog_act_trigger                        — Triggers an action program for a non-player character (NPC).
    /**
     * @fn void mprog_act_trigger(const char *buf, Character *mob, Character *ch, Object *obj, void *vo)
     *
     * @brief Triggers an action program for a non-player character (NPC).
     *
     * @details Triggers a mobile program action if conditions are met.
    This function checks if the given character 'mob' is a non-player character (NPC) and if it has the ACT_PROG flag set in its program type flags. If both conditions are met, it creates a new MobProgActList object, links it to the NPC's action program list, and assigns the provided parameters to the new action program entry. This setup allows the NPC to react to specific actions or events in the game.
     *
     * @param buf A constant character pointer to a buffer containing the action description or command.
     * @param mob A pointer to the Character object representing the mobile (NPC) that may trigger the action.
     * @param ch A pointer to the Character object representing the character involved in the action.
     * @param obj A pointer to the Object involved in the action.
     * @param vo A generic pointer to any additional data required for the action.
     * @return This function does not return a value.
     */

  0.690  mprog_driver                             — Processes a list of mobile program commands triggered by an event, han
    /**
     * @fn void mprog_driver(const String &com_list, Character *mob, Character *actor, Object *obj, void *vo)
     *
     * @brief Processes a list of mobile program commands triggered by an event, handling conditional logic and command execution.
     *
     * @details This function, mprog_driver, is invoked when a trigger condition is met within the game environment. It parses the provided command list, handling 'if' conditions through mprog_process_if and executing commands via mprog_process_cmnd. It first selects a random visible non-immortal player in the same room as the mobile (mob) to serve as a secondary target if needed. The command list is copied to a local buffer to prevent modification of the original. The function iterates through each command, processing conditional blocks and commands accordingly, and terminates if the mobile (mob) becomes garbage (e.g., destroyed) during execution.
     *
     * @param com_list The string containing the list of commands to be processed.
     * @param mob The mobile character (NPC) that triggered the program.
     * @param actor The character who initiated the trigger, if applicable.
     * @param obj The object associated with the trigger, if any.
     * @param vo A void pointer to a secondary target, which can be a character or object.
     * @return Void; the function performs command processing and execution with no return value.
     */

  0.680  mprog_percent_check                      — Checks and executes mobile program commands based on a probabilistic t
    /**
     * @fn void mprog_percent_check(Character *mob, Character *actor, Object *obj, void *vo, Flags::Bit type)
     *
     * @brief Checks and executes mobile program commands based on a probabilistic trigger.
     *
     * @details Performs a probabilistic check to trigger appropriate mob programs based on a random percentile.
    This function iterates through the list of mobile program scripts associated with a given mobile entity (mob). For each script, it verifies whether the object is marked as garbage; if so, it terminates early. It then compares the script's type with the specified type parameter and performs a percentage roll using number_percent(). If the roll is below the threshold specified by the script's argument list (converted to an integer), it executes the script's command list via mprog_driver, passing relevant context objects. For certain program types (GREET_PROG and ALL_GREET_PROG), it continues checking subsequent scripts; otherwise, it stops after executing one matching script.
     *
     * @param mob Pointer to the Character object representing the mobile (mob) to evaluate.
     * @param actor Pointer to the Character object representing the actor involved in the trigger.
     * @param obj Pointer to the Object involved in the trigger, if any.
     * @param vo Void pointer to additional data passed to the program driver.
     * @param type Flags::Bit value indicating the type of mob program to check against.
     * @return Void; the function performs side effects by executing mob programs when conditions are met.
     */

  0.677  mprog_entry_trigger                      — Triggers entry mob programs for a character if conditions are met.
    /**
     * @fn void mprog_entry_trigger(Character *mob)
     *
     * @brief Triggers entry mob programs for a character if conditions are met.
     *
     * @details Triggers entry-related mob programs for a given character if conditions are met.
    This function checks whether the specified character 'mob' is a non-player character (NPC) and has the 'ENTRY_PROG' flag set in its program type flags. If both conditions are true, it invokes the 'mprog_percent_check' function to probabilistically trigger any associated entry mob programs. The function performs no return value but may cause side effects through the execution of mob programs when triggered.
     *
     * @param mob Pointer to the Character object representing the mobile (mob) to evaluate for entry triggers.
     * @return Void; the function does not return a value but may trigger side effects via mob programs.
     */

  0.657  mprog_speech_trigger                     — Processes speech triggers for NPCs in the same room based on input tex
    /**
     * @fn void mprog_speech_trigger(const String &txt, Character *mob)
     *
     * @brief Processes speech triggers for NPCs in the same room based on input text.
     *
     * @details Processes speech triggers for NPC characters within a room based on input text.
    This function iterates through all characters present in the same room as the specified mobile character ('mob'). For each character, it checks if the character is an NPC with speech trigger programs enabled. If so, it invokes the trigger wordlist check to see if the input text matches any trigger words associated with that NPC, executing corresponding scripts if matches are found. The function terminates early if the 'mob' is marked as garbage, ensuring no further processing occurs on invalid or deallocated objects.
     *
     * @param txt The input text string representing speech to be checked against NPC triggers.
     * @param mob Pointer to the character (NPC) who is speaking and whose room is being evaluated.
     * @return Void; the function performs trigger checks and script executions without returning a value.
     */

  0.651  mprog_buy_trigger                        — Triggers buy-related mob programs when a character interacts with a mo
    /**
     * @fn void mprog_buy_trigger(Character *mob, Character *ch)
     *
     * @brief Triggers buy-related mob programs when a character interacts with a mobile NPC.
     *
     * @details This function checks if the specified mobile character ('mob') is an NPC and has the 'BUY_PROG' flag set in its program type flags. If both conditions are met, it performs a probabilistic check to determine whether to execute associated buy-related mob programs, passing the involved character ('ch') as the actor. The function does not return a value but may trigger side effects through mob program execution.
     *
     * @param mob Pointer to the Character object representing the mobile (NPC) to evaluate for buy triggers.
     * @param ch Pointer to the Character object representing the character interacting with the mob.
     * @return Void; the function performs side effects by potentially executing mob programs based on the conditions.
     */

  0.648  mprog_process_cmnd                       — Processes a command string by expanding variables and executing the re
    /**
     * @fn void mprog_process_cmnd(const String &cmnd, Character *mob, Character *actor, Object *obj, void *vo, Character *rndm)
     *
     * @brief Processes a command string by expanding variables and executing the resulting command.
     *
     * @details This function takes a command string and replaces variable placeholders denoted by '$' with their corresponding translations obtained via the mprog_translate function. It constructs the expanded command in a buffer and then interprets and executes it in the context of the specified mobile entity (mob). The process allows dynamic command generation based on game context and character states, facilitating scripted behaviors or reactive actions within mobile programs.
     *
     * @param cmnd The command string containing text and variable placeholders to be processed.
     * @param mob Pointer to the Character object representing the mobile executing the command.
     * @param actor Pointer to the Character object representing the actor involved in the command context.
     * @param obj Pointer to the Object involved in the command context.
     * @param vo A void pointer that can point to either a Character or an Object, used as a secondary target in translation.
     * @param rndm Pointer to a random Character object used within the translation context.
     * @return Void; the function performs command processing and execution with no return value.
     */

  0.647  mprog_death_trigger                      — Handles death-related triggers and effects for a character upon its de
    /**
     * @fn void mprog_death_trigger(Character *mob)
     *
     * @brief Handles death-related triggers and effects for a character upon its death.
     *
     * @details Handles death-related triggers and effects for a character, including mob program checks and death cry.
    This function checks if the specified character (mob) is a non-player character (NPC) with an associated death program. If so, it performs a probabilistic check to determine whether to trigger the death program, executing any associated mob scripts. Afterward, it invokes the death cry for the character, which may include messaging, object creation, and room notifications. The function operates as a black box, encapsulating death event handling logic for NPCs.
     *
     * @param mob Pointer to the Character object representing the entity that has died and is being processed for death triggers.
     * @return Void; the function performs side effects such as executing mob programs and messaging without returning a value.
     */

  0.635  mprog_bribe_trigger                      — Handles the bribe trigger event for a mobile character, executing asso
    /**
     * @fn void mprog_bribe_trigger(Character *mob, Character *ch, int amount)
     *
     * @brief Handles the bribe trigger event for a mobile character, executing associated mobile program logic.
     *
     * @details Handles the bribe trigger for a mobile character, executing associated mobile programs if conditions are met.
    This function processes a bribe event initiated by a character 'ch' towards a mobile character 'mob'. It first verifies that 'mob' is an NPC; if not, the function exits. It then searches 'mob's' list of mobile programs for a bribe trigger. Upon finding such a program, it creates a money object representing the bribe amount, deducts this amount from 'mob's' currency, and if the amount meets or exceeds the threshold specified in the program's argument list, it executes the corresponding mobile program commands. The function performs no return value and modifies game state accordingly.
     *
     * @param mob Pointer to the mobile character (NPC) being bribed.
     * @param ch Pointer to the character who is bribing.
     * @param amount The amount of currency offered as a bribe.
     * @return Void; the function performs side effects such as executing mobile programs and modifying character states without returning a value.
     */

  0.621  mprog_greet_trigger                      — Triggers greeting mob programs for NPCs in the same room when a charac
    /**
     * @fn void mprog_greet_trigger(Character *ch)
     *
     * @brief Triggers greeting mob programs for NPCs in the same room when a character enters.
     *
     * @details This function iterates through all characters present in the same room as the specified character 'ch'. For each NPC (non-player character) that is not the character itself, it checks if the NPC can see 'ch', is not currently fighting, and is awake. If these conditions are met, and the NPC has the 'GREET_PROG' or 'ALL_GREET_PROG' program type flags set, it performs a probabilistic check to potentially trigger the corresponding mob program. The function terminates early if the 'ch' object is marked as garbage. It effectively facilitates NPCs greeting or acknowledging the presence of a character entering their vicinity.
     *
     * @param ch Pointer to the Character object representing the character who has entered the room and triggers the greeting checks.
     * @return Void; the function performs side effects by potentially executing greeting scripts on NPCs in the room.
     */

  0.614  mprog_translate                          — Translates a character code into a string representation based on the 
    /**
     * @fn String mprog_translate(char ch, Character *mob, Character *actor, Object *obj, void *vo, Character *rndm)
     *
     * @brief Translates a character code into a string representation based on the context of a mobile program.
     *
     * @details The function mprog_translate takes a character code and translates it into a string based on the context provided by the mobile (mob), actor, object, victim, and random character. It handles various character codes to produce context-sensitive strings, such as names, pronouns, and descriptions, which are used in mobile programs for dynamic text generation in a game environment. The function ensures that the visibility of characters and objects is considered when generating the output string.
     *
     * @param ch The character code that determines the type of translation to perform.
     * @param mob A pointer to the Character object representing the mobile executing the program.
     * @param actor A pointer to the Character object representing the actor involved in the context.
     * @param obj A pointer to the Object involved in the context.
     * @param vo A void pointer that can point to either a Character or an Object, used as a secondary target.
     * @param rndm A pointer to a random Character object used in the context.
     * @return A String object containing the translated text based on the character code and context.
     */

  0.602  mprog_tick_trigger                       — Checks and potentially triggers mob programs based on a tick event for
    /**
     * @fn void mprog_tick_trigger(Character *mob)
     *
     * @brief Checks and potentially triggers mob programs based on a tick event for the specified mob.
     *
     * @details Triggers mob programs based on tick events if the mob has the TICK_PROG flag set.
    This function evaluates whether the given mob has the TICK_PROG flag set in its program type flags. If so, it performs a probabilistic check via mprog_percent_check to determine if a mob program associated with a tick event should be executed. The function does not return a value but may trigger side effects by executing mob programs when conditions are met. It is intended to be called periodically to handle tick-based triggers for mobs.
     *
     * @param mob Pointer to the Character object representing the mobile (mob) to evaluate for tick-based mob programs.
     * @return Void; the function performs side effects by potentially executing mob programs and does not return a value.
     */

  0.596  mprog_give_trigger                       — Handles the 'give' trigger for a mobile NPC when it receives an item f
    /**
     * @fn void mprog_give_trigger(Character *mob, Character *ch, Object *obj)
     *
     * @brief Handles the 'give' trigger for a mobile NPC when it receives an item from a character.
     *
     * @details Handles the 'give' trigger for a mobile NPC when it receives an item.
    This function checks if the specified mobile character ('mob') is an NPC with 'give' program flags enabled. If so, it iterates through the mobile's associated program list ('mobprogs') and processes each 'give' type program. For each program, it extracts the first argument from the program's argument list and compares the object name involved in the give event with the program's specified argument or the keyword 'all'. If a match is found, it executes the corresponding command list via 'mprog_driver', passing relevant entities such as the mobile, the character who gave the item, and the object itself. The function terminates after executing the first matching program.
     *
     * @param mob Pointer to the mobile character (NPC) that received the item.
     * @param ch Pointer to the character who gave the item to the NPC.
     * @param obj Pointer to the object that was given to the NPC.
     * @return Void; performs command processing and execution based on matching give triggers.
     */

  0.591  mprog_wordlist_check                     — Checks a character's mobile programs for keyword or phrase triggers wi
    /**
     * @fn void mprog_wordlist_check(const String &arg, Character *mob, Character *actor, Object *obj, void *vo, Flags::Bit type)
     *
     * @brief Checks a character's mobile programs for keyword or phrase triggers within a given argument string and executes matching scripts.
     *
     * @details Checks a list of trigger words against input arguments and executes associated mobile programs if matches are found.
    This function iterates through all mobile programs associated with the specified 'mob' character, filtering by the specified trigger 'type'. For each relevant program, it converts the program's argument list and the input argument string to lowercase for case-insensitive matching. If the argument list starts with 'p ', it searches for the presence of the entire phrase within the input string, ensuring word boundaries are respected. Otherwise, it tokenizes the argument list into individual words and searches for each within the input string, again respecting word boundaries. When a match is found, it invokes 'mprog_driver' to execute the associated command list. The function terminates early if the 'mob' object is marked as garbage, preventing further processing.
     *
     * @param arg The input argument string to be checked against trigger conditions.
     * @param mob Pointer to the character (mobile) whose triggers are being evaluated.
     * @param actor Pointer to the character who initiated the trigger, if applicable.
     * @param obj Pointer to the object associated with the trigger, if any.
     * @param vo Void pointer to a secondary target, such as a character or object, involved in the trigger.
     * @param type Bit flag indicating the type of trigger to match against (e.g., speech, command).
     * @return Void; the function performs trigger matching and executes associated scripts without returning a value.
     */

  0.583  mprog_process_if                         — Handles control flow logic for MOBprograms, processing 'if', 'else', '
    /**
     * @fn char * mprog_process_if(const char *ifchck, char *com_list, Character *mob, Character *actor, Object *obj, void *vo, Character *rndm)
     *
     * @brief Handles control flow logic for MOBprograms, processing 'if', 'else', 'break', and 'endif' commands within mobile scripts.
     *
     * @details This function evaluates conditional 'if' checks and manages the execution flow of MOBprogram command lists based on these conditions. It supports nested 'if' statements, 'else' branches, and proper termination with 'endif'. The function parses commands sequentially, executing commands when conditions are true, skipping or jumping over blocks when false, and handling errors or syntax issues by logging bugs and terminating execution. It ensures that the control flow adheres to the script syntax, maintaining robustness against malformed scripts. It also manages recursion for nested 'if' statements and respects 'break' commands to exit processing early. The function modifies the command list pointer to reflect the current position after processing the control flow blocks.
     *
     * @param ifchck The condition string to evaluate for the 'if' statement.
     * @param com_list Pointer to the current position in the command list string; gets advanced as commands are processed.
     * @param mob Pointer to the Character object representing the mobile entity executing the script.
     * @param actor Pointer to the Character object representing the actor involved in the script context.
     * @param obj Pointer to the Object involved in the script context.
     * @param vo Void pointer to either a Character or Object, used as a secondary target in command processing.
     * @param rndm Pointer to a random Character object used within command execution context.
     * @return Returns a pointer to the position in the command list after processing the 'if' block, or nullptr if execution should terminate or an error occurs.
     */

  0.577  mprog_do_ifchck                          — Performs evaluation of conditional checks within a game scripting syst
    /**
     * @fn bool mprog_do_ifchck(const char *ifchck, Character *mob, Character *actor, Object *obj, void *vo, Character *rndm)
     *
     * @brief Performs evaluation of conditional checks within a game scripting system, returning boolean results or error codes.
     *
     * @details This function parses and evaluates 'if' condition checks expressed as strings in the context of game entities such as characters, objects, and rooms. It supports various condition types like 'rand', 'mudtime', 'ispc', 'isnpc', 'isgood', 'isevil', 'isneutral', 'isfight', 'isimmort', 'iskiller', 'isthief', 'ischarmed', 'isfollow', 'ismaster', 'isleader', 'hitprcnt', 'inroom', 'sex', 'position', 'level', 'class', 'goldamt', 'objtype', 'objval0-3', 'number', and 'name'. The function extracts the condition name, optional operator, and value from the input string, then evaluates the condition based on the current game state and entity attributes. It returns 1 for true, 0 for false, or -1 if an error occurs such as syntax issues or invalid arguments. The evaluation of operators is delegated to helper functions to reduce redundancy. This function is primarily used in MOB scripting to determine whether certain conditions are met for executing subsequent actions.
     *
     * @param ifchck The string containing the conditional check to evaluate, formatted as 'ifchck ( arg ) [opr val]'.
     * @param mob Pointer to the Character object representing the mobile (NPC or player) performing the check.
     * @param actor Pointer to the Character object representing the actor involved in the check.
     * @param obj Pointer to the Object involved in the check.
     * @param vo Void pointer that can point to either a Character or Object, depending on context.
     * @param rndm Pointer to a randomly selected Character object for random comparisons.
     * @return Returns 1 if the condition evaluates to true, 0 if false, and -1 if an error occurs such as syntax errors or invalid arguments.
     */

  0.573  hunt_victim                              — Handles the hunting behavior of an NPC character to pursue and attack 
    /**
     * @fn void hunt_victim(Character *ch)
     *
     * @brief Handles the hunting behavior of an NPC character to pursue and attack its target.
     *
     * @details Handles the hunting behavior of aggressive NPC characters to pursue and attack their designated victims.
    This function manages an NPC character's attempt to hunt a designated victim. It verifies the existence and visibility of the victim, checks if the victim is in the same room to initiate an attack, and otherwise calculates a path toward the victim using pathfinding logic. If the path is found, the character moves in the appropriate direction, opening doors if necessary, or attacks if already in the same room. If the victim is no longer available or visible, the hunting is canceled. The function updates the character's state and issues appropriate game actions and messages during the process.
     *
     * @param ch Pointer to the Character object representing the NPC performing the hunt.
     * @param dir The direction in which the NPC should move to pursue the victim, determined by pathfinding or random selection.
     * @return Void; the function performs actions such as moving the character, initiating combat, or aborting the hunt based on conditions.
     */

  0.490  animate_mob                              — Creates and summons a mobile creature (mob) as a pet or servant for a 
    /**
     * @fn void animate_mob(Character *ch, int level, const char *name, long vnum)
     *
     * @brief Creates and summons a mobile creature (mob) as a pet or servant for a character, based on specified parameters.
     *
     * @details This function allows a non-player character (player) to summon a creature (mob) of a specified type and level, provided certain conditions are met. It first verifies that the caller is not an NPC, then checks if the character has already summoned a specific type of creature to prevent duplicates. It also ensures that summoning is not performed in restricted room types such as city or holy/unholy rooms. If all conditions are satisfied, it creates the mob from a prototype, assigns it to the character's current room, and sets up its behaviors and descriptions. The summoned creature is linked to the character's data for later reference, and appropriate effects and flags are applied to the mob.
     *
     * @param ch Pointer to the Character object initiating the summon.
     * @param level Integer representing the level of the summoned creature, influencing its strength or behavior.
     * @param name String name of the creature to be summoned, used for messaging and description.
     * @param vnum Long integer representing the unique virtual number identifying the creature's prototype.
     * @return Void; the function performs side effects such as creating the creature, assigning it to the character, and sending messages, but does not return a value.
     */

  0.389  mprog_seval                              — Evaluates a string comparison operation based on a specified operator.
    /**
     * @fn bool mprog_seval(const String &lhs, const char *opr, const char *rhs)
     *
     * @brief Evaluates a string comparison operation based on a specified operator.
     *
     * @details The function performs a comparison between a left-hand side string (lhs) and a right-hand side string (rhs) using a specified operator (opr). Supported operators include '==', '!=', '/' (substring), and '!/' (not substring). The function returns a boolean result based on the operation. If an unsupported operator is provided, it logs an error message.
     *
     * @param lhs The left-hand side String object to be compared.
     * @param opr A C-style string representing the operator for comparison. Supported operators are '==', '!=', '/', and '!/'.
     * @param rhs A C-style string representing the right-hand side string to compare against.
     * @return Returns true or false based on the evaluation of the comparison operation. If the operator is not recognized, logs an error and returns false.
     */

  0.369  mprog_veval                              — Evaluates a comparison or bitwise operation between two integers based
    /**
     * @fn bool mprog_veval(int lhs, const char *opr, int rhs)
     *
     * @brief Evaluates a comparison or bitwise operation between two integers based on a given operator.
     *
     * @details The function mprog_veval takes two integers and a string representing an operator, and performs the corresponding comparison or bitwise operation. Supported operators include '==', '!=', '>', '<', '<=', '>=', '&', and '|'. If the operator is not recognized, a bug is logged and the function returns false.
     *
     * @param lhs The left-hand side integer operand for the operation.
     * @param opr A string representing the operator to apply between lhs and rhs.
     * @param rhs The right-hand side integer operand for the operation.
     * @return A boolean value indicating the result of the comparison or bitwise operation. Returns false if the operator is not recognized.
     */

  0.342  mprog_next_command                       — Extracts the next line from a multi-line string.
    /**
     * @fn char * mprog_next_command(char *clist)
     *
     * @brief Extracts the next line from a multi-line string.
     *
     * @details This function processes a multi-line string, where lines are separated by newline characters ('
    '). It modifies the input string by replacing the first newline character with a null terminator ('\0'), effectively isolating the first line. The function returns a pointer to the character immediately following the replaced newline, which is the start of the next line. This operation is destructive to the input string, so the input should not be shared or reused after calling this function.
     *
     * @param clist A pointer to the multi-line string to be processed. The string will be modified in-place.
     * @return A pointer to the start of the next line in the string, or to the null terminator if there are no more lines.
     */


================================================================================
[domain] magic  (stability: stable)
  desc: Spell casting mechanics: object-triggered spell dispatch (scrolls, wands, staves, potions), saving throws against spells…
  locked: 6 functions, 6 with embeddings
  sim to desc — mean: 0.593  min: 0.560  max: 0.622

  0.622  obj_cast_spell                           — Performs spell casting at targets using a magical object within the ga
    /**
     * @fn void obj_cast_spell(skill::type sn, int level, Character *ch, Character *victim, Object *obj)
     *
     * @brief Performs spell casting at targets using a magical object within the game environment.
     *
     * @details Executes a spell cast from an object on specified targets within the game environment.
    This function allows a character to cast a specified spell or skill (identified by 'sn') on various targets, which can include characters or objects, depending on the spell's target type. It validates the spell type, retrieves the spell entry, and determines the appropriate target based on the spell's target type and provided parameters. It handles different target scenarios such as offensive, defensive, self, object, and area effects, performing safety checks, help checks for mobs, and logging errors for invalid cases. The spell is then executed with the specified level and target, and additional combat logic is applied if the spell is offensive. The function modifies the game state by invoking the spell's function pointer and manages combat initiation as needed.
     *
     * @param sn The skill::type representing the spell or skill to be cast.
     * @param level The level of the spell, influencing its potency and saving throw difficulty.
     * @param ch Pointer to the Character object who is casting the spell.
     * @param victim Pointer to the Character object who is the intended target of the spell, if any.
     * @param obj Pointer to the Object object on which the spell is cast, if applicable.
     * @return Void; the function performs spell casting and side effects without returning a value.
     */

  0.617  say_spell                                — Generates and displays a mystical spell incantation message for a char
    /**
     * @fn void say_spell(Character *ch, skill::type sn)
     *
     * @brief Generates and displays a mystical spell incantation message for a character, with effects depending on room context and language skill levels.
     *
     * @details This function constructs a stylized, mystical version of a spell name by substituting parts of the spell's name with predefined syllables, creating an incantation effect. It then formats a message indicating the character uttering the spell. If the character is in a duel arena room, the message is broadcast to viewers in the room. The message is also sent to other characters in the same room, with visibility and response depending on their guild affiliation and language skill level. Characters with higher language skills are more likely to understand the incantation, potentially improving their language skill through the interaction.
     *
     * @param ch Pointer to the Character object who is casting or uttering the spell.
     * @param sn The skill::type enumeration value representing the spell being cast.
     * @return This function has no return value; it performs side effects by dispatching messages to characters in the game environment.
     */

  0.595  dispel_char                              — Dispel a list of spells from a character using dispel magic or cancell
    /**
     * @fn bool dispel_char(Character *victim, int level, bool cancellation)
     *
     * @brief Dispel a list of spells from a character using dispel magic or cancellation.
     *
     * @details Attempts to dispel all effects of specified types from a character based on dispel level and cancellation status.
    This function attempts to dispel multiple spell affects from the specified victim character based on the provided level and whether the dispel is a cancellation. It iterates through a predefined dispel table, applying dispel or cancellation logic depending on the 'cancellation' flag. The function returns true if any affects of the spells were successfully dispelled or canceled; otherwise, it returns false.
     *
     * @param victim Pointer to the Character object from whom effects are to be dispelled or canceled.
     * @param level The dispel or cancellation level influencing success chances.
     * @param cancellation Boolean indicating whether the operation is a cancellation (true) or a dispel (false).
     * @return A boolean value indicating whether any effects of the specified types were successfully dispelled or canceled (true) or not (false).
     */

  0.589  saves_spell                              — Computes whether a character successfully makes a saving throw against
    /**
     * @fn bool saves_spell(int level, Character *victim, int dam_type)
     *
     * @brief Computes whether a character successfully makes a saving throw against a spell.
     *
     * @details Determines if a character successfully saves against a spell.
    This function calculates the probability of a character (victim) successfully making a saving throw against a spell cast by another character. The saving throw is influenced by the level difference between the victim and the spell caster, the victim's saving throw attributes, and any active affects such as berserk. Additionally, the victim's defense modifier against the specific damage type of the spell is considered. The final computed chance is clamped between 5% and 95% before determining if the saving throw is successful.
     *
     * @param level The level of the spell caster, used to calculate the level difference for the save chance.
     * @param victim A pointer to the Character object representing the target of the spell, whose save chance is being calculated.
     * @param dam_type The type of damage the spell inflicts, used to determine the victim's defense modifier.
     * @return Returns true if the character successfully saves against the spell, otherwise returns false.
     */

  0.577  comp_spells                              — Compares two spells for sorting by level and name.
    /**
     * @fn int comp_spells(const void *sn1, const void *sn2)
     *
     * @brief Compares two spells for sorting by level and name.
     *
     * @details This function is used as a comparison function for sorting spells using qsort. It first compares the spells based on their level. If the levels are different, it returns the difference, allowing spells to be sorted by level in ascending order. If the levels are the same, it compares the names of the spells lexicographically using the skill::lookup function to retrieve the skill names, ensuring spells with the same level are sorted alphabetically by name.
     *
     * @param sn1 A pointer to the first spell information structure to compare.
     * @param sn2 A pointer to the second spell information structure to compare.
     * @return An integer less than, equal to, or greater than zero if the first spell is found, respectively, to be less than, to match, or be greater than the second spell based on level and name.
     */

  0.560  chain_spell                              — Executes a chain spell that damages multiple targets in sequence, with
    /**
     * @fn void chain_spell(Character *ch, void *vo, skill::type sn, int type, int level)
     *
     * @brief Executes a chain spell that damages multiple targets in sequence, with visual and message effects for each rebound.
     *
     * @details This function initiates a chain spell effect originating from the caster character, dealing initial damage to a primary victim, then attempting to rebound to additional valid targets within the caster's room based on game safety and group rules. Damage is calculated based on the spell level and predefined damage values, with saving throws reducing damage. The spell continues rebounding until the level diminishes below or no valid targets are found, or it rebounds back to the caster, at which point appropriate messages are displayed. The function manages messaging, damage application, and target selection, simulating a multi-target chain effect with visual cues.
     *
     * @param ch Pointer to the Character casting or initiating the spell.
     * @param vo Pointer to the initial target Character of the spell.
     * @param sn The skill::type identifier for the spell being cast.
     * @param type Integer index selecting the specific chain spell configuration from the table.
     * @param level The spell level, influencing damage and chain length.
     * @return This function has no return value; it performs side effects including message dispatch and damage application.
     */


================================================================================
[domain] clans  (stability: stable)
  desc: Clan organisation system: membership checks, clan power and score computation, inter-clan war initiation, joining, resol…
  locked: 30 functions, 30 with embeddings
  sim to desc — mean: 0.599  min: 0.424  max: 0.733

  0.733  war_join                                 — Adds a clan to a war as either a challenger or defender.
    /**
     * @fn void war_join(Clan *clan, War *war, bool challenger)
     *
     * @brief Adds a clan to a war as either a challenger or defender.
     *
     * @details The function war_join assigns a clan to a war, either as a challenger or a defender, based on the challenger flag. It first checks for an available slot in the respective list (challengers or defenders) within the war. If the clan's score is zero or negative, it calculates the clan's power using calc_cp with curvature adjustment. The clan's details are then recorded in the appropriate slot, marking them as participating in the war and initializing their scores.
     *
     * @param clan A pointer to a Clan object representing the clan to be added to the war.
     * @param war A pointer to a War object representing the war to which the clan is being added.
     * @param challenger A boolean flag indicating whether the clan is joining as a challenger (true) or a defender (false).
     * @return This function does not return a value.
     */

  0.722  war_power_adjust                         — Adjusts the power of a clan based on ongoing wars and events.
    /**
     * @fn void war_power_adjust(Clan *vclan, bool surrender)
     *
     * @brief Adjusts the power of a clan based on ongoing wars and events.
     *
     * @details This function recalculates and adjusts the power of a specified clan, 'vclan', based on its involvement in ongoing wars. It processes events related to score adjustments and redistributes power and clan quest points (QP) accordingly. If the clan's power is reduced to zero, it announces the clan's wipeout to all players. The function also handles the redistribution of power and QP to other clans involved in the wars, based on their contributions to the score adjustments.
     *
     * @param vclan A pointer to the Clan object whose power is being adjusted.
     * @param surrender A boolean flag indicating whether the clan is surrendering, which affects the power loss calculation.
     * @return This function does not return a value.
     */

  0.691  clan_in_war                              — Checks if a clan is involved in a specified war.
    /**
     * @fn bool clan_in_war(Clan *clan, War *war, bool onlycurrent)
     *
     * @brief Checks if a clan is involved in a specified war.
     *
     * @details This function determines whether a given clan is a participant in a specified war. It checks both the challengers and defenders of the war to see if the clan is listed among them. If 'onlycurrent' is true, the function only returns true if the clan is actively participating in the war at the moment.
     *
     * @param clan A pointer to the Clan object that is being checked for participation in the war.
     * @param war A pointer to the War object that contains the details of the war in question.
     * @param onlycurrent A boolean flag indicating whether to check only for current participation in the war.
     * @return Returns true if the clan is involved in the war, and false otherwise. If 'onlycurrent' is true, it returns true only if the clan is currently participating in the war.
     */

  0.691  war_start                                — Initiates a war between two clans.
    /**
     * @fn War * war_start(Clan *chal, Clan *def)
     *
     * @brief Initiates a war between two clans.
     *
     * @details This function starts a new war between a challenging clan and a defending clan. It initializes a new War object, sets up the initial conditions for both clans, and records the start of the war. If either clan's score is non-positive, it calculates the clan's power using the calc_cp function with curvature adjustment. The function then updates the War object with the names, clan names, and starting scores of both clans, marks them as participating in the war, and sets the war status to ongoing. An event is recorded to signify the start of the war, and the War object is appended to a list of ongoing wars.
     *
     * @param chal A pointer to the challenging Clan object.
     * @param def A pointer to the defending Clan object.
     * @return A pointer to the newly created War object representing the ongoing war between the two clans.
     */

  0.690  calc_cp                                  — Calculates the clan power based on various clan attributes.
    /**
     * @fn int calc_cp(Clan *clan, bool curve)
     *
     * @brief Calculates the clan power based on various clan attributes.
     *
     * @details Calculates the power of a clan.
    This function computes the power level of a given clan by considering the number of members, the clan's gold balance, quest points, and war combat power modifier. Optionally, the result can be adjusted using a curving algorithm to ensure it falls within a certain range. The calculation takes into account the number of members in the clan, dividing it by two, and adds contributions from the clan's gold balance, quest points, and war combat power modifier. If the 'curve' parameter is true, the function applies a curving algorithm to adjust the calculated power, ensuring it is not exactly 30 and is positive.
     *
     * @param clan A pointer to a Clan object for which the power is to be calculated.
     * @param curve A boolean flag indicating whether to apply a curvature adjustment to the calculated power.
     * @return The calculated power of the clan, potentially adjusted by a curvature factor if specified.
     */

  0.684  war_unjoin                               — Removes or updates a clan's participation in a war.
    /**
     * @fn void war_unjoin(Clan *clan, War *war, bool remove)
     *
     * @brief Removes or updates a clan's participation in a war.
     *
     * @details This function manages the participation of a given clan in a specified war. It checks if the clan is part of the challengers or defenders in the war. If the 'remove' flag is true, it erases the clan's name and clanname from the war records and sets its final score to zero. Otherwise, it updates the clan's final score to its current score. The function also marks the clan as not being in the war. If the clan is removed, the war state is reorganized using 'fix_war'. If the clan is no longer participating in any wars, its score is reset to zero.
     *
     * @param clan A pointer to the Clan object that is being removed or updated in the war.
     * @param war A pointer to the War object from which the clan is being removed or updated.
     * @param remove A boolean flag indicating whether the clan should be removed from the war (true) or just updated (false).
     * @return This function does not return a value.
     */

  0.684  defeat_clan                              — Handles the defeat of a clan in a war.
    /**
     * @fn void defeat_clan(War *war, Character *ch, Character *victim)
     *
     * @brief Handles the defeat of a clan in a war.
     *
     * @details This function processes the defeat of a clan within a given war. It updates the war state by marking the defeated clan as no longer participating and sets their final score to zero. It checks if any clans remain in the war and logs an event of the clan's defeat. If no clans are left, it logs a bug message and concludes the war with the specified winning character.
     *
     * @param war A pointer to the War object representing the ongoing war.
     * @param ch A pointer to the Character object representing the participant who defeated the clan.
     * @param victim A pointer to the Character object representing a member of the defeated clan.
     * @return This function does not return a value.
     */

  0.679  clan_at_war                              — Determines if a clan is currently engaged in any ongoing wars.
    /**
     * @fn bool clan_at_war(Clan *clan)
     *
     * @brief Determines if a clan is currently engaged in any ongoing wars.
     *
     * @details Determines if a clan is currently involved in any ongoing war.
    This function iterates through all wars in the global war table to check if the specified clan is actively participating in any ongoing war. It utilizes the 'clan_in_war' function to verify the clan's involvement in each war, considering only those wars that are currently ongoing. If the clan is found to be participating in any such war, the function returns true immediately. If no ongoing wars involve the clan, the function returns false.
     *
     * @param clan A pointer to the Clan object that is being checked for participation in any ongoing war.
     * @return Returns true if the clan is currently involved in any ongoing war, and false otherwise.
     */

  0.674  clan_opponents                           — Determines if two clans are opponents in an ongoing war.
    /**
     * @fn bool clan_opponents(Clan *clanA, Clan *clanB)
     *
     * @brief Determines if two clans are opponents in an ongoing war.
     *
     * @details This function checks if two specified Clan objects, clanA and clanB, are participating in the same ongoing war and are on opposing sides. It first finds an ongoing war involving both clans using the get_same_war function. If such a war is found, it then checks if one clan is a challenger and the other is not using the clan_is_challenger function. If the clans are on opposing sides, the function returns true; otherwise, it returns false.
     *
     * @param clanA A pointer to the first Clan object to check for participation and opposition in a war.
     * @param clanB A pointer to the second Clan object to check for participation and opposition in a war.
     * @return Returns true if both clans are participating in the same ongoing war and are on opposing sides (one is a challenger and the other is not). Returns false if they are not in the same war or are on the same side.
     */

  0.656  get_same_war                             — Finds an ongoing war involving both specified clans.
    /**
     * @fn War * get_same_war(Clan *clanA, Clan *clanB)
     *
     * @brief Finds an ongoing war involving both specified clans.
     *
     * @details This function searches through the list of ongoing wars to find a war in which both specified clans, clanA and clanB, are currently participating. It iterates through the war list starting from the head and checks each war to see if both clans are involved. If such a war is found, it returns a pointer to that War object. If the clans are the same or no such war is found, it returns nullptr.
     *
     * @param clanA A pointer to the first Clan object to check for participation in a war.
     * @param clanB A pointer to the second Clan object to check for participation in a war.
     * @return A pointer to the War object if both clans are found to be participating in the same ongoing war, or nullptr if no such war exists or if the clans are the same.
     */

  0.651  save_clan_table                          — Saves the current state of all clans to the database.
    /**
     * @fn void save_clan_table()
     *
     * @brief Saves the current state of all clans to the database.
     *
     * @details The function save_clan_table iterates over a linked list of clan objects and updates their state in the database. Initially, it sets all entries in the 'clans' table to have 'current' set to 0. For each clan in the list, it checks if the clan already exists in the database by counting entries with the same name. If the clan does not exist, it inserts a new entry with the clan's details. If the clan exists, it updates the existing entry with the current details of the clan, setting 'current' to 1.
     *
     * @return This function does not return a value.
     */

  0.651  war_kill                                 — Handles the event of a character killing another character in a war.
    /**
     * @fn void war_kill(Character *ch, Character *victim)
     *
     * @brief Handles the event of a character killing another character in a war.
     *
     * @details This function processes the event where one character kills another during an ongoing war between their respective clans. It first verifies that both characters are in clans that are currently at war with each other. It records the kill event and calculates the points to adjust the war score based on the rank difference between the killer and the victim. The score is adjusted accordingly, potentially affecting the outcome of the war.
     *
     * @param ch A pointer to the Character object representing the character who performed the kill.
     * @param victim A pointer to the Character object representing the character who was killed.
     * @return This function does not return a value.
     */

  0.649  war_stop                                 — Stops an ongoing war and updates the scores of participating clans.
    /**
     * @fn void war_stop(War *war)
     *
     * @brief Stops an ongoing war and updates the scores of participating clans.
     *
     * @details The function war_stop is responsible for terminating a war by setting its ongoing status to false. It iterates over the challengers and defenders involved in the war, checking if each clan's name is non-empty. For each valid clan, it uses clan_lookup to find the corresponding Clan object. If the clan was participating in the war, its final score is updated to reflect its current score. Additionally, if the clan is not involved in any other ongoing wars, its score is reset to zero.
     *
     * @param war A pointer to the War object that is being stopped.
     * @return This function does not return a value.
     */

  0.638  clan_is_challenger                       — Determines if a clan is a challenger in a given war.
    /**
     * @fn bool clan_is_challenger(Clan *clan, War *war)
     *
     * @brief Determines if a clan is a challenger in a given war.
     *
     * @details This function checks if the specified clan is a challenger in the provided war. It iterates through the list of challengers and defenders in the war to find a match with the given clan. If the clan is found among the challengers and is currently in the war, the function returns true. If the clan is found among the defenders and is in the war, it returns false. If the clan is not found in either list, it logs a bug message and returns false.
     *
     * @param clan A pointer to the Clan object to be checked.
     * @param war A pointer to the War object containing the list of challengers and defenders.
     * @return Returns true if the clan is a challenger in the war and is currently participating. Returns false if the clan is a defender or not found in the war.
     */

  0.635  war_win                                  — Handles the conclusion of a war with a victory.
    /**
     * @fn void war_win(War *war, Character *ch)
     *
     * @brief Handles the conclusion of a war with a victory.
     *
     * @details This function records the event of a war being won and then stops the ongoing war. It first logs the event using rec_event, indicating whether the winning character's clan was a challenger. After recording the event, it calls war_stop to finalize the war and update the scores of the participating clans.
     *
     * @param war A pointer to the War object that is being concluded.
     * @param ch A pointer to the Character object representing the winning participant.
     * @return This function does not return a value.
     */

  0.597  clan_vnum_lookup                         — Finds a clan by a given virtual number (vnum).
    /**
     * @fn Clan * clan_vnum_lookup(const Vnum &vnum)
     *
     * @brief Finds a clan by a given virtual number (vnum).
     *
     * @details Finds and returns the clan associated with a given virtual number (vnum).
    This function searches through the linked list of clans, starting from the node after 'clan_table_head' and ending at 'clan_table_tail'. It checks if the provided vnum falls within the range of area_minvnum and area_maxvnum for each clan. If a matching clan is found, it returns a pointer to that clan. If no matching clan is found, it returns nullptr.
     *
     * @param vnum The virtual number to look up, used to find the corresponding Clan within the specified area range.
     * @return A pointer to the Clan object whose area range includes the specified vnum, or nullptr if no such Clan exists.
     */

  0.578  is_clan                                  — Checks if a character belongs to a clan.
    /**
     * @fn bool is_clan(Character *ch)
     *
     * @brief Checks if a character belongs to a clan.
     *
     * @details This function determines whether the given character is part of a clan by checking if the 'clan' attribute of the Character object is not null. It is used to verify clan membership status.
     *
     * @param ch A pointer to the Character object whose clan membership is being checked.
     * @return Returns true if the character is part of a clan (i.e., the 'clan' attribute is not null), otherwise returns false.
     */

  0.563  count_clan_members                       — Counts the number of members in a specified clan with an optional role
    /**
     * @fn int count_clan_members(Clan *clan, int bit)
     *
     * @brief Counts the number of members in a specified clan with an optional role filter.
     *
     * @details This function constructs and executes a SQL query to count the number of members in a given clan. It optionally filters the count by a specific role within the clan, such as leader or deputy. The function first validates the role filter, constructs the SQL query with proper escaping to prevent SQL injection, and then executes the query to retrieve the count of members. If an error occurs during query execution, the function returns 0.
     *
     * @param clan A pointer to a Clan object representing the clan whose members are to be counted.
     * @param bit An integer representing a bitmask to filter members by specific roles. Valid values are 0, GROUP_LEADER, or GROUP_DEPUTY.
     * @return The number of members in the specified clan that match the optional role filter. Returns 0 if an error occurs or if the bitmask is invalid.
     */

  0.550  count_clans                              — Counts the number of clans in a linked list.
    /**
     * @fn int count_clans()
     *
     * @brief Counts the number of clans in a linked list.
     *
     * @details This function iterates through a linked list of Clan objects, starting from the node after 'clan_table_head' and ending before 'clan_table_tail'. It counts the number of Clan nodes in this list and returns the total count. The function assumes that 'clan_table_head' and 'clan_table_tail' are sentinel nodes that mark the boundaries of the list.
     *
     * @return The total number of clans in the linked list, represented as an integer.
     */

  0.537  fix_war                                  — Reorganizes and updates the state of a given war.
    /**
     * @fn void fix_war(War *war)
     *
     * @brief Reorganizes and updates the state of a given war.
     *
     * @details The function 'fix_war' takes a pointer to a War object and creates a new War object with reorganized participants and updated links in the war sequence. It filters out empty participants from both challengers and defenders, copying only those with non-empty names to the new War object. It also transfers the event history and updates the linked list pointers to maintain the sequence of wars. The original War object is deleted to free memory.
     *
     * @param war A pointer to the War object that needs to be fixed and reorganized.
     * @return This function does not return a value.
     */

  0.536  remove_clan                              — Removes a clan from the clan list by name.
    /**
     * @fn void remove_clan(const String &)
     *
     * @brief Removes a clan from the clan list by name.
     *
     * @details This function searches through a linked list of Clan objects, starting from the node after 'clan_table_head' and ending before 'clan_table_tail'. It performs a case-insensitive comparison of each clan's name with the provided 'name'. If a match is found, the clan is removed from the list by adjusting the pointers of the neighboring nodes and the clan object is deleted.
     *
     * @param name The name of the clan to be removed, compared in a case-insensitive manner.
     * @return This function does not return a value.
     */

  0.530  compare_clans                            — Compares two Clan objects by their names for sorting purposes.
    /**
     * @fn int compare_clans(const void *p1, const void *p2)
     *
     * @brief Compares two Clan objects by their names for sorting purposes.
     *
     * @details This function is used to compare two Clan objects based on the lexicographical order of their names. It is intended to be used as a comparison function for sorting algorithms that require a function pointer, such as qsort. The function dereferences the void pointers to access the Clan objects and then uses the strcmp function to compare the names of the clans.
     *
     * @param p1 A pointer to the first Clan object to compare, passed as a void pointer.
     * @param p2 A pointer to the second Clan object to compare, passed as a void pointer.
     * @return An integer less than, equal to, or greater than zero if the name of the first Clan is found, respectively, to be less than, to match, or be greater than the name of the second Clan.
     */

  0.524  append_clan                              — Appends a Clan object to the end of a linked list of clans.
    /**
     * @fn void append_clan(Clan *)
     *
     * @brief Appends a Clan object to the end of a linked list of clans.
     *
     * @details This function adds a Clan object to the end of a doubly linked list, updating the necessary pointers to maintain the list's integrity. It assumes that the list has a sentinel node at the tail, referred to as 'clan_table_tail', which helps in managing the list boundaries. The function updates the 'previous' and 'next' pointers of the involved nodes to insert the new Clan object correctly.
     *
     * @param c A pointer to the Clan object that is to be appended to the list.
     * @return This function does not return a value.
     */

  0.517  clan_lookup                              — Finds a clan by its name prefix.
    /**
     * @fn Clan * clan_lookup(const String &name)
     *
     * @brief Finds a clan by its name prefix.
     *
     * @details Finds and returns a pointer to a clan with a name matching the given prefix.
    This function searches through a linked list of Clan objects to find the first clan whose name starts with the specified prefix. It begins the search from the head of the clan list and continues until it reaches the tail. If the provided name is empty, the function immediately returns nullptr. The search is case-insensitive and respects a minimum character requirement for the prefix match.
     *
     * @param name The String object representing the prefix to search for in the clan names.
     * @return A pointer to the Clan object whose name matches the given prefix, or nullptr if no such clan is found or if the input name is empty.
     */

  0.516  war_is_full                              — Checks if a side of the war is fully populated with participants.
    /**
     * @fn bool war_is_full(War *war, bool challenger)
     *
     * @brief Checks if a side of the war is fully populated with participants.
     *
     * @details This function determines whether all slots for either the challenger's or defender's side in a war are filled. It iterates through the list of participants for the specified side and checks if any participant's name is empty. If any name is empty, the function returns false, indicating that the side is not fully populated. Otherwise, it returns true.
     *
     * @param war A pointer to the War object containing the participants' information.
     * @param challenger A boolean indicating which side to check; true for the challenger's side, false for the defender's side.
     * @return Returns true if all slots on the specified side are filled with participants, false otherwise.
     */

  0.507  rec_event                                — Records an event in the specified war.
    /**
     * @fn void rec_event(War *war, int type, const String &astr, const String &bstr, int number)
     *
     * @brief Records an event in the specified war.
     *
     * @details This function creates a new event for a given war and appends it to the list of existing events. It initializes the event with the provided type, strings, and number, and sets the event time to the current game time. If the war has no prior events, this new event becomes the first in the list. After adding the event, it saves all war events to individual files.
     *
     * @param war A pointer to the War object where the event will be recorded.
     * @param type An integer representing the type of the event.
     * @param astr A string representing the first participant or detail of the event.
     * @param bstr A string representing the second participant or detail of the event.
     * @param number An integer representing a numerical detail of the event, such as a count or identifier.
     * @return This function does not return a value.
     */

  0.496  war_lookup                               — Retrieves a war from the list by its sequential number.
    /**
     * @fn War * war_lookup(int number)
     *
     * @brief Retrieves a war from the list by its sequential number.
     *
     * @details This function searches through a linked list of War objects, starting from the head of the list, and returns the War object that corresponds to the specified sequential number. The search is performed by iterating through the list and counting each War object until the specified number is reached. If the specified number is greater than the number of War objects in the list, the function returns nullptr.
     *
     * @param number The sequential number of the War object to retrieve from the list.
     * @return A pointer to the War object corresponding to the specified number, or nullptr if no such War object exists.
     */

  0.488  Room::clan                               — Retrieves the clan associated with the room.
    /**
     * @fn const Clan * Room::clan() const
     *
     * @brief Retrieves the clan associated with the room.
     *
     * @details This function returns a pointer to the Clan object that is associated with the current room instance. It accesses the clan information from the room's prototype, providing a way to determine the clan affiliation of the room within the game's context.
     *
     * @return A pointer to a Clan object representing the clan associated with the room. If the room has no associated clan, the return value may be null.
     */

  0.470  get_war_index                            — Retrieves the index of a specific War instance in the war list.
    /**
     * @fn int get_war_index(War *war)
     *
     * @brief Retrieves the index of a specific War instance in the war list.
     *
     * @details This function searches through a linked list of War instances, starting from the node following 'war_table_head' and ending at 'war_table_tail'. It returns the 1-based index of the specified War instance within this list. If the War instance is not found, the function returns -1.
     *
     * @param war A pointer to the War instance whose index is to be found in the list.
     * @return The 1-based index of the specified War instance if found; otherwise, -1 if the instance is not in the list.
     */

  0.424  append_war                               — Appends a War object to the end of a doubly linked list.
    /**
     * @fn void append_war(War *war)
     *
     * @brief Appends a War object to the end of a doubly linked list.
     *
     * @details This function inserts a War object into a doubly linked list, positioning it just before the tail sentinel node. It updates the pointers of the War object and the surrounding nodes to maintain the list's integrity.
     *
     * @param war A pointer to the War object to be appended to the list.
     * @return This function does not return a value.
     */


================================================================================
[domain] affects  (stability: stable)
  desc: Affect lifecycle management: applying, joining, and copying affects to characters, objects, and rooms; removing affects …
  locked: 88 functions, 88 with embeddings
  sim to desc — mean: 0.604  min: 0.386  max: 0.707

  0.707  affect::list_char                        — Retrieves the list of affects on a character.
    /**
     * @fn const Affect * affect::list_char(Character *ch)
     *
     * @brief Retrieves the list of affects on a character.
     *
     * @details This function returns a pointer to the first affect in the list of affects associated with the given character. It provides access to the character's current status effects or conditions.
     *
     * @param ch A pointer to the Character whose affects are to be retrieved.
     * @return A pointer to the first Affect in the character's list of affects, or nullptr if the character has no affects.
     */

  0.702  affect::list_room                        — Retrieves the list of affects associated with a room.
    /**
     * @fn const Affect * affect::list_room(Room *room)
     *
     * @brief Retrieves the list of affects associated with a room.
     *
     * @details This function returns a pointer to the first affect in the list of affects associated with the given room. It allows access to the affects that are currently applied to the room, which can be used to determine the room's current state or modify its behavior.
     *
     * @param room A pointer to the Room object whose affects are to be retrieved.
     * @return A pointer to the first Affect in the room's list of affects, or nullptr if the room has no affects.
     */

  0.697  affect::add_type_to_char                 — Adds an affect of a specified type to a character, handling duplicates
    /**
     * @fn void affect::add_type_to_char(Character *ch, ::affect::type type, int level, int duration, int evolution, bool permanent)
     *
     * @brief Adds an affect of a specified type to a character, handling duplicates and evolution levels.
     *
     * @details This function applies an affect of a given type to a character, modifying their attributes based on predefined rules. It searches through a static table of affect types and their corresponding attribute modifications. If the specified type is found, it creates an Affect object with the appropriate properties and applies it to the character using the join_to_char function. If the type is not found in the table, a bug is logged.
     *
     * @param ch A pointer to the Character object to which the affect is being added.
     * @param type The type of affect to be added, specified as an enumeration value.
     * @param level The level of the affect, influencing the strength of its effects.
     * @param duration The duration for which the affect will last.
     * @param evolution The evolution level of the affect, determining its cumulative behavior.
     * @param permanent A boolean indicating whether the affect is permanent.
     * @return This function does not return a value.
     */

  0.692  room_update                              — Updates all rooms by processing their affects.
    /**
     * @fn void room_update(void)
     *
     * @brief Updates all rooms by processing their affects.
     *
     * @details The function iterates over all rooms in all areas of the game world, processing the affects associated with each room. It first sorts the affects by duration and type to group similar affects together. It then checks for affects with a duration of zero and sends a message to the room if the affect is wearing off. After processing the messages, it removes affects with a duration of zero from the room. Finally, it iterates over the remaining affects to decrease their duration and potentially their level.
     *
     * @return This function does not return a value.
     */

  0.682  affect::remove_matching_from_char        — Removes matching affects from a character's affect list.
    /**
     * @fn void affect::remove_matching_from_char(Character *ch, comparator comp, const Affect *pattern)
     *
     * @brief Removes matching affects from a character's affect list.
     *
     * @details This function iterates over the list of affects applied to a character and removes those that match a specified pattern. It uses a comparator function to determine if an affect matches the pattern. The function modifies the character's attributes by applying or removing affects as necessary.
     *
     * @param ch A pointer to the Character object whose affects are being modified.
     * @param comp A comparator function used to determine if an affect matches the pattern. If null, all affects are considered matches.
     * @param pattern A pointer to an Affect object used as a pattern to match against affects in the character's list. If null, all affects are considered matches.
     * @return This function does not return a value.
     */

  0.681  affect::copy_flags_to_char               — Transforms a bitvector into a set of affects or defense modifiers for 
    /**
     * @fn void affect::copy_flags_to_char(Character *ch, char letter, Flags bitvector, bool permanent)
     *
     * @brief Transforms a bitvector into a set of affects or defense modifiers for a character.
     *
     * @details This function iterates over a Flags object representing a set of bit flags and applies corresponding affects or defense modifiers to a Character object. It initializes an Affect structure with the character's level, a default duration, evolution level, and permanence status. For each bit flag in the bitvector, it attempts to parse the flag into an affect using the parse_flags function. If successful, it applies the affect to the character. Special handling is applied when the letter parameter is 'A', which results in adding a type-specific affect to the character.
     *
     * @param ch A pointer to the Character object to which affects or defense modifiers are applied.
     * @param letter A character representing the type of affect to apply, influencing how affects are parsed and applied.
     * @param bitvector A Flags object representing the current set of bit flags to be transformed into affects.
     * @param permanent A boolean indicating whether the affects applied to the character are permanent.
     * @return This function does not return a value.
     */

  0.681  affect::fn_fade_spell                    — Decreases the duration and potentially the level of an affect over tim
    /**
     * @fn int affect::fn_fade_spell(Affect *node, void *data)
     *
     * @brief Decreases the duration and potentially the level of an affect over time.
     *
     * @details This function is used to simulate the fading of an affect over time. It decreases the duration of the affect by one if the duration is greater than zero and the affect type matches the specified type or is unspecified. Additionally, there is an 80% chance that the level of the affect will decrease by one if it is greater than zero, simulating the weakening of the affect's strength over time.
     *
     * @param node A pointer to the Affect object whose duration and level may be modified.
     * @param data A pointer to additional data that may specify the type of affect to be processed. If not null, it is expected to be a pointer to a fn_data_container_type containing the type.
     * @return Always returns 0, indicating the process should continue.
     */

  0.680  affect::join_to_char                     — Adds an affect to a character and removes duplicates.
    /**
     * @fn void affect::join_to_char(Character *ch, Affect *paf)
     *
     * @brief Adds an affect to a character and removes duplicates.
     *
     * @details This function applies a specified affect to a character by first removing any duplicate affects from the character's list of affects and then applying the new affect. It uses the dedup_in_list function to ensure that any existing affects that are duplicates of the new affect are removed and their effects are accumulated. After deduplication, the affect is applied to the character using the copy_to_char function.
     *
     * @param ch A pointer to the Character object to which the affect is being added.
     * @param paf A pointer to the Affect object that is being added to the character.
     * @return This function does not return a value.
     */

  0.679  affect::copy_to_char                     — Applies an affect to a character.
    /**
     * @fn void affect::copy_to_char(Character *ch, const Affect *aff_template)
     *
     * @brief Applies an affect to a character.
     *
     * @details This function applies a given affect to a character by first copying the affect to the character's list of affects and then modifying the character's attributes based on the affect. It uses the 'copy_to_list' function to insert the affect into the character's doubly linked list of affects and 'modify_char' to update the character's attributes.
     *
     * @param ch A pointer to the Character object to which the affect is being applied.
     * @param aff_template A constant pointer to the Affect object that serves as a template for the affect being applied to the character.
     * @return This function does not return a value.
     */

  0.678  affect_fn_dispel_char                    — Attempts to dispel an affect from a character based on various conditi
    /**
     * @fn int affect_fn_dispel_char(affect::Affect *node, void *data)
     *
     * @brief Attempts to dispel an affect from a character based on various conditions.
     *
     * @details This function evaluates whether a given affect on a character should be dispelled. It checks the type of the affect against the specified type in the dispel parameters. If the affect is not permanent and meets certain conditions based on the dispel level and saving throws, it marks the affect for dispelling and increments the dispel count. If the affect is not dispelled, its level is reduced by a random amount between 1 and 3.
     *
     * @param node A pointer to the affect::Affect object representing the affect to be evaluated for dispelling.
     * @param data A pointer to a dispel_params structure containing the parameters for the dispel operation, including the type of affect to dispel, the level of the dispel, whether a saving throw is required, and the target character.
     * @return Returns 0 after attempting to dispel the affect, indicating the function completed its operation.
     */

  0.675  affect::remort_affect_modify_char        — Modifies a character's attributes based on remort affects and bit flag
    /**
     * @fn void affect::remort_affect_modify_char(Character *ch, int where, Flags bitvector, bool fAdd)
     *
     * @brief Modifies a character's attributes based on remort affects and bit flags.
     *
     * @details This function applies or removes affects to a character's attributes based on a specified set of bit flags. It initializes an Affect structure with default values and determines the type of affect to apply based on the 'where' parameter. The function iterates over the bit flags, using 'parse_flags' to configure the Affect structure, and then applies or removes the affect using 'modify_char'. The process continues until all relevant bit flags have been processed.
     *
     * @param ch A pointer to the Character whose attributes are being modified.
     * @param where An integer indicating the type of affect to apply, which determines the affect category (e.g., resistance or vulnerability).
     * @param bitvector A Flags object representing the set of bit flags that dictate which affects to apply or remove.
     * @param fAdd A boolean indicating whether the affect is being added (true) or removed (false).
     * @return This function does not return a value.
     */

  0.667  affect::iterate_over_char                — Iterates over a character's affects and applies a function to each.
    /**
     * @fn void affect::iterate_over_char(Character *ch, affect_fn fn, void *data)
     *
     * @brief Iterates over a character's affects and applies a function to each.
     *
     * @details This function takes a character and iterates over its list of Affect objects, applying a specified function to each. It sets up the necessary parameters, including the character as the owner and the modify_char function as the modifier, before calling iterate_over_list to perform the iteration.
     *
     * @param ch A pointer to the Character whose affects are being iterated over.
     * @param fn A function pointer to be applied to each Affect object in the character's list.
     * @param data A pointer to additional data that may be used by the function applied to each Affect.
     * @return This function does not return a value.
     */

  0.667  affect::copy_to_room                     — Adds an affect to a room and updates the room's state.
    /**
     * @fn void affect::copy_to_room(Room *room, const Affect *aff_template)
     *
     * @brief Adds an affect to a room and updates the room's state.
     *
     * @details This function takes a room and an affect template, copies the affect into the room's list of affects, and updates the room's state to reflect the addition of the new affect. It first inserts the affect into the room's doubly linked list of affects and then modifies the room's state to account for the new affect.
     *
     * @param room A pointer to the Room object to which the affect will be added.
     * @param aff_template A constant pointer to the Affect object that serves as a template for the affect being added to the room.
     * @return This function does not return a value.
     */

  0.664  check_dispel_obj                         — Attempts to dispel affects on an object based on specified conditions.
    /**
     * @fn bool check_dispel_obj(int dis_level, Object *obj, affect::type type, bool save)
     *
     * @brief Attempts to dispel affects on an object based on specified conditions.
     *
     * @details Attempts to dispel affects of a specified type from an object.
    This function checks and attempts to dispel affects on a given object by iterating over its affect list. It uses the specified dispel level, affect type, and save flag to determine which affects should be marked for removal. If any affects are marked, they are removed from the object's affect list. The function returns true if any affects were dispelled, otherwise false.
     *
     * @param dis_level The level of the dispel operation, which influences the success of dispelling affects.
     * @param obj A pointer to the Object whose affects are to be checked and potentially dispelled.
     * @param type The type of affect to be targeted for dispelling.
     * @param save A boolean flag indicating whether a saving throw should be considered in the dispel operation.
     * @return Returns true if any affects were successfully marked and removed; otherwise, returns false.
     */

  0.662  undo_spell                               — Attempts to undo or dispel a specific affect of a given type from a ch
    /**
     * @fn bool undo_spell(int dis_level, Character *victim, affect::type type, bool save)
     *
     * @brief Attempts to undo or dispel a specific affect of a given type from a character if the affect is marked as undoable.
     *
     * @details Attempts to undo (remove) affects of a specified type from a character if permitted.
    This function checks whether the specified affect type can be undone by consulting the dispel table. If the affect type is found and marked as undoable, it proceeds to call check_dispel_char to attempt to dispel all affects of that type from the victim, considering the dispel level and saving throw. The function returns true if the dispel attempt was successful, indicating that the affects were removed; otherwise, it returns false. If the affect type is not found or not marked as undoable, no dispel attempt is made, and false is returned.
     *
     * @param dis_level The level of the dispel attempt, influencing the chance of success.
     * @param victim Pointer to the Character object from whom affects are to be potentially removed.
     * @param type The specific affect::type to be targeted for undoing.
     * @param save Boolean indicating whether to consider a saving throw during the dispel attempt.
     * @return A boolean value indicating whether any affects of the specified type were successfully dispelled (true) or not (false).
     */

  0.661  affect_fn_dispel_obj                     — Attempts to dispel an affect on an object based on certain conditions.
    /**
     * @fn int affect_fn_dispel_obj(affect::Affect *node, void *data)
     *
     * @brief Attempts to dispel an affect on an object based on certain conditions.
     *
     * @details This function checks if a given affect on an object can be dispelled. It compares the affect's type with the specified type in the parameters and ensures the affect is not permanent. If the affect's duration is indefinite, the dispel level is reduced. The function then determines if the affect can be dispelled based on the dispel level and a saving throw. If successful, the affect is marked for removal and a counter is incremented. Otherwise, the affect's level is reduced by a random amount between 1 and 3.
     *
     * @param node A pointer to the affect::Affect object representing the affect to be potentially dispelled.
     * @param data A pointer to a dispel_params structure containing the parameters for the dispel operation, including the type of affect, the level of the dispel, and a save flag.
     * @return Returns 0 after attempting to dispel the affect, indicating the function completed its operation.
     */

  0.660  affect::dedup_in_list                    — Removes duplicate affects from a list and accumulates their effects.
    /**
     * @fn void affect::dedup_in_list(Affect **list_head, Affect *paf, fn_params *params)
     *
     * @brief Removes duplicate affects from a list and accumulates their effects.
     *
     * @details This function iterates through a doubly linked list of Affect objects, removing any affects that have the same type, where, and location as the specified Affect object 'paf'. It accumulates the effects of these duplicate affects into 'paf', updating its level, duration, modifier, bitvector, and evolution attributes. The removed affects are deleted after their effects are accumulated.
     *
     * @param list_head A pointer to the head of the doubly linked list of Affect objects from which duplicates will be removed.
     * @param paf The Affect object into which the effects of duplicate affects will be accumulated.
     * @param params A pointer to an fn_params object that encapsulates additional parameters for the function, including a modifier function to be called for each removed affect.
     * @return This function does not return a value.
     */

  0.660  affect::sort_char                        — Sorts the list of Affect objects associated with a Character.
    /**
     * @fn void affect::sort_char(Character *ch, comparator comp)
     *
     * @brief Sorts the list of Affect objects associated with a Character.
     *
     * @details This function sorts the linked list of Affect objects that are associated with the given Character object. It uses a comparator function to determine the order of the Affect objects. The sorting is performed in-place, modifying the original list.
     *
     * @param ch A pointer to the Character whose list of Affect objects is to be sorted.
     * @param comp A comparator function used to determine the order of two Affect objects. It should return a positive value if the first object is greater than the second, zero if they are equal, and a negative value if the first is less than the second.
     * @return This function does not return a value.
     */

  0.658  affect::remove_all_from_char             — Removes all affects with a specified permanence from a character.
    /**
     * @fn void affect::remove_all_from_char(Character *ch, bool permanent)
     *
     * @brief Removes all affects with a specified permanence from a character.
     *
     * @details This function removes all affects from the specified character's affect list that match the permanence specified by the 'permanent' parameter. It constructs an Affect object with the 'permanent' attribute set to the provided value and uses it as a pattern to identify matching affects. The function then calls 'remove_matching_from_char' with a comparator function to remove all affects that match the pattern.
     *
     * @param ch A pointer to the Character object whose affects are to be modified.
     * @param permanent A boolean indicating whether to remove permanent affects (true) or non-permanent affects (false).
     * @return This function does not return a value.
     */

  0.657  affect::remove_marked_from_char          — Removes affects with a marked attribute from a character's affect list
    /**
     * @fn void affect::remove_marked_from_char(Character *ch)
     *
     * @brief Removes affects with a marked attribute from a character's affect list.
     *
     * @details This function creates a pattern Affect object with its mark attribute set to true. It then calls the remove_matching_from_char function, passing the character, a comparator function, and the pattern. The comparator function, comparator_mark, is used to identify affects in the character's list that have a matching mark attribute. All such affects are removed from the character's affect list.
     *
     * @param ch A pointer to the Character object whose affects are being modified.
     * @return This function does not return a value.
     */

  0.656  affect::join_to_obj                      — Integrates an Affect into an Object's affect list.
    /**
     * @fn void affect::join_to_obj(Object *obj, Affect *paf)
     *
     * @brief Integrates an Affect into an Object's affect list.
     *
     * @details This function first removes any duplicate affects from the specified object's affect list, accumulating their effects into the provided Affect object. It then adds the Affect to the object's affect list, updating the object's state accordingly. The function ensures that the object's affect list is both deduplicated and updated with the new Affect.
     *
     * @param obj A pointer to the Object whose affect list is being modified.
     * @param paf A pointer to the Affect object that is being added to the object's affect list.
     * @return This function does not return a value.
     */

  0.655  affect::modify_obj                       — Updates the state of an object's affect list.
    /**
     * @fn void affect::modify_obj(void *owner, const Affect *paf, bool fAdd)
     *
     * @brief Updates the state of an object's affect list.
     *
     * @details This function is invoked whenever there is a potential change to the list of affects associated with an object. It ensures that any caches or entities that depend on the affect list are updated accordingly. The function assumes that the 'owner->affected' already reflects the new state of the affects, meaning that the affect specified by 'paf' has already been added or removed from the list. The function then calls a more specific version of 'modify_obj' that operates on an 'Object' type.
     *
     * @param owner A pointer to the object whose affect list is being modified.
     * @param paf A pointer to the Affect that has been added or removed.
     * @param fAdd A boolean indicating whether the affect was added (true) or removed (false).
     * @return This function does not return a value.
     */

  0.653  affect::exists_on_char                   — Checks if a specific affect type exists on a character.
    /**
     * @fn bool affect::exists_on_char(const Character *ch, ::affect::type type)
     *
     * @brief Checks if a specific affect type exists on a character.
     *
     * @details This function determines whether a given affect type is present and active on a character by checking the character's affect cache. It utilizes the affect::in_cache function to verify if the specified affect type is cached for the character and has a positive value, indicating its presence.
     *
     * @param ch A pointer to the Character object whose affect status is being checked.
     * @param type The affect::type enumeration value representing the type of affect to check for existence on the character.
     * @return Returns true if the specified affect type is present and has a positive value in the character's cache, otherwise returns false.
     */

  0.653  affect::modify_room                      — Updates the room's state based on changes to its affects.
    /**
     * @fn void affect::modify_room(void *owner, const Affect *paf, bool fAdd)
     *
     * @brief Updates the room's state based on changes to its affects.
     *
     * @details This function is invoked whenever there is a potential change to the list of affects associated with a room. It ensures that any caches or entities dependent on the room's affects are updated accordingly. The function assumes that the 'owner->affected' list already reflects the new state, meaning the affect has already been added or removed from the list. The function then calls an overloaded version of 'modify_room' that operates specifically on Room objects.
     *
     * @param owner A pointer to the room object whose affects are being modified.
     * @param paf A pointer to the Affect object that is being added or removed.
     * @param fAdd A boolean flag indicating whether the affect is being added (true) or removed (false).
     * @return This function does not return a value.
     */

  0.652  affect::find_on_char                     — Finds an affect of a specified type on a character.
    /**
     * @fn const Affect * affect::find_on_char(Character *ch, ::affect::type type)
     *
     * @brief Finds an affect of a specified type on a character.
     *
     * @details This function searches through the list of affects associated with a given character to find the first affect that matches the specified type. It utilizes the affect::find_in_list function to perform the search on the character's list of affects.
     *
     * @param ch A pointer to the Character object whose affects are to be searched.
     * @param type The type of affect to search for in the character's list of affects.
     * @return A pointer to the first Affect object on the character that matches the specified type, or nullptr if no such Affect is found.
     */

  0.647  roll_raffects                            — Assigns multiple random remort affects to a character.
    /**
     * @fn void roll_raffects(Character *ch, Character *victim)
     *
     * @brief Assigns multiple random remort affects to a character.
     *
     * @details This function iterates over a calculated number of slots in the victim's remort affect array and assigns a random remort affect to each slot. The number of affects assigned is determined by dividing the victim's remort count by 10 and adding 1. It is assumed that the function is used in contexts where both ch and victim are player characters, with ch being an immortal character and victim being a character undergoing remort.
     *
     * @param ch A pointer to the Character object initiating the remort affect assignment.
     * @param victim A pointer to the Character object that will receive the remort affects.
     * @return This function does not return a value.
     */

  0.645  check_dispel_char                        — Attempts to dispel all affects of a specified type from a character ba
    /**
     * @fn bool check_dispel_char(int dis_level, Character *victim, affect::type type, bool save)
     *
     * @brief Attempts to dispel all affects of a specified type from a character based on dispel level and saving throw.
     *
     * @details Checks and attempts to dispel a specific affect from a character based on dispel level and saving throw.
    This function tries to remove all affects of a given type from the target character ('victim') by applying dispel logic with the specified dispel level ('dis_level') and save option ('save'). It initializes a set of parameters ('dispel_params') and invokes 'affect::iterate_over_char' with 'affect_fn_dispel_char' to mark affects for removal based on the dispel criteria. If any affects are marked (indicated by 'params.count' > 0), it proceeds to remove them from the character's affect list using 'affect::remove_marked_from_char'. After removal, if the affect type no longer exists on the character, it retrieves the corresponding table entry via 'affect::lookup' and sends appropriate messages to the room and the victim, if message strings are defined. The function returns true if any affects were dispelled, otherwise false.
     *
     * @param dis_level The level of the dispel attempt, influencing success chances.
     * @param victim Pointer to the Character object from whom the affect is to be dispelled.
     * @param type The affect::type enumeration value indicating which affect to dispel.
     * @param save Boolean indicating whether a saving throw is required for the dispel to succeed.
     * @return Returns true if an affect was successfully dispelled from the character; otherwise, false.
     */

  0.643  affect::print_cache                      — Generates a formatted string representing the affect cache of a charac
    /**
     * @fn String affect::print_cache(Character *ch)
     *
     * @brief Generates a formatted string representing the affect cache of a character.
     *
     * @details This function constructs a string that lists all affect types currently cached for a given character, along with their respective counts. It iterates through the character's affect cache and formats each non-zero entry using the affect type's name and count. If the character's affect cache is null, an empty string is returned.
     *
     * @param ch A pointer to the Character object whose affect cache is to be printed.
     * @return A String object containing the formatted list of affect types and their counts, or an empty string if the affect cache is null.
     */

  0.642  affect::modify_char                      — Updates character attributes based on an affect.
    /**
     * @fn void affect::modify_char(void *owner, const Affect *paf, bool fAdd)
     *
     * @brief Updates character attributes based on an affect.
     *
     * @details This function modifies the attributes of a character by applying or removing an affect. It ensures that any caches or entities dependent on the affect list are updated accordingly. The function assumes that the affect has already been added or removed from the character's affect list before being called. It is crucial for maintaining the integrity of the character's state.
     *
     * @param owner A pointer to the character whose attributes are being modified.
     * @param paf A pointer to the Affect object that is being applied or removed.
     * @param fAdd A boolean indicating whether the affect is being added (true) or removed (false).
     * @return This function does not return a value.
     */

  0.641  affect::add_perm_to_char                 — Adds a permanent affect of a specified type to a character.
    /**
     * @fn void affect::add_perm_to_char(Character *ch, ::affect::type type)
     *
     * @brief Adds a permanent affect of a specified type to a character.
     *
     * @details This function applies a permanent affect to a character by invoking the add_type_to_char function with specific parameters. The affect type is specified by the 'type' parameter, and it is applied at the character's current level. The affect is set to be permanent by passing 'true' for the 'permanent' parameter, and it has an evolution level of 1. The duration is set to -1 to indicate permanence.
     *
     * @param ch A pointer to the Character object to which the permanent affect is being added.
     * @param type The type of affect to be added, specified as an enumeration value from affect::type.
     * @return This function does not return a value.
     */

  0.639  affect::iterate_over_room                — Iterates over the affects of a room and applies a function to each.
    /**
     * @fn void affect::iterate_over_room(Room *room, affect_fn fn, void *data)
     *
     * @brief Iterates over the affects of a room and applies a function to each.
     *
     * @details This function traverses the linked list of Affect objects associated with a given Room object and applies a specified function to each Affect. It sets up the necessary parameters, including the room as the owner and the modify_room function as the modifier, and then calls iterate_over_list to perform the iteration and function application.
     *
     * @param room A pointer to the Room object whose affects are to be iterated over.
     * @param fn A function pointer to be applied to each Affect object in the room's affect list.
     * @param data A pointer to additional data that may be required by the function fn.
     * @return This function does not return a value.
     */

  0.638  affect::sort_room                        — Sorts the list of Affect objects in a Room.
    /**
     * @fn void affect::sort_room(Room *room, comparator comp)
     *
     * @brief Sorts the list of Affect objects in a Room.
     *
     * @details This function sorts the linked list of Affect objects associated with a given Room object. It uses a comparator function to determine the order of the Affect objects. The sorting is performed in-place on the list within the Room object.
     *
     * @param room A pointer to the Room object whose list of Affect objects is to be sorted.
     * @param comp A comparator function that determines the order of two Affect objects. It should return a positive value if the first object is greater than the second, zero if they are equal, and a negative value if the first is less than the second.
     * @return This function does not return a value.
     */

  0.634  rem_raff_affect                          — Removes remort affects from a character based on the affect index.
    /**
     * @fn void rem_raff_affect(Character *ch, int index)
     *
     * @brief Removes remort affects from a character based on the affect index.
     *
     * @details This function removes specific remort affects from a character by modifying their attributes. It checks the affect index to determine the type of affect to remove. If the affect ID is between 900 and 949, it removes a vulnerability affect. If the ID is between 950 and 999, it removes a resistance affect. The function uses the 'affect::remort_affect_modify_char' to apply these changes, passing 'false' to indicate the removal of affects.
     *
     * @param ch A pointer to the Character whose remort affects are being modified.
     * @param index An integer index used to access the specific remort affect from the 'raffects' array.
     * @return This function does not return a value.
     */

  0.632  affect::remove_matching_from_room        — Removes affects from a room that match a given pattern.
    /**
     * @fn void affect::remove_matching_from_room(Room *room, comparator comp, const Affect *pattern)
     *
     * @brief Removes affects from a room that match a given pattern.
     *
     * @details This function iterates over the list of affects associated with a given room and removes those that match a specified pattern. The matching is determined by a comparator function. If the comparator is null, all affects are considered matches. The function utilizes the 'remove_matching_from_list' function to perform the removal, and updates the room's state accordingly using the 'modify_room' function.
     *
     * @param room A pointer to the Room object from which matching affects will be removed.
     * @param comp A comparator function used to determine if an Affect matches the pattern. If null, all affects are considered matches.
     * @param pattern An Affect object used as a pattern to match against affects in the room's list. If null, all affects are considered matches.
     * @return This function does not return a value.
     */

  0.631  affect::remove_type_from_char            — Removes affects of a specific type from a character.
    /**
     * @fn void affect::remove_type_from_char(Character *ch, ::affect::type type)
     *
     * @brief Removes affects of a specific type from a character.
     *
     * @details This function removes all affects from a character's affect list that match a specified type. It creates a pattern Affect object with the given type and uses the remove_matching_from_char function with a comparator to identify and remove matching affects.
     *
     * @param ch A pointer to the Character object from which affects of the specified type will be removed.
     * @param type The specific type of affects to be removed from the character's affect list.
     * @return This function does not return a value.
     */

  0.629  affect::remove_matching_from_obj         — Removes matching Affect objects from an object's affect list.
    /**
     * @fn void affect::remove_matching_from_obj(Object *obj, comparator comp, const Affect *pattern)
     *
     * @brief Removes matching Affect objects from an object's affect list.
     *
     * @details This function removes Affect objects from the affect list of a specified object. It uses a comparator function to determine which affects match a given pattern. The function modifies the object's affect list by removing all matching affects. The modification is performed using the modify_obj function, which updates the state of the object's affect list accordingly.
     *
     * @param obj A pointer to the Object whose affect list is being modified.
     * @param comp A comparator function used to determine if an Affect matches the pattern. If null, all affects are considered matches.
     * @param pattern An Affect object used as a pattern to match against affects in the list. If null, all affects are considered matches.
     * @return This function does not return a value.
     */

  0.627  affect::iterate_over_obj                 — Iterates over an object's affect list and applies a function to each a
    /**
     * @fn void affect::iterate_over_obj(Object *obj, affect_fn fn, void *data)
     *
     * @brief Iterates over an object's affect list and applies a function to each affect.
     *
     * @details This function takes an object and iterates over its list of affects, applying a specified function to each affect in the list. It sets up the necessary parameters, including the owner object and a modifier function, and then calls 'iterate_over_list' to perform the iteration and function application.
     *
     * @param obj A pointer to the Object whose affect list will be iterated over.
     * @param fn A function pointer to be applied to each Affect object in the object's affect list.
     * @param data A pointer to additional data that will be passed to the function.
     * @return This function does not return a value.
     */

  0.627  affect::copy_to_obj                      — Adds an affect to an object's affect list.
    /**
     * @fn void affect::copy_to_obj(Object *obj, const Affect *aff_template)
     *
     * @brief Adds an affect to an object's affect list.
     *
     * @details This function copies an Affect object, specified by aff_template, into the affect list of the given object, obj. It first inserts the affect into the object's doubly linked list of affects using the copy_to_list function. Then, it updates the object's state to reflect the addition of the new affect by calling modify_obj with the fAdd parameter set to true.
     *
     * @param obj A pointer to the Object whose affect list is being modified.
     * @param aff_template A constant pointer to the Affect object that serves as a template for creating the new Affect to be added to the object's affect list.
     * @return This function does not return a value.
     */

  0.625  affect::parse_flags                      — Performs error checking and modifies an Affect struct based on a proto
    /**
     * @fn bool affect::parse_flags(char letter, Affect *paf, Flags &bitvector)
     *
     * @brief Performs error checking and modifies an Affect struct based on a prototype and bit flags.
     *
     * @details This function processes a character letter and a Flags bitvector to configure an Affect struct. It assigns the appropriate 'where' field based on the letter and modifies the bitvector accordingly. The function checks for specific conditions and logs errors if invalid states are encountered. It handles different cases for 'TO_OBJECT', 'TO_WEAPON', 'TO_AFFECTS', and 'TO_DEFENSE', adjusting the Affect's type, location, and modifier as needed. The function ensures that the Affect struct is valid for insertion by performing various checks and modifications.
     *
     * @param letter A character representing the type of affect to apply, which determines how the Affect struct is modified.
     * @param paf A pointer to an Affect struct that will be modified based on the letter and bitvector.
     * @param bitvector A Flags object representing the current set of bit flags, which will be modified during the function execution.
     * @return Returns true if the Affect struct is valid and ready for insertion; otherwise, returns false if an error is encountered during processing.
     */

  0.624  affect::list_obj                         — Retrieves the affect list associated with an object.
    /**
     * @fn const Affect * affect::list_obj(Object *obj)
     *
     * @brief Retrieves the affect list associated with an object.
     *
     * @details This function returns a pointer to the list of affects associated with the given object. It accesses the 'affected' member of the Object class, which is expected to hold a reference to an Affect or a list of Affect objects. The function assumes that the object has been properly initialized and that its 'affected' member is valid.
     *
     * @param obj A pointer to the Object whose affect list is to be retrieved.
     * @return A pointer to the Affect associated with the object, or nullptr if the object has no affects.
     */

  0.623  affect::remove_all_from_obj              — Removes all Affect objects with a specified 'permanent' attribute from
    /**
     * @fn void affect::remove_all_from_obj(Object *obj, bool permanent)
     *
     * @brief Removes all Affect objects with a specified 'permanent' attribute from an object's affect list.
     *
     * @details This function iterates over the affect list of the given object and removes all Affect objects that have a 'permanent' attribute matching the specified value. It utilizes the comparator_permanent function to compare the 'permanent' attribute of each Affect object in the list with the provided pattern. The function modifies the affect list of the object in place.
     *
     * @param obj A pointer to the Object whose affect list is being modified.
     * @param permanent A boolean value indicating the 'permanent' attribute value to match against when removing Affect objects.
     * @return This function does not return a value.
     */

  0.622  gem::compile_effects                     — Compiles and applies gem effects to an object.
    /**
     * @fn void gem::compile_effects(Object *eq)
     *
     * @brief Compiles and applies gem effects to an object.
     *
     * @details This function processes the gems attached to an object and applies their effects by modifying the object's affect list. If the object is currently worn, it logs a bug and exits early. Otherwise, it clears the existing affects on the object and iterates over each gem, creating a new affect based on the gem's properties, and adds it to the object's affect list.
     *
     * @param eq A pointer to the Object whose gem effects are to be compiled and applied.
     * @return This function does not return a value.
     */

  0.618  affect::in_cache                         — Checks if a specific affect type is present in the character's cache.
    /**
     * @fn bool affect::in_cache(const Character *ch, ::affect::type type)
     *
     * @brief Checks if a specific affect type is present in the character's cache.
     *
     * @details This function determines whether a given affect type is currently cached for a character. It checks if the affect type is valid and within the bounds of the cache size, and then verifies if the character's affect cache contains a positive value for that type.
     *
     * @param ch A pointer to the Character object whose affect cache is being checked.
     * @param type The affect::type enumeration value representing the type of affect to check in the cache.
     * @return Returns true if the specified affect type is cached for the character and has a positive value, otherwise returns false.
     */

  0.615  roll_one_raff                            — Assigns a random remort affect to a character.
    /**
     * @fn void roll_one_raff(Character *ch, Character *victim, int place)
     *
     * @brief Assigns a random remort affect to a character.
     *
     * @details This function selects a random remort affect from a predefined set and assigns it to a specified position in a victim character's remort affect array. The selection process involves generating random numbers and checking conditions based on the remort affect's ID and chance, as well as the victim's remort count. The function ensures that the selected affect is not already present in the victim's affects and does not belong to a group that the victim already has. If the character receiving the affect is different from the character initiating the function, a message is sent to both characters indicating the addition of the affect.
     *
     * @param ch A pointer to the Character object initiating the remort affect assignment.
     * @param victim A pointer to the Character object that will receive the remort affect.
     * @param place An integer representing the index in the victim's remort affect array where the new affect will be stored.
     * @return This function does not return a value.
     */

  0.613  affect::find_on_obj                      — Finds an affect of a specified type on a given object.
    /**
     * @fn const Affect * affect::find_on_obj(Object *obj, ::affect::type type)
     *
     * @brief Finds an affect of a specified type on a given object.
     *
     * @details This function searches for an affect of a specified type within the list of affects associated with a given object. It utilizes the affect::find_in_list function to traverse the linked list of affects starting from the object's 'affected' member. The function returns the first affect that matches the specified type, or nullptr if no matching affect is found.
     *
     * @param obj A pointer to the Object whose affects are to be searched.
     * @param type The type of affect to search for within the object's list of affects.
     * @return A pointer to the first Affect object on the given object that matches the specified type, or nullptr if no such Affect is found.
     */

  0.612  get_affect_evolution                     — Determines the highest evolution level of a specific affect type on a 
    /**
     * @fn int get_affect_evolution(Character *ch, affect::type type)
     *
     * @brief Determines the highest evolution level of a specific affect type on a character.
     *
     * @details Determines the highest evolution rating of a specified affect type on a character.
    This function iterates through the list of affects on a given character to find the highest evolution level of a specified affect type. It starts with a default evolution level of 1 and updates it if a higher evolution level is found for the specified affect type. The final evolution level is constrained between 1 and 3.
     *
     * @param ch A pointer to the Character whose affects are to be checked for evolution ratings.
     * @param type The specific affect type for which the evolution rating is being determined.
     * @return The highest evolution rating for the specified affect type on the character, clamped between 1 and 3.
     */

  0.612  affect::sort_obj                         — Sorts the list of Affect objects associated with an Object.
    /**
     * @fn void affect::sort_obj(Object *obj, comparator comp)
     *
     * @brief Sorts the list of Affect objects associated with an Object.
     *
     * @details This function sorts the linked list of Affect objects that are part of the specified Object. It uses a comparator function to determine the order of the Affect objects. The sorting is performed in-place on the list pointed to by the 'affected' member of the Object.
     *
     * @param obj A pointer to the Object whose list of Affect objects is to be sorted.
     * @param comp A comparator function used to determine the order of two Affect objects. It should return a positive value if the first object is greater than the second, zero if they are equal, and a negative value if the first is less than the second.
     * @return This function does not return a value.
     */

  0.610  affect::remove_marked_from_obj           — Removes marked Affect objects from an object's affect list.
    /**
     * @fn void affect::remove_marked_from_obj(Object *obj)
     *
     * @brief Removes marked Affect objects from an object's affect list.
     *
     * @details This function iterates over the affect list of the given object and removes all Affect objects that have their 'mark' attribute set to true. It uses the comparator_mark function to identify affects with the 'mark' attribute set to true, and the remove_matching_from_obj function to perform the removal.
     *
     * @param obj A pointer to the Object whose affect list will be modified by removing marked affects.
     * @return This function does not return a value.
     */

  0.610  raff_add_to_char                         — Adds a remort affect to a character based on a given affect ID.
    /**
     * @fn void raff_add_to_char(Character *ch, int raff_id)
     *
     * @brief Adds a remort affect to a character based on a given affect ID.
     *
     * @details This function attempts to add a remort affect to a character by looking up the affect ID in a predefined list of remort affects. If the affect ID is valid and the affect has associated attributes to add, it modifies the character's attributes accordingly. The function distinguishes between vulnerability and resistance affects based on the ID range and applies the appropriate modification.
     *
     * @param ch A pointer to the Character object to which the remort affect will be added.
     * @param raff_id An integer representing the remort affect ID to be added to the character.
     * @return This function does not return a value.
     */

  0.603  roll_mod                                 — Selects and applies a random affect modification to an object based on
    /**
     * @fn const String roll_mod(Object *obj, int eq_type, const std::multimap< int, affect::type > &mods_allowed)
     *
     * @brief Selects and applies a random affect modification to an object based on allowed types.
     *
     * @details The function roll_mod attempts to apply a random affect modification to the specified object. It first checks if there are any modifications allowed for the given equipment type (eq_type) by counting the entries in the mods_allowed multimap. If no modifications are allowed, it returns an empty string. Otherwise, it randomly selects a modification type from those allowed and checks if it can be applied based on its rarity. If successful, it creates an Affect object with properties derived from the selected modification and the object's level. The affect is then added to the object's affect list, ensuring no duplicate affects of the same type are applied. If the affect already exists, it is joined to the existing affect. The function returns a descriptive string of the applied modification.
     *
     * @param obj A pointer to the Object to which the affect modification will be applied.
     * @param eq_type An integer representing the equipment type for which modifications are being considered.
     * @param mods_allowed A multimap that maps equipment types to allowed affect types, used to determine which modifications can be applied to the object.
     * @return A String containing the description of the applied modification, or an empty string if no modification was applied.
     */

  0.603  spread_plague                            — Distributes a plague affect to characters in a room based on saving th
    /**
     * @fn void spread_plague(Room *room, const affect::Affect *plague, int chance)
     *
     * @brief Distributes a plague affect to characters in a room based on saving throws and chance.
     *
     * @details Distributes a plague affect to characters in a room based on chance and conditions.
    This function iterates through all characters present in the specified room and attempts to spread a plague affect to each. Characters are affected only if they fail a saving throw against the plague's level minus two, are not immortal, do not already have the plague affect, and a random chance check passes. When affected, characters receive a message indicating illness and are inflicted with a plague affect whose level and duration depend on the original plague's properties. The function ensures that only eligible characters are affected and respects the plague's level threshold.
     *
     * @param room Pointer to the Room object where the plague may spread.
     * @param plague Pointer to an affect::Affect object representing the plague to be spread.
     * @param chance An integer representing the chance factor; a random check is performed using number_bits(chance).
     * @return Void; the function performs side effects such as messaging and affect application without returning a value.
     */

  0.600  affect::exists_on_obj                    — Checks if an affect of a specified type exists on an object.
    /**
     * @fn bool affect::exists_on_obj(Object *obj, ::affect::type type)
     *
     * @brief Checks if an affect of a specified type exists on an object.
     *
     * @details This function determines whether an affect of the given type is present on the specified object. It utilizes the affect::find_on_obj function to search through the object's list of affects. If an affect of the specified type is found, the function returns true; otherwise, it returns false.
     *
     * @param obj A pointer to the Object whose affects are to be checked.
     * @param type The type of affect to search for within the object's list of affects.
     * @return A boolean value indicating whether an affect of the specified type exists on the object (true if it exists, false otherwise).
     */

  0.599  affect::remove_matching_from_list        — Removes matching Affect objects from a doubly linked list.
    /**
     * @fn void affect::remove_matching_from_list(Affect **list_head, comparator comp, const Affect *pattern, fn_params *params)
     *
     * @brief Removes matching Affect objects from a doubly linked list.
     *
     * @details This function iterates over a doubly linked list of Affect objects, removing those that match a specified pattern according to a comparator function. Permanent affects are not removed unless explicitly matched by a permanent pattern. For each removed Affect, a modifier function is called with the owner and the affect, and the affect is then deleted.
     *
     * @param list_head A pointer to the head of the doubly linked list of Affect objects.
     * @param comp A comparator function used to determine if an Affect matches the pattern. If null, all affects are considered matches.
     * @param pattern An Affect object used as a pattern to match against affects in the list. If null, all affects are considered matches.
     * @param params A structure containing parameters for the function, including a modifier function and an owner object.
     * @return This function does not return a value.
     */

  0.596  affect::enchanted_obj                    — Determines if an object is enchanted.
    /**
     * @fn bool affect::enchanted_obj(Object *obj)
     *
     * @brief Determines if an object is enchanted.
     *
     * @details This function checks whether an object is enchanted by comparing the checksum of its current affects with a precomputed checksum stored in its prototype data. It uses the affect::checksum_list function to calculate the checksum of the object's affects.
     *
     * @param obj A pointer to the Object structure whose enchantment status is being checked.
     * @return Returns true if the checksum of the object's affects does not match the stored checksum, indicating the object is enchanted. Returns false otherwise.
     */

  0.594  affect::comparator_permanent             — Compares the 'permanent' attribute of two Affect objects.
    /**
     * @fn int affect::comparator_permanent(const Affect *lhs, const Affect *rhs)
     *
     * @brief Compares the 'permanent' attribute of two Affect objects.
     *
     * @details This function takes two pointers to Affect objects and compares their 'permanent' attributes. It returns 0 if both attributes are equal, indicating that the 'permanent' status of both affects is the same. Otherwise, it returns 1, indicating a difference in the 'permanent' status.
     *
     * @param lhs A pointer to the first Affect object to be compared.
     * @param rhs A pointer to the second Affect object to be compared.
     * @return Returns 0 if the 'permanent' attributes of both Affect objects are equal, otherwise returns 1.
     */

  0.594  affect::checksum                         — Calculates a checksum for an Affect structure.
    /**
     * @fn unsigned long affect::checksum(const Affect *paf)
     *
     * @brief Calculates a checksum for an Affect structure.
     *
     * @details This function computes a checksum for the given Affect structure using Bernstein's djb2 algorithm. The checksum is calculated over the important parts of the Affect structure, excluding certain fields such as pointers to next and previous Affect objects. This checksum can be used to determine if two lists of Affect objects are different by comparing their checksums.
     *
     * @param paf A pointer to the Affect structure for which the checksum is to be calculated.
     * @return An unsigned long integer representing the checksum of the Affect structure.
     */

  0.594  affect::remove_type_from_obj             — Removes all affects of a specific type from an object's affect list.
    /**
     * @fn void affect::remove_type_from_obj(Object *obj, ::affect::type type)
     *
     * @brief Removes all affects of a specific type from an object's affect list.
     *
     * @details This function iterates over the affect list of the given object and removes all affects that match the specified type. It constructs a pattern Affect with the given type and uses the comparator_type function to identify matching affects, which are then removed from the object's list.
     *
     * @param obj A pointer to the Object from which affects of the specified type will be removed.
     * @param type The type of affects to be removed from the object's affect list.
     * @return This function does not return a value.
     */

  0.591  affect::add_racial_to_char               — Adds racial affects and modifiers to a character.
    /**
     * @fn void affect::add_racial_to_char(Character *ch)
     *
     * @brief Adds racial affects and modifiers to a character.
     *
     * @details This function applies a set of racial affects and defense modifiers to a character based on their race. It utilizes the 'copy_flags_to_char' function to transform and apply the affects, immunities, resistances, and vulnerabilities defined in the race_table for the character's race. All applied affects and modifiers are permanent.
     *
     * @param ch A pointer to the Character object to which racial affects and modifiers are applied.
     * @return This function does not return a value.
     */

  0.589  affect::iterate_over_list                — Iterates over a linked list of Affect objects and applies a function t
    /**
     * @fn void affect::iterate_over_list(Affect **list_head, affect_fn fn, fn_params *params)
     *
     * @brief Iterates over a linked list of Affect objects and applies a function to each.
     *
     * @details This function traverses a doubly linked list of Affect objects, temporarily unlinks each Affect from the list, applies a specified function to it, and then relinks it back into the list. During the process, if an owner is specified in the fn_params, a modifier function is called before and after the main function is applied. The main function, specified by the affect_fn parameter, is applied to each Affect object along with additional data from fn_params.
     *
     * @param list_head A pointer to the head of a linked list of Affect objects.
     * @param fn A function pointer to be applied to each Affect object in the list.
     * @param params A pointer to an fn_params structure containing additional parameters, including an owner and a modifier function.
     * @return This function does not return a value.
     */

  0.588  HAS_RAFF                                 — Checks if a character has a specific remort affect flag.
    /**
     * @fn bool HAS_RAFF(Character *ch, int flag)
     *
     * @brief Checks if a character has a specific remort affect flag.
     *
     * @details This function determines whether a given character has a specific remort affect flag set. It first checks if the flag is valid (greater than zero) and if the character is not an NPC. If both conditions are met, it iterates through the character's remort affects, which are determined by the character's remort count, to see if the specified flag is present.
     *
     * @param ch A pointer to the Character object being checked.
     * @param flag The remort affect flag to check for in the character's data.
     * @return Returns true if the character has the specified remort affect flag, otherwise returns false.
     */

  0.587  affect::comparator_duration              — Compares the duration of two Affect objects.
    /**
     * @fn int affect::comparator_duration(const Affect *lhs, const Affect *rhs)
     *
     * @brief Compares the duration of two Affect objects.
     *
     * @details This function takes two pointers to Affect objects and compares their duration attributes. It returns the difference between the duration of the first Affect object (lhs) and the duration of the second Affect object (rhs). This function can be used to sort or order Affect objects based on their duration.
     *
     * @param lhs A pointer to the first Affect object to compare.
     * @param rhs A pointer to the second Affect object to compare.
     * @return An integer representing the difference in duration between the two Affect objects. A positive value indicates that lhs has a longer duration than rhs, a negative value indicates that rhs has a longer duration than lhs, and zero indicates that both have the same duration.
     */

  0.584  fix_blank_raff                           — Fixes blank remort affects for a character.
    /**
     * @fn void fix_blank_raff(Character *ch, int start)
     *
     * @brief Fixes blank remort affects for a character.
     *
     * @details This function iterates through a character's remort affects, starting from a specified index, and removes any zero values except at the end of the list. It is intended for use with non-NPC characters that have undergone a remort process. The function shifts non-zero affects down the list to fill any gaps created by zero values, ensuring that only the last position may contain a zero.
     *
     * @param ch A pointer to the Character object whose remort affects are to be fixed.
     * @param start The starting index from which to begin checking and fixing remort affects, typically set to 0.
     * @return This function does not return a value.
     */

  0.578  affect_callback_weaken_bonewall          — Handles the weakening of a bone wall affect upon a hit.
    /**
     * @fn int affect_callback_weaken_bonewall(affect::Affect *node, void *null)
     *
     * @brief Handles the weakening of a bone wall affect upon a hit.
     *
     * @details This function is invoked when a bone wall affect is hit. It checks if the affect type is 'bone_wall'. If so, it decreases the duration of the affect by 1, ensuring it does not go below zero. Additionally, if the affect's level is greater than 5, it decrements the level by 1. The function ensures that only one bone wall affect is processed by returning 1.
     *
     * @param node A pointer to an affect::Affect object representing the affect to be processed.
     * @param null A placeholder parameter that is not used in this function.
     * @return Returns 1 to indicate that the processing of the bone wall affect should stop after one affect.
     */

  0.577  shock_effect                             — Applies a shock effect recursively to game entities such as rooms, cha
    /**
     * @fn void shock_effect(void *vo, int level, int dam, int target, int evolution)
     *
     * @brief Applies a shock effect recursively to game entities such as rooms, characters, and objects, causing damage and potential destruction.
     *
     * @details Applies a shock effect recursively to rooms, characters, and objects, causing damage and potential destruction.
    This function executes a shock effect on a specified target entity, which can be a room, character, or object. When targeting a room, it applies the effect to all contained objects. When targeting a character, it may cause muscle daze if the saving throw fails and recursively applies the effect to all items the character is carrying. When targeting an object, it determines if the object is protected or immune, calculates the chance of destruction based on level and damage, and if successful, destroys the object, potentially scattering its contents and gems, and recursively applies the effect to contained items. The function modifies game entities by inflicting damage, causing destruction, and triggering related effects, with no return value.
     *
     * @param vo Pointer to the target entity, which can be a Room, Character, or Object, depending on the target type.
     * @param level The level of the spell or effect, influencing the chance and severity of the shock.
     * @param dam The amount of damage inflicted by the shock effect.
     * @param target Integer indicating the type of target: room, character, or object.
     * @param evolution An integer parameter that may influence recursive effect strength or behavior.
     * @return This function has no return value; it performs side effects on game entities affected by the shock effect.
     */

  0.569  cold_effect                              — Applies a cold effect to a specified target, which can be a room, char
    /**
     * @fn void cold_effect(void *vo, int level, int dam, int target, int evolution)
     *
     * @brief Applies a cold effect to a specified target, which can be a room, character, or object, causing cold-related effects and damage.
     *
     * @details Applies a cold effect to a target, which can be a room, character, or object, causing various cold-related effects and damage.
    This function recursively applies a cold effect to the target entity based on its type. If the target is a room, it applies the effect to all objects within the room. If the target is a character, it applies a chilling touch, potentially inflicting a cold affect, reducing hunger, and propagating the effect to all objects carried by the character. If the target is an object, it may be destroyed or damaged based on probabilistic checks, with possible scattering of its contents and gems, and the effect propagates to contained objects. The function handles special protections such as 'sheen' and item-specific resistances, and manages the destruction and scattering of objects and their contents.
     *
     * @param vo A pointer to the target entity, which can be a Room, Character, or Object, depending on the target type.
     * @param level The level of the spell or effect, influencing the strength and chance calculations.
     * @param dam The damage value associated with the cold effect, affecting the severity of effects.
     * @param target An integer indicating the type of target: TARGET_ROOM, TARGET_CHAR, or TARGET_OBJ.
     * @param evolution The evolution level of the effect, influencing affect levels and damage scaling.
     * @return This function has no return value; it performs effects and modifications directly on the target entities and their contents.
     */

  0.567  affect::swap                             — Swaps the contents of two Affect objects.
    /**
     * @fn void affect::swap(Affect *a, Affect *b)
     *
     * @brief Swaps the contents of two Affect objects.
     *
     * @details This function swaps the contents of two Affect objects pointed to by the parameters. It first checks if either pointer is null and returns immediately if so. The swap is performed by copying the data from one Affect to a temporary Affect, then copying the data from the second Affect to the first, and finally copying the data from the temporary Affect to the second. The function also ensures that the 'next' and 'prev' pointers of the swapped Affect objects are correctly updated to maintain any list structure they may be part of.
     *
     * @param a A pointer to the first Affect object to be swapped.
     * @param b A pointer to the second Affect object to be swapped.
     * @return This function does not return a value.
     */

  0.565  affect::copy_to_list                     — Copies an Affect object and inserts it into a doubly linked list.
    /**
     * @fn void affect::copy_to_list(Affect **list_head, const Affect *aff_template)
     *
     * @brief Copies an Affect object and inserts it into a doubly linked list.
     *
     * @details This function creates a new Affect object by copying the attributes from a given Affect template. It initializes the new Affect's next and prev pointers to null, ensuring it is a standalone node. The function then inserts this new Affect into a doubly linked list by calling the insert_in_list function, updating the list head if necessary.
     *
     * @param list_head A pointer to the head of the doubly linked list of Affect objects. This pointer may be updated to point to the newly inserted Affect.
     * @param aff_template A constant pointer to the Affect object that serves as a template for creating the new Affect.
     * @return This function does not return a value.
     */

  0.556  enhance_blade                            — Enhances a weapon object with a specified affect if it meets certain c
    /**
     * @fn bool enhance_blade(Character *ch, Object *obj, affect::type type, int level, int evolution)
     *
     * @brief Enhances a weapon object with a specified affect if it meets certain conditions.
     *
     * @details This function applies a specified affect to a weapon object to enhance its properties, such as adding flaming, frost, vampiric, or shocking effects. It first verifies that the object is a weapon and is in the character's inventory (not worn or equipped). It then checks if the weapon already has any of the specified enhancement affects; if so, it aborts. If conditions are met, it initializes an affect structure with provided type, level, and evolution parameters, sets its duration based on a random percentile plus half the level, and applies it to the object. The function returns true if the enhancement is successfully applied, or false if any condition fails.
     *
     * @param ch Pointer to the Character attempting to enhance the weapon.
     * @param obj Pointer to the Object (weapon) to be enhanced.
     * @param type The affect::type indicating the specific enhancement effect to apply.
     * @param level Integer representing the level of the enhancement effect.
     * @param evolution Integer indicating the evolution state or variant of the affect.
     * @return Boolean value indicating whether the enhancement was successfully applied (true) or not (false).
     */

  0.552  affect::comparator_type                  — Compares two Affect objects based on their type.
    /**
     * @fn int affect::comparator_type(const Affect *lhs, const Affect *rhs)
     *
     * @brief Compares two Affect objects based on their type.
     *
     * @details This function compares the 'type' attribute of two Affect objects pointed to by lhs and rhs. It is used to determine the relative ordering of the two Affect objects based on their type values. The comparison is performed by checking if the type of lhs is less than, greater than, or equal to the type of rhs.
     *
     * @param lhs A pointer to the first Affect object to compare.
     * @param rhs A pointer to the second Affect object to compare.
     * @return Returns -1 if the type of lhs is less than the type of rhs, 1 if the type of lhs is greater than the type of rhs, and 0 if both types are equal.
     */

  0.551  check_cond                               — Checks and applies damage to an object based on character effects and 
    /**
     * @fn void check_cond(Character *ch, Object *obj)
     *
     * @brief Checks and applies damage to an object based on character effects and conditions, potentially destroying it.
     *
     * @details This function evaluates whether a given character can damage a specified object during combat. It first verifies that the character is not an immortal and that the object has a valid condition value. If the character has the 'sheen' affect, the function exits early, as sheen provides complete protection. Otherwise, it randomly determines whether damage is applied, with a 1 in 501 chance. If damage occurs, the object's condition is reduced, with additional damage if the character has the 'steel_mist' affect. When the object's condition drops to zero or below, it is destroyed, and appropriate messages are displayed, including scattering of contents and gems if the object is not in a duel arena. The function does not return a value but modifies the state of the object and possibly the game environment.
     *
     * @param ch Pointer to the Character object performing the action, used to check effects and display messages.
     * @param obj Pointer to the Object object being damaged and potentially destroyed.
     * @return This function does not return a value; it modifies the object's condition and may destroy the object.
     */

  0.549  affect::find_in_list                     — Finds an affect of a specified type in a linked list.
    /**
     * @fn const Affect * affect::find_in_list(Affect **list_head, ::affect::type type)
     *
     * @brief Finds an affect of a specified type in a linked list.
     *
     * @details This function searches through a linked list of Affect objects, starting from the head of the list, to find the first Affect that matches the specified type. The list is traversed using the 'next' pointer of each Affect object. If an Affect with the specified type is found, it is returned; otherwise, the function returns nullptr.
     *
     * @param list_head A pointer to the head of the linked list of Affect objects to be searched.
     * @param type The type of affect to search for in the list.
     * @return A pointer to the first Affect object in the list that matches the specified type, or nullptr if no such Affect is found.
     */

  0.548  poison_effect                            — Applies poison effects recursively to rooms, characters, and objects b
    /**
     * @fn void poison_effect(void *vo, int level, int dam, int target, int evolution)
     *
     * @brief Applies poison effects recursively to rooms, characters, and objects based on specified parameters.
     *
     * @details Applies poison effects to rooms, characters, and objects based on specified parameters.
    This function applies poison effects to various game entities depending on the target type. If the target is a room, it iterates through all objects in the room and applies poison effects to each object. If the target is a character, it attempts to apply poison to the character, considering saving throws and applying effects if successful, and also propagates poison to the character's equipment. If the target is an object, it determines whether the object can be poisoned based on its properties and chance calculations, then marks the object as poisoned accordingly. The function modifies the game state by adding poison effects and updating object states, but does not return a value.
     *
     * @param vo A pointer to the target entity, which can be a Room, Character, or Object, depending on the target parameter.
     * @param level The level of the poison effect, influencing the chance and severity of poisoning.
     * @param dam The damage value associated with the poison, affecting the poisoning probability.
     * @param target An integer indicating the type of target: TARGET_ROOM, TARGET_CHAR, or TARGET_OBJ.
     * @param evolution The evolution level of the poison, affecting its potency and effects.
     * @return This function does not return a value; it modifies the game state by applying poison effects to rooms, characters, and objects.
     */

  0.546  acid_effect                              — Applies acid effects recursively to game entities such as rooms, chara
    /**
     * @fn void acid_effect(void *vo, int level, int dam, int target, int evolution)
     *
     * @brief Applies acid effects recursively to game entities such as rooms, characters, and objects, causing damage and deterioration.
     *
     * @details Applies acid effects recursively to objects, characters, and rooms within the game environment.
    This function simulates acid damage within the game environment by applying effects to various entities depending on the target type. If the target is a room, it applies the effect to all objects on the floor. If the target is a character, it applies the effect to all items carried by the character, unless the character is immortal. If the target is an object, it calculates the chance of damage based on level, damage, and object properties, then potentially damages or destroys the object, including its contents and gems, with appropriate in-game messages. The function handles special protections like 'sheen' and item flags such as 'burn proof' or 'no purge'. It also manages the recursive application of effects to nested objects and their contents, simulating the corrosive nature of acid.
     *
     * @param vo Pointer to the target entity, which can be a Room, Character, or Object, depending on the target parameter.
     * @param level The level of the acid effect, influencing the severity and chance calculations.
     * @param dam The damage value associated with the acid effect, affecting the chance and extent of damage.
     * @param target Integer indicating the type of target: room, character, or object.
     * @param evolution An integer representing the evolution or stage of the effect, used for recursive damage scaling.
     * @return This function does not return a value; it modifies the state of game entities directly through side effects.
     */

  0.540  affect::remove_from_list                 — Removes an Affect from a doubly linked list.
    /**
     * @fn void affect::remove_from_list(Affect **list_head, Affect *paf)
     *
     * @brief Removes an Affect from a doubly linked list.
     *
     * @details This function removes a specified Affect object from a doubly linked list. It updates the pointers of the adjacent nodes to bypass the removed node, effectively unlinking it from the list. After removal, the pointers of the specified Affect are set to nullptr to indicate it is no longer part of the list.
     *
     * @param list_head A pointer to the head of the doubly linked list of Affect objects.
     * @param paf The Affect object to be removed from the list.
     * @return This function does not return a value.
     */

  0.540  fire_effect                              — Handles the fire effect on various targets such as rooms, characters, 
    /**
     * @fn void fire_effect(void *vo, int level, int dam, int target, int evolution)
     *
     * @brief Handles the fire effect on various targets such as rooms, characters, and objects, applying damage, effects, and potential destruction.
     *
     * @details This function applies a fire effect to a specified target, which can be a room, character, or object. When targeting a room, it recursively applies the effect to all objects within the room. When targeting a character, it may blind the character if they fail a saving throw, increases their thirst condition, and applies the effect to all items they carry. When targeting an object, it calculates the chance of ignition based on level and damage, possibly destroys the object, and if applicable, causes its contents and gems to scatter and be affected by the fire. The function also manages visual and game state effects such as acts and object extraction, simulating the destructive nature of fire.
     *
     * @param vo Pointer to the target entity, which can be a Room, Character, or Object, depending on the target parameter.
     * @param level The level of the spell or effect, influencing damage and chance calculations.
     * @param dam The amount of damage inflicted by the fire effect, affecting the severity of effects and destruction chances.
     * @param target An integer indicating the type of target: room, character, or object.
     * @param evolution The evolution level of the effect, influencing affect duration and intensity.
     * @return Void; the function performs effects and state modifications without returning a value.
     */

  0.538  affect::lookup                           — Retrieves the table entry associated with a given affect type.
    /**
     * @fn const table_entry & affect::lookup(::affect::type type)
     *
     * @brief Retrieves the table entry associated with a given affect type.
     *
     * @details This function searches for a table entry corresponding to the specified affect type within the affect_table. If the type is found, the associated table_entry is returned. If the type is not found, a bug report is logged, and the function returns the table entry for the 'unknown' affect type.
     *
     * @param type The affect type for which the table entry is to be retrieved.
     * @return A constant reference to the table_entry associated with the specified affect type, or the entry for 'unknown' if the type is not found.
     */

  0.534  affect::sort_list                        — Sorts a linked list of Affect objects using a comparator function.
    /**
     * @fn void affect::sort_list(Affect **list_head, comparator comp)
     *
     * @brief Sorts a linked list of Affect objects using a comparator function.
     *
     * @details This function performs a bubble sort on a linked list of Affect objects. It iterates through the list, comparing adjacent elements using the provided comparator function. If two adjacent elements are found to be out of order, their contents are swapped. The process repeats until the list is sorted. The function modifies the list in place and does not return a value.
     *
     * @param list_head A double pointer to the head of the linked list of Affect objects to be sorted.
     * @param comp A comparator function used to determine the order of two Affect objects. It should return a positive value if the first object is greater than the second, zero if they are equal, and a negative value if the first is less than the second.
     * @return This function does not return a value.
     */

  0.534  affect::comparator_mark                  — Compares two Affect objects based on their mark attribute.
    /**
     * @fn int affect::comparator_mark(const Affect *lhs, const Affect *rhs)
     *
     * @brief Compares two Affect objects based on their mark attribute.
     *
     * @details This function takes two pointers to Affect objects and compares their mark attributes. It returns an integer that indicates the relative ordering of the two objects based on the mark value. This is similar to how strcmp works for strings.
     *
     * @param lhs A pointer to the first Affect object to compare.
     * @param rhs A pointer to the second Affect object to compare.
     * @return An integer representing the difference between the mark attributes of the two Affect objects. A return value of 0 indicates that the marks are equal, a positive value indicates that the mark of lhs is greater than that of rhs, and a negative value indicates the opposite.
     */

  0.532  affect::checksum_list                    — Calculates a checksum for a list of Affect structures.
    /**
     * @fn unsigned long affect::checksum_list(Affect **list_head)
     *
     * @brief Calculates a checksum for a list of Affect structures.
     *
     * @details This function computes a checksum for a linked list of Affect structures. The checksum is calculated by iterating over each Affect in the list and summing their individual checksums, as determined by the affect::checksum function. The order of the Affect structures in the list does not affect the final checksum due to the properties of unsigned integer overflow, which makes the checksum insensitive to order.
     *
     * @param list_head A pointer to the head of a linked list of Affect structures.
     * @return An unsigned long integer representing the cumulative checksum of all Affect structures in the list.
     */

  0.519  affect::bit_to_type                      — Converts a bit flag to its corresponding affect type.
    /**
     * @fn ::affect::type affect::bit_to_type(Flags::Bit bit)
     *
     * @brief Converts a bit flag to its corresponding affect type.
     *
     * @details This function takes a bit flag from the Flags::Bit enumeration and maps it to the corresponding affect::type enumeration value. It uses a switch statement to determine the correct mapping. If the provided bit does not match any known flag, it logs a bug report using Logging::bugf and returns affect::type::none.
     *
     * @param bit A bit flag from the Flags::Bit enumeration representing a specific attribute or effect.
     * @return The corresponding affect::type enumeration value for the given bit flag, or affect::type::none if the bit flag is unrecognized.
     */

  0.514  check_protection_aura                    — Checks and applies protection aura effects on a victim based on the at
    /**
     * @fn void check_protection_aura(Character *ch, Character *victim)
     *
     * @brief Checks and applies protection aura effects on a victim based on the attacker's alignment and aura properties.
     *
     * @details This function evaluates whether the attacker character (ch), who is either evil or good, has an active protection aura (protection_evil or protection_good) on the victim character. If such an aura exists and its 'evolution' level meets certain thresholds, the function may trigger visual and gameplay effects such as shock or stun, with probabilities influenced by the aura's evolution level. The function also manages combat states like daze or wait, and dispatches contextual messages to involved characters to reflect the aura's impact.
     *
     * @param ch Pointer to the attacking Character object, used to determine alignment and trigger effects.
     * @param victim Pointer to the Character object being protected or affected by the aura.
     * @return Void; the function performs side effects including state changes and message dispatching without returning a value.
     */

  0.503  affect::clear_list                       — Recursively clears a linked list of Affect objects.
    /**
     * @fn void affect::clear_list(Affect **list_head)
     *
     * @brief Recursively clears a linked list of Affect objects.
     *
     * @details This function takes a pointer to the head of a linked list of Affect objects and recursively deletes each node in the list. It sets each node's pointer to null after deletion to ensure no dangling pointers remain. The function handles an empty list by returning immediately if the head is null.
     *
     * @param list_head A double pointer to the head of the linked list of Affect objects. It is modified to null after the list is cleared.
     * @return This function does not return a value.
     */

  0.498  affect::insert_in_list                   — Inserts an Affect object into a doubly linked list.
    /**
     * @fn void affect::insert_in_list(Affect **list_head, Affect *paf)
     *
     * @brief Inserts an Affect object into a doubly linked list.
     *
     * @details This function inserts a new Affect object, pointed to by 'paf', at the head of a doubly linked list. If the list already has elements, the function adjusts the pointers to maintain the list's integrity, ensuring that 'paf' becomes the new head. The list is updated such that 'paf' points to the previous head, and if the previous head had a predecessor, 'paf' is inserted between them.
     *
     * @param list_head A pointer to the head of the doubly linked list of Affect objects. This pointer is updated to point to the newly inserted Affect.
     * @param paf A pointer to the Affect object to be inserted into the list.
     * @return This function does not return a value.
     */

  0.497  affect::Affect::bitvector                — Returns a Flags object representing the current bitvector state.
    /**
     * @fn const Flags affect::Affect::bitvector() const
     *
     * @brief Returns a Flags object representing the current bitvector state.
     *
     * @details This function provides a way to access the internal bitvector state encapsulated within the object. It constructs and returns a Flags object initialized with the current value of the private member variable _bitvector. This allows external code to obtain a copy of the bitvector in a controlled manner.
     *
     * @return A Flags object initialized with the current value of the _bitvector member variable.
     */

  0.472  affect_loc_name                          — Returns a string representation of a location effect.
    /**
     * @fn String affect_loc_name(int location)
     *
     * @brief Returns a string representation of a location effect.
     *
     * @details Returns the ASCII name of an affect location based on its integer code.
    This function takes an integer representing a location effect and returns a corresponding string that describes the effect. It uses a switch statement to map predefined constants to their string representations. If the provided location does not match any known constants, it logs a bug message and returns "(unknown)".
     *
     * @param location An integer code representing the affect location to be converted to a string.
     * @return A String object containing the ASCII name of the affect location, or "(unknown)" if the location is not recognized.
     */

  0.433  affect_index_lookup                      — Finds the index of an affect table entry matching a given name prefix.
    /**
     * @fn int affect_index_lookup(const String &name, const std::vector< affect_table_type > &affect_table)
     *
     * @brief Finds the index of an affect table entry matching a given name prefix.
     *
     * @details This function searches through a vector of affect_table_type entries to find the first entry whose name starts with the same prefix as the provided name. The comparison is case-insensitive. If a match is found, the index of the matching entry is returned. If no match is found, the function returns -1.
     *
     * @param name The name prefix to search for in the affect table.
     * @param affect_table A vector of affect_table_type entries to search through.
     * @return The index of the first matching entry in the affect table, or -1 if no match is found.
     */

  0.387  raff_lookup                              — Finds the index of a raff based on its ID.
    /**
     * @fn int raff_lookup(int index)
     *
     * @brief Finds the index of a raff based on its ID.
     *
     * @details Finds the index of a raffect with a given ID.
    This function searches through an array of raffects to find a raff with a specified ID. It iterates over the raffects array starting from index 1 up to MAX_RAFFECTS. If a raff with the given ID is found, the function returns its index. If no such raff is found, or if the raff ID is null, the function returns 0.
     *
     * @param index The ID of the raffect to search for in the array.
     * @return The index of the raffect with the specified ID, or 0 if no such raffect is found.
     */

  0.386  affect::attr_location_check              — Checks if the given attribute location is valid and returns the corres
    /**
     * @fn int affect::attr_location_check(int location)
     *
     * @brief Checks if the given attribute location is valid and returns the corresponding constant.
     *
     * @details This function takes an integer representing an attribute location and checks it against a predefined set of valid attribute constants. If the location matches one of these constants, the function returns the corresponding constant value. If the location does not match any valid attribute, the function logs a bug report message and returns -1.
     *
     * @param location An integer representing the attribute location to be checked.
     * @return The function returns the corresponding constant value if the location is valid. If the location is invalid, it returns -1.
     */


================================================================================
[domain] pvp  (stability: stable)
  desc: Duel and arena mechanics: duel initiation, tracking, and kill resolution, arena setup and clearing, duel list management…
  locked: 6 functions, 6 with embeddings
  sim to desc — mean: 0.612  min: 0.550  max: 0.641

  0.641  get_duel                                 — Retrieves the duel associated with a character if valid.
    /**
     * @fn Duel * get_duel(Character *ch)
     *
     * @brief Retrieves the duel associated with a character if valid.
     *
     * @details Retrieves the duel associated with a given character.
    This function checks if the given character is involved in a valid duel. It verifies that the character is not an NPC, is in a room, and has a duel associated with their player data. It then checks the integrity of the duel, ensuring that both the challenger and defender are correctly set and that they are in the appropriate rooms within the arena. If any condition fails, the duel is removed and the function returns nullptr.
     *
     * @param ch A pointer to the Character object for which the duel is to be retrieved.
     * @return A pointer to the Duel object if the character is in a valid duel, otherwise null.
     */

  0.633  get_random_arena                         — Selects a random duel arena from the available arenas.
    /**
     * @fn Duel::Arena * get_random_arena()
     *
     * @brief Selects a random duel arena from the available arenas.
     *
     * @details This function iterates through a linked list of duel arenas, counting the total number of available arenas. It then uses the number_range function to select a random index within the range of available arenas. The function iterates through the list again to return the arena at the randomly selected index. If no arenas are available, it returns a null pointer.
     *
     * @return A pointer to a randomly selected Duel::Arena object, or nullptr if no arenas are available.
     */

  0.629  duel_kill                                — Handles the process of killing a victim in a duel, relocating involved
    /**
     * @fn void duel_kill(Character *victim)
     *
     * @brief Handles the process of killing a victim in a duel, relocating involved characters, and announcing the outcome.
     *
     * @details Handles the process of concluding a duel with a kill, relocating participants, announcing the outcome, and cleaning up duel data.
    This function manages the aftermath of a duel kill by removing both the challenger and victim from their current rooms, relocating them to their respective clan halls or a default altar if they lack a clan, retrieving and repositioning any pets associated with the duel participants from the arena, and broadcasting the duel result message. It also cleans up the duel data structure and persists the updated character states. The function assumes the victim is engaged in an ongoing duel and updates the game state accordingly.
     *
     * @param victim Pointer to the Character object who was killed in the duel, triggering the cleanup and relocation process.
     * @return Void; the function performs side effects such as moving characters, announcing results, and saving data, but does not return a value.
     */

  0.624  clear_arena                              — Clears all non-immortal characters from the specified duel arena.
    /**
     * @fn void clear_arena(Duel::Arena *arena)
     *
     * @brief Clears all non-immortal characters from the specified duel arena.
     *
     * @details This function iterates over all rooms within the specified duel arena's range of virtual numbers (vnums) and removes all non-immortal characters from them. It also clears non-immortal characters from the challenger and defender preparation rooms associated with the arena. The function utilizes the World singleton to access room data and checks each character's immortality status before extraction.
     *
     * @param arena A pointer to the Duel::Arena object representing the duel arena to be cleared of non-immortal characters.
     * @return This function does not return a value.
     */

  0.596  remove_duel                              — Removes a duel from the linked list and cleans up associated resources
    /**
     * @fn void remove_duel(Duel *c)
     *
     * @brief Removes a duel from the linked list and cleans up associated resources.
     *
     * @details This function removes a Duel object from a doubly linked list by adjusting the pointers of the adjacent Duel objects. It then iterates over the character list in the game world, setting the duel pointer to null for any non-NPC characters that are participating in the duel being removed. The function also clears the arena associated with the duel and deallocates the memory for the Duel object.
     *
     * @param c A pointer to the Duel object that is to be removed and deleted.
     * @return This function does not return a value.
     */

  0.550  append_duel                              — Appends a Duel to the end of the duel table.
    /**
     * @fn void append_duel(Duel *c)
     *
     * @brief Appends a Duel to the end of the duel table.
     *
     * @details This function inserts a Duel object at the end of a doubly linked list representing the duel table. It updates the pointers of the surrounding nodes to include the new Duel. Additionally, it sets the duel reference for both the challenger and defender involved in the Duel.
     *
     * @param c A pointer to the Duel object to be appended to the duel table.
     * @return This function does not return a value.
     */


================================================================================
[utility] flags  (stability: stable)
  desc: Bit-flag utility operations: testing, setting, and clearing individual bits, testing any/all/none-of predicates, flag-to…
  locked: 34 functions, 34 with embeddings
  sim to desc — mean: 0.637  min: 0.454  max: 0.759

  0.759  room_bit_name                            — Retrieves the names of set room bit flags.
    /**
     * @fn const String room_bit_name(const Flags &flags)
     *
     * @brief Retrieves the names of set room bit flags.
     *
     * @details This function takes a Flags object representing a set of room-related bit flags and returns a String containing the names of all the flags that are currently set. It utilizes the print_bit_names function to generate this list based on a predefined flag table, room_flags. If no flags are set, the function returns a String with the word 'none'.
     *
     * @param flags A Flags object that holds the current state of bit flags to be checked against the room_flags.
     * @return A String object containing the names of all set room flags, separated by spaces, or 'none' if no flags are set.
     */

  0.750  plr_bit_name                             — Retrieves the names of set player bit flags.
    /**
     * @fn const String plr_bit_name(const Flags &flags)
     *
     * @brief Retrieves the names of set player bit flags.
     *
     * @details Returns the ASCII names of set player flags.
    The function plr_bit_name takes a Flags object representing a set of player-related bit flags and returns a String containing the names of all flags that are currently set. It utilizes the print_bit_names function, passing a predefined flag table (pcdata_flags) and the provided Flags object to generate the output. This function is useful for obtaining a human-readable representation of the active player flags.
     *
     * @param flags A Flags object that contains the current state of player-related bit flags to be checked.
     * @return A String object containing the names of all set player flags, separated by spaces, or 'none' if no flags are set.
     */

  0.731  act_bit_name                             — Generates a string representation of active bit flags for a player or 
    /**
     * @fn const String act_bit_name(const Flags &flags, bool npc)
     *
     * @brief Generates a string representation of active bit flags for a player or NPC.
     *
     * @details The function act_bit_name constructs a string that lists the names of active bit flags for either a player or a non-player character (NPC). It uses the print_bit_names function to generate the list of active flags. If the npc parameter is true, the function prefixes the result with 'npc ' and uses the act_flags set; otherwise, it prefixes with 'player ' and uses the plr_flags set. This function is useful for debugging or displaying the current state of flags in a human-readable format.
     *
     * @param flags A Flags object that contains the current state of bit flags to be evaluated.
     * @param npc A boolean indicating whether the flags belong to a non-player character (true) or a player (false).
     * @return A String object containing the names of all active flags, prefixed by 'npc ' or 'player ', or 'none' if no flags are set.
     */

  0.723  wiz_bit_name                             — Generates a string of names for set bit flags in the Flags object.
    /**
     * @fn String wiz_bit_name(const Flags &flags)
     *
     * @brief Generates a string of names for set bit flags in the Flags object.
     *
     * @details Generates a string listing the names of set bit flags.
    The function iterates over a predefined table of bit flags and their corresponding names, checking each flag to see if it is set in the provided Flags object. If a flag is set, its name is appended to a buffer string, separated by spaces. The function returns a string containing the names of all set flags, or 'none' if no flags are set.
     *
     * @param flags A reference to a Flags object containing the set of bit flags to be checked.
     * @return A String object containing the names of the set bit flags, separated by spaces. Returns 'none' if no flags are set.
     */

  0.717  comm_bit_name                            — Retrieves the names of communication-related bit flags that are set.
    /**
     * @fn const String comm_bit_name(const Flags &flags)
     *
     * @brief Retrieves the names of communication-related bit flags that are set.
     *
     * @details Retrieves the names of communication bit flags that are set.
    This function takes a Flags object representing a set of bit flags and returns a String containing the names of all communication-related flags that are currently set. It utilizes the print_bit_names function to generate this list based on a predefined set of communication flags. If no flags are set, the function returns a String with the word 'none'.
     *
     * @param flags A Flags object representing the current state of bit flags to be checked against the communication flag table.
     * @return A String object containing the names of all set communication flags, separated by spaces, or 'none' if no flags are set.
     */

  0.709  part_bit_name                            — Generates a string of names for set bit flags.
    /**
     * @fn const String part_bit_name(const Flags &flags)
     *
     * @brief Generates a string of names for set bit flags.
     *
     * @details Generates a string of names for the set bit flags in a Flags object.
    The function part_bit_name takes a Flags object and returns a String containing the names of the bit flags that are currently set. It utilizes the print_bit_names function, passing a predefined set of flag configurations (part_flags) and the provided Flags object to determine which flags are set. The resulting string lists the names of these flags, separated by spaces, or returns 'none' if no flags are set.
     *
     * @param flags A Flags object used to determine which bit flags are currently set.
     * @return A String object containing the names of all set flags, separated by spaces, or 'none' if no flags are set.
     */

  0.701  cgroup_bit_name                          — Retrieves the names of set bit flags from a Flags object.
    /**
     * @fn const String cgroup_bit_name(const Flags &flags)
     *
     * @brief Retrieves the names of set bit flags from a Flags object.
     *
     * @details The function cgroup_bit_name takes a Flags object as input and uses the print_bit_names function to generate a string that lists the names of all bit flags that are currently set in the provided Flags object. It utilizes a predefined vector of flag_type objects, cgroup_flags, which contains the mapping of flag names to their respective bit positions. This function is useful for obtaining a human-readable representation of the active flags in a Flags object.
     *
     * @param flags A Flags object that contains the bit flags to be checked.
     * @return A String object containing the names of all set flags, separated by spaces, or 'none' if no flags are set.
     */

  0.700  cont_bit_name                            — Generates a string of names for set bit flags from a Flags object.
    /**
     * @fn const String cont_bit_name(const Flags &flags)
     *
     * @brief Generates a string of names for set bit flags from a Flags object.
     *
     * @details Generates a string listing the names of set bit flags from a predefined set.
    The function cont_bit_name takes a Flags object as input and utilizes the print_bit_names function to produce a String containing the names of all bit flags that are currently set within the provided Flags object. The names are derived from a predefined vector of flag_type objects, cont_flags, which associates each bit flag with a human-readable name. If no flags are set, the function returns a String with the word 'none'.
     *
     * @param flags A Flags object used to check which bit flags are currently set.
     * @return A String object containing the names of all set flags, separated by spaces, or 'none' if no flags are set.
     */

  0.692  __attribute__::bitvector                
    /**
     * @fn const Flags __attribute__::bitvector() const
     *
     */

  0.691  wear_bit_name                            — Retrieves the names of set wear bit flags.
    /**
     * @fn const String wear_bit_name(const Flags &flags)
     *
     * @brief Retrieves the names of set wear bit flags.
     *
     * @details This function calls the print_bit_names function with a predefined set of wear flags and the provided Flags object. It returns a String containing the names of all wear-related bit flags that are currently set in the Flags object. If no wear flags are set, it returns a String with the word 'none'.
     *
     * @param flags A Flags object used to check which wear bit flags are currently set.
     * @return A String object containing the names of all set wear flags, separated by spaces, or 'none' if no flags are set.
     */

  0.681  censor_bit_name                          — Generates a string of names for set bit flags related to censorship.
    /**
     * @fn const String censor_bit_name(const Flags &flags)
     *
     * @brief Generates a string of names for set bit flags related to censorship.
     *
     * @details This function utilizes the print_bit_names function to produce a string that lists the names of bit flags that are currently set in the provided Flags object, specifically for flags related to censorship. It uses a predefined set of flag definitions, censor_flags, to determine which flags are relevant. The resulting string will contain the names of all set flags, separated by spaces, or 'none' if no flags are set.
     *
     * @param flags A Flags object that contains the current state of bit flags to be checked against the censor_flags configuration.
     * @return A String object containing the names of all set censorship-related flags, separated by spaces, or 'none' if no such flags are set.
     */

  0.678  extra_bit_name                           — Generates a string of names for set bit flags from extra_flags.
    /**
     * @fn const String extra_bit_name(const Flags &flags)
     *
     * @brief Generates a string of names for set bit flags from extra_flags.
     *
     * @details Returns the names of set bit flags from the extra flags vector.
    The function extra_bit_name takes a Flags object as input and uses it to determine which bit flags are currently set in the extra_flags vector. It then calls the print_bit_names function to generate a String object containing the names of these set flags. If no flags are set, the function returns a String with the word 'none'. This function is useful for obtaining a human-readable representation of the active configuration options represented by the flags.
     *
     * @param flags A Flags object used to determine which bit flags are currently set.
     * @return A String object containing the names of all set flags from the extra_flags vector, separated by spaces, or 'none' if no flags are set.
     */

  0.676  form_bit_name                            — Generates a string of names for the set bit flags.
    /**
     * @fn const String form_bit_name(const Flags &flags)
     *
     * @brief Generates a string of names for the set bit flags.
     *
     * @details This function utilizes the print_bit_names function to create a string that lists the names of all bit flags currently set in the provided Flags object. It uses a predefined flag table, form_flags, to determine the names associated with each bit. If no flags are set, the function returns the string 'none'.
     *
     * @param flags A Flags object that contains the current state of bit flags to be checked.
     * @return A String object containing the names of all set flags, separated by spaces, or 'none' if no flags are set.
     */

  0.671  db_get_column_flags                      — Retrieves the flags for a database column at a specified index.
    /**
     * @fn const Flags db_get_column_flags(int index)
     *
     * @brief Retrieves the flags for a database column at a specified index.
     *
     * @details This function accesses the result set of a database query and retrieves the integer value of the column at the given index. It then constructs a Flags object using this integer value, which represents a set of bit flags associated with that column. The function is typically used to interpret metadata or status information stored as bit flags in a database column.
     *
     * @param index The zero-based index of the column in the database result set from which to retrieve the flags.
     * @return A Flags object representing the bit flags of the specified column in the database result set.
     */

  0.670  Room::flags                              — Retrieves the combined flags for the room.
    /**
     * @fn const Flags Room::flags() const
     *
     * @brief Retrieves the combined flags for the room.
     *
     * @details This function returns a Flags object that represents the combination of cached_room_flags and room_flags. It is used to obtain the current state of all flags associated with the room, taking into account both the cached and direct flag values.
     *
     * @return A Flags object representing the combined state of cached_room_flags and room_flags.
     */

  0.670  revoke_bit_name                          — Generates a string of names for revoked bit flags.
    /**
     * @fn const String revoke_bit_name(const Flags &flags)
     *
     * @brief Generates a string of names for revoked bit flags.
     *
     * @details This function calls the print_bit_names function with a predefined set of revoke_flags and the provided Flags object. It returns a String containing the names of all bit flags that are set within the revoke_flags context. If no flags are set, it returns 'none'. This function is useful for identifying which specific revoke-related flags are active in a given Flags object.
     *
     * @param flags A Flags object used to determine which bit flags are currently set.
     * @return A String object containing the names of all revoked flags that are set, separated by spaces, or 'none' if no such flags are set.
     */

  0.665  FLAGKEY                                 
    /**
     * @def FLAGKEY
     *
     */

  0.653  Flags::has                               — Checks if a specific bit flag is set.
    /**
     * @fn bool Flags::has(const Flags::Bit &b) const
     *
     * @brief Checks if a specific bit flag is set.
     *
     * @details This function determines whether a specific bit flag, represented by the enumeration Flags::Bit, is set in the current Flags object. It utilizes the has_all_of function to perform the check, ensuring that the specified bit is part of the current object's set bits.
     *
     * @param b A reference to a Flags::Bit enumeration value representing the bit flag to check.
     * @return Returns true if the specified bit flag is set in the current Flags object; otherwise, returns false.
     */

  0.639  print_bit_names                          — Generates a string listing the names of set bit flags.
    /**
     * @fn const String print_bit_names(const std::vector< flag_type > &flag_table, const Flags &flags)
     *
     * @brief Generates a string listing the names of set bit flags.
     *
     * @details This function iterates over a list of flag_type objects and checks each flag to see if it is set in the provided Flags object. If a flag is set, its name is appended to a buffer string. The function returns a string containing all the names of the set flags, separated by spaces. If no flags are set, it returns the string 'none'.
     *
     * @param flag_table A vector of flag_type objects, each representing a configuration option with a name and associated bit flag.
     * @param flags A Flags object used to check which bit flags are currently set.
     * @return A String object containing the names of all set flags, separated by spaces, or 'none' if no flags are set.
     */

  0.635  off_bit_name                             — Generates a string listing the names of bit flags that are set to off.
    /**
     * @fn const String off_bit_name(const Flags &flags)
     *
     * @brief Generates a string listing the names of bit flags that are set to off.
     *
     * @details This function utilizes the print_bit_names function to produce a string that contains the names of all bit flags that are currently set to off in the provided Flags object. It uses a predefined set of flags, off_flags, to determine which flags are considered. The resulting string lists the names of these flags, separated by spaces, or returns 'none' if no flags are set to off.
     *
     * @param flags A Flags object used to check which bit flags are currently set to off.
     * @return A String object containing the names of all flags that are set to off, separated by spaces, or 'none' if no flags are set to off.
     */

  0.617  Flags::has_all_of                        — Checks if all specified flags are set.
    /**
     * @fn bool Flags::has_all_of(const Flags &f) const
     *
     * @brief Checks if all specified flags are set.
     *
     * @details This function determines whether all the bits specified in the given Flags object 'f' are set in the current object. It performs a bitwise AND operation between the current object's bits and the bits of 'f', and checks if the result is equal to 'f.bits'. If so, it indicates that all the flags in 'f' are present in the current object.
     *
     * @param f A Flags object containing the bits to check against the current object's bits.
     * @return Returns true if all the bits in 'f' are set in the current object; otherwise, returns false.
     */

  0.614  MobProg::type_to_name                    — Converts a bit flag type to its corresponding program name.
    /**
     * @fn const String MobProg::type_to_name(Flags::Bit)
     *
     * @brief Converts a bit flag type to its corresponding program name.
     *
     * @details This function takes a Flags::Bit enumeration value representing a specific type of mobile program and returns a String containing the name of the program type. It maps various predefined bit flags to their respective string representations, which are used to identify different types of mobile programs in the system. If the provided bit flag does not match any known type, the function returns 'ERROR_PROG'.
     *
     * @param type The Flags::Bit enumeration value representing the type of mobile program.
     * @return A String containing the name of the program type corresponding to the given bit flag, or 'ERROR_PROG' if the type is unrecognized.
     */

  0.594  JSON::get_flags                          — Retrieves and sets flag values from a JSON object.
    /**
     * @fn void JSON::get_flags(cJSON *obj, Flags *target, const String &key)
     *
     * @brief Retrieves and sets flag values from a JSON object.
     *
     * @details This function searches for a JSON object item using a specified key and assigns the corresponding flag values to a target Flags object. It uses the key to locate the item within the JSON object 'obj'. If the item is found, the function initializes the 'target' Flags object with the string value of the JSON item.
     *
     * @param obj The JSON object from which to retrieve the flag values.
     * @param target A pointer to a Flags object where the retrieved flag values will be stored.
     * @param key The key string used to search for the corresponding JSON object item.
     * @return This function does not return a value.
     */

  0.592  ObjectValue::flags                       — Retrieves the flags associated with the object value.
    /**
     * @fn const Flags ObjectValue::flags() const
     *
     * @brief Retrieves the flags associated with the object value.
     *
     * @details This function returns a Flags object that represents the flags of the current object value. It encapsulates the internal state of the object in terms of its flags, allowing external code to query or manipulate these flags as needed.
     *
     * @return A Flags object constructed from the internal value of the object, representing its flags.
     */

  0.589  Flags::has_any_of                        — Checks if any of the specified flags are set.
    /**
     * @fn bool Flags::has_any_of(const Flags &f) const
     *
     * @brief Checks if any of the specified flags are set.
     *
     * @details This function determines whether any of the flags in the given Flags object 'f' are set in the current object. It performs a bitwise AND operation between the bits of the current object and the bits of 'f', and returns true if the result is non-zero, indicating that at least one flag is shared between the two objects.
     *
     * @param f A Flags object containing the flags to check against the current object's flags.
     * @return Returns true if at least one flag in 'f' is set in the current object; otherwise, returns false.
     */

  0.588  Flags::has_none_of                       — Checks if none of the specified flags are set.
    /**
     * @fn bool Flags::has_none_of(const Flags &f) const
     *
     * @brief Checks if none of the specified flags are set.
     *
     * @details This function determines whether none of the flags in the given Flags object 'f' are set in the current object. It performs a bitwise AND operation between the 'bits' of the current object and the 'bits' of 'f'. If the result is zero, it indicates that none of the flags in 'f' are set in the current object.
     *
     * @param f A Flags object containing the flags to check against the current object's flags.
     * @return Returns true if none of the flags in 'f' are set in the current object; otherwise, returns false.
     */

  0.570  Flags::to_string                         — Converts the Flags object to a string representation.
    /**
     * @fn const String Flags::to_string() const
     *
     * @brief Converts the Flags object to a string representation.
     *
     * @details This function iterates over the bits in the Flags object and constructs a string representation where each set bit is represented by a corresponding character. Bits 0-25 are mapped to 'A'-'Z', and bits 26-51 are mapped to 'a'-'z'. If no bits are set, the function returns '0'.
     *
     * @return A String object representing the set bits in the Flags object. If no bits are set, returns '0'.
     */

  0.566  Character::remove_cgroup                 — Removes a set of flags from a character's group flags.
    /**
     * @fn void Character::remove_cgroup(const Flags &cg)
     *
     * @brief Removes a set of flags from a character's group flags.
     *
     * @details This function removes the specified set of flags from the character's group flags if the character is not a non-player character (NPC). It checks if the character is a player character by verifying that 'pcdata' is not null. If the character is a player character, it subtracts the given flags from the character's current group flags.
     *
     * @param cg The set of flags to be removed from the character's group flags.
     * @return This function does not return a value.
     */

  0.562  Character::add_cgroup                    — Adds a set of flags to the character's group flags if the character is
    /**
     * @fn void Character::add_cgroup(const Flags &cg)
     *
     * @brief Adds a set of flags to the character's group flags if the character is a player.
     *
     * @details This function checks if the character is a player character (PC) by verifying that 'pcdata' is not null. If the character is a PC, it adds the specified set of flags, 'cg', to the character's existing group flags, 'cgroup_flags'. This operation is performed using the '+=' operator, which is assumed to be overloaded for the Flags class to handle the addition of flag sets.
     *
     * @param cg A constant reference to a Flags object representing the set of flags to be added to the character's group flags.
     * @return This function does not return a value.
     */

  0.537  RoomID::num_bits_vnum                    — Returns the number of bits used for a virtual number.
    /**
     * @fn int RoomID::num_bits_vnum() const
     *
     * @brief Returns the number of bits used for a virtual number.
     *
     * @details This inline member function returns a constant integer value representing the number of bits allocated for a virtual number in the system. It is a simple accessor that provides this fixed value, which is 16, indicating the bit-width used for certain operations or representations.
     *
     * @return An integer value of 16, representing the number of bits used for a virtual number.
     */

  0.533  Flags::clear                             — Clears all bits in the bitset.
    /**
     * @fn void Flags::clear()
     *
     * @brief Clears all bits in the bitset.
     *
     * @details This function resets all bits in the 'bits' bitset to 0. It effectively clears any set bits, ensuring that the bitset is in a default state with all bits turned off. This operation is useful when you need to reuse the bitset without any previous state.
     *
     * @return This function does not return a value.
     */

  0.527  Flags::empty                             — Checks if the bitset is empty.
    /**
     * @fn bool Flags::empty() const
     *
     * @brief Checks if the bitset is empty.
     *
     * @details This function determines whether all bits in the bitset are set to false. It returns true if none of the bits are set, indicating that the bitset is empty, and false otherwise.
     *
     * @return A boolean value: true if the bitset is empty (all bits are false), false otherwise.
     */

  0.520  flag_index_lookup                        — Finds the index of a flag in the flag table by its name.
    /**
     * @fn int flag_index_lookup(const String &name, const std::vector< flag_type > &flag_table)
     *
     * @brief Finds the index of a flag in the flag table by its name.
     *
     * @details This function searches through a vector of flag_type objects to find the index of a flag whose name matches the given name. The comparison is case-insensitive and checks if the provided name is a prefix of the flag's name. If a match is found, the index of the flag in the vector is returned. If no match is found, the function returns -1.
     *
     * @param name The name of the flag to search for, represented as a String object.
     * @param flag_table A vector of flag_type objects representing the available flags and their properties.
     * @return The index of the matching flag in the flag_table if found, otherwise -1.
     */

  0.454  Flags::to_ulong                          — Converts the stored bitset to an unsigned long integer.
    /**
     * @fn unsigned long Flags::to_ulong() const
     *
     * @brief Converts the stored bitset to an unsigned long integer.
     *
     * @details This function returns the value of the bitset as an unsigned long integer. It utilizes the to_ulong() method of the underlying bitset to perform the conversion. The function assumes that the bitset can be fully represented within the range of an unsigned long. If the bitset contains more bits than can be represented by an unsigned long, the behavior is undefined.
     *
     * @return An unsigned long integer representing the value of the bitset.
     */


================================================================================
[policy] visibility_rules  (stability: stable)
  desc: Visibility and perception checks: determining whether one character can see another (including in room, in WHO list), ob…
  locked: 10 functions, 10 with embeddings
  sim to desc — mean: 0.657  min: 0.513  max: 0.764

  0.764  can_see_in_room                          — Determines whether a character can see in a specific room based on var
    /**
     * @fn bool can_see_in_room(const Character *ch, const Room *room)
     *
     * @brief Determines whether a character can see in a specific room based on various conditions.
     *
     * @details Determines if a character can see characters and objects inside a specified room based on various visibility conditions.
    This function evaluates if the given character has visibility in the specified room by checking multiple conditions. It grants visibility unconditionally to immortal characters. For other characters, it denies visibility if the room is very dark, if the character is affected by blindness, or if the room is dark and the character lacks night vision. The function returns true if the character can see in the room under these conditions, and false otherwise.
     *
     * @param ch A pointer to the Character object representing the viewer whose visibility is being checked.
     * @param room A pointer to the Room object representing the environment in which visibility is being evaluated.
     * @return Returns true if the character can see inside the room, false if visibility is obstructed by darkness, blindness, or very dark conditions.
     */

  0.704  can_see_char                             — Determines if one character can see another character.
    /**
     * @fn bool can_see_char(const Character *ch, const Character *victim)
     *
     * @brief Determines if one character can see another character.
     *
     * @details This function evaluates various conditions to determine if the character 'ch' can see the character 'victim'. It checks for conditions such as whether the characters are the same, if 'ch' is an immortal or implementor, and if 'victim' has certain flags or affects that would make them invisible or hidden. The function also considers environmental factors like darkness and the presence of sneaking or hiding affects on 'victim'.
     *
     * @param ch A pointer to the Character object attempting to see the victim.
     * @param victim A pointer to the Character object whose visibility is being evaluated.
     * @return Returns true if the character (ch) can see the victim, otherwise returns false.
     */

  0.691  check_blind                              — Checks if a character can see, considering immortality and blindness.
    /**
     * @fn bool check_blind(Character *ch)
     *
     * @brief Checks if a character can see, considering immortality and blindness.
     *
     * @details This function determines whether a given character has the ability to see. It first checks if the character is immortal, in which case the character can always see, returning true. If the character is not immortal, it checks if the character is affected by any blindness-related conditions using the is_blinded function. If the character is blinded, it sends a message to the character indicating they can't see and returns false. Otherwise, it returns true, indicating the character can see.
     *
     * @param ch A pointer to the Character object whose ability to see is being checked.
     * @return Returns true if the character can see, either because they are immortal or not blinded. Returns false if the character is blinded and not immortal.
     */

  0.689  can_see_obj                              — Determines if a character can see a specific object.
    /**
     * @fn bool can_see_obj(const Character *ch, const Object *obj)
     *
     * @brief Determines if a character can see a specific object.
     *
     * @details This function evaluates multiple conditions to determine if a character, represented by 'ch', has the ability to see a given object, represented by 'obj'. The function checks for various states such as immortality, room darkness, blindness, object invisibility, and specific quest-related conditions. It also considers object attributes like visibility upon death, glow, and light emission. The function returns true if the character can see the object under the current conditions, otherwise it returns false.
     *
     * @param ch A pointer to the Character object whose ability to see the object is being evaluated.
     * @param obj A pointer to the Object that is being checked for visibility to the character.
     * @return Returns true if the character can see the object based on the evaluated conditions; otherwise, returns false.
     */

  0.678  can_see_who                              — Determines if a character can see another character in the 'who' list.
    /**
     * @fn bool can_see_who(const Character *ch, const Character *victim)
     *
     * @brief Determines if a character can see another character in the 'who' list.
     *
     * @details Determines if a character can see another character in the WHO list.
    This function checks various conditions to determine if the character 'ch' can see the character 'victim' in the 'who' list. It considers the victim's invisibility level, superuser status, and lurk level, as well as the relationship between the characters' rooms. The function ensures that non-immortal characters cannot see invisible or superuser characters unless certain conditions are met.
     *
     * @param ch The character attempting to see the victim in the WHO list.
     * @param victim The character whose visibility is being checked.
     * @return Returns true if the character ch can see the victim in the WHO list; otherwise, returns false.
     */

  0.677  can_see_room                             — Determines whether a character can see a specific room based on variou
    /**
     * @fn bool can_see_room(const Character *ch, const Room *room)
     *
     * @brief Determines whether a character can see a specific room based on various access restrictions and room flags.
     *
     * @details Determines if a character can see or enter a specific room.
    This function evaluates if a given character has permission to see or access a particular room within the game environment. It considers room flags such as 'IMP_ONLY', 'GODS_ONLY', 'REMORT_ONLY', 'HEROES_ONLY', 'NEWBIES_ONLY', 'LEADER_ONLY', as well as clan affiliations and character attributes like rank, level, gender, and group membership. The function grants access if the character meets all applicable restrictions, including special conditions for immortals and clan-related permissions, returning true if visibility is allowed, or false otherwise.
     *
     * @param ch A pointer to a Character object representing the character attempting to see or enter the room.
     * @param room A pointer to a Room object representing the room being evaluated for visibility or entry.
     * @return Returns true if the character is allowed to see or enter the room based on the evaluated conditions; otherwise, returns false.
     */

  0.640  is_blinded                               — Determines if a character is blinded by any affect.
    /**
     * @fn bool is_blinded(const Character *ch)
     *
     * @brief Determines if a character is blinded by any affect.
     *
     * @details Determines if a character is affected by any blindness-related conditions.
    This function checks if a character is blinded by evaluating several potential affect types. It first checks if the character is immortal, in which case they cannot be blinded, and returns false. If the character is not immortal, it checks for the presence of specific affect types related to blindness, such as blindness, dirt kicking, fire breath, smokescreen, and dazzle. If any of these affects are present on the character, the function returns true, indicating the character is blinded. Otherwise, it returns false.
     *
     * @param ch A pointer to the Character object whose blindness status is being evaluated.
     * @return Returns true if the character is affected by any blindness-related conditions, otherwise returns false.
     */

  0.607  Room::is_very_dark                       — Determines if the room is very dark.
    /**
     * @fn bool Room::is_very_dark() const
     *
     * @brief Determines if the room is very dark.
     *
     * @details This function checks if the room is considered very dark by verifying if the ROOM_NOLIGHT flag is set. If the flag is present, the room is deemed to have no light, and the function returns true. Otherwise, it returns false.
     *
     * @return Returns true if the ROOM_NOLIGHT flag is set, indicating the room is very dark; otherwise, returns false.
     */

  0.604  Room::is_dark                            — Determines if the room is dark.
    /**
     * @fn bool Room::is_dark() const
     *
     * @brief Determines if the room is dark.
     *
     * @details This function evaluates several conditions to determine if a room is considered dark. It first checks if the room is very dark using the is_very_dark() method. If true, the room is considered dark. If the room has any light, it is not dark. The function then checks if the room has the ROOM_DARK flag set in its flags. If so, the room is dark. It also considers the sector type of the room; if it is inside or in a city, the room is not dark. Finally, it checks the time of day from the Game's world instance; if it is nighttime, the room is dark. If none of these conditions are met, the room is not dark.
     *
     * @return Returns true if the room is considered dark based on various conditions, otherwise returns false.
     */

  0.513  Room::is_private                         — Determines if the room is private.
    /**
     * @fn bool Room::is_private() const
     *
     * @brief Determines if the room is private.
     *
     * @details This function checks if a room is considered private based on its owner and the number of characters present. A room is private if it has an owner or if it has specific flags set with a minimum number of characters present. Specifically, if the room has an owner, it is private. If the room has the ROOM_PRIVATE flag and at least two characters, it is private. If the room has the ROOM_SOLITARY flag and at least one character, it is private.
     *
     * @return A boolean value indicating whether the room is private. Returns true if the room is private, otherwise false.
     */

