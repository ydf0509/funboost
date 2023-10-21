"""
这个是用来测试，以redis为中间件，随意关闭代码会不会造成任务丢失的。
"""
import os
import time

from funboost import boost,BrokerEnum,FunctionResultStatusPersistanceConfig
from funboost.utils.redis_manager import RedisMixin
import multiprocessing

@boost('test_cost_long_time_fun_queue2d5', broker_kind=BrokerEnum.REDIS_PRIORITY, concurrent_num=5,log_level=20,
       # function_result_status_persistance_conf=FunctionResultStatusPersistanceConfig(True,True)
       )
def cost_long_time_fun(x):
    pass
    # print(f'正在消费 {x} 中 。。。。')
    # time.sleep(30)
    # print(f'消费完成 {x} ')

    if x%1000 == 0:
        print(multiprocessing.current_process().pid,x)

    RedisMixin().redis_db_frame.lpush('test_count5',x)

if __name__ == '__main__':
    # for i in range(100):
    #     cost_long_time_fun.push(i)
    cost_long_time_fun.multi_process_consume(4)