# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 9:46
"""
并发池 包括
有界队列线程池 加 错误提示
eventlet协程
gevent协程
自定义的有界队列线程池 加 错误提示，同时线程数量在任务数量少的时候可自动减少。项目中默认使用的并发方式是基于这个。

此文件夹包括5种并发池，可以单独用于任何项目，即使没有使用这个函数调度框架。
"""
from .base_pool_type import FunboostBaseConcurrentPool
from .async_pool_executor import AsyncPoolExecutor
from .bounded_threadpoolexcutor import BoundedThreadPoolExecutor
from .custom_threadpool_executor import CustomThreadPoolExecutor
from .flexible_thread_pool import FlexibleThreadPool
from .pool_commons import ConcurrentPoolBuilder