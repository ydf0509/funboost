from funboost import funboost_aps_scheduler,run_forever
from test_frame.test_timing.test_timming import consume_func

funboost_aps_scheduler.add_push_job(consume_func, 'interval', id='3_second_job', seconds=3, kwargs={"x": 5, "y": 6})  # 每隔3秒发布一次任务，自然就能每隔3秒消费一次任务了。

funboost_aps_scheduler.start()
run_forever()