from datetime import timedelta

from funboost.consumers.celery_consumer import CeleryBeat

beat_conf = {
    'add-every-30-seconds': {
        'task': 'celery_beat_queue_7',
        'schedule': timedelta(seconds=2),
        'args': (10000, 20000)
    }}

celery_beat = CeleryBeat(beat_conf)
# celery_app = celery_beat.get_celery_app()

if __name__ == '__main__':
    pass
    # funboost_celery_beat.start()
    '''
    set  PYTHONPATH=D:\codes\funboost\ && celery -A test_celery_beat beat
    '''
    celery_beat.start_beat()
