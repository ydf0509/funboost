



from huey import RedisHuey, crontab

# huey = RedisHuey('my-app', host='127.0.0.1',db=7)
huey = RedisHuey('my-app', url='redis://127.0.0.1:6379/11',)


def my_filter(task):
    print(11111,task)
    if 1:
        return True
    else:
        return False

@huey.task(filter=my_filter)
def add_numbers(a, b):
    print(a + b)

@huey.task(retries=2, retry_delay=60)
def flaky_task(url):
    # This task might fail, in which case it will be retried up to 2 times
    # with a delay of 60s between retries.
    print(url)

@huey.periodic_task(crontab(minute='0', hour='3'))
def nightly_backup():
    print('定时任务')


if __name__ == '__main__':
    """
    cd test_frame/test_huey
    test_huey_raw.py
    
    huey_consumer.py test_huey_raw.huey -k process -w 4
    
    Consumer
    {'self': <huey.consumer.Consumer object at 0x000001F4D7AA94C8>, 'huey': <huey.api.RedisHuey object at 0x000001F4D7AA9B48>, 'workers': 1, 'periodic': True, 'initial_delay': 0.1, 'backoff': 1.15, 'max_delay': 10.0, 'scheduler_interval': 1, 'worker_type': 'thread', 'check_worker_health': True, 'health_check_interval': 10, 'flush_locks': False, 'extra_locks': None}

    """
