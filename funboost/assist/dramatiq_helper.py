import argparse
import nb_log
import dramatiq
from dramatiq.cli import main

from dramatiq.brokers.redis import RedisBroker

redis_broker = RedisBroker(host="127.0.0.1", port=6379)
dramatiq.set_broker(redis_broker)


"""
 {'max_age', 'throws', 'pipe_target', 'pipe_ignore', 'on_success', 'retry_when', 'time_limit', 'min_backoff', 'max_retries', 'max_backoff', 'notify_shutdown', 'on_failure'}
"""


class DramatiqHelper:
    logger = nb_log.get_logger('funboost.DramatiqHelper')
    broker = dramatiq.get_broker()
    to_be_start_work_celery_queue_name_set = set()  # 存放需要worker运行的queue name。

    queue_name__actor_map = {}

    @classmethod
    def realy_start_dramatiq_worker(cls):
        p = argparse.ArgumentParser()
        pa = p.parse_args()

        pa.broker = 'funboost.assist.dramatiq_helper'
        pa.modules = []
        pa.processes = 1
        pa.threads = 200
        pa.path = ''
        pa.queues = list(cls.to_be_start_work_celery_queue_name_set)
        pa.log_file = None
        pa.skip_logging = False
        pa.use_spawn = False
        pa.forks = []
        pa.worker_shutdown_timeout = 600000
        pa.verbose = 0
        pa.pid_file = None

        cls.logger.warning(f'dramatiq 命令行启动参数 {pa}')
        main(pa)


'''
Namespace(broker='test_dramatiq_raw', modules=[], processes=1, threads=8, path='.', queues=None, pid_file=None, log_file=None, skip_logging=False, use_spawn=False, forks=[], worker_shutdown_timeout=600000, verbose=0)
python -m dramatiq test_dramatiq_raw -p 1
'''
