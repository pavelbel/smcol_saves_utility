== Sid Meier's Colonization (1994) SAV files utility pack ==
            (programmed by: Pavel Bel, 2023 )
                       Ver. 1.4 (dev)

https://github.com/pavelbel/smcol_saves_utility

REQS

* Windows x64 or Linux x86-64
* Colonization (1994) (ver 3.0) installed

CONTENTS
(well, it's just two utilities)

* enc_decode_sav - a utility for parsing binary SAV file data and saving it to human readable/editable JSON format
* smcol_sav_editor - utility for editing SAV files
* smcol_sav_settings.json - JSON file with utilities settings
* smcol_sav_struct.json - JSON file with Colonization (1994) SAV file structure outline

HOW TO USE

1) Open smcol_sav_settings.json in a text editor and set 'colonize_path' value to the 'COLONIZE' folder of your Colonization installation (i.e. "D:/Games/GOG.com/Colonization/MPS/COLONIZE")
    - If you've placed these files in the COLONIZE folder itself, you should be able to simply use "."
    - If you've placed these files in a subfolder of COLONIZE, you should be able to use ".."
    - In Linux, the format is the full path to your Col folder, e.g. "/home/username/Games/GOG.com/Colonization/MPS/COLONIZE", rather than "D:/Games..." ("." or ".." should work as well)

2) Run smcol_sav_editor to edit or enc_decode_sav to encode/decode SAV files

WHY TO USE

* enc_decode_sav.exe decodes your SAV files to human readable/editable JSON format (COLONY00.SAV.json). You can then edit it and encode back to SAV. The utility autodetects the file type and converts SAV to SAV.json and SAV.json to SAV. You can edit SAV structure outline in smcol_sav_struct.json by yourself to alter data representation. There are still several unknown regions there (named with 'unknown..'). Maybe you'll discover its purposes?

* smcol_sav_editor.exe: make some useful modifications in your SAV files:
- Remove fortifications in colonies,
- Plant forests on tiles
- Upgrade warehouse level above 2 (for a fee!). Adjust max level and fee increase koeff in settings
- Clear off forest and plow land under all AI's colonies (yes, to help AI manage its colonies)
- Assimilate Indian converts
- Arm/equip Indian converts (promote them to scouts, warriors or pioneers)
- Repair damaged artillery units
- Adjust expeditionary force size: reinforce, nerf or disband it
- Add 4th, 5th etc. specialist to manufactures

NOTE

The executable files are big (~7 megabytes). That's because they include the Python interpreter with its basic libraries. You can install Python yourself and use the utilities in its native *.py format. Download Python 3.7+ from https://www.python.org/ and utilities from https://github.com/pavelbel/smcol_saves_utility

CHANGELOG

== Version 1.4 (dev) == 
  (xx.xx.202x)

- enhanced backup files chains logic for enc_decode_sav
- minor fixes

New fields and sections mapped:
- click_before_open_colony x, y field (coords of the point player clicked before entering some colony screen)
- show_colony_prod_quantities (to show poduction quantities on colony screen flag)
- relation byte field partially decoded

== Version 1.3 == 
  (23.10.2023)

Editor:
- SAV files list now sorted alphabetically
- Regular pioneers can plant forests (adjustable in settings)
- Adjust expeditionary force size: reinforce, nerf or disband it
- Add 4th, 5th etc. specialist to manufactures (adjustable in settings)

Encoder/Decoder:
- SAV files list now sorted alphabetically
- AUTO UPDATE mode (track changes in certain SAV or SAV.json file and encode/decode it automatically)

SAV structure:
- new occupation_type value: Teacher
New fields and sections mapped:
- TRADE_ROUTE section
- cheats_enabled flag
- tile_selection_mode flag
- indian horse_herds field
- prime_resource_seed field (a value somehow responsible for prime resources and city rumors placement)
- trade_route_count field
- royal_money field (spent on REF increase)
- muskets field (for indian tribes)
- unknown46 field filled: internal state descriptors for computing prices of goods in price groups (thanks to @no-more-secrets)
- unknown_map38a and unknown_map38b - some unknown downsampled map fields

== Version 1.2 == 
  (06.03.2023)

SAV structure:
- Colony "external" population and fortification values mapped (These values represent how a colony is seen by other nations (Player and AIs) on their maps.)

Editor:
- Plant forest requires a pioneer on the tile, and he spends tools on planting
- Assimilate Indian converts
- Arm/equip Indian converts (promote them to scouts, warriors or pioneers)
- Repair damaged artillery units


== Version 1.1 == 
  (20.02.2023)

Editor:
- Upgrade warehouse level above 2
- Clear off forest and plow land under all AI's colonies


== Version 1.0 == 
  (18.02.2023)

First release.

