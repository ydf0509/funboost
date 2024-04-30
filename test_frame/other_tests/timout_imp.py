import traceback

import typing

from auto_run_on_remote import run_current_script_on_remote

run_current_script_on_remote()
import functools
import time
import signal


def timeout_linux(timeout: typing.Optional[int]):
    def _timeout_linux(func, ):
        """装饰器，为函数添加超时功能"""

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            def _timeout_handler(signum, frame):
                """超时处理函数，当接收到信号时抛出异常"""
                raise TimeoutError(f"Function: {func} params: {args}, {kwargs} ,execution timed out: {timeout}")

            # 设置超时信号处理器
            signal.signal(signal.SIGALRM, _timeout_handler)  # 只适合linux 的 timout
            # 启动一个定时器，超时后发送信号
            signal.alarm(timeout)

            try:
                return func(*args, **kwargs)
            finally:
                # 执行完毕记得取消定时器
                signal.alarm(0)  # 关闭定时器

        return wrapper

    return _timeout_linux


if __name__ == '__main__':

    # 使用装饰器实现超时功能
    @timeout_linux(3)
    def fun(x, ):
        """示例函数，模拟长时间运行的操作"""
        print(f"Running function with x={x}")
        time.sleep(5)  # 模拟耗时操作
        print("Function completed")
        return x + 1


    try:
        print(fun(10))  # 尝试运行函数，设置超时为3秒
    except TimeoutError as e:
        traceback.print_exc()

    import celery
