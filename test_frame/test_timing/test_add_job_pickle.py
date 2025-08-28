
"""
此脚本是演示,由于2025-08 Booster 对象支持了 pickle序列化后,
可以支持
aps_obj_sum_two_numbers2.add_job(
        sum_two_numbers2.push,...)
这种写法.

这样用户可以了解定时任的本质是 push到消息队列,而不是直接执行函数自身.

用户看这个脚本主要是需要对比 add_push_job 和 add_job 的区别.
"""
from funboost import boost, BrokerEnum,ctrl_c_recv,BoosterParams,ApsJobAdder

# 定义任务处理函数
@boost(BoosterParams(queue_name='sum_queue552', broker_kind=BrokerEnum.REDIS))
def sum_two_numbers2(x, y):
    result = x + y
    print(f'The sum of {x} and {y} is {result}')

if __name__ == '__main__':
    # ApsJobAdder(sum_two_numbers2, job_store_kind='redis').add_push_job(
    #     trigger='interval',
    #     seconds=5,
    #     args=(4, 6),
    #     replace_existing=True,
    #     id='interval_job501',
    # )
    aps_job_adder_sum_two_numbers2 = ApsJobAdder(sum_two_numbers2, job_store_kind='redis',is_auto_paused=False)
    aps_obj_sum_two_numbers2 =aps_job_adder_sum_two_numbers2.aps_obj
    aps_obj_sum_two_numbers2.remove_all_jobs() # 可选,删除sum_two_numbers2所有已添加的定时任务

    # 原来推荐的添加定时任务方式 add_push_job
    aps_job_adder_sum_two_numbers2.add_push_job(
        # ApsJobAdder.add_push_job 不需要传递第一个入参func,job函数
        trigger='interval',
        seconds=5,
        args=(4, 6),
        replace_existing=True,
        id='interval_job503',
    )


    """
    2025-08后 现在可以直接使用用户熟悉的 add_job ,第一个入参func传递 $消费函数.push
    
    当使用redis 这种数据库而非memory作为 apscheduler 的 jobstore 时候,apscheduler.add_job 需要pickle序列化 第一个入参 func,
    sum_two_numbers2.push 是一个实例方法, Booster对象属性链路上有 threading.Lock 和socket 这些类型,
    导致不可pickle序列化,所以原来需要使用 ApsJobAdder.add_push_job 曲线救国.
    
    由于现在新增添加了 booster 支持pickle 序列化和反序列化,所以可以支持 sum_two_numbers2.push 实例方法 作为job函数.
    
    (ps:有兴趣的可以看 funboost/core/booster.py 的 Booster 的 __getstate__ 和 __setstate__ 的实现方式,是怎么支持pickle的,很巧妙)
    """
    aps_obj_sum_two_numbers2.add_job(
        func = sum_two_numbers2.push, # aps_obj.add_job 是 原生的,需要传递第一个入参func ,sum_two_numbers2.push
        trigger='interval',
        seconds=5,
        args=(40, 60),
        replace_existing=True,
        id='interval_job504',
    )


    ctrl_c_recv()