# -*- coding: utf-8 -*-
"""
测试令牌桶控频 (TokenBucketRateLimitConsumerMixin)

对比 Funboost 原生 qps 控频和 Celery 风格的令牌桶控频的区别。

运行方式：
    python test_token_bucket_rate_limit.py
    
预期行为：
1. task_token_bucket: 前几个任务会"突发"执行（瞬间执行），之后恢复到稳定速率
2. task_native_qps: 始终保持匀速执行

观察日志中的时间戳，可以明显看出两种控频方式的差异。
"""

import time
import datetime
from funboost import boost, BoosterParams, BrokerEnum, ctrl_c_recv
from funboost.contrib.override_publisher_consumer_cls.token_bucket_rate_limit_mixin import (
    TokenBucketRateLimitConsumerMixin,
    TokenBucketBoosterParams,
)


# 场景1：令牌桶控频 (Celery 风格)
# rate_limit='6/m' = 每分钟6次 = 每10秒1次
# burst_size=3 = 最多可突发3个任务
@boost(BoosterParams(
    queue_name='test_token_bucket_queue',
    broker_kind=BrokerEnum.MEMORY_QUEUE,
    consumer_override_cls=TokenBucketRateLimitConsumerMixin,
    user_options={
        'rate_limit': '6/m',  # 每分钟6次
        'burst_size': 1,      # 突发容量3个
    },
    qps=1,  # 关闭原生 qps 控频
))
def task_token_bucket(x):
    print(f'🪣 [令牌桶] 执行任务 x={x}, 时间: {datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]}')


# 场景2：Funboost 原生 qps 控频 (匀速)
# qps = 6/60 = 0.1 = 每10秒1次
@boost(BoosterParams(
    queue_name='test_native_qps_queue',
    broker_kind=BrokerEnum.MEMORY_QUEUE,
    qps=0.1,  # 每10秒1次
))
def task_native_qps(x):
    print(f'⏱️ [原生QPS] 执行任务 x={x}, 时间: {datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]}')


if __name__ == '__main__':
    print("=" * 60)
    print("令牌桶控频 vs 原生QPS控频 对比测试")
    print("=" * 60)
    print()
    print("配置说明：")
    print("  - 令牌桶: rate_limit='6/m' (每分钟6次), burst_size=3 (突发3个)")
    print("  - 原生QPS: qps=0.1 (每10秒1次)")
    print()
    print("预期行为：")
    print("  🪣 令牌桶: 前3个任务瞬间执行（突发），之后每10秒1个")
    print("  ⏱️ 原生QPS: 从头到尾每10秒1个（匀速）")
    print()
    print("=" * 60)
    print()
    
    # 发布任务
    for i in range(10):
        task_token_bucket.push(i)
        task_native_qps.push(i)
    
    print(f"已发布 10 个任务到每个队列，开始消费... (时间: {datetime.datetime.now().strftime('%H:%M:%S')})")
    print()
    
    # 启动消费
    task_token_bucket.consume()
    # task_native_qps.consume()
    
    ctrl_c_recv()
