from apscheduler.jobstores.redis import RedisJobStore
from funboost.utils.redis_manager import RedisMixin

from funboost.timing_job import FunboostBackgroundScheduler
from funboost.funboost_config_deafult import BrokerConnConfig, FunboostCommonConfig
from funboost.utils.decorators import RedisDistributedBlockLockContextManager


"""
这个是使用redis作为定时任务持久化，支持跨机器好跨进程，外部远程 动态修改/添加/删除定时任务
"""


class FunboostBackgroundSchedulerProcessJobsWithinRedisLock(FunboostBackgroundScheduler):
    """
    分布式或多进程都启动某个apscheduler实例，如果都使用的同一个数据库类型的jobstores ，_process_jobs有很大概率会造成报错， 因为_process_jobs使用的是线程锁，管不了其他进程和分布式机器。

    https://groups.google.com/g/apscheduler/c/Gjc_JQMPePc 问题也提到了这个bug

    继承 Custom schedulers https://apscheduler.readthedocs.io/en/3.x/extending.html   可以重写 _create_lock
    """

    process_jobs_redis_lock_key = f'funboost.BackgroundSchedulerProcessJobsWithinRedisLock'

    def set_process_jobs_redis_lock_key(self, lock_key):
        self.process_jobs_redis_lock_key = lock_key

    # def  _create_lock(self):
    #     return RedisDistributedBlockLockContextManager(RedisMixin().redis_db_frame,self.process_jobs_redis_lock_key,) 这个类的写法不适合固定的单例，
    #     RedisDistributedBlockLockContextManager的写法不适合 永远用一个 对象，所以还是放到 def  _process_jobs 里面运行

    # def _process_jobs(self):
    #     for i in range(10) :
    #         with RedisDistributedLockContextManager(RedisMixin().redis_db_frame, self.process_jobs_redis_lock_key, ) as lock:
    #             if lock.has_aquire_lock:
    #                 wait_seconds = super()._process_jobs()
    #                 return wait_seconds
    #             else:
    #                 time.sleep(0.1)
    #     return 0.1

    def _process_jobs(self):
        with RedisDistributedBlockLockContextManager(RedisMixin().redis_db_frame, self.process_jobs_redis_lock_key, ):
            return super()._process_jobs()


jobstores = {
    "default": RedisJobStore(db=BrokerConnConfig.REDIS_DB, host=BrokerConnConfig.REDIS_HOST,
                             port=BrokerConnConfig.REDIS_PORT, password=BrokerConnConfig.REDIS_PASSWORD,
                             username=BrokerConnConfig.REDIS_USERNAME, jobs_key='funboost.apscheduler.jobs',run_times_key="funboost.apscheduler.run_times")
}

funboost_background_scheduler_redis_store = FunboostBackgroundSchedulerProcessJobsWithinRedisLock(timezone=FunboostCommonConfig.TIMEZONE, daemon=False, jobstores=jobstores)






"""
跨python解释器 跨机器动态修改定时任务配置的例子在

test_frame/test_apschedual/test_aps_redis_store.py
test_frame/test_apschedual/test_change_aps_conf.py

"""
