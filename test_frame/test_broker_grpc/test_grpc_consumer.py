import time
import json
from funboost import boost, BrokerEnum, BoosterParams, FunctionResultStatus,AsyncResult


@boost(BoosterParams(
    queue_name='test_grpc_queue', broker_kind=BrokerEnum.GRPC,
    broker_exclusive_config={'port': 55051, 'host': '127.0.0.1'},
    is_using_rpc_mode=True,  # brpc作为broker时候,is_using_rpc_mode可以为False,使用 $booster.publisher.sync_call ,则不依赖redis实现rpc
))
def f(x, y):
    time.sleep(2)
    print(f'x: {x}, y: {y}')
    return x + y


@boost(BoosterParams(
    queue_name='test_grpc_queue2', broker_kind=BrokerEnum.GRPC,
    broker_exclusive_config={'port': 55052, 'host': '127.0.0.1'},
    rpc_timeout=6,
    is_using_rpc_mode=False,  # brpc作为broker时候,is_using_rpc_mode可以为False,如果使用 $booster.publisher.sync_call ,则不依赖redis实现rpc
    concurrent_num=500,
))
def f2(a, b):
    time.sleep(5)
    print(f'a: {a}, b: {b}')
    return a * b


if __name__ == '__main__':
    f.consume()
    f2.consume()

    for i in range(100):
       

        """
        sync_call 是会进入阻塞直到返回结果,无论你是否进一步执行  rpc_data1.result 都会阻塞
        """
        rpc_data1: FunctionResultStatus = f.publisher.sync_call({'x': i, 'y': i * 2})
        print('grpc f result is :', rpc_data1.result)

        """
        任然可以使用 booster.push,但是AsyncResult获取结果需要redis作为rpc,
        如果不进一步async_result.result来获取结果,则f.push不会阻塞代码
        """
        async_result :AsyncResult = f.push(i, i * 2)
        print("result from redis:",async_result.result)

        rpc_data2 :FunctionResultStatus = f2.publisher.sync_call({'a': i, 'b': i * 2})
        print('grpc f2 result is :', rpc_data2.result)
