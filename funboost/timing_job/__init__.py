"""
集成定时任务。
"""
import importlib

import pickle

import time
from typing import Union
import threading

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.redis import RedisJobStore
# noinspection PyProtectedMember
from apscheduler.util import undefined

from funboost import funboost_config_deafult

from funboost.consumers.base_consumer import AbstractConsumer



def timing_publish_deco(consuming_func_decorated_or_consumer: Union[callable, AbstractConsumer]):
    def _deco(*args, **kwargs):
        if getattr(consuming_func_decorated_or_consumer, 'is_decorated_as_consume_function', False) is True:
            consuming_func_decorated_or_consumer.push(*args, **kwargs)
        elif isinstance(consuming_func_decorated_or_consumer, AbstractConsumer):
            consuming_func_decorated_or_consumer.publisher_of_same_queue.push(*args, **kwargs)
        else:
            raise TypeError('consuming_func_decorated_or_consumer 必须是被 boost 装饰的函数或者consumer类型')

    return _deco


class FsdfBackgroundScheduler(BackgroundScheduler):
    """
    自定义的，添加一个方法add_timing_publish_job
    """

    # noinspection PyShadowingBuiltins
    def add_timing_publish_job(self, func, trigger=None, args=None, kwargs=None, id=None, name=None,
                               misfire_grace_time=undefined, coalesce=undefined, max_instances=undefined,
                               next_run_time=undefined, jobstore='default', executor='default',
                               replace_existing=False, **trigger_args):
        return self.add_job(timing_publish_deco(func), trigger, args, kwargs, id, name,
                            misfire_grace_time, coalesce, max_instances,
                            next_run_time, jobstore, executor,
                            replace_existing, **trigger_args)

    def start(self,paused=False):
        # def _block_exit():
        #     while True:
        #         time.sleep(3600)
        #
        # threading.Thread(target=_block_exit).start()  # 既不希望用BlockingScheduler阻塞主进程也不希望定时退出。
        # self._daemon = False
        super(FsdfBackgroundScheduler, self).start(paused=paused)
        # _block_exit()   # python3.9 判断守护线程结束必须主线程在运行，否则结尾




fsdf_background_scheduler = FsdfBackgroundScheduler(timezone=funboost_config_deafult.TIMEZONE,daemon=False,)
funboost_aps_scheduler = fsdf_background_scheduler   # 定时配置基于内存的，不可以跨机器远程动态添加/修改/删除定时任务配置


# fsdf_background_scheduler = FsdfBackgroundScheduler()


if __name__ == '__main__':
    # 定时运行消费演示
    import datetime
    from funboost import boost, BrokerEnum, fsdf_background_scheduler, timing_publish_deco


    @boost('queue_test_666', broker_kind=BrokerEnum.LOCAL_PYTHON_QUEUE)
    def consume_func(x, y):
        print(f'{x} + {y} = {x + y}')


    # 定时每隔3秒执行一次。
    fsdf_background_scheduler.add_job(timing_publish_deco(consume_func),
                                      'interval', id='3_second_job', seconds=3, kwargs={"x": 5, "y": 6})

    # 定时，只执行一次
    fsdf_background_scheduler.add_job(timing_publish_deco(consume_func),
                                      'date', run_date=datetime.datetime(2020, 7, 24, 13, 53, 6), args=(5, 6,))

    # 定时，每天的11点32分20秒都执行一次。
    fsdf_background_scheduler.add_timing_publish_job(consume_func,
                                                     'cron', day_of_week='*', hour=18, minute=22, second=20, args=(5, 6,))

    # 启动定时
    fsdf_background_scheduler.start()

    # 启动消费
    consume_func.consume()
