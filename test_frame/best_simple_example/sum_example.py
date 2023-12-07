import time
from funboost import boost, BrokerEnum, BoosterParams


# @boost(boost_params=BoosterParams(queue_name="task_queue_name1", qps=5, broker_kind=BrokerEnum.SQLITE_QUEUE, log_level=20))  # 入参包括20种，运行控制方式非常多，想得到的控制都会有。
# @boost(queue_name="task_queue_name1", qps=5, broker_kind=BrokerEnum.SQLITE_QUEUE, log_level=20)
from funboost.core.func_params_model import BoosterParamsComplete


@boost(queue_name="task_queue_name1", qps=5,  log_level=10,
       boost_params=BoosterParamsComplete(queue_name='task_queue_name1',max_retry_times=4,qps=3,
                                  # log_filename='自定义.log'
                                  ))
def task_fun(x, y):
    print(f'{x} + {y} = {x + y}')
    time.sleep(3)  # 框架会自动并发绕开这个阻塞，无论函数内部随机耗时多久都能自动调节并发达到每秒运行 5 次 这个 task_fun 函数的目的。


if __name__ == "__main__":
    for i in range(10):
        task_fun.push(i, y=i * 2)  # 发布者发布任务
    task_fun.consume()  # 消费者启动循环调度并发消费任务
