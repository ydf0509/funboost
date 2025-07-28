from apscheduler.jobstores.redis import RedisJobStore
from funboost.utils.redis_manager import RedisMixin,get_redis_conn_kwargs

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

    process_jobs_redis_lock_key = None

    def set_process_jobs_redis_lock_key(self, lock_key):
        self.process_jobs_redis_lock_key = lock_key
        return self

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
        """
        funboost 的做法是 在任务取出阶段就加锁，从根本上防止了重复执行。
        这个很关键，防止多个apscheduler 实例同时扫描取出同一个定时任务，间接导致重复执行,
        在apscheduler 3.xx版本这样写来防止多个apscheduler实例 重复执行定时任务的问题,简直是神操作.

        _process_jobs 功能是扫描取出需要运行的定时任务,而不是直接运行定时任务
        只要扫描取出任务不会取出相同的任务,就间接的决定了不可能重复执行相同的定时任务了.
        

        不要以为随便在你自己的消费函数加个redis分布式锁就不会重复执行任务了,redis分布式锁是解决相同代码块不会并发执行,而不是解决重复执行.
        但funboost是神级别骚操作,把分布式锁加到_process_jobs里面,
        _process_jobs是获取一个即将运行的定时任务,是扫描并删除这个即将运行的定时任务,
        所以这里加分布式锁能间接解决不重复运行定时任务,一旦任务被取出，就会从 jobstore 中删除,其他实例就无法再取到这个任务了.

        """
        if self.process_jobs_redis_lock_key is None:
            raise ValueError('process_jobs_redis_lock_key is not set')
        with RedisDistributedBlockLockContextManager(RedisMixin().redis_db_frame, self.process_jobs_redis_lock_key, ):
            return super()._process_jobs()


jobstores = {
    "default": RedisJobStore(**get_redis_conn_kwargs(),
                             jobs_key='funboost.apscheduler.jobs',run_times_key="funboost.apscheduler.run_times")
}

"""
建议不要亲自使用这个 funboost_background_scheduler_redis_store 对象，而是 ApsJobAdder来添加定时任务，自动多个apscheduler对象实例，
尤其是redis作为jobstores时候，使用不同的jobstores，每个消费函数使用各自单独的jobs_key和 run_times_key
"""
funboost_background_scheduler_redis_store = FunboostBackgroundSchedulerProcessJobsWithinRedisLock(timezone=FunboostCommonConfig.TIMEZONE, daemon=False, jobstores=jobstores)






"""
跨python解释器 跨机器动态修改定时任务配置的例子在

test_frame/test_apschedual/test_aps_redis_store.py
test_frame/test_apschedual/test_change_aps_conf.py

"""
