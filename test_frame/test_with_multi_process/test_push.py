from function_scheduling_distributed_framework import PriorityConsumingControlConfig
from test_frame.test_with_multi_process.test_consume import ff

for i in range(1000, 10000):
    ff.push(i, y=i * 2)

    # 这个与push相比是复杂的发布，第一个参数是函数本身的入参字典，后面的参数为任务控制参数，例如可以设置task_id，设置延时任务，设置是否使用rpc模式等。
    ff.publish({'x': i * 10, 'y': i * 2}, priority_control_config=PriorityConsumingControlConfig(countdown=10, misfire_grace_time=30))
    ff.publish()