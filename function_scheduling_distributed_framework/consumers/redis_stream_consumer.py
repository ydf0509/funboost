# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2019/8/8 0008 13:32
import json
import time
from queue import Queue
from function_scheduling_distributed_framework.consumers.base_consumer import AbstractConsumer
from function_scheduling_distributed_framework.utils import RedisMixin


class RedisStreamConsumer(AbstractConsumer, RedisMixin):
    """
    redis作为中间件实现的。
    """
    BROKER_KIND = 12

    def _shedual_task(self):
        queue_tmp = Queue(100)
        redis_server_info_dict = self.redis_db_frame_version3.info()
        if float(redis_server_info_dict['redis_version'][0]) < 5:
            raise EnvironmentError('必须是5.0版本以上redis服务端才能支持  stream 数据结构，'
                                   '请升级服务端，否则使用 REDIS_ACK_ABLE 方式使用redis')
        if self.redis_db_frame_version3.type(self._queue_name) == 'list':
            raise EnvironmentError(f'检测到已存在 {self._queue_name} 这个键，且类型是list， 必须换个队列名字或者删除这个 list 类型的键。'
                                   f'RedisStreamConsumer 使用的是 stream数据结构')

        while True:
            # redis服务端必须是5.0以上，并且确保这个键的类型是stream不能是list数据结构。
            results = self.redis_db_frame_version3.xread({self._queue_name:'0-0'},count=100,block=60 *1000)
            print(results)
            if results:
                self.logger.debug(f'从redis的 [{self._queue_name}] 队列中 取出的消息是：  {results}  ')
                for msg_id,msg in results[0][1]:
                    kw = {'body': json.loads(msg['']),'msg_id':msg_id}
                    self._submit_task(kw)

    def _confirm_consume(self, kw):
        pass  # redis没有确认消费的功能。
        self.redis_db_frame_version3.xdel(self._queue_name,kw['msg_id'])

    def _requeue(self, kw):
        body = kw['body']
        self.redis_db_frame_version3.xadd(self._queue_name, {'':body})



