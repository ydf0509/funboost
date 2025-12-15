
import inspect

def func(a,b,c=3,d=4,e=5):
    pass

sig = inspect.signature(func)
bound = sig.bind(*(1,2), **{'d':8,'c':7})
bound.apply_defaults()

print(bound.arguments)




class MyClass:
    def __init__(self,x):
        self.x = x

    def func(self, a, b, c=3, d=4, e=5):
        pass

obj = MyClass(1)

sig = inspect.signature(MyClass.func)
bound = sig.bind(*(obj,1,2), **{'d':8,'c':7})
bound.apply_defaults()

print(bound.arguments)
