from funboost import boost,BrokerEnum,ConcurrentModeEnum
import time

@boost('test_delay2', broker_kind=BrokerEnum.REDIS_ACK_ABLE, qps=10, concurrent_mode=ConcurrentModeEnum.THREADING)
def f(x):
    print(x)

if __name__ == '__main__':
    f.consume()

    while 1:
        time.sleep(10)