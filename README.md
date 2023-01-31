# Sid Meier's Colonization (1994) SAV files utility pack

The aim of this work is to make study and edit process of SAV files easy and comfortable. The ultimate goal is to fully describe SAV file structure, outline it in universal format and prepare utility pack for working with SAV files for enhancing the gameplay of this brilliant game.

## What is being done:
- outline the SAV file structure in easy readable and editable universal JSON format
- utility for parsing binary SAV file data and saving it to human readable/editable JSON format
- utility for reading SAV file data FROM human readable/editable JSON format **and writing it back** to native SAV format (yes!)
- utility for editing SAV files (certain fields such as: remove stokade, arm indian converts, plant forests etc)

## SAV file structure outline in JSON format
It is stored in _smcol_sav_struct.json_ file. The structure itself was copied from [viceroy](https://github.com/hegemogy/viceroy) project and adapted to JSON format. Thanks to [**eb4x**](https://github.com/eb4x) and [**hegemogy**](https://github.com/hegemogy) for their great and thoroughful work!

Some additions were made:
- Warehouse Expansion level info was correctly mapped (byte 0x95 in colony record)
