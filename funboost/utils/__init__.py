# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2019/8/8 0008 9:48
import json
from datetime import datetime as _datetime
from datetime import date as _date


from nb_log import (LogManager, simple_logger, defaul_logger, LoggerMixin, LoggerLevelSetterMixin,
                    LoggerMixinDefaultWithFileHandler,nb_print,patch_print,reverse_patch_print,get_logger)

from funboost.utils.redis_manager import RedisMixin

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

#################以下为打猴子补丁#####################
monkey_patch_json()





