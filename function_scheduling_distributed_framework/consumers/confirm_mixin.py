# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2019/8/23 0023 21:10
import time
import json
from function_scheduling_distributed_framework.utils import RedisMixin


# noinspection PyUnresolvedReferences
class ConsumerConfirmMixinWithTheHelpOfRedis(RedisMixin):
    """
    使用redis的zset结构，value为任务，score为时间戳，这样具有良好的按时间范围搜索特性和删除特性。
    把这个抽离出来了。，是因为这个不仅可以给redis做消息确认，也可以给其他不支持消费确认的消息中间件增加消费确认。
    """
    # 超时未确认的时间，例如取出来后600秒都没有确认消费，就重新消费。这在rabbitmq和nsq对应的相同功能参数是heartbeat_interval。
    UNCONFIRMED_TIMEOUT = 600

    # noinspection PyAttributeOutsideInit
    def custom_init(self):
        self._unack_zset_name = f'{self._queue_name}__unack'

    def start_consuming_message(self):
        self.keep_circulating(60, block=False)(self.__requeue_tasks_which_unconfirmed_timeout)
        super().start_consuming_message()

    def _add_task_str_to_unack_zset(self, task_str, ):
        self.redis_db_frame.zadd(self._unack_zset_name, task_str, time.time())

    def _confirm_consume(self, kw):
        self.redis_db_frame.zrem(self._unack_zset_name, kw['task_str'])

    def __requeue_tasks_which_unconfirmed_timeout(self):
        time_max = time.time() - self.UNCONFIRMED_TIMEOUT
        for value in self.redis_db_frame.zrangebyscore(self._unack_zset_name, 0, time_max):
            self.logger.warning(f'向 {self._queue_name} 重新放入未消费确认的任务 {value}')
            self._requeue({'body': json.loads(value)})
            self.redis_db_frame.zrem(self._unack_zset_name, value)
        self.logger.info(f'{self._unack_zset_name} 中有待确认消费任务的数量是'
                         f' {self.redis_db_frame.zcard(self._unack_zset_name)}')
