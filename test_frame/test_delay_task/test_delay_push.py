from test_frame.test_delay_task.test_delay_consume import f
import datetime
import time
from function_scheduling_distributed_framework import PriorityConsumingControlConfig

"""
测试发布延时任务，不是发布后马上就执行函数。
"""
for i in range(1, 200):
    time.sleep(1)

    # 消息发布10秒后再执行。如果消费慢导致任务积压，即使轮到消息消费时候离发布超过10秒了仍然执行。
    f.publish({'x': i}, priority_control_config=PriorityConsumingControlConfig(countdown=10))

    # 规定消息在17点56分30秒运行，如果消费慢导致任务积压，即使轮到消息消费时候已经过了17点56分30秒仍然执行。
    f.publish({'x': i * 10}, priority_control_config=PriorityConsumingControlConfig(
        eta=datetime.datetime(2021, 5, 19, 17, 56, 30) + datetime.timedelta(seconds=i)))

    # 消息发布10秒后再执行。如果消费慢导致任务积压，如果轮到消息消费时候离发布超过10秒了则放弃执行。
    f.publish({'x': i * 100}, priority_control_config=PriorityConsumingControlConfig(
        countdown=10, execute_delay_task_even_if_when_task_is_expired=False))

    # 规定消息在17点56分30秒运行，如果消费慢导致任务积压，如果轮到消息消费时候已经过了17点56分30秒，则放弃执行。
    f.publish({'x': i * 1000}, priority_control_config=PriorityConsumingControlConfig(
        eta=datetime.datetime(2021, 5, 19, 17, 56, 30) + datetime.timedelta(seconds=i),
        execute_delay_task_even_if_when_task_is_expired=False))  # 按指定的时间运行一次。
