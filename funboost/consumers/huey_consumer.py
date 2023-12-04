import time

from huey import RedisHuey
from huey.consumer import Consumer

from funboost import AbstractConsumer
from funboost.assist.huey_helper import HueyHelper


class HueyConsumer(AbstractConsumer):
    """
    huey作为中间件实现的。
    """

    BROKER_EXCLUSIVE_CONFIG_DEFAULT = {'huey_task_kwargs': {}}
    """
    retries=0, retry_delay=0, priority=None, context=False,
             name=None, expires=None, **kwargs
    """

    def custom_init(self):
        # 这就是核心，
        huey_task_kwargs = self.consumer_params.broker_exclusive_config['huey_task_kwargs']
        huey_task_kwargs['retries'] = self.consumer_params.max_retry_times

        @HueyHelper.huey_obj.task(name=self.queue_name,
                        **huey_task_kwargs)
        def f(*args, **kwargs):
            self.logger.debug(f' 这条消息是 huey 从 {self.queue_name} 队列中取出 ,是由 huey 框架调度 {self.consuming_function.__name__} 函数处理: args:  {args} ,  kwargs: {kwargs}')
            return self.consuming_function(*args, **kwargs)

        HueyHelper.queue_name__huey_task_fun_map[self.queue_name] = f

    def start_consuming_message(self):
        # 不单独每个函数都启动一次celery的worker消费，是把要消费的 queue name放到列表中，realy_start_dramatiq_worker 一次性启动多个函数消费。
        HueyHelper.to_be_start_huey_queue_name_set.add(self.queue_name)
        super().start_consuming_message()

    def _shedual_task(self):
        """ 完全由dramatiq框架接管控制消费，不使用funboost的AbstractConsumer的_run"""
        while 1:
            time.sleep(100)

    def _confirm_consume(self, kw):
        """dramatiq框架默认自带，不需要funboost实现"""

    def _requeue(self, kw):
        pass
