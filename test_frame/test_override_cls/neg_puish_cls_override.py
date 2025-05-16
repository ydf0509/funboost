
"""
这个是实现后进先出，
原理就是吧消息发布到队尾
"""

import random
import time

from funboost import boost, BrokerEnum, BoosterParams, ConcurrentModeEnum,fct,ctrl_c_recv
from funboost.core.serialization import Serialization

from funboost.publishers.redis_publisher import RedisPublisher

class OppositeRedisPublisher(RedisPublisher):
    def OppositePublish(self,msg):
        push_method_opp = None
        if self. _push_method == 'rpush':
            push_method_opp = 'lpush'
        if self. _push_method == 'lpush':
            push_method_opp = 'rpush'
        # print(msg)
        getattr(self.redis_db_frame, push_method_opp)(self._queue_name, Serialization.to_json_str(msg))

    

@boost(BoosterParams(queue_name='test_redis_ack_opp_publish', broker_kind=BrokerEnum.REDIS_ACK_ABLE,
                     concurrent_mode=ConcurrentModeEnum.SINGLE_THREAD,
                     log_level=10,  
                     publisher_override_cls=OppositeRedisPublisher, # 这个是核心，覆盖了发布者。
                     is_show_message_get_from_broker=True,broker_exclusive_config={'pull_msg_batch_size':1}))
def cost_long_time_fun(x):
    print(f'start {x}')
    time.sleep(2)
    print(fct.queue_name,fct.full_msg)
    if random.random()>0.5:
        cost_long_time_fun.publisher.OppositePublish(fct.full_msg) # 这个是后进但能先出
        return 
    print(f'end {x}')
    return x*2


if __name__ == '__main__':
    for i in range(100):
        cost_long_time_fun.push(i)
    cost_long_time_fun.consume()
    ctrl_c_recv()
