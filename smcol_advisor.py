import os
import sys
import time
from datetime import datetime
from smcol_sav_converter import handle_metadata, read_sav_structure, REL_VER
from smcol_sav_common import *

TO_USE_COLORS = True

if TO_USE_COLORS:
    from colorama import *


def ifcolor(ss: str):
    """Function for disabling all coloring"""
    return ss if TO_USE_COLORS else ""


COLRESET = ifcolor(Style.RESET_ALL)


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


def run_advisor(json_sav_data, prev_json_sav_data):
    """Main advisor data output function"""

    caption_data = get_caption_data(json_sav_data, FIELD_VALUES)
    print(f"\n{caption_data['country_name']}, {caption_data['season'].capitalize()} of {caption_data['year']}, {caption_data['difficulty']} {caption_data['name']}, {caption_data['gold']} gold")

    units_counts = get_all_and_players_units_count(json_sav_data, caption_data['player_nation_id'])
    colonies_counts = get_all_and_players_colonies_count(json_sav_data, caption_data['player_nation_id'])
    print(f"All units: {units_counts[0]}. Player's units: {units_counts[1]}")
    print(f"All colonies: {colonies_counts[0]}. Player's colonies: {colonies_counts[1]}")

    print()

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

        col_name_color = ifcolor(Fore.LIGHTCYAN_EX) if colony['colony_flags']['level2_sol_bonus'] else ifcolor(Fore.LIGHTGREEN_EX) if colony['colony_flags']['level1_sol_bonus'] else ""
        print(f"{num}.", col_name_color + colony['name'], COLRESET + f"({colony['population']}):", end=" ")

        colony_rebel_val = get_rebel_val(colony, json_sav_data['NATION'][int(colony['nation_id'], 16)]['founding_fathers']['simon_bolivar'])
        prev_colony_rebel_val = 0
        if prev_colony:
            prev_colony_rebel_val = get_rebel_val(prev_colony, prev_json_sav_data['NATION'][int(colony['nation_id'], 16)]['founding_fathers']['simon_bolivar'])

        rebel_val_inc_str = f"+{colony_rebel_val - prev_colony_rebel_val}" if colony_rebel_val - prev_colony_rebel_val >= 0 else f"-{prev_colony_rebel_val - colony_rebel_val}"
        print(f"Rebel: {colony_rebel_val}({rebel_val_inc_str})%.", end=" ")

        if colony['building_in_production'] in FIELD_VALUES['production_type_inv']:
            print("Building:", FIELD_VALUES['production_type_inv'][colony['building_in_production']], end=" ")
            hammers_inc = 0 if prev_colony is None else colony['hammers'] - prev_colony['hammers']
            print(f"[H: {colony['hammers']}(+{hammers_inc})]")
        else:
            print("Building: (Nothing)")

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


