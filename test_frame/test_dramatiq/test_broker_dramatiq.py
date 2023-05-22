import time

from funboost import boost, BrokerEnum

from funboost.assist.dramatiq_helper import DramatiqHelper


@boost('test_dramatiq_q1', broker_kind=BrokerEnum.DRAMATIQ, function_timeout=10)
def f1(x):
    time.sleep(1)
    print('f1', x)


@boost('test_dramatiq_q2', broker_kind=BrokerEnum.DRAMATIQ, function_timeout=3)
def f2(y):
    time.sleep(2)
    print('f2', y)


if __name__ == '__main__':
    f1.consume()  # 登记要启动消费的queue
    f2.consume()  # 登记要启动消费的queue
    for i in range(100):
        f1.push(i)
        f2.push(i * 2)
    DramatiqHelper.realy_start_dramatiq_worker()  # 真正启动dramatiq消费
