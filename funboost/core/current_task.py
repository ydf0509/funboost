import contextvars
import threading
import asyncio
from funboost.core.function_result_status_saver import FunctionResultStatus


class ThreadCurrentTask:
    _local_data = threading.local()

    @property
    def function_params(self):
        return self._local_data.function_params

    @function_params.setter
    def function_params(self, function_params: dict):
        self._local_data.function_params = function_params

    @property
    def full_msg(self) -> dict:
        return self._local_data.full_msg

    @full_msg.setter
    def full_msg(self, full_msg: dict):
        self._local_data.full_msg = full_msg

    @property
    def function_result_status(self) -> FunctionResultStatus:
        return self._local_data.function_result_status

    @function_result_status.setter
    def function_result_status(self, function_result_status: FunctionResultStatus):
        self._local_data.function_result_status = function_result_status


def is_asyncio_environment():
    try:
        loop = asyncio.get_event_loop()
        return True
    except RuntimeError:
        return False


class AsyncioCurrentTask:
    _function_params = contextvars.ContextVar("function_params")
    _full_msg = contextvars.ContextVar("full_msg")
    _function_result_status = contextvars.ContextVar("function_result_status")

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


def funboost_current_task():
    return AsyncioCurrentTask() if is_asyncio_environment() else ThreadCurrentTask()
