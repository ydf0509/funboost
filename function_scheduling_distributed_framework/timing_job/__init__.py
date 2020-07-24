from typing import Union
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.util import undefined

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


class CustomBackgroundScheduler(BackgroundScheduler):
    """
    自定义的，添加一个方法add_timing_publish_job
    """

    def add_timing_publish_job(self, func, trigger=None, args=None, kwargs=None, id=None, name=None,
                               misfire_grace_time=undefined, coalesce=undefined, max_instances=undefined,
                               next_run_time=undefined, jobstore='default', executor='default',
                               replace_existing=False, **trigger_args):
        self.add_job(timing_publish_deco(func), trigger, args, kwargs, id, name,
                     misfire_grace_time, coalesce, max_instances,
                     next_run_time, jobstore, executor,
                     replace_existing, **trigger_args)


fsdf_background_scheduler = CustomBackgroundScheduler(timezone='Asia/Shanghai')
