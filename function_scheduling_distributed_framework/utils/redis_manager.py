# coding=utf8
import redis2 as redis
import redis3
from function_scheduling_distributed_framework import frame_config
from function_scheduling_distributed_framework.utils import decorators


class RedisManager(object):
    _pool_dict = {}

    def __init__(self, host='127.0.0.1', port=6379, db=0, password='123456'):
        if (host, port, db, password) not in self.__class__._pool_dict:
            # print ('创建一个连接池')
            self.__class__._pool_dict[(host, port, db, password)] = redis.ConnectionPool(host=host, port=port, db=db,
                                                                                         password=password)
        self._r = redis.Redis(connection_pool=self._pool_dict[(host, port, db, password)])
        self._ping()

    def get_redis(self):
        """
        :rtype :redis.Redis
        """
        return self._r

    def _ping(self):
        try:
            self._r.ping()
        except Exception as e:
            raise e


# noinspection PyArgumentEqualDefault
class RedisMixin(object):
    """
    可以被作为万能mixin能被继承，也可以单独实例化使用。
    """

    @property
    @decorators.cached_method_result
    def redis_db0(self):
        return RedisManager(host=frame_config.REDIS_HOST, port=frame_config.REDIS_PORT, password=frame_config.REDIS_PASSWORD, db=0).get_redis()

    @property
    @decorators.cached_method_result
    def redis_db8(self):
        return RedisManager(host=frame_config.REDIS_HOST, port=frame_config.REDIS_PORT, password=frame_config.REDIS_PASSWORD, db=8).get_redis()

    @property
    @decorators.cached_method_result
    def redis_db7(self):
        return RedisManager(host=frame_config.REDIS_HOST, port=frame_config.REDIS_PORT, password=frame_config.REDIS_PASSWORD, db=7).get_redis()

    @property
    @decorators.cached_method_result
    def redis_db6(self):
        return RedisManager(host=frame_config.REDIS_HOST, port=frame_config.REDIS_PORT, password=frame_config.REDIS_PASSWORD, db=6).get_redis()

    @property
    @decorators.cached_method_result
    def redis_db_frame(self):
        return RedisManager(host=frame_config.REDIS_HOST, port=frame_config.REDIS_PORT, password=frame_config.REDIS_PASSWORD, db=frame_config.REDIS_DB).get_redis()

    @property
    @decorators.cached_method_result
    def redis_db_frame_version3(self):
        return redis3.Redis(host=frame_config.REDIS_HOST, port=frame_config.REDIS_PORT, password=frame_config.REDIS_PASSWORD, db=frame_config.REDIS_DB,decode_responses=True)
