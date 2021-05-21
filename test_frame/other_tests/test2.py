import datetime
from copyreg import pickle

print(datetime.datetime.now())
import time

# import nb_log
# import decorator_libs
# import pysnooper_click_able
t1 = time.time()


# @pysnooper_click_able.snoop(depth=10000)
def f():
    import function_scheduling_distributed_framework


f()
print(time.time() - t1)
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
