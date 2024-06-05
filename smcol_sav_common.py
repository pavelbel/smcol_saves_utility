import json


def is_prime(row, col, prime_resource_seed):
    """Prime resources placement algo. Reverse engineered and coded by Nick Wagers (nawagers).
      Taken from: https://github.com/nawagers/Colonization-SAV-files
      Returns (is_clean_prime, is_forest_prime) tuple. is_clean_prime applies to all non-forest tiles including hills,
      mountains and sea. Suppressed and sea/water checks removed, that's why it may mark a tile as prime when
      it is actually not in the game: this applies to deep-sea fish and exhausted minerals."""

    pattern = {0: [0, 10, 17, 27, 34, 40, 51, 57],
               1: [4, 14, 21, 31, 38, 44, 55, 61],
               2: [2, 8, 19, 25, 32, 42, 49, 59],
               3: [6, 12, 23, 29, 36, 46, 53, 63]}
    col += 4 * prime_resource_seed + (row // 4) * 12
    is_clean_prime = col % 64 in pattern[row % 4]
    col += 60
    is_forest_prime = col % 64 in pattern[row % 4]

    return is_clean_prime, is_forest_prime


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
