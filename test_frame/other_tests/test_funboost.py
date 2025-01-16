

# from funboost import boost,BoosterParams

# @boost('test_queue')
# def add_numbers(x: int, y: int) -> int:
#     return x + y

# if __name__ == '__main__':
#     # Start the consumer
#     add_numbers.consume()

#     result = add_numbers.push(3, 4)
#     print(f"The sum is: {result.result()}")

import sys
print(sys.executable)

from funboost import boost, BoosterParams,ctrl_c_recv,run_forever
from funboost.timing_job.apscheduler_use_redis_store import funboost_background_scheduler_redis_store
from funboost.timing_job.timing_push import ApsJobAdder


class MyBoosterParams(BoosterParams):
    max_retry_times: int = 3  # 设置最大重试次数为3次
    function_timeout: int = 10  # 设置超时时间为10秒


@boost(MyBoosterParams(queue_name='add_numbers_queue'))
def add_numbers(x: int, y: int) -> int:
    """Add two numbers."""
    return x + y

if __name__ == '__main__':
    # 定义定时任务
    # Start the scheduler


    
    ApsJobAdder(add_numbers,job_store_kind='redis').add_push_job(
        args=(1, 2),
        trigger='date',  # 使用日期触发器
        run_date='2025-01-16 19:15:40',  # 设置运行时间
        # id='add_numbers_job'  # 任务ID
    )

    ApsJobAdder(add_numbers,job_store_kind='memory').add_push_job(
        args=(1, 2),
        trigger='date',  # 使用日期触发器
        run_date='2025-01-16 19:15:50',  # 设置运行时间
        # id='add_numbers_job'  # 任务ID
    )

    # 启动消费者
    add_numbers.consume()
    # ctrl_c_recv()
    run_forever()