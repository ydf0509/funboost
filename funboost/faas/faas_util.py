
from funboost.core.active_cousumer_info_getter import SingleQueueConusmerParamsGetter

IS_AUTO_START_APSCHEDULER = True # 必须启动，不启动获取和添加不了定时任务.这个不要改成False。
IS_AUTO_PAUSED_APSCHEDULER = True # 你可以暂停定时器，网页端用于专门执行定时任务的增删改查，但不触发发送定时任务到消息队列。 在消费脚本部署booster启动消费和启动定时器并且不暂停。

def gen_aps_job_adder(queue_name, job_store_kind):
    return SingleQueueConusmerParamsGetter(queue_name).generate_aps_job_adder(
        job_store_kind=job_store_kind, is_auto_start=IS_AUTO_START_APSCHEDULER, is_auto_paused=IS_AUTO_PAUSED_APSCHEDULER)