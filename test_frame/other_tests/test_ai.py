
import sys
print(sys.path)
from funboost import boost, BrokerEnum
from funboost.timing_job.timing_push import ApsJobAdder

a=rrr
# 1. 定义任务函数
@boost('queue_test_add_numbers', broker_kind=BrokerEnum.REDIS)
def add_numbers(x, y):
    print(f'计算 {x} + {y} = {x + y}')
    return x + y


if __name__ == '__main__':
    # 2. 添加定时任务，每5秒执行一次
    ApsJobAdder(add_numbers, job_store_kind='memory').add_push_job(
        args=(1, 2),  # 传入参数
        trigger='interval',  # 使用间隔触发器
        seconds=5,  # 每5秒执行一次
        id='add_numbers_job'  # 任务ID
    )

    # 3. 启动消费
    add_numbers.consume()