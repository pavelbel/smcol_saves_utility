import os
import sys
import time
import copy
from math import ceil
from datetime import datetime
from smcol_sav_converter import handle_metadata, read_sav_structure, REL_VER
from smcol_sav_common import *

TO_USE_COLORS = True

if TO_USE_COLORS:
    from colorama import *


def ifcolor(ss: str):
    """Function for disabling all coloring"""
    return ss if TO_USE_COLORS else ""


COL_RESET = ifcolor(Style.RESET_ALL)
COL_BRI = ifcolor(Style.BRIGHT)
COL_DIM = ifcolor(Style.DIM)


building_costs = {}  # Global building const dict. Will be filled later when FIELD_VALUES is ready

def init_building_costs():
    """Building costs data"""
    utypes = FIELD_VALUES['production_type']
    return {utypes['Stockade']: (64, 0), utypes['Fort']: (120, 100), utypes['Fortress']: (320, 200),
            utypes['Armory']: (52, 0), utypes['Magazine']: (120, 50), utypes['Arsenal']: (240, 100),
            utypes['Docks']: (52, 0), utypes['Drydock']: (80, 50), utypes['Shipyard']: (240, 100),
            utypes['Town Hall 1']: (64, 0), utypes['Town Hall 2']: (64, 50), utypes['Town Hall 3']: (120, 100),
            utypes['Schoolhouse']: (64, 0), utypes['College']: (160, 50), utypes['University']: (200, 100),
            utypes['Warehouse']: (80, 0), utypes['Warehouse Expansion']: (80, 20), utypes['Stable']: (64, 0),
            utypes['Custom House']: (160, 50), utypes['Printing Press']: (52, 20), utypes['Newspaper']: (120, 50),
            utypes["Weaver's House"]: (64, 0), utypes["Weaver's Shop"]: (64, 20), utypes["Textile Mill"]: (160, 100),
            utypes["Tobacconist's House"]: (64, 0), utypes["Tobacconist's Shop"]: (64, 20), utypes["Cigar Factory"]: (160, 100),
            utypes["Rum Distiller's House"]: (64, 0), utypes["Rum Distillery"]: (64, 20), utypes["Rum Factory"]: (160, 100),
            utypes["Capitol"]: (400, 100), utypes["Capitol Expansion"]: (400, 100),
            utypes["Fur Trader's House"]: (56, 0), utypes["Fur Trading Post"]: (56, 20), utypes["Fur Factory"]: (160, 100),
            utypes["Carpenter's Shop"]: (39, 0), utypes["Lumber Mill"]: (52, 0),
            utypes["Church"]: (64, 0), utypes["Cathedral"]: (176, 100),
            utypes["Blacksmith's House"]: (64, 0), utypes["Blacksmith's Shop"]: (64, 20), utypes["Iron Works"]: (240, 100),
            utypes["Artillery"]: (192, 40), utypes["Wagon Train"]: (40, 0),
            utypes['Caravel']: (128, 40), utypes['Merchantman']: (192, 80), utypes['Galleon']: (240, 100),
            utypes['Privateer']: (256, 120), utypes['Frigate']: (512, 200), utypes['(Nothing)']: (0, 0) }


def load_json_sav_data(fname: str):
    with open(fname, mode='rb') as sf:
        latest_sav_data = sf.read()

    read_metadata = handle_metadata(json_sav_structure['__metadata'])
    json_sav_data = read_sav_structure(json_sav_structure, latest_sav_data, read_metadata, ignore_compact=True, ignore_custom_type=True)

    # Если колония одна, то она не будет списком. Исправим это
    if 'COLONY' not in json_sav_data or json_sav_data['COLONY'] is None:
        json_sav_data['COLONY'] = []
    elif not isinstance(json_sav_data['COLONY'], list):
        json_sav_data['COLONY'] = [json_sav_data['COLONY']]

    # Если юнит один (но этого не бывает!), то он не будет списком. Исправим это
    if 'UNIT' not in json_sav_data or json_sav_data['UNIT'] is None:
        json_sav_data['UNIT'] = []
    elif not isinstance(json_sav_data['UNIT'], list):
        json_sav_data['UNIT'] = [json_sav_data['UNIT']]

    return json_sav_data


def get_all_and_players_units_count(json_sav_data, player_id):
    cnt = 0
    pl_cnt = 0
    for unit in json_sav_data['UNIT']:
        cnt += 1
        if int(unit['nation_info']['nation_id'], 2) == player_id:
            pl_cnt += 1

    return cnt, pl_cnt


def get_all_and_players_colonies_count(json_sav_data, player_id):
    cnt = 0
    pl_cnt = 0
    for colony in json_sav_data['COLONY']:
        cnt += 1
        if int(colony['nation_id'], 16) == player_id:
            pl_cnt += 1

    return cnt, pl_cnt


def get_rebel_val(colony, is_bolivar_present):
    """Get rebel sentiment value"""
    colony_rebel_val = int(colony['rebel_dividend'] / colony['rebel_divisor'] * 100)
    if is_bolivar_present:
        colony_rebel_val += 20
    return 100 if colony_rebel_val > 100 else colony_rebel_val


def add_unit_wn_data(colony, unit):
    """Add unit data"""
    curr_unit_type = unit['type']
    curr_unit_prof = unit['profession_or_treasure_amount']
    col_wn_data = colony['wn_data']
    if curr_unit_type in (FIELD_VALUES['unit_type']['soldier'], FIELD_VALUES['unit_type']['continental army']):
        if curr_unit_prof == FIELD_VALUES['profession_type']['veteran soldier']:
            col_wn_data['soldier'][0] += 1   # Veteran soldier
        else:
            col_wn_data['soldier'][1] += 1   # Rookie soldier
    elif curr_unit_type in (FIELD_VALUES['unit_type']['dragoon'], FIELD_VALUES['unit_type']['continental cavalry']):
        if curr_unit_prof == FIELD_VALUES['profession_type']['veteran soldier']:
            col_wn_data['dragoon'][0] += 1   # Veteran dragoon
        else:
            col_wn_data['dragoon'][1] += 1   # Rookie dragoon
    elif curr_unit_type == FIELD_VALUES['unit_type']['artillery']:
        if not unit['unknown15']['damaged']:
            col_wn_data['artillery'][0] += 1   # Artillery
        else:
            col_wn_data['artillery'][1] += 1   # Damaged artillery
    elif curr_unit_type == FIELD_VALUES['unit_type']['caravel']:
        col_wn_data['naval'] += "C"
    elif curr_unit_type == FIELD_VALUES['unit_type']['merchantman']:
        col_wn_data['naval'] += "M"
    elif curr_unit_type == FIELD_VALUES['unit_type']['galleon']:
        col_wn_data['naval'] += "G"
    elif curr_unit_type == FIELD_VALUES['unit_type']['privateer']:
        col_wn_data['naval'] += "P"
    elif curr_unit_type == FIELD_VALUES['unit_type']['frigate']:
        col_wn_data['naval'] += "F"
    elif curr_unit_type == FIELD_VALUES['unit_type']['man-o-war']:
        col_wn_data['naval'] += "W"

    pass


def match_cols_units(colonies, units, nation_id=None):
    """Find units for report"""
    wn_unit_types_raw = ('soldier', 'dragoon', 'continental cavalry', 'continental army', 'artillery',
                         'caravel', 'merchantman', 'galleon', 'frigate', 'man-o-war')
    wn_unit_types = set()
    for ut in wn_unit_types_raw:
        wn_unit_types.add(FIELD_VALUES['unit_type'][ut])

    # Prepare list of target units only
    war_and_naval_units = []
    for unit in units:
        unit_nation = int(unit['nation_info']['nation_id'], 2)
        if unit_nation > 3 or (nation_id and unit_nation != nation_id) or (unit['type'] not in wn_unit_types):
            continue
        war_and_naval_units.append(unit)

    # Prepare list of target colonies only
    if nation_id:
        players_colonies = []
        for colony in colonies:
            if int(colony['nation_id'], 16) != nation_id:
                continue
            players_colonies.append(colony)
    else:
        players_colonies = colonies

    # Main cycle
    wn_colony_empty_data = {'soldier': [0, 0], 'dragoon': [0, 0], 'artillery': [0, 0], 'naval': ""}
    for unit in war_and_naval_units:
        for colony in players_colonies:
            if 'wn_data' not in colony:
                colony['wn_data'] = copy.deepcopy(wn_colony_empty_data)
            if unit['x, y'] != colony['x, y']:
                continue
            add_unit_wn_data(colony, unit)

    pass


def get_diff_str(diff_value, width=1, coloring=True, custom_color="", result_len=None):
    """Get +X or -X string"""
    abs_diff_value_str = str(abs(diff_value))
    abs_diff_value_str += " " * (width - len(abs_diff_value_str))
    diff_value_str = f"+{abs_diff_value_str}" if diff_value >= 0 else f"-{abs_diff_value_str}"
    if isinstance(result_len, list) and len(result_len) == 0:
        diff_value_str_len = len(diff_value_str)
        result_len.append(diff_value_str_len)
    diff_color_str = ifcolor(Fore.LIGHTGREEN_EX) if diff_value > 0 else ifcolor(Fore.RED) if diff_value < 0 else ""
    color_str = diff_color_str if len(custom_color) == 0 else custom_color
    return diff_value_str if not coloring else color_str+diff_value_str+COL_RESET


def get_stock_state_str(colony, prev_colony, stock_name, is_neg_critical=False, width=9, max_cap=1000000):
    """Get stock 'stock_name' state string"""
    stock_inc = 0 if prev_colony is None else colony['stock'][stock_name] - prev_colony['stock'][stock_name]
    next_val = colony['stock'][stock_name] + stock_inc
    custom_color_str = Back.LIGHTRED_EX if (is_neg_critical and next_val < 0) else ""
    stock_val_color_str = COL_BRI if colony['stock'][stock_name] < max_cap else ifcolor(Fore.YELLOW)
    stock_val_str = str(colony['stock'][stock_name])
    diff_str_len = []
    stock_state_str = f"{COL_BRI}({get_diff_str(stock_inc, custom_color=custom_color_str, result_len=diff_str_len)}){stock_val_color_str}{stock_val_str}{COL_RESET}"
    full_stock_state_len = 1 + diff_str_len[0] + 1 + len(stock_val_str)
    if full_stock_state_len < width:
        stock_state_str += " " * (width - full_stock_state_len)
    return stock_state_str


def run_advisor(json_sav_data, prev_json_sav_data):
    """Main advisor data output function"""

    caption_data = get_caption_data(json_sav_data, FIELD_VALUES)
    print(f"\n{caption_data['country_name']}, {caption_data['season'].capitalize()} of {caption_data['year']}, {caption_data['difficulty']} {caption_data['name']}, {caption_data['gold']} gold")

    units_counts = get_all_and_players_units_count(json_sav_data, caption_data['player_nation_id'])
    colonies_counts = get_all_and_players_colonies_count(json_sav_data, caption_data['player_nation_id'])
    print(f"All units: {units_counts[0]}. Player's units: {units_counts[1]}")
    print(f"All colonies: {colonies_counts[0]}. Player's colonies: {colonies_counts[1]}")

    print()

    match_cols_units(json_sav_data['COLONY'], json_sav_data['UNIT']) #, nation_id)

    num = 0
    for colony in json_sav_data['COLONY']:
        # if int(colony['nation_id'], 16) != caption_data['player_nation_id']:
        #     continue
        prev_colony = None
        if prev_json_sav_data is not None:
            for prev_col in prev_json_sav_data['COLONY']:
                if prev_col['name'] == colony['name']:
                    prev_colony = prev_col
                    break
        num += 1

        # Fortification
        col_fort_val = int(colony['buildings']['fortification'], 2)
        col_fortification_str = "___" if col_fort_val == 0 else "===" if col_fort_val == 1 else "###" if col_fort_val == 3 else "III" if col_fort_val == 7 else "???"
        #print(f"({COL_BRI}{col_fortification_str}{COL_RESET})", end=" ")
        print(f"{COL_BRI}{col_fortification_str}{COL_RESET}", end=" ")

        # Colony's name
        col_name_color = ifcolor(Fore.LIGHTCYAN_EX) if colony['colony_flags']['level2_sol_bonus'] else ifcolor(Fore.LIGHTGREEN_EX) if colony['colony_flags']['level1_sol_bonus'] else ""
        print(COL_BRI + col_name_color + colony['name'], COL_RESET + f"[{COL_BRI}{colony['population']}{COL_RESET}]", end=" ")  #f"{num}."

        # Rebel sentiment percent value
        colony_rebel_val = get_rebel_val(colony, json_sav_data['NATION'][int(colony['nation_id'], 16)]['founding_fathers']['simon_bolivar'])
        prev_colony_rebel_val = 0
        if prev_colony:
            prev_colony_rebel_val = get_rebel_val(prev_colony, prev_json_sav_data['NATION'][int(colony['nation_id'], 16)]['founding_fathers']['simon_bolivar'])
        rebel_val_inc_str = get_diff_str(colony_rebel_val - prev_colony_rebel_val)
        #print(f"Rebel: {COL_BRI}{colony_rebel_val}({rebel_val_inc_str})%{COL_RESET}", end=" ")
        print(f"({COL_BRI}{rebel_val_inc_str}){COL_BRI}{col_name_color}{colony_rebel_val}%{COL_RESET}", end=" ")

        # Garrison
        col_wn_data = colony['wn_data']
        print(f"Sldr:{COL_BRI}{col_wn_data['soldier'][0]}+{col_wn_data['soldier'][1]}{COL_RESET} Drgn:{COL_BRI}{col_wn_data['dragoon'][0]}+{col_wn_data['dragoon'][1]}{COL_RESET} Art:{COL_BRI}{col_wn_data['artillery'][0]}+{col_wn_data['artillery'][1]}{COL_RESET} Naval:{COL_BRI}{col_wn_data['naval']}{COL_RESET}")

        ### Building
        if colony['building_in_production'] not in FIELD_VALUES['production_type_inv']:
            colony['building_in_production'] = FIELD_VALUES['production_type']['(Nothing)']

        print(f"Building: {COL_BRI}{ifcolor(Fore.LIGHTBLUE_EX)}{FIELD_VALUES['production_type_inv'][colony['building_in_production']]}{COL_RESET}", end=" ")

        col_wrhs_capacity = (colony['warehouse_level'] + 1) * 100

        build_cost = building_costs[colony['building_in_production']]

        # Hammers data
        hammers_inc = 0 if prev_colony is None else colony['hammers'] - prev_colony['hammers']
        hamm_turns_remain = 1
        hamm_turns_color = ""
        if build_cost[0] > colony['hammers']:
            if hammers_inc > 0:
                hamm_turns_remain = ceil((build_cost[0] - colony['hammers']) / hammers_inc)
            elif hammers_inc <= 0:
                hamm_turns_remain = "???"
                hamm_turns_color = ifcolor(Back.LIGHTRED_EX)
        if hamm_turns_remain != "???":
            hamm_turns_color =  ifcolor(Fore.LIGHTCYAN_EX) if hamm_turns_remain <= 2 else \
                                ifcolor(Fore.LIGHTGREEN_EX) if hamm_turns_remain <= 5 else \
                                ifcolor(Fore.LIGHTRED_EX) if hamm_turns_remain >= 10 else ""

        print(f"Hamm:{COL_BRI}({get_diff_str(hammers_inc)}{COL_BRI}){colony['hammers']}/{build_cost[0]}{COL_RESET}", end="")
        print(f"[{COL_BRI}{hamm_turns_color}{hamm_turns_remain}{COL_RESET}t]", end=" ")

        # Tools data
        tools_inc = 0 if prev_colony is None else colony['stock']['tools'] - prev_colony['stock']['tools']
        tools_turns_remain = 1
        tools_turns_color = ""
        if build_cost[1] > colony['stock']['tools']:
            if tools_inc > 0:
                tools_turns_remain = ceil((build_cost[1] - colony['stock']['tools']) / tools_inc)
            elif tools_inc <= 0:
                tools_turns_remain = "???"
                tools_turns_color = ifcolor(Back.LIGHTRED_EX)
        if tools_turns_remain != "???":
            tools_turns_color = ifcolor(Fore.LIGHTCYAN_EX) if tools_turns_remain <= 2 else \
                                ifcolor(Fore.LIGHTGREEN_EX) if tools_turns_remain <= 5 else \
                                ifcolor(Fore.LIGHTRED_EX) if tools_turns_remain >= 10 else ""

        if colony['stock']['tools'] >= col_wrhs_capacity:
            col_tools_stock_color_str = ifcolor(Fore.YELLOW)
        else:
            col_tools_stock_color_str = COL_BRI
        print(f"Tool:({COL_BRI}{get_diff_str(tools_inc)}){col_tools_stock_color_str}{str(colony['stock']['tools'])}{COL_RESET}/{COL_BRI}{build_cost[1]}{COL_RESET}", end="")
        print(f"[{COL_BRI}{tools_turns_color}{tools_turns_remain}{COL_RESET}t]")

        # Stock data
        print(f"Food:{get_stock_state_str(colony, prev_colony, 'food', is_neg_critical=True, max_cap=col_wrhs_capacity)}", end=" ")
        print(f"Lmbr:{get_stock_state_str(colony, prev_colony, 'lumber', max_cap=col_wrhs_capacity)}", end=" ")
        print(f" Ore:{get_stock_state_str(colony, prev_colony, 'ore', max_cap=col_wrhs_capacity)}", end=" ")
        print()
        print(f"Sugr:{get_stock_state_str(colony, prev_colony, 'sugar', max_cap=col_wrhs_capacity)}", end=" ")
        print(f" Rum:{get_stock_state_str(colony, prev_colony, 'rum', max_cap=col_wrhs_capacity)}", end=" ")
        print(f" Tob:{get_stock_state_str(colony, prev_colony, 'tobacco', max_cap=col_wrhs_capacity)}", end=" ")
        print(f" Cig:{get_stock_state_str(colony, prev_colony, 'cigars', max_cap=col_wrhs_capacity)}", end=" ")
        print()
        print(f"Cott:{get_stock_state_str(colony, prev_colony, 'cotton', max_cap=col_wrhs_capacity)}", end=" ")
        print(f"Clth:{get_stock_state_str(colony, prev_colony, 'cloth', max_cap=col_wrhs_capacity)}", end=" ")
        print(f" Fur:{get_stock_state_str(colony, prev_colony, 'furs', max_cap=col_wrhs_capacity)}", end=" ")
        print(f"Coat:{get_stock_state_str(colony, prev_colony, 'coats', max_cap=col_wrhs_capacity)}", end=" ")
        print()
        print(f"Hors:{get_stock_state_str(colony, prev_colony, 'horses', max_cap=col_wrhs_capacity)}", end=" ")
        print(f"Mskt:{get_stock_state_str(colony, prev_colony, 'muskets', max_cap=col_wrhs_capacity)}", end=" ")
        print(f"Slvr:{get_stock_state_str(colony, prev_colony, 'silver', max_cap=col_wrhs_capacity)}", end=" ")
        print(f"TrGd:{get_stock_state_str(colony, prev_colony, 'trade_goods', max_cap=col_wrhs_capacity)}", end=" ")
        print()


        print()

    print("=" * 80)
    sys.exit(0)
    pass


def dummy_main():
    pass


if __name__ == '__main__':
    just_fix_windows_console()

    print()
    print("== Sid Meier's Colonization (1994) ADVISOR ==")
    print(f"      by Pavel Bel. Version {REL_VER}")

    default_settings = {"colonize_path": "."}
    settings_json_filename = os.path.join(os.path.split(sys.argv[0])[0], 'smcol_sav_settings.json')
    settings = load_settings(settings_json_filename, default_settings)

    FIELD_VALUES = handle_metadata(FIELD_VALUES, to_lowercase=False)
    building_costs = init_building_costs()

    json_struct_filename = 'smcol_sav_struct.json'
    is_sav_structure_loaded = False
    try:
        with open(json_struct_filename, mode='rt') as sjf:
            json_sav_structure = json.load(sjf)
        is_sav_structure_loaded = True
    except Exception as ex:
        print(f"WARNING: problem with JSON SAV structure file '{json_struct_filename}': {ex}")

    if not is_sav_structure_loaded:
        print(f"ERROR: JSON SAV structure file '{json_struct_filename}' cannot be loaded. Aborting")

    col_autosav_1_filename = os.path.join(settings['colonize_path'], 'COLONY09.SAV')
    col_autosav_2_filename = os.path.join(settings['colonize_path'], 'COLONY08.SAV')

    curr_last_file_mtime_ns = max(os.stat(col_autosav_1_filename).st_mtime_ns, os.stat(col_autosav_2_filename).st_mtime_ns) - 1

    WAIT_STR = "\nWaiting for updates of autosave files... Press Ctrl+C to abort"
    POLL_INTERVAL = 1 # secs
    json_sav_data = load_json_sav_data(os.path.join(settings['colonize_path'], 'COLONY00.SAV')) # None
    try:
        while True:
            curr_1_time_ns = os.stat(col_autosav_1_filename).st_mtime_ns
            curr_2_time_ns = os.stat(col_autosav_2_filename).st_mtime_ns
            if curr_1_time_ns > curr_2_time_ns:
                curr_last_time_ns = curr_1_time_ns
                curr_last_filename = col_autosav_1_filename
            else:
                curr_last_time_ns = curr_2_time_ns
                curr_last_filename = col_autosav_2_filename

            if curr_last_time_ns <= curr_last_file_mtime_ns:
                time.sleep(POLL_INTERVAL)
                continue

            # Make sure the curr_last_filename file is closed (can be opened for writing)
            try:
                with open(curr_last_filename, "ab"):
                    pass
            except Exception as ex:
                time.sleep(POLL_INTERVAL)
                continue

            curr_last_file_mtime_ns = curr_last_time_ns

            last_file_mod_dt = datetime.fromtimestamp(curr_last_file_mtime_ns / 1e9)

            print("\n=============================================================")
            print(f"SAV file '{curr_last_filename}' updated at {last_file_mod_dt}:")

            prev_json_sav_data = json_sav_data.copy()
            try:
                json_sav_data = load_json_sav_data(curr_last_filename)
            except Exception as ex:
                print(f"ERROR: {curr_last_filename} file read/parse error: {ex}")
            else:
                run_advisor(json_sav_data, prev_json_sav_data)

            print(WAIT_STR)

            pass
    except KeyboardInterrupt as ex:
        print("Ctrl+C pressed, exiting...")
        sys.exit(0)


