from test_frame.test_delay_task.test_delay_consume import f
import datetime
from function_scheduling_distributed_framework import PriorityConsumingControlConfig

f.publish({'x':1},priority_control_config=PriorityConsumingControlConfig(countdown=5))  # 取出来后5秒后在执行。
f.publish({'x':10},priority_control_config=PriorityConsumingControlConfig(eta=datetime.datetime(2021, 5, 19, 11, 59, 30))) # 按指定的时间运行一次。