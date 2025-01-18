
"""
2025年后定时任务现在推荐使用 ApsJobAdder 写法 ，用户不需要亲自选择使用 apscheduler对象来添加定时任务
"""

from funboost import boost, BrokerEnum,ctrl_c_recv,BoosterParams,ApsJobAdder



# 定义任务处理函数
@BoosterParams(queue_name='sum_queue3', broker_kind=BrokerEnum.REDIS)
def sum_two_numbers(x, y):  
    result = x + y 
    print(f'The sum of {x} and {y} is {result}')  


if __name__ == '__main__':
 
    # 启动消费者
    sum_two_numbers.consume()
    
    # 发布任务
    sum_two_numbers.push(3, 5)
    sum_two_numbers.push(10, 20)
    
    # 使用ApsJobAdder添加定时任务， 里面的定时语法，和apscheduler是一样的，用户需要自己熟悉知名框架apscheduler的add_job定时入参

    # 方式1：指定日期执行一次
    ApsJobAdder(sum_two_numbers, job_store_kind='redis').add_push_job(
        trigger='date',
        run_date='2025-01-17 23:25:40', 
        args=(7, 8)
    )

    # 方式2：固定间隔执行
    ApsJobAdder(sum_two_numbers, job_store_kind='memory').add_push_job(
        trigger='interval', 
        seconds=5, 
        args=(4, 6)
    )

    # 方式3：使用cron表达式定时执行
    ApsJobAdder(sum_two_numbers, job_store_kind='redis').add_push_job(
        trigger='cron',
        day_of_week='*', 
        hour=23, 
        minute=49, 
        second=50,
        kwargs={"x":50,"y":60},
        replace_existing=True,
        id='cron_job1')
        
    ctrl_c_recv()