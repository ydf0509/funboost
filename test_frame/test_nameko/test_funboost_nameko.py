from eventlet import monkey_patch

monkey_patch()

from funboost.consumers.nameko_consumer import batch_start_nameko_consumers


import time

from funboost import boost, ConcurrentModeEnum, BrokerEnum



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
    batch_start_nameko_consumers([f, f2])
