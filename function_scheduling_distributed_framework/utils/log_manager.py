# coding=utf8
"""
日志管理，支持日志打印到控制台或写入切片文件或mongodb或email
使用方式为  logger = LogManager('logger_name').get_and_add_handlers(log_level_int=1, is_add_stream_handler=True, log_path=None, log_filename=None, log_file_size=10,mongo_url=None,formatter_template=2)
或者 logger = LogManager('logger_name').get_without_handlers(),此种没有handlers不立即记录日志，之后可以在单独统一的总闸处对所有日志根据loggerame进行get_and_add_handlers添加相关的各种handlers
创建一个邮件日志的用法为 logger = LogManager.bulid_a_logger_with_mail_handler('mail_logger_name', mail_time_interval=10, toaddrs=('909686xxx@qq.com', 'yangxx4508@dingtalk.com',subject='你的主题)),使用了独立的创建方式
concurrent_log_handler的ConcurrentRotatingFileHandler解决了logging模块自带的RotatingFileHandler多进程切片错误，此ConcurrentRotatingFileHandler在win和linux多进程场景下log文件切片都ok.
1、根据日志级别，使用coolorhanlder代替straemhandler打印5种颜色的日志，一目了然哪里是严重的日志。
2、带有多种handler，邮件 mongo stream file的。
3、支持pycharm点击日志跳转到对应代码文件的对应行。
4、对相同命名空间的logger可以无限添加同种类型的handlers，不会重复使用同种handler记录日志。不需要用户自己去判断。

"""
import sys
import os
from threading import Lock
import unittest
import time
from collections import OrderedDict
import pymongo
import logging
from logging import handlers
from concurrent_log_handler import ConcurrentRotatingFileHandler  # 需要安装。concurrent-log-handler==0.9.9

os_name = os.name
DING_TALK_TOKEN = 'xxxxxxxxxxxxxxxxxxx'  # 钉钉报警机器人

EMAIL_HOST = ('smtp.sohu.com', 465)
EMAIL_FROMADDR = 'xxxxxx@sohu.com'  # 'matafyhotel-techl@matafy.com',
EMAIL_TOADDRS = ('xxxxx@xxxx.com', 'zzzzzz@xxxxxx.com',)
EMAIL_CREDENTIALS = ('rrrrrr@sohu.com', '********')  # ('matafyhotel-techl@matafy.com', 'DDMkXzmlZtlNXB81YrYH'),


# noinspection PyProtectedMember,PyUnusedLocal,PyIncorrectDocstring
def very_nb_print(*args, sep=' ', end='\n', file=None):
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


# noinspection PyShadowingBuiltins
# print = very_nb_print
formatter_dict = {
    1: logging.Formatter(
        '日志时间【%(asctime)s】 - 日志名称【%(name)s】 - 文件【%(filename)s】 - 第【%(lineno)d】行 - 日志等级【%(levelname)s】 - 日志信息【%(message)s】',
        "%Y-%m-%d %H:%M:%S"),
    2: logging.Formatter(
        '%(asctime)s - %(name)s - %(filename)s - %(funcName)s - %(lineno)d - %(levelname)s - %(message)s',
        "%Y-%m-%d %H:%M:%S"),
    3: logging.Formatter(
        '%(asctime)s - %(name)s - 【 File "%(pathname)s", line %(lineno)d, in %(funcName)s 】 - %(levelname)s - %(message)s',
        "%Y-%m-%d %H:%M:%S"),  # 一个模仿traceback异常的可跳转到打印日志地方的模板
    4: logging.Formatter(
        '%(asctime)s - %(name)s - "%(filename)s" - %(funcName)s - %(lineno)d - %(levelname)s - %(message)s -               File "%(pathname)s", line %(lineno)d ',
        "%Y-%m-%d %H:%M:%S"),  # 这个也支持日志跳转
    5: logging.Formatter(
        '%(asctime)s - %(name)s - "%(pathname)s:%(lineno)d" - %(funcName)s - %(levelname)s - %(message)s',
        "%Y-%m-%d %H:%M:%S"),  # 我认为的最好的模板,推荐
    6: logging.Formatter('%(name)s - %(asctime)-15s - %(filename)s - %(lineno)d - %(levelname)s: %(message)s',
                         "%Y-%m-%d %H:%M:%S"),
    7: logging.Formatter('%(levelname)s - %(filename)s - %(lineno)d - %(message)s'),  # 一个只显示简短文件名和所处行数的日志模板
}


# noinspection PyMissingOrEmptyDocstring
class LogLevelException(Exception):
    def __init__(self, log_level):
        err = '设置的日志级别是 {0}， 设置错误，请设置为1 2 3 4 5 范围的数字'.format(log_level)
        Exception.__init__(self, err)


# noinspection PyMissingOrEmptyDocstring
class MongoHandler(logging.Handler):
    """
    一个mongodb的log handler,支持日志按loggername创建不同的集合写入mongodb中
    """

    # msg_pattern = re.compile('(\d+-\d+-\d+ \d+:\d+:\d+) - (\S*?) - (\S*?) - (\d+) - (\S*?) - ([\s\S]*)')

    def __init__(self, mongo_url, mongo_database='logs'):
        """
        :param mongo_url:  mongo连接
        :param mongo_database: 保存日志的数据库，默认使用logs数据库
        """
        logging.Handler.__init__(self)
        mongo_client = pymongo.MongoClient(mongo_url)
        self.mongo_db = mongo_client.get_database(mongo_database)

    def emit(self, record):
        # noinspection PyBroadException, PyPep8
        try:
            """以下使用解析日志模板的方式提取出字段"""
            # msg = self.format(record)
            # logging.LogRecord
            # msg_match = self.msg_pattern.search(msg)
            # log_info_dict = {'time': msg_match.group(1),
            #                  'name': msg_match.group(2),
            #                  'file_name': msg_match.group(3),
            #                  'line_no': msg_match.group(4),
            #                  'log_level': msg_match.group(5),
            #                  'detail_msg': msg_match.group(6),
            #                  }
            level_str = None
            if record.levelno == 10:
                level_str = 'DEBUG'
            elif record.levelno == 20:
                level_str = 'INFO'
            elif record.levelno == 30:
                level_str = 'WARNING'
            elif record.levelno == 40:
                level_str = 'ERROR'
            elif record.levelno == 50:
                level_str = 'CRITICAL'
            log_info_dict = OrderedDict()
            log_info_dict['time'] = time.strftime('%Y-%m-%d %H:%M:%S')
            log_info_dict['name'] = record.name
            log_info_dict['file_path'] = record.pathname
            log_info_dict['file_name'] = record.filename
            log_info_dict['func_name'] = record.funcName
            log_info_dict['line_no'] = record.lineno
            log_info_dict['log_level'] = level_str
            log_info_dict['detail_msg'] = record.msg
            col = self.mongo_db.get_collection(record.name)
            col.insert_one(log_info_dict)
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception:
            self.handleError(record)


class ColorHandler0(logging.Handler):
    """彩色日志handler，根据不同级别的日志显示不同颜色"""
    bule = 96 if os_name == 'nt' else 36
    yellow = 93 if os_name == 'nt' else 33

    def __init__(self):
        logging.Handler.__init__(self)
        self.formatter_new = logging.Formatter(
            '%(asctime)s - %(name)s - "%(filename)s" - %(funcName)s - %(lineno)d - %(levelname)s - %(message)s',
            "%Y-%m-%d %H:%M:%S")
        # 对控制台日志单独优化显示和跳转，单独对字符串某一部分使用特殊颜色，主要用于第四种模板，以免filehandler和mongohandler中带有\033

    @classmethod
    def _my_align(cls, string, length):
        if len(string) > length * 2:
            return string
        custom_length = 0
        for w in string:
            custom_length += 1 if cls._is_ascii_word(w) else 2
        if custom_length < length:
            place_length = length - custom_length
            string += ' ' * place_length
        return string

    @staticmethod
    def _is_ascii_word(w):
        if ord(w) < 128:
            return True

    def emit(self, record):
        """
        30    40    黑色
        31    41    红色
        32    42    绿色
        33    43    黃色
        34    44    蓝色
        35    45    紫红色
        36    46    青蓝色
        37    47    白色
        :type record:logging.LogRecord
        :return:
        """

        if self.formatter is formatter_dict[4] or self.formatter is self.formatter_new:
            self.formatter = self.formatter_new
            if os.name == 'nt':
                self.__emit_for_fomatter4_pycahrm(record)  # 使用模板4并使用pycharm时候
            else:
                self.__emit_for_fomatter4_linux(record)  # 使用模板4并使用linux时候
        else:
            self.__emit(record)  # 其他模板

    def __emit_for_fomatter4_linux(self, record):
        """
        当使用模板4针对linxu上的终端打印优化显示
        :param record:
        :return:
        """
        # noinspection PyBroadException,PyPep8
        try:
            msg = self.format(record)
            file_formatter = ' ' * 10 + '\033[7mFile "%s", line %d\033[0m' % (record.pathname, record.lineno)
            if record.levelno == 10:
                print('\033[0;32m%s' % self._my_align(msg, 150) + file_formatter)
            elif record.levelno == 20:
                print('\033[0;34m%s' % self._my_align(msg, 150) + file_formatter)
            elif record.levelno == 30:
                print('\033[0;33m%s' % self._my_align(msg, 150) + file_formatter)
            elif record.levelno == 40:
                print('\033[0;35m%s' % self._my_align(msg, 150) + file_formatter)
            elif record.levelno == 50:
                print('\033[0;31m%s' % self._my_align(msg, 150) + file_formatter)
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception:
            self.handleError(record)

    def __emit_for_fomatter4_pycahrm(self, record):
        """
        当使用模板4针对pycahrm的打印优化显示
        :param record:
        :return:
        """
        #              \033[0;93;107mFile "%(pathname)s", line %(lineno)d, in %(funcName)s\033[0m
        # noinspection PyBroadException
        try:
            msg = self.format(record)
            # for_linux_formatter = ' ' * 10 + '\033[7m;File "%s", line %d\033[0m' % (record.pathname, record.lineno)
            file_formatter = ' ' * 10 + '\033[0;93;107mFile "%s", line %d\033[0m' % (record.pathname, record.lineno)
            if record.levelno == 10:
                print('\033[0;32m%s\033[0m' % self._my_align(msg, 200) + file_formatter)  # 绿色
            elif record.levelno == 20:
                print('\033[0;36m%s\033[0m' % self._my_align(msg, 200) + file_formatter)  # 青蓝色
            elif record.levelno == 30:
                print('\033[0;92m%s\033[0m' % self._my_align(msg, 200) + file_formatter)  # 蓝色
            elif record.levelno == 40:
                print('\033[0;35m%s\033[0m' % self._my_align(msg, 200) + file_formatter)  # 紫红色
            elif record.levelno == 50:
                print('\033[0;31m%s\033[0m' % self._my_align(msg, 200) + file_formatter)  # 血红色
        except (KeyboardInterrupt, SystemExit):
            raise
        except:  # NOQA
            self.handleError(record)

    def __emit(self, record):
        # noinspection PyBroadException
        try:
            msg = self.format(record)
            if record.levelno == 10:
                print('\033[0;32m%s\033[0m' % msg)  # 绿色
            elif record.levelno == 20:
                print('\033[0;%sm%s\033[0m' % (self.bule, msg))  # 青蓝色 36    96
            elif record.levelno == 30:
                print('\033[0;%sm%s\033[0m' % (self.yellow, msg))
            elif record.levelno == 40:
                print('\033[0;35m%s\033[0m' % msg)  # 紫红色
            elif record.levelno == 50:
                print('\033[0;31m%s\033[0m' % msg)  # 血红色
        except (KeyboardInterrupt, SystemExit):
            raise
        except:  # NOQA
            self.handleError(record)


class ColorHandler(logging.Handler):
    """
    A handler class which writes logging records, appropriately formatted,
    to a stream. Note that this class does not close the stream, as
    sys.stdout or sys.stderr may be used.
    """

    terminator = '\n'
    bule = 96 if os_name == 'nt' else 36
    yellow = 93 if os_name == 'nt' else 33

    def __init__(self, stream=None, is_pycharm_2019=False):
        """
        Initialize the handler.

        If stream is not specified, sys.stderr is used.
        """
        logging.Handler.__init__(self)
        if stream is None:
            stream = sys.stdout  # stderr无彩。
        self.stream = stream
        self._is_pycharm_2019 = is_pycharm_2019
        self._display_method = 7 if os_name == 'posix' else 0

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
                msg_color = ('\033[%s;%sm%s\033[0m' % (self._display_method, 34 if self._is_pycharm_2019 else 32, msg))  # 绿色
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


class CompatibleSMTPSSLHandler(handlers.SMTPHandler):
    """
    官方的SMTPHandler不支持SMTP_SSL的邮箱，这个可以两个都支持,并且支持邮件发送频率限制
    """

    def __init__(self, mailhost, fromaddr, toaddrs: tuple, subject,
                 credentials=None, secure=None, timeout=5.0, is_use_ssl=True, mail_time_interval=0):
        """

        :param mailhost:
        :param fromaddr:
        :param toaddrs:
        :param subject:
        :param credentials:
        :param secure:
        :param timeout:
        :param is_use_ssl:
        :param mail_time_interval: 发邮件的时间间隔，可以控制日志邮件的发送频率，为0不进行频率限制控制，如果为60，代表1分钟内最多发送一次邮件
        """
        # noinspection PyCompatibility
        # very_nb_print(credentials)
        super().__init__(mailhost, fromaddr, toaddrs, subject,
                         credentials, secure, timeout)
        self._is_use_ssl = is_use_ssl
        self._current_time = 0
        self._time_interval = 3600 if mail_time_interval < 3600 else mail_time_interval  # 60分钟发一次群发邮件，以后用钉钉代替邮件，邮件频率限制的太死了。
        self._msg_map = dict()  # 是一个内容为键时间为值得映射
        self._lock = Lock()

    def emit0(self, record: logging.LogRecord):
        """
        不用这个判断内容
        """
        from threading import Thread
        if sys.getsizeof(self._msg_map) > 10 * 1000 * 1000:
            self._msg_map.clear()
        if record.msg not in self._msg_map or time.time() - self._msg_map[record.msg] > self._time_interval:
            self._msg_map[record.msg] = time.time()
            # print('发送邮件成功')
            Thread(target=self.__emit, args=(record,)).start()
        else:
            very_nb_print(f' 邮件发送太频繁间隔不足60分钟，此次不发送这个邮件内容： {record.msg}    ')

    def emit(self, record: logging.LogRecord):
        """
        Emit a record.

        Format the record and send it to the specified addressees.
        """
        from threading import Thread
        with self._lock:
            if time.time() - self._current_time > self._time_interval:
                self._current_time = time.time()
                Thread(target=self.__emit, args=(record,)).start()
            else:
                very_nb_print(f' 邮件发送太频繁间隔不足60分钟，此次不发送这个邮件内容： {record.msg}     ')

    def __emit(self, record):
        # noinspection PyBroadException
        try:
            import smtplib
            from email.message import EmailMessage
            import email.utils
            t_start = time.time()
            port = self.mailport
            if not port:
                port = smtplib.SMTP_PORT
            smtp = smtplib.SMTP_SSL(self.mailhost, port, timeout=self.timeout) if self._is_use_ssl else smtplib.SMTP(
                self.mailhost, port, timeout=self.timeout)
            msg = EmailMessage()
            msg['From'] = self.fromaddr
            msg['To'] = ','.join(self.toaddrs)
            msg['Subject'] = self.getSubject(record)
            msg['Date'] = email.utils.localtime()
            msg.set_content(self.format(record))
            if self.username:
                if self.secure is not None:
                    smtp.ehlo()
                    smtp.starttls(*self.secure)
                    smtp.ehlo()
                smtp.login(self.username, self.password)
            smtp.send_message(msg)
            smtp.quit()
            # noinspection PyPep8
            very_nb_print(
                f'发送邮件给 {self.toaddrs} 成功，'
                f'用时{round(time.time() - t_start, 2)} ,发送的内容是--> {record.msg}                    \033[0;35m!!!请去邮箱检查，可能在垃圾邮件中\033[0m')
        except Exception as e:
            # self.handleError(record)
            very_nb_print(
                f'[log_manager.py]   {time.strftime("%H:%M:%S", time.localtime())}  \033[0;31m !!!!!! 邮件发送失败,原因是： {e} \033[0m')


class DingTalkHandler(logging.Handler):
    def __init__(self, ding_talk_token=None, time_interval=60):
        super().__init__()
        self._ding_talk_url = f'https://oapi.dingtalk.com/robot/send?access_token={ding_talk_token}'
        self._current_time = 0
        self._time_interval = time_interval  # 最好别频繁发。
        self._lock = Lock()

    def emit(self, record):
        # from threading import Thread
        with self._lock:
            if time.time() - self._current_time > self._time_interval:
                # very_nb_print(self._current_time)
                self.__emit(record)
                # Thread(target=self.__emit, args=(record,)).start()
                self._current_time = time.time()
            else:
                very_nb_print(f' 此次离上次发送钉钉消息时间间隔不足 {self._time_interval} 秒，此次不发送这个钉钉内容： {record.msg}    ')

    def __emit(self, record):
        import requests
        message = self.format(record)
        data = {"msgtype": "text", "text": {"content": message, "title": '这里的标题能起作用吗？？'}}
        try:
            resp = requests.post(self._ding_talk_url, json=data, timeout=(30, 40))
            very_nb_print(f'钉钉返回 ： {resp.text}')
        except requests.RequestException as e:
            very_nb_print(f"发送消息给钉钉机器人失败 {e}")


# noinspection PyTypeChecker
def get_logs_dir_by_folder_name(folder_name='/app/'):
    """获取app文件夹的路径,如得到这个路径
    D:/coding/hotel_fares/app
    如果没有app文件夹，就在当前文件夹新建
    """
    three_parts_str_tuple = (os.path.dirname(__file__).replace('\\', '/').partition(folder_name))
    # print(three_parts_str_tuple)
    if three_parts_str_tuple[1]:
        return three_parts_str_tuple[0] + three_parts_str_tuple[1] + 'logs/'  # noqa
    else:
        return three_parts_str_tuple[0] + '/logs/'  # NOQA


def get_logs_dir_by_disk_root():
    """
    返回磁盘根路径下的pythonlogs文件夹,当使用文件日志时候自动创建这个文件夹。
    :return:
    """
    from pathlib import Path
    return str(Path(Path(__file__).absolute().root) / Path('pythonlogs'))


# noinspection PyMissingOrEmptyDocstring,PyPep8
class LogManager(object):
    """
    一个日志管理类，用于创建logger和添加handler，支持将日志打印到控制台打印和写入日志文件和mongodb和邮件。
    """
    logger_name_list = []
    logger_list = []

    def __init__(self, logger_name=None, is_pycharm_2019=False):
        """
        :param logger_name: 日志名称，当为None时候创建root命名空间的日志，一般情况下千万不要传None，除非你确定需要这么做和是在做什么
        """
        self._logger_name = logger_name
        self.logger = logging.getLogger(logger_name)
        self._is_pycharm_2019 = is_pycharm_2019

    # 此处可以使用*args ,**kwargs减少很多参数，但为了pycharm更好的自动智能补全提示放弃这么做
    @classmethod
    def bulid_a_logger_with_mail_handler(cls, logger_name, log_level_int=10, *, is_add_stream_handler=True,
                                         do_not_use_color_handler=False, log_path=get_logs_dir_by_disk_root(),
                                         log_filename=None,
                                         log_file_size=100, mongo_url=None,
                                         ding_talk_token=DING_TALK_TOKEN, ding_talk_time_interval=60,
                                         formatter_template=5, mailhost: tuple = EMAIL_HOST,  # ('smtpdm.aliyun.com', 465), # 公司邮箱有频率限制影响业务
                                         fromaddr: str = EMAIL_FROMADDR,  # 'matafyhotel-techl@matafy.com',
                                         toaddrs: tuple = EMAIL_TOADDRS,
                                         subject: str = '马踏飞燕日志报警测试',
                                         credentials: tuple = EMAIL_CREDENTIALS,  # ('matafyhotel-techl@matafy.com', 'DDMkXzmlZtlNXB81YrYH'),
                                         secure=None, timeout=5.0, is_use_ssl=True, mail_time_interval=60):
        """
        创建一个附带邮件handler的日志
        :param logger_name:
        :param log_level_int: 可以用1 2  3  4 5 ，用可以用官方logging模块的正规的10 20 30 40 50,兼容。
        :param is_add_stream_handler:
        :param do_not_use_color_handler:
        :param log_path:
        :param log_filename:
        :param log_file_size:
        :param mongo_url:
        :param ding_talk_token:钉钉机器人token
        :param ding_talk_time_interval : 时间间隔，少于这个时间不发送钉钉消息
        :param formatter_template:
        :param mailhost:
        :param fromaddr:
        :param toaddrs:
        :param subject:
        :param credentials:
        :param secure:
        :param timeout:
        :param is_use_ssl:
        :param mail_time_interval: 邮件的频率控制，为0不限制，如果为100，代表100秒内相同内容的邮件最多发送一次邮件
        :return:
        """
        if log_filename is None:
            log_filename = f'{logger_name}.log'
        logger = cls(logger_name).get_logger_and_add_handlers(log_level_int=log_level_int,
                                                              is_add_stream_handler=is_add_stream_handler,
                                                              do_not_use_color_handler=do_not_use_color_handler,
                                                              log_path=log_path, log_filename=log_filename,
                                                              log_file_size=log_file_size, mongo_url=mongo_url, ding_talk_token=ding_talk_token, ding_talk_time_interval=ding_talk_time_interval,
                                                              formatter_template=formatter_template, )
        smtp_handler = CompatibleSMTPSSLHandler(mailhost, fromaddr,
                                                toaddrs,
                                                subject,
                                                credentials,
                                                secure,
                                                timeout,
                                                is_use_ssl,
                                                mail_time_interval,
                                                )
        log_level_int = log_level_int * 10 if log_level_int < 10 else log_level_int
        smtp_handler.setLevel(log_level_int)
        smtp_handler.setFormatter(formatter_dict[formatter_template])
        if not cls.__judge_logger_contain_handler_class(logger, CompatibleSMTPSSLHandler):
            if logger.name == 'root':
                for logger_x in cls.logger_list:
                    for hdlr in logger_x.handlers:
                        if isinstance(hdlr, CompatibleSMTPSSLHandler):
                            logger_x.removeHandler(hdlr)
            logger.addHandler(smtp_handler)

        return logger

    # 加*是为了强制在调用此方法时候使用关键字传参，如果以位置传参强制报错，因为此方法后面的参数中间可能以后随时会增加更多参数，造成之前的使用位置传参的代码参数意义不匹配。
    # noinspection PyAttributeOutsideInit
    def get_logger_and_add_handlers(self, log_level_int: int = 10, *, is_add_stream_handler=True,
                                    do_not_use_color_handler=False, log_path=get_logs_dir_by_disk_root(),
                                    log_filename=None, log_file_size=100,
                                    mongo_url=None, ding_talk_token=None, ding_talk_time_interval=60, formatter_template=5):
        """
       :param log_level_int: 日志输出级别，设置为 1 2 3 4 5，分别对应原生logging.DEBUG(10)，logging.INFO(20)，logging.WARNING(30)，logging.ERROR(40),logging.CRITICAL(50)级别，现在可以直接用10 20 30 40 50了，兼容了。
       :param is_add_stream_handler: 是否打印日志到控制台
       :param do_not_use_color_handler :是否禁止使用color彩色日志
       :param log_path: 设置存放日志的文件夹路径
       :param log_filename: 日志的名字，仅当log_path和log_filename都不为None时候才写入到日志文件。
       :param log_file_size :日志大小，单位M，默认10M
       :param mongo_url : mongodb的连接，为None时候不添加mongohandler
       :param ding_talk_token:钉钉机器人token
       :param ding_talk_time_interval : 时间间隔，少于这个时间不发送钉钉消息
       :param formatter_template :日志模板，1为formatter_dict的详细模板，2为简要模板,5为最好模板
       :type log_level_int :int
       :type is_add_stream_handler :bool
       :type log_path :str
       :type log_filename :str
       :type mongo_url :str
       :type log_file_size :int
       """
        self._logger_level = log_level_int * 10 if log_level_int < 10 else log_level_int
        self._is_add_stream_handler = is_add_stream_handler
        self._do_not_use_color_handler = do_not_use_color_handler
        self._log_path = log_path
        self._log_filename = log_filename
        self._log_file_size = log_file_size
        self._mongo_url = mongo_url
        self._ding_talk_token = ding_talk_token
        self._ding_talk_time_interval = ding_talk_time_interval
        self._formatter = formatter_dict[formatter_template]
        self.__set_logger_level()
        self.__add_handlers()
        self.logger_name_list.append(self._logger_name)
        self.logger_list.append(self.logger)
        return self.logger

    def get_logger_without_handlers(self):
        """返回一个不带hanlers的logger"""
        return self.logger

    # noinspection PyMethodMayBeStatic,PyMissingOrEmptyDocstring
    def look_over_all_handlers(self):
        very_nb_print(f'{self._logger_name}名字的日志的所有handlers是--> {self.logger.handlers}')

    def remove_all_handlers(self):
        for hd in self.logger.handlers:
            self.logger.removeHandler(hd)

    def remove_handler_by_handler_class(self, handler_class: type):
        """
        去掉指定类型的handler
        :param handler_class:logging.StreamHandler,ColorHandler,MongoHandler,ConcurrentRotatingFileHandler,MongoHandler,CompatibleSMTPSSLHandler的一种
        :return:
        """
        if handler_class not in (logging.StreamHandler, ColorHandler, MongoHandler, ConcurrentRotatingFileHandler, MongoHandler, CompatibleSMTPSSLHandler):
            raise TypeError('设置的handler类型不正确')
        for handler in self.logger.handlers:
            if isinstance(handler, handler_class):
                self.logger.removeHandler(handler)

    def __set_logger_level(self):
        self.logger.setLevel(self._logger_level)

    def __remove_handlers_from_other_logger_when_logger_name_is_none(self, handler_class):
        """
        当logger name为None时候需要移出其他logger的handler，否则重复记录日志
        :param handler_class: handler类型
        :return:
        """
        if self._logger_name is None:
            for logger in self.logger_list:
                for hdlr in logger.handlers:
                    if isinstance(hdlr, handler_class):
                        logger.removeHandler(hdlr)

    @staticmethod
    def __judge_logger_contain_handler_class(logger: logging.Logger, handler_class):
        for h in logger.handlers + logging.getLogger().handlers:
            if isinstance(h, (handler_class,)):
                return True

    def __add_handlers(self):
        if self._is_add_stream_handler:
            if not self.__judge_logger_contain_handler_class(self.logger,
                                                             ColorHandler):  # 主要是阻止给logger反复添加同种类型的handler造成重复记录
                self.__remove_handlers_from_other_logger_when_logger_name_is_none(ColorHandler)
                self.__add_stream_handler()

        if all([self._log_path, self._log_filename]):
            if not self.__judge_logger_contain_handler_class(self.logger, ConcurrentRotatingFileHandler):
                self.__remove_handlers_from_other_logger_when_logger_name_is_none(ConcurrentRotatingFileHandler)
                self.__add_file_handler()

        if self._mongo_url:
            if not self.__judge_logger_contain_handler_class(self.logger, MongoHandler):
                self.__remove_handlers_from_other_logger_when_logger_name_is_none(MongoHandler)
                self.__add_mongo_handler()

        if self._ding_talk_token:
            if not self.__judge_logger_contain_handler_class(self.logger, DingTalkHandler):
                self.__remove_handlers_from_other_logger_when_logger_name_is_none(DingTalkHandler)
                self.__add_ding_talk_handler()

    def __add_ding_talk_handler(self):
        handler = DingTalkHandler(self._ding_talk_token, self._ding_talk_time_interval)
        handler.setLevel(self._logger_level)
        handler.setFormatter(self._formatter)
        self.logger.addHandler(handler)

    def __add_mongo_handler(self):
        """写入日志到mongodb"""
        mongo_handler = MongoHandler(self._mongo_url)
        mongo_handler.setLevel(self._logger_level)
        mongo_handler.setFormatter(self._formatter)
        self.logger.addHandler(mongo_handler)

    def __add_stream_handler(self):
        """
        日志显示到控制台
        """
        # stream_handler = logging.StreamHandler()
        stream_handler = ColorHandler(is_pycharm_2019=self._is_pycharm_2019) if not self._do_not_use_color_handler else logging.StreamHandler()  # 不使用streamhandler，使用自定义的彩色日志
        stream_handler.setLevel(self._logger_level)
        stream_handler.setFormatter(self._formatter)
        self.logger.addHandler(stream_handler)

    def __add_file_handler(self):
        """
        日志写入日志文件
        """
        if not os.path.exists(self._log_path):
            os.makedirs(self._log_path)
        log_file = os.path.join(self._log_path, self._log_filename)
        rotate_file_handler = None
        if os_name == 'nt':
            # windows下用这个，非进程安全
            rotate_file_handler = ConcurrentRotatingFileHandler(log_file, maxBytes=self._log_file_size * 1024 * 1024,
                                                                backupCount=3,
                                                                encoding="utf-8")
        if os_name == 'posix':
            # linux下可以使用ConcurrentRotatingFileHandler，进程安全的日志方式
            rotate_file_handler = ConcurrentRotatingFileHandler(log_file, maxBytes=self._log_file_size * 1024 * 1024,
                                                                backupCount=3, encoding="utf-8")
        rotate_file_handler.setLevel(self._logger_level)
        rotate_file_handler.setFormatter(self._formatter)
        self.logger.addHandler(rotate_file_handler)


def get_logger(log_name):
    return LogManager(log_name).get_logger_and_add_handlers(log_filename=f'{log_name}.log')


class LoggerMixin(object):
    subclass_logger_dict = {}

    @property
    def logger_extra_suffix(self):
        return self.__logger_extra_suffix

    @logger_extra_suffix.setter
    def logger_extra_suffix(self, value):
        # noinspection PyAttributeOutsideInit
        self.__logger_extra_suffix = value

    @property
    def logger_full_name(self):
        try:
            # noinspection PyUnresolvedReferences
            return type(self).__name__ + '-' + self.logger_extra_suffix
        except AttributeError:
            # very_nb_print(type(e))
            return type(self).__name__

    @property
    def logger(self):
        logger_name_key = self.logger_full_name + '1'
        if logger_name_key not in self.subclass_logger_dict:
            logger_var = LogManager(self.logger_full_name).get_logger_and_add_handlers()
            self.subclass_logger_dict[logger_name_key] = logger_var
            return logger_var
        else:
            return self.subclass_logger_dict[logger_name_key]

    @property
    def logger_with_file(self):
        logger_name_key = self.logger_full_name + '2'
        if logger_name_key not in self.subclass_logger_dict:
            logger_var = LogManager(self.logger_full_name).get_logger_and_add_handlers(log_filename=self.logger_full_name + '.log', log_file_size=50)
            self.subclass_logger_dict[logger_name_key] = logger_var
            return logger_var
        else:
            return self.subclass_logger_dict[logger_name_key]

    @property
    def logger_with_file_mongo(self):
        from function_scheduling_distributed_framework import frame_config
        logger_name_key = self.logger_full_name + '3'
        if logger_name_key not in self.subclass_logger_dict:
            logger_var = LogManager(self.logger_full_name).get_logger_and_add_handlers(log_filename=self.logger_full_name + '.log', log_file_size=50, mongo_url=frame_config.MONGO_CONNECT_URL)
            self.subclass_logger_dict[logger_name_key] = logger_var
            return logger_var
        else:
            return self.subclass_logger_dict[logger_name_key]


class LoggerMixinDefaultWithFileHandler(LoggerMixin):
    subclass_logger_dict = {}

    @property
    def logger(self):
        logger_name_key = self.logger_full_name + '3'
        if logger_name_key not in self.subclass_logger_dict:
            logger_var = LogManager(self.logger_full_name).get_logger_and_add_handlers(log_filename=self.logger_full_name + '.log', log_file_size=50)
            self.subclass_logger_dict[logger_name_key] = logger_var
            return logger_var
        else:
            return self.subclass_logger_dict[logger_name_key]


class LoggerLevelSetterMixin:
    # noinspection PyUnresolvedReferences
    def set_log_level(self, log_level=10):
        try:
            self.logger.setLevel(log_level)
        except AttributeError as e:
            very_nb_print(e)

        return self


simple_logger = LogManager('simple').get_logger_and_add_handlers()
defaul_logger = LogManager('hotel').get_logger_and_add_handlers(do_not_use_color_handler=True, formatter_template=7)
file_logger = LogManager('hotelf').get_logger_and_add_handlers(do_not_use_color_handler=True,
                                                               log_filename='hotel_' + time.strftime("%Y-%m-%d",
                                                                                                     time.localtime()) + ".log",
                                                               formatter_template=7)


# noinspection PyMethodMayBeStatic,PyNestedDecorators,PyArgumentEqualDefault
class _Test(unittest.TestCase):
    # noinspection PyMissingOrEmptyDocstring
    @classmethod
    def tearDownClass(cls):
        """

        """
        time.sleep(1)

    @unittest.skip
    def test_repeat_add_handlers_(self):
        """测试重复添加handlers"""
        LogManager('test').get_logger_and_add_handlers(log_path='../logs', log_filename='test.log')
        LogManager('test').get_logger_and_add_handlers(log_path='../logs', log_filename='test.log')
        LogManager('test').get_logger_and_add_handlers(log_path='../logs', log_filename='test.log')
        test_log = LogManager('test').get_logger_and_add_handlers(log_path='../logs', log_filename='test.log')
        print('下面这一句不会重复打印四次和写入日志四次')
        time.sleep(1)
        test_log.debug('这一句不会重复打印四次和写入日志四次')

    @unittest.skip
    def test_get_logger_without_hanlders(self):
        """测试没有handlers的日志"""
        log = LogManager('test2').get_logger_without_handlers()
        print('下面这一句不会被打印')
        time.sleep(1)
        log.info('这一句不会被打印')

    @unittest.skip
    def test_add_handlers(self):
        """这样可以在具体的地方任意写debug和info级别日志，只需要在总闸处规定级别就能过滤，很方便"""
        LogManager('test3').get_logger_and_add_handlers(2)
        log1 = LogManager('test3').get_logger_without_handlers()
        print('下面这一句是info级别，可以被打印出来')
        time.sleep(1)
        log1.info('这一句是info级别，可以被打印出来')
        print('下面这一句是debug级别，不能被打印出来')
        time.sleep(1)
        log1.debug('这一句是debug级别，不能被打印出来')

    @unittest.skip
    def test_only_write_log_to_file(self):  # NOQA
        """只写入日志文件"""
        log5 = LogManager('test5').get_logger_and_add_handlers(20)
        log6 = LogManager('test6').get_logger_and_add_handlers(is_add_stream_handler=False, log_filename='test6.log')
        print('下面这句话只写入文件')
        log5.debug('这句话只写入文件')
        log6.debug('这句话只写入文件')

    @unittest.skip
    def test_get_app_logs_dir(self):  # NOQA
        print(get_logs_dir_by_folder_name())
        print(get_logs_dir_by_disk_root())

    @unittest.skip
    def test_none(self):
        # noinspection PyUnusedLocal
        log1 = LogManager('log1').get_logger_and_add_handlers()
        LogManager().get_logger_and_add_handlers()

        LogManager().get_logger_and_add_handlers()
        log1 = LogManager('log1').get_logger_and_add_handlers()
        LogManager().get_logger_and_add_handlers()
        LogManager('log1').get_logger_and_add_handlers(log_filename='test_none.log')
        log1.debug('打印几次？')

    @unittest.skip
    def test_formater(self):
        logger2 = LogManager('test_formater2').get_logger_and_add_handlers(formatter_template=6)
        logger2.debug('测试日志模板2')
        logger5 = LogManager('test_formater5').get_logger_and_add_handlers(formatter_template=5)
        logger5.error('测试日志模板5')
        defaul_logger.debug('dddddd')
        file_logger.info('ffffff')

    @unittest.skip
    def test_bulid_a_logger_with_mail_handler(self):
        """
        测试日志发送到邮箱中
        :return:
        """
        logger = LogManager.bulid_a_logger_with_mail_handler('mail_logger_name', mail_time_interval=60, toaddrs=(
            '909686719@qq.com', 'yangdefeng4508@dingtalk.com', 'defeng.yang@silknets.com'))
        for _ in range(100):
            logger.warning('测试邮件日志的内容。。。。')
            time.sleep(10)

    @unittest.skip
    def test_ding_talk(self):
        logger = LogManager('testdinding').get_logger_and_add_handlers(ding_talk_token=DING_TALK_TOKEN, ding_talk_time_interval=10)
        logger.debug('啦啦啦德玛西亚1')
        logger.debug('啦啦啦德玛西亚2')
        time.sleep(10)
        logger.debug('啦啦啦德玛西亚3')

    @unittest.skip
    def test_remove_handler(self):
        logger = LogManager('test13').get_logger_and_add_handlers()
        logger.debug('去掉coloerhandler前')
        LogManager('test13').remove_handler_by_handler_class(ColorHandler)
        logger.debug('去掉coloerhandler后，此记录不会被打印')

    @unittest.skip
    def test_logging(self):
        # logging命名空间是root,会导致日志重复打印，不要直接用。
        logger = LogManager('test14').get_logger_and_add_handlers(formatter_template=4)
        logger.debug('xxxx')
        logging.warning('yyyyyyy')
        logger.warning('zzzzzzzzz')

    @unittest.skip
    def test_logger_level_setter_mixin(self):
        """
        测试可以设置日志级别的mixin类
        :return:
        """
        print('测试非常流弊的print')

        class A(LoggerMixin, LoggerLevelSetterMixin):
            pass

        a = A().set_log_level(20)
        a.logger.debug('这句话不能被显示')  # 这句话不能被打印
        a.logger.error('这句话可以显示')

    # @unittest.skip
    def test_color_and_mongo_hanlder(self):
        """测试彩色日志和日志写入mongodb"""
        from function_scheduling_distributed_framework import frame_config
        very_nb_print('测试颜色和mongo')
        logger = LogManager('helloMongo', is_pycharm_2019=False).get_logger_and_add_handlers(mongo_url=frame_config.MONGO_CONNECT_URL, formatter_template=5)
        logger.debug('一个debug级别的日志。' * 5)
        logger.info('一个info级别的日志。' * 5)
        logger.warning('一个warning级别的日志。' * 5)
        logger.error('一个error级别的日志。' * 5)
        logger.critical('一个critical级别的日志。' * 5)


if __name__ == "__main__":
    unittest.main()
    # raise Exception
