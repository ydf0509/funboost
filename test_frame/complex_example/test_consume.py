
"""
一个展示更全面 funboost 用法的例子
包含了
1.继承BoosterParams，为了每个装饰器少写入参
2.rpc获取结果
3.连续丝滑启动多个消费函数
4.定时任务
"""
from funboost import boost, BrokerEnum,BoosterParams,ctrl_c_recv,ConcurrentModeEnum,ApsJobAdder
import time

class MyBoosterParams(BoosterParams):  # 自定义的参数类，继承BoosterParams，用于减少每个消费函数装饰器的重复相同入参个数
    broker_kind: str = BrokerEnum.REDIS_ACK_ABLE
    max_retry_times: int = 3
    concurrent_mode: str = ConcurrentModeEnum.THREADING 

    
@boost(MyBoosterParams(queue_name='s1_queue', qps=1, 
                    #    do_task_filtering=True, # 可开启任务过滤，防止重复入参消费。
                       is_using_rpc_mode=True, # 开启rpc模式，支持rpc获取结果
                       ))
def step1(a:int,b:int):
    print(f'a={a},b={b}')
    time.sleep(0.7)
    for j in range(10):
        step2.push(c=a+b +j,d=a*b +j,e=a-b +j ) # step1消费函数里面，也可以继续向其他任意队列发布消息。
    return a+b


@boost(MyBoosterParams(queue_name='s2_queue', qps=3, ))
def step2(c:int,d:int,e:int=666):
    time.sleep(3)
    print(f'c={c},d={d},e={e}')
    return c* d * e


if __name__ == '__main__':
    step1.clear() # 清空队列
    step2.clear() # 清空队列

    step1.consume() # 调用.consume是非阻塞的启动消费，是在单独的子线程中循环拉取消息的。 
    # 有的人还担心阻塞而手动使用 threading.Thread(target=step1.consume).start() 来启动消费，这是完全多此一举的错误写法。
    step2.consume() # 所以可以在当前主线程连续无阻塞丝滑的启动多个函数消费。
    step2.multi_process_consume(3) # 这是多进程叠加了多线程消费，开启了3个进程，叠加了默认的线程并发。

    async_result = step1.push(100,b=200)
    print('step1的rpc结果是：',async_result.result)  # rpc阻塞等待消step1的费结果返回

    for i in range(100):
        step1.push(i,i*2) # 向 step1函数的队列发送消息,入参和手动调用函数那样很相似。
        step1.publish ({'a':i,'b':i*2},task_id=f'task_{i}') # publish 第一个入参是字典，比push能传递更多funboost的辅助参数，类似celery的apply_async和delay的关系。一个简单，一个复杂但强大。
    
    

    """
    1.funboost 使用 ApsJobAdder.add_push_job来添加定时任务，不是add_job。
    2.funboost是轻度封装的知名apscheduler框架，所以定时任务的语法和apscheduler是一样的，没有自己发明语法和入参
    用户需要苦学apscheduler教程，一切定时都是要学apscheduler知识，定时和funboost知识关系很小。
    3.funboost的定时任务目的是定时推送消息到消息队列中，而不是定时直接在当前程序中执行某个消费函数。

    下面是三种方式添加定时任务，这些定时方式都是知名apscheduler包的定时方式，和funboost没关系。
    """
    # 方式1：指定日期执行一次
    ApsJobAdder(step2, 
               job_store_kind='redis', # 使用reids作为 apscheduler的 jobstrores
               is_auto_start=True,   # 添加任务，并同时启动定时器 执行了apscheduler对象.start()
    ).add_push_job(
        trigger='date',
        run_date='2025-06-30 16:25:40',
        args=(7, 8,9),
        id='date_job1',
        replace_existing=True,
    )

    # 方式2：固定间隔执行
    ApsJobAdder(step2, job_store_kind='redis').add_push_job(
        trigger='interval',
        seconds=30,
        args=(4, 6,10),
        id='interval_job1',
        replace_existing=True,
    )

    # 方式3：使用cron表达式定时执行
    ApsJobAdder(step2, job_store_kind='redis').add_push_job(
        trigger='cron',
        day_of_week='*',
        hour=23,
        minute=49,
        second=50,
        kwargs={"c": 50, "d": 60,"e":70},
        replace_existing=True,
        id='cron_job1')
    
    ctrl_c_recv()  # 用于阻塞代码，阻止主线程退出，使主线程永久运行。  相当于 你在代码最末尾，加了个 while 1:time.sleep(10)，使主线程永不结束。apscheduler background定时器守护线程需要这样保持定时器不退出。