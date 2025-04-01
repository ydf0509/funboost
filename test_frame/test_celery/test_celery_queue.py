

# Celery 的写法
from celery import Celery

# 创建 Celery 实例时仍需要基础配置
app = Celery('myapp', broker='redis://localhost:6379/0')

@app.task(queue='my_queue_name1b')
def task_function(x):
    return x * 2


@app.task(queue='my_queue_name2b')
def task_function2(x):
    return x * 2

if __name__ == '__main__':
    task_function.delay(1)
    task_function2.delay(2)

    
    app.worker_main(
            argv=['worker', '--pool=threads','--concurrency=500', '-n', 'worker1@%h', '--loglevel=DEBUG',
                # '--queues=test_pri'
                ])