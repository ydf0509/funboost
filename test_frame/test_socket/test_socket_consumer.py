import time
import random
from funboost import boost, BrokerEnum, ConcurrentModeEnum


@boost('10.0.126.147:5691', broker_kind=BrokerEnum.TCP, qps=0.5, is_print_detail_exception=True, max_retry_times=3)
def f(x):
    # time.sleep(7)
    if x % 10 == 0 and random.random() < 0.2:
        raise ValueError('测试函数出错')
    print(x)
    return x * 10


if __name__ == '__main__':
    f.consume()
    for i in range(10):
        f.push(i)
