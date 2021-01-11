import time

from function_scheduling_distributed_framework.utils import RedisMixin, LogManager
from test_frame.test_celery.test_celery_app import add, sub

LogManager().get_logger_and_add_handlers()
RedisMixin().redis_db_frame.delete('queue_add')
RedisMixin().redis_db_frame.delete('queue_sub')

t1 = time.time()
for i in range(3):
    # print('生产者添加任务')
    print(i)
    # result = add.delay(i, i * 2)
    result = add.apply_async(args=(i, i * 2),countdown=120)
    # print(type(result))
    # sub.delay(i * 10, i * 20)


print(time.time() - t1)
print('任务添加完成')

"""
import celery
celery.result.AsyncResult
"""
