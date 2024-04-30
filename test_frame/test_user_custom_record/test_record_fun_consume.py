from funboost import boost, BrokerEnum, BoosterParams


def my_record(result_status):
    print('自定义记录消费：', result_status)


@boost(BoosterParams(queue_name='test_queue77e', log_level=10, broker_kind=BrokerEnum.MEMORY_QUEUE, qps=5,
                     create_logger_file=False, is_show_message_get_from_broker=True,
                     user_custom_record_process_info_func=my_record, ))
def f2(a, b):
    print(a, b)
    1 / 0
    return a - b


if __name__ == '__main__':
    f2.push(1, 2)
    f2.consume()
