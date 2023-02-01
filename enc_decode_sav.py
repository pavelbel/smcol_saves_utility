import os
import json
import sys
from smcol_sav_converter import handle_metadata, read_sav_structure, dump_sav_structure


def get_input(input_hint: str, res_type=str, check_fun=lambda x: True, error_str=''):
    """Ввод значения c клавиатуры с преобразованием в нужный тип и повторами в случае некорректных значений"""

    while True:
        inp_res = input(input_hint)
        if len(inp_res) == 0:
            return None

        try:
            inp_val = res_type(inp_res)
            if check_fun(inp_val):
                return inp_val
            else:
                raise Exception
        except:
            print(f"{error_str} '{inp_res}'")


def decode_sav_file(sav_filename: str, sav_structure: dict):
    try:
        with open(sav_filename, mode='rb') as sf:
            sav_data = sf.read()

        read_metadata = handle_metadata(sav_structure['__metadata'])
        read_struct_data = read_sav_structure(sav_structure, sav_data, read_metadata)
        read_struct_data['__structure'] = sav_structure

        decoded_sav_json_data_filename = sav_filename + '.json'

        # Save structured SAV data to JSON file sav_json_data_filename
        with open(decoded_sav_json_data_filename, mode='wt') as svftj:
            json.dump(read_struct_data, svftj, indent=4)

    except Exception as ex:
        print(f"ERROR: SAV file '{sav_filename}' decoding failure: {ex}")
    else:
        print(f"SAV file '{sav_filename}' decoding SUCCESS! JSON structured data written to '{decoded_sav_json_data_filename}'")


def encode_sav_file(json_sav_filename: str):
    try:
        with open(json_sav_filename, mode='rt') as sjf:
            read_struct_data = json.load(sjf)

        loaded_sav_structure = read_struct_data['__structure']
        loaded_metadata = handle_metadata(loaded_sav_structure['__metadata'])

        # Serialize and dump JSON data to original binary SAV format
        enc_sav_data = dump_sav_structure(read_struct_data, loaded_sav_structure, loaded_metadata)
        #saved_filename = os.path.splitext(json_sav_filename)[0][:-2] + '07.SAV'
        saved_filename = os.path.splitext(json_sav_filename)[0] + '.enc'
        with open(saved_filename, mode='wb') as svftenc:
            svftenc.write(enc_sav_data)

    except Exception as ex:
        print(f"ERROR: SAV.JSON file '{json_sav_filename}' encoding failure: {ex}")
    else:
        print(f"SAV.JSON file '{json_sav_filename}' encoding SUCCESS! Binary SAV data written to '{saved_filename}'. Remove '.enc' to load it from the game")


if __name__ == '__main__':
    print("== Sid Meier's Colonization (1994) SAV files DECODER and ENCODER ==")

    json_struct_filename = 'smcol_sav_struct.json'
    is_sav_structure_loaded = False
    try:
        with open(json_struct_filename, mode='rt') as sjf:
            json_sav_structure = json.load(sjf)

        is_sav_structure_loaded = True
    except Exception as ex:
        print(f"WARNING: problem with JSON SAV structure file '{json_struct_filename}': {ex}")

    while True:
        sav_files_list = []

        with os.scandir('.') as scan_res:
            for dir_entry in scan_res:
                if dir_entry.is_dir():
                    continue

                file_type = None
                if dir_entry.name.lower().endswith(".sav"):
                    file_type = 'sav'
                elif dir_entry.name.lower().endswith(".sav.json"):
                    file_type = 'sav_json'
                else:
                    continue

                if file_type == 'sav':
                    with open(dir_entry.path, mode='rb') as f:
                        col_str = f.read(8)
                        if col_str != b'COLONIZE':
                            continue

                sav_files_list.append((dir_entry.name, file_type))

        if len(sav_files_list) == 0:
            print("NO sav files in current directory. Place this file to COLONIZE folder.")
            sys.exit(0)

        print()
        print("SAV and SAV.JSON files in the current folder:")
        for i, sav_file_data in enumerate(sav_files_list, start=1):
            print(f"{i}. {sav_file_data[0]}")

        sav_idx = get_input("Enter file index to decode or encode it or press ENTER to quit: ", res_type=int, error_str="Wrong SAV file index:", check_fun=lambda x: 1 <= x <= len(sav_files_list))
        if sav_idx is None:
            break

        chosen_filename = sav_files_list[sav_idx-1][0]

        if sav_files_list[sav_idx-1][1] == 'sav':
            if is_sav_structure_loaded:
                decode_sav_file(chosen_filename, json_sav_structure)
            else:
                print("ERROR: json_sav_structure not loaded, you cannot decode SAV files!")
        else:
            encode_sav_file(chosen_filename)


