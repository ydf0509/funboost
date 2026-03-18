# -*- coding: utf-8 -*-
"""
测试任务定义：故意让部分任务失败，配合 MongoAlertMonitor 观察告警效果。

运行步骤：
  1. 先运行本文件启动消费者并持续投递任务
  2. 再运行 t_monitor.py 启动告警监控（也可以先启动监控再投递）

前置条件：
  - funboost_config.py 中配置好 Redis（broker）和 MongoDB（状态持久化）连接信息
"""
import random
import time

from funboost import boost, BrokerEnum
from funboost.core.func_params_model import BoosterParams, FunctionResultStatusPersistanceConfig


# ── 任务A：高失败率队列，约 60% 的任务会抛异常 ──────────────────────────────
@boost(BoosterParams(
    queue_name='test_alert__high_failure_rate',
    broker_kind=BrokerEnum.REDIS,
    concurrent_num=5,
    function_result_status_persistance_conf=FunctionResultStatusPersistanceConfig(
        is_save_status=True,
    ),
))
def task_high_failure(x: int):
    if random.random() < 0.6:
        raise ValueError(f"task_high_failure 故意失败: x={x}")
    return f"ok: {x}"


# ── 任务B：低失败率队列，约 10% 的任务会抛异常 ──────────────────────────────
@boost(BoosterParams(
    queue_name='test_alert__low_failure_rate',
    broker_kind=BrokerEnum.REDIS,
    concurrent_num=5,
    function_result_status_persistance_conf=FunctionResultStatusPersistanceConfig(
        is_save_status=True,
    ),
))
def task_low_failure(x: int):
    if random.random() < 0.1:
        raise ValueError(f"task_low_failure 故意失败: x={x}")
    return f"ok: {x}"


if __name__ == '__main__':
    # 启动消费者（后台消费）
    task_high_failure.consume()
    task_low_failure.consume()

    # 持续投递任务，每 0.5 秒投一批
    i = 0
    while True:
        task_high_failure.push(x=i)
        task_low_failure.push(x=i)
        i += 1
        time.sleep(0.5)
