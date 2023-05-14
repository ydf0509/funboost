import time

from apscheduler.jobstores.redis import RedisJobStore

from funboost import funboost_config_deafult
from funboost.timing_job import FsdfBackgroundScheduler

jobstores = {
    "default": RedisJobStore(db=4, host=funboost_config_deafult.REDIS_HOST,
                             port=funboost_config_deafult.REDIS_PORT, password=funboost_config_deafult.REDIS_PASSWORD,),

"default2": RedisJobStore(db=6, host=funboost_config_deafult.REDIS_HOST,
                             port=funboost_config_deafult.REDIS_PORT, password=funboost_config_deafult.REDIS_PASSWORD,)

}

funboost_background_scheduler_redis_store = FsdfBackgroundScheduler(timezone=funboost_config_deafult.TIMEZONE, daemon=False, jobstores=jobstores)


def f(x,y):
    print(x,y)

funboost_background_scheduler_redis_store.add_job(f,'interval', id='17', name='namexx3', seconds=5,
                                                  args=(1,2),replace_existing=True)

funboost_background_scheduler_redis_store.start()


while 1:
    time.sleep(20)