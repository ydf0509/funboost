

from pydantic import BaseModel, BaseConfig

class NoExtraFieldsConfig(BaseConfig):
    # allow_mutation = False
    extra = "forbid"

class MyModel(BaseModel):


    name: str
    age: int

    # __config__ = NoExtraFieldsConfig

    class Config:
        extra = "forbid"

# 创建一个实例
obj = MyModel(name="John", age=30)

# 子类试图增加额外字段
class SubModel(MyModel):
    extra_field: bool

# 试图创建子类实例
sub_obj = SubModel(name="Jane", age=25, extra_field=True)  # 引发错误：pydantic.error_wrappers.ValidationError