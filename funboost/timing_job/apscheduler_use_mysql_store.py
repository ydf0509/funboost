from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore

from funboost import funboost_config_deafult

from funboost.timing_job import FsdfBackgroundScheduler


"""
这个是使用mysql作为定时任务持久化，支持动态修改 添加定时任务
"""