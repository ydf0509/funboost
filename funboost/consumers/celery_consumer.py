# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 13:32
import logging
import json
from funboost.consumers.base_consumer import AbstractConsumer
import celery


# from funboost.publishers.celery_publisher import celery_app


class CeleryConsumer(AbstractConsumer):
    """
    celery作为中间件实现的。
    """
    BROKER_KIND = 30
    BROKER_EXCLUSIVE_CONFIG_DEFAULT = {'broker': 'redis://192.168.64.151:6378/11'}

    def _shedual_task(self):
        raw_fun = self.consuming_function

        celery_app = celery.Celery(broker='redis://192.168.64.151:6378/11')

        # celery_app.config_from_object(self.broker_exclusive_config)
        if not celery_app.conf.task_routes:
            celery_app.conf.task_routes = {}
        celery_app.conf.task_routes.update({self.queue_name: {"queue": self.queue_name}})

        celery_app.conf.task_reject_on_worker_lost = True  # 配置这两项可以随意停止
        celery_app.conf.task_acks_late = True

        # celery_app.conf.worker_task_log_format = '%(asctime)s - %(name)s - "%(pathname)s:%(lineno)d" - %(funcName)s - %(levelname)s - %(message)s'
        # celery_app.conf.worker_log_format = '%(asctime)s - %(name)s - "%(pathname)s:%(lineno)d" - %(funcName)s - %(levelname)s - %(message)s'

        celery_app.conf.worker_redirect_stdouts = False

        @celery_app.task(name=self.queue_name)
        def f(*args, **kwargs):
            # func_params = json.loads(msg)
            # func_params.pop('extra')
            # return raw_fun(**func_params)
            # print(args)
            # print(kwargs)
            self.logger.debug(f' 这条消息是 funboost 在 celery 框架中处理的: {kwargs}')
            return raw_fun(*args, **kwargs)

        # celery_app.worker_main(
        #     argv=['worker', '--pool=threads', '--concurrency=500', '-n', 'worker1@%h', '--loglevel=INFO',
        #           f'--queues={self.queue_name}',
        #           ])

        # logging.getLevelName(self._log_level)
        celery_app.worker_main(
            argv=['worker', '--pool=threads', f'--concurrency={self._concurrent_num}',
                  '-n', f'worker_{self.queue_name}@%h', f'--loglevel=INFO',
                  f'--queues={self.queue_name}',
                  ])

    def _confirm_consume(self, kw):
        pass

    def _requeue(self, kw):
        pass
