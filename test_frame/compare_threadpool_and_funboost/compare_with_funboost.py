import time

from funboost import boost, BrokerEnum, ConcurrentModeEnum


@boost('test_queue', broker_kind=BrokerEnum.MEMORY_QUEUE, concurrent_mode=ConcurrentModeEnum.THREADING, concurrent_num=10)
def f(x):
    time.sleep(3)
    print(x)


if __name__ == '__main__':
    for i in range(100):
        f.push(i)
    f.consume()
