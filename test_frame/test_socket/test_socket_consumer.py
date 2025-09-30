from concurrent.futures import ThreadPoolExecutor
import sys

import time
import random
from funboost import boost, BrokerEnum, ConcurrentModeEnum, BoosterParams,ctrl_c_recv
from funboost.core.msg_result_getter import AsyncResult


@boost(BoosterParams(
    queue_name='test_queue_socket', broker_kind=BrokerEnum.HTTP,
    broker_exclusive_config={'host': '127.0.0.1', 'port': 7100},
    # qps=0, 
    concurrent_num=100,
    is_print_detail_exception=True, max_retry_times=3, log_level=20,
))
def f(x):
    print(x)
    return x * 10


if __name__ == '__main__':
    f.consume()
    time.sleep(10)
    start_time = time.time()
    for i in range(1000):
        async_result: AsyncResult = f.push(i)
        # print('async_result is :', async_result.result) # 会阻塞,如果不运行 async_result.result,f.push不会阻塞
        # rpc_data_obj = f.publisher.sync_call({'x': i},is_return_rpc_data_obj=True) # 已经阻塞,无论是否执行下面的rpc_data_obj.result
        # print('result is :', rpc_data_obj.result)

    # with ThreadPoolExecutor(max_workers=50) as pool:
    #     for i in range(1000):
    #         pool.submit(f.push, i)
    print('cost time is :', time.time() - start_time)
    ctrl_c_recv()

    

