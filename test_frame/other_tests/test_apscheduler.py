from funboost.utils.apscheduler_monkey import patch_run_job
patch_run_job()

from apscheduler.events import EVENT_JOB_MISSED
from apscheduler.executors.asyncio import AsyncIOExecutor
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.jobstores.redis import RedisJobStore
from apscheduler.schedulers.background import BackgroundScheduler
import datetime
import time
from apscheduler.schedulers . blocking import BlockingScheduler
import threading
import decorator_libs

def func(x,y,d):
    time.sleep(5)
    print(f'{d} {x} + {y} = {x + y}')

scheduler = BackgroundScheduler()
# scheduler.add_job(func,'date', run_date=datetime.datetime(2021, 5, 19, 10, 53, 20), args=(5, 6,))
# print(scheduler._executors)
scheduler.add_executor(ThreadPoolExecutor(1))
# scheduler.add_jobstore(RedisJobStore(jobs_key='apscheduler.jobs', run_times_key='apscheduler.run_times',db=6))
# scheduler.add_jobstore()


def job_miss(event):
    # print(event)
    # print(event.__dict__)
    # print(scheduler.get_job(event.job_id))
    print(event.function,event.function_kwargs,event.function_args)


scheduler.add_listener(job_miss, EVENT_JOB_MISSED)
scheduler.start()

with decorator_libs.TimerContextManager():
    for i in range(10):
        run_date = datetime.datetime(2021, 5, 19, 18, 56, 30) + datetime.timedelta(seconds=i)
        scheduler.add_job(func,'date',run_date=run_date , args=(i, i,run_date),misfire_grace_time=None)


print(datetime.datetime.now())
print('over')


while 1:
    # print(threading.active_count())
    # print(scheduler._executors)
    time.sleep(2)