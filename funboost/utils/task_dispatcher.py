

import inspect
import asyncio
from functools import wraps
from typing import Callable, Any

class LocalFunctionsDispatcher:
    """
    本地内存中函数分发运行
    """  
    def __init__(self):
        self._registry = {}

    def task(self, name: str = None):
        """注册任务的装饰器"""
        def decorator(func: Callable):
            task_name = name or func.__name__
            if task_name in self._registry:
                raise ValueError(f"Task '{task_name}' is already registered")
            sig = inspect.signature(func)
            self._registry[task_name] = (func, sig)  # 直接存原函数
            return func
        return decorator

    def run(self, task_name: str, *args, **kwargs) -> Any:
        """同步调用任务，不支持直接 await 异步函数"""
        if task_name not in self._registry:
            raise ValueError(f"Task '{task_name}' not registered")
        
        func, sig = self._registry[task_name]
        sig.bind(*args, **kwargs)  # 参数校验

        if inspect.iscoroutinefunction(func):
            # 如果是 async 函数，直接用 asyncio.run 调用（在主线程可用）
            return asyncio.run(func(*args, **kwargs))
        else:
            return func(*args, **kwargs)

    async def aio_run(self, task_name: str, *args, **kwargs) -> Any:
        """异步调用任务，普通函数通过线程池执行"""
        if task_name not in self._registry:
            raise ValueError(f"Task '{task_name}' not registered")
        
        func, sig = self._registry[task_name]
        sig.bind(*args, **kwargs)  # 参数校验

        if inspect.iscoroutinefunction(func):
            return await func(*args, **kwargs)
        else:
            # 普通函数通过线程池运行，不阻塞事件循环
            return await asyncio.to_thread(func, *args, **kwargs)


if __name__ == '__main__':
    dispatcher = LocalFunctionsDispatcher()

    @dispatcher.task()
    def add(a, b):
        return a + b

    @dispatcher.task(name='mul_task')
    async def mul(a, b):
        await asyncio.sleep(0.1)
        return a * b

    print(add(1,2)) # 直接调用

    # 同步调用
    print(dispatcher.run("add", 2, 3))  # 5
    print(dispatcher.run("mul_task", 4, 5))  # 20，asyncio.run 自动运行

    # 异步调用
    async def main():
        print(await dispatcher.aio_run("add", 6, 7))  # 13
        print(await dispatcher.aio_run("mul_task", 3, 5))  # 15

    asyncio.run(main())
