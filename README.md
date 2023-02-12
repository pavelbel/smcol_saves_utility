# Sid Meier's Colonization (1994) SAV files utility pack

**Forewarning**: sorry for my english! Not a native speaker. Will be glad if someone makes pull requests to correct the text

The aim of this work is to make study and edit process of SAV files easy and comfortable. The ultimate goal is to fully describe SAV file structure, outline it in universal format and prepare utility pack for working with SAV files for enhancing the gameplay of this brilliant game.

## What is being done:
- (COMPLETE) outline the SAV file structure in easy readable and editable universal JSON format (_smcol_sav_struct.json_)
- (COMPLETE) utility *enc_decode_sav.py* for parsing binary SAV file data and saving it to human readable/editable JSON format
- (COMPLETE) the same utility for reading SAV file data FROM human readable/editable JSON format **and writing it back** to native SAV format (yes!)
- (IN DEVELOPMENT) utility for editing SAV files (certain fields such as: remove stokade, arm indian converts, plant forests etc)

## Utility _smcol_sav_editor.py_
== IN DEVELOPMENT ==

The utility to edit SAV files. __Warning__: this is not a cheat utility! It won't give you unlimited gold or turn all AI's ships to caravels (though you can do it all and much more with _enc_decode_sav.py_)! All changes it is supposed to make are relatively fair (in my opinion), much anticipated (like removinig of yout colonies' fortifications and planting forests) and refreshing for the gameplay (like arming indian converts or assimilating them)
Functionality:
* Plant forests
* Remove fortifications in colonies
* (IN DEVELOPMENT) Remove drydocks in colonies (if you don't want your ships to go there for repairs)
* (IN DEVELOPMENT) Increase warehouses capacity
* (IN DEVELOPMENT) Carrier growth for indian converts:
  * assimilate them as *Indentured Servants* (after several turns of work in a colony)
  * arm them with muskets and/or horses to fight by your side
* (IN DEVELOPMENT) Repair damaged artillery (half a cost of building)
* (IN DEVELOPMENT) Clean and plow tiles under AI's colonies (why doesn't AI do it?)

## Utility _enc_decode_sav.py_
Functionality:
* Read Colonization's native binary SAV files, decode them and save in a human readable/editable SAV.JSON format
* Encode SAV.JSON files back to binary SAV format

It means that you can decode your saved game file, then easily edit the generated SAV.JSON file without HEX editor etc, then encode it back to SAV, load it and continue playing with your changes applied!

To run:
* Install [Python interpreter](https://www.python.org)
* Additionally install bitarray module with pip (google how to do this please)
* Place all the files of __smcol_saves_utility__ to some folder
* Open _smcol_sav_settings.json_ file in a text editor and set value of a _colonize_path_ record to the path of the COLONIZE folder of your Colonization installation
* Run *enc_decode_sav.py* whether using command `python enc_decode_sav.py` or just clicking on it (depends on how you configured your Python installation)
* Follow onscreen instructions

## SAV file structure outline in JSON format
It is stored in _smcol_sav_struct.json_ file. The structure itself was copied from [viceroy](https://github.com/hegemogy/viceroy) project and adapted to JSON format. Thanks to [**eb4x**](https://github.com/eb4x) and [**hegemogy**](https://github.com/hegemogy) for their great and thoroughful work!

Some additions were made:
- Warehouse Expansion level info was correctly mapped (byte 0x95 in colony record)
- Profession field value for Treasure unit is it's gold amount (x100), i.e. 0x32 = 50d = 5000 gold
- Artillery damaged flag discovered. Now we can "repair" it! (for a price in wood and tools of course). Though this flag means something else for ships

### _smcol_sav_struct.json_ file structure
It is a [dictionary](https://en.wikipedia.org/wiki/Associative_array). Each entry of it is itself a dictionary too.

It's first record (section) is *__metadata*. It is not stored directly in SAV file. *__metadata* is used to represent field values in human readable form (instead of raw hex or bits). You can add new types here and use it for data fields below. For example:
* *nation_type* represents nation id fields values in text form (England, France, Aztec, Sioux, Tupi...) instead of hex values ("01", "02", "05", "0A", "0B")
* *cargo_type* represents cargo id fields values in text form (tobacco, silver, cloth...) instead of 4-bit values (0010, 0111, 1011...)

The next records map regions of SAV file data. The record can be:
* simple - with a size entry value in bytes or bits
  *  with just *size* entry in bytes (for ex `"unknown00": {"size": 3}`) - will be parsed as hex string (`"unknown00": "1A 49 00"`)
  *  with *size* and *type* hint (`"year": {"size": 2, "type": "int"}`) - will be parsed as a value of desired type (`"year": 1694`)
  *  with *count/cols* entries (rows and cols count of data) - will be parsed as an 1d-array or 2d-array:
     `"cargo_hold": {"size": 1, "cols": 6, "type": "int"}`
     leads to:
     `"cargo_hold": [100, 100, 100, 50, 0, 0]`
  *  with *save_meta* flag (to save the value to *metadata* dict and use it later - for colonies or units count for example)
* structured - with *struct* field, describing it's inner structure with byte-mapping:
  ```
  "expeditionary_force": {
      "struct": {
          "regulars": {"size": 2, "type": "int"},
          "dragoons": {"size": 2, "type": "int"},
          "man-o-wars": {"size": 2, "type": "int"},
          "artillery": {"size": 2, "type": "int"}
      }        
  }
  ```
  will be parsed as:
  ```
  "expeditionary_force": {
      "regulars": 64,
      "dragoons": 21,
      "man-o-wars": 11,
      "artillery": 20
  }  
  ```
  Structured fields allow use of *count/cols* entries, but not *size* (it will be computed manually) or *type*.
  
* bit-structured - with *bit_struct* field, describing it's inner structure with bit-mapping:
  ```
  "buildings":
  {
      "bit_struct":
      {
          "fortification": {"size": 3, "type": "fort_type"},
          "armory": {"size": 3, "type": "level_3bit_type"},
          "docks": {"size": 3, "type": "level_3bit_type"},
          "town_hall": {"size": 3, "type": "level_3bit_type"},
          "schoolhouse": {"size": 3, "type": "level_3bit_type"},
          "warehouse": {"size": 1, "type": "bit_bool"},
          "unused05a": {"size": 1, "type": "bit_bool"},
          "stables": {"size": 1, "type": "bit_bool"},
          "custom_house": {"size": 1, "type": "bit_bool"},
          "printing_press": {"size": 2, "type": "level_2bit_type"},
          "weavers_house": {"size": 3, "type": "level_3bit_type"},
          "tobacconists_house": {"size": 3, "type": "level_3bit_type"},
          "rum_distillers_house": {"size": 3, "type": "level_3bit_type"},
          "capitol (unused)": {"size": 2, "type": "level_2bit_type"},
          "fur_traders_house": {"size": 3, "type": "level_3bit_type"},
          "carpenters_shop": {"size": 2, "type": "level_2bit_type"},
          "church": {"size": 2, "type": "level_2bit_type"},
          "blacksmiths_house": {"size": 3, "type": "level_3bit_type"},
          "unused05b": {"size": 6}          
      }
  }
  ```
  will be parsed as:
  ```
  "buildings": {
      "fortification": "none",
      "armory": "0",
      "docks": "0",
      "town_hall": "1",
      "schoolhouse": "0",
      "warehouse": true,
      "unused05a": false,
      "stables": false,
      "custom_house": false,
      "printing_press": "0",
      "weavers_house": "1",
      "tobacconists_house": "1",
      "rum_distillers_house": "1",
      "capitol (unused)": "0",
      "fur_traders_house": "1",
      "carpenters_shop": "1",
      "church": "0",
      "blacksmiths_house": "1",
      "unused05b": "000000"
  }
  ```
  Bit-structured fields allow use of *count/cols* entries, but not *size* (it will be computed manually) or *type*. All *size* values of bit-structure's sub records will be interpreted as bits.
