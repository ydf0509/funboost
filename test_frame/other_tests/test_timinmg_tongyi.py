# difference_calculator.py
from funboost import boost, BrokerEnum

# 定义一个消费者函数，用于计算两个数的差
@boost('difference_queue', broker_kind=BrokerEnum.REDIS)
def calculate_difference(a, b):
    result = a - b
    print(f'The difference between {a} and {b} is {result}')
    return result

# 定义一个生产者函数，用于推送任务
def push_difference_tasks():
    tasks = [(10, 5), (20, 3), (15, 7)]
    for a, b in tasks:
        calculate_difference.push(a=a, b=b)

if __name__ == '__main__':
    # 启动消费者
    calculate_difference.consume()
    # 推送任务
    push_difference_tasks()