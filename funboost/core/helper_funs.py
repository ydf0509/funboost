import copy
import pytz
import time
import uuid
import datetime
from funboost.core.funboost_time import FunboostTime


def get_publish_time(paramsx: dict):
    """
    :param paramsx:
    :return:
    """
    return paramsx.get('extra', {}).get('publish_time', None)


def delete_keys_and_return_new_dict(dictx: dict, keys: list = None):
    dict_new = copy.copy(dictx)  # 主要是去掉一级键 publish_time，浅拷贝即可。新的消息已经不是这样了。
    keys = ['publish_time', 'publish_time_format', 'extra'] if keys is None else keys
    for dict_key in keys:
        try:
            dict_new.pop(dict_key)
        except KeyError:
            pass
    return dict_new


def block_python_main_thread_exit():
    """

    https://funboost.readthedocs.io/zh/latest/articles/c10.html#runtimeerror-cannot-schedule-new-futures-after-interpreter-shutdown

    主要是用于 python3.9以上 定时任务报错，  定时任务报错 RuntimeError: cannot schedule new futures after interpreter shutdown
    如果主线程结束了，apscheduler就会报这个错，加上这个while 1 ： time.sleep(100) 目的就是阻止主线程退出。
    """
    while 1:
        time.sleep(100)


run_forever = block_python_main_thread_exit


class MsgGenerater:
    @staticmethod
    def generate_task_id(queue_name:str) -> str:
        return f'{queue_name}_result:{uuid.uuid4()}'

    @staticmethod
    def generate_publish_time() -> float:
        return round(time.time(),4)

    @staticmethod
    def generate_publish_time_format() -> str:
        return FunboostTime().get_str()

    @classmethod
    def generate_pulish_time_and_task_id(cls,queue_name:str,task_id=None):
        extra_params = {'task_id': task_id or cls.generate_task_id(queue_name), 'publish_time': cls.generate_publish_time(),
                        'publish_time_format': cls.generate_publish_time_format()}
        return extra_params



if __name__ == '__main__':

    from funboost import FunboostCommonConfig

    print(FunboostTime())
    for i in range(1000000):
        # time.time()
        # MsgGenerater.generate_publish_time_format()

        datetime.datetime.now(tz=pytz.timezone(FunboostCommonConfig.TIMEZONE)).strftime(FunboostTime.FORMATTER_DATETIME_NO_ZONE)

    print(FunboostTime())