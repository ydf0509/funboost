# tasks.py
import time
from funboost import boost, BrokerEnum, BoosterParams

# 为了让 Web 端和后台 Worker 端都能连接到同一个消息队列，
# 我们使用 Redis 作为中间件。
# 确保你的 funboost_config.py 中已经配置好了 Redis。
@boost(BoosterParams(
    queue_name='web_dynamic_task_queue2',
    broker_kind=BrokerEnum.REDIS_ACK_ABLE
))
def dynamic_task(task_id: str, message: str):
    """
    这个函数将被 Web 应用动态地、定时地调度。
    """
    current_time = time.strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{current_time}] [后台Worker] 正在执行任务...\n"
          f"  - 任务ID: {task_id}\n"
          f"  - 消息内容: '{message}'")
    # 可以在这里执行发送邮件、生成报表等实际操作

