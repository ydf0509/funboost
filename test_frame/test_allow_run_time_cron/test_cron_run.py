
import time
import datetime
from funboost import boost, BoosterParams, BrokerEnum,ctrl_c_recv

# 场景1：只在工作日上班时间运行 (测试通过前提：当前必须是工作日9-18点，否则这也会被暂停)
# * 9-18 * * 1-5 表示周一到周五的 9:00-18:59 允许运行
# qps=1 控制一下速度，方便观察
@boost(BoosterParams(
    queue_name='test_cron_allow_queue', 
    # allow_run_time_cron='* 9-18 * * 1-5',
    allow_run_time_cron='* 9-19 * * 1-5',
    qps=1,
    broker_kind=BrokerEnum.MEMORY_QUEUE
))
def task_allow(x):
    print(f'✅ [允许运行的任务] 正常执行中... 参数: {x}, 当前时间: {datetime.datetime.now()}')

# 场景2：当前时间不允许运行
# 0 0 1 1 * 表示每年1月1日0点0分运行。除非现在刚好是那个时刻，否则不运行。
@boost(BoosterParams(
    queue_name='test_cron_deny_queue', 
    allow_run_time_cron='0 0 1 1 *',
    qps=1,
    broker_kind=BrokerEnum.MEMORY_QUEUE
))
def task_deny(x):
    print(f'❌ [禁止运行的任务] 竟然执行了！BUG！参数: {x}')

if __name__ == '__main__':
    # 1. 先发布一些任务
    for i in range(2):
        task_allow.push(i)
        task_deny.push(i)
        
    print(f"任务已发布。当前时间: {datetime.datetime.now()}")
    print("-" * 50)
    print("预期结果：")
    print("1. task_allow 应该正常打印日志")
    print("2. task_deny 不应该执行任何函数逻辑，控制台应该没有任何 task_deny 的print输出，")
    print("   但你应该会看到 funboost 的 warning 日志提示 '不在 allow_run_time_cron ... 暂停运行'")
    print("-" * 50)

    # 2. 启动消费
    task_allow.consume()
    task_deny.consume()
    ctrl_c_recv()

 
