"""

这是一个错误的调用 async 协程的方式，协程成了废物。包括celery，如果为了调用async def的函数，只要这么玩，异步就成了废物。
"""
import asyncio
from funboost import boost,BrokerEnum,ConcurrentModeEnum

async def f(x,):
    print(id(asyncio.get_event_loop()))   # 从这里可以看到，打印出来的loop每次都是不同的，不是同一个循环
    await  asyncio.sleep(4)
    return x + 5

##为了兼容调用asyncio， 需要多加一个函数， 真的多此一举。 正确方法是直接把装饰器加在上面那个async def f上面，然后设置concurrent_mode=ConcurrentModeEnum.ASYNC
@boost('test_asyncio_error_queue', broker_kind=BrokerEnum.LOCAL_PYTHON_QUEUE, )
def my_task(x):
    print(asyncio.new_event_loop().run_until_complete(f(x,)))


if __name__ == '__main__':
    for i in range(5):
        my_task.push(i)
    my_task.consume()