from funboost import boost, BrokerEnum


@boost('test_queue77e', log_level=10, broker_kind=BrokerEnum.MEMORY_QUEUE, qps=5,
       create_logger_file=False,is_show_message_get_from_broker=True,
       # specify_concurrent_pool= pool2,
       # concurrent_mode=ConcurrentModeEnum.SINGLE_THREAD, concurrent_num=3,is_send_consumer_hearbeat_to_redis=True,function_timeout=10,
       # function_result_status_persistance_conf=FunctionResultStatusPersistanceConfig(True,True)
       )
def f2(a, b):
    # time.sleep(100)

    print(a, b)
    return a - b


if __name__ == '__main__':
    f2.push(1,2)
    f2.consume()