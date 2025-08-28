"""
这个是用来测试，以redis为中间件，随意关闭代码会不会造成任务丢失的。
"""
import os
import time

from funboost import boost,BrokerEnum,FunctionResultStatusPersistanceConfig
from funboost.utils.redis_manager import RedisMixin
import multiprocessing

@boost('test_cost_long_time_fun_queue888', broker_kind=BrokerEnum.REDIS_ACK_ABLE,
       )
def cost_long_time_fun(x):
   print(f'函数开始 hello {x}')
   time.sleep(120)
   print('函数完全结束')

if __name__ == '__main__':
    cost_long_time_fun.push(666)
    cost_long_time_fun.consume()
    # cost_long_time_fun.multi_process_consume(4)