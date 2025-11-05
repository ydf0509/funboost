import asyncio
from typing import Callable, Any, Optional, Coroutine, TypeVar
from asyncio import Queue
from concurrent.futures import Future
import threading
from functools import wraps

T = TypeVar('T')


class AsyncioPool:
    """异步并发池，专门用于执行 async def 函数"""
    
    def __init__(
        self,
        max_workers: int = 10,
        queue_size: int = 0,
        loop: Optional[asyncio.AbstractEventLoop] = None
    ):
        """
        初始化并发池
        
        Args:
            max_workers: 最大并发工作数量
            queue_size: 工作队列大小，0 表示无限制
            loop: 事件循环，如果为 None 则自动获取
        """
        self.max_workers = max_workers
        self.queue_size = queue_size
        self._loop = loop
        self._work_queue: Optional[Queue] = None
        self._workers = []
        self._started = False
        self._shutdown = False
        self._lock = threading.Lock()
        
    @property
    def loop(self) -> asyncio.AbstractEventLoop:
        """获取或创建事件循环"""
        if self._loop is None:
            try:
                self._loop = asyncio.get_running_loop()
            except RuntimeError:
                # 如果当前没有运行的循环，尝试获取默认循环
                try:
                    self._loop = asyncio.get_event_loop()
                except RuntimeError:
                    self._loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(self._loop)
        return self._loop
    
    async def start(self):
        """启动并发池"""
        if self._started:
            return
        
        self._started = True
        self._shutdown = False
        
        # 创建工作队列
        if self.queue_size > 0:
            self._work_queue = Queue(maxsize=self.queue_size)
        else:
            self._work_queue = Queue()
        
        # 启动工作协程
        for i in range(self.max_workers):
            worker = asyncio.create_task(self._worker(i))
            self._workers.append(worker)
    
    async def _worker(self, worker_id: int):
        """工作协程，持续从队列中获取任务并执行"""
        while not self._shutdown:
            try:
                # 等待任务
                task_item = await self._work_queue.get()
                
                if task_item is None:  # 结束信号
                    self._work_queue.task_done()
                    break
                
                coro_func, args, kwargs, future = task_item
                
                try:
                    # 执行异步任务
                    result = await coro_func(*args, **kwargs)
                    
                    # 设置结果
                    if not future.done():
                        self.loop.call_soon_threadsafe(future.set_result, result)
                        
                except Exception as e:
                    # 设置异常
                    if not future.done():
                        self.loop.call_soon_threadsafe(future.set_exception, e)
                finally:
                    self._work_queue.task_done()
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Worker {worker_id} error: {e}")
    
    async def aio_submit(
        self,
        coro_func: Callable[..., Coroutine[Any, Any, T]],
        *args,
        **kwargs
    ) -> T:
        """
        异步提交任务到并发池
        
        Args:
            coro_func: 异步函数 (async def)
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            任务执行结果
            
        Raises:
            RuntimeError: 如果池正在关闭
            TypeError: 如果提交的不是异步函数
        """
        if not asyncio.iscoroutinefunction(coro_func):
            raise TypeError(f"{coro_func} is not a coroutine function (async def)")
        
        if not self._started:
            await self.start()
        
        if self._shutdown:
            raise RuntimeError("Pool is shutting down")
        
        # 创建 asyncio Future 对象
        future = self.loop.create_future()
        
        # 将任务放入队列
        await self._work_queue.put((coro_func, args, kwargs, future))
        
        # 等待结果
        return await future
    
    def submit(
        self,
        coro_func: Callable[..., Coroutine[Any, Any, T]],
        *args,
        **kwargs
    ) -> Future:
        """
        同步提交任务到并发池（返回 concurrent.futures.Future 对象）
        
        Args:
            coro_func: 异步函数 (async def)
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            concurrent.futures.Future 对象
            
        Raises:
            TypeError: 如果提交的不是异步函数
        """
        if not asyncio.iscoroutinefunction(coro_func):
            raise TypeError(f"{coro_func} is not a coroutine function (async def)")
        
        # 创建线程安全的 Future
        future = Future()
        
        async def _submit_task():
            try:
                if not self._started:
                    await self.start()
                
                if self._shutdown:
                    raise RuntimeError("Pool is shutting down")
                
                # 创建 asyncio Future
                asyncio_future = self.loop.create_future()
                
                # 将任务放入队列
                await self._work_queue.put((coro_func, args, kwargs, asyncio_future))
                
                # 等待结果并设置到线程安全的 Future
                result = await asyncio_future
                future.set_result(result)
            except Exception as e:
                future.set_exception(e)
        
        # 在事件循环中调度任务
        asyncio.run_coroutine_threadsafe(_submit_task(), self.loop)
        
        return future
    
    async def map(
        self,
        coro_func: Callable[..., Coroutine[Any, Any, T]],
        *iterables
    ) -> list[T]:
        """
        异步 map 操作，对可迭代对象中的每个元素应用异步函数
        
        Args:
            coro_func: 异步函数
            *iterables: 可迭代对象
            
        Returns:
            结果列表
        """
        tasks = []
        for args in zip(*iterables):
            task = self.aio_submit(coro_func, *args)
            tasks.append(task)
        
        return await asyncio.gather(*tasks)
    
    async def shutdown(self, wait: bool = True):
        """
        关闭并发池
        
        Args:
            wait: 是否等待所有任务完成
        """
        if self._shutdown:
            return
        
        self._shutdown = True
        
        if wait and self._work_queue is not None:
            # 等待队列中的任务完成
            await self._work_queue.join()
        
        # 向所有 worker 发送结束信号
        for _ in range(len(self._workers)):
            if self._work_queue is not None:
                await self._work_queue.put(None)
        
        # 等待所有 worker 结束
        if self._workers:
            await asyncio.gather(*self._workers, return_exceptions=True)
        
        self._workers.clear()
        self._started = False
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.shutdown(wait=True)
        return False
    
    def qsize(self) -> int:
        """获取当前队列大小"""
        if self._work_queue is None:
            return 0
        return self._work_queue.qsize()
    
    def pending(self) -> int:
        """获取待处理任务数量（队列中的任务）"""
        return self.qsize()
    
    def is_shutdown(self) -> bool:
        """检查池是否已关闭"""
        return self._shutdown


# ==================== 使用示例 ====================

async def example_aio_submit():
    """示例：使用 aio_submit 异步提交"""
    print("\n=== aio_submit 异步提交示例 ===")
    
    # 创建并发池：最大5个并发，队列大小为10
    pool = AsyncioPool(max_workers=5, queue_size=10)
    
    async def fetch_data(task_id: int, delay: float):
        """模拟异步任务"""
        print(f"Task {task_id} started")
        await asyncio.sleep(delay)
        print(f"Task {task_id} completed")
        return f"Result-{task_id}"
    
    async with pool:
        # 提交多个任务
        tasks = []
        for i in range(10):
            task = pool.aio_submit(fetch_data, i, 0.5)
            tasks.append(task)
        
        # 等待所有任务完成
        results = await asyncio.gather(*tasks)
        print(f"\n所有结果: {results}")


def example_sync_submit():
    """示例：使用 submit 同步提交"""
    print("\n=== submit 同步提交示例 ===")
    
    async def process_item(item_id: int):
        """处理单个项目"""
        await asyncio.sleep(0.5)
        return f"Processed-{item_id}"
    
    # 创建事件循环
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    # 创建并发池
    pool = AsyncioPool(max_workers=3, queue_size=5, loop=loop)
    
    # 在单独的线程中运行事件循环
    def run_loop():
        asyncio.set_event_loop(loop)
        loop.run_forever()
    
    import threading
    loop_thread = threading.Thread(target=run_loop, daemon=True)
    loop_thread.start()
    
    # 同步提交任务
    futures = []
    for i in range(10):
        future = pool.submit(process_item, i)
        futures.append(future)
        print(f"Submitted task {i}")
    
    # 等待所有任务完成
    results = []
    for i, future in enumerate(futures):
        result = future.result(timeout=10)
        results.append(result)
        print(f"Task {i} result: {result}")
    
    print(f"\n所有结果: {results}")
    
    # 清理
    asyncio.run_coroutine_threadsafe(pool.shutdown(), loop).result()
    loop.call_soon_threadsafe(loop.stop)
    loop_thread.join(timeout=2)


async def example_map():
    """示例：使用 map 批量处理"""
    print("\n=== map 批量处理示例 ===")
    
    pool = AsyncioPool(max_workers=4, queue_size=20)
    
    async def square(x: int):
        """计算平方"""
        await asyncio.sleep(0.1)
        return x * x
    
    async with pool:
        numbers = range(1, 11)
        results = await pool.map(square, numbers)
        print(f"平方结果: {results}")


async def example_error_handling():
    """示例：错误处理"""
    print("\n=== 错误处理示例 ===")
    
    pool = AsyncioPool(max_workers=3, queue_size=5)
    
    async def risky_task(task_id: int):
        """可能失败的任务"""
        await asyncio.sleep(0.2)
        if task_id % 3 == 0:
            raise ValueError(f"Task {task_id} failed!")
        return f"Success-{task_id}"
    
    async with pool:
        tasks = []
        for i in range(10):
            task = pool.aio_submit(risky_task, i)
            tasks.append(task)
        
        # 收集结果，处理异常
        for i, task in enumerate(tasks):
            try:
                result = await task
                print(f"Task {i}: {result}")
            except ValueError as e:
                print(f"Task {i}: Error - {e}")


async def example_queue_monitoring():
    """示例：队列监控"""
    print("\n=== 队列监控示例 ===")
    
    pool = AsyncioPool(max_workers=2, queue_size=5)
    
    async def slow_task(task_id: int):
        """慢速任务"""
        print(f"  [Worker] Processing task {task_id}")
        await asyncio.sleep(1)
        return task_id
    
    async with pool:
        # 提交任务并监控队列
        tasks = []
        for i in range(12):
            print(f"提交任务 {i}, 队列大小: {pool.qsize()}, 待处理: {pool.pending()}")
            task = pool.aio_submit(slow_task, i)
            tasks.append(task)
            await asyncio.sleep(0.2)
        
        print(f"\n所有任务已提交，等待完成...")
        results = await asyncio.gather(*tasks)
        print(f"完成所有任务: {len(results)} 个")


async def example_real_world_crawler():
    """示例：模拟爬虫场景"""
    print("\n=== 爬虫场景示例 ===")
    
    # 限制并发为 5，避免过载目标服务器
    pool = AsyncioPool(max_workers=5, queue_size=20)
    
    async def fetch_url(url: str):
        """模拟抓取 URL"""
        print(f"Fetching {url}...")
        await asyncio.sleep(0.5)  # 模拟网络延迟
        return f"Content from {url}"
    
    urls = [f"https://example.com/page/{i}" for i in range(20)]
    
    async with pool:
        results = await pool.map(fetch_url, urls)
        print(f"\n成功抓取 {len(results)} 个页面")


# 运行所有示例
if __name__ == "__main__":
    print("=" * 60)
    print("AsyncioPool 示例演示")
    print("=" * 60)
    
    # 异步示例
    asyncio.run(example_aio_submit())
    asyncio.run(example_map())
    asyncio.run(example_error_handling())
    asyncio.run(example_queue_monitoring())
    asyncio.run(example_real_world_crawler())
    
    # 同步示例
    example_sync_submit()