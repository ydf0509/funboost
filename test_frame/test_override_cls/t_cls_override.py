import random
import time

from funboost import boost, BrokerEnum, FunctionResultStatusPersistanceConfig, BoosterParams, ConcurrentModeEnum, AbstractConsumer, FunctionResultStatus


class MyConsumer(AbstractConsumer):
    def user_custom_record_process_info_func(self, current_function_result_status: FunctionResultStatus):
        print('使用指定的consumer_override_cls来自定义或重写方法')
        if current_function_result_status.success is True:
            print(f'入参 {current_function_result_status.params} 成功了，结果是： {current_function_result_status.result}，模拟发个微信通知')
        else:
            print(f'入参 {current_function_result_status.params} 失败了，原因是： {current_function_result_status.exception},模拟发个邮件')
        self.logger.debug(current_function_result_status.get_status_dict()) # 给用户打印下current_function_result_status有哪些字段信息。


@boost(BoosterParams(queue_name='test_redis_ack_use_timeout_queue', broker_kind=BrokerEnum.REDIS,
                     concurrent_mode=ConcurrentModeEnum.SINGLE_THREAD,
                     log_level=10,  consumer_override_cls=MyConsumer,
                     is_show_message_get_from_broker=True))
def cost_long_time_fun(x):
    print(f'start {x}')
    time.sleep(2)
    if random.random()>0.5:
        raise ValueError('模拟函数运行出错')
    print(f'end {x}')
    return x*2


if __name__ == '__main__':
    for i in range(100):
        cost_long_time_fun.push(i)
    cost_long_time_fun.consume()
