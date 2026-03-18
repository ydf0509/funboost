# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2026/3/8
"""
熔断器消费者 Mixin (Circuit Breaker Consumer Mixin)

功能：当消费函数失败达到阈值时自动熔断，熔断期间阻塞等待恢复或执行 fallback 降级函数。

=== 三态状态机 ===

CLOSED（关闭/正常）→ 触发条件满足 → OPEN（打开/熔断）
OPEN → 经过 recovery_timeout 秒 → HALF_OPEN（半开/试探）
HALF_OPEN → 连续成功 >= half_open_max_calls → CLOSED
HALF_OPEN → 任意一次失败 → OPEN
HALF_OPEN → 超过 half_open_ttl → OPEN（可选）

=== 两种触发策略 ===

1. consecutive（连续失败计数，默认）：
   连续失败 >= failure_threshold 时触发熔断，任何一次成功重置计数。

2. rate（错误率滑动窗口）：
   在 period 秒的滑动窗口内，当调用次数 >= min_calls 且
   错误率 >= errors_rate 时触发熔断。

=== 两种计数后端 ===

1. local（本地内存，默认）：
   单进程内有效，使用 threading.Lock 保证线程安全。

2. redis（Redis 分布式）：
   多进程/多机器共享熔断状态，同一队列的所有消费者共享计数。

=== 两种熔断行为 ===

1. 阻塞模式（默认，无 fallback）：
   熔断期间阻塞 _submit_task，消息留在中间件中等待恢复。

2. Fallback 模式（指定 fallback）：
   熔断期间用 fallback 函数替代原函数执行。

=== user_options['circuit_breaker_options'] 参数说明 ===

所有熔断器参数放在 user_options 的 'circuit_breaker_options' 字典中，
避免与其他 mixin 的 user_options 一级 key 冲突（例如 period 可能与 PeriodicQuotaConsumerMixin 冲突）。

    strategy:               'consecutive'(连续失败计数) 或 'rate'(错误率滑动窗口)，默认 'consecutive'
    counter_backend:        'local'(本地内存) 或 'redis'(Redis 分布式)，默认 'local'

    failure_threshold:      连续失败次数阈值（consecutive 策略），默认 5
    errors_rate:            错误率阈值 0.0~1.0（rate 策略），默认 0.5
    period:                 统计窗口秒数（rate 策略），默认 60.0
    min_calls:              窗口内最少调用数才评估（rate 策略），默认 5

    recovery_timeout:       熔断后等待恢复秒数（= cashews 的 ttl），默认 60.0
    half_open_max_calls:    半开状态需连续成功次数，默认 3
    half_open_ttl:          半开状态超时秒数，超时后重新进入 OPEN（None 则不超时），默认 None

    exceptions:             要跟踪的异常类型元组（None 跟踪所有），默认 None
    fallback:               降级函数（None 则阻塞模式），默认 None

=== 钩子方法（子类重写） ===

    _on_circuit_open(self,info_dict):   熔断触发时调用，可发送微信/钉钉/邮件告警
    _on_circuit_close(self,info_dict):  熔断恢复时调用，可发送恢复通知

=== 用法示例 ===

    from funboost import boost, BoosterParams, BrokerEnum
    from funboost.contrib.override_publisher_consumer_cls.circuit_breaker_mixin import (
        CircuitBreakerConsumerMixin,
        CircuitBreakerBoosterParams,
    )

    # 方式1：连续失败策略 + 本地计数（最简用法）
    @boost(CircuitBreakerBoosterParams(
        queue_name='my_task',
        broker_kind=BrokerEnum.REDIS,
        user_options={
            'circuit_breaker_options': {
                'failure_threshold': 5,
                'recovery_timeout': 60,
            },
        },
    ))
    def my_task(x):
        return call_external_api(x)

    # 方式2：错误率策略 + Redis 分布式计数
    @boost(BoosterParams(
        queue_name='my_task_rate',
        broker_kind=BrokerEnum.REDIS,
        consumer_override_cls=CircuitBreakerConsumerMixin,
        user_options={
            'circuit_breaker_options': {
                'strategy': 'rate',
                'counter_backend': 'redis',
                'errors_rate': 0.5,
                'period': 60,
                'min_calls': 10,
                'recovery_timeout': 30,
                'exceptions': (ConnectionError, TimeoutError),
            },
        },
    ))
    def my_task_rate(x):
        return call_external_api(x)

    # 方式3：继承重写钩子，熔断/恢复时发送告警
    class MyAlertCircuitBreakerMixin(CircuitBreakerConsumerMixin):
        def _on_circuit_open(self, info_dict):
            send_dingtalk(f'[告警] 队列 {info_dict["queue_name"]} 已熔断! 失败{info_dict["failure_count"]}次')

        def _on_circuit_close(self, info_dict):
            send_wechat(f'[恢复] 队列 {info_dict["queue_name"]} 已恢复正常')

    @boost(BoosterParams(
        queue_name='my_task_alert',
        broker_kind=BrokerEnum.REDIS,
        consumer_override_cls=MyAlertCircuitBreakerMixin,
        user_options={
            'circuit_breaker_options': {
                'failure_threshold': 5,
                'recovery_timeout': 60,
            },
        },
    ))
    def my_task_alert(x):
        return call_external_api(x)

    # 方式4：Fallback 降级
    def my_fallback(x):
        return {'status': 'degraded', 'x': x}

    @boost(BoosterParams(
        queue_name='my_task_fb',
        broker_kind=BrokerEnum.REDIS,
        consumer_override_cls=CircuitBreakerConsumerMixin,
        user_options={
            'circuit_breaker_options': {
                'failure_threshold': 3,
                'recovery_timeout': 30,
                'fallback': my_fallback,
            },
        },
    ))
    def my_task_fb(x):
        return call_external_api(x)
"""

"""
Funboost 的熔断器实现达到了顶流熔断器框架的水平，它遵循了业界通用的三态状态机模型，支持两种触发策略，
提供了完善的配置项和扩展钩子，并且额外支持分布式计数，非常适合构建高可用的分布式系统。
配置方式清晰直观，开发者可以像使用 Hystrix 或 resilience4j 一样轻松驾驭它。
"""

"""
funboost 支持自动熔断管理，也支持手动熔断管理

手动熔断管理:
由你自己人工判断并且手动操作是需要否暂停和恢复消费。
你主动发现大规模报错 或者通过promethus告警发现 大规模报错后，可以人工暂停某个队列的消费。
- 就是可以通过对 redis的queue_name 设置 pause 标志，
- 也可以通过faas接口 /funboost/pause_consume 和 /funboost/resume_consume 来暂停和恢复拉取消息
- 也可以通过 funboost web manager 网页来设置暂停和恢复

自动熔断管理：
通过 CircuitBreakerConsumerMixin，智能自动进进入熔断和半开和恢复三种状态。
"""



import asyncio
import collections
import inspect
import threading
import time
import typing
import uuid

from funboost.consumers.base_consumer import AbstractConsumer
from funboost.core.func_params_model import BoosterParams
from funboost.core.function_result_status_saver import FunctionResultStatus
from funboost.concurrent_pool.async_helper import simple_run_in_executor


class CircuitState:
    CLOSED = 'closed'
    OPEN = 'open'
    HALF_OPEN = 'half_open'


def _parse_exception_names(exceptions) -> typing.Optional[set]:
    """将异常类型元组转换为异常类名字符串集合，None 表示跟踪所有异常"""
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


# ================================================================
# 本地内存熔断器
# ================================================================

class CircuitBreaker:
    """
    线程安全的三态熔断器（本地内存计数）

    支持两种触发策略：
    - consecutive: 连续失败 >= failure_threshold 时熔断
    - rate: 滑动窗口内错误率 >= errors_rate 且调用数 >= min_calls 时熔断

    HALF_OPEN 状态的逻辑与策略无关：连续成功 >= half_open_max_calls 则 CLOSED，任意失败则 OPEN。
    """

    def __init__(self,
                 strategy: str = 'consecutive',
                 failure_threshold: int = 5,
                 errors_rate: float = 0.5,
                 period: float = 60.0,
                 min_calls: int = 5,
                 recovery_timeout: float = 60.0,
                 half_open_max_calls: int = 3,
                 half_open_ttl: float = None,
                 ):
        self.strategy = strategy
        self.failure_threshold = failure_threshold
        self.errors_rate = errors_rate
        self.period = period
        self.min_calls = min_calls
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls
        self.half_open_ttl = half_open_ttl

        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._half_open_success_count = 0
        self._last_open_time = 0.0
        self._last_half_open_time = 0.0
        self._lock = threading.Lock()

        # rate 策略的滑动窗口：(timestamp, is_success)
        self._call_records: typing.Deque[typing.Tuple[float, bool]] = collections.deque()

    @property
    def state(self) -> str:
        with self._lock:
            return self._get_state_unlocked()

    def _get_state_unlocked(self) -> str:
        now = time.time()
        if self._state == CircuitState.OPEN:
            if now - self._last_open_time >= self.recovery_timeout:
                self._state = CircuitState.HALF_OPEN
                self._half_open_success_count = 0
                self._last_half_open_time = now
        elif self._state == CircuitState.HALF_OPEN and self.half_open_ttl is not None:
            if now - self._last_half_open_time >= self.half_open_ttl:
                self._state = CircuitState.OPEN
                self._last_open_time = now
        return self._state

    @property
    def failure_count(self) -> int:
        with self._lock:
            return self._failure_count

    def time_until_half_open(self) -> float:
        with self._lock:
            if self._state != CircuitState.OPEN:
                return 0.0
            remaining = self.recovery_timeout - (time.time() - self._last_open_time)
            return max(0.0, remaining)

    def get_error_rate_info(self) -> dict:
        """获取当前滑动窗口的错误率信息（仅 rate 策略有意义）"""
        with self._lock:
            self._cleanup_old_records_unlocked()
            total = len(self._call_records)
            if total == 0:
                return {'total': 0, 'failures': 0, 'rate': 0.0}
            failures = sum(1 for _, success in self._call_records if not success)
            return {'total': total, 'failures': failures, 'rate': failures / total}

    def record_success(self) -> str:
        with self._lock:
            state = self._get_state_unlocked()
            if state == CircuitState.CLOSED:
                if self.strategy == 'consecutive':
                    self._failure_count = 0
                elif self.strategy == 'rate':
                    self._call_records.append((time.time(), True))
                    self._cleanup_old_records_unlocked()
            elif state == CircuitState.HALF_OPEN:
                self._half_open_success_count += 1
                if self._half_open_success_count >= self.half_open_max_calls:
                    self._state = CircuitState.CLOSED
                    self._failure_count = 0
                    self._half_open_success_count = 0
                    self._call_records.clear()
            return self._state

    def record_failure(self) -> str:
        with self._lock:
            state = self._get_state_unlocked()
            if state == CircuitState.CLOSED:
                if self.strategy == 'consecutive':
                    self._failure_count += 1
                    if self._failure_count >= self.failure_threshold:
                        self._transition_to_open_unlocked()
                elif self.strategy == 'rate':
                    self._call_records.append((time.time(), False))
                    self._cleanup_old_records_unlocked()
                    self._failure_count += 1
                    if self._should_open_by_rate_unlocked():
                        self._transition_to_open_unlocked()
            elif state == CircuitState.HALF_OPEN:
                self._transition_to_open_unlocked()
                self._half_open_success_count = 0
            return self._state

    def _transition_to_open_unlocked(self):
        self._state = CircuitState.OPEN
        self._last_open_time = time.time()

    def _should_open_by_rate_unlocked(self) -> bool:
        total = len(self._call_records)
        if total < self.min_calls:
            return False
        failures = sum(1 for _, success in self._call_records if not success)
        return (failures / total) >= self.errors_rate

    def _cleanup_old_records_unlocked(self):
        cutoff = time.time() - self.period
        while self._call_records and self._call_records[0][0] < cutoff:
            self._call_records.popleft()


# ================================================================
# Redis 分布式熔断器
# ================================================================

class RedisCircuitBreaker:
    """
    Redis 分布式三态熔断器

    多进程/多机器共享熔断状态，同一 queue_name 的所有消费者共享计数。
    使用 Redis hash 存储状态，sorted set 存储滑动窗口调用记录。

    注意：Redis 操作不使用 Lua 脚本，在极高并发下存在微小的竞态窗口，
    但对于熔断器来说这些竞态是良性的（最多延迟 1-2 次调用触发/恢复）。
    """

    HASH_KEY_PREFIX = 'funboost:circuit_breaker:'
    CALLS_KEY_SUFFIX = ':calls'

    def __init__(self,
                 queue_name: str,
                 strategy: str = 'consecutive',
                 failure_threshold: int = 5,
                 errors_rate: float = 0.5,
                 period: float = 60.0,
                 min_calls: int = 5,
                 recovery_timeout: float = 60.0,
                 half_open_max_calls: int = 3,
                 half_open_ttl: float = None,
                 ):
        self.queue_name = queue_name
        self.strategy = strategy
        self.failure_threshold = failure_threshold
        self.errors_rate = errors_rate
        self.period = period
        self.min_calls = min_calls
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls
        self.half_open_ttl = half_open_ttl

        from funboost.utils.redis_manager import RedisMixin
        self._redis = RedisMixin().redis_db_frame

        self._hash_key = f'{self.HASH_KEY_PREFIX}{queue_name}'
        self._calls_key = f'{self._hash_key}{self.CALLS_KEY_SUFFIX}'

        self._init_redis_state()

    def _hash_ttl_seconds(self) -> int:
        """hash key 的最大 TTL：熔断恢复后一段时间没有流量则自动清理"""
        return int(self.recovery_timeout * 10 + self.period * 2 + 3600)

    def _init_redis_state(self):
        defaults = {
            'state': CircuitState.CLOSED,
            'failure_count': '0',
            'half_open_success_count': '0',
            'last_open_time': '0',
            'last_half_open_time': '0',
        }
        for field, value in defaults.items():
            self._redis.hsetnx(self._hash_key, field, value)
        # 设置兜底 TTL，防止进程异常退出后 key 永久残留
        self._redis.expire(self._hash_key, self._hash_ttl_seconds())

    def _get_hash_fields(self) -> dict:
        data = self._redis.hgetall(self._hash_key)
        # hgetall 返回 {bytes: bytes}，需要先 decode
        decoded = {
            k.decode() if isinstance(k, bytes) else k: v.decode() if isinstance(v, bytes) else v
            for k, v in data.items()
        }
        return {
            'state': decoded.get('state', CircuitState.CLOSED),
            'failure_count': int(decoded.get('failure_count', '0')),
            'half_open_success_count': int(decoded.get('half_open_success_count', '0')),
            'last_open_time': float(decoded.get('last_open_time', '0')),
            'last_half_open_time': float(decoded.get('last_half_open_time', '0')),
        }

    @property
    def state(self) -> str:
        fields = self._get_hash_fields()
        now = time.time()
        current_state = fields['state']

        if current_state == CircuitState.OPEN:
            if now - fields['last_open_time'] >= self.recovery_timeout:
                self._redis.hset(self._hash_key, mapping={
                    'state': CircuitState.HALF_OPEN,
                    'half_open_success_count': '0',
                    'last_half_open_time': str(now),
                })
                return CircuitState.HALF_OPEN
        elif current_state == CircuitState.HALF_OPEN and self.half_open_ttl is not None:
            if now - fields['last_half_open_time'] >= self.half_open_ttl:
                self._redis.hset(self._hash_key, mapping={
                    'state': CircuitState.OPEN,
                    'last_open_time': str(now),
                })
                return CircuitState.OPEN
        return current_state

    @property
    def failure_count(self) -> int:
        val = self._redis.hget(self._hash_key, 'failure_count')
        if val is None:
            return 0
        return int(val.decode() if isinstance(val, bytes) else val)

    def time_until_half_open(self) -> float:
        fields = self._get_hash_fields()
        if fields['state'] != CircuitState.OPEN:
            return 0.0
        remaining = self.recovery_timeout - (time.time() - fields['last_open_time'])
        return max(0.0, remaining)

    @staticmethod
    def _is_failure_member(m) -> bool:
        """判断 sorted set 成员是否为失败记录（兼容 bytes/str）"""
        if isinstance(m, bytes):
            return m.endswith(b':0')
        return str(m).endswith(':0')

    def get_error_rate_info(self) -> dict:
        self._cleanup_old_calls()
        members = self._redis.zrangebyscore(self._calls_key, time.time() - self.period, '+inf')
        total = len(members)
        if total == 0:
            return {'total': 0, 'failures': 0, 'rate': 0.0}
        failures = sum(1 for m in members if self._is_failure_member(m))
        return {'total': total, 'failures': failures, 'rate': failures / total}

    def record_success(self) -> str:
        current_state = self.state

        if current_state == CircuitState.CLOSED:
            if self.strategy == 'consecutive':
                self._redis.hset(self._hash_key, 'failure_count', '0')
            elif self.strategy == 'rate':
                self._redis.zadd(self._calls_key, {f'{uuid.uuid4().hex}:1': time.time()})
                self._cleanup_old_calls()

        elif current_state == CircuitState.HALF_OPEN:
            new_count = self._redis.hincrby(self._hash_key, 'half_open_success_count', 1)
            if new_count >= self.half_open_max_calls:
                self._redis.hset(self._hash_key, mapping={
                    'state': CircuitState.CLOSED,
                    'failure_count': '0',
                    'half_open_success_count': '0',
                })
                self._redis.expire(self._hash_key, self._hash_ttl_seconds())
                self._redis.delete(self._calls_key)
                return CircuitState.CLOSED

        return self.state

    def record_failure(self) -> str:
        current_state = self.state

        if current_state == CircuitState.CLOSED:
            if self.strategy == 'consecutive':
                new_count = self._redis.hincrby(self._hash_key, 'failure_count', 1)
                if new_count >= self.failure_threshold:
                    self._transition_to_open()
            elif self.strategy == 'rate':
                self._redis.zadd(self._calls_key, {f'{uuid.uuid4().hex}:0': time.time()})
                self._redis.hincrby(self._hash_key, 'failure_count', 1)
                self._cleanup_old_calls()
                if self._should_open_by_rate():
                    self._transition_to_open()

        elif current_state == CircuitState.HALF_OPEN:
            self._transition_to_open()
            self._redis.hset(self._hash_key, 'half_open_success_count', '0')

        return self.state

    def _transition_to_open(self):
        now = time.time()
        self._redis.hset(self._hash_key, mapping={
            'state': CircuitState.OPEN,
            'last_open_time': str(now),
        })
        self._redis.expire(self._hash_key, self._hash_ttl_seconds())
        # 进入 OPEN 后清理 sorted set 中已过期的旧记录，释放内存
        self._cleanup_old_calls()

    def _should_open_by_rate(self) -> bool:
        members = self._redis.zrangebyscore(
            self._calls_key, time.time() - self.period, '+inf'
        )
        total = len(members)
        if total < self.min_calls:
            return False
        failures = sum(1 for m in members if self._is_failure_member(m))
        return (failures / total) >= self.errors_rate

    def _cleanup_old_calls(self):
        cutoff = time.time() - self.period
        self._redis.zremrangebyscore(self._calls_key, '-inf', cutoff)
        # sorted set 的 TTL = period 的 2 倍兜底，防止极端情况下无人清理导致内存泄漏
        self._redis.expire(self._calls_key, int(self.period * 2) + 60)


# ================================================================
# CircuitBreakerConsumerMixin
# ================================================================

class CircuitBreakerConsumerMixin(AbstractConsumer):
    """
    熔断器消费者 Mixin

    通过 user_options['circuit_breaker_options'] 配置所有参数，详见模块文档。
    """

    def custom_init(self):
        super().custom_init()

        user_options = self.consumer_params.user_options
        cb_options = user_options['circuit_breaker_options']
        strategy = cb_options.get('strategy', 'consecutive')
        counter_backend = cb_options.get('counter_backend', 'local')

        common_kwargs = dict(
            strategy=strategy,
            failure_threshold=cb_options.get('failure_threshold', 5),
            errors_rate=cb_options.get('errors_rate', 0.5),
            period=cb_options.get('period', 60.0),
            min_calls=cb_options.get('min_calls', 5),
            recovery_timeout=cb_options.get('recovery_timeout', 60.0),
            half_open_max_calls=cb_options.get('half_open_max_calls', 3),
            half_open_ttl=cb_options.get('half_open_ttl', None),
        )

        if counter_backend == 'redis':
            self._circuit_breaker = RedisCircuitBreaker(
                queue_name=self.queue_name, **common_kwargs
            )
        else:
            self._circuit_breaker = CircuitBreaker(**common_kwargs)

        self._circuit_breaker_fallback = cb_options.get('fallback', None)
        self._tracked_exception_names = _parse_exception_names(
            cb_options.get('exceptions', None)
        )

        self.logger.info(
            f"CircuitBreaker initialized: strategy={strategy}, backend={counter_backend}, "
            f"{'failure_threshold=' + str(common_kwargs['failure_threshold']) if strategy == 'consecutive' else 'errors_rate=' + str(common_kwargs['errors_rate']) + ', period=' + str(common_kwargs['period']) + 's, min_calls=' + str(common_kwargs['min_calls'])}, "
            f"recovery_timeout={common_kwargs['recovery_timeout']}s, "
            f"half_open_max_calls={common_kwargs['half_open_max_calls']}, "
            f"half_open_ttl={common_kwargs['half_open_ttl']}, "
            f"exceptions={self._tracked_exception_names or 'all'}, "
            f"fallback={'yes' if self._circuit_breaker_fallback else 'no'}"
        )

    def _on_circuit_open(self, info_dict: dict):
        """
        熔断触发时的钩子，子类可重写此方法来发送告警（微信/钉钉/邮件等）。

        info_dict 包含:
            old_state:       变化前状态
            new_state:       变化后状态 (固定为 'open')
            queue_name:      队列名
            failure_count:   累计失败次数
            strategy:        当前策略 ('consecutive' 或 'rate')
            error_rate_info: 错误率详情 (仅 rate 策略, 含 total/failures/rate)

        用法示例::

            class MyCircuitBreakerMixin(CircuitBreakerConsumerMixin):
                def _on_circuit_open(self, info_dict):
                    send_dingtalk(f'队列 {info_dict["queue_name"]} 已熔断!')
        """
        pass

    def _on_circuit_close(self, info_dict: dict):
        """
        熔断恢复时的钩子，子类可重写此方法来发送恢复通知。

        info_dict 内容同 _on_circuit_open，new_state 固定为 'closed'。

        用法示例::

            class MyCircuitBreakerMixin(CircuitBreakerConsumerMixin):
                def _on_circuit_close(self, info_dict):
                    send_wechat(f'队列 {info_dict["queue_name"]} 已恢复正常')
        """
        pass

    def _submit_task(self, kw):
        if not self._circuit_breaker_fallback:
            while self._circuit_breaker.state == CircuitState.OPEN:
                remaining = self._circuit_breaker.time_until_half_open()
                sleep_secs = min(remaining, 5.0) if remaining > 0 else 0.1
                self.logger.warning(
                    f"CircuitBreaker OPEN for queue [{self.queue_name}], "
                    f"waiting {remaining:.1f}s for recovery"
                )
                time.sleep(sleep_secs)
        super()._submit_task(kw)

    _CB_FALLBACK_FLAG = '__funboost_cb_fallback__'

    # noinspection PyProtectedMember
    def _run_consuming_function_with_confirm_and_retry(self, kw: dict, current_retry_times,
                                                       function_result_status: FunctionResultStatus):
        if self._circuit_breaker_fallback and self._circuit_breaker.state == CircuitState.OPEN:
            kw[self._CB_FALLBACK_FLAG] = True
            function_only_params = kw['function_only_params'] if self._do_not_delete_extra_from_msg is False else kw['body']
            try:
                result = self._circuit_breaker_fallback(
                    **self._convert_real_function_only_params_by_conusuming_function_kind(
                        function_only_params, kw['body']['extra']
                    )
                )
                function_result_status.result = result
                function_result_status.success = True
                self.logger.debug(
                    f"CircuitBreaker fallback executed for [{self.consuming_function.__name__}], "
                    f"params={function_only_params}"
                )
            except BaseException as e:
                function_result_status.exception = f'{e.__class__.__name__}    {str(e)}'
                function_result_status.exception_msg = str(e)
                function_result_status.exception_type = e.__class__.__name__
                function_result_status.result = FunctionResultStatus.FUNC_RUN_ERROR
                self.logger.error(f"CircuitBreaker fallback error: {type(e)} {e}")
            return function_result_status

        kw.pop(self._CB_FALLBACK_FLAG, None)
        return super()._run_consuming_function_with_confirm_and_retry(kw, current_retry_times, function_result_status)

    # noinspection PyProtectedMember
    async def _async_run_consuming_function_with_confirm_and_retry(self, kw: dict, current_retry_times,
                                                                   function_result_status: FunctionResultStatus):
        if self._circuit_breaker_fallback and self._circuit_breaker.state == CircuitState.OPEN:
            kw[self._CB_FALLBACK_FLAG] = True
            function_only_params = kw['function_only_params'] if self._do_not_delete_extra_from_msg is False else kw['body']
            try:
                result = self._circuit_breaker_fallback(
                    **self._convert_real_function_only_params_by_conusuming_function_kind(
                        function_only_params, kw['body']['extra']
                    )
                )
                if asyncio.iscoroutine(result) or inspect.isawaitable(result):
                    result = await result
                function_result_status.result = result
                function_result_status.success = True
                self.logger.debug(
                    f"CircuitBreaker fallback executed for [{self.consuming_function.__name__}], "
                    f"params={function_only_params}"
                )
            except BaseException as e:
                function_result_status.exception = f'{e.__class__.__name__}    {str(e)}'
                function_result_status.exception_msg = str(e)
                function_result_status.exception_type = e.__class__.__name__
                function_result_status.result = FunctionResultStatus.FUNC_RUN_ERROR
                self.logger.error(f"CircuitBreaker fallback error: {type(e)} {e}")
            return function_result_status

        kw.pop(self._CB_FALLBACK_FLAG, None)
        return await super()._async_run_consuming_function_with_confirm_and_retry(kw, current_retry_times, function_result_status)

    def _is_tracked_exception(self, function_result_status: FunctionResultStatus) -> bool:
        """判断该失败是否属于需要被熔断器跟踪的异常类型"""
        if self._tracked_exception_names is None:
            return True
        if not function_result_status.exception_type:
            return True
        return function_result_status.exception_type in self._tracked_exception_names

    def _frame_custom_record_process_info_func(self, current_function_result_status: FunctionResultStatus, kw: dict):
        """
        任务执行完成后（含重试耗尽），根据最终结果更新熔断器状态。
        - fallback 执行的成功不计入恢复统计
        - 不在 exceptions 列表中的异常不计入熔断器
        """
        super()._frame_custom_record_process_info_func(current_function_result_status, kw)

        if (current_function_result_status._has_requeue
                or current_function_result_status._has_to_dlx_queue
                or current_function_result_status._has_kill_task):
            return

        if kw.get(self._CB_FALLBACK_FLAG):
            return

        old_state = self._circuit_breaker.state
        if current_function_result_status.success:
            new_state = self._circuit_breaker.record_success()
        else:
            if not self._is_tracked_exception(current_function_result_status):
                return
            new_state = self._circuit_breaker.record_failure()

        if old_state != new_state:
            info_dict = {
                'old_state': old_state,
                'new_state': new_state,
                'queue_name': self.queue_name,
                'failure_count': self._circuit_breaker.failure_count,
                'strategy': self._circuit_breaker.strategy,
            }
            if self._circuit_breaker.strategy == 'rate':
                info_dict['error_rate_info'] = self._circuit_breaker.get_error_rate_info()

            extra_info = ''
            if 'error_rate_info' in info_dict:
                ri = info_dict['error_rate_info']
                extra_info = f", error_rate={ri['rate']:.2%} ({ri['failures']}/{ri['total']})"
            self.logger.warning(
                f"CircuitBreaker state changed: {old_state} -> {new_state} "
                f"for queue [{self.queue_name}], "
                f"failure_count={info_dict['failure_count']}"
                f"{extra_info}"
            )

            try:
                if new_state == CircuitState.OPEN:
                    self._on_circuit_open(info_dict)
                elif new_state == CircuitState.CLOSED:
                    self._on_circuit_close(info_dict)
            except Exception as e:
                self.logger.error(f"circuit breaker hook error: {type(e).__name__} {e}")

    async def _aio_frame_custom_record_process_info_func(self, current_function_result_status: FunctionResultStatus, kw: dict):
        await super()._aio_frame_custom_record_process_info_func(current_function_result_status, kw)
        await simple_run_in_executor(self._frame_custom_record_process_info_func, current_function_result_status, kw)


# ================================================================
# 预配置 BoosterParams
# ================================================================

class CircuitBreakerBoosterParams(BoosterParams):
    """
    预配置了熔断器的 BoosterParams

    使用示例：

        # 连续失败策略（默认）
        @boost(CircuitBreakerBoosterParams(
            queue_name='my_task',
            broker_kind=BrokerEnum.REDIS,
            user_options={
                'circuit_breaker_options': {
                    'failure_threshold': 5,
                    'recovery_timeout': 60,
                },
            },
        ))
        def my_task(x):
            return call_external_api(x)

        # 错误率策略 + Redis 分布式
        @boost(CircuitBreakerBoosterParams(
            queue_name='my_task',
            broker_kind=BrokerEnum.REDIS,
            user_options={
                'circuit_breaker_options': {
                    'strategy': 'rate',
                    'counter_backend': 'redis',
                    'errors_rate': 0.5,
                    'period': 60,
                    'min_calls': 10,
                    'recovery_timeout': 30,
                },
            },
        ))
        def my_task(x):
            return call_external_api(x)
    """
    consumer_override_cls: typing.Optional[typing.Type] = CircuitBreakerConsumerMixin
    user_options: dict = {
        'circuit_breaker_options': {
            'strategy': 'consecutive',
            'counter_backend': 'local',
            'failure_threshold': 5,
            'recovery_timeout': 60.0,
            'half_open_max_calls': 3,
        },
    }


__all__ = [
    'CircuitState',
    'CircuitBreaker',
    'RedisCircuitBreaker',
    'CircuitBreakerConsumerMixin',
    'CircuitBreakerBoosterParams',
]
