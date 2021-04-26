::  也可以用这个启动，没必要，直接启动 python test_test_celery_app.py  香多了
celery -A test_celery_app worker --pool=threads --concurrency=50  -n  worker1@%h  --loglevel=DEBUG  --queues=queue_f1,queue_add2,queue_sub2