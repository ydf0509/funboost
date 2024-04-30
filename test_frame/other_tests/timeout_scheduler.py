
import time
import schedule
from functools import wraps

class TimeoutException(Exception):
    """自定义超时异常"""
    pass

def timeout_decorator(timeout):
    """基于schedule库的超时装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = [None]  # 使用列表来存储结果，以便在内部函数修改
            executed = [False]  # 使用列表来跟踪函数是否已执行

            def job():
                nonlocal result, executed
                try:
                    result[0] = func(*args, **kwargs)
                finally:
                    executed[0] = True

            schedule.every(timeout).seconds.do(job).tag('timeout_job')  # 使用tag便于后续清除

            start_time = time.time()
            while time.time() - start_time < timeout * 2:  # 运行两倍的超时时间以确保有机会检查超时
                schedule.run_pending()
                time.sleep(0.1)
                if executed[0]:
                    schedule.clear('timeout_job')  # 清除标记的job
                    return result[0]

            schedule.clear('timeout_job')  # 如果超时，确保清除任务
            raise TimeoutException(f"Function {func.__name__} timed out after {timeout} seconds.")

        return wrapper
    return decorator

# 示例函数
@timeout_decorator(timeout=3)
def long_running_function(x):
    print(f"Running function with x={x}")
    time.sleep(5)  # 模拟耗时操作
    print("Function completed")
    return x + 1

try:
    print(long_running_function(10))
except TimeoutException as e:
    print(4444)
    print(e)