import time

from funboost import boost, BrokerEnum, BoosterParams, AbstractConsumer, FunctionResultStatus


class MyConsumer(AbstractConsumer):
    def user_custom_record_process_info_func(self, current_function_result_status: FunctionResultStatus):
        print('使用指定的consumer_override_cls来自定义或重写方法')
        self.logger.debug(current_function_result_status.get_status_dict())


@boost(BoosterParams(queue_name='test_define_cls_queue', broker_kind=BrokerEnum.REDIS,
                     concurrent_num=10, consumer_override_cls=MyConsumer,
                     is_show_message_get_from_broker=True))
def cost_long_time_fun(x):
    print(f'start {x}')
    time.sleep(20)
    print(f'end {x}')


if __name__ == '__main__':
    for i in range(100):
        cost_long_time_fun.push(i)
    cost_long_time_fun.consume()
