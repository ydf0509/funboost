# -*- coding: utf-8 -*-
"""
MongoAlertMonitor 告警监控示例

运行前请先启动 t_tasks.py 让任务持续产生成功/失败记录到 MongoDB。

本脚本演示三种使用场景：
  场景1：只监控高失败率队列，按报错次数告警
  场景2：只监控低失败率队列，按失败率告警
  场景3：同时监控两个队列，两种策略叠加（任一满足即告警）

运行时将在 window_seconds=60 秒窗口内统计执行情况，
每 poll_interval=10 秒检查一次，alert_interval=60 秒内不重复发告警。

webhook_url 替换为你自己的企业微信/钉钉/飞书 Webhook 地址。
"""
import os
from dotenv import load_dotenv

load_dotenv('/my_dotenv.env')

# 必须先 import 任务定义才能拿到 Booster 对象
from test_frame.test_mongo_alert.t_tasks import task_high_failure, task_low_failure

from funboost.core.mongo_alert_monitor import MongoAlertMonitor
from funboost import ctrl_c_recv

WECHAT_WEBHOOK = os.getenv('QYWEIXIN_WEBHOOK')

# ── 场景1：60 秒内报错次数 >= 5 次 就告警（高失败率队列）────────────────────
MongoAlertMonitor(
    boosters=task_high_failure,
    alert_app='wechat',
    webhook_url=WECHAT_WEBHOOK,
    window_seconds=60,
    failure_count=5,        # 60 秒内报错 >= 5 次触发
    poll_interval=10,       # 每 10 秒检查一次
    alert_interval=60,      # 60 秒内不重复发告警（方便测试，生产建议 300+）
).start()

# ── 场景2：60 秒内失败率 >= 50% 且总调用 >= 10 次 就告警（低失败率队列）──────
MongoAlertMonitor(
    boosters=task_low_failure,
    alert_app='wechat',
    webhook_url=WECHAT_WEBHOOK,
    window_seconds=60,
    errors_rate=0.5,        # 失败率 >= 50% 触发
    min_calls=10,           # 至少 10 次调用才评估
    poll_interval=10,
    alert_interval=60,
).start()

# ── 场景3：同时监控两个队列，两种策略叠加（任一满足即告警）──────────────────
# 注意：一个 MongoAlertMonitor 实例同时监控多个队列，每个队列告警状态独立
MongoAlertMonitor(
    boosters=[task_high_failure, task_low_failure],
    alert_app='wechat',
    webhook_url=WECHAT_WEBHOOK,
    window_seconds=60,
    failure_count=3,        # 任一队列 60 秒内报错 >= 3 次
    errors_rate=0.3,        # 或 失败率 >= 30%
    min_calls=5,
    poll_interval=10,
    alert_interval=60,
).start()



