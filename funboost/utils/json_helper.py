import json
import typing
from datetime import datetime as _datetime
from datetime import date as _date

def dict_to_un_strict_json(dictx: dict, indent=4):
    dict_new = {}
    for k, v in dictx.items():
        # only_print_on_main_process(f'{k} :  {v}')
        if isinstance(v, (bool, tuple, dict, float, int)):
            dict_new[k] = v
        else:
            dict_new[k] = str(v)
    return json.dumps(dict_new, ensure_ascii=False, indent=indent)


class _CustomEncoder(json.JSONEncoder):
    """自定义的json解析器，mongodb返回的字典中的时间格式是datatime，json直接解析出错"""

    def default(self, obj):
        if isinstance(obj, _datetime):
            return obj.strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(obj, _date):
            return obj.strftime('%Y-%m-%d')
        else:
            return json.JSONEncoder.default(self, obj)


# noinspection PyProtectedMember,PyPep8,PyRedundantParentheses
def _dumps(obj, skipkeys=False, ensure_ascii=True, check_circular=True, allow_nan=True, cls=_CustomEncoder, indent=None, separators=None,
           default=None, sort_keys=False, **kw):
    # 全局patch ensure_ascii = False 会引起极少数库不兼容。
    if (not skipkeys and ensure_ascii and check_circular and allow_nan and cls is None and indent is None and separators is None and default is None and not sort_keys and not kw):
        return json._default_encoder.encode(obj)
    if cls is None:
        cls = json.JSONEncoder
    return cls(
        skipkeys=skipkeys, ensure_ascii=ensure_ascii,
        check_circular=check_circular, allow_nan=allow_nan, indent=indent,
        separators=separators, default=default, sort_keys=sort_keys, ).encode(obj)



def monkey_patch_json():
    json.dumps = _dumps


# class JsonUtils:
#     @staticmethod
#     def to_dict(obj:typing.Union[str,dict,list]):
#         if isinstance(obj,str):
#             return json.loads(obj)
#         else:
#             return obj
#
#     @staticmethod
#     def to_json_str(obj:typing.Union[str,dict,list]):
#         if isinstance(obj,str):
#             return obj
#         else:
#             return json.dumps(obj,ensure_ascii=False)

if __name__ == '__main__':
    pass
