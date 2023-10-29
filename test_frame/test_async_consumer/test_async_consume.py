import time
import asyncio
from funboost import boost, BrokerEnum, ConcurrentModeEnum
from auto_run_on_remote import run_current_script_on_remote
# import uvloop
# uvloop.install()

# run_current_script_on_remote()
@boost('test_async_queue', concurrent_mode=ConcurrentModeEnum.THREADING, qps=0, broker_kind=BrokerEnum.REDIS, concurrent_num=60,log_level=20)
async def async_f(x):   # 调度异步消费函数
    # return

    # time.sleep(2)   # 不能搞同步time.sleep 2秒的代码，否则不管设置多大并发实际qps最大只能达到0.5
    # await asyncio.sleep(2)
    print(x)
    return x * 3


@boost('test_f_queue', concurrent_mode=ConcurrentModeEnum.SINGLE_THREAD, qps=0, broker_kind=BrokerEnum.MEMORY_QUEUE,log_level=20)
def f(y):  # 调度同步消费函数
    if y % 1000 == 0:
        print(y)
    # time.sleep(7)


if __name__ == '__main__':
    async_f.clear()
    f.clear()

    for i in range(800000):
        # async_f.push(i)
        f.push(i * 1)

    # async_f.consume()
    f.consume()
