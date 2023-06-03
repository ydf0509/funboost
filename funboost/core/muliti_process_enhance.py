import os
import signal
from multiprocessing import Process
import time
from typing import List
from concurrent.futures import ProcessPoolExecutor
import nb_log
from funboost.core.booster import Booster

logger = nb_log.get_logger('funboost')


def _run_consumer_by_init_params(queue_name):
    from funboost.core.get_booster import get_boost_params_and_conusming_function
    from funboost.core.booster import boost
    from funboost import  ConsumersManager
    boost_params,conusming_function = get_boost_params_and_conusming_function(queue_name)
    booster = boost(**boost_params)(conusming_function)
    booster.consume()
    ConsumersManager.join_all_consumer_shedual_task_thread()


def run_consumer_with_multi_process(booster: Booster, process_num=1):
    """
    :param booster:被 boost 装饰器装饰的消费函数
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
    if not isinstance(booster, Booster):
        raise ValueError(f'{booster} 参数必须是一个被 boost 装饰的函数')
    if process_num == 1 and False:
        booster.consume()
    else:
        for i in range(process_num):
            # print(i)
            Process(target=_run_consumer_by_init_params,
                    args=(booster.queue_name, )).start()


def _multi_process_pub_params_list_by_consumer_init_params(queue_name, msgs: List[dict]):
    from funboost.core.get_booster import get_boost_params_and_conusming_function
    from funboost.core.booster import boost
    boost_params, conusming_function = get_boost_params_and_conusming_function(queue_name)
    booster = boost(**boost_params)(conusming_function)
    publisher = booster.publisher
    publisher.set_log_level(20)  # 超高速发布，如果打印详细debug日志会卡死屏幕和严重降低代码速度。
    for msg in msgs:
        publisher.publish(msg)


def multi_process_pub_params_list(booster: Booster, params_list, process_num=16):
    """超高速多进程发布任务，充分利用多核"""
    if not isinstance(booster, Booster):
        raise ValueError(f'{booster} 参数必须是一个被 boost 装饰的函数')
    params_list_len = len(params_list)
    if params_list_len < 1000 * 100:
        raise ValueError(f'要要发布的任务数量是 {params_list_len} 个,要求必须至少发布10万任务才使用此方法')
    ava_len = params_list_len // process_num + 1
    with ProcessPoolExecutor(process_num) as pool:
        t0 = time.time()
        for i in range(process_num):
            msgs = params_list[i * ava_len: (i + 1) * ava_len]
            # print(msgs)
            pool.submit(_multi_process_pub_params_list_by_consumer_init_params, booster.queue_name,
                         msgs)
    logger.info(f'\n 通过 multi_process_pub_params_list 多进程子进程的发布方式，发布了 {params_list_len} 个任务。耗时 {time.time() - t0} 秒')
