# coding=utf-8
import typing
import datetime
import time
import re
import pytz
from funboost import funboost_config_deafult

from funboost.utils import nb_print


def build_defualt_date():
    """
    获取今天和明天的日期
    :return:
    """
    today = datetime.date.today()
    today_str = today.__str__()
    tomorrow = today + datetime.timedelta(days=1)
    tomorrow_str = str(tomorrow)
    return today, tomorrow, today_str, tomorrow_str


def get_day_by_interval(n):
    """
    :param n: 离当天的日期，可为正负整数
    :return:
    """
    today = datetime.date.today()
    day = today + datetime.timedelta(days=n)
    day_str = str(day)
    return day, day_str


def get_ahead_one_hour(datetime_str):
    """
    获得提前一小时的时间字符串和时间戳
    :return:
    """
    datetime_obj = datetime.datetime.strptime(datetime_str, '%Y-%m-%d %H:%M:%S')
    datetime_obj_one_hour_ahead = datetime_obj + datetime.timedelta(hours=-1)
    return datetime_obj_one_hour_ahead.strftime('%Y-%m-%d %H:%M:%S'), datetime_obj_one_hour_ahead.timestamp()


def timestamp_to_datetime_str(timestamp):
    time_local = time.localtime(timestamp)
    # 转换成新的时间格式(2016-05-05 20:28:54)
    return time.strftime("%Y-%m-%d %H:%M:%S", time_local)


class DatetimeConverter:
    """
    最爽的时间操作方式。使用真oop需要实例化，调用方式比纯静态方法工具类好太多。
    """
    DATETIME_FORMATTER = "%Y-%m-%d %H:%M:%S"
    DATETIME_FORMATTER2 = "%Y-%m-%d"
    DATETIME_FORMATTER3 = "%H:%M:%S"

    @classmethod
    def bulid_conveter_with_other_formatter(cls, datetime_str, datetime_formatter):
        """
        :param datetime_str: 时间字符串
        :param datetime_formatter: 能够格式化该字符串的模板
        :return:
        """
        datetime_obj = datetime.datetime.strptime(datetime_str, datetime_formatter)
        return cls(datetime_obj)

    def __init__(self, datetimex: typing.Union[int, float, datetime.datetime, str] = None):  # REMIND 不要写成默认 datetime.datetime.now()或time.time()，否则默认参数值运行一次
        """
        :param datetimex: 接受时间戳  datatime类型 和 时间字符串三种类型
        """
        if isinstance(datetimex, str):
            if not re.match(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}', datetimex):
                raise ValueError('时间字符串的格式不符合此传参的规定')
            else:
                self.datetime_obj = datetime.datetime.strptime(datetimex, self.DATETIME_FORMATTER)
        elif isinstance(datetimex, (int, float)):
            if datetimex < 1:
                datetimex += 86400
            self.datetime_obj = datetime.datetime.fromtimestamp(datetimex, tz=pytz.timezone(funboost_config_deafult.TIMEZONE))  # 时间戳0在windows会出错。
        elif isinstance(datetimex, datetime.datetime):
            self.datetime_obj = datetimex
        elif datetimex is None:
            self.datetime_obj = datetime.datetime.now(tz=pytz.timezone(funboost_config_deafult.TIMEZONE))
        else:
            raise ValueError('实例化时候的传参不符合规定')

    @property
    def datetime_str(self):
        return self.datetime_obj.strftime(self.DATETIME_FORMATTER)

    @property
    def time_str(self):
        return self.datetime_obj.strftime(self.DATETIME_FORMATTER3)

    @property
    def date_str(self):
        return self.datetime_obj.strftime(self.DATETIME_FORMATTER2)

    @property
    def timestamp(self):
        return self.datetime_obj.timestamp()

    @property
    def one_hour_ago_datetime_converter(self):
        """
        酒店经常需要提前一小时免费取消，直接封装在这里
        :return:
        """
        one_hour_ago_datetime_obj = self.datetime_obj + datetime.timedelta(hours=-1)
        return self.__class__(one_hour_ago_datetime_obj)

    def is_greater_than_now(self):
        return self.timestamp > time.time()

    def __str__(self):
        return self.datetime_str

    def __call__(self):
        return self.datetime_obj


def seconds_to_hour_minute_second(seconds):
    """
    把秒转化成还需要的时间
    :param seconds:
    :return:
    """
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    return "%02d:%02d:%02d" % (h, m, s)


if __name__ == '__main__':
    """
    1557113661.0
    '2019-05-06 12:34:21'
    '2019/05/06 12:34:21'
    DatetimeConverter(1557113661.0)()
    """
    # noinspection PyShadowingBuiltins
    print = nb_print
    o3 = DatetimeConverter('2019-05-06 12:34:21')
    print(o3)
    print('- - - - -  - - -')

    o = DatetimeConverter.bulid_conveter_with_other_formatter('2019/05/06 12:34:21', '%Y/%m/%d %H:%M:%S')
    print(o)
    print(o.date_str)
    print(o.timestamp)
    print('***************')
    o2 = o.one_hour_ago_datetime_converter
    print(o2)
    print(o2.date_str)
    print(o2.timestamp)
    print(o2.is_greater_than_now())
    print(o2(), type(o2()))
    print(DatetimeConverter())
    print(datetime.datetime.now())
    time.sleep(5)
    print(DatetimeConverter())
    print(datetime.datetime.now())
    print(DatetimeConverter(3600 * 24))

    print(seconds_to_hour_minute_second(3600 * 2))
