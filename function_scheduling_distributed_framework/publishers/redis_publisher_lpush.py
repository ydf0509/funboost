# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2019/8/8 0008 12:12


from function_scheduling_distributed_framework.publishers.redis_publisher import RedisPublisher


class RedisPublisherLpush(RedisPublisher):
    """
    使用redis作为中间件,这种是最简单的使用redis的方式，此方式不靠谱很容易丢失大量消息。非要用reids作为中间件，请用其他类型的redis consumer
    """

    def concrete_realization_of_publish(self, msg):
        self.redis_db_frame.lpush(self._queue_name, msg)


