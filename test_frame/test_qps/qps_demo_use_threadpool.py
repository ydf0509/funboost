
"""
这个代码是模拟常规并发手段无法达到每秒持续精确运行8次函数(请求flask接口8次)的目的。

下面的代码使用8个线程并发运行 request_flask_api 函数，
当flask_veiw_mock 接口耗时0.1秒时候,在python输出控制台可以看到，10秒钟就运行结束了，控制台每秒打印了80次hello world，严重超频10倍了不符合需求
当flask_veiw_mock 接口耗时刚好精确等于1秒时候,在python输出控制台可以看到，100秒钟运行结束了，控制台每秒打印了8次hello world，只有当接口耗时刚好精确等于1秒时候，并发数量才符合qps需求
当flask_veiw_mock 接口耗时10秒时候,在python输出控制台可以看到，需要1000秒钟运行结束，控制台是每隔10秒才打印8次hello world，严重不符合持续每1秒都打印8次的目的。
由此可见，用设置并发数量来达到每秒请求8次flask的目的非常困难，99。99%的情况下服务端没那么巧刚好耗时1秒。

有些人到现在还没明白并发数量和qps(每秒执行多少次)之间的区别，并发数量只有在函数耗时刚好精确等于1秒时候才等于qps。
"""
import time
from concurrent.futures import ThreadPoolExecutor


def flask_veiw_mock(x):
    # time.sleep(0.1)  # 通过不同的sleep大小来模拟服务端响应需要消耗的时间
    # time.sleep(1)   # 通过不同的sleep大小来模拟服务端响应需要消耗的时间
    time.sleep(10)  # 通过不同的sleep大小来模拟服务端响应需要消耗的时间
    return f"hello world {x}"


def request_flask_api(x):
    response = flask_veiw_mock(x)
    print(time.strftime("%H:%M:%S"), '   ', response)


if __name__ == '__main__':
    with ThreadPoolExecutor(8) as pool:
        for i in range(800):
            pool.submit(request_flask_api,i)
