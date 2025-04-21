
"""
2025年后定时任务现在推荐使用 ApsJobAdder 写法 ，用户不需要亲自选择使用 apscheduler对象来添加定时任务。

使用对apscheduler封装的ApsJobAdder比 直接使用 apscheduler 包的好处如下：

1、ApsJobAdder.add_push_job 来添加定时发布到消息队列的任务，
  可以让用户少写一个 push_xx_fun_to_broker 的函数，用户不需要 apscheduler.add_job(push_xx_fun_to_broker,args=(1,)) ，
  而是 ApsJobAdder.add_push_job(xx_fun,args=(1,))

2.ApsJobAdder在redis作为job_store时候，每个消费函数使用单独的 jobs_key ，每个消费函数使用独立的 apscheduler对象，避免扫描定时任务互相干扰。
  例如你只想启动fun1的定时任务，而不像启动fun2的定时任务，更能单独控制。

3. ApsJobAdder在redis作为job_store时候 ，_process_jobs 使用了 redis分布式锁， 解决经典头疼的 apschduler建议只在一个进程启动一次，
现在可以在多机器多进程随意反复启动多次 apscheduler对象，不会造成定时任务执行重复。
"""

from funboost import boost, BrokerEnum,ctrl_c_recv,BoosterParams,ApsJobAdder



# 定义任务处理函数
@boost(BoosterParams(queue_name='sum_queue5', broker_kind=BrokerEnum.REDIS))
def sum_two_numbers(x, y):  
    result = x + y 
    print(f'The sum of {x} and {y} is {result}')  


@boost(BoosterParams(queue_name='data_queue5', broker_kind=BrokerEnum.REDIS))
def show_msg(data):
    print(f'data: {data}')

if __name__ == '__main__':
 
    # 启动消费者
    sum_two_numbers.consume()
    show_msg.consume()
    
    # 发布任务
    sum_two_numbers.push(3, 5)
    sum_two_numbers.push(10, 20)

    show_msg.push('hello world')
    
    # 使用ApsJobAdder添加定时任务， 里面的定时语法，和apscheduler是一样的，用户需要自己熟悉知名框架apscheduler的add_job定时入参

    # 方式1：指定日期执行一次
    # ApsJobAdder(sum_two_numbers, job_store_kind='redis').aps_obj.start(paused=False)
    ApsJobAdder(sum_two_numbers, job_store_kind='redis').add_push_job(
        trigger='date',
        run_date='2025-01-17 23:25:40',
        args=(7, 8),
        replace_existing=True, # 如果写个id，就不能重复添加相同id的定时任务了，要使用replace_existing来替换之前的定时任务id
        id='date_job1'
    )

    # 方式2：固定间隔执行,使用内存作为apscheduler的 job_store
    ApsJobAdder(sum_two_numbers, job_store_kind='redis').add_push_job(
        trigger='interval',
        seconds=5,
        args=(4, 6),
        replace_existing=True
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

    # 延时使用内存作为apscheduler的 job_store ，因为是内存，这种定时任务计划就不能持久化。
    ApsJobAdder(show_msg, job_store_kind='memory').add_push_job(
        trigger='interval',
        seconds=20,
        args=('hi python',)
    )

    ctrl_c_recv() # 这个是阻止代码主线程结束，这在background类型的apscheduler很重要，否则会报错提示主线程已退出。 当然，你也可以在末尾加 time.sleep 来阻止主线结束。