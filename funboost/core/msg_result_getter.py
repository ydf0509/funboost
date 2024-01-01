import asyncio
import time

import typing
import json

from funboost.utils.mongo_util import MongoMixin

from funboost.concurrent_pool import CustomThreadPoolExecutor
from funboost.concurrent_pool.flexible_thread_pool import FlexibleThreadPoolMinWorkers0
from funboost.utils.redis_manager import RedisMixin
from funboost.utils.redis_manager import AioRedisMixin


class HasNotAsyncResult(Exception):
    pass


NO_RESULT = 'no_result'


class AsyncResult(RedisMixin):
    callback_run_executor = FlexibleThreadPoolMinWorkers0(200)

    def __init__(self, task_id, timeout=120):
        self.task_id = task_id
        self.timeout = timeout
        self._has_pop = False
        self._status_and_result = None

    def set_timeout(self, timeout=60):
        self.timeout = timeout
        return self

    def is_pending(self):
        return not self.redis_db_filter_and_rpc_result.exists(self.task_id)

    @property
    def status_and_result(self):
        if not self._has_pop:
            redis_value = self.redis_db_filter_and_rpc_result.blpop(self.task_id, self.timeout)
            self._has_pop = True
            if redis_value is not None:
                status_and_result_str = redis_value[1]
                self._status_and_result = json.loads(status_and_result_str)
                self.redis_db_filter_and_rpc_result.lpush(self.task_id, status_and_result_str)
                self.redis_db_filter_and_rpc_result.expire(self.task_id, self._status_and_result['rpc_result_expire_seconds'])
                return self._status_and_result
            return None
        return self._status_and_result

    def get(self):
        # print(self.status_and_result)
        if self.status_and_result is not None:
            return self.status_and_result['result']
        else:
            raise HasNotAsyncResult

    @property
    def result(self):
        return self.get()

    def is_success(self):
        if self.status_and_result is not None:
            return self.status_and_result['success']
        else:
            raise HasNotAsyncResult

    def _run_callback_func(self, callback_func):
        callback_func(self.status_and_result)

    def set_callback(self, callback_func: typing.Callable):
        """
        :param callback_func: 函数结果回调函数，使回调函数自动在线程池中并发运行。
        :return:
        """

        ''' 用法例如
        from test_frame.test_rpc.test_consume import add
        def show_result(status_and_result: dict):
            """
            :param status_and_result: 一个字典包括了函数入参、函数结果、函数是否运行成功、函数运行异常类型
            """
            print(status_and_result)

        for i in range(100):
            async_result = add.push(i, i * 2)
            # print(async_result.result)   # 执行 .result是获取函数的运行结果，会阻塞当前发布消息的线程直到函数运行完成。
            async_result.set_callback(show_result) # 使用回调函数在线程池中并发的运行函数结果
        '''
        self.callback_run_executor.submit(self._run_callback_func, callback_func)


class AioAsyncResult(AioRedisMixin):
    """ 这个是可以用于asyncio的语法环境中。"""
    '''
    用法例子
import asyncio

from funboost import AioAsyncResult
from test_frame.test_rpc.test_consume import add


async def process_result(status_and_result: dict):
    """
    :param status_and_result: 一个字典包括了函数入参、函数结果、函数是否运行成功、函数运行异常类型
    """
    await asyncio.sleep(1)
    print(status_and_result)


async def test_get_result(i):
    async_result = add.push(i, i * 2)
    aio_async_result = AioAsyncResult(task_id=async_result.task_id) # 这里要使用asyncio语法的类，更方便的配合asyncio异步编程生态
    print(await aio_async_result.result) # 注意这里有个await，如果不await就是打印一个协程对象，不会得到结果。这是asyncio的基本语法，需要用户精通asyncio。
    print(await aio_async_result.status_and_result)
    await aio_async_result.set_callback(process_result)  #  你也可以编排任务到loop中


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    for j in range(100):
        loop.create_task(test_get_result(j))
    loop.run_forever()

    '''

    def __init__(self, task_id, timeout=120):
        self.task_id = task_id
        self.timeout = timeout
        self._has_pop = False
        self._status_and_result = None

    def set_timeout(self, timeout=60):
        self.timeout = timeout
        return self

    async def is_pending(self):
        is_exists = await self.aioredis_db_filter_and_rpc_result.exists(self.task_id)
        return not is_exists

    @property
    async def status_and_result(self):
        if not self._has_pop:
            t1 = time.time()
            redis_value = await self.aioredis_db_filter_and_rpc_result.blpop(self.task_id, self.timeout)
            self._has_pop = True
            if redis_value is not None:
                status_and_result_str = redis_value[1]
                self._status_and_result = json.loads(status_and_result_str)
                await self.aioredis_db_filter_and_rpc_result.lpush(self.task_id, status_and_result_str)
                await self.aioredis_db_filter_and_rpc_result.expire(self.task_id, self._status_and_result['rpc_result_expire_seconds'])
                return self._status_and_result
            return None
        return self._status_and_result

    async def get(self):
        # print(self.status_and_result)
        if (await self.status_and_result) is not None:
            return (await self.status_and_result)['result']
        else:
            raise HasNotAsyncResult

    @property
    async def result(self):
        return await self.get()

    async def is_success(self):
        if (await self.status_and_result) is not None:
            return (await self.status_and_result)['success']
        else:
            raise HasNotAsyncResult

    async def _run_callback_func(self, callback_func):
        await callback_func(await self.status_and_result)

    async def set_callback(self, aio_callback_func: typing.Callable):
        asyncio.create_task(self._run_callback_func(callback_func=aio_callback_func))


class ResultFromMongo(MongoMixin):
    """
    以非阻塞等待的方式从funboost的状态结果持久化的mongodb数据库根据taskid获取结果

    async_result = add.push(i, i * 2)
    task_id=async_result.task_id
    print(ResultFromMongo(task_id).get_status_and_result())


    print(ResultFromMongo('test_queue77h6_result:764a1ba2-14eb-49e2-9209-ac83fc5db1e8').get_status_and_result())
    print(ResultFromMongo('test_queue77h6_result:5cdb4386-44cc-452f-97f4-9e5d2882a7c1').get_result())
    """

    def __init__(self, task_id: str, ):
        self.task_id = task_id
        self.col_name = task_id.split('_result:')[0]
        self.mongo_row = None
        self._has_query = False

    def query_result(self):
        col = self.get_mongo_collection('task_status', self.col_name)
        self.mongo_row = col.find_one({'_id': self.task_id})
        self._has_query = True

    def get_status_and_result(self):
        self.query_result()
        return self.mongo_row or NO_RESULT

    def get_result(self):
        """以非阻塞等待的方式从funboost的状态结果持久化的mongodb数据库根据taskid获取结果"""
        self.query_result()
        return (self.mongo_row or {}).get('result', NO_RESULT)


if __name__ == '__main__':
    print(ResultFromMongo('test_queue77h6_result:764a1ba2-14eb-49e2-9209-ac83fc5db1e8').get_status_and_result())
    print(ResultFromMongo('test_queue77h6_result:5cdb4386-44cc-452f-97f4-9e5d2882a7c1').get_result())
