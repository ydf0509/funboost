import time

from apscheduler.jobstores.redis import RedisJobStore
from funboost.timing_job.apscheduler_use_redis_store import funboost_background_scheduler_redis_store

from funboost.funboost_config_deafult import BrokerConnConfig
from funboost.timing_job import FsdfBackgroundScheduler

jobstores = {
    "default": RedisJobStore(db=4, host=BrokerConnConfig.REDIS_HOST,
                             port=BrokerConnConfig.REDIS_PORT, password=BrokerConnConfig.REDIS_PASSWORD,),

"default2": RedisJobStore(db=6, host=BrokerConnConfig.REDIS_HOST,
                             port=BrokerConnConfig.REDIS_PORT, password=BrokerConnConfig.REDIS_PASSWORD,)

}

# funboost_background_scheduler_redis_store = FsdfBackgroundScheduler(timezone=funboost_config_deafult.TIMEZONE, daemon=False, jobstores=jobstores)




# funboost_background_scheduler_redis_store.add_job(f,'interval', id='17', name='namexx3', seconds=5,
#                                                   args=(1,2),replace_existing=True)

funboost_background_scheduler_redis_store.start()


while 1:
    time.sleep(20)