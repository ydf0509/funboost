# import gevent.monkey;gevent.monkey.patch_all()
import time

from funboost import boost, BrokerEnum,ConcurrentModeEnum
import nb_log

logger = nb_log.get_logger('sdsda',is_add_stream_handler=False,log_filename='xxx.log')


@boost('test_speed_queuex', broker_kind=BrokerEnum.MEMORY_QUEUE, concurrent_num=2, log_level=20, qps=0, concurrent_mode=ConcurrentModeEnum.SINGLE_THREAD, )
def f_test_speed(x):
    pass
    # logger.debug(x)
    # f_test_speed2.push(x * 10)
    if x% 5000 == 0:
        print(x)
    # time.sleep(20)



# @boost('speed_test_queue2', broker_kind=BrokerEnum.REDIS, log_level=20, qps=2)
# def f_test_speed2(y):
#     pass
#     print(y)


if __name__ == '__main__':
    # f_test_speed.clear()

    for i in range(500000):
        f_test_speed.push(i)

    # f_test_speed.consume()
    f_test_speed.multi_process_consume(1)
    # # f_test_speed2.consume()
