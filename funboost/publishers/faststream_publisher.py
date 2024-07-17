# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2023/8/8 0008 12:12

import abc
import asyncio
import json
import time
import typing

from funboost import PriorityConsumingControlConfig
from funboost.core.serialization import Serialization
from funboost.publishers.base_publisher import AbstractPublisher
from funboost.assist.faststream_helper import app,get_broker
from faststream import FastStream,Context
from faststream.annotations import Logger

class FastStreamPublisher(AbstractPublisher, metaclass=abc.ABCMeta):
    """
    空的发布者，空的实现，需要搭配 boost入参的 consumer_override_cls 和 publisher_override_cls使用，或者被继承。
    """
    def custom_init(self):
        pass
        # asyncio.get_event_loop().run_until_complete(broker.start())
        self.broker = get_broker()
        asyncio.get_event_loop().run_until_complete(self.broker.connect())

    def publish(self, msg: typing.Union[str, dict], task_id=None,
                priority_control_config: PriorityConsumingControlConfig = None) :
        msg, msg_function_kw, extra_params, task_id = self._convert_msg(msg, task_id, priority_control_config)
        t_start = time.time()
        faststream_result =  asyncio.get_event_loop().run_until_complete(self.broker.publish(Serialization.to_json_str(msg), self.queue_name))
        self.logger.debug(f'向{self._queue_name} 队列，推送消息 耗时{round(time.time() - t_start, 4)}秒  {msg_function_kw}')  # 显示msg太长了。
        with self._lock_for_count:
            self.count_per_minute += 1
            self.publish_msg_num_total += 1
            if time.time() - self._current_time > 10:
                self.logger.info(
                    f'10秒内推送了 {self.count_per_minute} 条消息,累计推送了 {self.publish_msg_num_total} 条消息到 {self._queue_name} 队列中')
                self._init_count()
        # return AsyncResult(task_id)
        return faststream_result  #

    def concrete_realization_of_publish(self, msg):
        pass


    def clear(self):
        pass


    def get_message_count(self):
        return -1


    def close(self):
        pass
