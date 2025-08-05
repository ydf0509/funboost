

import time

from funboost import boost, BrokerEnum, BoosterParams


@boost(BoosterParams(
    queue_name='test_http_queue', broker_kind=BrokerEnum.ZEROMQ,
    broker_exclusive_config={'port':17102},
))
def f(x):
    time.sleep(2)
    print(x)


if __name__ == '__main__':
    f.consume()
    for i in range(100):
        f.push(i)
