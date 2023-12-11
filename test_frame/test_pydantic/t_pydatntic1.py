import typing
from pydantic import BaseModel


def f():
    pass

class M1(BaseModel):
    fun = f
    a=1
    _b = 2

    class Config:
        json_encoders = {
            typing.Callable: lambda v: str(v)  # 自定义 函数 类型的序列化逻辑
        }
        underscore_attrs_are_private = True


print(M1()._b)
m1 = M1()
m1._b  =7
print((M1(_b=6).json()))