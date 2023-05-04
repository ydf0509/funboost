import typing
from funboost.constant import BrokerEnum

from funboost.publishers.base_publisher import AbstractPublisher
from funboost.consumers.base_consumer import AbstractConsumer
from funboost.factories.broker_kind__publsiher_consumer_type_map import broker_kind__funboost_cls_map

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
        raise TypeError(f'publisher_class 必须是 AbstractPublisher 的子或孙类')
    if not issubclass(consumer_class, AbstractConsumer):
        raise TypeError(f'consumer_class 必须是 AbstractConsumer 的子或孙类')
    broker_kind__funboost_cls_map[broker_kind] = (publisher_class, consumer_class)
    consumer_class.BROKER_KIND = broker_kind


def register_kombu_broker():
    """
    直接导入kombu有的人的环境容易报错，有的人从来不使用kombu作为消息队列中间件免得报错，需要使用kombu作为消息队列的人,
    自己在 @boost,先调用 register_kombu_broker() 就可以使用了.如

    from funboost import BrokerEnum,boost
    from funboost.assist.user_custom_broker_register import register_kombu_broker

    register_kombu_broker()


    @boost('test_kombu',broker_kind=BrokerEnum.KOMBU)
    def f1(x,y):
        print(f'{x} + {y} = {x  + y}')


    if __name__ == '__main__':
        f1.push(1,2)
        f1.consume()
    """
    from funboost.consumers.kombu_consumer import KombuConsumer
    from funboost.publishers.kombu_publisher import KombuPublisher
    register_custom_broker(BrokerEnum.KOMBU, KombuPublisher, KombuConsumer)


def register_pulsar_broker():
    from funboost.consumers.pulsar_consumer import PulsarConsumer
    from funboost.publishers.pulsar_publisher import PulsarPublisher
    register_custom_broker(BrokerEnum.PULSAR, PulsarPublisher, PulsarConsumer)


def register_celery_broker():
    """
     如果有人想用celery作为funboost的消息队列中间件，先自己pip 安装celery包，然后调用这个函数，之后 boost装饰器就可以正常使用了。
    :return:
    """
    """
import time

from funboost import boost, BrokerEnum
from funboost.assist.user_custom_broker_register import register_celery_broker

register_celery_broker()


@boost('tets_funboost_celery_queue29a', broker_kind=BrokerEnum.CELERY, concurrent_num=10,
       broker_exclusive_config={'celery_app_config':
                                    {'task_default_rate_limit': '1/s', }}
       )
def fa(x, y):
    time.sleep(3)
    print(6666, x, y)


@boost('tets_funboost_celery_queue29b', broker_kind=BrokerEnum.CELERY, concurrent_num=10,
       broker_exclusive_config={'celery_app_config':
                                    {'task_default_rate_limit': '2/s', }}
       )
def fb(a, b):
    time.sleep(2)
    print(7777, a, b)


if __name__ == '__main__':
    for i in range(1000):
        fa.push(i, i + 1)
        fb.push(i, i * 2)

    fa.consume()
    fb.consume()
"""
    from funboost.consumers.celery_consumer import CeleryConsumer
    from funboost.publishers.celery_publisher import CeleryPublisher
    register_custom_broker(BrokerEnum.CELERY, CeleryPublisher, CeleryConsumer)


def register_nameko_broker():
    from funboost.consumers.nameko_consumer import NamekoConsumer
    from funboost.publishers.nameko_publisher import NamekoPublisher
    register_custom_broker(BrokerEnum.NAMEKO, NamekoPublisher, NamekoConsumer)
