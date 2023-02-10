import os
import sys
import json
from smcol_sav_converter import handle_metadata, read_sav_structure, dump_sav_structure
from get_input import *


def read_json_sav_data(sav_filename: str, sav_structure: dict, sections_to_read=None):
    try:
        with open(sav_filename, mode='rb') as sf:
            sav_data = sf.read()

        read_metadata = handle_metadata(sav_structure['__metadata'])
        json_sav_data = read_sav_structure(sav_structure, sav_data, read_metadata, ignore_compact=True, sections_to_read=sections_to_read)
        json_sav_data['__structure'] = sav_structure
    except Exception as ex:
        return None
    else:
        return json_sav_data


def get_caption_data(json_sav_data: dict):
    if json_sav_data is None:
        return None

    caption_data = {'year': json_sav_data['HEAD']['year'],
                    'season': json_sav_data['HEAD']['season'],
                    'difficulty': json_sav_data['HEAD']['difficulty']}

    for pl in json_sav_data['PLAYER']:
        if pl['control'] == 'PLAYER':
            caption_data['name'] = pl['name']
            caption_data['country_name'] = pl['country_name']
            caption_data['colonies'] = pl['founded_colonies']
            break
    else:
        caption_data['country_name'] = 'no'
        caption_data['colonies'] = 0

    return caption_data


def extract_coords_from_str(coords_str: str):
    coords_splt = coords_str.split(',')
    if len(coords_splt) != 2:
        return None

    try:
        x = int(coords_splt[0])
        y = int(coords_splt[1])
    except:
        return None
    else:
        return x, y


def run_grow_forest_routine(json_sav_data):
    """Run plant forest routine"""

    def check_coords_str(coords_str: str):
        coords_val = extract_coords_from_str(coords_str)
        if coords_val is None:
            return False

        return 1 <= coords_val[0] <= json_sav_data['HEAD']['map_size_x'] and 1 <= coords_val[1] <= json_sav_data['HEAD']['map_size_y']

    while True:
        coords_str = get_input("Enter coords of a tile you want to turn to a forest (x, y) or press ENTER to quit: ", res_type=str, error_str="Wrong tile coords:", check_fun=check_coords_str)
        if coords_str is None:
            break


def edit_sav_file(sav_filename: str, sav_structure, json_sav_data=None):
    """Full SAV editing process"""

    if json_sav_data is None:
        json_sav_data = read_json_sav_data(sav_filename, sav_structure)

    print()
    if json_sav_data is not None:
        print(f"SAV file '{sav_filename}' loading SUCCESS")
    else:
        print(f"SAV file '{sav_filename}' loading ERROR!")
        return

    print(f"== {caption_data['country_name']}, {caption_data['season'].capitalize()} of {caption_data['year']}, {caption_data['difficulty']} {caption_data['name']} ==")

    routines = [(run_grow_forest_routine, "Plant a forest"),]

    while True:
        print("Actions list:")
        for num, rout in enumerate(routines, start=1):
            print(f"{num}. {rout[1]}")

        action_idx = get_input("Enter action index or press ENTER to quit: ", res_type=int, error_str="Wrong action index:", check_fun=lambda x: 1 <= x <= len(routines))
        if action_idx is None:
            break

        routines[action_idx - 1][0](json_sav_data)

    return


if __name__ == '__main__':
    print("== Sid Meier's Colonization (1994) SAV files EDITOR ==")

    json_struct_filename = 'smcol_sav_struct.json'
    is_sav_structure_loaded = False
    try:
        with open(json_struct_filename, mode='rt') as sjf:
            json_sav_structure = json.load(sjf)

        is_sav_structure_loaded = True
    except Exception as ex:
        print(f"ERROR: error loading JSON SAV structure file '{json_struct_filename}': {ex}")
        sys.exit(0)

    while True:
        sav_files_list = []

        with os.scandir('.') as scan_res:
            for dir_entry in scan_res:
                if dir_entry.is_dir():
                    continue

                file_type = None
                if dir_entry.name.lower().endswith(".sav"):
                    file_type = 'sav'
                else:
                    continue

                curr_read_json_sav_data = read_json_sav_data(dir_entry.path, json_sav_structure, sections_to_read=['HEAD', 'PLAYER'])
                sav_files_list.append((dir_entry.name, file_type, curr_read_json_sav_data))

        if len(sav_files_list) == 0:
            print("NO SAV files in current directory. Place this file to COLONIZE folder.")
            sys.exit(0)

        print()
        print("SAV and SAV.JSON files in the current folder:")
        for i, sav_file_data in enumerate(sav_files_list, start=1):
            print(f"{i}. {sav_file_data[0]}", end=': ')
            caption_data = get_caption_data(sav_file_data[2])
            if caption_data is None:
                print('Corrupt')
            else:
                print(f"{caption_data['country_name']}, {caption_data['season'].capitalize()} of {caption_data['year']}, {caption_data['difficulty']} {caption_data['name']}")

        sav_idx = get_input("Enter file index to decode or encode it or press ENTER to quit: ", res_type=int, error_str="Wrong SAV file index!", check_fun=lambda x: 1 <= x <= len(sav_files_list))
        if sav_idx is None:
            break

        chosen_filename = sav_files_list[sav_idx-1][0]

        edit_sav_file(chosen_filename, json_sav_structure)
