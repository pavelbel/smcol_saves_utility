import json
import os
import sys
import hashlib

from bitarray import bitarray, util
from partial_indent_json_encoder import *

SAV_STRUCT_JSON_FILENAME = r'smcol_sav_struct.json'
#SAV_STRUCT_JSON_FILENAME = r'smcol_sav_struct_old.json'
#SAV_FILENAME = r'D:\Games\GOG.com\Colonization\MPS\COLONIZE\COLONY03.SAV'
# SAV_FILENAME = r'COLONY07.SAV'
SAV_FILENAME = r'COLONY01.SAV'


def get_entry_count(entry, metadata):
    curr_entry_count = entry.get('count', 1)
    if isinstance(curr_entry_count, str):
        curr_entry_count = int.from_bytes(metadata[curr_entry_count], "little")

    curr_entry_cols = entry.get('cols', 1)
    if isinstance(curr_entry_cols, str):
        curr_entry_cols = int.from_bytes(metadata[curr_entry_cols], "little")

    return curr_entry_count, curr_entry_cols


def get_entry_size(entry, metadata):
    if entry.get('size', None) is not None:
        return entry['size']

    ssize = 0
    if 'struct' in entry:
        for inner_entry_name, inner_entry_data in entry['struct'].items():
            ie_r, ie_c = get_entry_count(inner_entry_data, metadata)
            ssize += get_entry_size(inner_entry_data, metadata) * ie_r * ie_c
    elif 'bit_struct' in entry:
        for inner_entry_name, inner_entry_data in entry['bit_struct'].items():
            ie_r, ie_c = get_entry_count(inner_entry_data, metadata)
            ssize += get_entry_size(inner_entry_data, metadata) * ie_r * ie_c
        if ssize % 8 != 0:
            print("WARNING: bit len of a field is not aligned! Aligning manually")
            ssize += 8 - ssize % 8
        ssize //= 8
    else:
        raise  # Cannot calculate size of the field given

    return ssize


def deserialize(val: [bytes, bitarray], struct_data: dict, metadata: dict, to_print_typename=False):
    """Decode bytes data to target type or to string of bytes values"""

    to_type = struct_data.get('type', None)

    if "bit_struct" in struct_data:
        bit_struct_data = struct_data["bit_struct"]
        curr_bit_offset = 0
        in_res_data = {}

        bit_arr = bitarray()
        bit_arr.frombytes(val)
        bit_arr.bytereverse()

        for struct_entry_key, struct_entry_value in bit_struct_data.items():
            curr_entry_bit_size = struct_entry_value['size']  # Сделать правильно!
            curr_bit_substr = bit_arr[curr_bit_offset: curr_bit_offset + curr_entry_bit_size][::-1]
            if ('type' in struct_entry_value) and (struct_entry_value['type'] != 'bits'):
                in_res_data[struct_entry_key] = deserialize(curr_bit_substr, struct_entry_value, metadata)
            else:
                in_res_data[struct_entry_key] = curr_bit_substr.to01()
            curr_bit_offset += curr_entry_bit_size
        return in_res_data
    elif to_type == "int":
        if isinstance(val, bytes):
            return int.from_bytes(val, 'little', signed=True)
        elif isinstance(val, bitarray):
            return util.ba2int(val, signed=True)
    elif to_type == "uint":
        if isinstance(val, bytes):
            return int.from_bytes(val, 'little', signed=False)
        elif isinstance(val, bitarray):
            return util.ba2int(val, signed=False)
    elif to_type == "str":
        return val.decode(encoding='ascii').split(sep='\x00')[0] #replace(b'\x00', b'')
    elif to_type == "bits":
        out_str = ""
        for bb in val:
            out_str += f"{bb:08b} "
        out_str = out_str[:-1]
        return out_str + (' (bits)' if to_print_typename else '')
    elif to_type == "coords":
        x = int.from_bytes(val[0:1], 'little', signed=False)
        y = int.from_bytes(val[1:2], 'little', signed=False)
        return f"{x}, {y}"
    elif to_type == "bit_bool":
        if val == bitarray('1'):
            return True
        elif val == bitarray('0'):
            return False
        else:
            print(f"WARNING: wrong value '{val}' in a bit bool field")
            return False
    elif to_type in metadata:
        inv_type = to_type + '_inv'
        try:
            if isinstance(val, bitarray):
                key_name = val.to01()
            else:
                key_name = val.hex(sep=' ').upper()
            return metadata[inv_type][key_name]
        except KeyError as kex:
            print(f"WARNING: no value '{key_name}' of type '{to_type}', leaving it 'as is'")
            return deserialize(val, {}, metadata)
        except:
            raise
    else:
        if to_type is not None:
            print(f"WARNING: Unknown type: {to_type}")

        return val.hex(sep=' ').upper()


def serialize(data, data_structure, metadata: dict, to_type=bytes):
    """Encode data to bytes"""

    if "bit_struct" in data_structure:
        bit_struct_data = data_structure["bit_struct"]

        full_bit_str = bitarray()
        if data_structure.get('compact', False):
            if not isinstance(data[0], list):
                data = [[data]]
            elif not isinstance(data[0][0], list):
                data = [data]
        else:
            if not isinstance(data, list):
                data = [[data]]
            elif not isinstance(data[0], list):
                data = [data]

        for data_row in data:
            for data_entry in data_row:
                if data_structure.get('compact', False):
                    full_data_entry = {}
                    for i, key_name in enumerate(bit_struct_data):
                        full_data_entry[key_name] = data_entry[i]
                    data_entry = full_data_entry

                for data_key, data_value in data_entry.items():
                    curr_entry_bit_size = bit_struct_data[data_key]['size']  # Сделать правильно!
                    if ('type' in bit_struct_data[data_key]) and (bit_struct_data[data_key]['type'] != 'bits'):
                        #full_data_str += serialize(data_value, bit_struct_data[data_key], metadata)[:curr_entry_bit_size][::-1].to01()
                        full_bit_str += serialize(data_value, bit_struct_data[data_key], metadata, to_type=bitarray)[:curr_entry_bit_size][::-1]
                    else:
                        #full_data_str += data_value.replace(' ', '')[:curr_entry_bit_size][::-1]
                        full_bit_str += bitarray(data_value)[:curr_entry_bit_size][::-1]

        full_bit_str.bytereverse()
        bytes_data = full_bit_str.tobytes()
        return bytes_data
    elif "type" not in data_structure:
        return bytes.fromhex(data)
    if data_structure["type"] == "int":
        if to_type == bytes:
            bytes_data = data.to_bytes(data_structure["size"], byteorder='little', signed=True)
            return bytes_data
        elif to_type == bitarray:
            return util.int2ba(data, length=data_structure["size"], signed=True)
        else:
            raise Exception(f"ERROR: unknown target type: '{to_type}'")
    if data_structure["type"] == "uint":
        if to_type == bytes:
            bytes_data = data.to_bytes(data_structure["size"], byteorder='little', signed=False)
            return bytes_data
        elif to_type == bitarray:
            return util.int2ba(data, length=data_structure["size"], signed=False)
        else:
            raise Exception(f"ERROR: unknown target type: '{to_type}'")
    elif data_structure["type"] == "str":
        bytes_data = data.encode(encoding='ascii')
        if len(bytes_data) < data_structure["size"]:
            bytes_data += b'\x00' * (data_structure["size"] - len(bytes_data))
        return bytes_data
    elif data_structure["type"] == "bits":
        bits_data = bitarray(data)
        bytes_data = bits_data.tobytes()
        return bytes_data
    elif data_structure["type"] == "coords":
        vals_strs = data.replace(' ', '').split(sep=',')
        bytes_data = int(vals_strs[0]).to_bytes(1, byteorder='little', signed=False) + int(vals_strs[1]).to_bytes(1, byteorder='little', signed=False)
        return bytes_data
    elif data_structure["type"] == "bit_bool":
        if data == True:
            return bitarray('1')
        elif data == False:
            return bitarray('0')
        else:
            print(f"WARNING: wrong value '{data}' in a bit_bool field. Setting it to False")
            return bitarray('0')
    elif data_structure["type"] in metadata:
        key_name = data.lower() if isinstance(data, str) else data
        try:
            data_str = metadata[data_structure["type"]][key_name]
        except KeyError as kex:
            print(f"WARNING: no value '{key_name}' of type '{data_structure['type']}', leaving it 'as is'")
            data_str = data

        if to_type == bytes:
            return bytes.fromhex(data_str)
        elif to_type == bitarray:
            return bitarray(data_str)
        else:
            raise Exception(f"ERROR: unknown target type: '{to_type}'")
    else:
        return bytes.fromhex(data)


def reverse_dict(in_dict: dict):
    """Reverse dict"""
    return {y: x for (x, y) in in_dict.items()}


def lowercase_dict(in_dict: dict):
    """Lowercase string key values"""
    return {x.lower() if isinstance(x, str) else x : y for (x, y) in in_dict.items()}


def handle_metadata(entry_metadata):
    """Handle metadata - save it to metadata object"""

    metadata = {}
    # extract types from entry_metadata
    for entry_name, entry_data in entry_metadata.items():
        if entry_name.startswith('__'):
            continue

        if isinstance(entry_data, dict):
            metadata[entry_name] = lowercase_dict(entry_data)
            metadata[entry_name + '_inv'] = reverse_dict(entry_data)

    return metadata


def read_sav_structure(sav_structure, sav_data, metadata, prefix='', data_offset=0, log_file=None):
    """Read structured SAV data to JSON file IN NEW FORMAT"""

    read_res = {}

    curr_data_offset = data_offset
    for entry_name, entry_data in sav_structure.items():
        if entry_name.startswith('__'):
            continue

        try:
            curr_entry_size = get_entry_size(entry_data, metadata)
        except:
            raise Exception(f"ERROR: cannot calculate size of field '{entry_name}'")

        curr_entry_count, curr_entry_cols = get_entry_count(entry_data, metadata)
        #total_entry_size = curr_entry_count * curr_entry_size

        full_list = None
        for entry_ex in range(curr_entry_count):
            row_list = None
            for entry_col in range(curr_entry_cols):
                #save_as_string = True
                if 'struct' in entry_data:
                    in_res_data = read_sav_structure(entry_data['struct'], sav_data, metadata, prefix=prefix + '> ', data_offset=curr_data_offset, log_file=log_file)
                    #save_as_string = False
                else:
                    in_res_data = sav_data[curr_data_offset:curr_data_offset + curr_entry_size]
                    if entry_data.get('save_meta', False):
                        metadata[entry_name] = in_res_data
                    #in_res_data = in_res_data.hex(sep=' ').upper()
                    in_res_data = deserialize(in_res_data, entry_data, metadata)#, to_print_typename=entry_col == curr_entry_cols - 1)

                if entry_data.get('compact', False) and isinstance(in_res_data, dict):
                    #in_res_data = ''.join([str(dt[1]) for dt in in_res_data.items()])
                    in_res_data = [dt[1] for dt in in_res_data.items()]

                if entry_col == 0:
                    row_list = in_res_data
                elif entry_col == 1:
                    # if save_as_string:
                    #     row_list += ' ' + in_res_data
                    # else:
                        row_list = [row_list, in_res_data]
                else:
                    # if save_as_string:
                    #     row_list += ' ' + in_res_data
                    # else:
                        #row_list = [row_list, in_res_data]
                    row_list.append(in_res_data)

                    #row_list.append(in_res_data)

                curr_data_offset += curr_entry_size

            if entry_ex == 0:
                full_list = row_list
            elif entry_ex == 1:
                full_list = [full_list, row_list]
            else:
                full_list.append(row_list)

        #read_res.append({entry['name']: full_list})
        read_res[entry_name] = full_list
        #read_res.append((entry['name'], full_list))
        #read_res.append({'name': entry['name'], 'data': full_list})

    return read_res


def dump_sav_structure(read_struct_data, data_structure, metadata):
    """Сериализация JSON-структурированных SAV данных обратно в bytes"""

    res_data = b''
    if read_struct_data is None:
        return res_data

    if 'bit_struct' in data_structure:
        res_data += serialize(read_struct_data, data_structure, metadata)
    elif isinstance(read_struct_data, list):
        for entry in read_struct_data:
            res_data += dump_sav_structure(entry, data_structure, metadata)
    elif isinstance(read_struct_data, dict):
        for entry_name, entry_data in read_struct_data.items():
            if entry_name.startswith('__'):
                continue
            if 'struct' in data_structure[entry_name]:
                if data_structure[entry_name].get('compact', False):
                    full_entry_data = {}
                    for i, key_name in enumerate(data_structure[entry_name]['struct']):
                        full_entry_data[key_name] = entry_data[i]
                    entry_data = full_entry_data

                res_data += dump_sav_structure(entry_data, data_structure[entry_name]['struct'], metadata)
            else:
                res_data += dump_sav_structure(entry_data, data_structure[entry_name], metadata)
    else:
        res_data += serialize(read_struct_data, data_structure, metadata)

    return res_data


def prepare_sav_struct_for_optional_indent(read_struct_data, data_structure):

    if isinstance(read_struct_data, dict):
        for entry_name, entry_data in read_struct_data.items():
            if entry_name.startswith('__'):
                continue
            if data_structure[entry_name].get('no_indent', False):
                read_struct_data[entry_name] = NoIndent(read_struct_data[entry_name])
            elif 'struct' in data_structure[entry_name]:
                prepare_sav_struct_for_optional_indent(read_struct_data[entry_name], data_structure[entry_name]['struct'])
            elif 'bit_struct' in data_structure[entry_name]:
                prepare_sav_struct_for_optional_indent(read_struct_data[entry_name], data_structure[entry_name]['bit_struct'])
            elif isinstance(entry_data, list):
                prepare_sav_struct_for_optional_indent(entry_data, data_structure[entry_name])
    elif isinstance(read_struct_data, list):
        for i, entry in enumerate(read_struct_data):
            if isinstance(entry, list):
                read_struct_data[i] = NoIndent(entry)
            if isinstance(entry, dict):
                prepare_sav_struct_for_optional_indent(entry, data_structure)
    elif read_struct_data is None:
        pass  # Nothing to do here, data is None
    else:
        pass

    pass


if __name__ == '__main__':
    with open(SAV_STRUCT_JSON_FILENAME, mode='rt') as sjf:
        sav_structure = json.load(sjf)

    with open(SAV_FILENAME, mode='rb') as sf:
        sav_data = sf.read()

    read_metadata = handle_metadata(sav_structure['__metadata'])
    read_struct_data = read_sav_structure(sav_structure, sav_data, read_metadata)
    read_struct_data['__structure'] = sav_structure

    sav_json_data_filename = SAV_FILENAME + ".json"

    prepare_sav_struct_for_optional_indent(read_struct_data, sav_structure)

    # Save structured SAV data to JSON file sav_json_data_filename
    with open(sav_json_data_filename, mode='wt') as svftj:
        json.dump(read_struct_data, svftj, indent=4, cls=PartialNoIndentJSONEncoder)

    # sav_json_data_filename = SAV_FILENAME + "_no_ind.json"
    # with open(sav_json_data_filename, mode='wt') as svftj:
    #     json.dump(read_struct_data, svftj, indent=4, cls=PartialNoIndentJSONEncoder)

    # sys.exit(0)

    # Do something with the JSON data in sav_json_data_filename
    stop_here_and_do_something = True

    # Read sav_json_data_filename file again to load changes from it
    with open(sav_json_data_filename, mode='rt') as sjf:
        read_struct_data = json.load(sjf)

    loaded_sav_structure = read_struct_data['__structure']
    loaded_metadata = handle_metadata(loaded_sav_structure['__metadata'])

    # Serialize and dump JSON data to original binary SAV format
    enc_sav_data = dump_sav_structure(read_struct_data, loaded_sav_structure, loaded_metadata)
    saved_filename = os.path.splitext(SAV_FILENAME)[0][:-2] + '07_new.SAV'
    with open(saved_filename, mode='wb') as svftenc:
        svftenc.write(enc_sav_data)

    pass
