# -*- coding: utf-8 -*-

import datetime
import time
from funboost import boost, BoosterParams, BrokerEnum, ctrl_c_recv



fail_count_sleep = 0
fail_count_requeue = 0

# ========== 测试1: sleep 模式 + 指数退避 ==========
@boost(BoosterParams(
    queue_name='test_adv_retry_sleep_queue',
    broker_kind=BrokerEnum.MEMORY_QUEUE,
    is_show_message_get_from_broker=True,

    max_retry_times=30,
    is_using_advanced_retry=True,
    advanced_retry_config={
        'retry_mode': 'sleep',           # 在当前线程 sleep
        'retry_base_interval': 1.0,       # 基础间隔 1 秒
        'retry_multiplier': 2.0,          # 1s, 2s, 4s
        'retry_max_interval': 60.0,
        'retry_jitter': False,
    },
    
))
def task_sleep_retry(x):
    global fail_count_sleep
    fail_count_sleep += 1
    now = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
    print(f'❌ [sleep模式] 第{fail_count_sleep}次执行 x={x}, 时间: {now}，即将抛出异常')
    raise ValueError(f'模拟错误 x={x}')


# ========== 测试2: requeue 模式 + 指数退避 ==========
# 注意：requeue 模式需要延迟任务支持，MEMORY_QUEUE 配合 memory jobstore 即可
@boost(BoosterParams(
    queue_name='test_adv_retry_requeue_queue',
    broker_kind=BrokerEnum.MEMORY_QUEUE,
    is_show_message_get_from_broker=True,
    delay_task_apscheduler_jobstores_kind='memory',  # 测试用 memory，不依赖 redis
    
    max_retry_times=100,
    is_using_advanced_retry=True,
    advanced_retry_config={
        'retry_mode': 'requeue',          # 发回队列等待
        'retry_base_interval': 10.0,       # 基础间隔 10 秒
        'retry_multiplier': 2.0,          # 10s, 20s, 40s, 80s, 160s, 300s, 300s, 300s ...
        'retry_max_interval': 300.0,
        'retry_jitter': False,
    },  
))
def task_requeue_retry(x):
    global fail_count_requeue
    fail_count_requeue += 1
    now = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
    print(f'❌ [requeue模式] 第{fail_count_requeue}次执行 x={x}, 时间: {now}，即将抛出异常')
    raise ValueError(f'模拟错误 x={x}')


if __name__ == '__main__':
    # 发布测试任务
    task_sleep_retry.push(100)
    task_requeue_retry.push(200)

    print(f"已发布测试任务，开始消费... (时间: {datetime.datetime.now().strftime('%H:%M:%S')})")
    print()

    # 启动消费
    task_sleep_retry.consume()
    # task_requeue_retry.consume()

    ctrl_c_recv()
