
from funboost.timing_job.apscheduler_use_redis_store import funboost_background_scheduler_redis_store
from test_frame.test_apschedual.test_aps_redis_store import consume_func

"""
此文件是测试修改定时任务配置，另一个脚本的一启动的定时任务配置，会自动发生变化。因为定时任务配置通过中间件存储和通知了。
"""

funboost_background_scheduler_redis_store.remove_all_jobs()

funboost_background_scheduler_redis_store.add_push_job(consume_func,  # 这里也可以用 my_push函数秒，那样就不用传递函数的位置和名字了，看test_aps_redis_store.py。
                                                       'interval', id='15', name='namexx', seconds=4,
                                                       kwargs={"x": 19, "y": 33},
                                                       replace_existing=True)   # replace_existing 就是如果id已存在就修改，不存在则添加。


