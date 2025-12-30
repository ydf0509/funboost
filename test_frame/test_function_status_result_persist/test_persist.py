import asyncio

from funboost import boost, FunctionResultStatusPersistanceConfig, BoosterParams,BrokerEnum,ctrl_c_recv,ConcurrentModeEnum
from funboost.funboost_web_manager.app import start_funboost_web_manager
import time
import random


class MyBoosterParams(BoosterParams):
    function_result_status_persistance_conf:FunctionResultStatusPersistanceConfig = FunctionResultStatusPersistanceConfig(
        is_save_status=True, is_save_result=True, expire_seconds=17 * 24 * 3600,table_name='test_project1_use_one_table')
    is_send_consumer_heartbeat_to_redis:bool = True
    broker_exclusive_config :dict= {'pull_msg_batch_size':1}
    project_name:str = 'test_project1'
    is_using_rpc_mode:bool = True
    # xxxx:int=5


@boost(MyBoosterParams(queue_name='queue_test_g01t',broker_kind=BrokerEnum.REDIS,qps=1,))
def my_consuming_function(x):
    time.sleep(5)
    print(f'hi: {x}')
    if random.random() > 0.6:
        raise ValueError('f error 很长的报错，看看显示咋样，啦啦啦啦啦啦啦啦啦啦啦啦啊啊啊啊')
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
max_retry_times=1,concurrent_mode=ConcurrentModeEnum.ASYNC))
async def aio_f3(x):
    await asyncio.sleep(3)
    print(f'aio_f3: {x}')
    if random.random() > 0.5:
        raise ValueError('aio_f3 error')
    return x + 1

@boost(MyBoosterParams(queue_name='queue_test_g04t',broker_kind=BrokerEnum.REDIS,qps=1,))
def f4(x):
    time.sleep(5)
    print(f'f4: {x}')
    if random.random() > 0.9:
        raise ValueError('f4 error')
    return x + 1


@boost(MyBoosterParams(
        queue_name='queue_test_g05t',
        broker_kind=BrokerEnum.RABBITMQ_AMQPSTORM,qps=10,
        broker_exclusive_config={'x-max-priority':5},
        ))
def f5(x):
    time.sleep(1)
    print(f'f5: {x}')
    if random.random() > 0.9:
        raise ValueError('f5 error')
    return x + 1

@boost(MyBoosterParams(queue_name='queue_test_g06t',broker_kind=BrokerEnum.REDIS,qps=3,
max_retry_times=1,concurrent_mode=ConcurrentModeEnum.ASYNC))
async def aio_f6(x):
    await asyncio.sleep(3)
    print(f'aio_f6: {x}')
    if random.random() > 0.5:
        raise ValueError('aio_f6 error')
    return x + 1

if __name__ == '__main__':
    start_funboost_web_manager(port=27018)  # 也可以在python代码中启动web,启动 funboost web manager funboost队列管理界面

    f2.clear()

    f2.multi_process_consume(4)
    my_consuming_function.consume()
    aio_f3.consume()
    f4.consume()
    f5.consume()
    aio_f6.consume()
    for i in range(0, 1000):
        my_consuming_function.push(i)
        f2.push(i,i*2)
        aio_f3.push(i)
        aio_f6.push(i)
        time.sleep(1)
    ctrl_c_recv()
    

    

