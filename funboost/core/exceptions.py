

class FunboostException(Exception):
    """funboost 异常基类"""


class ExceptionForRetry(FunboostException):
    """为了重试的，抛出错误。只是定义了一个子类，用不用都可以，函数出任何类型错误了框架都会自动重试"""


class ExceptionForRequeue(FunboostException):
    """框架检测到此错误，重新放回当前队列中"""


class ExceptionForPushToDlxqueue(FunboostException):
    """框架检测到ExceptionForPushToDlxqueue错误，发布到死信队列"""


class BoostDecoParamsIsOldVersion(FunboostException):
    new_version_change_hint = """
你的@boost入参是老的方式,建议用新的入参方式,老入参方式不再支持函数入参代码自动补全了。

老版本的@boost装饰器方式是:
@boost('queue_name_xx',qps=3)
def f(x):
    pass
    

用户需要做的改变如下:
@boost(BoosterParams(queue_name='queue_name_xx',qps=3))
def f(x):
    pass

就是把原来函数入参的加个 BoosterParams 就可以了.

@boost这个最重要的funboost核心方法作出改变的原因是:
1/由于开发框架时候,Booster和Consumer多处需要重复声明入参,
2/入参个数较多,需要locals转化,麻烦
    """

    def __str__(self):
        return self.new_version_change_hint
