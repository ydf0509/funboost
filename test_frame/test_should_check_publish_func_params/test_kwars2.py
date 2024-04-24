import time
from funboost import boost, BrokerEnum, BoosterParams, funboost_current_task


@boost(boost_params=BoosterParams(queue_name="task_queue_name2c", qps=5, broker_kind=BrokerEnum.REDIS, log_level=10, should_check_publish_func_params=False))  # 入参包括20种，运行控制方式非常多，想得到的控制都会有。
def task_fun(**kwargs):
    print(kwargs)
    fct = funboost_current_task()
    print(fct.full_msg)
    time.sleep(3)  # 框架会自动并发绕开这个阻塞，无论函数内部随机耗时多久都能自动调节并发达到每秒运行 5 次 这个 task_fun 函数的目的。


if __name__ == "__main__":
    for i in range(10):
        task_fun.push(x=i, y=i * 2, x3=6, x4=8, x5={'k1': i, 'k2': i * 2, 'k3': i * 3})  # 发布者发布任务
        task_fun.publisher.send_msg(dict(x=i, y=i * 2, x3=6, x4=8, x5={'k1': i, 'k2': i * 2, 'k3': i * 3}))
    task_fun.consume()  # 消费者启动循环调度并发消费任务
    # task_fun.multi_process_consume(2)  # 消费者启动循环调度并发消费任务
