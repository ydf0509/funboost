
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import time
from threading import Thread
# from concurrent.futures import ThreadPoolExecutor
from apscheduler.executors.pool import ThreadPoolExecutor, ProcessPoolExecutor,BasePoolExecutor

from funboost.concurrent_pool.custom_threadpool_executor import ThreadPoolExecutorShrinkAbleNonDaemon

# ThreadPoolExecutorShrinkAbleNonDaemon


class ThreadPoolExecutorForAps(BasePoolExecutor):
    """
    An executor that runs jobs in a concurrent.futures thread pool.

    Plugin alias: ``threadpool``

    :param max_workers: the maximum number of spawned threads.
    :param pool_kwargs: dict of keyword arguments to pass to the underlying
        ThreadPoolExecutor constructor
    """

    def __init__(self, max_workers=100, pool_kwargs=None):
        pool = ThreadPoolExecutorShrinkAbleNonDaemon(int(max_workers), )
        super().__init__(pool)

executors = {
    'default': ThreadPoolExecutor(10) , # 默认线程池，最大线程数 10
    'non_daemon': ThreadPoolExecutorForAps(10) , # 默认线程池，最大线程数 10
}


def job():
    print("执行任务:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))


def t1():
    while 1:
        time.sleep(10)
        print('sleep 10 seconds')

if __name__ == "__main__":
    t = Thread(target=t1)
    t.start()

    scheduler = BackgroundScheduler(executors=executors)
    
    # 每 3 秒执行一次
    scheduler.add_job(job, trigger='interval', seconds=30,executor='non_daemon')
    
    # 启动调度器（后台线程）
    scheduler.start()
    
    print("调度器已启动，主线程继续运行...")

    
    # try:0
    #     # 主线程可以做其他事情，这里用 sleep 模拟
    #     while True:
    #         print("主线程工作中...")
    #         time.sleep(5)
    # except (KeyboardInterrupt, SystemExit):
    #     scheduler.shutdown()
    #     print("调度器已关闭")

