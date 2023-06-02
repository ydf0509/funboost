import os
import signal
from multiprocessing import Process
import time
from typing import List
from concurrent.futures import ProcessPoolExecutor
from nb_log import LoggerMixin
import nb_log

logger = nb_log.get_logger('funboost')


def _run_many_consumer_by_init_params(consumer_init_params_list: List[dict]):
    from funboost import get_consumer, ConsumersManager
    for consumer_init_params in consumer_init_params_list:
        get_consumer(**consumer_init_params).start_consuming_message()
    ConsumersManager.join_all_consumer_shedual_task_thread()


def run_consumer_with_multi_process(task_fun, process_num=1):
    """
    :param task_fun:被 boost 装饰器装饰的消费函数
    :param process_num:开启多个进程。  主要是 多进程并发  + 4种细粒度并发(threading gevent eventlet asyncio)。叠加并发。
    这种是多进程方式，一次编写能够兼容win和linux的运行。一次性启动6个进程 叠加 多线程 并发。
    """
    '''
       from funboost import boost, BrokerEnum, ConcurrentModeEnum, run_consumer_with_multi_process
       import os

       @boost('test_multi_process_queue',broker_kind=BrokerEnum.REDIS_ACK_ABLE,concurrent_mode=ConcurrentModeEnum.THREADING,)
       def fff(x):
           print(x * 10,os.getpid())

       if __name__ == '__main__':
           # fff.consume()
           run_consumer_with_multi_process(fff,6) # 一次性启动6个进程 叠加 多线程 并发。
           fff.multi_process_conusme(6)    # 这也是一次性启动6个进程 叠加 多线程 并发。
    '''
    if not getattr(task_fun, 'is_decorated_as_consume_function'):
        raise ValueError(f'{task_fun} 参数必须是一个被 boost 装饰的函数')
    if process_num == 1 and False:
        task_fun.consume()
    else:
        for i in range(process_num):
            # print(i)
            Process(target=_run_many_consumer_by_init_params,
                    args=([{**{'consuming_function': task_fun}, **task_fun.init_params}],)).start()


def _multi_process_pub_params_list_by_consumer_init_params(consumer_init_params: dict, msgs: List[dict]):
    from funboost import get_consumer
    consumer = get_consumer(**consumer_init_params)
    publisher = consumer.publisher_of_same_queue
    publisher.set_log_level(20)  # 超高速发布，如果打印详细debug日志会卡死屏幕和严重降低代码速度。
    for msg in msgs:
        publisher.publish(msg)


def multi_process_pub_params_list(task_fun, params_list, process_num=16):
    """超高速多进程发布任务，充分利用多核"""
    if not getattr(task_fun, 'is_decorated_as_consume_function'):
        raise ValueError(f'{task_fun} 参数必须是一个被 boost 装饰的函数')
    params_list_len = len(params_list)
    if params_list_len < 1000 * 100:
        raise ValueError(f'要要发布的任务数量是 {params_list_len} 个,要求必须至少发布10万任务才使用此方法')
    ava_len = params_list_len // process_num + 1
    with ProcessPoolExecutor(process_num) as pool:
        t0 = time.time()
        for i in range(process_num):
            msgs = params_list[i * ava_len: (i + 1) * ava_len]
            # print(msgs)
            pool.submit(_multi_process_pub_params_list_by_consumer_init_params,
                        {**{'consuming_function': task_fun}, **task_fun.init_params}, msgs)
    logger.info(f'\n 通过 multi_process_pub_params_list 多进程子进程的发布方式，发布了 {params_list_len} 个任务。耗时 {time.time() - t0} 秒')


class FunctionResultStatusPersistanceConfig(LoggerMixin):
    def __init__(self, is_save_status: bool, is_save_result: bool, expire_seconds: int = 7 * 24 * 3600, is_use_bulk_insert=False):
        """
        :param is_save_status:
        :param is_save_result:
        :param expire_seconds: 设置统计的过期时间，在mongo里面自动会移除这些过期的执行记录。
        :param is_use_bulk_insert : 是否使用批量插入来保存结果，批量插入是每隔0.5秒钟保存一次最近0.5秒内的所有的函数消费状态结果，始终会出现最后0.5秒内的执行结果没及时插入mongo。为False则，每完成一次函数就实时写入一次到mongo。
        """

        if not is_save_status and is_save_result:
            raise ValueError(f'你设置的是不保存函数运行状态但保存函数运行结果。不允许你这么设置')
        self.is_save_status = is_save_status
        self.is_save_result = is_save_result
        if expire_seconds > 10 * 24 * 3600:
            self.logger.warning(f'你设置的过期时间为 {expire_seconds} ,设置的时间过长。 ')
        self.expire_seconds = expire_seconds
        self.is_use_bulk_insert = is_use_bulk_insert

    def to_dict(self):
        return {"is_save_status": self.is_save_status,

                'is_save_result': self.is_save_result, 'expire_seconds': self.expire_seconds}

    def __str__(self):
        return f'<FunctionResultStatusPersistanceConfig> {id(self)} {self.to_dict()}'






