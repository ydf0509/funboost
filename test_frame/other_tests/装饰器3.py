
import functools
import abc
import sys
import typing


class Undefind:
    pass

F = typing.TypeVar('F')
class BaseDecorator(metaclass=abc.ABCMeta):
    """
    简化了装饰器的编写。

    用户的装饰器需要继承这个，用户可以按需重新定义 before，after，when_exception 方法。

    为了一致性和省事，统一采用有参数装饰器，用户的装饰器后面必须带括号。

    用户可以选择重写 before  after  when_exception 三个方法
    """

    # def __init__(self, *args, **kwargs):
    #     pass

    raw_fun = Undefind()
    raw_result = Undefind()
    exc_info = Undefind()
    final_result = Undefind()  # 用户可以自己定义final_result的值，如果定义了就把这个值作为函数的结果，否则把函数原始结果作为结果。

    def __call__(self, fun:F, *args, **kwargs)->F:
        # print(locals())
        if not callable(fun) or args or kwargs:  # 正常是只有fun一个参数，除非是装饰器没加括号造成的。
            raise ValueError('为了简单和一致起见，所有装饰器都采用有参数装饰器，被装饰函数上面的装饰器后面别忘了加括号')
        self.raw_fun = fun
        f = functools.partial(BaseDecorator._execute, self)  # 比 self.execute 利于补全
        functools.update_wrapper(f, fun, )
        functools.wraps(fun)(f)
        return f

    def _execute(self, *args, **kwargs):
        self.before()
        try:
            self.raw_result = self.raw_fun(*args, **kwargs)
            self.after()
        except Exception as e:
            self.exc_info = sys.exc_info()
            self.when_exception()
        if not isinstance(self.final_result, Undefind):  # 用户可以自己定义final_result的值，如果定义了就把这个值作为函数的结果。
            return self.final_result
        else:
            return self.raw_result

    def before(self):
        pass

    def after(self):
        pass

    def when_exception(self):
        # print(self.exc_info) # (<class 'ZeroDivisionError'>, ZeroDivisionError('division by zero',), <traceback object at 0x000001D22BA3FD48>)
        raise self.exc_info[1]


if __name__ == '__main__':
    import nb_log  # noqa


    class MyDeco(BaseDecorator):
        def __init__(self, a=5, b=6):
            self.a = a
            self.b = b

        def before(self):
            print('开始执行')

        # noinspection PyAttributeOutsideInit
        def after(self):
            self.final_result = self.a * self.b * self.raw_result


    def common_deco(a=5, b=6):
        """  上面的逻辑如果用常规方式写"""

        def _inner(f):
            @functools.wraps(f)
            def __inner(*args, **kwargs):
                try:
                    print('开始执行')
                    result = f(*args, **kwargs)
                    return a * b * result
                except Exception as e:
                    raise e

            return __inner

        return _inner


    @MyDeco(b=4)
    # @common_deco(b=4)  # 这两个装饰器等效，二选一。
    def fun3(x):
        print(x)
        return x * 2


    print(type(fun3))
    print(fun3)
    print(fun3.__wrapped__)  # noqa
    print(fun3(10))
