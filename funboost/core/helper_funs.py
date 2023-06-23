import copy
import time


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
