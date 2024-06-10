import contextvars
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


class __ThreadCurrentTask:
    """
    用于在用户自己函数内部去获取 消息的完整体,当前重试次数等.
    """


    _fct_local_data = threading.local()
    _fct_local_data._asyncio_use_thread_concurrent_mode = False

    @property
    def function_params(self):
        return self._fct_local_data.function_params

    @function_params.setter
    def function_params(self, function_params: dict):
        self._fct_local_data.function_params = function_params

    @property
    def full_msg(self) -> dict:
        return self._fct_local_data.full_msg

    @full_msg.setter
    def full_msg(self, full_msg: dict):
        self._fct_local_data.full_msg = full_msg

    @property
    def function_result_status(self) -> FunctionResultStatus:
        return self._fct_local_data.function_result_status

    @function_result_status.setter
    def function_result_status(self, function_result_status: FunctionResultStatus):
        self._fct_local_data.function_result_status = function_result_status

    @property
    def task_id(self) -> FunctionResultStatus:
        return self.function_result_status.task_id

    @property
    def logger(self) -> logging.Logger:
        return self._fct_local_data.logger

    @logger.setter
    def logger(self, logger: logging.Logger):
        self._fct_local_data.logger = logger

thread_current_task = __ThreadCurrentTask()
def is_asyncio_environment():
    try:
        loop = asyncio.get_running_loop()
        return True
    except RuntimeError as e:
        return False


class __AsyncioCurrentTask:
    _function_params = contextvars.ContextVar("function_params")
    _full_msg = contextvars.ContextVar("full_msg")
    _function_result_status = contextvars.ContextVar("function_result_status")
    _logger = contextvars.ContextVar('logger')

    @property
    def function_params(self):
        return self._function_params.get()

    @function_params.setter
    def function_params(self, function_params: dict):
        self._function_params.set(function_params)

    @property
    def full_msg(self) -> dict:
        return self._full_msg.get()

    @full_msg.setter
    def full_msg(self, full_msg: dict):
        self._full_msg.set(full_msg)

    @property
    def function_result_status(self) -> FunctionResultStatus:
        return self._function_result_status.get()

    @function_result_status.setter
    def function_result_status(self, function_result_status: FunctionResultStatus):
        self._function_result_status.set(function_result_status)

    @property
    def task_id(self) :
        return self.function_result_status.task_id

    @property
    def logger(self) -> logging.Logger:
        return self._logger.get()

    @logger.setter
    def logger(self, logger: logging.Logger):
        self._logger.set(logger)

asyncio_current_task = __AsyncioCurrentTask()

def funboost_current_task():
    if is_asyncio_environment():
        if getattr(__ThreadCurrentTask._fct_local_data,'_asyncio_use_thread_concurrent_mode',None) is True:
            # 如果用户使用的是默认的ConcurrentModeEnum.THREADING并发模式，那么也使用线程获取上下文
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
    except (AttributeError,LookupError) as e:
        # print(e,type(e))
        return 'no_task_id'

if __name__ == '__main__':
    print(is_asyncio_environment())
    print()
    for i in range(100000):
        funboost_current_task()
        get_current_taskid()
    print()
