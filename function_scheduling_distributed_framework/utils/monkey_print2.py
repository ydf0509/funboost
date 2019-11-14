# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2019/5/9 19:02
"""
对内置print函数打猴子补丁。使项目中任意print自动变化成可点击跳转形式。
如果项目太大，有人疯狂print无前缀提示的变量，由于不能使用全局字母前缀搜索，很难找出print是从哪里冒出来的，打这个猴子补丁后，能够轻松找出来是哪里print的。

"""
import sys
import time


# noinspection PyProtectedMember,PyUnusedLocal,PyIncorrectDocstring
def nb_print(*args, sep=' ', end='\n', file=None):
    """
    超流弊的print补丁
    :param x:
    :return:
    """
    # 获取被调用函数在被调用时所处代码行数
    line = sys._getframe().f_back.f_lineno
    # 获取被调用函数所在模块文件名
    file_name = sys._getframe(1).f_code.co_filename
    # sys.stdout.write(f'"{__file__}:{sys._getframe().f_lineno}"    {x}\n')
    args = (str(arg) for arg in args)  # REMIND 防止是数字不能被join
    sys.stdout.write(f'"{file_name}:{line}"  {time.strftime("%H:%M:%S")}  \033[0;94m{"".join(args)}\033[0m\n')  # 36  93 96 94


# print = nb_print


def patch_print(only_effect_on_current_module=False):
    """
    Python有几个namespace，分别是

    locals

    globals

    builtin

    其中定义在函数内声明的变量属于locals，而模块内定义的函数属于globals。

    :param only_effect_on_current_module:
    :return:
    """
    if only_effect_on_current_module:
        # noinspection PyShadowingNames,PyUnusedLocal,PyShadowingBuiltins
        print = nb_print  # REMIND 这样做只能对当前模块生效，要使项目所有文件的任意print自动变化，需要 __builtins__.print = nb_print
    else:
        __builtins__.print = nb_print


if __name__ == '__main__':
    print('before patch')
    patch_print()
    print(0)
    print(123, 'abc')
    print(456, 'def')
