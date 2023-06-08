import time

from funboost import register_custom_broker, boost
from funboost.consumers.rq_consumer import RqConsumer
from funboost.publishers.rq_publisher import RqPublisher
from funboost.assist.rq_helper import RqHelper

register_custom_broker(204, RqPublisher, RqConsumer)


@boost('test_rq_queue1a', broker_kind=204)
def f(x, y):
    time.sleep(0.02)
    print(f'x:{x},y:{y}')


@boost('test_rq_queue2a', broker_kind=204)
def f2(a, b):
    time.sleep(0.03)
    print(f'a:{a},b:{b}')


if __name__ == '__main__':
    pass
    for i in range(1000):
        f.push(i, i * 2)
        f2.push(i, i * 10)
    f.consume()
    f2.consume()
    RqHelper.realy_start_rq_worker()
