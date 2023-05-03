# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 13:32
import os
import sys
import threading
import typing

from functools import partial

from funboost import funboost_config_deafult

from funboost.consumers.base_consumer import AbstractConsumer
import celery

from funboost.publishers.celery_publisher import celery_app


class CeleryConsumer(AbstractConsumer):
    """
    celery作为中间件实现的。
    """
    BROKER_KIND = 30
    BROKER_EXCLUSIVE_CONFIG_DEFAULT = {'celery_task_config': {}}

    # celery的可以配置项大全  https://docs.celeryq.dev/en/stable/userguide/configuration.html#new-lowercase-settings

    def custom_init(self):
        @celery_app.task(name=self.queue_name,rate_limit=f'{self._qps}/s',**self.broker_exclusive_config['celery_task_config'])
        def f(*args, **kwargs):
            self.logger.debug(f' 这条消息将由 funboost 在 celery 框架中处理: args:  {args} ,  kwargs: {kwargs}')
            return self.consuming_function(*args, **kwargs)

    def _shedual_task(self):
        """ 建议使用 batch_start_celery_consumers([f1,f2]) ,而不是 f1.consume()  f2.consume() 方式"""


        # # celery_app.worker_main(
        # #     argv=['worker', '--pool=threads', '--concurrency=500', '-n', 'worker1@%h', '--loglevel=INFO',
        # #           f'--queues={self.queue_name}',
        # #           ])
        #
        # # logging.getLevelName(self._log_level)
        def f():
            celery_app.worker_main(
                argv=['worker', '--pool=threads', f'--concurrency={self._concurrent_num}',
                      '-n', f'worker_{self.queue_name}@%h', f'--loglevel=INFO',
                      f'--queues={self.queue_name}',
                      ])

        # threading.Thread(target=f).start()
        f()
        #
        # # worker = celery_app.Worker()
        # # worker.start()

    def _confirm_consume(self, kw):
        pass

    def _requeue(self, kw):
        pass


def celery_start_beat(beat_schedule: dict):
    celery_app.conf.beat_schedule = beat_schedule

    def _f():
        beat = partial(celery_app.Beat, loglevel='INFO', )
        beat().run()

    threading.Thread(target=_f).start()  # 使得可以很方便启动定时任务，继续启动函数消费


def start_flower(port=5555):
    def _f():
        python_executable = sys.executable
        # print(python_executable)

        # cmd = f'''{python_executable} -m celery -A funboost.publishers.celery_publisher --broker={funboost_config_deafult.CELERY_BROKER_URL}  --result-backend={funboost_config_deafult.CELERY_RESULT_BACKEND}   flower --address=0.0.0.0 --port={port}  --auto_refresh=True '''
        cmd = f'''{python_executable} -m celery  --broker={funboost_config_deafult.CELERY_BROKER_URL}  --result-backend={funboost_config_deafult.CELERY_RESULT_BACKEND}   flower --address=0.0.0.0 --port={port}  --auto_refresh=1 '''

        print(f'启动flower命令:   {cmd}')
        os.system(cmd)
    threading.Thread(target=_f).start()


def batch_start_celery_consumers(consumers: typing.List):
    queue_names = [consumer.queue_name for consumer in consumers]
    queue_names_str = ','.join(queue_names)

    celery_app.worker_main(
        argv=['worker', '--pool=threads', '--concurrency=200',
              '-n', f'worker_funboost_pid_{os.getpid()}@%h', f'--loglevel=INFO',
              f'--queues={queue_names_str}',
              ])