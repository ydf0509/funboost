import time


from test_frame.test_celery.test_celery_app import add, sub





t1 = time.time()
for i in range(300000):
    # print('生产者添加任务')
    print(i)
    # result = add.delay(i, i * 2)
    result = add.apply_async(args=(i, i * 2))
    # print(type(result))
    # sub.delay(i * 10, i * 20)


print(time.time() - t1)
print('任务添加完成')

"""
import celery
celery.result.AsyncResult
"""
