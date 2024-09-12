# -*- coding: utf-8 -*-
import time
from funboost import BoosterParams, BrokerEnum

@BoosterParams(queue_name='test_rpc_queue_a1', is_using_rpc_mode=True, broker_kind=BrokerEnum.REDIS_ACK_ABLE, qps=2, max_retry_times=5)
def f1(x):
    time.sleep(5)
    async_result_list = [f2.push(x + i) for i in range(10)]
    for async_result in async_result_list:
        async_result.set_timeout(300)
        print(async_result.task_id, async_result.status_and_result, async_result.result)
    print('f2 10个任务都完成了，现在开始进行下一步，打印哈哈。')
    print('哈哈')


@BoosterParams(queue_name='test_rpc_queue_a2',
               is_using_rpc_mode=True,  # f2必须支持rpc，必须写is_using_rpc_mode=True
               broker_kind=BrokerEnum.REDIS_ACK_ABLE,
               qps=5, max_retry_times=5)
def f2(y):
    time.sleep(10)
    return y * 10


if __name__ == '__main__':
    f1.consume()
    f2.consume()

    for j in range(20):
        f1.push(j)
