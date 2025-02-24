
import logging
import time
from funboost import boost, BrokerEnum,BoosterParams,ctrl_c_recv,ConcurrentModeEnum


@boost(BoosterParams(queue_name='test_load_balancing', broker_kind=BrokerEnum.REDIS_ACK_ABLE,log_level=logging.INFO,
                     concurrent_mode=ConcurrentModeEnum.SINGLE_THREAD,
                     broker_exclusive_config={'pull_msg_batch_size':1}
                     ))
def test_load_balancing(x):
    print(x)
    time.sleep(1)

if __name__ == '__main__':
    test_load_balancing.consume()
    ctrl_c_recv()
