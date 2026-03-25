import json
import typing
from datetime import datetime as _datetime
from datetime import date as _date
import orjson

def to_un_strict_json_compatible_obj(obj: typing.Any,first_call=True):
    """
    递归把任意对象转换成可 json.dumps 的结构。
    对不可序列化对象做 str()，并深度处理 dict/list/tuple/set。
    """
    if isinstance(obj, (str, int, float, bool)) or obj is None:
        return obj

    if isinstance(obj, dict):
        dict_new = {}
        for k, v in obj.items():
            # json 对象键建议使用字符串；复杂对象键转字符串避免 dumps 失败
            if isinstance(k, (str, int, float, bool)) or k is None:
                k_new = k
            else:
                k_new = str(k)
            dict_new[k_new] = to_un_strict_json_compatible_obj(v)
        return dict_new

    if isinstance(obj, (list, tuple, set, frozenset)):
        return [to_un_strict_json_compatible_obj(i) for i in obj]

    if isinstance(obj, _datetime):
        return obj.isoformat(sep=' ')

    if isinstance(obj, _date):
        return obj.isoformat()

    return str(obj)


def dict_to_un_strict_json(dictx: dict, indent=4):
    """字典尽量转json，一级kyes的值无法转就转成str"""
    dict_new = {}
    for k, v in dictx.items():
        # only_print_on_main_process(f'{k} :  {v}')
        if isinstance(v, (bool, tuple, dict, float, int)):
            dict_new[k] = v
        else:
            dict_new[k] = str(v)
    return json.dumps(dict_new, ensure_ascii=False, indent=indent)


def dict_to_un_strict_json_deep(dictx: dict, indent=4):
    """字典尽量转json，任何深层级kyes的值无法转就转成str"""
    dict_new = to_un_strict_json_compatible_obj(dictx)
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
