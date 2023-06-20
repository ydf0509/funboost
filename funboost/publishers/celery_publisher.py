# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 12:12
import os
import sys
import uuid
import copy
import time
import threading
import json
import celery
import celery.result
import typing

from funboost.assist.celery_helper import celery_app
from funboost.publishers.base_publisher import AbstractPublisher, PriorityConsumingControlConfig


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

        celery_app.conf.task_routes.update({self.queue_name: {"queue": self.queue_name}})

    def publish(self, msg: typing.Union[str, dict], task_id=None,
                priority_control_config: PriorityConsumingControlConfig = None) -> celery.result.AsyncResult:
        msg, msg_function_kw, extra_params = self._convert_msg(msg, task_id, priority_control_config)
        t_start = time.time()
        celery_result = celery_app.send_task(name=self.queue_name, kwargs=msg_function_kw, task_id=extra_params['task_id'])  # type: celery.result.AsyncResult
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

    def clear(self):
        python_executable = sys.executable
        cmd = f''' {python_executable} -m celery -A funboost.publishers.celery_publisher purge -Q {self.queue_name} -f'''
        self.logger.warning(f'刪除celery {self.queue_name} 隊列中的消息  {cmd}')
        os.system(cmd)

    def get_message_count(self):
        # return -1
        with celery_app.connection_or_acquire() as conn:
            msg_cnt = conn.default_channel.queue_declare(
                queue=self.queue_name, passive=False,durable=True,auto_delete=False).message_count
        return msg_cnt

    def close(self):
        pass
