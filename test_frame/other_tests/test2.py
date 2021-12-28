import datetime
from copyreg import pickle

# print(datetime.datetime.now())
import time

# import nb_log
# import decorator_libs
# import pysnooper_click_able
t1 = time.time()

#
# # @pysnooper_click_able.snoop(depth=10000)
# def f():
#     import funboost
#
#
# f()
# print(time.time() - t1)
# import pickle
# import threading
# import redis
#
# class CannotPickleObject:
#     def __init__(self):
#         self._lock = threading.Lock()
#
#
# class CannotPickleObject2:
#     def __init__(self):
#         self._redis = redis.Redis()
#
# print(pickle.dumps(CannotPickleObject()))
# print(pickle.dumps(CannotPickleObject2()))

from funboost import boost, BrokerEnum, IdeAutoCompleteHelper, PriorityConsumingControlConfig, run_consumer_with_multi_process


@boost('test_queue', broker_kind=BrokerEnum.REDIS)
def ff(x, y):
    import os
    time.sleep(10)
    print(os.getpid(), x, y)


if __name__ == '__main__':
    # ff.publish()
    ff.clear() # 清除
    for i in range(1000):
        ff.push(i, y=i * 2)

        # 这个与push相比是复杂的发布，第一个参数是函数本身的入参字典，后面的参数为任务控制参数，例如可以设置task_id，设置延时任务，设置是否使用rpc模式等。
        ff.publish({'x': i * 10, 'y': i * 2}, priority_control_config=PriorityConsumingControlConfig(countdown=1, misfire_grace_time=1))

    ff(666, 888)  # 直接运行函数
    ff.start()  # 和 conusme()等效
    ff.consume()  # 和 start()等效
    run_consumer_with_multi_process(ff, 2)  # 启动两个进程
    ff.multi_process_start(2)  # 启动两个进程，和上面的run_consumer_with_multi_process等效,现在新增这个multi_process_start方法。
    # IdeAutoCompleteHelper(ff).multi_process_start(3)  # IdeAutoCompleteHelper 可以补全提示，但现在装饰器加了类型注释，ff. 已近可以在pycharm下补全了。
