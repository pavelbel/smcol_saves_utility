import json

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
