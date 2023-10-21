# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/7/9 0008 12:12
import threading
import time
from funboost.funboost_config_deafult import BrokerConnConfig

from funboost.publishers.base_publisher import AbstractPublisher



class RocketmqPublisher(AbstractPublisher, ):
    _group_id__rocketmq_producer = {}
    _lock_for_create_producer = threading.Lock()

    # noinspection PyAttributeOutsideInit
    def custom_init(self):
        try:
            from rocketmq.client import Producer
        except BaseException as e:
            # print(traceback.format_exc())
            raise ImportError(f'rocketmq包 只支持linux和mac {str(e)}')

        group_id = f'g-{self._queue_name}'
        with self._lock_for_create_producer:
            if group_id not in self.__class__._group_id__rocketmq_producer:  # 同一个进程中创建多个同组消费者会报错。
                producer = Producer(group_id)
                producer.set_namesrv_addr(BrokerConnConfig.ROCKETMQ_NAMESRV_ADDR)
                producer.start()
                self.__class__._group_id__rocketmq_producer[group_id] = producer
            else:
                producer = self.__class__._group_id__rocketmq_producer[group_id]
            self._producer = producer

    def concrete_realization_of_publish(self, msg):
        try:
            from rocketmq.client import Message
        except BaseException as e:
            # print(traceback.format_exc())
            raise ImportError(f'rocketmq包 只支持linux和mac {str(e)}')
        rocket_msg = Message(self._queue_name)
        # rocket_msg.set_keys(msg)  # 利于检索
        # rocket_msg.set_tags('XXX')
        rocket_msg.set_body(msg)
        # print(msg)
        self._producer.send_sync(rocket_msg)

    def clear(self):
        self.logger.error('清除队列，python版的rocket包太弱了，没有方法设置偏移量或者删除主题。java才能做到')

    def get_message_count(self):
        if time.time() - getattr(self, '_last_warning_count', 0) > 300:
            setattr(self, '_last_warning_count', time.time())
            self.logger.warning('获取消息数量，python版的rocket包太弱了，没找到方法。java才能做到。')
        return -1

    def close(self):
        self._producer.shutdown()
