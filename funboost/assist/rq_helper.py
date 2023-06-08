import threading
import os
import uuid
from random import shuffle
from rq.worker import RandomWorker
import nb_log
from redis3 import Redis
from rq import Worker
from rq_win import WindowsWorker
from funboost import funboost_config_deafult

nb_log.get_logger('rq')


def _install_signal_handlers_monkey(self):
    """ 不能在非主线程中操作信号"""
    pass


Worker._install_signal_handlers = _install_signal_handlers_monkey


class RandomWindowsWorker(RandomWorker, WindowsWorker):
    """ 这个是为了 每个队列随机拉取，默认是前面的队列先消费完才会消费下一个队列名"""

    pass


class RqHelper:
    redis_conn = Redis.from_url(funboost_config_deafult.REDIS_URL)

    queue_name__rq_job_map = {}
    to_be_start_work_rq_queue_name_set = set()

    @classmethod
    def realy_start_rq_worker(cls):
        for i in range(50):
            threading.Thread(target=cls.__rq_work).start()

    @classmethod
    def __rq_work(cls):
        worker_cls = RandomWindowsWorker if os.name == 'nt' else RandomWorker
        worker = worker_cls(list(cls.to_be_start_work_rq_queue_name_set), connection=cls.redis_conn, name=uuid.uuid4().hex)
        worker.work()
