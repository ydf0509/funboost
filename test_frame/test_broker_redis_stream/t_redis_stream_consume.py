


import time
from funboost import boost, BrokerEnum,BoosterParams,ctrl_c_recv


@BoosterParams(queue_name='test_redis_stream_queue_2',
               broker_kind=BrokerEnum.REDIS_STREAM,
               is_show_message_get_from_broker=True, )
def test_fun(x):
   print(f'start to work {x}')
   time.sleep(x)
   print(f'end to work {x}')

if __name__ == '__main__':
    test_fun.consume()