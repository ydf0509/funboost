import time
from auto_run_on_remote import run_current_script_on_remote

run_current_script_on_remote()
from funboost import boost, BrokerEnum, PriorityConsumingControlConfig,FunctionResultStatusPersistanceConfig,BoosterParams

"""
演示多进程启动消费，多进程和 asyncio/threading/gevnt/evntlet是叠加关系，不是平行的关系。
"""


# qps=5，is_using_distributed_frequency_control=True 分布式控频每秒执行5次。
# 如果is_using_distributed_frequency_control不设置为True,默认每个进程都会每秒执行5次。
@boost(BoosterParams(queue_name='test_queue_s23', qps=1, broker_kind=BrokerEnum.REDIS,

       ))
def ff(x, y):
    import os
    time.sleep(2)
    print(os.getpid(), x, y)


if __name__ == '__main__':
    # ff.publish()
    ff.clear()


        # 这个与push相比是复杂的发布，第一个参数是函数本身的入参字典，后面的参数为任务控制参数，例如可以设置task_id，设置延时任务，设置是否使用rpc模式等。
        # ff.publish({'x': i * 10, 'y': i * 20}, )

    # ff(666, 888)  # 直接运行函数
    # ff.start()  # 和 conusme()等效
    # ff.consume()  # 和 start()等效
    # # run_consumer_with_multi_process(ff, 2)  # 启动两个进程
    # ff.multi_process_consume(3)
    for i in range(1000):
        ff.push(i, y=0)
    ff.multi_process_consume(3)  # 启动两个进程，和上面的run_consumer_with_multi_process等效,现在新增这个multi_process_start方法。
    # IdeAutoCompleteHelper(ff).multi_process_start(3)  # IdeAutoCompleteHelper 可以补全提示，但现在装饰器加了类型注释，ff. 已近可以在pycharm下补全了。

    time.sleep(100000)