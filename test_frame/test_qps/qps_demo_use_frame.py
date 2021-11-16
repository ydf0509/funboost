
"""
这个代码是模拟常规并发手段无法达到每秒持续精确运行8次函数(请求flask接口8次)的目的。
但是使用分布式函数调度框架能轻松达到这个目的。

下面的代码使用分部署函数调度框架来调度运行 request_flask_api 函数，

flask_veiw_mock 接口耗时0.1秒时候，控制台每秒打印8次 hello world，非常精确的符合控频目标
flask_veiw_mock 接口耗时1秒时候，控制台每秒打印8次 hello world，非常精确的符合控频目标
flask_veiw_mock 接口耗时10秒时候控，控制台每秒打印8次 hello world，非常精确的符合控频目标
flask_veiw_mock 接口耗时0.001秒时候，控制台每秒打印8次 hello world，非常精确的符合控频目标
flask_veiw_mock 接口耗时50 秒时候，控制台每秒打印8次 hello world，非常精确的符合控频目标
可以发现分布式函数调度框架无视函数耗时大小，都能做到精确控频，常规的线程池 asyncio什么的，面对这种不确定的接口耗时，简直毫无办法。

有些人到现在还没明白并发数量和qps(每秒执行多少次)之间的区别，并发数量只有在函数耗时刚好精确等于1秒时候才等于qps。
"""
import time
from function_scheduling_distributed_framework import task_deco,BrokerEnum


def flask_veiw_mock(x):
    time.sleep(0.1)  # 通过不同的sleep大小来模拟服务端响应需要消耗的时间
    # time.sleep(1)   # 通过不同的sleep大小来模拟服务端响应需要消耗的时间
    # time.sleep(10)  # 通过不同的sleep大小来模拟服务端响应需要消耗的时间
    return f"hello world {x}"

@task_deco("test_qps",broker_kind=BrokerEnum.MEMORY_QUEUE,qps=8)
def request_flask_api(x):
    response = flask_veiw_mock(x)
    print(time.strftime("%H:%M:%S"), '   ', response)


if __name__ == '__main__':
    for i in range(800):
        request_flask_api.push(i)
    request_flask_api.consume()
