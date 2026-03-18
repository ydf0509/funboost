# -*- coding: utf-8 -*-
# @Author  : AI Assistant
# @Time    : 2026/3/15
"""
告警通知消费者 Mixin (Alert Notifier Consumer Mixin)

功能：当消费函数失败达到阈值时自动发送告警通知，错误恢复后自动发送恢复通知。
仅做告警，不实现熔断（不阻塞消费、不降级）。

=== 两种触发策略 ===

1. consecutive（连续失败计数，默认）：
   连续失败 >= failure_threshold 时触发告警，任何一次成功重置计数。

2. rate（错误率滑动窗口）：
   在 period 秒的滑动窗口内，当调用次数 >= min_calls 且
   错误率 >= errors_rate 时触发告警。

=== 告警通道 ===

支持五种告警通道（选其一）：
- dingtalk:  钉钉机器人
- wechat:    企业微信机器人
- feishu:    飞书机器人
- webhook:   自定义 Webhook（POST JSON: {"content": "消息内容"}）
- custom:    用户自定义，继承 AlertNotifierConsumerMixin 并重写 custom_send_notification 方法

=== 去重与恢复 ===

- alert_interval:  告警去重窗口秒数，同一队列在此时间内不重复告警
- 错误恢复后（从告警状态变为正常状态）自动发送恢复通知

=== user_options['alert_options'] 参数说明 ===

    strategy:           'consecutive'(连续失败计数) 或 'rate'(错误率滑动窗口)，默认 'consecutive'

    failure_threshold:  连续失败次数阈值（consecutive 策略），默认 5
    errors_rate:        错误率阈值 0.0~1.0（rate 策略），默认 0.5
    period:             统计窗口秒数（rate 策略），默认 60.0
    min_calls:          窗口内最少调用数才评估（rate 策略），默认 5

    alert_app:          告警通道，可选值: 'dingtalk', 'wechat', 'feishu', 'webhook', 'custom'，默认 'wechat'
                        设为 'custom' 时需继承 AlertNotifierConsumerMixin 并重写 custom_send_notification 方法
    webhook_url:        对应告警通道的 Webhook 地址（必填）

    alert_interval:     告警去重间隔秒数，同一队列在此时间内不重复发送告警，默认 300（5分钟）
    exceptions:         要跟踪的异常类型元组（None 跟踪所有），默认 None

=== 用法示例 ===

    from funboost import boost, BoosterParams, BrokerEnum
    from funboost.contrib.override_publisher_consumer_cls.alert_notifier_mixin import (
        AlertNotifierConsumerMixin,
        AlertNotifierBoosterParams,
    )

    # 方式1：连续失败策略 + 企业微信告警（最简用法）
    @boost(AlertNotifierBoosterParams(
        queue_name='my_task',
        broker_kind=BrokerEnum.REDIS,
        user_options={
            'alert_options': {
                'failure_threshold': 5,
                'alert_app': 'wechat',
                'webhook_url': 'https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=your_key',
            },
        },
    ))
    def my_task(x):
        return call_external_api(x)

    # 方式2：错误率策略 + 钉钉告警
    @boost(BoosterParams(
        queue_name='my_task_rate',
        broker_kind=BrokerEnum.REDIS,
        consumer_override_cls=AlertNotifierConsumerMixin,
        user_options={
            'alert_options': {
                'strategy': 'rate',
                'errors_rate': 0.5,
                'period': 60,
                'min_calls': 10,
                'alert_app': 'dingtalk',
                'webhook_url': 'https://oapi.dingtalk.com/robot/send?access_token=your_token',
                'alert_interval': 600,
            },
        },
    ))
    def my_task_rate(x):
        return call_external_api(x)

"""

import collections
import threading
import time
import typing
import datetime

from funboost.consumers.base_consumer import AbstractConsumer
from funboost.core.func_params_model import BoosterParams
from funboost.core.function_result_status_saver import FunctionResultStatus
from funboost.utils.notify_util import Notifier
from funboost.concurrent_pool.async_helper import simple_run_in_executor

class AlertState:
    NORMAL = 'normal'
    ALERTING = 'alerting'


def _parse_exception_names(exceptions) -> typing.Optional[set]:
    if exceptions is None:
        return None
    names = set()
    for exc in exceptions:
        if isinstance(exc, str):
            names.add(exc)
        elif isinstance(exc, type) and issubclass(exc, BaseException):
            names.add(exc.__name__)
        else:
            names.add(str(exc))
    return names


class AlertTracker:
    """
    线程安全的告警状态跟踪器（本地内存）

    支持两种触发策略：
    - consecutive: 连续失败 >= failure_threshold 时触发告警
    - rate: 滑动窗口内错误率 >= errors_rate 且调用数 >= min_calls 时触发告警

    成功时重置连续失败计数。当从 ALERTING 状态恢复到 NORMAL 时，通知上层。
    """

    def __init__(self,
                 strategy: str = 'consecutive',
                 failure_threshold: int = 5,
                 errors_rate: float = 0.5,
                 period: float = 60.0,
                 min_calls: int = 5,
                 ):
        self.strategy = strategy
        self.failure_threshold = failure_threshold
        self.errors_rate = errors_rate
        self.period = period
        self.min_calls = min_calls

        self._state = AlertState.NORMAL
        self._consecutive_failure_count = 0
        self._total_failure_count = 0
        self._lock = threading.Lock()

        self._call_records: typing.Deque[typing.Tuple[float, bool]] = collections.deque()

    @property
    def state(self) -> str:
        with self._lock:
            return self._state

    @property
    def consecutive_failure_count(self) -> int:
        with self._lock:
            return self._consecutive_failure_count

    @property
    def total_failure_count(self) -> int:
        with self._lock:
            return self._total_failure_count

    def get_error_rate_info(self) -> dict:
        with self._lock:
            self._cleanup_old_records_unlocked()
            total = len(self._call_records)
            if total == 0:
                return {'total': 0, 'failures': 0, 'rate': 0.0}
            failures = sum(1 for _, success in self._call_records if not success)
            return {'total': total, 'failures': failures, 'rate': failures / total}

    def record_success(self) -> typing.Tuple[str, str]:
        """记录成功，返回 (old_state, new_state)"""
        with self._lock:
            old_state = self._state
            self._consecutive_failure_count = 0
            if self.strategy == 'rate':
                self._call_records.append((time.time(), True))
                self._cleanup_old_records_unlocked()

            if old_state == AlertState.ALERTING:
                if self.strategy == 'consecutive':
                    self._state = AlertState.NORMAL
                elif self.strategy == 'rate':
                    if not self._should_alert_by_rate_unlocked():
                        self._state = AlertState.NORMAL
            return old_state, self._state

    def record_failure(self) -> typing.Tuple[str, str]:
        """记录失败，返回 (old_state, new_state)"""
        with self._lock:
            old_state = self._state
            self._consecutive_failure_count += 1
            self._total_failure_count += 1

            if self.strategy == 'consecutive':
                if self._consecutive_failure_count >= self.failure_threshold:
                    self._state = AlertState.ALERTING
            elif self.strategy == 'rate':
                self._call_records.append((time.time(), False))
                self._cleanup_old_records_unlocked()
                if self._should_alert_by_rate_unlocked():
                    self._state = AlertState.ALERTING
            return old_state, self._state

    def _should_alert_by_rate_unlocked(self) -> bool:
        total = len(self._call_records)
        if total < self.min_calls:
            return False
        failures = sum(1 for _, success in self._call_records if not success)
        return (failures / total) >= self.errors_rate

    def _cleanup_old_records_unlocked(self):
        cutoff = time.time() - self.period
        while self._call_records and self._call_records[0][0] < cutoff:
            self._call_records.popleft()


class AlertNotifierConsumerMixin(AbstractConsumer):
    """
    告警通知消费者 Mixin

    通过 user_options['alert_options'] 配置所有参数，详见模块文档。
    仅监控并告警，不实现熔断逻辑。
    """

    def custom_init(self):
        super().custom_init()

        user_options = self.consumer_params.user_options
        alert_options = user_options.get('alert_options', {})
        strategy = alert_options.get('strategy', 'consecutive')

        self._alert_tracker = AlertTracker(
            strategy=strategy,
            failure_threshold=alert_options.get('failure_threshold', 5),
            errors_rate=alert_options.get('errors_rate', 0.5),
            period=alert_options.get('period', 60.0),
            min_calls=alert_options.get('min_calls', 5),
        )

        self._alert_app: str = alert_options.get('alert_app', 'wechat')
        self._alert_webhook_url = alert_options.get('webhook_url', None)

        notifier_kwargs = {}
        if self._alert_app == 'dingtalk':
            notifier_kwargs['dingtalk_webhook'] = self._alert_webhook_url
        elif self._alert_app == 'wechat':
            notifier_kwargs['wechat_webhook'] = self._alert_webhook_url
        elif self._alert_app == 'feishu':
            notifier_kwargs['feishu_webhook'] = self._alert_webhook_url
        self._alert_notifier = Notifier(**notifier_kwargs)

        self._alert_interval = alert_options.get('alert_interval', 300)
        self._last_alert_time = 0.0
        self._last_recovery_time = 0.0
        self._alert_time_lock = threading.Lock()

        self._alert_tracked_exception_names = _parse_exception_names(
            alert_options.get('exceptions', None)
        )

        self.logger.info(
            f"AlertNotifier initialized: strategy={strategy}, "
            f"{'failure_threshold=' + str(alert_options.get('failure_threshold', 5)) if strategy == 'consecutive' else 'errors_rate=' + str(alert_options.get('errors_rate', 0.5)) + ', period=' + str(alert_options.get('period', 60.0)) + 's, min_calls=' + str(alert_options.get('min_calls', 5))}, "
            f"alert_app={self._alert_app}, alert_interval={self._alert_interval}s, "
            f"exceptions={self._alert_tracked_exception_names or 'all'}"
        )

    def _is_alert_tracked_exception(self, function_result_status: FunctionResultStatus) -> bool:
        if self._alert_tracked_exception_names is None:
            return True
        if not function_result_status.exception_type:
            return True
        return function_result_status.exception_type in self._alert_tracked_exception_names

    def _should_send_alert(self) -> bool:
        """检查是否在去重窗口外，可以发送告警"""
        with self._alert_time_lock:
            now = time.time()
            if now - self._last_alert_time < self._alert_interval:
                return False
            self._last_alert_time = now
            return True

    def _should_send_recovery(self) -> bool:
        """检查是否在去重窗口外，可以发送恢复通知"""
        with self._alert_time_lock:
            now = time.time()
            if now - self._last_recovery_time < self._alert_interval:
                return False
            self._last_recovery_time = now
            return True

    def _format_alert_message(self, info_dict: dict) -> str:
        now_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        msg_lines = [
            "🚨 [告警] 队列任务异常",
            f"队列名: {info_dict['queue_name']}",
            f"策略: {info_dict['strategy']}",
        ]
        if info_dict['strategy'] == 'consecutive':
            msg_lines.append(f"连续失败次数: {info_dict['consecutive_failure_count']}")
        if 'error_rate_info' in info_dict:
            ri = info_dict['error_rate_info']
            msg_lines.append(f"错误率: {ri['rate']:.2%} ({ri['failures']}/{ri['total']})")
        msg_lines.append(f"累计失败次数: {info_dict['total_failure_count']}")
        msg_lines.append(f"告警时间: {now_str}")
        return '\n'.join(msg_lines)

    def _format_recovery_message(self, info_dict: dict) -> str:
        now_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        msg_lines = [
            "✅ [恢复] 队列任务已恢复正常",
            f"队列名: {info_dict['queue_name']}",
            f"策略: {info_dict['strategy']}",
            f"恢复时间: {now_str}",
        ]
        return '\n'.join(msg_lines)

    def custom_send_notification(self, message: str):
        """
        用户自定义告警发送钩子，当 alert_app='custom' 时自动调用。
        继承 AlertNotifierConsumerMixin 并重写此方法，可实现任意告警方式（邮件、短信、企业内部系统等）。

        示例：
            class EmailAlertConsumer(AlertNotifierConsumerMixin):
                def custom_send_notification(self, message: str):
                    send_email(to='ops@example.com', subject='任务告警', body=message)

            @boost(BoosterParams(
                queue_name='my_task',
                consumer_override_cls=EmailAlertConsumer,
                user_options={'alert_options': {'alert_app': 'custom', 'failure_threshold': 5}},
            ))
            def my_task(x):
                ...
        """
        raise NotImplementedError(
            "alert_app='custom' 时需要继承 AlertNotifierConsumerMixin 并重写 custom_send_notification 方法"
        )

    def _send_notification(self, message: str):
        """通过配置的告警通道发送通知"""
        try:
            if self._alert_app == 'dingtalk':
                self._alert_notifier.send_dingtalk(message, add_caller_info=False)
            elif self._alert_app == 'wechat':
                self._alert_notifier.send_wechat(message, add_caller_info=False)
            elif self._alert_app == 'feishu':
                self._alert_notifier.send_feishu(message, add_caller_info=False)
            elif self._alert_app == 'webhook':
                if self._alert_webhook_url:
                    import requests
                    import json
                    requests.post(
                        self._alert_webhook_url,
                        headers={'Content-Type': 'application/json'},
                        data=json.dumps({'content': message}),
                        timeout=10,
                    )
            elif self._alert_app == 'custom':
                self.custom_send_notification(message)
            else:
                self.logger.warning(f"Unknown alert_app: {self._alert_app}, supported: dingtalk, wechat, feishu, webhook, custom")
        except Exception as e:
            self.logger.error(f"Failed to send alert via {self._alert_app}: {type(e).__name__} {e}")

    def _frame_custom_record_process_info_func(
            self, current_function_result_status: FunctionResultStatus, kw: dict):
        super()._frame_custom_record_process_info_func(
            current_function_result_status, kw)
        
        """
        如果任务被 requeue、发到死信队列、或被远程 kill，这些不是真正的业务失败，可以不计入告警计数，否则会导致误告警。
        """
        if (current_function_result_status._has_requeue
                or current_function_result_status._has_to_dlx_queue
                or current_function_result_status._has_kill_task):
            return

        if current_function_result_status.success:
            old_state, new_state = self._alert_tracker.record_success()
        else:
            if not self._is_alert_tracked_exception(current_function_result_status):
                return
            old_state, new_state = self._alert_tracker.record_failure()

        info_dict = {
            'queue_name': self.queue_name,
            'strategy': self._alert_tracker.strategy,
            'consecutive_failure_count': self._alert_tracker.consecutive_failure_count,
            'total_failure_count': self._alert_tracker.total_failure_count,
        }
        if self._alert_tracker.strategy == 'rate':
            info_dict['error_rate_info'] = self._alert_tracker.get_error_rate_info()

        # 进入告警状态 → 发送告警
        if new_state == AlertState.ALERTING:
            if self._should_send_alert():
                msg = self._format_alert_message(info_dict)
                self.logger.warning(
                    f"AlertNotifier triggered for queue [{self.queue_name}], "
                    f"consecutive_failures={info_dict['consecutive_failure_count']}, "
                    f"total_failures={info_dict['total_failure_count']}"
                )
                self._send_notification(msg)
            elif old_state != AlertState.ALERTING:
                self.logger.warning(
                    f"AlertNotifier triggered for queue [{self.queue_name}], "
                    f"but suppressed by alert_interval={self._alert_interval}s"
                )

        # 从告警状态恢复 → 发送恢复通知
        if old_state == AlertState.ALERTING and new_state == AlertState.NORMAL:
            if self._should_send_recovery():
                msg = self._format_recovery_message(info_dict)
                self.logger.info(
                    f"AlertNotifier recovered for queue [{self.queue_name}]"
                )
                self._send_notification(msg)
    
    async def _aio_frame_custom_record_process_info_func(self, current_function_result_status: FunctionResultStatus, kw: dict):
        await super()._aio_frame_custom_record_process_info_func(current_function_result_status, kw)
        await simple_run_in_executor(self._frame_custom_record_process_info_func, current_function_result_status, kw)


class AlertNotifierBoosterParams(BoosterParams):
    """
    预配置了告警通知的 BoosterParams

    使用示例：

        # 连续失败5次告警 + 企业微信
        @boost(AlertNotifierBoosterParams(
            queue_name='my_task',
            broker_kind=BrokerEnum.REDIS,
            user_options={
                'alert_options': {
                    'failure_threshold': 5,
                    'alert_app': 'wechat',
                    'webhook_url': 'https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx',
                },
            },
        ))
        def my_task(x):
            return call_external_api(x)

        # 错误率策略 + 钉钉
        @boost(AlertNotifierBoosterParams(
            queue_name='my_task_rate',
            broker_kind=BrokerEnum.REDIS,
            user_options={
                'alert_options': {
                    'strategy': 'rate',
                    'errors_rate': 0.5,
                    'period': 60,
                    'min_calls': 10,
                    'alert_app': 'dingtalk',
                    'webhook_url': 'https://oapi.dingtalk.com/robot/send?access_token=xxx',
                    'alert_interval': 600,
                },
            },
        ))
        def my_task_rate(x):
            return call_external_api(x)
    """
    consumer_override_cls: typing.Optional[typing.Type] = AlertNotifierConsumerMixin
    user_options: dict = {
        'alert_options': {
            'strategy': 'consecutive',
            'failure_threshold': 5,
            'alert_app': 'wechat',
            'alert_interval': 300,
        },
    }


__all__ = [
    'AlertState',
    'AlertTracker',
    'AlertNotifierConsumerMixin',
    'AlertNotifierBoosterParams',
]
