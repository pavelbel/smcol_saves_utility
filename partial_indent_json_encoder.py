import json


# Class for JSON formatting without indent
class NoIndent:
    def __init__(self, value):
        self.value = value


# Custom JSONEncoder for formatting with partial indent
class PartialNoIndentJSONEncoder(json.JSONEncoder):
    MAGIC_STRING = 'N*&y8&(B69n)*&6n9^69o'

    def __init__(self, **kwargs):
        self.no_indent_objects = []

        # Keyword arguments to ignore when encoding NoIndent wrapped values.
        ignore = {'cls', 'indent'}

        # Save copy of any keyword argument values needed for use here.
        self._kwargs = {k: v for k, v in kwargs.items() if k not in ignore}
        super().__init__(**kwargs)

    def default(self, obj):
        if isinstance(obj, NoIndent):
            self.no_indent_objects.append(obj.value)
            return self.MAGIC_STRING + str(len(self.no_indent_objects)-1)
        else:
            return super().default(obj)

    def iterencode(self, obj, **kwargs):
        for encoded in super().iterencode(obj, **kwargs):
            if encoded.startswith('"' + self.MAGIC_STRING):
                obj_idx_str = encoded[len(self.MAGIC_STRING)+1:-1]
                try:
                    obj_idx = int(obj_idx_str)
                except:
                    pass
                else:
                    encoded = json.dumps(self.no_indent_objects[obj_idx], **self._kwargs)

            yield encoded


if __name__ == '__main__':
    test_obj = {"a1": {"b1": NoIndent(1), "b2": NoIndent("Chumbra"), "b3": 3}, "a2": NoIndent([10, ["a", "b"], 30]), "a3": NoIndent([{"size": 1}, {"size": 2}, {"size": 3}]), "a4": [NoIndent([1, 2, 3]), NoIndent([4, 5, 6]), NoIndent([7, 8, 9])]}
    # json_res = json.dumps(test_obj, indent=2)
    json_res_test = json.dumps(test_obj, cls=PartialNoIndentJSONEncoder, indent=2)
    #json_res_test = simplejson.dumps(test_obj, indent=2, for_json=True)

    # print("----------- json_res -----------")
    # print(json_res)
    print("----------- json_res_test -----------")
    print(json_res_test)
