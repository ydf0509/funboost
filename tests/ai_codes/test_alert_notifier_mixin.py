# -*- coding: utf-8 -*-
"""
AlertNotifierConsumerMixin 使用示例

演示三种场景：
1. 连续失败策略 + 企业微信告警
2. 错误率策略 + 钉钉告警
3. 只跟踪特定异常类型
"""
import time
import random
from funboost import boost, BoosterParams, BrokerEnum, ctrl_c_recv,ConcurrentModeEnum
 
from funboost.contrib.override_publisher_consumer_cls.alert_notifier_mixin import (
    AlertNotifierConsumerMixin,
    AlertNotifierBoosterParams,
)

# ================================================================
# 示例1：连续失败策略 + 企业微信告警（最常用场景）
#
# 连续失败 3 次就发企业微信告警，恢复后也通知，
# 60 秒内不重复告警。
# ================================================================

@boost(AlertNotifierBoosterParams(
    queue_name='alert_demo_consecutive',
    broker_kind=BrokerEnum.MEMORY_QUEUE,
    concurrent_mode=ConcurrentModeEnum.SINGLE_THREAD,
    qps=5,
    max_retry_times=0,
    user_options={
        'alert_options': {
            'strategy': 'consecutive',
            'failure_threshold': 3,
            'alert_app': 'wechat',
            'webhook_url': 'https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=your_key_here',
            'alert_interval': 60,
        },
    },
))
def task_consecutive(x: int):
    """模拟一个不稳定的任务：前6次失败，之后恢复正常"""
    time.sleep(1)
    if x < 6:
        raise ConnectionError(f"模拟连接失败 x={x}")
    return f"success x={x}"


# ================================================================
# 示例2：错误率策略 + 钉钉告警
#
# 60 秒滑动窗口内，至少 5 次调用且错误率 >= 50% 时告警。
# ================================================================

@boost(BoosterParams(
    queue_name='alert_demo_rate',
    broker_kind=BrokerEnum.MEMORY_QUEUE,
    qps=5,
    max_retry_times=0,
    concurrent_mode=ConcurrentModeEnum.SINGLE_THREAD,
    consumer_override_cls=AlertNotifierConsumerMixin,
    user_options={
        'alert_options': {
            'strategy': 'rate',
            'errors_rate': 0.5,
            'period': 60,
            'min_calls': 5,
            'alert_app': 'dingtalk',
            'webhook_url': 'https://oapi.dingtalk.com/robot/send?access_token=your_token_here',
            'alert_interval': 120,
        },
    },
))
def task_rate(x: int):
    """模拟一个概率性失败的任务：50% 概率失败"""
    time.sleep(1)
    if random.random() < 0.5:
        raise TimeoutError(f"模拟超时 x={x}")
    return f"success x={x}"


# ================================================================
# 示例3：只跟踪特定异常类型
#
# 只有 ConnectionError 和 TimeoutError 才触发告警，
# 其他异常类型（如 ValueError）不计入。
# ================================================================

@boost(AlertNotifierBoosterParams(
    queue_name='alert_demo_filtered',
    broker_kind=BrokerEnum.MEMORY_QUEUE,
    qps=5,
    max_retry_times=0,
    user_options={
        'alert_options': {
            'failure_threshold': 3,
            'alert_app': 'webhook',
            'webhook_url': 'https://your-custom-webhook.example.com/alert',
            'alert_interval': 60,
            'exceptions': (ConnectionError, TimeoutError),
        },
    },
))
def task_filtered(x: int):
    """ValueError 不会触发告警，只有 ConnectionError 才会"""
    if x % 3 == 0:
        raise ValueError(f"参数校验失败 x={x}（不触发告警）")
    if x % 3 == 1:
        raise ConnectionError(f"连接失败 x={x}（触发告警）")
    return f"success x={x}"


if __name__ == '__main__':
    # 发布测试消息
    for i in range(15):
        task_consecutive.push(x=i)

    for i in range(200):
        task_rate.push(x=i)

    for i in range(15):
        task_filtered.push(x=i)

    # 启动消费（都是内存队列，无需外部依赖）
    # task_consecutive.consume()
    task_rate.consume()
    # task_filtered.consume()

    ctrl_c_recv()
