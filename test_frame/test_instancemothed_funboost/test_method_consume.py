import copy
from funboost import BoosterParams, boost
from funboost.utils.class_utils import FunctionKind, MethodType


def get_obj_init_params_for_funboost(obj_init_params: dict):
    obj_init_params.pop('self')
    return copy.deepcopy(obj_init_params)



class Myclass:
    m = 1

    def __init__(self, x):
        self.obj_init_params_for_funboost: dict = get_obj_init_params_for_funboost(copy.copy(locals()))
        self.x = x

    @boost(BoosterParams(queue_name='instance_method_queue',  is_show_message_get_from_broker=True, ))
    def instance_method(self, y):
        print(self.x + y)

    #
    @classmethod
    @BoosterParams(queue_name='class_method_queue',  is_show_message_get_from_broker=True, )
    def class_method(clsaaa, y):
        print(clsaaa.m + y)

    @staticmethod
    @BoosterParams(queue_name='static_method_queue', is_show_message_get_from_broker=True)
    def static_method(y):
        print(y)


@BoosterParams(queue_name='common_fun_queue', is_show_message_get_from_broker=True)
def common_f(y):
    print(y)


if __name__ == '__main__':

    for i in range(6, 10):
        Myclass.instance_method.push(Myclass(i), i * 2) # 注意发布形式，实例方法发布消息不能写成 Myclass(i).push(i * 2) , 要使用实例方法的本质入场方式，self就是对象本身。
    Myclass.instance_method.consume()

    for i in range(6, 10):
        Myclass.class_method.push( i * 2) #  # 框架自动处理了cls入参。
    Myclass.class_method.consume()

    for i in range(10):
        Myclass.static_method.push(i * 2)   # 不需要注意发布形式，和 普通函数的发布一样
    Myclass.static_method.consume()

    for i in range(10):
        common_f.push(i * 2)
    common_f.consume()
