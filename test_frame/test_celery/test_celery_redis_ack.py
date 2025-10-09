



# Celery 的写法
from celery import Celery
import time
import kombu
# 创建 Celery 实例时仍需要基础配置
app = Celery('myapp', broker='redis://localhost:6379/11',backend='redis://localhost:6379/14')
app.conf.task_acks_late = True
app.conf.broker_transport_options = {
    'visibility_timeout': 5 
}
@app.task(name='task_function_name1', queue='my_queue_name1b6')
def task_function(x):
    print(f'task_function {x} 开始执行')
    time.sleep(60)
    print(f'task_function {x} 执行完成')
    return x 


if __name__ == '__main__':
    

    app.worker_main(
            argv=['worker', '--pool=threads','--concurrency=500', '-n', 'worker1@%h', '--loglevel=INFO',
                '--queues=my_queue_name1b6'
                ])