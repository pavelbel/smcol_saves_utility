import json
from _ctypes import PyObj_FromPtr  # see https://stackoverflow.com/a/15012814/355230
import re

class NoIndent:
    def __init__(self, value):
        self.value = value

    def for_json(self):
        return self.value #json.JSONEncoder().encode(1) #self.value)


class MyEncoder(json.JSONEncoder):
    FORMAT_SPEC = '@@{}@@'  # Unique string pattern of NoIndent object ids.
    MAGIC_STRING = 'N*&y8&(B69'
    regex = re.compile(FORMAT_SPEC.format(r'(\d+)'))  # compile(r'@@(\d+)@@')

    def __init__(self, **kwargs):
        # Keyword arguments to ignore when encoding NoIndent wrapped values.
        ignore = {'cls', 'indent'}

        # Save copy of any keyword argument values needed for use here.
        self._kwargs = {k: v for k, v in kwargs.items() if k not in ignore}
        super(MyEncoder, self).__init__(**kwargs)

    def default(self, obj):
        #return (self.FORMAT_SPEC.format(id(obj)) if isinstance(obj, NoIndent) else super(MyEncoder, self).default(obj))
        return (self.MAGIC_STRING+json.dumps(obj.value, **self._kwargs)) if isinstance(obj, NoIndent) else super(MyEncoder, self).default(obj)

    def iterencode(self, obj, **kwargs):
        format_spec = self.FORMAT_SPEC  # Local var to expedite access.

        # Replace any marked-up NoIndent wrapped values in the JSON repr
        # with the json.dumps() of the corresponding wrapped Python object.
        for encoded in super(MyEncoder, self).iterencode(obj, **kwargs):
            #match = self.regex.search(encoded)
            #if match:
            if encoded.startswith('"' + self.MAGIC_STRING):
                #id = int(match.group(1))
                #no_indent = PyObj_FromPtr(id)
                encoded = encoded[1:-1].lstrip(self.MAGIC_STRING)
                #json_repr = json.dumps(no_indent.value, **self._kwargs)
                # Replace the matched id string with json formatted representation
                # of the corresponding Python object.
                #encoded = encoded.replace(f'"{format_spec.format(id)}"', json_repr)

            yield encoded

# class MyEncoder(json.JSONEncoder):
#     def __init__(self, **kwargs):
#         super(MyEncoder, self).__init__(**kwargs)
#         self.in_base_JSONEncoder = json.JSONEncoder(**kwargs)
#         # self.kwargs = kwargs
#         # self.given_indent = kwargs['indent']
#         del kwargs['indent']
#         self.in_base_JSONEncoder_on_int = json.JSONEncoder(**kwargs)
#
#     # def default(self, obj):
#     #     # super(MyEncoder, self).default(obj)
#     #     print(f"default() called for object: '{obj}'")
#     #     if isinstance(obj, NoIndentType):
#     #         # return self.in_base_JSONEncoder_on_int.default(obj.value)
#     #         return obj.value
#     #     else:
#     #         return self.in_base_JSONEncoder.default(obj)
#
#     def iterencode(self, obj, **kws):
#         print(f"iterencode() called for object: '{obj}'")
#         #return json.JSONEncoder(**self.kwargs).iterencode(obj, **kws)
#         if isinstance(obj, NoIndentType):
#             yield "NoIndentType!"
#         else:
#             yield from self.in_base_JSONEncoder.iterencode(obj, **kws)
#
#     # def encode(self, obj):
#     #     # if isinstance(obj, NoIndentType):
#     #     #     return json.JSONEncoder(**self.kwargs, indent=None).encode(obj.value)
#     #     # else:
#     #         print(f"encode() called for object: '{obj}'")
#     #         #return json.JSONEncoder(**self.kwargs, indent=self.given_indent).encode(obj)
#     #         return self.in_base_JSONEncoder.encode(obj)


if __name__ == '__main__':
    test_obj = {"a1": {"b1": NoIndent(1), "b2": NoIndent("Chumbra"), "b3": 3}, "a2": NoIndent([10, 20, 30]), "a3": [{"size": 1}, {"size": 2}, {"size": 3}]}
    # json_res = json.dumps(test_obj, indent=2)
    json_res_test = json.dumps(test_obj, cls=MyEncoder, indent=2)
    #json_res_test = simplejson.dumps(test_obj, indent=2, for_json=True)

    # print("----------- json_res -----------")
    # print(json_res)
    print("----------- json_res_test -----------")
    print(json_res_test)
