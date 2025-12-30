# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 13:07
from collections import deque

from funboost.publishers.base_publisher import AbstractPublisher

deque_queue_name__deque_obj_map = dict()  # 使local queue和其他中间件完全一样的使用方式，使用映射保存队列的名字，使消费和发布通过队列名字能找到队列对象。


class DequePublisher(AbstractPublisher):
    """
    使用python内置queue对象作为中间件。方便测试，每个中间件的消费者类是鸭子类，多态可以互相替换。
    """

    # noinspection PyAttributeOutsideInit
    def custom_init(self):
        if self._queue_name not in deque_queue_name__deque_obj_map:
            deque_queue_name__deque_obj_map[self._queue_name] = deque()
        self.queue = deque_queue_name__deque_obj_map[self._queue_name]  # type: deque

    def _publish_impl(self, msg):
        # noinspection PyTypeChecker
        self.queue.append(msg)

    def clear(self):
        pass
        # noinspection PyUnresolvedReferences
        self.queue.clear()
        self.logger.warning(f'清除 本地队列中的消息成功')

    def get_message_count(self):
        return len(self.queue)

    def close(self):
        pass
