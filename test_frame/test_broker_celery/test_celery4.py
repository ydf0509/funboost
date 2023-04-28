

from celery import Celery

app = Celery(main='abcd')

app2 = Celery(main='abcd')

print(app,app2)