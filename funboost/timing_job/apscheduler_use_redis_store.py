from apscheduler.jobstores.redis import RedisJobStore

from funboost import funboost_config_deafult

from funboost.timing_job import FsdfBackgroundScheduler

"""
这个是使用redis作为定时任务持久化，支持动态修改 添加定时任务
"""

jobstores = {
    "default": RedisJobStore(db=funboost_config_deafult.REDIS_DB, host=funboost_config_deafult.REDIS_HOST,
                             port=funboost_config_deafult.REDIS_PORT, password=funboost_config_deafult.REDIS_PASSWORD)
}

funboost_background_scheduler_redis_store = FsdfBackgroundScheduler(timezone=funboost_config_deafult.TIMEZONE, daemon=False, jobstores=jobstores)





"""
跨python解释器 跨机器动态修改定时任务配置的例子在

test_frame/test_apschedual/test_aps_redis_store.py
test_frame/test_apschedual/test_change_aps_conf.py

"""