from concurrent.futures import ThreadPoolExecutor
import sys

import time
import random
from funboost import boost, BrokerEnum, ConcurrentModeEnum, BoosterParams,ctrl_c_recv


@boost(BoosterParams(
    queue_name='test_queue_socket', broker_kind=BrokerEnum.HTTP,
    broker_exclusive_config={'host': '127.0.0.1', 'port': 7100},
    # qps=0, 
    is_print_detail_exception=True, max_retry_times=3, log_level=20,
))
def f(x):
    # time.sleep(7)
    # if x % 10 == 0 and random.random() < 0.2:
    #     raise ValueError('测试函数出错')
    # if x % 1000 == 0:
    #     print(x)
    print(x)
    return x * 10


if __name__ == '__main__':
    f.consume()
    time.sleep(10)
    start_time = time.time()
    for i in range(1000):
        # f.push(i)
        rpc_data_obj = f.publisher.sync_call({'x': i},is_return_rpc_data_obj=True)
        print('result is :', rpc_data_obj.result)

    # with ThreadPoolExecutor(max_workers=50) as pool:
    #     for i in range(10000):
    #         pool.submit(f.push, i)
    print('cost time is :', time.time() - start_time)
    ctrl_c_recv()



