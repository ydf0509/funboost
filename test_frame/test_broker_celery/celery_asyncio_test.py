
from celery import Celery

app = Celery(__name__, broker='redis://127.0.0.1')

app.conf.task_routes = {'add2':{'queue':'add2'}}
import asyncio

# @app.task
# async def add(x, y):
#     await asyncio.sleep(1)
#     return x + y

@app.task(name='add2')
def add2(x, y):
    print(x,y)
    return x + y


if __name__ == '__main__':
    add2.delay(1,2)
    '''
    celery -A celery_asyncio_test worker -l info -P threads -Q '*' # chatgtp回答错误，celery 5.2.7 都不支持asyncio
    '''