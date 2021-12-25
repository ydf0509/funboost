# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2019/8/8 0008 12:12


from funboost.publishers.redis_publisher import RedisPublisher


class RedisPublisherLpush(RedisPublisher):
    """
    使用redis作为中间件,
    """

    _push_method = 'lpush'


