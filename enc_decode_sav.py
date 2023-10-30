import os
import json
import time
import sys
from smcol_sav_converter import handle_metadata, read_sav_structure, dump_sav_structure, prepare_sav_struct_for_optional_indent, REL_VER
from partial_indent_json_encoder import *
from smcol_sav_common import *


def prepare_backups_sequence(base_filename, backups_count):
    if backups_count > 0:
        make_backup_filename = lambda i: base_filename + f'.prev_{i}' if i > 0 else base_filename
        # Saving backups
        for backup_i in range(backups_count, 0, -1):
            bck_fname_i = make_backup_filename(backup_i)
            bck_fname_i_1 = make_backup_filename(backup_i - 1)
            try:
                os.replace(bck_fname_i_1, bck_fname_i)
                print(f"Backup: {bck_fname_i_1} saved as {bck_fname_i}")
            except:
                pass


def decode_sav_file(sav_filename: str, sav_structure: dict, settings: dict):
    try:
        with open(sav_filename, mode='rb') as sf:
            sav_data = sf.read()

        read_metadata = handle_metadata(sav_structure['__metadata'])
        read_struct_data = read_sav_structure(sav_structure, sav_data, read_metadata, ignore_compact=settings['enc_decoder']['ignore_compact'])
        read_struct_data['__structure'] = sav_structure

        decoded_sav_json_data_filename = sav_filename + '.json'
        decoded_sav_json_data_filename_tmp = decoded_sav_json_data_filename + '.tmp'

        prepare_sav_struct_for_optional_indent(read_struct_data, sav_structure)

        # Save structured SAV data to JSON file sav_json_data_filename: to tmp file at first
        with open(decoded_sav_json_data_filename_tmp, mode='wt') as svftj:
            json.dump(read_struct_data, svftj, indent=4, cls=PartialNoIndentJSONEncoder)

        backups_count = settings['enc_decoder']['json_backups_to_store']
        prepare_backups_sequence(decoded_sav_json_data_filename, backups_count)

        # if tmp file is ok -> to final .json file
        os.replace(decoded_sav_json_data_filename_tmp, decoded_sav_json_data_filename)

    except Exception as ex:
        print(f"ERROR: SAV file '{sav_filename}' decoding failure: {ex}")
    else:
        print(f"SAV file '{sav_filename}' decoding SUCCESS! JSON structured data written to '{decoded_sav_json_data_filename}'")


def encode_sav_file(json_sav_filename: str, settings: dict):
    try:
        with open(json_sav_filename, mode='rt') as sjf:
            read_struct_data = json.load(sjf)

        loaded_sav_structure = read_struct_data['__structure']
        loaded_metadata = handle_metadata(loaded_sav_structure['__metadata'])

        # Serialize and dump JSON data to original binary SAV format
        enc_sav_data = dump_sav_structure(read_struct_data, loaded_sav_structure, loaded_metadata)
        #saved_filename = os.path.splitext(json_sav_filename)[0][:-2] + '07.SAV'
        #saved_filename = os.path.splitext(json_sav_filename)[0] + '.enc'
        saved_filename = os.path.splitext(json_sav_filename)[0]
        saved_filename_tmp = saved_filename + '.tmp'

        # writing SAV to tmp file
        with open(saved_filename_tmp, mode='wb') as svftenc:
            svftenc.write(enc_sav_data)

        # creating backups
        backups_count = settings['enc_decoder']['sav_backups_to_store']
        prepare_backups_sequence(saved_filename, backups_count)

        # renaming tmp file
        os.replace(saved_filename_tmp, saved_filename)


    except Exception as ex:
        print(f"ERROR: SAV.JSON file '{json_sav_filename}' encoding failure: {ex}")
    else:
        print(f"SAV.JSON file '{json_sav_filename}' encoding SUCCESS! Binary SAV data written to '{saved_filename}'. ")


if __name__ == '__main__':
    print()
    print("== Sid Meier's Colonization (1994) SAV files DECODER and ENCODER ==")
    print(f"                   by Pavel Bel. Version {REL_VER}")

    default_settings = {"colonize_path": ".", "enc_decoder": {"ignore_compact": False, "auto_update_mode": False, "sav_backups_to_store": 1, "json_backups_to_store": 3}}
    settings_json_filename = os.path.join(os.path.split(sys.argv[0])[0], 'smcol_sav_settings.json')
    settings = load_settings(settings_json_filename, default_settings)

    try:
        auto_update_mode = settings['enc_decoder']['auto_update_mode']
    except:
        print("WARNING: incorrect or absent 'auto_update_mode' value")
        auto_update_mode = default_settings['enc_decoder']['auto_update_mode']

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

        try:
            with os.scandir(settings['colonize_path']) as scan_res:
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
                    sav_files_list.append({"name": dir_entry.name, "path": dir_entry.path, "type": file_type})
        except:
            print(f"ERROR: Failed to scan '{settings['colonize_path']}' folder. Does it exist?")
            sys.exit(0)

        if len(sav_files_list) == 0:
            print("NO SAV files in current directory. Open the 'smcol_sav_settings.json' file and set 'colonize_path' value to COLONIZE folder of your Colonization installation")
            sys.exit(0)

        sav_files_list.sort(key=lambda x: x["name"])

        print()
        print(f"AUTO UPDATE mode is: {'ON' if auto_update_mode else 'OFF'}. SAV and SAV.JSON files in the current folder:")
        for i, sav_file_data in enumerate(sav_files_list, start=1):
            print(f"{i}. {sav_file_data['name']}")

        sav_idx = get_input("Enter file index to decode or encode it or 0 to toggle AUTO UPDATE mode or press ENTER to quit: ", res_type=int, error_str="Wrong SAV file index:", check_fun=lambda x: 0 <= x <= len(sav_files_list))
        if sav_idx is None:
            break

        if sav_idx == 0:
            auto_update_mode = not auto_update_mode
            continue

        chosen_filename = sav_files_list[sav_idx-1]['path']

        while True:
            chosen_file_mtime_ns = os.stat(chosen_filename).st_mtime_ns

            print()
            if sav_files_list[sav_idx-1]['type'] == 'sav':
                if is_sav_structure_loaded:
                    decode_sav_file(chosen_filename, json_sav_structure, settings)
                else:
                    print("ERROR: json_sav_structure not loaded, you cannot decode SAV files!")
                    break
            else:
                encode_sav_file(chosen_filename, settings)

            if not auto_update_mode:
                break

            # Waiting for changes of chosen_filename
            print(f"Waiting for changes in '{chosen_filename}'... Press Ctrl+C to abort")
            try:
                while True:
                    time.sleep(0.5)
                    if os.stat(chosen_filename).st_mtime_ns != chosen_file_mtime_ns:
                        is_accessible = False
                        # Make sure the chosen_filename file is closed (can be opened for writing)
                        try:
                            with open(chosen_filename, "ab"):
                                is_accessible = True
                        except Exception as ex:
                            pass

                        if is_accessible:
                            break
            except KeyboardInterrupt as ex:
                break

            deb = 0
