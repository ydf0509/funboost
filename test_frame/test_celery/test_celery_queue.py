

# Celery 的写法
from celery import Celery
import time

from celery.utils.log import get_task_logger
logger = get_task_logger(__name__)

# 创建 Celery 实例时仍需要基础配置
app = Celery('myapp', broker='redis://localhost:6379/0')

@app.task(queue='my_queue_name1b',rate_limit='10/h')
def task_function(x):
    print('task_function运行',time.strftime('%Y-%m-%d %H:%M:%S'),x)
    logger.info(f'task_function运行 {time.strftime("%Y-%m-%d %H:%M:%S")} {x}')
    return x * 2


@app.task(queue='my_queue_name2b')
def task_function2(x):
    return x * 2

if __name__ == '__main__':
    for i in range(100):
        task_function.delay(i)
    # task_function2.delay(2)

    
    app.worker_main(
            argv=['worker', '--pool=threads','--concurrency=500', '-n', 'worker1@%h', '--loglevel=DEBUG',
                # '--queues=test_pri'
                ])