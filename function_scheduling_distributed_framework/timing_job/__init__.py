"""
集成定时任务。
"""
from typing import Union
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.util import undefined

from function_scheduling_distributed_framework import frame_config

from function_scheduling_distributed_framework.consumers.base_consumer import AbstractConsumer


def timing_publish_deco(consuming_func_decorated_or_consumer: Union[callable, AbstractConsumer]):
    def _deco(*args, **kwargs):
        if getattr(consuming_func_decorated_or_consumer, 'is_decorated_as_consume_function') is True:
            consuming_func_decorated_or_consumer.push(*args, **kwargs)
        elif isinstance(consuming_func_decorated_or_consumer, AbstractConsumer):
            consuming_func_decorated_or_consumer.publisher_of_same_queue.push(*args, **kwargs)
        else:
            raise TypeError('consuming_func_decorated_or_consumer 必须是被 task_deco 装饰的函数或者consumer类型')

    return _deco


class FsdfBackgroundScheduler(BackgroundScheduler):
    """
    自定义的，添加一个方法add_timing_publish_job
    """

    def add_timing_publish_job(self, func, trigger=None, args=None, kwargs=None, id=None, name=None,
                               misfire_grace_time=undefined, coalesce=undefined, max_instances=undefined,
                               next_run_time=undefined, jobstore='default', executor='default',
                               replace_existing=False, **trigger_args):
        return self.add_job(timing_publish_deco(func), trigger, args, kwargs, id, name,
                            misfire_grace_time, coalesce, max_instances,
                            next_run_time, jobstore, executor,
                            replace_existing, **trigger_args)


fsdf_background_scheduler = FsdfBackgroundScheduler(timezone=frame_config.TIMEZONE)

if __name__ == '__main__':
    # 定时运行消费演示
    import datetime
    from function_scheduling_distributed_framework import task_deco, BrokerEnum, fsdf_background_scheduler, timing_publish_deco


    @task_deco('queue_test_666', broker_kind=BrokerEnum.LOCAL_PYTHON_QUEUE)
    def consume_func(x, y):
        print(f'{x} + {y} = {x + y}')


    if __name__ == '__main__':
        fsdf_background_scheduler.add_job(timing_publish_deco(consume_func), 'interval', id='3_second_job', seconds=3, kwargs={"x": 5, "y": 6})  # 每隔3秒发布一次任务，自然就能每隔3秒消费一次任务了。
        fsdf_background_scheduler.add_job(timing_publish_deco(consume_func), 'date', run_date=datetime.datetime(2020, 7, 24, 13, 53, 6), args=(5, 6,))  # 定时，只执行一次
        fsdf_background_scheduler.add_timing_publish_job(consume_func, 'cron', day_of_week='*', hour=14, minute=51, second=20, args=(5, 6,))  # 定时，每天的11点32分20秒都执行一次。

        # 启动定时
        fsdf_background_scheduler.start()

        # 启动消费
        consume_func.consume()

