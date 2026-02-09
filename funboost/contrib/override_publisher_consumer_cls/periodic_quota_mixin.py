# -*- coding: utf-8 -*-
# @Author  : AI Assistant
# @Time    : 2026/1/30
"""
周期配额控频消费者 Mixin (Periodic Quota Rate Limiter Consumer Mixin)

功能：在指定周期内限制执行次数，周期结束后配额自动重置。这个超越了celery 的 rate_limit 概念。

例如假设chatgpt允许你每天使用24次，不代表你每使用一次然后需要间隔1小时才能再次使用chatgpt，
你可以一口气把一天额度快速的用完，然后当天或24小时内不用chatgpt就好了，所以周期额度和运行频率是两码事，
周期额度不代表你要把额度次数除以周期时长，然后匀速执行频率。
如果每次使用chtgpt要等1个小时，你愿意刚好掐点每隔1小时去用一次chatgpt吗，太抓狂了这样；肯定是能自由随意啥时候用完24次这种更爽，不用一直看手表掐点。

周期额度功能可以和qps参数结合起来使用，一个控制频率，一个控制周期额度。


celery的 rate_limit 被 funboost的周期额度功能完虐，
celery的 rate_limit = '24/d',每次运行消息需要间隔1小时，这不是我们想要的。


=== 核心概念 ===

与令牌桶的区别：
- 令牌桶：令牌持续补充，速率 = 配额/周期
- 周期配额：周期开始时配额重置，周期内用完就暂停

=== 两种窗口模式 ===

1. 滑动窗口 (sliding_window=True, 默认)：
   - 从程序启动时刻开始计算周期
   - 例如：19:33:55启动，每分钟6次 -> 周期为 19:33:55 ~ 19:34:55
   
2. 固定窗口 (sliding_window=False)：
   - 从整点边界开始计算周期
   - 例如：每分钟6次 -> 周期为 19:33:00 ~ 19:34:00

=== 使用场景 ===

典型场景：每天自动评论30次博客，每10分钟评论1次，当天配额用完就停止
配置方式：
    quota_limit = 30        # 每个周期最多30次
    quota_period = 'd'      # 周期为"天"
    qps = 1/600             # 每10分钟执行1次
    sliding_window = False  # 使用固定窗口，从0点开始算

效果：
    - 因为 qps=0.00167，所以每10分钟才执行1次（匀速间隔）
    - 因为 quota_limit=30, quota_period='d'，每天最多执行30次
    - 配额用完后暂停，第二天0点配额自动重置为30

=== 用法示例 ===

    from funboost import boost, BoosterParams, BrokerEnum
    from funboost.contrib.override_publisher_consumer_cls.periodic_quota_mixin import PeriodicQuotaConsumerMixin

    # 滑动窗口模式（默认）：每秒1次，每分钟最多6次
    @boost(BoosterParams(
        queue_name='minute_quota_queue',
        broker_kind=BrokerEnum.REDIS,
        consumer_override_cls=PeriodicQuotaConsumerMixin,
        user_options={
            'quota_limit': 6,           # 每周期最多6次
            'quota_period': 'm',        # 周期为分钟 (s/m/h/d)
            'sliding_window': True,     # 滑动窗口（默认，可省略）
        },
        qps=1,  # 每秒执行1次（间隔控制）# 周期额度可以和qps一起使用
    ))
    def my_task(x):
        print(f'Processing {x}')
"""

import threading
import time
import datetime
import typing
from funboost.consumers.base_consumer import AbstractConsumer
from funboost.constant import BrokerEnum
from funboost.core.func_params_model import BoosterParams


class PeriodicQuota:
    """
    周期配额实现
    
    参数：
    - quota_limit: 每个周期的最大执行次数
    - period_type: 周期类型 ('s', 'm', 'h', 'd')
    - sliding_window: 是否使用滑动窗口模式
        - True (默认): 滑动窗口，从程序启动时开始计算 (如启动后1小时内最多N次)
        - False: 固定窗口，从整点开始计算 (如每小时从 XX:00:00 开始)
        例如 chatgpt是让你从0点到24点使用24次，还是最近24小时内使用24次。
        固定窗口(False)：你在1月1日 23:50-23:59用了24次，1月2日 0:01还能用24次（因为跨过了0点边界）。
        滑动窗口(True)：你在1月1日 23:50-23:59用了24次，1月2日 0:01不能用，要等到1月2日 23:50才能用。
    """
    
    PERIOD_SECONDS = {
        's': 1,
        'm': 60,
        'h': 3600,
        'd': 86400,
    }
    
    def __init__(self, quota_limit: int, period_type: str = 'm', sliding_window: bool = False):
        self.quota_limit = quota_limit
        self.period_type = period_type
        self.period_seconds = self.PERIOD_SECONDS.get(period_type, 60)
        self.sliding_window = sliding_window
        
        self._used_count = 0
        self._lock = threading.Lock()
        
        # 根据模式设置周期起点
        if sliding_window:
            # 滑动窗口：从当前时间开始
            self._current_period_start = time.time()
        else:
            # 固定窗口：从整点开始
            self._current_period_start = self._get_fixed_period_start(time.time())
    
    def _get_fixed_period_start(self, timestamp: float) -> float:
        """计算固定窗口模式下，当前时间所属周期的开始时间（整点边界）"""
        dt = datetime.datetime.fromtimestamp(timestamp)
        
        if self.period_type == 's':
            return datetime.datetime(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second).timestamp()
        elif self.period_type == 'm':
            return datetime.datetime(dt.year, dt.month, dt.day, dt.hour, dt.minute, 0).timestamp()
        elif self.period_type == 'h':
            return datetime.datetime(dt.year, dt.month, dt.day, dt.hour, 0, 0).timestamp()
        elif self.period_type == 'd':
            return datetime.datetime(dt.year, dt.month, dt.day, 0, 0, 0).timestamp()
        else:
            return datetime.datetime(dt.year, dt.month, dt.day, dt.hour, dt.minute, 0).timestamp()
    
    def _check_and_reset_period(self):
        """检查是否进入新周期，如果是则重置配额"""
        now = time.time()
        
        if self.sliding_window:
            # 滑动窗口：检查是否超过了周期长度
            if now - self._current_period_start >= self.period_seconds:
                self._current_period_start = now
                self._used_count = 0
                return True
        else:
            # 固定窗口：检查是否进入了新的整点周期
            current_period_start = self._get_fixed_period_start(now)
            if current_period_start > self._current_period_start:
                self._current_period_start = current_period_start
                self._used_count = 0
                return True
        
        return False
    
    def acquire(self, timeout: float = None) -> bool:
        """
        尝试获取一个配额
        
        :param timeout: 最大等待时间（秒），None 表示无限等待
        :return: 是否成功获取
        """
        start_time = time.time()
        
        while True:
            with self._lock:
                self._check_and_reset_period()
                
                if self._used_count < self.quota_limit:
                    self._used_count += 1
                    return True
            
            # 计算距离下一个周期还有多久
            now = time.time()
            next_period_start = self._current_period_start + self.period_seconds
            wait_time = next_period_start - now
            
            if wait_time <= 0:
                # 已经到了新周期，继续循环检查
                continue
            
            # 检查是否超时
            if timeout is not None:
                elapsed = time.time() - start_time
                if elapsed >= timeout:
                    return False
                wait_time = min(wait_time, timeout - elapsed)
            
            # 等待，但最多等待1秒后重新检查
            time.sleep(min(wait_time, 1.0))
    
    def get_remaining_quota(self) -> int:
        """获取当前周期剩余配额"""
        with self._lock:
            self._check_and_reset_period()
            return self.quota_limit - self._used_count
    
    def get_seconds_until_reset(self) -> float:
        """获取距离下次配额重置的秒数"""
        now = time.time()
        next_period_start = self._current_period_start + self.period_seconds
        return max(0, next_period_start - now)


class PeriodicQuotaConsumerMixin(AbstractConsumer):
    """
    周期配额控频消费者 Mixin
    
    核心原理：
    1. 每个周期开始时，配额重置为 quota_limit
    2. 每次执行消耗1个配额
    3. 配额用完后，等待到下一个周期开始
    4. 结合 qps 控制执行间隔
    
    配置参数（通过 user_options 传递）：
    - quota_limit: 每周期最大执行次数
    - quota_period: 周期类型 ('s'=秒, 'm'=分钟, 'h'=小时, 'd'=天)
    - sliding_window: 窗口模式 (True=滑动窗口[默认], False=固定窗口)
    """
    
    def custom_init(self):
        """初始化周期配额"""
        super().custom_init()
        
        user_options = self.consumer_params.user_options
        quota_limit = user_options.get('quota_limit', 10)
        quota_period = user_options.get('quota_period', 'm')
        sliding_window = user_options.get('sliding_window', True)  # 默认使用滑动窗口
        
        # 创建周期配额对象
        self._periodic_quota = PeriodicQuota(
            quota_limit=quota_limit,
            period_type=quota_period,
            sliding_window=sliding_window
        )
        
        period_names = {'s': 'second', 'm': 'minute', 'h': 'hour', 'd': 'day'}
        if quota_period not in period_names:
            raise ValueError(f'quota_period is error,must in {period_names}')
        period_name = period_names.get(quota_period, quota_period)
        window_mode = "sliding" if sliding_window else "fixed"
        
        self.logger.info(
            f"PeriodicQuota rate limiter initialized: "
            f"quota_limit={quota_limit}/{period_name}, mode={window_mode}, qps={self.consumer_params.qps}"
        )
    
    def _check_quota_before_execute(self):
        """
        在任务执行前检查配额
        
        如果配额用完，会阻塞等待到下一周期
        """
        remaining = self._periodic_quota.get_remaining_quota()
        if remaining <= 0:
            wait_seconds = self._periodic_quota.get_seconds_until_reset()
            self.logger.warning(
                f"Quota exhausted ({self._periodic_quota.quota_limit}/{self._periodic_quota.period_type}), "
                f"waiting {wait_seconds:.1f}s for next period reset"
            )
        
        # 阻塞直到获取到配额
        self._periodic_quota.acquire(timeout=86400)
    
    def _submit_task(self, kw):
        """
        重写 _submit_task 方法，在任务执行前检查配额
        """
        # Step 1: 先检查配额（阻塞直到有配额可用）
        self._check_quota_before_execute()
        
        # Step 2: 调用父类的 _submit_task 执行任务
        super()._submit_task(kw)


class PeriodicQuotaBoosterParams(BoosterParams):
    """
    预配置的周期配额 BoosterParams
    
    使用示例：
    
        # 每秒1次，每分钟最多6次
        @boost(PeriodicQuotaBoosterParams(
            queue_name='minute_quota_queue',
            user_options={'quota_limit': 6, 'quota_period': 'm'},
            qps=1,
        ))
        def my_task(x):
            ...
    """
    broker_kind: str = BrokerEnum.REDIS
    consumer_override_cls: typing.Optional[typing.Type] = PeriodicQuotaConsumerMixin
    qps: typing.Union[float, int, None] = 1
    user_options: dict = {
        'quota_limit': 10,
        'quota_period': 'm',  # s=秒, m=分钟, h=小时, d=天
        'sliding_window': True, # 滑动窗口（默认，可省略）
    }
