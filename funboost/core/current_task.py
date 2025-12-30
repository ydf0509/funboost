""" 
fct 是 funboost current task 的简写，就是当前任务的意思。能同时兼容threading和asyncio隔离。

fct用法例子 
'''
from funboost import fct 

在消费函数内部能知道自己的takid，queue_name 等等。
print(fct.function_result_status.get_status_dict())
print(fct.function_result_status.task_id)
print(fct.run_times)
print(fct.full_msg)
'''


"""

import typing
import contextvars
from dataclasses import dataclass
import logging
import threading


from funboost.core.function_result_status_saver import FunctionResultStatus

@dataclass
class FctContext:
    """
    fct 是 funboost current task 的简写
    """
    function_result_status: FunctionResultStatus
    logger: logging.Logger
    # asyncio_use_thread_concurrent_mode: bool = False # 这个属性已经废弃了，现在不管什么并发模式，都使用contextvars

# 使用 contextvars 统一管理上下文，contextvars 同时支持多线程和异步协程场景
_fct_context_var: contextvars.ContextVar[typing.Optional[FctContext]] = contextvars.ContextVar('fct_context', default=None)


def set_fct_context(fct_context: typing.Optional[FctContext]):
    """设置当前线程/协程的 FctContext"""
    _fct_context_var.set(fct_context)


def get_fct_context() -> FctContext:
    """获取当前线程/协程的 FctContext"""
    return _fct_context_var.get()


class _FctProxy:
    """
    fct 代理类，通过 contextvars 自动获取当前线程/协程的上下文。
    可以直接导入这个 fct，不需要手动写 fct = funboost_current_task() 了。
    直接 from funboost import fct 就完了。
    funboost 的 fct 相当于 flask 的 request 那种对象，自动线程/协程级别隔离，多个线程不会互相干扰。


    fct 比直接 get_fct_context 好用一点点，fct相当于把FctContext对象的一级属性的function_result_status中的很多最重要二级属性直接提升作为一级属性了。
    """

    @property
    def fct_context(self) -> FctContext:
        return get_fct_context()

    @property
    def logger(self) -> logging.Logger:
        return self.fct_context.logger

    # 下面这些属性都是 function_result_status 的二级属性，为了方便使用，把常用的二级属性直接提升作为一级属性了。
    # 你仍然可以 通过 fct.function_result_status 来访问更多的其他属性
    @property
    def function_params(self) -> dict:
        return self.fct_context.function_result_status.params

    @property
    def full_msg(self) -> dict:
        return self.fct_context.function_result_status.msg_dict

    @property
    def function_result_status(self) -> FunctionResultStatus:
        return self.fct_context.function_result_status

    @property
    def task_id(self) -> str:
        return self.fct_context.function_result_status.task_id
    @property
    def queue_name(self) -> str:
        return self.fct_context.function_result_status.queue_name

    def __str__(self):
        return f'<{self.__class__.__name__} [{self.function_result_status.get_status_dict()}]>'


fct = _FctProxy() # 推荐使用这个 fct 对象。fct 是funboost_current_task 的简写，就是当前消息任务的意思。


def funboost_current_task() -> _FctProxy:
    """
    这个是兼容老的funboost_current_task() 函数，现在直接用 fct 就行了。

    获取当前任务上下文代理对象。
    由于 contextvars 同时支持多线程和异步协程，这里直接返回 fct 代理对象即可。
    """
    return fct


def get_current_taskid() -> str:
    """获取当前任务的 task_id"""
    try:
        ctx = get_fct_context()
        if ctx is None:
            return 'no_task_id'
        return ctx.function_result_status.task_id
    except (AttributeError, LookupError):
        return 'no_task_id'


class FctContextThread(threading.Thread):
    """
    这个类自动把当前线程的 funboost 上下文自动传递给新开的线程。
    由于 contextvars 不会自动跨线程传递，只能跨协程自动传递，如果想跨线程自动传递，需要手动复制上下文。


    如果没有这个基类，那么需要 手动复制上下文，然后让线程运行 ctx.run(worker) 而不是直接运行 worker： 
    # 1. 显式捕获当前上下文
    ctx = contextvars.copy_context()
    # 2. 让线程运行 ctx.run(worker) 而不是直接运行 worker
    # 这样 worker 就会在 ctx 的上下文中执行
    t = threading.Thread(target=ctx.run, args=(worker,)) # 这是正解，传递上下文

    # t = threading.Thread(target=worker,args=(,)) # 这是错误写法，不能自动传递上下文给子线程，
    # 例如funboost的超时 kill功能，都是在另外单独的子线程去运行消费函数的，所以有时候需要传递给子线程。

    """

    def __init__(self, group=None, target=None, name=None,
                 args=(), kwargs=None, *, daemon=None):
        super().__init__(group=group, target=target, name=name,
                         args=args, kwargs=kwargs, daemon=daemon)
        # self._fct_context = get_fct_context() # 这只针对ct

        # 1. 核心修改：捕获当前所有的 contextvars 上下文快照，
        # 这更通用，不仅针对 fct_context，还可以针对所有其他 contextvars 上下文，例如opentelemetry 的
        self._ctx = contextvars.copy_context()

    def run(self):
        # set_fct_context(self._fct_context) # 这是仅针对fct_context的上下文，其他contextvars上下文不会传递。
        # super().run()

        # 2. 核心修改：在捕获的上下文中运行 super().run()
        # 这更通用，这样 run 方法内部的所有代码都能访问到父线程的 OTel TraceID 和 fct
        return self._ctx.run(super().run)



if __name__ == '__main__':
    print(get_current_taskid())
