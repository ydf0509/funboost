import time

from function_scheduling_distributed_framework.utils import RedisMixin,LogManager
from test_frame.test_frame_using_thread.test_celery.test_celery_app import add

LogManager().get_logger_and_add_handlers()
RedisMixin().redis_db_frame.delete('queue_add')

t1 = time.time()
for i in range(100):
    # print('生产者添加任务')
    print(i)
    result = add.delay(i,i*2)
    print(type(result))
    # print(result.get())

print(time.time() -t1)
print('任务添加完成')


"""
import celery
celery.result.AsyncResult
"""





