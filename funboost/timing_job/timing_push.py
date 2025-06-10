from funboost.utils import redis_manager
from funboost.core.booster import BoostersManager, Booster

from apscheduler.jobstores.redis import RedisJobStore
from funboost.timing_job.timing_job_base import funboost_aps_scheduler, undefined
from funboost.timing_job.apscheduler_use_redis_store import FunboostBackgroundSchedulerProcessJobsWithinRedisLock
from funboost.funboost_config_deafult import FunboostCommonConfig
from apscheduler.schedulers.base import BaseScheduler


class ApsJobAdder:
    """
    20250116新增加的统一的新增定时任务的方式，推荐这种方式。
    用户不用像之前再去关心使用哪个apscheduler对象去添加定时任务了。

    例如 add_numbers 是@boost装饰的消费函数
    ApsJobAdder(add_numbers,job_store_kind='memory').add_push_job(
        args=(1, 2),
        trigger='date',  # 使用日期触发器
        run_date='2025-01-16 18:23:50',  # 设置运行时间
        # id='add_numbers_job'  # 任务ID
    )

    """

    queue__redis_aps_map = {}

    def __init__(self, booster: Booster, job_store_kind: str = 'memory',is_auto_start=True,is_auto_paused=False):
        """
        Initialize the ApsJobAdder.

        :param booster: A Booster object representing the function to be scheduled.
        :param job_store_kind: The type of job store to use. Default is 'memory'.
                               Can be 'memory' or 'redis'.
        """
        self.booster = booster
        self.job_store_kind = job_store_kind
        if getattr(self.aps_obj, 'has_started_flag', False) is False:
            if is_auto_start:
                self.aps_obj.has_started_flag = True
                self.aps_obj.start(paused=is_auto_paused)



    @classmethod
    def get_funboost_redis_apscheduler(cls, queue_name):
        """ 
        每个队列名字的定时任务用不同的redis jobstore的 jobs_key 和 run_times_key，防止互相干扰和取出不属于自己的任务
        """
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
    def aps_obj(self) -> BaseScheduler:
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
                     replace_existing=False, **trigger_args, ):
        """
        1. 这里的入参都是和apscheduler的add_job的入参一样的，funboost作者没有创造新的入参。
        但是官方apscheduler的入参第一个入参是函数，
        funboost的ApsJobAdder对象.add_push_job入参去掉了函数，因为类的实例化时候会把函数传进来，不需要再麻烦用户一次了。
        

        2. add_push_job目的是 定时运行 消费函数.push方法发布消息到消费队列， 而不是 定时直接运行 消费函数自身。

        相当于 aps_obj.add_job(消费函数.push, trigger, args, kwargs, id, name, .....)
        那为什么 不直接使用 aps_obj.add_job(消费函数.push, trigger, args, kwargs, id, name, .....) 呢？因为 消费函数.push是实例方法，
        如果redis作为 jobstore， 消费函数.push 会报错，因为 消费函数.push 是实例方法，不能被序列化。只有普通函数和静态方法才能被序列化。
        所以开发了一个 add_push_job方法， 里面再去用 add_job， 使用 push_fun_params_to_broker 这个普通函数作为 add_job 的第一个入参，
        这个普通函数里面再去调用 消费函数.push 方法， 相当于是曲线救国避免 aps_obj.add_job(消费函数.push 不可序列化问题。


        3. 用户也可以自己定义一个普通函数my_push，你这个普通函数my_push 里面去调用消费函数.push方法；然后使用 aps_obj.add_job 使用你自己定义的这个my_push作为第一个入参。
        这种方式更容易你去理解，和apscheduler 官方库的原生写法一模一样。 但是不如 add_push_job 方便，因为 需要你亲自给每个消费函数分别定义一个普通函数my_push。

        """

        # if not getattr(self.aps_obj, 'has_started_flag', False):
        #     self.aps_obj.has_started_flag = True
        #     self.aps_obj.start(paused=False)
        return self.aps_obj.add_push_job(self.booster, trigger, args, kwargs, id, name,
                                         misfire_grace_time, coalesce, max_instances,
                                         next_run_time, jobstore, executor,
                                         replace_existing, **trigger_args, )


if __name__ == '__main__':
    """
    2025年后定时任务现在推荐使用 ApsJobAdder 写法 ，用户不需要亲自选择使用 apscheduler对象来添加定时任务
    """
    from funboost import boost, BrokerEnum, ctrl_c_recv, BoosterParams, ApsJobAdder


    # 定义任务处理函数
    @BoosterParams(queue_name='sum_queue3', broker_kind=BrokerEnum.REDIS)
    def sum_two_numbers(x, y):
        result = x + y
        print(f'The sum of {x} and {y} is {result}')

    # 启动消费者
    sum_two_numbers.consume()

    # 发布任务
    sum_two_numbers.push(3, 5)
    sum_two_numbers.push(10, 20)



    # 使用ApsJobAdder添加定时任务， 里面的定时语法，和apscheduler是一样的，用户需要自己熟悉知名框架apscheduler的add_job定时入参

    # 方式1：指定日期执行一次
    ApsJobAdder(sum_two_numbers, job_store_kind='redis').add_push_job(
        trigger='date',
        run_date='2025-01-17 23:25:40',
        args=(7, 8),
        id='date_job1'
    )

    # 方式2：固定间隔执行
    ApsJobAdder(sum_two_numbers, job_store_kind='memory').add_push_job(
        trigger='interval',
        seconds=5,
        args=(4, 6),
        id='interval_job1'
    )

    # 方式3：使用cron表达式定时执行
    ApsJobAdder(sum_two_numbers, job_store_kind='redis').add_push_job(
        trigger='cron',
        day_of_week='*',
        hour=23,
        minute=49,
        second=50,
        kwargs={"x": 50, "y": 60},
        replace_existing=True,
        id='cron_job1')

    ctrl_c_recv()
