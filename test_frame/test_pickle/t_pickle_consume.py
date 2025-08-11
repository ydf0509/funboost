

import ast
import typing

import os
import sys
import time
import datetime
import pickle

os.environ['path'] = os.path.dirname(sys.executable) + os.pathsep + os.environ['PATH']

from funboost import (boost, BoosterParams, BrokerEnum, ctrl_c_recv,
                      ConcurrentModeEnum, AsyncResult,FunctionResultStatus,
                      BoostersManager, AioAsyncResult, fct
                      )



@boost(BoosterParams(queue_name='queue_pickle',concurrent_num=10,is_using_rpc_mode=True,
                     broker_kind=BrokerEnum.REDIS_ACK_ABLE))
def func1(a,b):
    print(fct.full_msg)
    print(pickle.loads(ast.literal_eval(a)),b)


class MyClass:
    def __init__(self,x,y):
        self.x = x
        self.y = y
    def __str__(self):
        return f'MyClass(x={self.x},y={self.y})'

if __name__ == '__main__':

    func1.push(str(pickle.dumps(MyClass(1,2))),datetime.datetime.now())
    func1.consume()
    ctrl_c_recv()






