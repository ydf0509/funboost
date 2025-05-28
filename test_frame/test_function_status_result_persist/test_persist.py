import asyncio

from funboost import boost, FunctionResultStatusPersistanceConfig, BoosterParams,BrokerEnum,ctrl_c_recv,ConcurrentModeEnum
from funboost.function_result_web.app import start_funboost_web_manager
import time
import random


class MyBoosterParams(BoosterParams):
    function_result_status_persistance_conf:FunctionResultStatusPersistanceConfig = FunctionResultStatusPersistanceConfig(
        is_save_status=True, is_save_result=True, expire_seconds=7 * 24 * 3600)
    is_send_consumer_hearbeat_to_redis:bool = True
    broker_exclusive_config = {'pull_msg_batch_size':1}


@boost(MyBoosterParams(queue_name='queue_test_g01t',broker_kind=BrokerEnum.REDIS,qps=1,))
def my_consuming_function(x):
    time.sleep(5)
    print(f'hi: {x}')
    if random.random() > 0.9:
        raise ValueError('f error')
    return x + 1

@boost(MyBoosterParams(queue_name='queue_test_g02t',broker_kind=BrokerEnum.RABBITMQ_AMQPSTORM,qps=0.5,
max_retry_times=0,))
def f2(x,y):
    time.sleep(2)
    print(f'hello: {x} {y}')
    if random.random() > 0.5:
        raise ValueError('f2 error')
    return x + y

@boost(MyBoosterParams(queue_name='queue_test_g03t',broker_kind=BrokerEnum.REDIS,qps=0.5,
max_retry_times=0,concurrent_mode=ConcurrentModeEnum.ASYNC))
async def aio_f3(x):
    await asyncio.sleep(3)
    print(f'f3aa: {x}')
    if random.random() > 0.5:
        raise ValueError('f3 error')
    return x + 1

@boost(MyBoosterParams(queue_name='queue_test_g04t',broker_kind=BrokerEnum.REDIS,qps=1,))
def f4(x):
    time.sleep(5)
    print(f'f4: {x}')
    if random.random() > 0.9:
        raise ValueError('f4 error')
    return x + 1

if __name__ == '__main__':
    start_funboost_web_manager(port=27018)  # 也可以在python代码中启动web,启动 funboost web manager funboost队列管理界面

    f2.clear()
    # f.multi_process_consume(3)
    # f2.multi_process_consume(4)
    my_consuming_function.consume()
    f2.multi_process_consume(2)
    aio_f3.consume()
    # f4.consume()
    # for i in range(0, 1000):
    #     f.push(i)
    #     f2.push(i,i*2)
    #     aio_f3.push(i)
    #     time.sleep(1)
    ctrl_c_recv()
    

    
