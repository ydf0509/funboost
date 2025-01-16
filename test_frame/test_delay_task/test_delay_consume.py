from funboost import boost,BrokerEnum,ConcurrentModeEnum,BoosterParams
import time

@BoosterParams(queue_name='test_delay2', broker_kind=BrokerEnum.REDIS_ACK_ABLE, qps=10, concurrent_mode=ConcurrentModeEnum.THREADING,publish_msg_log_use_full_msg=True)
def f(x):
    print(x)

if __name__ == '__main__':
    f.consume()

    while 1:
        time.sleep(10)