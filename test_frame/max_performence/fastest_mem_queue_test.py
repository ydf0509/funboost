
import time
import datetime
from funboost import boost, BoosterParams, BrokerEnum,ConcurrentModeEnum
from nb_libs.system_monitoring import thread_show_system_cpu_usage,thread_show_process_cpu_usage,thread_show_cpu_per_core


total_cnt = 200000

class GlobalVars:
    t_start_publish = None
    t_end_publish = None
    t_start_consume = None
    t_end_consume = None


@boost(BoosterParams(queue_name='test_queue', broker_kind=BrokerEnum.FASTEST_MEM_QUEUE, 
concurrent_mode=ConcurrentModeEnum.SINGLE_THREAD, log_level=20,
 broker_exclusive_config={
        "pull_msg_batch_size": 1000,  # 默认单条拉取，批量建议设置 100-5000
        "ultra_fast_mode": True,  # 极速模式，跳过框架开销
    },
))
def f(x):
    if x == 0:
        GlobalVars.t_start_consume = time.time()
    if x == total_cnt:
        GlobalVars.t_end_consume = time.time()
    if x% 10000 == 0:
        print(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3], x)

if __name__ == '__main__':
    thread_show_process_cpu_usage()
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
    

    

    
