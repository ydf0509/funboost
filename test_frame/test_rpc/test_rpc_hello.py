import time
import deprecated
# from inspect import ismethod, isclass, formatargspec
from funboost import boost, BrokerEnum, BoosterParamsComplete, AsyncResult
from funboost.concurrent_pool.bounded_threadpoolexcutor import BoundedThreadPoolExecutor


@boost(BoosterParamsComplete(queue_name='test_rpc_hello',is_using_rpc_mode=True,broker_kind=BrokerEnum.REDIS_ACK_ABLE))
def fun(x):
    time.sleep(2)
    print(x)
    return f'hello {x} '


def show_result(status_and_result: dict):
    """
    :param status_and_result: 一个字典包括了函数入参、函数结果、函数是否运行成功、函数运行异常类型
    """
    print(status_and_result)


thread_pool = BoundedThreadPoolExecutor(200)

def wait_msg_result(async_result:AsyncResult):
    print(async_result.status_and_result)

if __name__ == '__main__':
    fun.consume()

    for i in range(100):
        async_result = fun.push(i)
        print(async_result.result) # print(async_result.get()) 用法相等

        async_result.set_callback(show_result) # thread_pool.submit(wait_msg_result,async_result) 等效