"""
测试redis无其他逻辑时候的性能
"""
from redis3 import Redis
import decorator_libs
import nb_log

r = Redis(decode_responses=True)

# with decorator_libs.TimerContextManager():
#     for i in range(1000000):
#         print(i)
#         r.lpush('test_performance',i)


# while 1:
#     result = r.brpop('test_performance')
#     print(result)

# for i in range(100000):
#     print(i)
#     r.xadd('testp2',{"":i})


