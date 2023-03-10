import os
import datetime
import sys
import json
from smcol_sav_converter import handle_metadata, read_sav_structure, dump_sav_structure, REL_VER
from smcol_sav_common import *

DEFAULT_SETTINGS = {"colonize_path": ".",
                    "editor": {"remove_fortifications_only_in_player_colonies": True,
                               "plant_forest_tools_cost": 100,
                               "warehouse_max_level": 4,
                               "warehouse_level_inc_hammers_multiplier": 2,
                               "warehouse_level_inc_tools_multiplier": 2,
                               "assimilate_work_duration_thresh": 10,
                               "assimilate_target_state": "Indentured servant"}
                    }
FIELD_VALUES = {
"control_type":     {"PLAYER": "00", "AI": "01", "WITHDRAWN": "02"},
"difficulty_type":  {"Discoverer": "00", "Explorer": "01", "Conquistador": "02", "Governor": "03", "Viceroy": "04"},
"season_type":      {"autumn": "01 00", "spring": "00 00"},
"nation_type":      {"England": "00", "France": "01", "Spain": "02", "Netherlands": "03", "Inca": "04", "Aztec": "05",
                     "Awarak": "06", "Iroquois": "07", "Cherokee": "08", "Apache": "09", "Sioux": "0A", "Tupi": "0B", "None": "FF"},
"profession_type":  {"expert farmer": "00", "master sugar planter": "01", "master tobacco planter": "02", "master cotton planter": "03",
                     "expert fur trapper": "04", "expert lumberjack": "05", "expert ore miner": "06", "expert silver miner": "07",
                     "expert fisherman": "08", "master distiller": "09", "master tobacconist": "0A", "master weaver": "0B",
                     "master fur trader": "0C", "master carpenter": "0D", "master blacksmith": "0E", "master gunsmith": "0F",
                     "firebrand preacher": "10", "elder statesman": "11", "*(student)": "12", "*(free colonist)": "13", "hardy pioneer": "14",
                     "veteran soldier": "15", "seasoned scout": "16", "veteran dragoon": "17", "jesuit missionary": "18",
                     "indentured servant": "19", "petty criminal": "1A", "indian convert": "1B", "free colonist": "1C"},
"unit_type":        {"colonist": "00", "soldier": "01", "pioneer": "02", "missionary": "03", "dragoon": "04", "scout": "05", "tory regular": "06",
                     "continental cavalry": "07", "tory cavalry": "08", "continental army": "09", "treasure": "0A", "artillery": "0B",
                     "wagon train": "0C", "caravel": "0D", "merchantman": "0E", "galeon": "0F", "privateer": "10", "frigate": "11",
                     "man-o-war": "12", "brave": "13", "armed brave": "14", "mounted brave": "15", "mounted warrior": "16"}
}

IND_CONV_PROM_DATA = [{'unit_type': 'scout', 'reqs': [('horses', 50)]},
                      {'unit_type': 'mounted brave', 'reqs': [('horses', 50)]},
                      {'unit_type': 'armed brave', 'reqs': [('muskets', 50)]},
                      {'unit_type': 'mounted warrior', 'reqs': [('horses', 50), ('muskets', 50)]},
                      {'unit_type': 'pioneer', 'reqs': [('tools', 20, 100, 20)]}]   # <- ('tools', min, max, step)


def read_json_sav_data(sav_filename: str, sav_structure: dict, sections_to_read=None):
    try:
        with open(sav_filename, mode='rb') as sf:
            sav_data = sf.read()

        read_metadata = handle_metadata(sav_structure['__metadata'])
        json_sav_data = read_sav_structure(sav_structure, sav_data, read_metadata, ignore_compact=True, ignore_custom_type=True, sections_to_read=sections_to_read)
        json_sav_data['__structure'] = sav_structure
    except Exception as ex:
        return None
    else:
        return json_sav_data, read_metadata


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
    else:
        bak_sav_filename = None

    #saved_filename = sav_filename + '.enc'
    with open(sav_filename, mode='wb') as svftenc:
        svftenc.write(enc_sav_data)

    return bak_sav_filename


def get_caption_data(json_sav_data: dict):
    if json_sav_data is None:
        return None

    caption_data = {'year': json_sav_data['HEAD']['year'],
                    'season': FIELD_VALUES['season_type_inv'][json_sav_data['HEAD']['season']],
                    'difficulty': FIELD_VALUES['difficulty_type_inv'][json_sav_data['HEAD']['difficulty']]}

    for i, pl in enumerate(json_sav_data['PLAYER']):
        if pl['control'] == FIELD_VALUES['control_type']['PLAYER']:
            caption_data['name'] = pl['name']
            caption_data['country_name'] = pl['country_name']
            caption_data['colonies'] = pl['founded_colonies']
            caption_data['gold'] = json_sav_data['NATION'][i]['gold']
            caption_data['player_nation_id'] = i
            break
    else:
        caption_data['name'] = 'no'
        caption_data['country_name'] = 'no'
        caption_data['colonies'] = 0
        caption_data['gold'] = 0
        caption_data['player_nation_id'] = None

    return caption_data


class SAVEditor:
    def __init__(self, in_sav_filepath: str, sav_structure: dict):
        self.sav_filepath = in_sav_filepath
        self.sav_structure = sav_structure
        self.json_sav_data = None
        self.metadata = None
        self.caption_data = None
        self.is_initialized = False
        self.unsaved_changes = []
        self.load()

    def filename(self):
        return os.path.split(self.sav_filepath)[1]

    def filepath(self):
        return self.sav_filepath

    def load(self):
        self.json_sav_data, self.metadata = read_json_sav_data(self.sav_filepath, self.sav_structure)
        self.is_initialized = self.json_sav_data is not None
        self.caption_data = get_caption_data(self.json_sav_data)

        self.unsaved_changes = []

        # ???????? ?????????????? ????????, ???? ?????? ???? ?????????? ??????????????. ???????????????? ??????
        if 'COLONY' not in self.json_sav_data or self.json_sav_data['COLONY'] is None:
            self.json_sav_data['COLONY'] = []
        elif not isinstance(self.json_sav_data['COLONY'], list):
            self.json_sav_data['COLONY'] = [self.json_sav_data['COLONY']]

        # ???????? ???????? ???????? (???? ?????????? ???? ????????????!), ???? ???? ???? ?????????? ??????????????. ???????????????? ??????
        if 'UNIT' not in self.json_sav_data or self.json_sav_data['UNIT'] is None:
            self.json_sav_data['UNIT'] = []
        elif not isinstance(self.json_sav_data['UNIT'], list):
            self.json_sav_data['UNIT'] = [self.json_sav_data['UNIT']]

    def save(self):
        bak_filename = save_sav_data(self.sav_filepath, self.json_sav_data)
        self.unsaved_changes = []
        return bak_filename

    def get_player_nation(self):
        if not self.is_initialized or self.caption_data['player_nation_id'] is None:
            return None

        # return self.metadata['nation_type_inv'][self.caption_data['player_nation_id']]
        return list(self.metadata['nation_type_inv'].values())[self.caption_data['player_nation_id']]

    def __getitem__(self, item):
        return self.json_sav_data[item]

    def __setitem__(self, key, value):
        self.json_sav_data[key] = value


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
    print('== Plant forest ==')

    field_name = 'plant_forest_tools_cost'
    try:
        plant_forest_tools_cost = int(settings['editor'][field_name])
    except:
        plant_forest_tools_cost = DEFAULT_SETTINGS['editor'][field_name]
        print(f"WARNING: wrong '{field_name}' value! Setting it to default ({plant_forest_tools_cost})")

    print(f"Plant forest on a tile with coordinates you enter.", end=" ")
    if plant_forest_tools_cost > 0:
        print(f"The player's HARDY PIONEER with at least {plant_forest_tools_cost} tools must stay on the tile.")
        print("(You may edit 'plant_forest_tools_cost' value in settings)")
    else:
        print()

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
        if curr_tile[0] == '1':
            print('ERROR: cannot plant forest on an ocean or arctic tile!')
            continue

        if sav_editor['TILE'][tile_y][tile_x]['hill_river'][2] == '1':
            print('ERROR: cannot plant forest on a hill or mountain!')
            continue

        if curr_tile[1] == '1':
            print('ERROR: the tile is already forested!')
            continue

        if plant_forest_tools_cost > 0:
            # Searching for the player's hardy pioneer on selected tile
            pioneer_unit = None
            for unit in sav_editor['UNIT']:
                if unit['x, y'][0] == tile_x and unit['x, y'][1] == tile_y and unit['type'] == FIELD_VALUES['unit_type']['pioneer']\
                        and unit['profession_or_treasure_amount'] == FIELD_VALUES['profession_type']['hardy pioneer']\
                        and unit['cargo_hold'][5] >= plant_forest_tools_cost:
                    pioneer_unit = unit
                    break

            if pioneer_unit is None:
                print(f"ERROR: The player's HARDY PIONEER with tools quantity not less than {plant_forest_tools_cost} must stay on the tile!")
                continue

            pioneer_unit['cargo_hold'][5] -= plant_forest_tools_cost
            pioneer_unit['orders'] = '00'
            pioneer_unit['moves'] = 3
            if pioneer_unit['cargo_hold'][5] == 0:
                pioneer_unit['type'] = '00'

        # Planting forest!
        sav_editor['TILE'][tile_y][tile_x]['tile'] = curr_tile[:1] + '1' + curr_tile[2:]
        sav_editor['MASK'][tile_y][tile_x]['plowed'] = '0'

        res_str = f"Forest planted on tile {(tile_x, tile_y)}"
        sav_editor.unsaved_changes.append(res_str)
        print(res_str)


def run_reload_routine(sav_editor: SAVEditor):
    if len(sav_editor.unsaved_changes) > 0:
        ans = get_input("There are unsaved changes. Do you want to skip them? [y/n]: ", res_type=str, error_str="Wrong answer:", check_fun=lambda x: x[0].lower() in ['y', 'n'])
        if ans is None or ans[0].lower() == 'n':
            print("Reloading canceled")
            return

    sav_editor.load()
    if sav_editor.is_initialized:
        print(f"SAV file '{sav_editor.filename()}' reload SUCCESS")


def run_save_routine(sav_editor: SAVEditor):
    try:
        bak_filename = sav_editor.save()
    except Exception as ex:
        print(f"ERROR: saving FAILED!: {ex}")
    else:
        print(f"Saving SUCCESS!", end=' ')
        if bak_filename:
            print(f"Backup saved to '{bak_filename}'")
        else:
            print("Failed to make a backup!")


def run_show_changes_routine(sav_editor: SAVEditor):
    print()
    if len(sav_editor.unsaved_changes) > 0:
        print('== Pending changes ==')
        for uc in sav_editor.unsaved_changes:
            print(f"* {uc}")
    else:
        print("== No changes made ==")


def run_remove_stokade_routine(sav_editor: SAVEditor):
    print()
    print('== Remove fortifications ==')
    if settings['editor']['remove_fortifications_only_in_player_colonies']:
        print("  (from player's colonies)  ")

    if settings['editor']['remove_fortifications_only_in_player_colonies']:
        player_nation = sav_editor.get_player_nation()
    else:
        player_nation = None

    colonies_list = []
    for colony in sav_editor['COLONY']:
        if player_nation is not None and FIELD_VALUES['nation_type_inv'][colony['nation_id']] not in player_nation:
            continue
        colonies_list.append(colony)

    if len(colonies_list) == 0:
        print("No colonies found!")
        return

    no_fort = '000'
    fortifications = {no_fort: 'no', '001': 'stockade', '011': 'fort', '111': 'fortress'}
    while True:
        print()
        print("Colonies list:")
        for i, col in enumerate(colonies_list, start=1):
            print(f"{i:2}. {col['name']}: {fortifications[col['buildings']['fortification']]}")

        col_idx = get_input("Enter colony index or press ENTER to quit: ", res_type=int, error_str="Wrong colony index:", check_fun=lambda x: 1 <= x <= len(colonies_list))
        if col_idx is None:
            break

        curr_colony = colonies_list[col_idx-1]
        if curr_colony['buildings']['fortification'] == no_fort:
            print(f"Colony '{curr_colony['name']}' doesn't have any fortification")
            continue

        ans_yn = get_input(f"Colony '{curr_colony['name']}' has fortification: {fortifications[curr_colony['buildings']['fortification']]}. Remove it? [y/n]", res_type=str, error_str="Wrong answer:", check_fun=lambda x: x[0].lower() in ['y', 'n'])
        if ans_yn is None or ans_yn[0].lower() == 'n':
            print(f"Fortification removing cancelled")
            continue

        curr_colony['buildings']['fortification'] = no_fort

        res_str = f"Fortification removed in '{curr_colony['name']}'"
        sav_editor.unsaved_changes.append(res_str)
        print(res_str)


def get_upgrade_wh_settings_values():
    field_name = 'warehouse_max_level'
    try:
        max_wh_level = int(settings['editor'][field_name])
    except:
        max_wh_level = DEFAULT_SETTINGS['editor'][field_name]
        print(f"WARNING: wrong '{field_name}' value! Setting it to default ({max_wh_level})")

    field_name = 'warehouse_level_inc_hammers_multiplier'
    try:
        hammers_mult_koeff = settings['editor']['field_name']
    except:
        hammers_mult_koeff = DEFAULT_SETTINGS['editor'][field_name]
        print(f"WARNING: wrong '{field_name}' value! Setting it to default ({hammers_mult_koeff})")

    field_name = 'warehouse_level_inc_tools_multiplier'
    try:
        tools_mult_koeff = settings['editor'][field_name]
    except:
        tools_mult_koeff = DEFAULT_SETTINGS['editor'][field_name]
        print(f"WARNING: wrong '{field_name}' value! Setting it to default ({tools_mult_koeff})")

    return max_wh_level, hammers_mult_koeff, tools_mult_koeff


def run_upgrade_warehouse_level_routine(sav_editor: SAVEditor):
    """Upgrade warehouse level above 2"""

    print()
    print('== Upgrade warehouse ==')
    max_wh_level, hammers_mult_koeff, tools_mult_koeff = get_upgrade_wh_settings_values()
    print(f"Upgrade warehouse level in player's colonies above 2. Each level costs {hammers_mult_koeff} times more hammers\n"
          f"and {tools_mult_koeff} times more tools than previous. Max level is {max_wh_level}.")

    player_nation = sav_editor.get_player_nation()

    colonies_list = []
    for colony in sav_editor['COLONY']:
        if player_nation is not None and FIELD_VALUES['nation_type_inv'][colony['nation_id']] not in player_nation:
            continue
        colonies_list.append(colony)

    if len(colonies_list) == 0:
        print("No colonies found!")
        return

    while True:
        print()
        print("Colonies list:")
        for i, col in enumerate(colonies_list, start=1):
            print(f"{i:2}. {col['name']}: warehouse {col['warehouse_level']} lvl")

        col_idx = get_input("Enter colony index or press ENTER to quit: ", res_type=int, error_str="Wrong colony index:", check_fun=lambda x: 1 <= x <= len(colonies_list))
        if col_idx is None:
            break

        curr_colony = colonies_list[col_idx-1]
        curr_wh_level = curr_colony['warehouse_level']
        if curr_wh_level < 2:
            print(f"Colony '{curr_colony['name']}' has warehouse level below 2. Build warehouse expansion first to proceed.")
            continue

        if curr_wh_level == max_wh_level:
            print(f"Colony '{curr_colony['name']}' already has maximum warehouse level ({curr_colony['warehouse_level']}).")
            continue

        needed_hammers_count = 80 * (hammers_mult_koeff ** (curr_wh_level-1))
        needed_tools_count = 20 * (tools_mult_koeff ** (curr_wh_level - 1))

        print(f"{needed_hammers_count} HAMMERS and {needed_tools_count} TOOLS are required to upgrade warehouse to level {curr_wh_level+1}")
        if curr_colony['hammers'] < needed_hammers_count:
            print(f"Colony '{curr_colony['name']}' doesn't have enough HAMMERS. There are only {curr_colony['hammers']}")
            continue

        if curr_colony['stock']['tools'] < needed_tools_count:
            print(f"Colony '{curr_colony['name']}' doesn't have enough TOOLS. There are only {curr_colony['stock']['tools']}")
            continue

        ans_yn = get_input(f"Colony '{curr_colony['name']}' has enough HAMMERS ({curr_colony['hammers']}) and TOOLS ({curr_colony['stock']['tools']}) for warehouse upgrade. Upgrade it? [y/n]", res_type=str, error_str="Wrong answer:", check_fun=lambda x: x[0].lower() in ['y', 'n'])
        if ans_yn is None or ans_yn[0].lower() == 'n':
            print("Warehouse upgrade cancelled")
            continue

        curr_colony['warehouse_level'] += 1
        curr_colony['hammers'] -= needed_hammers_count
        curr_colony['stock']['tools'] -= needed_tools_count

        res_str = f"Warehouse in '{curr_colony['name']}' upgraded to level {curr_wh_level+1}"
        sav_editor.unsaved_changes.append(res_str)
        print(res_str)


def get_working_converts_count(colony, duration_thresh):
    """Get indian converts workers count in the colony"""

    durations = []
    for dur in colony['duration']:
        durations.append(dur['dur_1'])
        durations.append(dur['dur_2'])
    total_converts_count = 0
    ready_converts_count = 0
    max_work_dur = 0
    ready_converts_indexes = []
    for colonist_index in range(colony['population']):
        if colony['profession'][colonist_index] != FIELD_VALUES['profession_type']['indian convert']:
            continue
        total_converts_count += 1
        max_work_dur = max(max_work_dur, durations[colonist_index])
        if durations[colonist_index] >= duration_thresh:
            ready_converts_count += 1
            ready_converts_indexes.append(colonist_index)

    return total_converts_count, ready_converts_count, max_work_dur, ready_converts_indexes


def get_assimilate_settings_values():
    field_name = 'assimilate_work_duration_thresh'
    try:
        work_duration_thresh = int(settings['editor'][field_name])
    except:
        work_duration_thresh = DEFAULT_SETTINGS['editor'][field_name]
        print(f"WARNING: wrong '{field_name}' value! Setting it to default ({work_duration_thresh})")

    field_name = 'assimilate_target_state'
    try:
        convert_to_state = settings['editor'][field_name]
    except:
        convert_to_state = DEFAULT_SETTINGS['editor'][field_name]
        print(f"WARNING: wrong '{field_name}' value! Setting it to default ({convert_to_state})")

    return work_duration_thresh, convert_to_state


def run_assimilate_converts_routine(sav_editor: SAVEditor):
    """Assimilate indian converts working in colonies"""

    work_duration_thresh, convert_to_state = get_assimilate_settings_values()

    print()
    print('== Assimilate Indian converts ==')
    print(f"Assimilate Indian converts who WORK at player's colonies for at least {work_duration_thresh} turns as {convert_to_state}s.")
    print("Converts remaining outside the colony (at gates) cannot be converted.")

    player_nation = sav_editor.get_player_nation()

    colonies_list = []
    for colony in sav_editor['COLONY']:
        if player_nation is not None and FIELD_VALUES['nation_type_inv'][colony['nation_id']] not in player_nation:
            continue
        colonies_list.append(colony)

    if len(colonies_list) == 0:
        print("No player's colonies found!")
        return

    while True:
        print()
        print("Colonies list:")
        for i, col in enumerate(colonies_list, start=1):
            total_conv_count, ready_conv_count, _, _ = get_working_converts_count(col, work_duration_thresh)
            if total_conv_count == 0:
                res_str = "-"
            else:
                res_str = f"{total_conv_count} converts total, {ready_conv_count} of them ready for assimilation"
            print(f"{i:2}. {col['name']}: " + res_str)

        col_idx = get_input("Enter colony index or press ENTER to quit: ", res_type=int, error_str="Wrong colony index:", check_fun=lambda x: 1 <= x <= len(colonies_list))
        if col_idx is None:
            break

        curr_colony = colonies_list[col_idx - 1]
        total_conv_count, ready_conv_count, max_work_dur, ready_converts_indexes = get_working_converts_count(curr_colony, work_duration_thresh)

        if total_conv_count == 0:
            print(f"No Indian converts working in {curr_colony['name']}")
            continue

        if ready_conv_count == 0:
            print(f"No Indian converts ready for assimilation in {curr_colony['name']}. They must work for at least {work_duration_thresh - max_work_dur} turns more.")
            continue

        # Assimilation!
        curr_colony['profession'][ready_converts_indexes[0]] = FIELD_VALUES['profession_type'][convert_to_state.lower()]

        res_str = f"An Indian convert in {curr_colony['name']} was assimilated as {convert_to_state.capitalize()}"
        sav_editor.unsaved_changes.append(res_str)
        print(res_str)


def get_waiting_converts(colony, sav_editor):
    """Get number of Indian converts waiting at the colony's gates"""

    waiting_coverts = []
    for unit in sav_editor['UNIT']:
        if unit['x, y'][0] == colony['x, y'][0] and unit['x, y'][1] == colony['x, y'][1] and unit['type'] == FIELD_VALUES['unit_type']['colonist'] \
                and unit['profession_or_treasure_amount'] == FIELD_VALUES['profession_type']['indian convert']:
            waiting_coverts.append(unit)

    return waiting_coverts


def run_arm_equip_converts_routine(sav_editor: SAVEditor):
    """Arm/equip Indian converts remaining at colonies' gates and make them warriors, scouts or pioneers"""

    print()
    print('== Arm/Equip Indian converts ==')
    print("Promote Indian converts remaining outside the colony (at gates) to:")
    print("* Scouts (for 50 horses)")
    print("* Mounted braves (for 50 horses)")
    print("* Armed braves (for 50 muskets)")
    print("* Mounted warriors (for 50 horses and 50 muskets)")
    print("* Pioneers (for 100 tools)")
    print("Converts working in colonies cannot be promoted.")

    player_nation = sav_editor.get_player_nation()

    colonies_list = []
    for colony in sav_editor['COLONY']:
        if player_nation is not None and FIELD_VALUES['nation_type_inv'][colony['nation_id']] not in player_nation:
            continue
        colonies_list.append(colony)

    if len(colonies_list) == 0:
        print("No player's colonies found!")
        return

    while True:
        print()
        print("Colonies list:")
        for i, col in enumerate(colonies_list, start=1):
            waiting_converts = get_waiting_converts(col, sav_editor)
            if len(waiting_converts) == 0:
                res_str = "-"
            else:
                res_str = f"{len(waiting_converts)} converts remaining at gates"
            print(f"{i:2}. {col['name']}: " + res_str)

        col_idx = get_input("Enter colony index or press ENTER to quit: ", res_type=int, error_str="Wrong colony index:", check_fun=lambda x: 1 <= x <= len(colonies_list))
        if col_idx is None:
            break

        curr_colony = colonies_list[col_idx - 1]
        while True:
            curr_waiting_converts = get_waiting_converts(curr_colony, sav_editor)
            if len(curr_waiting_converts) < 1:
                print(f"No Indian converts remaining at gates in {curr_colony['name']}")
                break

            print()
            print(f"There is/are {len(curr_waiting_converts)} Indian converts remaining at gates in {curr_colony['name']}. Promote one to:")
            for i, prom in enumerate(IND_CONV_PROM_DATA, start=1):
                print(f"{i}. {prom['unit_type'].capitalize()}")

            promote_idx = get_input("Enter promotion index or press ENTER to quit: ", res_type=int, error_str="Wrong colony index:", check_fun=lambda x: 1 <= x <= len(IND_CONV_PROM_DATA))
            if promote_idx is None:
                break

            # Checking requirements
            curr_promotion = IND_CONV_PROM_DATA[promote_idx - 1]
            reqs_met = True
            for req in curr_promotion['reqs']:
                if curr_colony['stock'][req[0]] < req[1]:
                    print(f"ERROR: not enough {req[0]} to promote an Indian convert to {curr_promotion['unit_type'].capitalize()} in {curr_colony['name']}: {req[1]} is needed but only {curr_colony['stock'][req[0]]} available")
                    reqs_met = False

            if not reqs_met:
                print(f"Promotion to {curr_promotion['unit_type'].capitalize()} cancelled")
                continue

            # Updating stocks
            tools_count = 0
            for req in curr_promotion['reqs']:
                if len(req) == 2:
                    curr_colony['stock'][req[0]] -= req[1]
                elif len(req) == 4:
                    tools_count = req[1]
                    while curr_colony['stock'][req[0]] >= tools_count and tools_count <= req[2]:
                        tools_count += req[3]
                    tools_count -= req[3]
                    curr_colony['stock'][req[0]] -= tools_count

            # Promoting!
            curr_waiting_converts[0]['type'] = FIELD_VALUES['unit_type'][curr_promotion['unit_type']]
            curr_waiting_converts[0]['orders'] = '00'
            curr_waiting_converts[0]['moves'] = 12
            if tools_count > 0:
                curr_waiting_converts[0]['cargo_hold'][5] = tools_count

            res_str = f"An Indian convert in {curr_colony['name']} was promoted to {curr_promotion['unit_type'].capitalize()}"
            sav_editor.unsaved_changes.append(res_str)
            print(res_str)


def get_damaged_artillery(colony, sav_editor):
    """Get damaged artillery units waiting at the colony's gates"""

    waiting_dam_art = []
    for unit in sav_editor['UNIT']:
        if unit['x, y'][0] == colony['x, y'][0] and unit['x, y'][1] == colony['x, y'][1]\
                and unit['type'] == FIELD_VALUES['unit_type']['artillery'] and unit['unknown15']['damaged']:
            waiting_dam_art.append(unit)

    return waiting_dam_art


def run_repair_damaged_artillery_routine(sav_editor: SAVEditor):
    """Repair damaged artillery"""

    # Hardcoded, just half a price of building
    needed_hammers_count = 96
    needed_tools_count = 20

    print()
    print('== Repair damaged artillery ==')
    print(f"Restore full power of a damaged artillery for {needed_hammers_count} hammers and {needed_tools_count} tools. Damaged artillery unit must be inside a colony.")

    player_nation = sav_editor.get_player_nation()

    colonies_list = []
    for colony in sav_editor['COLONY']:
        if player_nation is not None and FIELD_VALUES['nation_type_inv'][colony['nation_id']] not in player_nation:
            continue
        colonies_list.append(colony)

    if len(colonies_list) == 0:
        print("No player's colonies found!")
        return

    while True:
        print()
        print("Colonies list:")
        for i, col in enumerate(colonies_list, start=1):
            waiting_dam_art = get_damaged_artillery(col, sav_editor)
            if len(waiting_dam_art) == 0:
                res_str = "-"
            else:
                res_str = f"{len(waiting_dam_art)} damaged artillery units"
            print(f"{i:2}. {col['name']}: " + res_str)

        col_idx = get_input("Enter colony index or press ENTER to quit: ", res_type=int, error_str="Wrong colony index:", check_fun=lambda x: 1 <= x <= len(colonies_list))
        if col_idx is None:
            break

        curr_colony = colonies_list[col_idx - 1]
        curr_waiting_dam_art = get_damaged_artillery(curr_colony, sav_editor)
        if len(curr_waiting_dam_art) < 1:
            print(f"No damaged artillery units in {curr_colony['name']}")
            continue

        #print(f"{needed_hammers_count} HAMMERS and {needed_tools_count} TOOLS are required to repair a damaged artillery")
        if curr_colony['hammers'] < needed_hammers_count:
            print(f"Colony '{curr_colony['name']}' doesn't have enough HAMMERS: {needed_hammers_count} is needed but only {curr_colony['hammers']} available")
            continue

        if curr_colony['stock']['tools'] < needed_tools_count:
            print(f"Colony '{curr_colony['name']}' doesn't have enough TOOLS: {needed_tools_count} is needed but only {curr_colony['stock']['tools']} available")
            continue

        curr_colony['hammers'] -= needed_hammers_count
        curr_colony['stock']['tools'] -= needed_tools_count
        curr_waiting_dam_art[0]['unknown15']['damaged'] = False
        curr_waiting_dam_art[0]['moves'] = 3

        res_str = f"A damaged artillery repaired in {curr_colony['name']}"
        sav_editor.unsaved_changes.append(res_str)
        print(res_str)


def run_clear_plow_colonies_tiles_routine(sav_editor: SAVEditor):
    """Clear away forest and plow tiles under AI's colonies"""

    print()
    print("== Clear & plow tiles under AI's colonies ==")

    player_nation = sav_editor.get_player_nation()

    colonies_list = []
    for colony in sav_editor['COLONY']:
        if player_nation is not None and FIELD_VALUES['nation_type_inv'][colony['nation_id']] in player_nation:
            continue
        colonies_list.append(colony)

    if len(colonies_list) == 0:
        print("No AI's colonies found!")
        return

    changes_made = False
    for col in colonies_list:
        tile_x = col['x, y'][0]
        tile_y = col['x, y'][1]

        curr_tile = sav_editor['TILE'][tile_y][tile_x]['tile']
        curr_tile_split = [s for s in curr_tile]
        if curr_tile_split[1] == '1':
            curr_tile_split[1] = '0'
            sav_editor['TILE'][tile_y][tile_x]['tile'] = ''.join(curr_tile_split)
            res_str = f"Forest cleared at '{col['name']}' (tile {(tile_x, tile_y)})"
            sav_editor.unsaved_changes.append(res_str)
            print(res_str)
            changes_made = True

        if sav_editor['MASK'][tile_y][tile_x]['plowed'] == '0':
            sav_editor['MASK'][tile_y][tile_x]['plowed'] = '1'
            res_str = f"Land plowed at '{col['name']}' (tile {(tile_x, tile_y)})"
            sav_editor.unsaved_changes.append(res_str)
            print(res_str)
            changes_made = True

    if not changes_made:
        print("All colonies' tiles are already plowed")


def edit_sav_file(in_sav_filename: str, sav_structure: dict):
    """Full SAV editing process"""

    sav_editor = SAVEditor(in_sav_filename, sav_structure)

    if not sav_editor.is_initialized:
        print(f"SAV file '{os.path.split(sav_editor.filename())[1]}' loading ERROR!")
        return

    routines = [(run_reload_routine, "Reload SAV file"),
                (run_save_routine, "Save SAV file"),
                (run_show_changes_routine, "See pending changes"),
                (run_plant_forest_routine, "Plant forest"),
                (run_remove_stokade_routine, "Remove fortification"),
                (run_upgrade_warehouse_level_routine, "Upgrade warehouse level"),
                (run_clear_plow_colonies_tiles_routine, "Clear off forest and plow land under all AI's colonies"),
                (run_assimilate_converts_routine, "Assimilate Indian converts"),
                (run_arm_equip_converts_routine, "Arm/equip Indian converts"),
                (run_repair_damaged_artillery_routine, "Repair damaged artillery")]

    while True:
        print()
        print(f"== {sav_editor.filename()}: {sav_editor.caption_data['country_name']}, {sav_editor.caption_data['season'].capitalize()} of {sav_editor.caption_data['year']}, {sav_editor.caption_data['difficulty']} {sav_editor.caption_data['name']}, {sav_editor.caption_data['gold']} gold ==")

        print("Actions list:")
        for num, rout in enumerate(routines, start=1):
            print(f"{num:2}. {rout[1]}")

        action_idx = get_input("Enter action index or press ENTER to quit: ", res_type=int, error_str="Wrong action index:", check_fun=lambda x: 1 <= x <= len(routines))
        if action_idx is None:
            if len(sav_editor.unsaved_changes) > 0:
                ans = get_input("There are unsaved changes. Do you want to skip them? [y/n]: ", res_type=str, error_str="Wrong answer:", check_fun=lambda x: x[0].lower() in ['y', 'n'])
                if ans is None or ans[0].lower() == 'n':
                    continue
            break

        routines[action_idx - 1][0](sav_editor)
        if not sav_editor.is_initialized:
            print(f"SAV file '{sav_editor.filename()}' BROKEN or ABSENT!")

    return


if __name__ == '__main__':
    print( "== Sid Meier's Colonization (1994) SAV files EDITOR ==")
    print(f"             by Pavel Bel. Version {REL_VER}")

    settings_json_filename = os.path.join(os.path.split(sys.argv[0])[0], 'smcol_sav_settings.json')
    settings = load_settings(settings_json_filename, DEFAULT_SETTINGS)

    FIELD_VALUES = handle_metadata(FIELD_VALUES, to_lowercase=False)

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

        try:
            with os.scandir(settings['colonize_path']) as scan_res:
                for dir_entry in scan_res:
                    if dir_entry.is_dir():
                        continue

                    file_type = None
                    if dir_entry.name.lower().endswith(".sav"):
                        file_type = 'sav'
                    else:
                        continue

                    curr_read_json_sav_data, _ = read_json_sav_data(dir_entry.path, json_sav_structure, sections_to_read=['HEAD', 'PLAYER', 'NATION'])
                    #sav_files_list.append((dir_entry.name, file_type, curr_read_json_sav_data))
                    sav_files_list.append({"name": dir_entry.name, "path": dir_entry.path, "type": file_type, "data": curr_read_json_sav_data})
        except:
            print(f"ERROR: Failed to scan '{settings['colonize_path']}' folder. Does it exist?")
            sys.exit(0)

        if len(sav_files_list) == 0:
            print("NO SAV files in current directory. Open the 'smcol_sav_settings.json' file and set 'colonize_path' value to COLONIZE folder of your Colonization installation")
            sys.exit(0)

        print()
        print("SAV and SAV.JSON files in the current folder:")
        bad_saves_idxs = []
        for i, sav_file_data in enumerate(sav_files_list, start=1):
            print(f"{i:2}. {sav_file_data['name']}", end=': ')
            caption_data = get_caption_data(sav_file_data['data'])
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

        chosen_filepath = sav_files_list[sav_idx - 1]['path']

        edit_sav_file(chosen_filepath, json_sav_structure)
