from celery.schedules import crontab
from datetime import timedelta

from funboost.consumers.celery_consumer import celery_start_beat

beat_schedule = {
    'add-every-10-seconds_job': {
        'task': 'celery_beat_queue_7',
        # 'schedule': timedelta(seconds=10),
'schedule': crontab(minute=36, hour=16),
        'args': (10000, 20000)
    }}

if __name__ == '__main__':
    celery_start_beat(beat_schedule)
