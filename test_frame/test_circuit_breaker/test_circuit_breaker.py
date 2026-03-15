# -*- coding: utf-8 -*-
"""
熔断器 CircuitBreakerConsumerMixin 测试

Part 1: CircuitBreaker 状态机单元测试（本地内存，无需 funboost 运行环境）
  - 1a: consecutive 策略
  - 1b: rate 策略
  - 1c: half_open_ttl 超时
  - 1d: 多线程并发安全
Part 2: 与 funboost MEMORY_QUEUE 集成测试
  - 2a: 阻塞模式（consecutive 策略）
  - 2b: Fallback 模式（consecutive 策略）
  - 2c: 错误率策略 + exceptions 过滤
"""
import time
import threading

from funboost.contrib.override_publisher_consumer_cls.circuit_breaker_mixin import (
    CircuitState,
    CircuitBreaker,
    _parse_exception_names,
)


def _elapsed(t0):
    """返回距 t0 的经过秒数字符串"""
    return f'[T+{time.time() - t0:.1f}s]'


# ================================================================
# Part 1a: consecutive 策略
# ================================================================

def test_initial_state():
    cb = CircuitBreaker(strategy='consecutive', failure_threshold=3, recovery_timeout=5, half_open_max_calls=2)
    assert cb.state == CircuitState.CLOSED
    assert cb.failure_count == 0
    print('  [PASS] 初始状态为 CLOSED')


def test_success_resets_failure_count():
    cb = CircuitBreaker(failure_threshold=5)
    cb.record_failure()
    cb.record_failure()
    assert cb.failure_count == 2
    cb.record_success()
    assert cb.failure_count == 0
    assert cb.state == CircuitState.CLOSED
    print('  [PASS] 成功重置失败计数')


def test_failures_trigger_open():
    cb = CircuitBreaker(failure_threshold=3)
    cb.record_failure()
    cb.record_failure()
    assert cb.state == CircuitState.CLOSED
    cb.record_failure()
    assert cb.state == CircuitState.OPEN
    print('  [PASS] 连续失败 >= threshold 触发 OPEN')


def test_open_to_half_open_after_timeout():
    cb = CircuitBreaker(failure_threshold=2, recovery_timeout=1.0)
    cb.record_failure()
    cb.record_failure()
    assert cb.state == CircuitState.OPEN

    remaining = cb.time_until_half_open()
    assert remaining > 0
    print(f'  等待恢复 ({remaining:.1f}s)...')
    time.sleep(1.1)

    assert cb.state == CircuitState.HALF_OPEN
    assert cb.time_until_half_open() == 0.0
    print('  [PASS] OPEN -> HALF_OPEN 超时自动转换')


def test_half_open_success_closes():
    cb = CircuitBreaker(failure_threshold=2, recovery_timeout=0.5, half_open_max_calls=2)
    cb.record_failure()
    cb.record_failure()
    time.sleep(0.6)
    assert cb.state == CircuitState.HALF_OPEN

    cb.record_success()
    assert cb.state == CircuitState.HALF_OPEN
    cb.record_success()
    assert cb.state == CircuitState.CLOSED
    assert cb.failure_count == 0
    print('  [PASS] HALF_OPEN 连续成功 -> CLOSED')


def test_half_open_failure_reopens():
    cb = CircuitBreaker(failure_threshold=2, recovery_timeout=0.5, half_open_max_calls=3)
    cb.record_failure()
    cb.record_failure()
    time.sleep(0.6)
    assert cb.state == CircuitState.HALF_OPEN

    cb.record_success()
    cb.record_failure()
    assert cb.state == CircuitState.OPEN
    print('  [PASS] HALF_OPEN 失败 -> 重新 OPEN')


# ================================================================
# Part 1b: rate 策略
# ================================================================

def test_rate_strategy_no_open_below_min_calls():
    cb = CircuitBreaker(strategy='rate', errors_rate=0.5, period=10.0, min_calls=5, recovery_timeout=5)
    for _ in range(4):
        cb.record_failure()
    assert cb.state == CircuitState.CLOSED, '调用数不足 min_calls 时不应触发 OPEN'
    print('  [PASS] rate: 调用数不足 min_calls 时不触发 OPEN')


def test_rate_strategy_opens_on_high_error_rate():
    cb = CircuitBreaker(strategy='rate', errors_rate=0.5, period=10.0, min_calls=4, recovery_timeout=5)
    cb.record_success()
    cb.record_failure()
    cb.record_failure()
    cb.record_failure()
    info = cb.get_error_rate_info()
    print(f'  当前错误率: {info["rate"]:.0%} ({info["failures"]}/{info["total"]})')
    assert cb.state == CircuitState.OPEN, f'错误率 75% >= 50%，应触发 OPEN，实际 {cb.state}'
    print('  [PASS] rate: 错误率达到阈值触发 OPEN')


def test_rate_strategy_no_open_below_threshold():
    cb = CircuitBreaker(strategy='rate', errors_rate=0.5, period=10.0, min_calls=4, recovery_timeout=5)
    cb.record_success()
    cb.record_success()
    cb.record_success()
    cb.record_failure()
    info = cb.get_error_rate_info()
    print(f'  当前错误率: {info["rate"]:.0%} ({info["failures"]}/{info["total"]})')
    assert cb.state == CircuitState.CLOSED, '错误率 25% < 50%，不应触发 OPEN'
    print('  [PASS] rate: 错误率低于阈值不触发 OPEN')


def test_rate_strategy_window_expiry():
    cb = CircuitBreaker(strategy='rate', errors_rate=0.5, period=1.0, min_calls=2, recovery_timeout=5)
    cb.record_failure()
    cb.record_failure()
    assert cb.state == CircuitState.OPEN

    cb._state = CircuitState.CLOSED
    cb._failure_count = 0
    cb._call_records.clear()

    cb.record_failure()
    cb.record_failure()
    assert cb.state == CircuitState.OPEN
    cb._state = CircuitState.CLOSED
    cb._failure_count = 0

    print('  等待窗口过期 (1s)...')
    time.sleep(1.1)

    cb.record_failure()
    assert cb.state == CircuitState.CLOSED, '旧记录过期后, 1次失败不应达到 min_calls=2'
    print('  [PASS] rate: 滑动窗口过期后旧记录不再计入')


# ================================================================
# Part 1c: half_open_ttl 超时
# ================================================================

def test_half_open_ttl_timeout():
    cb = CircuitBreaker(failure_threshold=2, recovery_timeout=0.5, half_open_max_calls=10, half_open_ttl=0.5)
    cb.record_failure()
    cb.record_failure()
    time.sleep(0.6)
    assert cb.state == CircuitState.HALF_OPEN

    cb.record_success()
    print('  等待 half_open_ttl 超时 (0.5s)...')
    time.sleep(0.6)

    assert cb.state == CircuitState.OPEN, '半开状态超时应回到 OPEN'
    print('  [PASS] HALF_OPEN 超过 half_open_ttl -> OPEN')


# ================================================================
# Part 1d: 多线程并发安全 + 异常名解析
# ================================================================

def test_thread_safety():
    cb = CircuitBreaker(failure_threshold=100, recovery_timeout=10)
    errors = []

    def record_many(is_success):
        try:
            for _ in range(500):
                if is_success:
                    cb.record_success()
                else:
                    cb.record_failure()
        except Exception as e:
            errors.append(e)

    threads = [threading.Thread(target=record_many, args=(i % 2 == 0,)) for i in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert not errors
    assert cb.state in (CircuitState.CLOSED, CircuitState.OPEN)
    print('  [PASS] 多线程并发安全')


def test_parse_exception_names():
    assert _parse_exception_names(None) is None
    assert _parse_exception_names((ValueError, TimeoutError)) == {'ValueError', 'TimeoutError'}
    assert _parse_exception_names(('RuntimeError',)) == {'RuntimeError'}
    assert _parse_exception_names((ConnectionError, 'CustomError')) == {'ConnectionError', 'CustomError'}
    print('  [PASS] _parse_exception_names 正确解析异常类型')


def run_unit_tests():
    print('=' * 60)
    print('Part 1: CircuitBreaker 状态机单元测试')
    print('=' * 60)

    print('--- 1a: consecutive 策略 ---')
    test_initial_state()
    test_success_resets_failure_count()
    test_failures_trigger_open()
    test_open_to_half_open_after_timeout()
    test_half_open_success_closes()
    test_half_open_failure_reopens()

    print('--- 1b: rate 策略 ---')
    test_rate_strategy_no_open_below_min_calls()
    test_rate_strategy_opens_on_high_error_rate()
    test_rate_strategy_no_open_below_threshold()
    test_rate_strategy_window_expiry()

    print('--- 1c: half_open_ttl ---')
    test_half_open_ttl_timeout()

    print('--- 1d: 其他 ---')
    test_thread_safety()
    test_parse_exception_names()

    print('-' * 60)
    print('Part 1 全部通过!')
    print()


# ================================================================
# Part 2: 与 funboost 集成测试
# ================================================================

def run_integration_test_block_mode():
    """
    阻塞模式：consecutive 策略 + 本地计数

    预期时序 (recovery_timeout=2.0s):
      T+0.0  consume() 启动
      T+0.3  consumer 就绪，push 3 条消息
      T+0.5  3 条消息消费完毕，连续失败 3 次 → OPEN
      T+1.3  assert OPEN ✓，push(100)
      T+1.3  _submit_task 阻塞等待 (remaining≈1.2s)
      T+2.5  recovery_timeout 到期 → HALF_OPEN，task 100 被执行 (should_fail=False → 成功)
      T+4.3  main 线程唤醒，检查 task 100 已执行 ✓
    """
    from funboost import boost, BoosterParams, BrokerEnum
    from funboost.contrib.override_publisher_consumer_cls.circuit_breaker_mixin import (
        CircuitBreakerConsumerMixin,
    )

    print('=' * 60)
    print('Part 2a: 集成测试 - 阻塞模式 (consecutive)')
    print('=' * 60)

    call_log = []
    should_fail = True

    @boost(BoosterParams(
        queue_name='test_cb_block_v3',
        broker_kind=BrokerEnum.MEMORY_QUEUE,
        qps=0,
        concurrent_num=1,
        max_retry_times=0,
        consumer_override_cls=CircuitBreakerConsumerMixin,
        user_options={
            'strategy': 'consecutive',
            'failure_threshold': 3,
            'recovery_timeout': 2.0,
            'half_open_max_calls': 2,
        },
    ))
    def task_block(x):
        call_log.append(('call', x, time.time()))
        if should_fail:
            raise RuntimeError(f'simulated failure for {x}')
        return x * 10

    task_block.consume()
    time.sleep(0.3)
    t0 = time.time()
    print(f'  {_elapsed(t0)} consumer 启动完成')

    for i in range(3):
        task_block.push(i)
    time.sleep(1.0)

    cb = task_block.consumer._circuit_breaker
    print(f'  {_elapsed(t0)} 失败 3 次后状态: {cb.state}, failure_count={cb.failure_count}')
    assert cb.state == CircuitState.OPEN

    should_fail = False
    task_block.push(100)
    print(f'  {_elapsed(t0)} 发送消息 100, 等待 recovery_timeout=2.0s 后恢复...')
    time.sleep(3.0)

    success_calls = [log for log in call_log if log[1] == 100]
    if success_calls:
        print(f'  {_elapsed(t0)} 消息 100 在 T+{success_calls[0][2] - t0:.1f}s 被执行 (预期 T+~2.2s，即 OPEN 后约 recovery_timeout=2.0s)')
    else:
        print(f'  {_elapsed(t0)} 消息 100 未被执行!')
    assert len(success_calls) >= 1
    print(f'  {_elapsed(t0)} [PASS] 阻塞模式 consecutive 测试通过')
    print()


def run_integration_test_fallback_mode():
    """
    Fallback 模式：consecutive 策略 + 本地计数

    预期时序 (recovery_timeout=2.0s):
      T+0.0  consume() 启动
      T+0.3  consumer 就绪，push 3 条消息（全部失败）
      T+0.5  OPEN
      T+1.3  assert OPEN ✓，push(100), push(101) → fallback 立即执行
      T+1.5  fallback 完成
      T+2.3  assert fallback ✓
      T+2.5  recovery_timeout 到期 → HALF_OPEN（lazy 触发）
      T+3.8  push(200)，此时状态已是 HALF_OPEN → 真实函数执行
      T+4.8  assert task 200 成功 ✓
    """
    from funboost import boost, BoosterParams, BrokerEnum
    from funboost.contrib.override_publisher_consumer_cls.circuit_breaker_mixin import (
        CircuitBreakerConsumerMixin,
    )

    print('=' * 60)
    print('Part 2b: 集成测试 - Fallback 模式 (consecutive)')
    print('=' * 60)

    call_log = []
    fallback_log = []
    should_fail = True

    def my_fallback(x):
        fallback_log.append(('fallback', x, time.time()))
        return f'fallback_result_{x}'

    @boost(BoosterParams(
        queue_name='test_cb_fallback_v3',
        broker_kind=BrokerEnum.MEMORY_QUEUE,
        qps=0,
        concurrent_num=1,
        max_retry_times=0,
        consumer_override_cls=CircuitBreakerConsumerMixin,
        user_options={
            'failure_threshold': 3,
            'recovery_timeout': 2.0,
            'half_open_max_calls': 2,
            'circuit_breaker_fallback': my_fallback,
        },
    ))
    def task_fb(x):
        call_log.append(('call', x, time.time()))
        if should_fail:
            raise RuntimeError(f'simulated failure for {x}')
        return x * 10

    task_fb.consume()
    time.sleep(0.3)
    t0 = time.time()
    print(f'  {_elapsed(t0)} consumer 启动完成')

    for i in range(3):
        task_fb.push(i)
    time.sleep(1.0)

    cb = task_fb.consumer._circuit_breaker
    print(f'  {_elapsed(t0)} 失败 3 次后状态: {cb.state}')
    assert cb.state == CircuitState.OPEN

    task_fb.push(100)
    task_fb.push(101)
    time.sleep(1.0)

    print(f'  {_elapsed(t0)} fallback 调用次数: {len(fallback_log)}')
    assert len(fallback_log) >= 2
    for log in fallback_log:
        print(f'    -> T+{log[2] - t0:.1f}s fallback({log[1]})')

    should_fail = False
    print(f'  {_elapsed(t0)} 当前状态: {cb.state}, 距 HALF_OPEN 剩余 {cb.time_until_half_open():.1f}s')
    print(f'  {_elapsed(t0)} 等待确保超过 recovery_timeout 后发送新消息...')
    time.sleep(1.5)

    task_fb.push(200)
    time.sleep(1.0)

    success_calls = [log for log in call_log if log[1] == 200]
    if success_calls:
        print(f'  {_elapsed(t0)} 消息 200 在 T+{success_calls[0][2] - t0:.1f}s 被真正执行 (状态应为 HALF_OPEN)')
    else:
        print(f'  {_elapsed(t0)} 消息 200 未被执行!')
    assert len(success_calls) >= 1
    print(f'  {_elapsed(t0)} [PASS] Fallback 模式测试通过')
    print()


def run_integration_test_rate_with_exceptions():
    """
    错误率策略 + exceptions 过滤

    预期时序:
      T+0.3  push 3 条消息 → RuntimeError (不在 exceptions 中，不被跟踪)
      T+1.3  assert CLOSED ✓
      T+1.3  push 3 条消息 → ConnectionError (被跟踪)
      T+2.3  错误率 = 3/3 = 100% >= 50%, min_calls=3 满足 → OPEN ✓
    """
    from funboost import boost, BoosterParams, BrokerEnum
    from funboost.contrib.override_publisher_consumer_cls.circuit_breaker_mixin import (
        CircuitBreakerConsumerMixin,
    )

    print('=' * 60)
    print('Part 2c: 集成测试 - rate 策略 + exceptions 过滤')
    print('=' * 60)

    call_log = []
    error_type = 'runtime'

    @boost(BoosterParams(
        queue_name='test_cb_rate_exc_v3',
        broker_kind=BrokerEnum.MEMORY_QUEUE,
        qps=0,
        concurrent_num=1,
        max_retry_times=0,
        consumer_override_cls=CircuitBreakerConsumerMixin,
        user_options={
            'strategy': 'rate',
            'errors_rate': 0.5,
            'period': 30.0,
            'min_calls': 3,
            'recovery_timeout': 2.0,
            'half_open_max_calls': 2,
            'exceptions': (ConnectionError,),
        },
    ))
    def task_rate(x):
        call_log.append(('call', x, time.time()))
        if error_type == 'runtime':
            raise RuntimeError(f'untracked error for {x}')
        elif error_type == 'connection':
            raise ConnectionError(f'tracked error for {x}')
        return x * 10

    task_rate.consume()
    time.sleep(0.3)
    t0 = time.time()
    print(f'  {_elapsed(t0)} consumer 启动完成')

    for i in range(3):
        task_rate.push(i)
    time.sleep(1.0)

    cb = task_rate.consumer._circuit_breaker
    print(f'  {_elapsed(t0)} RuntimeError 3 次后状态: {cb.state} (预期 CLOSED，因为 RuntimeError 不被跟踪)')
    assert cb.state == CircuitState.CLOSED, f'RuntimeError 不被跟踪，不应触发 OPEN，实际 {cb.state}'

    error_type = 'connection'
    for i in range(10, 13):
        task_rate.push(i)
    time.sleep(1.0)

    print(f'  {_elapsed(t0)} ConnectionError 3 次后状态: {cb.state}')
    rate_info = cb.get_error_rate_info()
    print(f'  {_elapsed(t0)} 错误率信息: {rate_info}')
    assert cb.state == CircuitState.OPEN, f'ConnectionError 被跟踪且错误率 >= 50%，应触发 OPEN，实际 {cb.state}'

    print(f'  {_elapsed(t0)} [PASS] rate 策略 + exceptions 过滤测试通过')
    print()


if __name__ == '__main__':
    run_unit_tests()
    run_integration_test_block_mode()
    run_integration_test_fallback_mode()
    run_integration_test_rate_with_exceptions()
    print('=' * 60)
    print('所有测试通过!')
    print('=' * 60)
