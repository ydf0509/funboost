from test_celery_consume2_thread import f1
from celery.result import AsyncResult

res = f1.push(100, 400) # type: AsyncResult

res.revoke(terminate=True)

print(res.result)