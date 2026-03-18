# -*- coding: utf-8 -*-
# @Author  : AI Assistant
# @Time    : 2026/3/16
"""
基于 MongoDB 轮询的分布式告警监控 (Mongo Alert Monitor)

原理：用户通过 BoosterParams 配置 is_save_status=True 将函数执行状态保存到 MongoDB，
本模块定期轮询 MongoDB 中近 N 秒内的执行记录，统计成功/失败情况，
达到告警条件时发送告警，恢复后发送恢复通知。

优势：
- 天然分布式汇总：所有进程/机器的消费者都往同一个 MongoDB 集合写状态，
  只需一个监控实例即可汇总全局执行情况
- 零侵入：不需要修改消费者代码，不需要 mixin，只需开启 is_save_status
- 支持同时监控多个队列

=== 前置条件 ===

消费者需开启状态持久化：

    @boost(BoosterParams(
        queue_name='my_task',
        broker_kind=BrokerEnum.REDIS,
        function_result_status_persistance_conf=FunctionResultStatusPersistanceConfig(
            is_save_status=True,
        ),
    ))
    def my_task(x):
        ...

=== 两种告警策略 ===

1. count（报错次数）：
   window_seconds 秒内，报错次数 >= failure_count 时告警。

2. rate（报错比例）：
   window_seconds 秒内，调用次数 >= min_calls 且失败率 >= errors_rate 时告警。

两种策略可以同时设置，任一条件满足即触发告警。

=== MongoAlertMonitor 参数说明 ===

    boosters:           被 @boost 装饰的函数（Booster 对象），支持单个或列表，自动提取 queue_name 和 table_name
    alert_app:          告警通道: 'dingtalk', 'wechat', 'feishu', 'webhook', 'custom'，默认 'wechat'
                        设为 'custom' 时，需继承 MongoAlertMonitor 并重写 custom_send_notification 方法
    webhook_url:        告警通道的 Webhook 地址（alert_app 为 'webhook' 时使用）

    window_seconds:     统计窗口秒数，查询最近 N 秒的执行记录，默认 60

    failure_count:      窗口内报错次数阈值，达到即告警，None 表示不按次数告警，默认 None，按次数告警时候无视min_calls参数。
    errors_rate:        窗口内失败率阈值 0.0~1.0，None 表示不按比例告警，默认 None
    min_calls:          按比例告警时，窗口内最少调用数才评估，默认 5

    poll_interval:      轮询间隔秒数，默认 10
    alert_interval:     告警去重间隔秒数，默认 300

=== 用法示例 ===

    from funboost.core.mongo_alert_monitor import MongoAlertMonitor

    # 示例1：监控单个队列，窗口内报错次数 >= 10 就告警
    MongoAlertMonitor(
        boosters=my_task,
        alert_app='wechat',
        webhook_url='https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx',
        window_seconds=60,
        failure_count=10,
    ).start()

    # 示例2：一次监控多个队列，失败率 >= 50% 就告警
    MongoAlertMonitor(
        boosters=[task_a, task_b, task_c],
        alert_app='dingtalk',
        webhook_url='https://oapi.dingtalk.com/robot/send?access_token=xxx',
        window_seconds=60,
        errors_rate=0.5,
        min_calls=10,
    ).start()

    # 示例3：两种策略同时生效（任一满足即告警）
    MongoAlertMonitor(
        boosters=[my_task, other_task], #  如果你要监控所有boosters，可以写 boosters=BoostersManager.get_all_boosters()
        alert_app='feishu',
        webhook_url='https://open.feishu.cn/open-apis/bot/v2/hook/xxx',
        window_seconds=60,
        failure_count=10,     # 报错 >= 10 次
        errors_rate=0.3,      # 或 失败率 >= 30%
        min_calls=5,
    ).start()

    # 示例4：自定义告警通道（发邮件等），继承重写 custom_send_notification
    class EmailAlertMonitor(MongoAlertMonitor):
        def custom_send_notification(self, message: str):
            import smtplib
            from email.mime.text import MIMEText
            msg = MIMEText(message)
            msg['Subject'] = '任务告警'
            msg['From'] = 'bot@example.com'
            msg['To'] = 'ops@example.com'
            with smtplib.SMTP('smtp.example.com') as s:
                s.send_message(msg)

    EmailAlertMonitor(
        boosters=my_task,
        alert_app='custom',
        window_seconds=60,
        failure_count=10,
    ).start()


"""

import datetime
import time
import typing

from funboost.constant import MongoDbName
from funboost.utils.mongo_util import MongoMixin
from funboost.utils.notify_util import Notifier
from funboost.core.loggers import logger_notify
from  funboost.core.funboost_time import FunboostTime
logger = logger_notify


class _QueueAlertState:
    """单个队列的告警状态跟踪"""

    def __init__(self, queue_name: str, table_name: str):
        self.queue_name = queue_name
        self.table_name = table_name
        self.is_alerting = False
        self.last_alert_time = 0.0
        self.last_recovery_time = 0.0


class MongoAlertMonitor(MongoMixin):
    """
    基于 MongoDB 轮询的分布式告警监控

    定期查询 MongoDB 中近 window_seconds 秒内的函数执行记录，
    按报错次数或报错比例判断是否告警，恢复后发送恢复通知。
    支持一次监控多个 booster 队列，每个队列告警状态独立。
    """

    def __init__(self,
                 boosters,
                 alert_app: str = 'wechat',
                 webhook_url: str = None,
                 window_seconds: float = 60,
                 failure_count: int = None,
                 errors_rate: float = None,
                 min_calls: int = 5,
                 poll_interval: float = 10,
                 alert_interval: float = 300,
                 ):
        if failure_count is None and errors_rate is None:
            raise ValueError("failure_count 和 errors_rate 至少设置一个，否则无法触发告警")

        # 支持单个 booster 或列表
        if not isinstance(boosters, (list, tuple)):
            boosters = [boosters]

        self._queue_states: typing.List[_QueueAlertState] = []
        for booster in boosters:
            bp = booster.boost_params
            queue_name = bp.queue_name
            table_name = bp.function_result_status_persistance_conf.table_name or queue_name
            self._queue_states.append(_QueueAlertState(queue_name, table_name))

        self.window_seconds = window_seconds
        self.failure_count = failure_count
        self.errors_rate = errors_rate
        self.min_calls = min_calls
        self.poll_interval = poll_interval
        self.alert_interval = alert_interval

        self._alert_app = alert_app
        self._webhook_url = webhook_url
        notifier_kwargs = {}
        if alert_app == 'dingtalk':
            notifier_kwargs['dingtalk_webhook'] = webhook_url
        elif alert_app == 'wechat':
            notifier_kwargs['wechat_webhook'] = webhook_url
        elif alert_app == 'feishu':
            notifier_kwargs['feishu_webhook'] = webhook_url
        self._notifier = Notifier(**notifier_kwargs)

    def _query_stats(self, queue_state: _QueueAlertState) -> dict:
        """查询最近 window_seconds 秒内、指定 queue_name 的执行统计"""
        col = self.get_mongo_collection(MongoDbName.TASK_STATUS_DB, queue_state.table_name)
        cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(seconds=self.window_seconds)

        pipeline = [
            {'$match': {'queue_name': queue_state.queue_name, 'utime': {'$gte': cutoff}}},
            {'$group': {
                '_id': None,
                'total': {'$sum': 1},
                'failures': {'$sum': {'$cond': [{'$eq': ['$success', False]}, 1, 0]}},
                'successes': {'$sum': {'$cond': [{'$eq': ['$success', True]}, 1, 0]}},
            }},
        ]
        results = list(col.aggregate(pipeline))
        if not results:
            return {'total': 0, 'failures': 0, 'successes': 0, 'rate': 0.0}
        r = results[0]
        total = r['total']
        failures = r['failures']
        return {
            'total': total,
            'failures': failures,
            'successes': r['successes'],
            'rate': failures / total if total > 0 else 0.0,
        }

    def _is_alert_condition_met(self, stats: dict) -> bool:
        """判断是否满足告警条件（任一策略满足即触发）"""
        if self.failure_count is not None:
            if stats['failures'] >= self.failure_count:
                return True
        if self.errors_rate is not None:
            if stats['total'] >= self.min_calls and stats['rate'] >= self.errors_rate:
                return True
        return False

    def _should_send_alert(self, queue_state: _QueueAlertState) -> bool:
        now = time.time()
        if now - queue_state.last_alert_time < self.alert_interval:
            return False
        queue_state.last_alert_time = now
        return True

    def _should_send_recovery(self, queue_state: _QueueAlertState) -> bool:
        now = time.time()
        if now - queue_state.last_recovery_time < self.alert_interval:
            return False
        queue_state.last_recovery_time = now
        return True

    def _format_alert_message(self, queue_name: str, stats: dict) -> str:
        now_str = FunboostTime().get_str()
        lines = [
            "🚨 [告警] 队列任务异常",
            f"队列名: {queue_name}",
            f"统计窗口: 最近 {self.window_seconds} 秒",
            f"失败次数: {stats['failures']}/{stats['total']}",
            f"失败率: {stats['rate']:.2%}",
        ]
        triggers = []
        if self.failure_count is not None and stats['failures'] >= self.failure_count:
            triggers.append(f"报错次数 {stats['failures']} >= {self.failure_count}")
        if self.errors_rate is not None and stats['total'] >= self.min_calls and stats['rate'] >= self.errors_rate:
            triggers.append(f"失败率 {stats['rate']:.2%} >= {self.errors_rate:.0%}")
        lines.append(f"触发条件: {'; '.join(triggers)}")
        lines.append(f"告警时间: {now_str}")
        return '\n'.join(lines)

    def _format_recovery_message(self, queue_name: str, stats: dict) -> str:
        now_str = FunboostTime().get_str()
        return '\n'.join([
            "✅ [恢复] 队列任务已恢复正常",
            f"队列名: {queue_name}",
            f"统计窗口: 最近 {self.window_seconds} 秒",
            f"当前失败: {stats['failures']}/{stats['total']} ({stats['rate']:.2%})",
            f"恢复时间: {now_str}",
        ])

    def custom_send_notification(self, message: str):
        """
        用户自定义告警发送钩子，当 alert_app='custom' 时自动调用。
        子类继承 MongoAlertMonitor 并重写此方法，可实现任意告警方式（邮件、短信、企业内部系统等）。

        示例：
            class MyMonitor(MongoAlertMonitor):
                def custom_send_notification(self, message: str):
                    send_email(to='ops@example.com', subject='任务告警', body=message)
        """
        raise NotImplementedError(
            "alert_app='custom' 时需要继承 MongoAlertMonitor 并重写 custom_send_notification 方法"
        )

    def _send_notification(self, message: str):
        try:
            if self._alert_app == 'dingtalk':
                self._notifier.send_dingtalk(message, add_caller_info=False)
            elif self._alert_app == 'wechat':
                self._notifier.send_wechat(message, add_caller_info=False)
            elif self._alert_app == 'feishu':
                self._notifier.send_feishu(message, add_caller_info=False)
            elif self._alert_app == 'webhook':
                if self._webhook_url:
                    import requests
                    import json
                    requests.post(
                        self._webhook_url,
                        headers={'Content-Type': 'application/json'},
                        data=json.dumps({'content': message}),
                        timeout=10,
                    )
            elif self._alert_app == 'custom':
                self.custom_send_notification(message)
        except Exception as e:
            logger.error(f"Failed to send alert via {self._alert_app}: {type(e).__name__} {e}")

    def _check_queue(self, queue_state: _QueueAlertState):
        """检查单个队列，更新其告警状态"""
        stats = self._query_stats(queue_state)
        alert_triggered = self._is_alert_condition_met(stats)

        if alert_triggered:
            if not queue_state.is_alerting:
                queue_state.is_alerting = True
                logger.warning(
                    f"[{queue_state.queue_name}] ALERTING: "
                    f"failures={stats['failures']}/{stats['total']}, rate={stats['rate']:.2%}"
                )
            if self._should_send_alert(queue_state):
                self._send_notification(self._format_alert_message(queue_state.queue_name, stats))
        else:
            if queue_state.is_alerting:
                queue_state.is_alerting = False
                logger.info(
                    f"[{queue_state.queue_name}] RECOVERED: "
                    f"failures={stats['failures']}/{stats['total']}, rate={stats['rate']:.2%}"
                )
                if self._should_send_recovery(queue_state):
                    self._send_notification(self._format_recovery_message(queue_state.queue_name, stats))

        return stats

    def check_once_all(self):
        """对所有监控队列各执行一次检查，由 scheduler 定时调用。"""
        for queue_state in self._queue_states:
            try:
                self._check_queue(queue_state)
            except Exception as e:
                logger.error(f"[{queue_state.queue_name}] check error: {type(e).__name__} {e}")

    def start(self):
        """
        向 funboost_aps_scheduler 注册 interval 定时任务，每隔 poll_interval 秒对所有队列执行一次检查。
        若 scheduler 尚未启动则自动启动；同一个 MongoAlertMonitor 实例重复调用 start() 只注册一次。
        """
        from funboost.timing_job.timing_job_base import funboost_aps_scheduler

        queue_names = [qs.queue_name for qs in self._queue_states]
        strategy_desc = []
        if self.failure_count is not None:
            strategy_desc.append(f"failure_count>={self.failure_count}")
        if self.errors_rate is not None:
            strategy_desc.append(f"errors_rate>={self.errors_rate} (min_calls={self.min_calls})")
        logger.info(
            f"MongoAlertMonitor starting: queues={queue_names}, "
            f"window={self.window_seconds}s, strategy=[{', '.join(strategy_desc)}], "
            f"poll_interval={self.poll_interval}s, alert_app={self._alert_app}, "
            f"alert_interval={self.alert_interval}s"
        )

        job_id = f'mongo_alert_monitor__{id(self)}'
        funboost_aps_scheduler.add_job(
            self.check_once_all,
            trigger='interval',
            seconds=self.poll_interval,
            id=job_id,
            replace_existing=True,
            max_instances=1,
        )
        logger.info(f"MongoAlertMonitor job registered: id={job_id}, queues={queue_names}, interval={self.poll_interval}s")

        if not funboost_aps_scheduler.running:
            funboost_aps_scheduler.start()
