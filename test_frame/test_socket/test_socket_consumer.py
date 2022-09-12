import time
import random
from funboost import boost, BrokerEnum


@boost('127.0.0.1:6668', broker_kind=BrokerEnum.UDP, qps=0.5, is_print_detail_exception=True, max_retry_times=3)
def f(x):
    # time.sleep(7)
    if x % 10 == 0 and random.random() < 0.2:
        raise ValueError('测试函数出错')
    print(x)
    return x * 10


if __name__ == '__main__':
    f.consume()
    # for i in range(10):
    #     f.push(i)
