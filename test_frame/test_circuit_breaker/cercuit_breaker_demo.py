import time
from funboost import boost, BoosterParams, BrokerEnum,ConcurrentModeEnum
from funboost.contrib.override_publisher_consumer_cls.circuit_breaker_mixin import CircuitBreakerConsumerMixin


class CircuitBreakerConsumerWithAlertMixin(CircuitBreakerConsumerMixin):
    def _on_circuit_open(self, info_dict):
        # 熔断开启时调用
        print('模拟发个钉钉告警',f'队列 {info_dict["queue_name"]} 开启熔断，熔断信息： {info_dict}')
    
    def _on_circuit_close(self, info_dict):
        # 熔断恢复时调用
        print('模拟发个微信告警',f'队列 {info_dict["queue_name"]} 已恢复正常，恢复信息： {info_dict}')

@boost(BoosterParams(
        queue_name='test_cb_block_v5',
        broker_kind=BrokerEnum.MEMORY_QUEUE,
        qps=0,
        # concurrent_num=1,
        concurrent_mode=ConcurrentModeEnum.SINGLE_THREAD,
        max_retry_times=0,
        consumer_override_cls=CircuitBreakerConsumerWithAlertMixin,
        user_options={
            'circuit_breaker_options': {
                'counter_backend': 'redis',
                'strategy': 'consecutive',
                'failure_threshold': 3,
                'recovery_timeout': 5,
                'half_open_max_calls': 2,
            },
        },
    ))
def task_block(x):
    # if random.random() < 0.5:
    #     raise RuntimeError(f'simulated failure for {x}')
    time.sleep(1)
    if x < 6 :
        raise RuntimeError(f'simulated failure for {x}')
    return x * 10

if __name__ == '__main__':
    
    # time.sleep(5)
    t0 = time.time()
  
    for i in range(100):
        task_block.push(i)
    # time.sleep(10)
    task_block.consume()