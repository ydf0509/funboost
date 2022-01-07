import copy
class DataClassBase:
    """
    使用类实现的 简单数据类。
    也可以使用装饰器来实现数据类
    """
    def __new__(cls, **kwargs):
        self = super().__new__(cls)
        self.__dict__ = copy.copy({k: v for k, v in cls.__dict__.items() if not k.startswith('__')})
        return self

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    def __call__(self, ) -> dict:
        return self.get_dict()

    def get_dict(self):
        return {k: v.get_dict() if isinstance(v, DataClassBase) else v for k, v in self.__dict__.items()}

    def __str__(self):
        return f"{self.__class__}    {self.get_dict()}"

    def __getitem__(self, item):
        return getattr(self,item)


if __name__ == '__main__':
    class A(DataClassBase):
        x =1
        y = 2

    print(A())
    print(A(y=3))
    print(A(y=5).get_dict())

    print(A()['y'])
    print(A().y)