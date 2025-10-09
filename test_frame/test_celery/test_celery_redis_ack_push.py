import time

from test_celery_redis_ack import task_function

if __name__ == '__main__':
    result = task_function.delay(time.strftime('%Y-%m-%d %H:%M:%S') + 'hello')
    print(f"Task sent with ID: {result.id}")