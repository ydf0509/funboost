# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 13:07
from collections import deque
from concurrent.futures import Future
from queue import Queue, SimpleQueue
import asyncio

from funboost.publishers.base_publisher import AbstractPublisher
from funboost.queues.memory_queues_map import PythonQueues

local_pyhton_queue_name__local_pyhton_queue_obj_map = dict()  # 使local queue和其他中间件完全一样的使用方式，使用映射保存队列的名字，使消费和发布通过队列名字能找到队列对象。


class LocalPythonQueuePublisher(AbstractPublisher):
    """
    使用python内置queue对象作为中间件。
    内存队列非常重要，性能强，不担心有的对象无法pickle序列化
    可以通过get_future和get_aio_future方法不依赖Redis实现rpc获取结果
    """

    # noinspection PyAttributeOutsideInit

    @property
    def local_python_queue(self) -> Queue:
        maxsize = self.publisher_params.broker_exclusive_config['maxsize']
        return PythonQueues.get_queue(self._queue_name, maxsize=maxsize)

    def _publish_impl(self, msg):
        # noinspection PyTypeChecker
        pass
        self.local_python_queue.put(msg)

   
    def clear(self):
        # noinspection PyUnresolvedReferences
        self.local_python_queue.queue.clear()
        self.logger.warning(f'清除 本地队列中的消息成功')

    def get_message_count(self):
        return self.local_python_queue.qsize()

    def close(self):
        pass


    # 内存队列独有方法，获取结果直接通过future.result()获取，不依赖Redis实现rpc获取结果
    def get_future(self, *func_args, **func_kwargs) -> Future:
        """
        内存队列专用方法，发布消息并返回 concurrent.futures.Future 对象，不依赖 Redis 作为 RPC。
        
        利用内存队列不序列化的特性，直接把 Future 对象塞进消息体的 extra 中随消息一起流转，
        消费端执行完函数后，将 FunctionResultStatus 通过 future.set_result() 设置回来。
        完全零外部依赖，纯进程内通信。

        用法:
            future = task_fun.publisher.get_future(1, y=2)
            function_result_status = future.result(timeout=10)   # 阻塞等待结果
            print(function_result_status.result)    # 获取函数返回值
            print(function_result_status.success)   # 是否成功
        """
        future = Future()
        # 构造 msg_dict
        msg_dict = dict(func_kwargs)
        for index, arg in enumerate(func_args):
            msg_dict[self.publish_params_checker.all_arg_name_list[index]] = arg
        # 将 Future 对象直接放入消息的 extra 中，内存队列不序列化，Future 对象可以直接传递
        msg_dict['extra'] = {'_memory_call_future': future}
        self.publish(msg_dict)
        return future
    
    # 内存队列独有方法，获取结果直接通过 await future 获取，不依赖Redis实现rpc获取结果
    def get_aio_future(self, *func_args, **func_kwargs) -> asyncio.Future:
        """
        内存队列专用方法，发布消息并返回 asyncio.Future 对象，不依赖 Redis 作为 RPC。

        注意：此方法本身是同步的，返回值是 asyncio.Future，需要在异步上下文中 await 使用。
        内部调用 get_future() 获取 concurrent.futures.Future，
        再通过 asyncio.wrap_future() 将其桥接为 asyncio.Future。

        用法（在异步上下文中）:
            # 先拿到 future，稍后再 await（推荐，可并发多个任务）
            future = task_fun.publisher.get_aio_future(1, y=2)
            # ... 做其他事 ...
            result_status = await future
            print(result_status.result)    # 获取函数返回值
            print(result_status.success)   # 是否成功
        """
        sync_future = self.get_future(*func_args, **func_kwargs)
        loop = asyncio.get_running_loop()
        return asyncio.wrap_future(sync_future, loop=loop)



