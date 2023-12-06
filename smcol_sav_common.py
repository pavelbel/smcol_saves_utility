import json


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


def load_settings(settings_json_filename: str, default_settings: dict):

    if default_settings is None:
        default_settings = {"colonize_path": "."}

    try:
        with open(settings_json_filename, mode='rt') as sjf:
            settings = json.load(sjf)
    except:
        settings = {}

    if settings.get('colonize_path', None) is None:
        settings['colonize_path'] = default_settings['colonize_path']

    return settings

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


def get_caption_data(json_sav_data: dict, FIELD_VALUES: dict = FIELD_VALUES):
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
