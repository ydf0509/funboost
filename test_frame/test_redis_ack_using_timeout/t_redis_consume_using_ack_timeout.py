"""
这个是用来测试，以redis为中间件，随意关闭代码会不会造成任务丢失的。
"""

import time

from funboost import boost, BrokerEnum, FunctionResultStatusPersistanceConfig, BoosterParams, ConcurrentModeEnum


@boost(BoosterParams(queue_name='test_redis_ack__use_timeout', broker_kind=BrokerEnum.REIDS_ACK_USING_TIMEOUT, concurrent_mode=ConcurrentModeEnum.SINGLE_THREAD,
                     log_level=20, broker_exclusive_config={'ack_timeout': 30}))
def cost_long_time_fun(x):
    print(f'start {x}')
    time.sleep(120)
    print(f'end {x}')


if __name__ == '__main__':
    cost_long_time_fun.push(666)
    cost_long_time_fun.consume()
