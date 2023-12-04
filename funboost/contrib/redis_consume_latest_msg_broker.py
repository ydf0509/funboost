from funboost import register_custom_broker
from funboost import boost, FunctionResultStatus,BoosterParams
from funboost.consumers.redis_consumer_simple import RedisConsumer
from funboost.publishers.redis_publisher_simple import RedisPublisher

"""
此文件是演示添加自定义类型的中间件,演示怎么使用redis 实现先进后出 后进先出的队列，就是消费总是拉取最晚发布的消息，而不是优先消费最早发布的消息
lpush + lpop 或者 rpush + rpop 就会消费最新发布的消息，如果是 lpush + rpop 或者 rpush + lpop 则会先消费最早发布的消息(框架内置的目前就是消费最早发布的消息)。

此种方式也可以在子类中重写来更改 AbstractConsumer 基类的逻辑,例如你想在任务执行完成后把结果插入到mysql或者做更精细化的定制流程，可以不使用原来推荐的装饰器叠加方式
而是在类中直接重写方法

"""


class RedisConsumeLatestPublisher(RedisPublisher):
    def concrete_realization_of_publish(self, msg):
        self.redis_db_frame.lpush(self._queue_name, msg)


class RedisConsumeLatestConsumer(RedisConsumer):
    pass


BROKER_KIND_REDIS_CONSUME_LATEST = 105
register_custom_broker(BROKER_KIND_REDIS_CONSUME_LATEST, RedisConsumeLatestPublisher, RedisConsumeLatestConsumer)  # 核心，这就是将自己写的类注册到框架中，框架可以自动使用用户的类，这样用户无需修改框架的源代码了。


if __name__ == '__main__':
    @boost(boost_params=BoosterParams(queue_name='test_list_queue2', broker_kind=BROKER_KIND_REDIS_CONSUME_LATEST, qps=10, ))
    def f(x):
        print(x * 10)

    f.clear()
    for i in range(50):
        f.push(i)
    print(f.publisher.get_message_count())
    f.consume()  # 从可以看到事从最后发布的消息开始消费。
