from test_frame.test_delay_task.test_delay_consume import f
import datetime
import time
from function_scheduling_distributed_framework import PriorityConsumingControlConfig


for i in range(10):
    time.sleep(2)
    f.publish({'x':i},priority_control_config=PriorityConsumingControlConfig(countdown=5))  # 取出来后5秒后在执行。
    f.publish({'x':i*10},priority_control_config=PriorityConsumingControlConfig(eta=datetime.datetime(2021, 5, 19, 14, 21, 30) + datetime.timedelta(seconds=i))) # 按指定的时间运行一次。
