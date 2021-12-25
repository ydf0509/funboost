from funboost import boost,BrokerEnum,ConcurrentModeEnum
import time

@boost('test_delay', broker_kind=BrokerEnum.REDIS_ACK_ABLE, qps=0.5, concurrent_mode=ConcurrentModeEnum.SINGLE_THREAD)
def f(x):
    print(x)

if __name__ == '__main__':
    f.consume()