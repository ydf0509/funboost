

from celery import Celery


app = Celery('tasks', broker='redis://localhost:6379/3', backend='redis://localhost:6379/3')

app.send_task('tasks.funx', args=(2, 2),queue='queue1')