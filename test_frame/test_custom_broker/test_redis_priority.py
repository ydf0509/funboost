import random

from funboost import register_custom_broker, boost, PriorityConsumingControlConfig
from funboost.consumers.redis_consumer_priority import RedisPriorityConsumer
from funboost.publishers.redis_publisher_priority import RedisPriorityPublisher

BROKER_KIND_REDIS_PRIORITY = 111
register_custom_broker(BROKER_KIND_REDIS_PRIORITY, RedisPriorityPublisher, RedisPriorityConsumer)  # 核心，这就是将自己写的类注册到框架中，框架可以自动使用用户的类，这样用户无需修改框架的源代码了。


@boost('test_redis_priority_queue3', broker_kind=BROKER_KIND_REDIS_PRIORITY, qps=5,concurrent_num=2,broker_exclusive_config={'x-max-priority':4})
def f(x):
    print(x)


if __name__ == '__main__':
    f.clear()
    print(f.get_message_count())

    for i in range(1000):
        # test_fun.push(i)
        # test_fun2.push(i)
        randx = random.randint(1, 6)
        if randx > 4:
            randx = None
        print(randx)
        f.publish({'x': randx}, priority_control_config=PriorityConsumingControlConfig(other_extra_params={'priroty': randx}))
    print(f.get_message_count())

    f.consume()