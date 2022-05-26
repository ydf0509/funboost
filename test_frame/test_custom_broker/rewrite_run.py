from funboost import register_custom_broker
from funboost import boost, FunctionResultStatus
from funboost.consumers.redis_consumer_simple import RedisConsumer as SimpleRedisConsumer
from funboost.publishers.redis_publisher_simple import RedisPublisher as SimpleRedisPublisher

"""
演示重写最关键的 _run 方法，_run里面可以控制函数运行逻辑，_run方法这是消费者中最关键的一个方法。

"""


class MyRedisPublisher(SimpleRedisPublisher):
    pass


class MyRedisConsumer(SimpleRedisConsumer):
    def _run(self, kw: dict, ):
        self.logger.warning(f'kw: {kw}')
        print(self._get_priority_conf)
        super()._run(kw)   # 如果更精细化控制可以把AbstractConsumer类的 _run方法的代码全部复制到这里，直接修改里面的代码逻辑


BROKER_KIND_MY_REEDIS = 104
register_custom_broker(BROKER_KIND_MY_REEDIS, MyRedisPublisher, MyRedisConsumer)  # 核心，这就是将自己写的类注册到框架中，框架可以自动使用用户的类，这样用户无需修改框架的源代码了。


@boost('test_my_redis_queue', broker_kind=BROKER_KIND_MY_REEDIS, qps=1, )
def f(x):
    print(x * 10)

if __name__ == '__main__':
    for i in range(50):
        f.push(i)
    print(f.publisher.get_message_count())
    f.consume()
