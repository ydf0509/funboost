import multiprocessing
import threading

from funboost.funboost_config_deafult import BrokerConnConfig
from huey import RedisHuey
from huey.consumer import Consumer

huey_obj = RedisHuey('funboost_huey', url=BrokerConnConfig.REDIS_URL,)

class HueyHelper:
    huey_obj = huey_obj
    queue_name__huey_task_fun_map = {}
    to_be_start_huey_queue_name_set= set()

    # @classmethod
    # def realy_start_huey_consume(cls):
    #     for queue_name in list(cls.to_be_start_huey_queue_name_set):
    #         multiprocessing.Process(target=cls._start_huey,args=(queue_name,)).start()  # huey的consumer的run方法无法在子线程运行，必须是主线程。
    #
    # @classmethod
    # def _start_huey(cls,queue_name):
    #     consumer_kwargs = {'huey': HueyHelper.queue_name__huey_obj_map[queue_name], 'workers': 200, 'periodic': True, 'initial_delay': 0.1, 'backoff': 1.15, 'max_delay': 10.0, 'scheduler_interval': 1, 'worker_type': 'thread', 'check_worker_health': True, 'health_check_interval': 10, 'flush_locks': False, 'extra_locks': None}
    #     huey_consumer = Consumer(**consumer_kwargs)
    #     huey_consumer.run()

    @classmethod
    def realy_start_huey_consume(cls):
        """ huey 启动所有函数开始消费"""
        consumer_kwargs = {'huey': huey_obj, 'workers': 200, 'periodic': True,
                           'initial_delay': 0.1, 'backoff': 1.15, 'max_delay': 10.0,
                           'scheduler_interval': 1, 'worker_type': 'thread',
                           'check_worker_health': True, 'health_check_interval': 10,
                           'flush_locks': False, 'extra_locks': None}
        huey_consumer = Consumer(**consumer_kwargs)
        huey_consumer.run()






