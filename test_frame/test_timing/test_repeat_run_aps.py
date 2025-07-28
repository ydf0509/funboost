

"""
此脚本演示，funboost的 redis jobstore的apscheudler 不害怕你反复部署，因为使用用redis分布式锁，防止扫描取出同样的定时任务。
"""

from funboost import boost, BrokerEnum,ctrl_c_recv,BoosterParams,ApsJobAdder



# 定义任务处理函数
@boost(BoosterParams(queue_name='sum_queue550', broker_kind=BrokerEnum.REDIS))
def sum_two_numbers(x, y):  
    result = x + y 
    print(f'The sum of {x} and {y} is {result}')  

if __name__ == '__main__':
    ApsJobAdder(sum_two_numbers, job_store_kind='redis').add_push_job(
        trigger='interval',
        seconds=5,
        args=(4, 6),
        replace_existing=True,
        id='interval_job501',
    )
    ctrl_c_recv()
