import time
from funboost import boost, BrokerEnum


@boost('test1', broker_kind=BrokerEnum.MEMORY_QUEUE, concurrent_num=5)
def f(x, y):
    print(f'{x} + {y} = {x + y}')
    time.sleep(10)


if __name__ == '__main__':
    f.consume()
    for i in range(100):
        f.push(i, i * 2)
