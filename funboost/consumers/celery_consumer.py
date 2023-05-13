# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 13:32
import logging
import os
import sys
import threading
import time
from functools import partial

import nb_log
from nb_log import get_logger

from funboost import funboost_config_deafult
from funboost.consumers.base_consumer import AbstractConsumer
from funboost.publishers.celery_publisher import celery_app
from funboost.constant import ConcurrentModeEnum


class CeleryConsumer(AbstractConsumer):
    """
    celery作为中间件实现的。
    """

    BROKER_EXCLUSIVE_CONFIG_DEFAULT = {'celery_task_config': {}}

    # celery的可以配置项大全  https://docs.celeryq.dev/en/stable/userguide/configuration.html#new-lowercase-settings
    # celery @app.task() 所有可以配置项可以看  D:\ProgramData\Miniconda3\Lib\site-packages\celery\app\task.py

    '''
        #: Execution strategy used, or the qualified name of one.
        Strategy = 'celery.worker.strategy:default'

        #: Request class used, or the qualified name of one.
        Request = 'celery.worker.request:Request'

        #: The application instance associated with this task class.
        _app = None

        #: Name of the task.
        name = None

        #: Enable argument checking.
        #: You can set this to false if you don't want the signature to be
        #: checked when calling the task.
        #: Defaults to :attr:`app.strict_typing <@Celery.strict_typing>`.
        typing = None

        #: Maximum number of retries before giving up.  If set to :const:`None`,
        #: it will **never** stop retrying.
        max_retries = 3

        #: Default time in seconds before a retry of the task should be
        #: executed.  3 minutes by default.
        default_retry_delay = 3 * 60

        #: Rate limit for this task type.  Examples: :const:`None` (no rate
        #: limit), `'100/s'` (hundred tasks a second), `'100/m'` (hundred tasks
        #: a minute),`'100/h'` (hundred tasks an hour)
        rate_limit = None

        #: If enabled the worker won't store task state and return values
        #: for this task.  Defaults to the :setting:`task_ignore_result`
        #: setting.
        ignore_result = None

        #: If enabled the request will keep track of subtasks started by
        #: this task, and this information will be sent with the result
        #: (``result.children``).
        trail = True

        #: If enabled the worker will send monitoring events related to
        #: this task (but only if the worker is configured to send
        #: task related events).
        #: Note that this has no effect on the task-failure event case
        #: where a task is not registered (as it will have no task class
        #: to check this flag).
        send_events = True

        #: When enabled errors will be stored even if the task is otherwise
        #: configured to ignore results.
        store_errors_even_if_ignored = None

        #: The name of a serializer that are registered with
        #: :mod:`kombu.serialization.registry`.  Default is `'json'`.
        serializer = None

        #: Hard time limit.
        #: Defaults to the :setting:`task_time_limit` setting.
        time_limit = None

        #: Soft time limit.
        #: Defaults to the :setting:`task_soft_time_limit` setting.
        soft_time_limit = None

        #: The result store backend used for this task.
        backend = None

        #: If enabled the task will report its status as 'started' when the task
        #: is executed by a worker.  Disabled by default as the normal behavior
        #: is to not report that level of granularity.  Tasks are either pending,
        #: finished, or waiting to be retried.
        #:
        #: Having a 'started' status can be useful for when there are long
        #: running tasks and there's a need to report what task is currently
        #: running.
        #:
        #: The application default can be overridden using the
        #: :setting:`task_track_started` setting.
        track_started = None

        #: When enabled messages for this task will be acknowledged **after**
        #: the task has been executed, and not *just before* (the
        #: default behavior).
        #:
        #: Please note that this means the task may be executed twice if the
        #: worker crashes mid execution.
        #:
        #: The application default can be overridden with the
        #: :setting:`task_acks_late` setting.
        acks_late = None

        #: When enabled messages for this task will be acknowledged even if it
        #: fails or times out.
        #:
        #: Configuring this setting only applies to tasks that are
        #: acknowledged **after** they have been executed and only if
        #: :setting:`task_acks_late` is enabled.
        #:
        #: The application default can be overridden with the
        #: :setting:`task_acks_on_failure_or_timeout` setting.
        acks_on_failure_or_timeout = None

        #: Even if :attr:`acks_late` is enabled, the worker will
        #: acknowledge tasks when the worker process executing them abruptly
        #: exits or is signaled (e.g., :sig:`KILL`/:sig:`INT`, etc).
        #:
        #: Setting this to true allows the message to be re-queued instead,
        #: so that the task will execute again by the same worker, or another
        #: worker.
        #:
        #: Warning: Enabling this can cause message loops; make sure you know
        #: what you're doing.
        reject_on_worker_lost = None

        #: Tuple of expected exceptions.
        #:
        #: These are errors that are expected in normal operation
        #: and that shouldn't be regarded as a real error by the worker.
        #: Currently this means that the state will be updated to an error
        #: state, but the worker won't log the event as an error.
        throws = ()

        #: Default task expiry time.
        expires = None

        #: Default task priority.
        priority = None

        #: Max length of result representation used in logs and events.
        resultrepr_maxsize = 1024

        #: Task request stack, the current request will be the topmost.
        request_stack = None
    '''

    def custom_init(self):
        # 这就是核心，@boost时候回注册任务路由到celery_app
        @celery_app.task(name=self.queue_name, rate_limit=f'{self._qps}/s', soft_time_limit=self._function_timeout,
                         max_retries=self._max_retry_times,
                         **self.broker_exclusive_config['celery_task_config'])
        def f(*args, **kwargs):
            self.logger.debug(f' 这条消息是 celery 从 {self.queue_name} 队列中取出 ,是由 celery 框架调度 {self.consuming_function.__name__} 函数处理: args:  {args} ,  kwargs: {kwargs}')
            return self.consuming_function(*args, **kwargs)

        CeleryHelper.concurrent_mode = self._concurrent_mode

        # print(type(f), dir(f), f.__dict__)

    # def _shedual_task000(self):
    #     """ 建议使用 batch_start_celery_consumers([f1,f2]) ,而不是 f1.consume()  f2.consume() 方式"""
    #
    #     # # celery_app.worker_main(
    #     # #     argv=['worker', '--pool=threads', '--concurrency=500', '-n', 'worker1@%h', '--loglevel=INFO',
    #     # #           f'--queues={self.queue_name}',
    #     # #           ])
    #     #
    #     # # logging.getLevelName(self._log_level)
    #     def f():
    #         celery_app.worker_main(
    #             argv=['worker', '--pool=threads', f'--concurrency={self._concurrent_num}',
    #                   '-n', f'worker_{self.queue_name}@%h', f'--loglevel=INFO',
    #                   f'--queues={self.queue_name}',
    #                   ])
    #
    #     # threading.Thread(target=f).start()
    #     f()
    #     #
    #     # # worker = celery_app.Worker()
    #     # # worker.start()
    #     # raise Exception('不建议这样启动')

    def start_consuming_message(self):
        # 不单独每个函数都启动一次celery的worker消费，是把要消费的 queue name放到列表中，realy_start_celery_worker 一次性启动多个函数消费。
        CeleryHelper.to_be_start_work_celery_queue_name_set.add(self.queue_name)
        super().start_consuming_message()

    def _shedual_task(self):
        while 1:
            time.sleep(100)

    def _confirm_consume(self, kw):
        pass

    def _requeue(self, kw):
        pass


class CeleryHelper:
    celery_app = celery_app
    to_be_start_work_celery_queue_name_set = set()  # 存放需要worker运行的queue name。
    to_be_start_work_celery_queue_name__conmsumer_map = {}
    logger = get_logger('funboost.CeleryHelper')
    concurrent_mode = None

    @staticmethod
    def update_celery_app_conf(celery_app_conf: dict):
        """
        更新celery app的配置，celery app配置大全见 https://docs.celeryq.dev/en/stable/userguide/configuration.html
        :param celery_app_conf:
        :return:
        """
        celery_app.conf.update(celery_app_conf)

    @classmethod
    def show_celery_app_conf(cls):
        cls.logger.debug('展示celery app的配置')
        for k, v in celery_app.conf.items():
            print(k, ' : ', v)

    @staticmethod
    def celery_start_beat(beat_schedule: dict):
        celery_app.conf.beat_schedule = beat_schedule  # 配置celery定时任务

        def _f():
            beat = partial(celery_app.Beat, loglevel='INFO', )
            beat().run()

        threading.Thread(target=_f).start()  # 使得可以很方便启动定时任务，继续启动函数消费

    @classmethod
    def start_flower(cls, port=5555):
        def _f():
            python_executable = sys.executable
            # print(python_executable)

            # cmd = f'''{python_executable} -m celery -A funboost.publishers.celery_publisher --broker={funboost_config_deafult.CELERY_BROKER_URL}  --result-backend={funboost_config_deafult.CELERY_RESULT_BACKEND}   flower --address=0.0.0.0 --port={port}  --auto_refresh=True '''
            cmd = f'''{python_executable} -m celery  --broker={funboost_config_deafult.CELERY_BROKER_URL}  --result-backend={funboost_config_deafult.CELERY_RESULT_BACKEND}   flower --address=0.0.0.0 --port={port}  --auto_refresh=True '''

            cls.logger.info(f'启动flower命令:   {cmd}')
            os.system(cmd)

        threading.Thread(target=_f).start()

    @classmethod
    def realy_start_celery_worker(cls, worker_name=None):
        if len(cls.to_be_start_work_celery_queue_name_set) == 0:
            raise Exception('celery worker 没有需要运行的queue')
        queue_names_str = ','.join(list(cls.to_be_start_work_celery_queue_name_set))
        # '--concurrency=200',
        # '--autoscale=5,500' threads 并发模式不支持自动扩大缩小并发数量,
        worker_name = worker_name or f'pid_{os.getpid()}'
        pool_name = 'threads'
        if cls.concurrent_mode == ConcurrentModeEnum.GEVENT:
            pool_name = 'gevent'
        if cls.concurrent_mode == ConcurrentModeEnum.EVENTLET:
            pool_name = 'eventlet'
        argv = ['worker', f'--pool={pool_name}', '--concurrency=200',
                '-n', f'worker_funboost_{worker_name}@%h', f'--loglevel=INFO',
                f'--queues={queue_names_str}',
                ]
        cls.logger.info(f'celery 启动work参数 {argv}')
        celery_app.worker_main(argv)

    @staticmethod
    def use_nb_log_instead_celery_log(log_level: int = logging.INFO, log_filename='celery.log', formatter_template=7):
        """
        使用nb_log的日志来取代celery的日志
        """
        celery_app.conf.worker_hijack_root_logger = False
        nb_log.get_logger('celery', log_level_int=log_level, log_filename=log_filename, formatter_template=formatter_template, )
