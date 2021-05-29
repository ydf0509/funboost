import time
import nb_log

from test_frame.test_celery.test_celery_app import add, sub



t1 = time.time()
for i in range(1,20000):
    # print('生产者添加任务')
    # print(i)
    # result = add.delay(i, i * 2)
    # time.sleep(0.01)
    result = add.apply_async(args=(i, i * 2),countdown=0)
    # result = add.apply_async(args=(i, i * 2), )
    print(result)
    # print(result.get())
    # print(type(result))
    # sub.delay(i * 10, i * 20)


print(time.time() - t1)
print('任务添加完成')

"""
import celery
celery.result.AsyncResult
"""
