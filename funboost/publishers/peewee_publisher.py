# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2019/8/8 0008 13:05
from funboost.queues.peewee_queue import PeeweeQueue
from funboost.publishers.base_publisher import AbstractPublisher


# noinspection PyProtectedMember
class PeeweePublisher(AbstractPublisher):
    """
    使用Sqlachemy 操作数据库 ，实现的5种sql 数据库服务器作为 消息队列。包括sqlite mydql microsoftsqlserver postgre oracle
    这个是使用数据库表模拟的消息队列。这不是突发奇想一意孤行，很多包库都实现了这。
    """

    # noinspection PyAttributeOutsideInit
    def custom_init(self):
        self.queue = PeeweeQueue(self._queue_name, )

    def concrete_realization_of_publish(self, msg):
        # print(msg)
        self.queue.push(body=msg, )

    def clear(self):
        self.queue.clear_queue()
        self.logger.warning(f'清除 sqlalchemy 数据库队列 {self._queue_name} 中的消息成功')

    def get_message_count(self):
        return self.queue.to_be_consumed_count

    def close(self):
        pass
