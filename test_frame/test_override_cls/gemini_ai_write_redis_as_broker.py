import threading
import json
import time
import redis
from collections import defaultdict
from funboost import boost, BrokerEnum, BoosterParams, EmptyConsumer, EmptyPublisher,funboost_config_deafult


'''
使用 redis 作为 消息队列的中间件 实现, 通过指定 consumer_override_cls 和 publisher_override_cls 为用户自定义的类来实现新增消息队列种类。
'''


class MyRedisConsumer(EmptyConsumer):
    def custom_init(self):
        print(funboost_config_deafult.BrokerConnConfig.REDIS_URL)
        self.redis_client = redis.from_url(funboost_config_deafult.BrokerConnConfig.REDIS_URL)

    def _shedual_task(self):
        while True:
            try:
                _, msg_bytes = self.redis_client.brpop(self.queue_name)
                msg = msg_bytes.decode('utf-8')
                self._submit_task({'body': msg})
            except redis.exceptions.ConnectionError as e:
                print(f"Redis connection error: {e}")
                time.sleep(5)  # 发生连接错误时等待一段时间后重试
            except Exception as e:
                print(f"Error during message consumption: {e}")
                time.sleep(1)

    def _confirm_consume(self, kw):
        """ 这里是演示,所以搞简单一点,不实现确认消费 """
        pass

    def _requeue(self, kw):
        self.redis_client.lpush(self.queue_name, kw['body'])

class MyRedisPublisher(EmptyPublisher):
    def custom_init(self):
        self.redis_client = redis.from_url(funboost_config_deafult.BrokerConnConfig.REDIS_URL)

    def concrete_realization_of_publish(self, msg: str):
        self.redis_client.lpush(self.queue_name, msg)

    def clear(self):
        self.redis_client.delete(self.queue_name)

    def get_message_count(self):
        return self.redis_client.llen(self.queue_name)

    def close(self):
        self.redis_client.connection_pool.disconnect()

'''
完全重新自定义增加中间件时候,broker_kind 建议指定为 BrokerEnum.EMPTY
'''

@boost(BoosterParams(queue_name='test_define_redis_queue',
                     broker_kind=BrokerEnum.REDIS,  # 使用 redis 作为中间件
                     concurrent_num=1, consumer_override_cls=MyRedisConsumer, publisher_override_cls=MyRedisPublisher,
                     is_show_message_get_from_broker=True))
def cost_long_time_fun(x):
    print(f'start {x}')
    time.sleep(2)
    print(f'end {x}')

if __name__ == '__main__':
    for i in range(10):
        cost_long_time_fun.push(i)
    cost_long_time_fun.consume()
