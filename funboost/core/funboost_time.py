import pytz
import time

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
