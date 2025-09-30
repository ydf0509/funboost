import time

import dramatiq

from funboost.consumers.base_consumer import AbstractConsumer
from funboost.assist.dramatiq_helper import DramatiqHelper


class DramatiqConsumer(AbstractConsumer):
    """
    dramatiq作为中间件实现的。
    """


    def custom_init(self):
        # 这就是核心，
        dramatiq_actor_options = self.consumer_params.broker_exclusive_config['dramatiq_actor_options']
        if self.consumer_params.function_timeout:
            dramatiq_actor_options['time_limit'] = self.consumer_params.function_timeout * 1000  # dramatiq的超时单位是毫秒，funboost是秒。
        dramatiq_actor_options['max_retries'] = self.consumer_params.max_retry_times

        @dramatiq.actor(actor_name=self.queue_name, queue_name=self.queue_name,
                        **dramatiq_actor_options)
        def f(*args, **kwargs):
            self.logger.debug(f' 这条消息是 dramatiq 从 {self.queue_name} 队列中取出 ,是由 dramatiq 框架调度 {self.consuming_function.__name__} 函数处理: args:  {args} ,  kwargs: {kwargs}')
            return self.consuming_function(*args, **kwargs)

        DramatiqHelper.queue_name__actor_map[self.queue_name] = f

    def start_consuming_message(self):
        # 不单独每个函数都启动一次celery的worker消费，是把要消费的 queue name放到列表中，realy_start_dramatiq_worker 一次性启动多个函数消费。
        DramatiqHelper.to_be_start_work_celery_queue_name_set.add(self.queue_name)
        super().start_consuming_message()

    def _shedual_task(self):
        """ 完全由dramatiq框架接管控制消费，不使用funboost的AbstractConsumer的_run"""
        while 1:
            time.sleep(100)

    def _confirm_consume(self, kw):
        """dramatiq框架默认自带，不需要funboost实现"""

    def _requeue(self, kw):
        pass
