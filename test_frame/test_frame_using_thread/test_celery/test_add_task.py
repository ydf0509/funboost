import time

from function_scheduling_distributed_framework.utils import RedisMixin
from test_frame.test_frame_using_thread.test_celery.test_celery_app import add

RedisMixin().redis_db_frame.delete('queue_add')

t1 = time.time()
for i in range(10000):
    # print('生产者添加任务')
    add.delay(i,i*2)

print(time.time() -t1)
print('任务添加完成')









