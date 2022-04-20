import typing
from funboost.publishers.base_publisher import AbstractPublisher
from funboost.consumers.base_consumer import AbstractConsumer

from funboost.factories import publisher_factotry
from funboost.factories import consumer_factory

"""
这个有两个用途
1 是给用户提供一种方式新增消息队列中间件种类，(框架支持了所有知名类型消息队列中间件或模拟中间件，这个用途的可能性比较少)
2 可以对已有中间件类型的消费者 发布者类继承重写符合自己意愿的，这样就不需要修改项目的源代码了，这种用法非常的强大自由，可以满足一切用户的特殊定制想法。
  因为用户可以使用到self成员变量和通过重写使用其中的函数内部局部变量，能够做到更精细化的特殊定制。这个用途很强大自由灵活定制。

test_frame/test_custom_broker/test_custom_list_as_broker.py 中有例子，使用list作为消息队列。
test_frame/test_custom_broker/test_custom_deque_as_broker.py 中有例子，使用deque作为消息队列。
test_frame/test_custom_broker/test_custom_redis_consume_latest_publish_msg_broker.py 中有例子，使用redis实现先进后出 后进先出，总是优先消费最晚发布的消息的例子
"""


def register_custom_broker(broker_kind: int, publisher_class: typing.Type[AbstractPublisher], consumer_class: typing.Type[AbstractConsumer]):
    if not issubclass(publisher_class, AbstractPublisher):
        raise TypeError(f'publisher_class 必须是 AbstractPublisher 的子孙类')
    if not issubclass(consumer_class, AbstractConsumer):
        raise TypeError(f'consumer_class 必须是 AbstractConsumer 的子孙类')
    publisher_factotry.broker_kind__publisher_type_map[broker_kind] = publisher_class
    consumer_factory.broker_kind__consumer_type_map[broker_kind] = consumer_class
    consumer_class.BROKER_KIND = broker_kind
