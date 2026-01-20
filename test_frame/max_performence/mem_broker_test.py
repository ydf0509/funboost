
import time
import datetime
from funboost import boost, BoosterParams, BrokerEnum,ConcurrentModeEnum


total_cnt = 200000

class GlobalVars:
    t_start_publish = None
    t_end_publish = None
    t_start_consume = None
    t_end_consume = None


@boost(BoosterParams(queue_name='test_queue', broker_kind=BrokerEnum.MEMORY_QUEUE, 
concurrent_mode=ConcurrentModeEnum.SINGLE_THREAD, log_level=20,
# broker_exclusive_config={'pull_msg_batch_size':5000} , # redis模式支持
))
def f(x):
    if x == 0:
        GlobalVars.t_start_consume = time.time()
    if x == total_cnt:
        GlobalVars.t_end_consume = time.time()
    if x% 10000 == 0:
        print(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3], x)

if __name__ == '__main__':
    time.sleep(5)
    for i in range(0,total_cnt+1):
        if i == 0:
            GlobalVars.t_start_publish = time.time()
        if i == total_cnt:
            GlobalVars.t_end_publish = time.time()
        if i % 10000 == 0:
            print(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3], i)
        f.push(i)
     
    f.consume()
    
    while GlobalVars.t_end_consume is None:
        time.sleep(0.1)
    

    print(f"publish time: {GlobalVars.t_end_publish - GlobalVars.t_start_publish}")
    print(f"consume time: {GlobalVars.t_end_consume - GlobalVars.t_start_consume}")
    

    

    
