# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2019/8/8 0008 12:12
import json
from function_scheduling_distributed_framework.publishers.base_publisher import AbstractPublisher
from function_scheduling_distributed_framework.utils import RedisMixin


class RedisStreamPublisher(AbstractPublisher, RedisMixin):
    """
    使用redis作为中间件,这个是
    """

    def custom_init(self):
        redis_server_info_dict = self.redis_db_frame_version3.info()
        if float(redis_server_info_dict['redis_version'][0]) < 5:
            raise EnvironmentError('必须是5.0版本以上redis服务端才能支持  stream 数据结构，'
                                   '请升级服务端，否则使用 REDIS_ACK_ABLE 方式使用redis')
        if self.redis_db_frame_version3.type(self._queue_name) == 'list':
            raise EnvironmentError(f'检测到已存在 {self._queue_name} 这个键，且类型是list， 必须换个队列名字或者删除这个 list 类型的键。'
                                   f'RedisStreamConsumer 使用的是 stream数据结构')

    def concrete_realization_of_publish(self, msg):
        # redis服务端必须是5.0以上，并且确保这个键的类型是stream不能是list数据结构。
        self.redis_db_frame_version3.xadd(self._queue_name, {"": msg})

    def clear(self):
        self.redis_db_frame.delete(self._queue_name)
        self.redis_db_frame.delete(f'{self._queue_name}__unack')
        self.logger.warning(f'清除 {self._queue_name} 队列中的消息成功')

    def get_message_count(self):
        # nb_print(self.redis_db7,self._queue_name)
        return self.redis_db_frame_version3.xlen(self._queue_name)

    def close(self):
        # self.redis_db7.connection_pool.disconnect()
        pass
