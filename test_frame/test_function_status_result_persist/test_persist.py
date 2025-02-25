from funboost import boost, FunctionResultStatusPersistanceConfig, BoosterParams,BrokerEnum,ctrl_c_recv
import time

class MyBoosterParams(BoosterParams):
    function_result_status_persistance_conf:FunctionResultStatusPersistanceConfig = FunctionResultStatusPersistanceConfig(
        is_save_status=True, is_save_result=True, expire_seconds=7 * 24 * 3600)
    is_send_consumer_hearbeat_to_redis = True


@boost(MyBoosterParams(queue_name='queue_test_g01t',broker_kind=BrokerEnum.REDIS,
                       function_result_status_persistance_conf=FunctionResultStatusPersistanceConfig(
                           is_save_status=True, is_save_result=True, expire_seconds=7 * 24 * 3600)))
def f(x):
    time.sleep(5)
    print(f'hi: {x}')
    return x + 1

@boost(MyBoosterParams(queue_name='queue_test_g02t',broker_kind=BrokerEnum.REDIS,
                       function_result_status_persistance_conf=FunctionResultStatusPersistanceConfig(
                           is_save_status=True, is_save_result=True, expire_seconds=7 * 24 * 3600)))
def f2(x):
    time.sleep(5)
    print(f'hello: {x}')
    return x + 1

if __name__ == '__main__':
    f.consume()
    f2.consume()
    ctrl_c_recv()
    

    
