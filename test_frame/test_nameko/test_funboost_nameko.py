from eventlet import monkey_patch

monkey_patch()

from funboost.consumers.nameko_consumer import start_batch_nameko_service_in_new_process, start_batch_nameko_service_in_new_thread

from funboost.assist.user_custom_broker_register import register_nameko_broker
import time

from funboost import boost, ConcurrentModeEnum, BrokerEnum

'''
目前没有加到 funboost/factories/consumer_factory.py的 broker_kind__consumer_type_map 字典中，防止用户安装celery报错和funboost瘦身，
如果想要使用namelo作为funboost的消息中间件，需要先调用 register_nameko_broker() 函数，目的是把类注册到funboost框架中。看文档4.21自由扩展中间件文档。
'''
register_nameko_broker()


@boost('test_nameko_queue', broker_kind=BrokerEnum.NAMEKO, concurrent_mode=ConcurrentModeEnum.EVENTLET)
def f(a, b):
    print(a, b)
    time.sleep(1)
    return 'hi'


@boost('test_nameko_queue2', broker_kind=BrokerEnum.NAMEKO, concurrent_mode=ConcurrentModeEnum.EVENTLET)
def f2(x, y):
    print(f'x: {x}   y:{y}')
    time.sleep(2)
    return 'heelo'


if __name__ == '__main__':
    # 用户可以使用nameko的 ServiceContainer ,直接启动每个nameko的service类，语法和funboost使用其他中间件语法一样。
    f.consume()
    f2.consume()

    # 也可以批量启动，使用nameko的 ServiceRunner 批量启动多个 nameko的service类。这个函数专门为nameko 中间件而写的。
    start_batch_nameko_service_in_new_thread([f, f2])
