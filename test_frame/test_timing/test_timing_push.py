import threading

import time

from funboost import fsdf_background_scheduler, timing_publish_deco
from test_frame.test_timing.test_timming import consume_func

fsdf_background_scheduler.add_job(timing_publish_deco(consume_func), 'interval', id='3_second_job', seconds=3, kwargs={"x": 5, "y": 6})  # 每隔3秒发布一次任务，自然就能每隔3秒消费一次任务了。
# fsdf_background_scheduler.add_job(timing_publish_deco(consume_func), 'date', run_date=datetime.datetime(2020, 7, 24, 13, 53, 6), args=(5, 6,))  # 定时，只执行一次
# fsdf_background_scheduler.add_timing_publish_job(consume_func, 'cron', day_of_week='*', hour=14, minute=51, second=20, args=(5, 6,))  # 定时，每天的11点32分20秒都执行一次。
# fsdf_background_scheduler.add_timing_publish_job(consume_func, 'cron', day_of_week='*', hour='*', minute='*', second=20, args=(5, 6,))  # 定时，每分钟的第20秒执行一次
# 启动定时
fsdf_background_scheduler.start()
#
# while 1:
#     time.sleep(100)


