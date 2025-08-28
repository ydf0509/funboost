

"""
演示子线程中的loop怎么正确操作 异步aio连接池

正解就是子线程要使用 asyncio.run_coroutine_threadsafe(aio_do_select(1), 主线程的loop)

错误做法就是,子线程生成自己的loop,却用主线程的aio连接池查询数据库,造成经典错误  RuntimeError:  attached to a different loop

funboost的 AsyncPoolExecutor 就是在子线程运行的loop ,需要懂这个例子,才知道为什么操作aio连接池时候, funboost装饰器为什么要把主loop传给 specify_async_loop
"""

import threading

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
    print(f'主线程 threading id: {threading.get_ident()}')
    pool = await aiomysql.create_pool(**DB_CONFIG, minsize=1, maxsize=10,) # 这些是重点.
    global g_aiomysql_pool
    g_aiomysql_pool = pool
    return pool


async def aio_do_select(i):
    async with g_aiomysql_pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("SELECT now()")
            res = await cur.fetchall()
            print(res)

def run_do_select_in_child_thread(loopx:asyncio.AbstractEventLoop):
    """ 查询数据库争取的做法"""
    print(f'子线程 threading id: {threading.get_ident()}')
    asyncio.run_coroutine_threadsafe(aio_do_select(1), loopx)  # 这是正解


def run_do_select_in_child_thread_error():
    """查询数据库错误的写法, 用子线程自己的loop去调用 主线程loop绑定的g_aiomysql_pool,
     造成经典错误  RuntimeError:  attached to a different loop
     """
    print(f'子线程 threading id: {threading.get_ident()}')
    loop = asyncio.new_event_loop()
    loop.run_until_complete(aio_do_select(1))

if __name__ == '__main__':
    loop.run_until_complete(create_pool())
    threading.Thread(target=run_do_select_in_child_thread, args=(loop,)).start()
    threading.Thread(target=run_do_select_in_child_thread_error, ).start()
    loop.run_forever()
