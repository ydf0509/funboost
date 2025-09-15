import pytz
import time
import sys
import datetime

import typing
import threading
from nb_time import NbTime
from funboost.funboost_config_deafult import FunboostCommonConfig


class FunboostTime(NbTime):
    default_formatter = NbTime.FORMATTER_DATETIME_NO_ZONE

    def get_time_zone_str(self, time_zone: typing.Union[str, datetime.tzinfo, None] = None):
        return time_zone or self.default_time_zone or FunboostCommonConfig.TIMEZONE or self.get_localzone_name()

    @staticmethod
    def _get_tow_digist(num: int) -> str:
        if len(str(num)) == 1:
            return f'0{num}'
        return str(num)

    def get_str(self, formatter=None):
        return self.datetime_obj.strftime(formatter or self.datetime_formatter)

    def get_str_fast(self):
        t_str = f'{self.datetime_obj.year}-{self._get_tow_digist(self.datetime_obj.month)}-{self._get_tow_digist(self.datetime_obj.day)} {self._get_tow_digist(self.datetime_obj.hour)}:{self._get_tow_digist(self.datetime_obj.minute)}:{self._get_tow_digist(self.datetime_obj.second)}'
        return t_str


# 缓存时区对象，提升性能（避免重复解析）
_tz_cache = {}

_DIGIT_MAP = {i: f'{i:02d}' for i in range(100)}


def _gen_2_dig_number(n):
    return _DIGIT_MAP[n]


def get_now_time_str_by_tz(tz_name: str = None) -> str:
    # 生成100万次当前时间字符串%Y-%m-%d %H:%M:%S仅需1.9秒.              
    """
    根据时区名（如 'Asia/Shanghai'）返回当前时间字符串，格式：'%Y-%m-%d %H:%M:%S'
    
    兼容 Python 3.6+，优先使用 zoneinfo（3.9+），否则尝试 pytz
    
    :param tz_name: IANA 时区名称，如 'Asia/Shanghai', 'America/New_York'
    :return: 格式化时间字符串
    """
    # 检查缓存
    tz_name = tz_name or FunboostCommonConfig.TIMEZONE
    if tz_name not in _tz_cache:
        if sys.version_info >= (3, 9):
            from zoneinfo import ZoneInfo
            _tz_cache[tz_name] = ZoneInfo(tz_name)
        else:
            # Python < 3.9，使用 pytz
            _tz_cache[tz_name] = pytz.timezone(tz_name)


    tz = _tz_cache[tz_name]

    # 获取当前时间并格式化（注意：datetime.now(tz) 是最高效的方式）
    now = datetime.datetime.now(tz)
    # return f'{now.year:04d}-{now.month:02d}-{now.day:02d} {now.hour:02d}:{now.minute:02d}:{now.second:02d}'
    # return now.strftime("%Y-%m-%d %H:%M:%S")
    return f'{now.year}-{_gen_2_dig_number(now.month)}-{_gen_2_dig_number(now.day)} {_gen_2_dig_number(now.hour)}:{_gen_2_dig_number(now.minute)}:{_gen_2_dig_number(now.second)}'


class NowTimeStrCache:
    # 生成100万次当前时间字符串%Y-%m-%d %H:%M:%S仅需0.4秒.
    # 全局变量，用于存储缓存的时间字符串和对应的整秒时间戳
    _cached_time_str: typing.Optional[str] = None
    _cached_time_second: int = 0

    # 为了线程安全，使用锁。在极高并发下，锁的开销远小于每毫秒都进行时间格式化。
    _time_cache_lock = threading.Lock()

    @classmethod
    def fast_get_now_time_str(cls,timezone_str:str=None) -> str:
        """
        获取当前时间字符串，格式为 '%Y-%m-%d %H:%M:%S'。
        通过缓存机制，同一秒内的多次调用直接返回缓存结果，极大提升性能。
        适用于对时间精度要求不高（秒级即可）的高并发场景。
        :return: 格式化后的时间字符串，例如 '2024-06-12 15:30:45'
        """
        timezone_str = timezone_str or FunboostCommonConfig.TIMEZONE

        # 获取当前的整秒时间戳（去掉小数部分）
        current_second = int(time.time())

        # 如果缓存的时间戳与当前秒数一致，直接返回缓存的字符串。
        if current_second == cls._cached_time_second:
            return cls._cached_time_str

        # 如果不一致，说明进入新的一秒，需要重新计算并更新缓存。
        # 使用锁确保在多线程环境下，只有一个线程会执行更新操作。

        with cls._time_cache_lock:
            # 双重检查锁定 (Double-Checked Locking)，防止在等待锁的过程中，其他线程已经更新了缓存。
            if current_second == cls._cached_time_second:
                return cls._cached_time_str

            # 重新计算时间字符串。这里直接使用 time.strftime，因为它在秒级更新的场景下性能足够。
            # 我们不需要像 Funboost 那样为每一毫秒的调用都去做查表优化。
            now = datetime.datetime.now(tz=pytz.timezone(timezone_str))
            cls._cached_time_str = now.strftime('%Y-%m-%d %H:%M:%S', )
            cls._cached_time_second = current_second

        return cls._cached_time_str


if __name__ == '__main__':
    print(FunboostTime().get_str())
    tz = pytz.timezone(FunboostCommonConfig.TIMEZONE)
    for i in range(1000000):
        pass
        # FunboostTime()#.get_str_fast()

        # datetime.datetime.now().strftime(NbTime.FORMATTER_DATETIME_NO_ZONE)
        tz = pytz.timezone(FunboostCommonConfig.TIMEZONE)
        datetime.datetime.now(tz=tz)
        # datetime.datetime.now(tz=pytz.timezone(FunboostCommonConfig.TIMEZONE))#.strftime(NbTime.FORMATTER_DATETIME_NO_ZONE)
        # datetime.datetime.now(tz=pytz.timezone(FunboostCommonConfig.TIMEZONE)).timestamp()

        # time.strftime(NbTime.FORMATTER_DATETIME_NO_ZONE)
        # time.time()
    print(NbTime())
