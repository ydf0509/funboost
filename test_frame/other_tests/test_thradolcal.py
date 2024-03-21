import functools
import threading

tl = threading.local()


# def f1(b):
#     tl.x=b
#     tl.y = b+2
#     # f2()
#     print(tl.__dict__)
#     t2 = threading.Thread(target=f2,args=(tl.__dict__,))
#     t2.start()
#
# def f2(tl_dict):
#     tl2 = threading.local()
#     tl2.__dict__.update(tl_dict)
#     print(tl2.x)
#
#
#
# threading.Thread(target=f1,args=(3,)).start()
# threading.Thread(target=f1,args=(4,)).start()
import nb_log

# @functools.lru_cache()
class ClassProperty:
    def __init__(self, fget):
        self.fget = fget

    def __get__(self, instance, owner):
        return self.fget(owner)

class MyClass:
    _my_class_property = "Hello, World!"

    @ClassProperty
    def my_class_property(cls):
        return cls._my_class_property

# 直接通过类名访问类属性的值
value = MyClass.my_class_property
print(value)  # 输出: Hello, World!