
from auto_run_on_remote import run_current_script_on_remote
run_current_script_on_remote()

import asyncio

from funboost import AioAsyncResult,TaskOptions
from test_frame.test_rpc.test_consume import add


async def process_result(status_and_result: dict):
    """
    :param status_and_result: 一个字典包括了函数入参、函数结果、函数是否运行成功、函数运行异常类型
    """
    await asyncio.sleep(1)
    print(status_and_result)


async def test_get_result(i):
    add.publish({"a":1,"b":2},task_id=100005,task_options=TaskOptions(is_using_rpc_mode=True))
    async_result = add.push(i, i * 2)
    aio_async_result = AioAsyncResult(task_id=async_result.task_id) # 这里要使用asyncio语法的类，更方便的配合asyncio异步编程生态
    print(await aio_async_result.result) # 注意这里有个await，如果不await就是打印一个协程对象，不会得到结果。这是asyncio的基本语法，需要用户精通asyncio。
    print(await aio_async_result.status_and_result)
    # await aio_async_result.set_callback(process_result)  #  你也可以编排任务到loop中


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    for j in range(100):
        loop.create_task(test_get_result(j))
    loop.run_forever()