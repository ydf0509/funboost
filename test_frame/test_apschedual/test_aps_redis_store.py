
import apscheduler.jobstores.base
import nb_log
from funboost import boost, BrokerEnum,run_forever
from funboost.timing_job.apscheduler_use_redis_store import funboost_background_scheduler_redis_store

nb_log.get_logger('apscheduler')
'''
test_frame/test_apschedual/test_aps_redis_store.py
和 test_frame/test_apschedual/test_change_aps_conf.py  搭配测试，动态修改定时任务

test_change_aps_conf.py 中修改定时任务间隔和函数入参，test_aps_redis_store.py定时任务就会自动更新变化。
'''

@boost('queue_test_aps_redis', broker_kind=BrokerEnum.LOCAL_PYTHON_QUEUE)
def consume_func(x, y):
    print(f'{x} + {y} = {x + y}')


if __name__ == '__main__':
    # funboost_background_scheduler_redis_store.remove_all_jobs() # 删除数据库中所有已配置的定时任务
    consume_func.clear()
    #
    funboost_background_scheduler_redis_store.start(paused=False)  # 此脚本是演示不重启的脚本，动态读取新增或删除的定时任务配置，并执行。注意是 paused=False
    #
    try:

        funboost_background_scheduler_redis_store.add_push_job(consume_func,  # 这样做是可以的，用户自己定义一个函数，可picke序列化存储到redis或者mysql mongo。推荐这样。
                                                          'interval', id='691', name='namexx', seconds=5,
                                                          kwargs={"x": 7, "y": 8},
                                                          replace_existing=False)
    except apscheduler.jobstores.base.ConflictingIdError as e:
        print('定时任务id已存在： {e}')

    consume_func.consume()
    run_forever()






