import time
from funboost.utils.uuid7 import uuid7
from funboost.core.funboost_time import FunboostTime, fast_get_now_time_str


def get_publish_time(paramsx: dict):
    """
    :param paramsx:
    :return:
    """
    return paramsx.get('extra', {}).get('publish_time', None)


def get_publish_time_format(paramsx: dict):
    """
    :param paramsx:
    :return:
    """
    return paramsx.get('extra', {}).get('publish_time_format', None)






def delete_keys_and_return_new_dict(dictx: dict, exclude_keys: list ):
    """
    返回一个不包含extra字段的新字典,也即是真正的函数入参字典。
    优化：使用字典推导式代替 deepcopy + pop，性能提升 10-50 倍。
    """
    return {k: v for k, v in dictx.items() if k not in exclude_keys}

_DEFAULT_EXCLUDE_KEYS = frozenset(['extra'])

def get_func_only_params(dictx: dict)->dict:
    """
    消息中剔除 extra 字段，返回真正的函数入参字典。
    :param dictx:
    :return:
    """
    return {k: v for k, v in dictx.items() if k not in _DEFAULT_EXCLUDE_KEYS}

def block_python_main_thread_exit():
    """

    https://funboost.readthedocs.io/zh-cn/latest/articles/c10.html#runtimeerror-cannot-schedule-new-futures-after-interpreter-shutdown

    主要是用于 python3.9以上 定时任务报错，  定时任务报错 RuntimeError: cannot schedule new futures after interpreter shutdown
    如果主线程结束了，apscheduler就会报这个错，加上这个while 1 ： time.sleep(100) 目的就是阻止主线程退出。
    """
    while 1:
        time.sleep(100)


run_forever = block_python_main_thread_exit


class MsgGenerater:
    @staticmethod
    def generate_task_id(queue_name:str) -> str:
        """
        UUIDv7 是 时间有序（time-ordered） 的 UUID，新一代 UUID 规范（RFC 9562，已标准化），
        专门为数据库/分布式系统设计。一句话总结：
        UUIDv7 = “像 UUID 一样全局唯一 + 像雪花 ID 一样按时间递增”
        """
        # return f'{queue_name}_result:{uuid.uuid4()}'
        uuid7_obj =  uuid7()
        return str(uuid7_obj) # uuid7 对数据库顺序更友好


    @staticmethod
    def generate_publish_time() -> float:
        return round(time.time(),4)


    @staticmethod
    def generate_publish_time_format() -> str:
        # return FunboostTime().get_str()  # 性能不好
        # return get_now_time_str_by_tz()  # 2秒100万次
        return fast_get_now_time_str() # 0.4秒100万次


    @classmethod
    def generate_pulish_time_and_task_id(cls,queue_name:str,task_id=None):
        extra_params = {'task_id': task_id or cls.generate_task_id(queue_name), 
                        'publish_time': cls.generate_publish_time(),  # 时间戳秒
                        'publish_time_format': cls.generate_publish_time_format() # 时间字符串 例如 2025-12-25 10:00:00
                        
                        }
        return extra_params



if __name__ == '__main__':

    from funboost import FunboostCommonConfig

    print(FunboostTime())
    for i in range(1000000):
        # time.time()
        MsgGenerater.generate_publish_time_format()
        # FunboostTime().get_str()

        # datetime.datetime.now(tz=pytz.timezone(FunboostCommonConfig.TIMEZONE)).strftime(FunboostTime.FORMATTER_DATETIME_NO_ZONE)

    print(FunboostTime())