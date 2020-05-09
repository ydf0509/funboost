# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2019/8/1 0001 17:54
"""
如果老项目没用使用Logmanager,可以打此猴子补丁，自动使项目中的任何日志变彩色和可跳转。

"""

import sys
import os
import logging


class ColorHandler(logging.Handler):
    """
    A handler class which writes logging records, appropriately formatted,
    to a stream. Note that this class does not close the stream, as
    sys.stdout or sys.stderr may be used.
    """
    os_name = os.name
    terminator = '\n'
    bule = 96 if os_name == 'nt' else 36
    yellow = 93 if os_name == 'nt' else 33

    def __init__(self, stream=None, ):
        """
        Initialize the handler.

        If stream is not specified, sys.stderr is used.
        """
        logging.Handler.__init__(self)
        self.formatter = logging.Formatter(
            '%(asctime)s - %(name)s - "%(pathname)s:%(lineno)d" - %(funcName)s - %(levelname)s - %(message)s',
            "%Y-%m-%d %H:%M:%S")
        if stream is None:
            stream = sys.stdout  # stderr无彩。
        self.stream = stream
        self._display_method = 7 if self.os_name == 'posix' else 0

    def setFormatter(self, fmt):
        pass  # 禁止私自设置日志模板。固定使用可跳转的模板。

    def flush(self):
        """
        Flushes the stream.
        """
        self.acquire()
        try:
            if self.stream and hasattr(self.stream, "flush"):
                self.stream.flush()
        finally:
            self.release()

    def emit0(self, record):
        """
        前后彩色不分离的方式
        Emit a record.

        If a formatter is specified, it is used to format the record.
        The record is then written to the stream with a trailing newline.  If
        exception information is present, it is formatted using
        traceback.print_exception and appended to the stream.  If the stream
        has an 'encoding' attribute, it is used to determine how to do the
        output to the stream.
        """
        # noinspection PyBroadException
        try:
            msg = self.format(record)
            stream = self.stream
            if record.levelno == 10:
                # msg_color = ('\033[0;32m%s\033[0m' % msg)  # 绿色
                msg_color = ('\033[%s;%sm%s\033[0m' % (self._display_method, 32, msg))  # 绿色
            elif record.levelno == 20:
                msg_color = ('\033[%s;%sm%s\033[0m' % (self._display_method, self.bule, msg))  # 青蓝色 36    96
            elif record.levelno == 30:
                msg_color = ('\033[%s;%sm%s\033[0m' % (self._display_method, self.yellow, msg))
            elif record.levelno == 40:
                msg_color = ('\033[%s;35m%s\033[0m' % (self._display_method, msg))  # 紫红色
            elif record.levelno == 50:
                msg_color = ('\033[%s;31m%s\033[0m' % (self._display_method, msg))  # 血红色
            else:
                msg_color = msg
            # print(msg_color,'***************')
            stream.write(msg_color)
            stream.write(self.terminator)
            self.flush()
        except Exception:
            self.handleError(record)

    def emit(self, record):
        """
        前后彩色分离的方式。
        Emit a record.

        If a formatter is specified, it is used to format the record.
        The record is then written to the stream with a trailing newline.  If
        exception information is present, it is formatted using
        traceback.print_exception and appended to the stream.  If the stream
        has an 'encoding' attribute, it is used to determine how to do the
        output to the stream.
        """
        # noinspection PyBroadException
        try:
            msg = self.format(record)
            stream = self.stream
            msg1, msg2 = self.__spilt_msg(record.levelno, msg)
            if record.levelno == 10:
                # msg_color = ('\033[0;32m%s\033[0m' % msg)  # 绿色
                msg_color = f'\033[0;32m{msg1}\033[0m \033[7;32m{msg2}\033[0m'  # 绿色
            elif record.levelno == 20:
                # msg_color = ('\033[%s;%sm%s\033[0m' % (self._display_method, self.bule, msg))  # 青蓝色 36    96
                msg_color = f'\033[0;{self.bule}m{msg1}\033[0m \033[7;{self.bule}m{msg2}\033[0m'
            elif record.levelno == 30:
                # msg_color = ('\033[%s;%sm%s\033[0m' % (self._display_method, self.yellow, msg))
                msg_color = f'\033[0;{self.yellow}m{msg1}\033[0m \033[7;{self.yellow}m{msg2}\033[0m'
            elif record.levelno == 40:
                # msg_color = ('\033[%s;35m%s\033[0m' % (self._display_method, msg))  # 紫红色
                msg_color = f'\033[0;35m{msg1}\033[0m \033[7;35m{msg2}\033[0m'
            elif record.levelno == 50:
                # msg_color = ('\033[%s;31m%s\033[0m' % (self._display_method, msg))  # 血红色
                msg_color = f'\033[0;31m{msg1}\033[0m \033[7;31m{msg2}\033[0m'
            else:
                msg_color = msg
            # print(msg_color,'***************')
            stream.write(msg_color)
            stream.write(self.terminator)
            self.flush()
        except Exception:
            self.handleError(record)

    @staticmethod
    def __spilt_msg(log_level, msg: str):
        split_text = '- 级别 -'
        if log_level == 10:
            split_text = '- DEBUG -'
        elif log_level == 20:
            split_text = '- INFO -'
        elif log_level == 30:
            split_text = '- WARNING -'
        elif log_level == 40:
            split_text = '- ERROR -'
        elif log_level == 50:
            split_text = '- CRITICAL -'
        msg_split = msg.split(split_text, maxsplit=1)
        return msg_split[0] + split_text, msg_split[-1]

    def __repr__(self):
        level = logging.getLevelName(self.level)
        name = getattr(self.stream, 'name', '')
        if name:
            name += ' '
        return '<%s %s(%s)>' % (self.__class__.__name__, name, level)


logging.StreamHandler = ColorHandler  # REMIND 这一行就是打猴子补丁，可以尝试注释掉这一行对比。
"""
这里就是打猴子补丁,要在脚本最开始打猴子补丁，越早越好。
否则原来脚本中使用from logging import StreamHandler变为不了彩色的handler。
只有import logging，logging.StreamHandler的这种用法才会变彩。所以猴子补丁要趁早打。
"""


def my_func():
    """
    模拟常规使用控制台StreamHandler日志的方式。自动变彩。
    :return:
    """
    from logging import StreamHandler
    logger = logging.getLogger('abc')
    print(logger.handlers)
    print(StreamHandler().formatter)
    logger.addHandler(StreamHandler())
    logger.setLevel(10)
    print(logger.handlers)
    for _ in range(100):
        logger.debug('一个debug级别的日志' * 5)
        logger.info('一个info级别的日志' * 5)
        logger.warning('一个warning级别的日志' * 5)
        logger.error('一个error级别的日志' * 5)
        logger.critical('一个critical级别的日志' * 5)


if __name__ == '__main__':
    my_func()
