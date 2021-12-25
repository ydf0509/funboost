# -*- coding: utf-8 -*-
# @Author  : ydf
"""
基于0.0.11版本，对其打猴子补丁改进的。现在推荐使用pysnooper_ydf里面的，不需要用这里。
DeBug Python代码全靠print函数？换用这个一天2K+Star的工具吧
对最火热的github库，进行了三点改造。
1、由于部署一般是linux，开发是windows，所以可以自动使其在linux上失效，调试会消耗性能。
2、将代码运行轨迹修改成可以点击的，点击对应行号可以跳转到代码位置。
3、提供一个猴子补丁，使用猴子补丁修改三方包的模块级全局变量MAX_VARIABLE_LENGTH ，最大变量默认是100，但对调试对接方json时候，往往很大，可以加大到最大显示10万个字母。

"""
import datetime
import os
from functools import wraps
import decorator
import pysnooper  # 需要安装 pip install pysnooper==0.0.11
from pysnooper.pysnooper import get_write_function
from pysnooper.tracer import Tracer, get_local_reprs, get_source_from_frame

os_name = os.name


class TracerCanClick(Tracer):
    """
    使代码运行轨迹可点击。
    """

    def trace(self, frame, event, arg):
        if frame.f_code is not self.target_code_object:
            if self.depth == 1:

                return self.trace
            else:
                _frame_candidate = frame
                for i in range(1, self.depth):
                    _frame_candidate = _frame_candidate.f_back
                    if _frame_candidate is None:
                        return self.trace
                    elif _frame_candidate.f_code is self.target_code_object:
                        indent = ' ' * 4 * i
                        break
                else:
                    return self.trace
        else:
            indent = ''

        self.frame_to_old_local_reprs[frame] = old_local_reprs = \
            self.frame_to_local_reprs[frame]
        self.frame_to_local_reprs[frame] = local_reprs = \
            get_local_reprs(frame, variables=self.variables)

        modified_local_reprs = {}
        newish_local_reprs = {}

        for key, value in local_reprs.items():
            if key not in old_local_reprs:
                newish_local_reprs[key] = value
            elif old_local_reprs[key] != value:
                modified_local_reprs[key] = value

        newish_string = ('Starting var:.. ' if event == 'call' else
                         'New var:....... ')
        for name, value_repr in newish_local_reprs.items():
            self.write('{indent}{newish_string}{name} = {value_repr}'.format(
                **locals()))
        for name, value_repr in modified_local_reprs.items():
            self.write('{indent}Modified var:.. {name} = {value_repr}'.format(
                **locals()))

        now_string = datetime.datetime.now().time().isoformat()
        source_line = get_source_from_frame(frame)[frame.f_lineno - 1]
        # print(frame)
        # print(dir(frame.f_code))
        # print(frame.f_code.co_filename)
        file_name_and_line = f'{frame.f_code.co_filename}:{frame.f_lineno}'
        # print(file_name_and_line)

        # self.write('{indent}{now_string} {event:9} '
        #            '{frame.f_lineno:4} {source_line}'.format(**locals()))
        file_name_and_line2 = f'"{file_name_and_line}"'
        self.write('{indent}{now_string} {event:9} '  # REMIND 主要是修改了这一行，使debug可点击。
                   '{file_name_and_line2:100} {source_line}'.format(**locals()))
        return self.trace


def _snoop_can_click(output=None, variables=(), depth=1, prefix=''):
    write = get_write_function(output)

    # noinspection PyShadowingBuiltins
    @decorator.decorator
    def decorate(function, *args, **kwargs):
        target_code_object = function.__code__
        with TracerCanClick(target_code_object=target_code_object,
                            write=write, variables=variables,
                            depth=depth, prefix=prefix):
            return function(*args, **kwargs)

    return decorate


def snoop_deco(output=None, variables: tuple = (), depth=1, prefix='', do_not_effect_on_linux=True, line_can_click=True):
    # REMIND 对装饰器再包装一次，不使用上面的和官方的。
    def _snoop(func):
        nonlocal prefix
        if prefix == '':
            prefix = f'调试 [{func.__name__}] 函数 -->  '

        @wraps(func)
        def __snoop(*args, **kwargs):
            if os_name != 'nt' and do_not_effect_on_linux:  # 不要修改任何代码，自动就会不在linux上debug，一般linux是部署机器。
                return func(*args, **kwargs)
            else:
                if line_can_click:
                    return _snoop_can_click(output, variables, depth, prefix)(func)(*args, **kwargs)
                else:
                    return pysnooper.snoop(output, variables, depth, prefix)(func)(*args, **kwargs)

        return __snoop

    return _snoop


def patch_snooper_max_variable_length(max_lenth=100000):
    """
    提供一个猴子补丁，三方包默认是变量最大显示100个字母，对于我这种经常debug对接方json的，要加到10万才能显示一个josn。
    最好是放在name = main中去执行此补丁，否则由于模块是单例的永远只导入一次，会改变其他地方的运行表现。
    :param max_lenth:
    :return:
    """
    from pysnooper import tracer
    tracer.MAX_VARIABLE_LENGTH = max_lenth


if __name__ == '__main__':
    patch_snooper_max_variable_length(10000)


    @snoop_deco(line_can_click=True, do_not_effect_on_linux=True)
    def fun2():
        x = 1
        x += 2
        y = '6' * 10
        if x == 3:
            print('ttttt')
        else:
            print('ffff')


    fun2()
