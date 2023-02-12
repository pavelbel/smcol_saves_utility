import os
import datetime
import sys
import json
from smcol_sav_converter import handle_metadata, read_sav_structure, dump_sav_structure
from smcol_sav_common import *


def read_json_sav_data(sav_filename: str, sav_structure: dict, sections_to_read=None):
    try:
        with open(sav_filename, mode='rb') as sf:
            sav_data = sf.read()

        read_metadata = handle_metadata(sav_structure['__metadata'])
        json_sav_data = read_sav_structure(sav_structure, sav_data, read_metadata, ignore_compact=True,
                                           sections_to_read=sections_to_read)
        json_sav_data['__structure'] = sav_structure
    except Exception as ex:
        return None
    else:
        return json_sav_data


def save_sav_data(sav_filename: str, json_sav_data: dict):
    loaded_sav_structure = json_sav_data['__structure']
    loaded_metadata = handle_metadata(loaded_sav_structure['__metadata'])

    # Serialize and dump JSON data to original binary SAV format
    enc_sav_data = dump_sav_structure(json_sav_data, loaded_sav_structure, loaded_metadata)

    for bak_num in range(100):
        bak_sav_filename = sav_filename + f'.bak_{bak_num}'
        try:
            with open(bak_sav_filename, mode='rb') as svftenc:
                continue
        except:
            os.rename(sav_filename, bak_sav_filename)
            break

    #saved_filename = sav_filename + '.enc'
    with open(sav_filename, mode='wb') as svftenc:
        svftenc.write(enc_sav_data)


def get_caption_data(json_sav_data: dict):
    if json_sav_data is None:
        return None

    caption_data = {'year': json_sav_data['HEAD']['year'],
                    'season': json_sav_data['HEAD']['season'],
                    'difficulty': json_sav_data['HEAD']['difficulty']}

    for i, pl in enumerate(json_sav_data['PLAYER']):
        if pl['control'] == 'PLAYER':
            caption_data['name'] = pl['name']
            caption_data['country_name'] = pl['country_name']
            caption_data['colonies'] = pl['founded_colonies']
            caption_data['gold'] = json_sav_data['NATION'][i]['gold']
            break
    else:
        caption_data['country_name'] = 'no'
        caption_data['colonies'] = 0
        caption_data['gold'] = 0

    return caption_data


class SAVEditor:
    def __init__(self, sav_filename: str, sav_structure: dict):
        self.sav_filename = sav_filename
        self.sav_structure = sav_structure
        self.json_sav_data = None
        self.caption_data = None
        self.is_initialized = False
        self.unsaved_changes = []
        self.load()

    def load(self):
        self.json_sav_data = read_json_sav_data(self.sav_filename, self.sav_structure)
        self.is_initialized = self.json_sav_data is not None
        self.caption_data = get_caption_data(self.json_sav_data)
        self.unsaved_changes = []

    def save(self):
        save_sav_data(self.sav_filename, self.json_sav_data)
        self.unsaved_changes = []

    def __getitem__(self, item):
        return self.json_sav_data[item]


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


def run_plant_forest_routine(sav_editor: SAVEditor):
    """Run plant forest routine"""

    print()
    print('== Plant a forest ==')

    def check_coords_str(coords_str: str):
        coords_val = extract_coords_from_str(coords_str)
        if coords_val is None:
            return False
        return 1 <= coords_val[0] <= sav_editor['HEAD']['map_size_x'] and 1 <= coords_val[1] <= sav_editor['HEAD']['map_size_y']

    while True:
        coords_str = get_input("Enter coords of a tile you want to turn to a forest (x, y) or press ENTER to quit: ", res_type=str, error_str="Wrong tile coords:", check_fun=check_coords_str)
        if coords_str is None:
            break

        tile_x, tile_y = extract_coords_from_str(coords_str)

        curr_tile = sav_editor['TILE'][tile_y][tile_x]['tile']
        if curr_tile in ['~~~', '~:~']:
            print('ERROR: cannot plant a forest on ocean!')
            continue

        if curr_tile == 'arc':
            print('ERROR: cannot plant a forest in arctic!')
            continue

        if curr_tile[2].lower() == 'f':
            print('ERROR: the tile is already forested!')
            continue

        # Planting forest!
        sav_editor['TILE'][tile_y][tile_x]['tile'] = curr_tile[:2] + 'F' + curr_tile[3:]
        sav_editor['MASK'][tile_y][tile_x]['plowed'] = ' '

        res_str = f"Forest planted on tile {(tile_x, tile_y)}"
        sav_editor.unsaved_changes.append(res_str)
        print(res_str)


def run_reload_routine(sav_editor: SAVEditor):
    if len(sav_editor.unsaved_changes) > 0:
        ans = get_input("There are unsaved changes. Do you want to skip them? [y/n]: ", res_type=str, error_str="Wrong answer:", check_fun=lambda x: x[0].lower() in ['y', 'n'])
        if ans[0].lower() == 'n':
            print("Reloading canceled")
            return

    sav_editor.load()
    if sav_editor.is_initialized:
        print(f"SAV file '{sav_editor.sav_filename}' reload SUCCESS")


def run_save_routine(sav_editor: SAVEditor):
    try:
        sav_editor.save()
    except Exception as ex:
        print(f"ERROR: saving FAILED!: {ex}")
    else:
        print(f"Saving SUCCESS!")


def run_show_changes_routine(sav_editor: SAVEditor):
    print()
    if len(sav_editor.unsaved_changes) > 0:
        print('== Changes made ==')
        for uc in sav_editor.unsaved_changes:
            print(f"* {uc}")
    else:
        print("== No changes made ==")


def edit_sav_file(sav_filename: str, sav_structure: dict):
    """Full SAV editing process"""

    sav_editor = SAVEditor(sav_filename, sav_structure)

    if not sav_editor.is_initialized:
        print(f"SAV file '{sav_editor.sav_filename}' loading ERROR!")
        return

    routines = [(run_reload_routine, "Reload SAV file"),
                (run_save_routine, "Save SAV file"),
                (run_show_changes_routine, "See pending changes"),
                (run_plant_forest_routine, "Plant a forest")]

    while True:
        print()
        print(f"== {sav_filename}: {sav_editor.caption_data['country_name']}, {sav_editor.caption_data['season'].capitalize()} of {sav_editor.caption_data['year']}, {sav_editor.caption_data['difficulty']} {sav_editor.caption_data['name']}, {sav_editor.caption_data['gold']} gold ==")

        print("Actions list:")
        for num, rout in enumerate(routines, start=1):
            print(f"{num:2}. {rout[1]}")

        action_idx = get_input("Enter action index or press ENTER to quit: ", res_type=int, error_str="Wrong action index:", check_fun=lambda x: 1 <= x <= len(routines))
        if action_idx is None:
            if len(sav_editor.unsaved_changes) > 0:
                ans = get_input("There are unsaved changes. Do you want to skip them? [y/n]: ", res_type=str, error_str="Wrong answer:", check_fun=lambda x: x[0].lower() in ['y', 'n'])
                if ans[0].lower() == 'n':
                    continue
            break

        routines[action_idx - 1][0](sav_editor)
        if not sav_editor.is_initialized:
            print(f"SAV file '{sav_editor.sav_filename}' BROKEN or ABSENT!")

    return


if __name__ == '__main__':
    print("== Sid Meier's Colonization (1994) SAV files EDITOR ==")

    default_settings = {"colonize_path": ".", "editor": {}}
    settings_json_filename = os.path.join(os.path.split(sys.argv[0])[0], 'smcol_sav_settings.json')
    settings = load_settings(settings_json_filename, default_settings)

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

        with os.scandir(settings['colonize_path']) as scan_res:
            for dir_entry in scan_res:
                if dir_entry.is_dir():
                    continue

                file_type = None
                if dir_entry.name.lower().endswith(".sav"):
                    file_type = 'sav'
                else:
                    continue

                curr_read_json_sav_data = read_json_sav_data(dir_entry.path, json_sav_structure, sections_to_read=['HEAD', 'PLAYER', 'NATION'])
                sav_files_list.append((dir_entry.name, file_type, curr_read_json_sav_data))

        if len(sav_files_list) == 0:
            print("NO SAV files in current directory. Place this file to COLONIZE folder.")
            sys.exit(0)

        print()
        print("SAV and SAV.JSON files in the current folder:")
        bad_saves_idxs = []
        for i, sav_file_data in enumerate(sav_files_list, start=1):
            print(f"{i:2}. {sav_file_data[0]}", end=': ')
            caption_data = get_caption_data(sav_file_data[2])
            if caption_data is None:
                print('Corrupt')
                bad_saves_idxs.append(i)
            else:
                print(f"{caption_data['country_name']}, {caption_data['season'].capitalize()} of {caption_data['year']}, {caption_data['difficulty']} {caption_data['name']}, {caption_data['gold']} gold")

        sav_idx = get_input("Enter file index to decode or encode it or press ENTER to quit: ", res_type=int, error_str="Wrong SAV file index!", check_fun=lambda x: 1 <= x <= len(sav_files_list))
        if sav_idx is None:
            break

        if sav_idx in bad_saves_idxs:
            print("This SAV file is corrupt!")
            continue

        chosen_filename = sav_files_list[sav_idx-1][0]

        edit_sav_file(chosen_filename, json_sav_structure)
