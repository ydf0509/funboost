import time
from funboost import boost, BoosterParams, BrokerEnum


@boost(BoosterParams(
    queue_name="task_queue_1",
    broker_kind=BrokerEnum.MEMORY_QUEUE,
    qps=2,
    concurrent_num=10
))
def task1(x, y):
    print(f'[任务1] 计算: {x} + {y} = {x + y}')
    time.sleep(1)
    return x + y


@boost(BoosterParams(
    queue_name="task_queue_2",
    broker_kind=BrokerEnum.MEMORY_QUEUE,
    qps=3,
    concurrent_num=10
))
def task2(a, b):
    print(f'[任务2] 计算: {a} * {b} = {a * b}')
    time.sleep(1)
    return a * b


if __name__ == '__main__':
    print('--- 启动两个函数的消费者 ---')
    task1.consume()
    task2.consume()
    
    print('\n--- 发布任务1 ---')
    for i in range(3):
        task1.push(i, i * 2)
    
    print('\n--- 发布任务2 ---')
    for i in range(3):
        task2.push(i, i * 2)
    
    print('\n--- 演示完成 ---')
    time.sleep(5)
