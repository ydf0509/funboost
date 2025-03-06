import asyncio
import queue
import threading
from concurrent.futures import Future,ThreadPoolExecutor
import time
from flask.cli import traceback
import nb_log
import uuid

from funboost.concurrent_pool.async_helper import simple_run_in_executor

class AsyncPool:
    def __init__(self, size, loop=None,min_tasks=1,  idle_timeout=1):
        # 初始化参数
        self.min_tasks = min_tasks
        self.max_tasks = size
        self.sync_queue = queue.Queue(maxsize=size)  # 同步队列
        # self.async_queue = asyncio.Queue(maxsize=size)  # 异步队列
        self.loop = asyncio.new_event_loop()  # 创建事件循环
        self.workers = set()  # 工作协程集合
        self._lock = threading.Lock()
        self._lock_for_adjust = threading.Lock()
        self.idle_timeout = idle_timeout

        self.async_queue = None
        def create_async_queue():
            self.async_queue = asyncio.Queue(maxsize=size)
        self.loop.call_soon_threadsafe(create_async_queue)

        # 启动事件循环线程
        self.loop_thread = threading.Thread(target=self._run_loop, daemon=False)
        self.loop_thread.start()
        print("事件循环线程已启动")

        # 启动任务转移协程
        asyncio.run_coroutine_threadsafe(self._transfer_tasks(),self.loop )
        print("任务转移协程已启动")

        # 初始化工作协程
        # self._adjust_workers(min_tasks)
        # print(f"已初始化 {min_tasks} 个工作协程")

    def _run_loop(self):
        """运行事件循环"""
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    async def _transfer_tasks(self):
        """将任务从同步队列转移到异步队列"""
        while True:
            try:
                task =await simple_run_in_executor(self.sync_queue.get,timeout=0.1,async_loop=self.loop)
                await self.async_queue.put(task)
                print("任务转移到异步队列")
            except Exception: 
                print(traceback.format_exc())
                
            # try:
            #     task = self.sync_queue.get(timeout=0.01)
            #     self.sync_queue.task_done()
            #     print("任务转移到异步队列")
            #     await self.async_queue.put(task)
            # except queue.Empty:
            #     await asyncio.sleep(0.01)
         

    async def _worker(self,worker_uuid):
        """工作协程，处理任务"""
        while True:
            try:
                print(f"工作协程等待任务...  {self.async_queue.qsize()}")
                coro, args, kwargs, future = await asyncio.wait_for(
                    self.async_queue.get(), timeout=self.idle_timeout
                )
                print("工作协程获取到任务")
               
                try:
                    result = await coro(*args, **kwargs)  # 执行异步任务
                    future.set_result(result)
                    print(f"任务完成，结果: {result}")
                except Exception as e:
                    future.set_exception(e)
                    print(f"任务失败: {e}")
                finally:
                    pass
                    # self.async_queue.task_done()
                    if len(self.workers) > self.max_tasks:
                        print("工作协程超过了，准备退出")
                        with self._lock:
                            self.workers.remove(worker_uuid)
                        return
            except asyncio.TimeoutError:
                with self._lock:
                    if len(self.workers) > self.min_tasks:
                        print("工作协程获取任务超时，准备退出")
                        self.workers.remove(worker_uuid)
                        return
            except Exception as e:
                traceback.print_exc()
                return

    # def _adjust_workers(self, target_count):
    #     """调整工作协程数量"""
    #     with self._lock_for_adjust:
    #         current_count = len(self.workers)
    #         if target_count > current_count and current_count < self.max_tasks:
    #             for _ in range(target_count - current_count):
    #                 worker = asyncio.run_coroutine_threadsafe(self._worker(), self.loop)
    #                 self.workers.add(worker)
    #                 print(f"添加工作协程，总数: {len(self.workers)}")

    def submit(self, coro, *args, **kwargs):
        """提交任务"""
        if not asyncio.iscoroutinefunction(coro):
            raise ValueError("Submitted function must be an async def coroutine")

        future = Future()
        task = (coro, args, kwargs, future)
        
        self.sync_queue.put(task)  # 提交任务到同步队列
        print("提交任务到同步队列")
        if len(self.workers) < self.max_tasks:
            uuidx = uuid.uuid4()
            asyncio.run_coroutine_threadsafe(self._worker(uuidx), self.loop)
            self.workers.add(uuidx)
            print(f"添加工作协程，总数: {len(self.workers)}")
        return future



# 测试函数
async def example_task(n):
    # print(f"example_task {n} 开始运行")
    await asyncio.sleep(1)
    print(f"example_task {n} 完成")
    return n * 2

# 主程序
if __name__ == "__main__":
    pool = AsyncPool(5)
    for i in range(20):
        pool.submit(example_task, i)
    # for i, f in enumerate(futures):
    #     print(f"任务 {i} 结果: {f.result()}")  # 等待并获取结果
    # pool.shutdown()

    
    time.sleep(20)
    print('新一轮提交')
    for i in range(20):
        pool.submit(example_task, 100+i)
