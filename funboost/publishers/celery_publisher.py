# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 12:12
import threading

import json

import celery
from funboost.publishers.base_publisher import AbstractPublisher
from funboost import funboost_config_deafult

# celery_app = celery.Celery(broker='redis://192.168.64.151:6378/11',task_routes={})


class CeleryPublisher(AbstractPublisher, ):
    """
    使用celery作为中间件
    """
    celery_conf_lock = threading.Lock()

    # noinspection PyAttributeOutsideInit
    def custom_init(self):
        # self.broker_exclusive_config['task_routes'] = {self.queue_name: {"queue": self.queue_name}}
        # celery_app.config_from_object(self.broker_exclusive_config)
        pass

        # celery_app.conf.task_routes.update({self.queue_name: {"queue": self.queue_name}})
        #
        # @celery_app.task(name=self.queue_name)
        # def f(*args, **kwargs):
        #     pass
        #
        # self._celery_app = celery_app
        # self._celery_fun = f

        self._has_build_celery_app = False

    def _build_celery_app(self):
        celery_app = celery.Celery(broker=funboost_config_deafult.CELERY_BROKER_URL,
                                   backend = funboost_config_deafult.CELERY_RESULT_BACKEND,
                                   task_routes={})
        celery_app.config_from_object(self.broker_exclusive_config['celery_app_config'])
        celery_app.conf.task_routes.update({self.queue_name: {"queue": self.queue_name}})

        @celery_app.task(name=self.queue_name)
        def f(*args, **kwargs):
            pass

        self._celery_app = celery_app
        self._celery_fun = f

        self._has_build_celery_app = True

    def concrete_realization_of_publish(self, msg):
        with self.celery_conf_lock:
            if not self._has_build_celery_app:
                # t = threading.Thread(target=self._build_celery_app_in_new_thread)
                # t.start()
                # t.join()
                self._build_celery_app()
        func_params = json.loads(msg)
        func_params.pop('extra')
        self._celery_fun.delay(**func_params)

    def clear(self):
        pass

    def get_message_count(self):
        return -1

    def close(self):
        # self.redis_db7.connection_pool.disconnect()
        pass
