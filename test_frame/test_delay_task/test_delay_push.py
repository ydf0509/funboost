# 需要用publish，而不是push，这个前面已经说明了，如果要传函数入参本身以外的参数到中间件，需要用publish。
# 不然框架分不清哪些是函数入参，哪些是控制参数。如果无法理解就，就好好想想琢磨下celery的 apply_async 和 delay的关系。
from test_frame.test_delay_task.test_delay_consume import f
import datetime
import time
from funboost import PriorityConsumingControlConfig

"""
测试发布延时任务，不是发布后马上就执行函数。

countdown 和 eta 只能设置一个。
countdown 指的是 离发布多少秒后执行，
eta是指定的精确时间运行一次。

misfire_grace_time 是指定消息轮到被消费时候，如果已经超过了应该运行的时间多少秒之内，仍然执行。
misfire_grace_time 如果设置为None，则消息一定会被运行，不会由于大连消息积压导致消费时候已近太晚了而取消运行。
misfire_grace_time 如果不为None，必须是大于等于1的整数，此值表示消息轮到消费时候超过本应该运行的时间的多少秒内仍然执行。
此值的数字设置越小，如果由于消费慢的原因，就有越大概率导致消息被丢弃不运行。如果此值设置为1亿，则几乎不会导致放弃运行(1亿的作用接近于None了)
如果还是不懂这个值的作用，可以百度 apscheduler 包的 misfire_grace_time 概念

"""
# for i in range(1, 20):
#     time.sleep(1)
#
#     # 消息发布10秒后再执行。如果消费慢导致任务积压，misfire_grace_time为None，即使轮到消息消费时候离发布超过10秒了仍然执行。
#     f.publish({'x': i}, priority_control_config=PriorityConsumingControlConfig(countdown=10))
#
#     # 规定消息在17点56分30秒运行，如果消费慢导致任务积压，misfire_grace_time为None，即使轮到消息消费时候已经过了17点56分30秒仍然执行。
#     f.publish({'x': i * 10}, priority_control_config=PriorityConsumingControlConfig(
#         eta=datetime.datetime(2023, 5, 14, 17, 56, 30) + datetime.timedelta(seconds=i)))
#
#     # 消息发布10秒后再执行。如果消费慢导致任务积压，misfire_grace_time为30，如果轮到消息消费时候离发布超过40 (10+30) 秒了则放弃执行，
#     # 如果轮到消息消费时候离发布时间是20秒，由于 20 < (10 + 30)，则仍然执行
#     f.publish({'x': i * 100}, priority_control_config=PriorityConsumingControlConfig(
#         countdown=10, misfire_grace_time=30))
#
#     # 规定消息在17点56分30秒运行，如果消费慢导致任务积压，如果轮到消息消费时候已经过了17点57分00秒，
#     # misfire_grace_time为30，如果轮到消息消费时候超过了17点57分0秒 则放弃执行，
#     # 如果如果轮到消息消费时候是17点56分50秒则执行。
#     f.publish({'x': i * 1000}, priority_control_config=PriorityConsumingControlConfig(
#         eta=datetime.datetime(2023, 5, 14, 17, 56, 30) + datetime.timedelta(seconds=i),
#         misfire_grace_time=30))  # 按指定的时间运行一次。
#
#     # 这个设置了消息由于消息堆积导致运行的时候比本应该运行的时间如果小于1亿秒，就仍然会被执行，所以几乎肯定不会被放弃运行
#     f.publish({'x': i * 10000}, priority_control_config=PriorityConsumingControlConfig(
#         eta=datetime.datetime(2022, 5, 19, 17, 56, 30) + datetime.timedelta(seconds=i),
#         misfire_grace_time=100000000))   # 按指定的时间运行一次。

f.publish({'x':  10}, priority_control_config=PriorityConsumingControlConfig(
    eta=datetime.datetime.now() + datetime.timedelta(seconds=20)))

f.push(666)
time.sleep(100000)