import abc
import contextvars
from dataclasses import dataclass
import logging
import threading
import asyncio

from funboost.core.function_result_status_saver import FunctionResultStatus

""" 用法例子 
    '''
    fct = funboost_current_task()
    print(fct.function_result_status.get_status_dict())
    print(fct.function_result_status.task_id)
    print(fct.function_result_status.run_times)
    print(fct.full_msg)
    '''
import random
import time

from funboost import boost, FunctionResultStatusPersistanceConfig,BoosterParams
from funboost.core.current_task import funboost_current_task

@boost(BoosterParams(queue_name='queue_test_f01', qps=2,concurrent_num=5,
       function_result_status_persistance_conf=FunctionResultStatusPersistanceConfig(
           is_save_status=True, is_save_result=True, expire_seconds=7 * 24 * 3600)))
def f(a, b):
    fct = funboost_current_task()
    print(fct.function_result_status.get_status_dict())
    print(fct.function_result_status.task_id)
    print(fct.function_result_status.run_times)
    print(fct.full_msg)

    time.sleep(20)
    if random.random() > 0.5:
        raise Exception(f'{a} {b} 模拟出错啦')
    print(a+b)

    return a + b


if __name__ == '__main__':
    # f(5, 6)  # 可以直接调用

    for i in range(0, 200):
        f.push(i, b=i * 2)

    f.consume()

    """


# @dataclass
# class FctContext:
#     """
#     fct 是 funboost current task 的简写
#     """
#
#     function_params: dict
#     full_msg: dict
#     function_result_status: FunctionResultStatus
#     logger: logging.Logger
#     asyncio_use_thread_concurrent_mode: bool = False

class FctContext:
    """
    fct 是 funboost current task 的简写
    """

    def __init__(self, function_params: dict,
                 full_msg: dict,
                 function_result_status: FunctionResultStatus,
                 logger: logging.Logger,
                 asyncio_use_thread_concurrent_mode: bool = False):
        self.function_params = function_params
        self.full_msg = full_msg
        self.function_result_status = function_result_status
        self.logger = logger
        self.asyncio_use_thread_concurrent_mode = asyncio_use_thread_concurrent_mode


class _BaseCurrentTask(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def set_fct_context(self, fct_context: FctContext):
        raise NotImplemented

    @abc.abstractmethod
    def get_fct_context(self) -> FctContext:
        raise NotImplemented

    @property
    def function_params(self):
        return self.get_fct_context().function_params

    @property
    def full_msg(self) -> dict:
        return self.get_fct_context().full_msg

    @property
    def function_result_status(self) -> FunctionResultStatus:
        return self.get_fct_context().function_result_status

    @property
    def task_id(self) -> FunctionResultStatus:
        return self.function_result_status.task_id

    @property
    def logger(self) -> logging.Logger:
        return self.get_fct_context().logger

    def __str__(self):
        return f'<{self.__class__.__name__} [{self.function_result_status.get_status_dict()}]>'


class __ThreadCurrentTask(_BaseCurrentTask):
    """
    用于在用户自己函数内部去获取 消息的完整体,当前重试次数等.
    """

    _fct_local_data = threading.local()

    def set_fct_context(self, fct_context: FctContext):
        self._fct_local_data.fct_context = fct_context

    def get_fct_context(self) -> FctContext:
        return self._fct_local_data.fct_context


class __AsyncioCurrentTask(_BaseCurrentTask):
    _fct_context = contextvars.ContextVar('fct_context')

    def set_fct_context(self, fct_context: FctContext):
        self._fct_context.set(fct_context)

    def get_fct_context(self) -> FctContext:
        return self._fct_context.get()


thread_current_task = __ThreadCurrentTask()
asyncio_current_task = __AsyncioCurrentTask()


def is_asyncio_environment():
    try:
        asyncio.get_running_loop()
        return True
    except RuntimeError:
        return False


def funboost_current_task():
    if is_asyncio_environment():
        if thread_current_task.get_fct_context().asyncio_use_thread_concurrent_mode is True:
            # 如果用户使用的是默认的ConcurrentModeEnum.THREADING并发模式来运行async def 函数，那么也使用线程获取上下文
            return thread_current_task
        else:
            return asyncio_current_task
    else:
        return thread_current_task


def get_current_taskid():
    fct = funboost_current_task()
    # return fct.function_result_status.task_id
    try:
        return fct.task_id  # 不在funboost的消费函数里面就获取不到上下文了
    except (AttributeError, LookupError) as e:
        # print(e,type(e))
        return 'no_task_id'


class FctContextThread(threading.Thread):
    def __init__(self, group=None, target=None, name=None,
                 args=(), kwargs=None, *, daemon=None,
                 ):
        threading.Thread.__init__(**locals())
        self.fct_context = thread_current_task.get_fct_context()

    def run(self):
        thread_current_task.set_fct_context(self.fct_context)
        super().run()


if __name__ == '__main__':
    print(is_asyncio_environment())
    print()
    for i in range(2):
        funboost_current_task()
        print(get_current_taskid())
    print()
