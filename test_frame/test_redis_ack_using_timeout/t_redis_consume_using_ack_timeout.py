"""
这个是用来测试，以redis为中间件，随意关闭代码会不会造成任务丢失的。
"""

import time

from funboost import boost, BrokerEnum, FunctionResultStatusPersistanceConfig, BoosterParams, ConcurrentModeEnum, AbstractConsumer, FunctionResultStatus


class MyConsumer(AbstractConsumer):
    def user_custom_record_process_info_func(self, current_function_result_status: FunctionResultStatus):
        print('使用指定的consumer_override_cls来自定义或重写方法')
        self.logger.debug(current_function_result_status.get_status_dict())


@boost(BoosterParams(queue_name='test_redis_ack_use_timeout_queue', broker_kind=BrokerEnum.REIDS_ACK_USING_TIMEOUT,
                     concurrent_mode=ConcurrentModeEnum.SINGLE_THREAD,
                     log_level=10, broker_exclusive_config={'ack_timeout': 600}, consumer_override_cls=MyConsumer,
                     is_show_message_get_from_broker=True))
def cost_long_time_fun(x):
    print(f'start {x}')
    time.sleep(20)
    print(f'end {x}')


if __name__ == '__main__':
    cost_long_time_fun.push(666)
    cost_long_time_fun.consume()
