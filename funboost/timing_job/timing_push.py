from funboost.utils import redis_manager
from funboost.core.booster import BoostersManager, Booster

from apscheduler.jobstores.redis import RedisJobStore
from funboost.timing_job.timing_job_base import funboost_aps_scheduler, undefined
from funboost.timing_job.apscheduler_use_redis_store import FunboostBackgroundSchedulerProcessJobsWithinRedisLock
from funboost.funboost_config_deafult import FunboostCommonConfig


class ApsJobAdder:
    """
    20250116新增加的统一的新增定时任务的方式，
    用户不用像之前再去关心使用哪个apscheduler对象去添加定时任务了。

    ApsJobAdder(add_numbers,job_store_kind='memory').add_push_job(
        args=(1, 2),
        trigger='date',  # 使用日期触发器
        run_date='2025-01-16 18:23:50',  # 设置运行时间
        # id='add_numbers_job'  # 任务ID
    )

    """

    queue__redis_aps_map = {}

    def __init__(self, booster: Booster, job_store_kind: str = 'memory'):
        """
        Initialize the ApsJobAdder.

        :param booster: A Booster object representing the function to be scheduled.
        :param job_store_kind: The type of job store to use. Default is 'memory'.
                               Can be 'memory' or 'redis'.
        """
        self.booster = booster
        self.job_store_kind = job_store_kind

    @classmethod
    def get_funboost_redis_apscheduler(cls, queue_name):
        if queue_name in cls.queue__redis_aps_map:
            return cls.queue__redis_aps_map[queue_name]
        redis_jobstores = {

            "default": RedisJobStore(**redis_manager.get_redis_conn_kwargs(),
                                     jobs_key=f'funboost.apscheduler.{queue_name}.jobs',
                                     run_times_key=f'funboost.apscheduler.{queue_name}.run_times',
                                     )
        }
        redis_aps = FunboostBackgroundSchedulerProcessJobsWithinRedisLock(timezone=FunboostCommonConfig.TIMEZONE,
                                                                          daemon=False, jobstores=redis_jobstores)
        cls.queue__redis_aps_map[queue_name] = redis_aps
        return redis_aps

    @property
    def aps_obj(self):
        if self.job_store_kind == 'redis':
            return self.get_funboost_redis_apscheduler(self.booster.queue_name)
        elif self.job_store_kind == 'memory':
            return funboost_aps_scheduler
        else:
            raise ValueError('Unsupported job_store_kind')

    def add_push_job(self, trigger=None, args=None, kwargs=None, 
                     id=None, name=None,
                     misfire_grace_time=undefined, coalesce=undefined, max_instances=undefined,
                     next_run_time=undefined, jobstore='default', executor='default',
                     replace_existing=False, **trigger_args,):
        # if
        if not getattr(self.aps_obj, 'has_started_flag', False):
            self.aps_obj.has_started_flag = True
            self.aps_obj.start(paused=False)
        return self.aps_obj.add_push_job(self.booster, trigger, args, kwargs, id, name,
                                         misfire_grace_time, coalesce, max_instances,
                                         next_run_time, jobstore, executor,
                                         replace_existing, **trigger_args, )
