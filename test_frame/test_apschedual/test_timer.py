# 定时运行消费演示
import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from function_scheduling_distributed_framework import task_deco, BrokerEnum


@task_deco('queue_test_666', broker_kind=BrokerEnum.LOCAL_PYTHON_QUEUE)
def consume_func(x, y):
    print(f'{x} + {y} = {x + y}')


# 写一个推送的函数
def pubilsh_task():
    consume_func.push(1, 2)


if __name__ == '__main__':
    sched = BackgroundScheduler(timezone='Asia/Shanghai')
    # sched.add_job(pubilsh_task, 'interval', id='3_second_job', seconds=3)  # 每隔3秒发布一次任务，自然就能每隔3秒消费一次任务了。
    # sched.add_job(pubilsh_task, 'date', run_date=datetime.datetime(2020, 7, 24, 11, 27, 6))  # 定时，只执行一次
    sched.add_job(pubilsh_task, 'cron', day_of_week='*', hour=11, minute='32', second='20')  # 定时，每天的11点32分20秒都执行一次。
    # 启动定时
    sched.start()

    # 启动消费
    consume_func.consume()
