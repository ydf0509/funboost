"""
集成定时任务。
"""
import atexit

import time
from apscheduler.executors.pool import BasePoolExecutor

from typing import Union
import threading

from apscheduler.schedulers.background import BackgroundScheduler
# noinspection PyProtectedMember
from apscheduler.schedulers.base import STATE_STOPPED, STATE_RUNNING
from apscheduler.util import undefined
from threading import TIMEOUT_MAX
import deprecated
from funboost.utils.redis_manager import RedisMixin

from funboost.funboost_config_deafult import FunboostCommonConfig

from funboost.consumers.base_consumer import AbstractConsumer
from funboost.core.booster import BoostersManager, Booster

from funboost import BoosterParams
from funboost.concurrent_pool.custom_threadpool_executor import ThreadPoolExecutorShrinkAble,ThreadPoolExecutorShrinkAbleNonDaemon


@deprecated.deprecated(reason='以后不要再使用这种方式，对于job_store为数据库时候需要序列化不好。使用内存和数据库都兼容的添加任务方式: add_push_job')
def timing_publish_deco(consuming_func_decorated_or_consumer: Union[callable, AbstractConsumer]):
    def _deco(*args, **kwargs):
        if getattr(consuming_func_decorated_or_consumer, 'is_decorated_as_consume_function', False) is True:
            consuming_func_decorated_or_consumer.push(*args, **kwargs)
        elif isinstance(consuming_func_decorated_or_consumer, AbstractConsumer):
            consuming_func_decorated_or_consumer.publisher_of_same_queue.push(*args, **kwargs)
        else:
            raise TypeError('consuming_func_decorated_or_consumer 必须是被 boost 装饰的函数或者consumer类型')

    return _deco


def push_fun_params_to_broker(queue_name: str, *args, **kwargs):
    """
    queue_name 队列名字
    *args **kwargs 是消费函数的入参
    """
    booster = BoostersManager.get_or_create_booster_by_queue_name(queue_name)
    booster.push(*args, **kwargs)


class ThreadPoolExecutorForAps(BasePoolExecutor):
    """
    An executor that runs jobs in a concurrent.futures thread pool.

    Plugin alias: ``threadpool``

    :param max_workers: the maximum number of spawned threads.
    :param pool_kwargs: dict of keyword arguments to pass to the underlying
        ThreadPoolExecutor constructor
    """

    def __init__(self, max_workers=100, pool_kwargs=None):

        # pool = ThreadPoolExecutorShrinkAble(int(max_workers), )
        pool = ThreadPoolExecutorShrinkAbleNonDaemon(int(max_workers), ) 

        """
        raise RuntimeError('cannot schedule new futures after ' RuntimeError: cannot schedule new futures after interpreter shutdown
        
        ThreadPoolExecutorShrinkAbleNonDaemon 这个更好，阻止主线程退出导致apschrduler使用了守护线程的线程池而导致这个报错。
        ThreadPoolExecutorShrinkAbleNonDaemon 线程池里面的线程不是守护线程，
        
        """

        super().__init__(pool)


class FunboostBackgroundScheduler(BackgroundScheduler):
    """
    自定义的， 继承了官方BackgroundScheduler，
    通过重写 _main_loop ，使得动态修改增加删除定时任务配置更好。
    """

    _last_wait_seconds = None
    _last_has_task = False

    @deprecated.deprecated(reason='以后不要再使用这种方式，对于job_store为数据库时候需要序列化不好。使用内存和数据库都兼容的添加任务方式: add_push_job')
    def add_timing_publish_job(self, func, trigger=None, args=None, kwargs=None, id=None, name=None,
                               misfire_grace_time=undefined, coalesce=undefined, max_instances=undefined,
                               next_run_time=undefined, jobstore='default', executor='default',
                               replace_existing=False, **trigger_args):
        return self.add_job(timing_publish_deco(func), trigger, args, kwargs, id, name,
                            misfire_grace_time, coalesce, max_instances,
                            next_run_time, jobstore, executor,
                            replace_existing, **trigger_args)

    def add_push_job(self, func: Booster, trigger=None, args=None, kwargs=None, 
                     id=None, name=None,
                     misfire_grace_time=undefined, coalesce=undefined, max_instances=undefined,
                     next_run_time=undefined, jobstore='default', executor='default',
                     replace_existing=False, **trigger_args, ):
        """
        :param func: 被@boost装饰器装饰的函数
        :param trigger:
        :param args:
        :param kwargs:
        :param id:
        :param name:
        :param misfire_grace_time:
        :param coalesce:
        :param max_instances:
        :param next_run_time:
        :param jobstore:
        :param executor:
        :param replace_existing:
        :param trigger_args:
        :return:
        """
        # args = args or {}
        # kwargs['queue_name'] = func.queue_name

        """
        用户如果不使用funboost的 FunboostBackgroundScheduler 类型对象，而是使用原生的apscheduler类型对象，可以scheduler.add_job(push_fun_params_to_broker,args=(,),kwargs={}) 
        push_fun_params_to_broker函数入参是消费函数队列的 queue_name 加上 原消费函数的入参
        """
        if args is None:
            args = tuple()
        
        args_list = list(args)
        args_list.insert(0, func.queue_name)
        args = tuple(args_list)
        if name is None:
            name = f'push_fun_params_to_broker_for_queue_{func.queue_name}'
        func.publisher.check_func_input_params(*args[1:], **(kwargs or {})) # 这一行是检查入参是否合法，防止添加了不合法的定时入参，到执行时候才发现，这比官方apscheduler更靠谱。
        return self.add_job(push_fun_params_to_broker, trigger, args, kwargs, id, name,
                            misfire_grace_time, coalesce, max_instances,
                            next_run_time, jobstore, executor,
                            replace_existing, **trigger_args, )

    def start(self, paused=False, block_exit=True):
        # def _block_exit():
        #     while True:
        #         time.sleep(3600)
        #
        # threading.Thread(target=_block_exit,).start()  # 既不希望用BlockingScheduler阻塞主进程也不希望定时退出。
        # self._daemon = False
        # def _when_exit():
        #     while 1:
        #         # print('阻止退出')
        #         time.sleep(100)

        # if block_exit:
        #     atexit.register(_when_exit)
        self._daemon = False   # 这里强制默认改成非守护线程。默认是守护线程，主线程退出会报错。
        super().start(paused=paused, )
        # _block_exit()   # python3.9 判断守护线程结束必须主线程在运行。你自己在你的运行代碼的最末尾加上 while 1： time.sleep(100)  ,来阻止主线程退出。

    def _main_loop00000(self):
        """
        原来的代码是这，动态添加任务不友好。
        :return:
        """
        wait_seconds = threading.TIMEOUT_MAX
        while self.state != STATE_STOPPED:
            print(6666, self._event.is_set(), wait_seconds)
            self._event.wait(wait_seconds)
            print(7777, self._event.is_set(), wait_seconds)
            self._event.clear()
            wait_seconds = self._process_jobs()

    def _main_loop(self):
        """原来的_main_loop 删除所有任务后wait_seconds 会变成None，无限等待。
        或者下一个需要运行的任务的wait_seconds是3600秒后，此时新加了一个动态任务需要3600秒后，
        现在最多只需要1秒就能扫描到动态新增的定时任务了。
        """
        MAX_WAIT_SECONDS_FOR_NEX_PROCESS_JOBS = 0.5
        wait_seconds = None
        while self.state != STATE_STOPPED:
            if wait_seconds is None:
                wait_seconds = MAX_WAIT_SECONDS_FOR_NEX_PROCESS_JOBS
            self._last_wait_seconds = min(wait_seconds, MAX_WAIT_SECONDS_FOR_NEX_PROCESS_JOBS)
            if wait_seconds in (None, TIMEOUT_MAX):
                self._last_has_task = False
            else:
                self._last_has_task = True
            time.sleep(self._last_wait_seconds)  # 这个要取最小值，不然例如定时间隔0.1秒运行，不取最小值，不会每隔0.1秒运行。
            wait_seconds = self._process_jobs()

    def _create_default_executor(self):
        return ThreadPoolExecutorForAps()  # 必须是apscheduler pool的子类


FsdfBackgroundScheduler = FunboostBackgroundScheduler  # 兼容一下名字，fsdf是 function-scheduling-distributed-framework 老框架名字的缩写
# funboost_aps_scheduler定时配置基于内存的，不可以跨机器远程动态添加/修改/删除定时任务配置。如果需要动态增删改查定时任务，可以使用funboost_background_scheduler_redis_store

"""
建议不要亲自使用这个 funboost_aps_scheduler 对象，而是 ApsJobAdder来添加定时任务，自动多个apscheduler对象实例，
尤其是redis作为jobstores时候，使用不同的jobstores，每个消费函数使用各自单独的jobs_key和 run_times_key
"""
funboost_aps_scheduler = FunboostBackgroundScheduler(timezone=FunboostCommonConfig.TIMEZONE, daemon=False, )
fsdf_background_scheduler = funboost_aps_scheduler  # 兼容一下老名字。



if __name__ == '__main__':

    """
    下面的例子过时了，可以用但不建议，建议统一使用 ApsJobAdder 来添加定时任务。

    """

    # 定时运行消费演示
    import datetime
    from funboost import boost, BrokerEnum, fsdf_background_scheduler, timing_publish_deco, run_forever


    @Booster(boost_params=BoosterParams(queue_name='queue_test_666', broker_kind=BrokerEnum.LOCAL_PYTHON_QUEUE))
    def consume_func(x, y):
        print(f'{x} + {y} = {x + y}')


    print(consume_func, type(consume_func))

    # 定时每隔3秒执行一次。
    funboost_aps_scheduler.add_push_job(consume_func,
                                        'interval', id='3_second_job', seconds=3, kwargs={"x": 5, "y": 6})

    # 定时，只执行一次
    funboost_aps_scheduler.add_push_job(consume_func,
                                        'date', run_date=datetime.datetime(2020, 7, 24, 13, 53, 6), args=(5, 6,))

    # 定时，每天的11点32分20秒都执行一次。
    funboost_aps_scheduler.add_push_job(consume_func,
                                        'cron', day_of_week='*', hour=18, minute=22, second=20, args=(5, 6,))

    # 启动定时
    funboost_aps_scheduler.start()

    # 启动消费
    consume_func.consume()
    run_forever()
