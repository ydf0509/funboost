# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2019/8/8 0008 13:10
import json
from collections import OrderedDict
import typing

from function_scheduling_distributed_framework.utils import RedisMixin


class RedisFilter(RedisMixin):
    """
    基于函数参数的任务过滤。
    """
    def __init__(self, redis_key_name):
        self._redis_key_name = redis_key_name

    @staticmethod
    def _get_ordered_str(value):
        """对json的键值对在redis中进行过滤，需要先把键值对排序，否则过滤会不准确如 {"a":1,"b":2} 和 {"b":2,"a":1}"""
        if isinstance(value, str):
            value = json.loads(value)
        ordered_dict = OrderedDict()
        for k in sorted(value):
            ordered_dict[k] = value[k]
        return json.dumps(ordered_dict)

    def add_a_value(self, value: typing.Union[str, dict]):
        self.redis_db7.sadd(self._redis_key_name, self._get_ordered_str(value))

    def check_value_exists(self, value):
        return self.redis_db7.sismember(self._redis_key_name, self._get_ordered_str(value))
