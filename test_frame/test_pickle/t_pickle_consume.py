
import os
import sys
os.environ['path'] = os.path.dirname(sys.executable) + os.pathsep + os.environ['PATH']

"""
此demo演示funboost新增支持了pickle序列化,
当用户的消费函数入参不是基本类型,而是自定义类型时候,funboost能自动识别,并将相关字段使用pickle序列化成字符串.
当消费函数运行时,funboost能自动将pickle字符串反序列化成对象,并赋值给消费函数入参.
"""

from pydantic import BaseModel
from funboost import (boost, BoosterParams, BrokerEnum, ctrl_c_recv, fct)


class MyClass:
    def __init__(self,x,y):
        self.x = x
        self.y = y

    def change(self,n):
        self.x +=n
        self.y +=n
    def __str__(self):
        return f'<MyClass(x={self.x},y={self.y})>'

class MyPydanticModel(BaseModel):
    str1:str
    num1:int


@boost(BoosterParams(queue_name='queue_json_test',concurrent_num=10,is_using_rpc_mode=True,
                     broker_kind=BrokerEnum.REDIS_ACK_ABLE))
def func0(m:str,n:int,q:dict,r:list): # 以前只支持这样的入参,入参必须是简单基本类型
    print(f'm:{m},n:{n}')
    print(f'q:{q},r:{r}')
   


@boost(BoosterParams(queue_name='queue_pickle_test',concurrent_num=10,is_using_rpc_mode=True,
                     broker_kind=BrokerEnum.REDIS_ACK_ABLE))
def func1(a:MyClass,b:str,c:MyPydanticModel): # 现在支持这样的自定义类型对象的入参
    # print(fct.full_msg) # 可以查看原始消息
    print(f'a:{a}')
    print(f'b:{b}')
    print(f'c:{c}')
    print(f'a.x:{a.x},a.y:{a.y}')


if __name__ == '__main__':
    func0.consume()
    func1.consume()

    obj1 = MyClass(1,2)
    func1.push(obj1,'hello',MyPydanticModel(str1='hello',num1=1)) # 现在支持发布不可json序列化的对象

    obj1.change(10)
    func1.push(obj1,'hello',MyPydanticModel(str1='world',num1=100))

    func0.push('hello',100,{'a':1,'b':2},[1,2,3]) # 以前只允许发布这样基本类型入参的消息
   
    ctrl_c_recv()






