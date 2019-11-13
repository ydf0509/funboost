# Copyright 2019 Ram Rachum and collaborators.
# This program is distributed under the MIT license.

import abc
import time
import sys
from .pycompat import ABC, string_types, collections_abc

def _check_methods(C, *methods):
    mro = C.__mro__
    for method in methods:
        for B in mro:
            if method in B.__dict__:
                if B.__dict__[method] is None:
                    return NotImplemented
                break
        else:
            return NotImplemented
    return True


class WritableStream(ABC):
    @abc.abstractmethod
    def write(self, s):
        pass

    @classmethod
    def __subclasshook__(cls, C):
        if cls is WritableStream:
            return _check_methods(C, 'write')
        return NotImplemented



file_reading_errors = (
    IOError,
    OSError,
    ValueError # IronPython weirdness.
)



def shitcode(s):
    return ''.join(
        (c if (0 < ord(c) < 256) else '?') for c in s
    )


def get_repr_function(item, custom_repr):
    for condition, action in custom_repr:
        if isinstance(condition, type):
            condition = lambda x, y=condition: isinstance(x, y)
        if condition(item):
            return action
    return repr


def get_shortish_repr(item, custom_repr=(), max_length=None):
    repr_function = get_repr_function(item, custom_repr)
    try:
        r = repr_function(item)
    except Exception:
        r = 'REPR FAILED'
    r = r.replace('\r', '').replace('\n', '')
    if max_length:
        r = truncate(r, max_length)
    return r


def truncate(string, max_length):
    if (max_length is None) or (len(string) <= max_length):
        return string
    else:
        left = (max_length - 3) // 2
        right = max_length - 3 - left
        return u'{}...{}'.format(string[:left], string[-right:])


def ensure_tuple(x):
    if isinstance(x, collections_abc.Iterable) and \
                                               not isinstance(x, string_types):
        return tuple(x)
    else:
        return (x,)


def nb_print( *args, sep=' ', end='\n', file=None):
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

