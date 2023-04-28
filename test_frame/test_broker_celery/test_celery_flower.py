
import celery


CELERY_BROKER_URL = 'redis://:372148@106.55.244.110:6379/12'  # 使用celery作为中间件。funboost新增支持celery框架来运行函数
CELERY_RESULT_BACKEND = 'redis://:372148@106.55.244.110:6379/13'  # celery结果存放，可以为None

app = celery.Celery(broker=CELERY_BROKER_URL,backend=CELERY_RESULT_BACKEND)

queue_1 = 'celery_beat_queue_7a'

@app.task(name='celery_beat_queue_7a')
def f1(x,y):
    pass


'''
set PYTHONPATH=D:/codes/funboost   ; python -m  flower  -A  test_celery_flower --broker='redis://:372148@106.55.244.110:6379/12' --port=5555

 python -m celery --broker='redis://:372148@106.55.244.110:6379/12'  --result-backend='redis://:372148@106.55.244.110:6379/13'    flower --address=0.0.0.0 --port=5555 
'''