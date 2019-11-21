# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2019/5/9 19:02
"""
不直接给print打补丁，自己重新赋值。

"""
import logging
import sys
import time
import traceback


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


# noinspection PyPep8,PyUnusedLocal
def print_exception(etype, value, tb, limit=None, file=None, chain=True):
    """
    避免每行有两个可跳转的，导致第二个可跳转的不被ide识别。
    主要是针对print_exception，logging.exception里面会调用这个函数。

    :param etype:
    :param value:
    :param tb:
    :param limit:
    :param file:
    :param chain:
    :return:
    """
    if file is None:
        file = sys.stderr
    for line in traceback.TracebackException(
            type(value), value, tb, limit=limit).format(chain=chain):
        # print(line, file=file, end="")
        if file != sys.stderr:
            sys.stderr.write(f'{line} \n')
        else:
            print(line, file=file, end="")


# print = nb_print

def patch_print():
    """
    Python有几个namespace，分别是

    locals

    globals

    builtin

    其中定义在函数内声明的变量属于locals，而模块内定义的函数属于globals。

    :return:
    """
    try:
        __builtins__.print = nb_print
    except AttributeError:
        """
        <class 'AttributeError'>
        'dict' object has no attribute 'print'
        """
        # noinspection PyUnresolvedReferences
        __builtins__['print'] = nb_print
    traceback.print_exception = print_exception


if __name__ == '__main__':
    print('before patch')
    patch_print()
    print(0)
    nb_print(123, 'abc')
    print = nb_print
    print(456, 'def')
