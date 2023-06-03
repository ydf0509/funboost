
from funboost.timing_job.apscheduler_use_redis_store import funboost_background_scheduler_redis_store
from test_frame.test_apschedual.test_aps_redis_store import consume_func

"""
此文件是测试修改定时任务配置，另一个脚本的一启动的定时任务配置，会自动发生变化。因为定时任务配置通过中间件存储和通知了。
"""

# 修改或添加定时任务必须执行.start，值修改配置但不想执行函数，就设置paused=True
funboost_background_scheduler_redis_store.start(paused=True) # 此脚本是演示远程动态修改的脚本，动态新增或删除定时任务配置，但不执行定时任务执行。注意是 paused=True

# 查看数据库中的所有定时任务配置
print(funboost_background_scheduler_redis_store.get_jobs())

#  删除数据库中所有已添加的定时任务配置
# funboost_background_scheduler_redis_store.remove_all_jobs()

# 删除数据库中已添加的id为691的定时任务配置
# funboost_background_scheduler_redis_store.remove_job(job_id='691')

# 增加或修改定时任务配置 replace_existing=True 就是如果id已存在就修改，不存在则添加。
funboost_background_scheduler_redis_store.add_push_job(consume_func,
                                                       'interval', id='15', name='namexx', seconds=4,
                                                       kwargs={"x": 19, "y": 33},
                                                       replace_existing=True)




