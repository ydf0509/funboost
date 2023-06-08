import os
import threading
import time
import uuid

import nb_log
from redis import Redis
from rq import Queue,Connection, Worker
from rq.decorators import job
from rq_win import WindowsWorker

q = Queue(connection=Redis())

import requests


nb_log.get_logger('rq')
nb_log.get_logger('rq_win')
redis_conn = Redis()

@job(queue='my_queue',connection=Redis())
def count_words_at_url(url):
    time.sleep(5)
    resp = requests.get(url)
    print(6666,os.getpid(),threading.get_ident(),url)
    return len(resp.text)




'''
from rq import Connection, Worker

# 设置 Redis 连接
redis_conn = Redis(host='localhost', port=6379)

# 在 RQ 上下文中启动 worker
with Connection(redis_conn):
    worker = Worker(['my_queue'])
    worker.work()
'''

'''
D:\ProgramData\Miniconda3\Lib\site-packages\rq\worker.py

   def _install_signal_handlers(self):
        """Installs signal handlers for handling SIGINT and SIGTERM
        gracefully.
        """
        pass
        # signal.signal(signal.SIGINT, self.request_stop)
        # signal.signal(signal.SIGTERM, self.request_stop)
        
        多线程worker运行要打猴子补丁。
'''

def work(queues):
    worker = WindowsWorker(queues, connection=redis_conn,name=uuid.uuid4().hex)
    worker.work()

if __name__ == '__main__':
    '''
    rq worker
    rqworkor
    
    rqworker -w rq_win.WindowsWorker
    '''

    for i in range(50):
        threading.Thread(target=work,args=(['my_queue'],)).start()
        