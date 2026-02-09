# -*- coding: utf-8 -*-
"""
测试周期配额控频 (PeriodicQuotaConsumerMixin)

场景：每秒执行1次，但每分钟最多执行6次，配额用完后等待60秒重置

运行方式：
    python test_periodic_quota.py
    
预期行为（滑动窗口模式，默认）：
1. 每秒执行1次（qps=1 控制间隔）
2. 前6秒执行6次后，配额用完
3. 等待60秒（从启动时刻开始算的1分钟周期结束）
4. 配额重置，继续每秒执行1次...
"""

import datetime
from funboost import boost, BoosterParams, BrokerEnum, ctrl_c_recv
from funboost.contrib.override_publisher_consumer_cls.periodic_quota_mixin import (
    PeriodicQuotaConsumerMixin,
)


# 每秒1次，每分钟最多6次
@boost(BoosterParams(
    queue_name='test_periodic_quota_queue',
    broker_kind=BrokerEnum.MEMORY_QUEUE,
    consumer_override_cls=PeriodicQuotaConsumerMixin,
    is_show_message_get_from_broker = True,
    user_options={
        'quota_limit': 6,       # 每分钟最多6次
        'quota_period': 'm',    # 周期为分钟
        'sliding_window': False, # 固定窗口（从0秒/分/小时/天开始算）
    },
    qps=1,  # 每秒执行1次 # 周期额度可以和qps一起使用
))
def task_periodic_quota(x):
    print(f'⏰ [周期配额] 执行任务 x={x}, 时间: {datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]}')


if __name__ == '__main__':
    print("=" * 70)
    print("周期配额控频测试")
    print("=" * 70)
    print()
    print("配置说明：")
    print("  - quota_limit=6, quota_period='m' (每分钟最多6次)")
    print("  - qps=1 (每秒执行1次)")
    print("  - sliding_window=True (默认，滑动窗口模式)")
    print()
    print("预期行为（滑动窗口模式）：")
    print("  ⏰ 前6秒：每秒执行1次")
    print("  ⏰ 第7秒开始：配额用完，等待至启动后60秒（滑动周期结束）")
    print("  ⏰ 周期重置后：配额恢复，继续每秒执行")
    print()
    print("=" * 70)
    print()
    
    # 发布100个任务
    for i in range(100):
        task_periodic_quota.push(i)
    
    print(f"已发布 100 个任务，开始消费... (时间: {datetime.datetime.now().strftime('%H:%M:%S')})")
    print()
    
    # 启动消费
    task_periodic_quota.consume()
    
    ctrl_c_recv()
