# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 12:12
import uuid
import copy
import time
import threading
import json
import celery
import celery.result
import typing

from funboost.publishers.base_publisher import AbstractPublisher, PriorityConsumingControlConfig
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
                                   backend=funboost_config_deafult.CELERY_RESULT_BACKEND,
                                   task_routes={}, timezone=funboost_config_deafult.TIMEZONE, enable_utc=False)
        celery_app.config_from_object(self.broker_exclusive_config['celery_app_config'])
        celery_app.conf.task_routes.update({self.queue_name: {"queue": self.queue_name}})

        @celery_app.task(name=self.queue_name)
        def f(*args, **kwargs):
            pass

        self._celery_app = celery_app
        self._celery_fun = f

        self._has_build_celery_app = True

    def publish(self, msg: typing.Union[str, dict], task_id=None,
                priority_control_config: PriorityConsumingControlConfig = None) -> celery.result.AsyncResult:
        if isinstance(msg, str):
            msg = json.loads(msg)
        msg_function_kw = copy.copy(msg)
        if self.publish_params_checker:
            self.publish_params_checker.check_params(msg)
        task_id = task_id or f'{self._queue_name}_result:{uuid.uuid4()}'
        msg['extra'] = extra_params = {'task_id': task_id, 'publish_time': round(time.time(), 4),
                                       'publish_time_format': time.strftime('%Y-%m-%d %H:%M:%S')}
        if priority_control_config:
            extra_params.update(priority_control_config.to_dict())
        with self.celery_conf_lock:
            if not self._has_build_celery_app:
                self._build_celery_app()
        t_start = time.time()
        celery_result = self._celery_fun.apply_async(kwargs=msg_function_kw, task_id=extra_params['task_id'])  # type: celery.result.AsyncResult
        self.logger.debug(f'向{self._queue_name} 队列，推送消息 耗时{round(time.time() - t_start, 4)}秒  {msg_function_kw}')  # 显示msg太长了。
        with self._lock_for_count:
            self.count_per_minute += 1
            self.publish_msg_num_total += 1
            if time.time() - self._current_time > 10:
                self.logger.info(
                    f'10秒内推送了 {self.count_per_minute} 条消息,累计推送了 {self.publish_msg_num_total} 条消息到 {self._queue_name} 队列中')
                self._init_count()
        # return AsyncResult(task_id)
        return celery_result  # 这里返回celery结果原生对象，类型是 celery.result.AsyncResult。

    def concrete_realization_of_publish(self, msg):
        pass
        # with self.celery_conf_lock:
        #     if not self._has_build_celery_app:
        #         # t = threading.Thread(target=self._build_celery_app_in_new_thread)
        #         # t.start()
        #         # t.join()
        #         self._build_celery_app()
        #
        # func_params = json.loads(msg)
        # msg_extra = func_params['extra']
        # func_params.pop('extra')
        # return self._celery_fun.apply_async(kwargs=func_params, task_id=msg_extra['task_id'])

    def clear(self):
        pass

    def get_message_count(self):
        return -1

    def close(self):
        pass
