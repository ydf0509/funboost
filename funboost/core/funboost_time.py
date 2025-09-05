import pytz
import time
import sys
import datetime

import typing

from nb_time import NbTime
from funboost.funboost_config_deafult import FunboostCommonConfig

class FunboostTime(NbTime):
    default_formatter = NbTime.FORMATTER_DATETIME_NO_ZONE

    def get_time_zone_str(self,time_zone: typing.Union[str, datetime.tzinfo,None] = None):
        return time_zone or self.default_time_zone or  FunboostCommonConfig.TIMEZONE  or self.get_localzone_name()

    @staticmethod
    def _get_tow_digist(num:int)->str:
        if len(str(num)) ==1:
            return f'0{num}'
        return str(num)

    def get_str(self, formatter=None):
        return self.datetime_obj.strftime(formatter or self.datetime_formatter)

    def get_str_fast(self):
        t_str = f'{self.datetime_obj.year}-{self._get_tow_digist(self.datetime_obj.month)}-{self._get_tow_digist(self.datetime_obj.day)} {self._get_tow_digist(self.datetime_obj.hour)}:{self._get_tow_digist(self.datetime_obj.minute)}:{self._get_tow_digist(self.datetime_obj.second)}'
        return t_str




# 缓存时区对象，提升性能（避免重复解析）
_tz_cache = {}

def get_now_time_str_by_tz(tz_name: str=None) -> str:                   
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
            try:
                import pytz
                _tz_cache[tz_name] = pytz.timezone(tz_name)
            except ImportError:
                raise RuntimeError(
                    f"Python < 3.9 requires 'pytz' to handle timezones. "
                    f"Install it with: pip install pytz"
                ) from None
            except pytz.UnknownTimeZoneError:
                raise pytz.UnknownTimeZoneError(tz_name)

    tz = _tz_cache[tz_name]
    
    # 获取当前时间并格式化（注意：datetime.now(tz) 是最高效的方式）
    now = datetime.datetime.now(tz)
    return f'{now.year:04d}-{now.month:02d}-{now.day:02d} {now.hour:02d}:{now.minute:02d}:{now.second:02d}'
    # return now.strftime("%Y-%m-%d %H:%M:%S")

if __name__ == '__main__':
    print(FunboostTime().get_str())
    tz=pytz.timezone(FunboostCommonConfig.TIMEZONE)
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
