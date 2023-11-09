import time
from funboost import boost, BrokerEnum


@boost("task_api_push_queue1", qps=500, broker_kind=BrokerEnum.REDIS, is_using_rpc_mode=True)  # 入参包括20种，运行控制方式非常多，想得到的控制都会有。
def task_fun1(x, y):
    print(f'{x} + {y} = {x + y}')
    time.sleep(3)  # 框架会自动并发绕开这个阻塞，无论函数内部随机耗时多久都能自动调节并发达到每秒运行 5 次 这个 task_fun 函数的目的。
    return x + y


if __name__ == "__main__":
    # for i in range(100):
    #     task_fun1.push(i, y=i * 2)  # 发布者发布任务
    task_fun1.consume()  # 消费者启动
