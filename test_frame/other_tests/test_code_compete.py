
import requests
from pydantic import BaseModel

from dataclasses import dataclass

@dataclass
class User:
    name: str       # 必须字段（无默认值）
    age: int = 18   # 可选字段（有默认值）

class MyModel(BaseModel):
    name: str
    age: int
    sex: str
    address: str
    phone: str
    email: str

class CommonKls:
    def __init__(self,name,sex,age):
        pass

if __name__ == '__main__':
    m = MyModel(name='张三', age=18, sex='男', 
                address='北京市朝阳区', phone='13800138000',email='123456@qq.com')
    print(m)

    
   
    CommonKls(name='张三', sex='男', age=18)
