import copy
from funboost import BoosterParams, boost
from funboost.constant import FunctionKind
from funboost.utils.class_utils import ClsHelper
from test_frame.test_instancemothed_funboost.test_method_consume import Myclass, common_f

if __name__ == '__main__':

    # for i in range(6, 10):
    #     Myclass.instance_method.push(Myclass(i), i * 2)  # 注意发布形式，实例方法发布消息不能写成 Myclass(i).push(i * 2) 只发布self之后的入参, self也必须传递。
    # Myclass.instance_method.consume()

    for i in range(6, 10):
        Myclass.class_method.push(Myclass, i * 2)  # # 框架自动处理了cls入参，不麻烦用户亲自传递cls入参。
    Myclass.class_method.consume()

    # for i in range(10):
    #     Myclass.static_method.push(i * 2)  # 不需要注意发布形式，和 普通函数的发布一样
    # Myclass.static_method.consume()
    #
    # for i in range(10):
    #     common_f.push(i * 2)
    # common_f.consume()
