"""
此脚本演示, funboost的子线程的loop中怎么操作aiomysql 连接池.

演示了2种方式使用aiomysql连接池
方式一:
async_aiomysql_f1 使用主线程的连接池,.
核心灵魂代码是 async_aiomysql_f1 的装饰器需要传参specify_async_loop=主线程loop
如果 async_aiomysql_f1 不指定specify_async_loop,就会出现经典报错 attached to a different loop ,
子线程的loop去操作主线程loop的连接池,这是大错特错的.

有的人压根不懂主线程loop和子线程loop,还非要装逼使用asyncio编程生态,
不精通asyncio编程生态的人应该老老实实使用同步多线程编程生态,简单多了.
因为funboost的线程池 FlexibleThreadPool能自动扩缩,
能自动缩容是吊打内置线程池 concurrent.futures.threadpoolexecutor的神级别操作,
FlexibleThreadPool 去掉了实现futures特性,精简了代码, 性能比官方内置线程池提高了250%


方式2:
async_aiomysql_f2_use_thread_local_aio_mysql_pool 使用 thread local 级别的全局变量连接池
这样子线程的loop避免了操作主线程loop的aiomysql连接池, 不会出现张冠李戴  attached to a different loop
"""
import threading

from funboost import boost, BrokerEnum, ConcurrentModeEnum, ctrl_c_recv, BoosterParams
import asyncio
import  time
import aiomysql


loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop) # 这是重点

DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': '123456',
    'db': 'testdb',
    'charset': 'utf8mb4',
    'autocommit': True
}

g_aiomysql_pool : aiomysql.Pool
async def create_pool():
    pool = await aiomysql.create_pool(**DB_CONFIG, minsize=1, maxsize=10,) # 这些是重点.
    global g_aiomysql_pool
    g_aiomysql_pool = pool
    return pool



# 如果 async_aiomysql_f1 不指定specify_async_loop,就会出现经典报错 attached to a different loop ,子线程的loop去操作主线程loop的连接池
r"""
Traceback (most recent call last):
  File "D:\codes\funboost\test_frame\test_async_consumer\test_child_thread_loop_aiomysql_pool.py", line 46, in async_aiomysql_f1
    await cur.execute("SELECT now()")
  File "D:\ProgramData\Miniconda3\envs\py39b\lib\site-packages\aiomysql\cursors.py", line 239, in execute
    await self._query(query)
  File "D:\ProgramData\Miniconda3\envs\py39b\lib\site-packages\aiomysql\cursors.py", line 457, in _query
    await conn.query(q)
  File "D:\ProgramData\Miniconda3\envs\py39b\lib\site-packages\aiomysql\connection.py", line 469, in query
    await self._read_query_result(unbuffered=unbuffered)
  File "D:\ProgramData\Miniconda3\envs\py39b\lib\site-packages\aiomysql\connection.py", line 683, in _read_query_result
    await result.read()
  File "D:\ProgramData\Miniconda3\envs\py39b\lib\site-packages\aiomysql\connection.py", line 1164, in read
    first_packet = await self.connection._read_packet()
  File "D:\ProgramData\Miniconda3\envs\py39b\lib\site-packages\aiomysql\connection.py", line 609, in _read_packet
    packet_header = await self._read_bytes(4)
  File "D:\ProgramData\Miniconda3\envs\py39b\lib\site-packages\aiomysql\connection.py", line 657, in _read_bytes
    data = await self._reader.readexactly(num_bytes)
  File "D:\ProgramData\Miniconda3\envs\py39b\lib\asyncio\streams.py", line 723, in readexactly
    await self._wait_for_data('readexactly')
  File "D:\ProgramData\Miniconda3\envs\py39b\lib\asyncio\streams.py", line 517, in _wait_for_data
    await self._waiter
RuntimeError: Task <Task pending name='Task-2' coro=<AsyncPoolExecutor._consume() running at D:\codes\funboost\funboost\concurrent_pool\async_pool_executor.py:110>> got Future <Future pending> attached to a different loop

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "D:\codes\funboost\funboost\consumers\base_consumer.py", line 929, in _async_run_consuming_function_with_confirm_and_retry
    rs = await corotinue_obj
  File "D:\codes\funboost\test_frame\test_async_consumer\test_child_thread_loop_aiomysql_pool.py", line 48, in async_aiomysql_f1
    print(res)
  File "D:\ProgramData\Miniconda3\envs\py39b\lib\site-packages\aiomysql\utils.py", line 139, in __aexit__
    await self._pool.release(self._conn)
RuntimeError: Task <Task pending name='Task-2' coro=<AsyncPoolExecutor._consume() running at D:\codes\funboost\funboost\concurrent_pool\async_pool_executor.py:110>> got Future <Task pending name='Task-22' coro=<Pool._wakeup() running at D:\ProgramData\Miniconda3\envs\py39b\lib\site-packages\aiomysql\pool.py:203>> attached to a different loop
"""

"""
方式一:
消费函数使用全局g_aiomysql连接池,每个线程都使用主线程的loop来使用连接池查询,所以@boost需要指定specify_async_loop为主线程的loop
"""
@boost(BoosterParams(queue_name='async_aiomysql_f1_queue', concurrent_mode=ConcurrentModeEnum.ASYNC, broker_kind=BrokerEnum.REDIS,
        log_level=10,concurrent_num=3,
       specify_async_loop=loop, # specify_async_loop传参是核心灵魂代码,不传这个还要使用主loop绑定的连接池就会报错.
       is_auto_start_specify_async_loop_in_child_thread=True,
       ))
async def async_aiomysql_f1(x):
    await asyncio.sleep(5)
    async with g_aiomysql_pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("SELECT now()")
            res = await cur.fetchall()
            print(res)


thread_local = threading.local()

async def create_pool_thread_local():
    if hasattr(thread_local, 'aiomysql_pool'):
        return thread_local.aiomysql_pool
    pool = await aiomysql.create_pool(**DB_CONFIG, minsize=1, maxsize=5, )  # 这些是重点.
    setattr(thread_local, 'aiomysql_pool', pool)
    print('创建了线程级别 threadlocal的 aiomysql连接池')
    return pool


"""
方式二:
消费函数使用thread_local线程级别全局变量,每个消费函数的那个子线程的loop使用的是线程级别自己的连接池,
这样就避免了子线程的loop去用 主线程绑定的aiomysqlpool查询数据库,导致报错

"""
@boost(BoosterParams(queue_name='async_aiomysql_f2_queue', concurrent_mode=ConcurrentModeEnum.ASYNC, broker_kind=BrokerEnum.REDIS,
        log_level=10,concurrent_num=3,
       # specify_async_loop=loop, # specify_async_loop 不需要传递,因为子线程的loop有自己的pool,不使用主线程的pool去查数据库
       is_auto_start_specify_async_loop_in_child_thread=True,
       ))
async def async_aiomysql_f2_use_thread_local_aio_mysql_pool(x):
    await asyncio.sleep(5)
    aiomysql_pool_thread_local = await create_pool_thread_local()
    async with aiomysql_pool_thread_local.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("SELECT now()")
            res = await cur.fetchall()
            print(res)




if __name__ == '__main__':
    loop.run_until_complete(create_pool()) # 先创建pool,aiomysql的pool不能直接在模块级全局变量直接生成.

    async_aiomysql_f1.clear()
    async_aiomysql_f2_use_thread_local_aio_mysql_pool.clear()

    for i in range(10):
        async_aiomysql_f1.push(i)
        async_aiomysql_f2_use_thread_local_aio_mysql_pool.push(i*10)

    async_aiomysql_f1.consume()
    async_aiomysql_f2_use_thread_local_aio_mysql_pool.consume()
    ctrl_c_recv()
