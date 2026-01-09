import time
from funboost import boost, BoosterParams,ctrl_c_recv,BrokerEnum

@boost(BoosterParams(queue_name='test_redis_conn',broker_kind=BrokerEnum.REDIS,is_using_rpc_mode=True))
def add(x, y):
    return x + y

if __name__ == '__main__':
    add.consume()
    print(add.push(1, 2).result)
    time.sleep(700)
    print(add.push(3, 4).result)




