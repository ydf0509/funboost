"""
集成定时任务。
"""
import atexit
import copy
import importlib

import pickle

import time
from typing import Union
import threading

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.redis import RedisJobStore
# noinspection PyProtectedMember
from apscheduler.schedulers.base import STATE_STOPPED, STATE_RUNNING
from apscheduler.util import undefined
import deprecated
from funboost.utils import RedisMixin

from funboost import funboost_config_deafult

from funboost.consumers.base_consumer import AbstractConsumer
from funboost.core.get_booster import get_booster, Booster
from funboost.publishers.base_publisher import AbstractPublisher


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


def push_fun_params_to_broker(queue_name: str, *args, **kwargs, ):
    """
    *args **kwargs 是消费函数的入参
    """
    runonce_uuid = kwargs['runonce_uuid']
    kwargs.pop('runonce_uuid')
    if runonce_uuid:
        key = 'apscheduler.redisjobstore_runonce2'
        if RedisMixin().redis_db_frame.sadd(key, runonce_uuid):
            get_booster(queue_name).push(*args, **kwargs)
    else:
        get_booster(queue_name).push(*args, **kwargs)


class FunboostBackgroundScheduler(BackgroundScheduler):
    """
    自定义的， 继承了官方BackgroundScheduler，
    通过重写 _main_loop ，使得动态修改增加删除定时任务配置更好。
    """

    @deprecated.deprecated(reason='以后不要再使用这种方式，对于job_store为数据库时候需要序列化不好。使用内存和数据库都兼容的添加任务方式: add_push_job')
    def add_timing_publish_job(self, func, trigger=None, args=None, kwargs=None, id=None, name=None,
                               misfire_grace_time=undefined, coalesce=undefined, max_instances=undefined,
                               next_run_time=undefined, jobstore='default', executor='default',
                               replace_existing=False, **trigger_args):
        return self.add_job(timing_publish_deco(func), trigger, args, kwargs, id, name,
                            misfire_grace_time, coalesce, max_instances,
                            next_run_time, jobstore, executor,
                            replace_existing, **trigger_args)

    def add_push_job(self, func: Booster, trigger=None, args=None, kwargs=None, id=None, name=None,
                     misfire_grace_time=undefined, coalesce=undefined, max_instances=undefined,
                     next_run_time=undefined, jobstore='default', executor='default',
                     replace_existing=False, runonce_uuid=None, **trigger_args, ):
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
        kwargs = kwargs or {}
        kwargs['runonce_uuid'] = runonce_uuid
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
        def _when_exit():
            while 1:
                # print('阻止退出')
                time.sleep(100)

        if block_exit:
            atexit.register(_when_exit)
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
        MAX_WAIT_SECONDS_FOR_NEX_PROCESS_JOBS = 1
        wait_seconds = None
        while self.state == STATE_RUNNING:
            if wait_seconds is None:
                wait_seconds = MAX_WAIT_SECONDS_FOR_NEX_PROCESS_JOBS
            time.sleep(min(wait_seconds, MAX_WAIT_SECONDS_FOR_NEX_PROCESS_JOBS))  # 这个要取最小值，不然例如定时间隔0.1秒运行，不取最小值，不会每隔0.1秒运行。
            wait_seconds = self._process_jobs()


FsdfBackgroundScheduler = FunboostBackgroundScheduler  # 兼容一下名字，fsdf是 function-scheduling-distributed-framework 老框架名字的缩写
# funboost_aps_scheduler定时配置基于内存的，不可以跨机器远程动态添加/修改/删除定时任务配置。如果需要动态增删改查定时任务，可以使用funboost_background_scheduler_redis_store

funboost_aps_scheduler = FunboostBackgroundScheduler(timezone=funboost_config_deafult.TIMEZONE, daemon=False, )
fsdf_background_scheduler = funboost_aps_scheduler  # 兼容一下老名字。

if __name__ == '__main__':
    # 定时运行消费演示
    import datetime
    from funboost import boost, BrokerEnum, fsdf_background_scheduler, timing_publish_deco, run_forever, Booster


    @Booster('queue_test_666', broker_kind=BrokerEnum.LOCAL_PYTHON_QUEUE)
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
