import json
import logging
import os
import sys
import threading
from functools import partial

import celery

from funboost import funboost_config_deafult, ConcurrentModeEnum
from nb_log import get_logger

celery_app = celery.Celery(main='funboost_celery', broker=funboost_config_deafult.CELERY_BROKER_URL,
                           backend=funboost_config_deafult.CELERY_RESULT_BACKEND,
                           task_routes={}, timezone=funboost_config_deafult.TIMEZONE, enable_utc=False, )

celery_app.conf.task_acks_late = True
celery_app.conf.worker_redirect_stdouts = False

logger = get_logger('funboost.CeleryHelper')


class CeleryHelper:
    celery_app = celery_app
    to_be_start_work_celery_queue_name_set = set()  # start_consuming_message时候，添加需要worker运行的queue name。

    concurrent_mode = None

    @staticmethod
    def update_celery_app_conf(celery_app_conf: dict):
        """
        更新celery app的配置，celery app配置大全见 https://docs.celeryq.dev/en/stable/userguide/configuration.html
        :param celery_app_conf:
        :return:
        """
        celery_app.conf.update(celery_app_conf)

    @staticmethod
    def show_celery_app_conf():
        logger.debug('展示celery app的配置')
        conf_dict_json_able = {}
        for k, v in celery_app.conf.items():
            conf_dict_json_able[k] = str(v)
            # print(k, ' : ', v)
        print('celery app 的配置是：',json.dumps(conf_dict_json_able,ensure_ascii=False,indent=4))

    @staticmethod
    def celery_start_beat(beat_schedule: dict):
        celery_app.conf.beat_schedule = beat_schedule  # 配置celery定时任务

        def _f():
            beat = partial(celery_app.Beat, loglevel='INFO', )
            beat().run()

        threading.Thread(target=_f).start()  # 使得可以很方便启动定时任务，继续启动函数消费

    @staticmethod
    def start_flower(port=5555):
        def _f():
            python_executable = sys.executable
            # print(python_executable)
            # cmd = f'''{python_executable} -m celery -A funboost.publishers.celery_publisher --broker={funboost_config_deafult.CELERY_BROKER_URL}  --result-backend={funboost_config_deafult.CELERY_RESULT_BACKEND}   flower --address=0.0.0.0 --port={port}  --auto_refresh=True '''
            cmd = f'''{python_executable} -m celery  --broker={funboost_config_deafult.CELERY_BROKER_URL}  --result-backend={funboost_config_deafult.CELERY_RESULT_BACKEND}   flower --address=0.0.0.0 --port={port}  --auto_refresh=True '''

            logger.info(f'启动flower命令:   {cmd}')
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
        logger.info(f'celery 启动work参数 {argv}')
        celery_app.worker_main(argv)

    @staticmethod
    def use_nb_log_instead_celery_log(log_level: int = logging.INFO, log_filename='celery.log', formatter_template=7):
        """
        使用nb_log的日志来取代celery的日志
        """
        celery_app.conf.worker_hijack_root_logger = False
        get_logger('celery', log_level_int=log_level, log_filename=log_filename, formatter_template=formatter_template, )
