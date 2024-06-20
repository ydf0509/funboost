import copy
from funboost import BoosterParams, boost
from funboost.constant import FunctionKind
from funboost.utils.class_utils import ClsHelper


class Myclass:
    m = 1

    def __init__(self, x):
        # 这行重要，如果实例方法作为消费函数，那么必须定义obj_init_params_for_funboost保存对象的 __init__ 入参，用于还原生成对象。
        self.obj_init_params: dict = ClsHelper.get_obj_init_params_for_funboost(copy.copy(locals()))
        # self.obj_init_params_for_funboost= {'x':x}  # 上面这行相当于这行，如果__init__入参太多，一个个的写到字典麻烦，可以使用上面的方式获取__init__入参字典。
        self.x = x

    @boost(BoosterParams(queue_name='instance_method_queue', is_show_message_get_from_broker=True, ))
    def instance_method(self, y):
        print(self.x + y)  # 这个求和用到了实例属性和方法入参求和，证明为什么发布消息时候要传递self。

    #
    @classmethod
    @BoosterParams(queue_name='class_method_queue', is_show_message_get_from_broker=True, )
    def class_method(cls, y):
        print(cls.m + y)

    @staticmethod
    @BoosterParams(queue_name='static_method_queue', is_show_message_get_from_broker=True)
    def static_method(y):
        print(y)


@BoosterParams(queue_name='common_fun_queue', is_show_message_get_from_broker=True)
def common_f(y):
    print(y)


if __name__ == '__main__':

    for i in range(6, 10):
        Myclass.instance_method.push(Myclass(i), i * 2)  # 注意发布形式，实例方法发布消息不能写成 Myclass(i).push(i * 2) 只发布self之后的入参, self也必须传递。
    Myclass.instance_method.consume()

    for i in range(6, 10):
        Myclass.class_method.push(Myclass,i * 2)  # 注意发布形式，不是 Myclass.class_method.push(i * 2) ， 而是应该写 Myclass.class_method.push(Myclass,i * 2)
    Myclass.class_method.consume()

    for i in range(10):
        Myclass.static_method.push(i * 2)  # 不需要注意发布形式，和 普通函数的发布一样
    Myclass.static_method.consume()

    for i in range(10):
        common_f.push(i * 2)
    common_f.consume()
