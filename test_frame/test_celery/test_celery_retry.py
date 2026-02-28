
import celery
from celery import Celery
import time

app = Celery('tasks', broker='redis://localhost:6379/0')

@app.task(bind=True,
          autoretry_for=(ZeroDivisionError,),   # 遇到这些异常自动重试
         retry_backoff=5,  # Factor in seconds (first retry: 5s, second: 10s, third: 20s, etc.)
    retry_jitter=False,  # Set False to disable randomization (use exact values: 5s, 10s, 20s)
    retry_kwargs={"max_retries": 3},
          )                   
def my_task(self, some_arg):
    # 可能会抛出 TemporaryError 的业务逻辑
    print(time.strftime("%H:%M:%S"))
    return 1/0



if __name__ == '__main__':

    print(celery.__version__)
    
    my_task.delay(1)

    app.worker_main(
        argv=['worker', '--pool=threads','--concurrency=500', '-n', 'worker1@%h', 
              '--loglevel=DEBUG',
            #   '--queues=test_pri'
              ]
        )