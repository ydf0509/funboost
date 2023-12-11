import time
import deprecated
# from inspect import ismethod, isclass, formatargspec
from funboost import boost,BrokerEnum


@boost('test_rpc_hello',is_using_rpc_mode=True,broker_kind=BrokerEnum.REDIS_ACK_ABLE)
def fun(x):
    time.sleep(2)
    print(x)
    return f'hello {x} '


if __name__ == '__main__':
    fun.consume()
    async_result = fun.push(666)
    print(async_result.result)