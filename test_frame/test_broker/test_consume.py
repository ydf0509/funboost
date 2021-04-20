import time
from function_scheduling_distributed_framework import task_deco,BrokerEnum,run_consumer_with_multi_process,ConcurrentModeEnum
import nb_log
# nb_log.reverse_patch_print()
@task_deco('test_kafka8',broker_kind=BrokerEnum.REDIS,qps=0,log_level=20,concurrent_mode=ConcurrentModeEnum.THREADING,create_logger_file=True)
def f(x):

    print(time.time(),x)
    # time.sleep(60)


if __name__ == '__main__':
    # f.consume()
    run_consumer_with_multi_process(f,1)