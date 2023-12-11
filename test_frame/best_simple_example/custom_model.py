import logging
import time
from funboost import boost, BrokerEnum, BoosterParams


class BoosterParamsMy(BoosterParams):  # 传这个类就可以少每次都亲自指定使用rabbitmq作为消息队列，和使用rpc模式。
    """
    定义子类时候，字段也要注意带上类型注释
    """
    BrokerEnum: str = BrokerEnum.RABBITMQ
    max_retry_times: int = 4
    log_level: int = logging.DEBUG
    log_filename :str= '自定义.log'


@boost(boost_params=BoosterParamsMy(queue_name='task_queue_name1d', qps=3,))
def task_fun(x, y):
    print(f'{x} + {y} = {x + y}')
    time.sleep(3)  # 框架会自动并发绕开这个阻塞，无论函数内部随机耗时多久都能自动调节并发达到每秒运行 3 次 这个 task_fun 函数的目的。


@boost(boost_params=BoosterParamsMy(queue_name='task_queue_name1d', qps=10,))
def task_fun2(x, y):
    print(f'{x} - {y} = {x - y}')
    time.sleep(3)  # 框架会自动并发绕开这个阻塞，无论函数内部随机耗时多久都能自动调节并发达到每秒运行 10 次 这个 task_fun 函数的目的。


if __name__ == "__main__":
    task_fun.consume()  # 消费者启动循环调度并发消费任务
    task_fun2.consume()
    for i in range(10):
        task_fun.push(i, y=i * 2)  # 发布者发布任务
        task_fun2.push(i, i * 10)