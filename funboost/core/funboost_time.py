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



if __name__ == '__main__':
    print(NbTime())
    for i in range(100000):
        # print(generate_publish_time())
        # print(generate_publish_time_format())
        # generate_publish_time()
        # generate_publish_time_format()

        datetime.datetime.now(tz=pytz.timezone(FunboostCommonConfig.TIMEZONE)).strftime(NbTime.FORMATTER_DATETIME_NO_ZONE)
        datetime.datetime.now(tz=pytz.timezone(FunboostCommonConfig.TIMEZONE)).timestamp()
    print(NbTime())
