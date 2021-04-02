# import gevent.monkey;gevent.monkey.patch_all()
import time

from function_scheduling_distributed_framework import task_deco, BrokerEnum,run_consumer_with_multi_process,ConcurrentModeEnum
import nb_log

logger = nb_log.get_logger('sdsda',is_add_stream_handler=False,log_filename='xxx.log')


@task_deco('speed_test_queue', broker_kind=BrokerEnum.REDIS,concurrent_num=2, log_level=20, qps=0,concurrent_mode=ConcurrentModeEnum.THREADING)
def f_test_speed(x):
    pass
    # logger.debug(x)
    # f_test_speed2.push(x * 10)
    print(x)
    # time.sleep(20)


# @task_deco('speed_test_queue2', broker_kind=BrokerEnum.REDIS, log_level=20, qps=2)
# def f_test_speed2(y):
#     pass
#     print(y)


if __name__ == '__main__':
    # f_test_speed.clear()

    # for i in range(1000000):
    #     f_test_speed.push(i)

    # f_test_speed.consume()
    run_consumer_with_multi_process(f_test_speed,1)
    # # f_test_speed2.consume()
