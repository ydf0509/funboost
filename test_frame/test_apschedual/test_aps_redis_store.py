import time

import apscheduler.jobstores.base
import datetime

from apscheduler.schedulers.base import STATE_RUNNING

import nb_log
from funboost import boost, BrokerEnum
from funboost.timing_job.apscheduler_use_redis_store import funboost_background_scheduler_redis_store
from funboost.timing_job.push_fun_for_apscheduler_use_db import push_for_apscheduler_use_db

nb_log.get_logger('apscheduler')
'''
test_frame/test_apschedual/test_aps_redis_store.py
和 test_frame/test_apschedual/test_change_aps_conf.py  搭配测试，动态修改定时任务

test_change_aps_conf.py 中修改定时任务间隔和函数入参，test_aps_redis_store.py定时任务就会自动更新变化。
'''

@boost('queue_test_aps_redis', broker_kind=BrokerEnum.LOCAL_PYTHON_QUEUE)
def consume_func(x, y):
    print(f'{x} + {y} = {x + y}')


def my_push(x,y): # 推荐这样做，自己写个发布函数
    consume_func.push(x,y)


if __name__ == '__main__':
    # funboost_background_scheduler_redis_store.remove_all_jobs() # 删除数据库中所有已配置的定时任务
    consume_func.clear()
    #
    funboost_background_scheduler_redis_store.start(paused=False)
    #
    try:
        # funboost_background_scheduler_redis_store.add_job(push_for_apscheduler_use_db, # 这个可以，定时调用push_for_apscheduler_use_db，需要把文件路径和函数名字传来。
        #                                                   'interval', id='6', name='namexx', seconds=3,
        #                                                   args=('test_frame/test_apschedual/test_aps_redis_store.py', 'consume_func'), kwargs={"x": 5, "y": 6},
        #                                                   replace_existing=False)

        # funboost_background_scheduler_redis_store.add_job(consume_func.push,       # 使用数据库持久化定时任务，这样做是不行的，consume_func.push不可picke序列化存储到redis或者mysql mongo。
        #                                                   'interval', id='66', name='namexx', seconds=3,
        #                                                   kwargs={"x": 5, "y": 6},
        #                                                   replace_existing=False)

        funboost_background_scheduler_redis_store.add_job(my_push,       # 这样做是可以的，用户自己定义一个函数，可picke序列化存储到redis或者mysql mongo。推荐这样。
                                                          'interval', id='68', name='namexx', seconds=3,
                                                          kwargs={"x": 5, "y": 6},
                                                          replace_existing=False)
        funboost_background_scheduler_redis_store.add_job(my_push,  # 这样做是可以的，用户自己定义一个函数，可picke序列化存储到redis或者mysql mongo。推荐这样。
                                                          'interval', id='69', name='namexx', seconds=5,
                                                          kwargs={"x": 7, "y": 8},
                                                          replace_existing=False)
    except apscheduler.jobstores.base.ConflictingIdError as e:
        print('定时任务id已存在： {e}')

    consume_func.consume()

    # while 1:
    #     time.sleep(5)
    #     print(funboost_background_scheduler_redis_store.state)
    #     print(funboost_background_scheduler_redis_store._event.is_set())
    #     if funboost_background_scheduler_redis_store.state == STATE_RUNNING:
    #         funboost_background_scheduler_redis_store.wakeup()





