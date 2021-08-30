# coding=utf8
"""
日志管理，支持日志打印到控制台和写入切片文件和mongodb和email和钉钉机器人和elastic和kafka。
建造者模式一键创建返回添加了各种好用的handler的原生官方Logger对象，兼容性扩展性极强。
使用观察者模式按照里面的例子可以扩展各种有趣的handler。

使用方式为  logger = LogManager('logger_name').get_and_add_handlers(log_level_int=1, is_add_stream_handler=True, log_path=None, log_filename=None, log_file_size=10,mongo_url=None,formatter_template=2)
或者 logger = LogManager('logger_name').get_without_handlers(),此种没有handlers不立即记录日志，之后可以在单独统一的总闸处对所有日志根据loggerame进行get_and_add_handlers添加相关的各种handlers
创建一个邮件日志的用法为 logger = LogManager.bulid_a_logger_with_mail_handler('mail_logger_name', mail_time_interval=10, toaddrs=('909686xxx@qq.com', 'yangxx4508@dingtalk.com',subject='你的主题)),使用了独立的创建方式
concurrent_log_handler的ConcurrentRotatingFileHandler解决了logging模块自带的RotatingFileHandler多进程切片错误，此ConcurrentRotatingFileHandler在win和linux多进程场景下log文件切片都ok.

1、根据日志级别，使用coolorhanlder代替straemhandler打印5种颜色的日志，一目了然哪里是严重的日志。
2、带有多种handler，邮件 mongo stream file的。
3、支持pycharm点击日志跳转到对应代码文件的对应行。
4、对相同命名空间的logger可以无限添加同种类型的handlers，不会重复使用同种handler记录日志。不需要用户自己去判断。
5、更新文件日志性能，基于ConcurrentRotatingFileHandler继承重写，使用缓存1秒内的消息成批量的方式插入，
使极限多进程安全切片的文件日志写入性能在win下提高100倍，linux下提高10倍。

使用pycharm时候，建议重新自定义设置pycharm的console里面的主题颜色。
设置方式为 打开pycharm的settings -> Editor -> Color Scheme -> Console Colors 选择monokai，
并重新修改自定义6个颜色，设置Blue为1585FF，Cyan为06B8B8，Green 为 07E85E，Magenta为 ff1cd5,red为FF0207，yellow为FFB009。

使用xshell或finashell工具连接linux也可以自定义主题颜色，默认使用shell连接工具的颜色也可以。


"""
import atexit
import socket
import datetime
import sys
import os
import json
import traceback
import unittest
import time
from collections import OrderedDict
from queue import Queue, Empty
# noinspection PyPackageRequirements
from kafka import KafkaProducer
from elasticsearch import Elasticsearch, helpers
from threading import Lock, Thread
import pymongo
import requests
import logging
from logging import handlers
from concurrent_log_handler import ConcurrentRotatingFileHandler  # 需要安装。concurrent-log-handler==0.9.1

os_name = os.name

DING_TALK_TOKEN = '3dd0ee497f0xxx'  # 钉钉报警机器人

EMAIL_HOST = ('smtp.sohu.com', 465)
EMAIL_FROMADDR = 'ydxxx@sohu.com'
EMAIL_TOADDRS = ('chaxxx@silkxx.com', 'yaxxx8@dingtalk.com',)
EMAIL_CREDENTIALS = ('xxx@sohu.com', 'acrdd123')

ELASTIC_HOST = '1xx.xx.89.1x'
ELASTIC_PORT = 9200

KAFKA_BOOTSTRAP_SERVERS = ['192.xx.xx.202:9092']
ALWAYS_ADD_KAFKA_HANDLER_IN_TEST_ENVIRONENT = True


# noinspection PyPep8Naming
class app_config:  # 由于日志引用导入了app.config as app_config，此处模拟模块级的配置，实际代码不是这样。类名用了小写是为了不想修改多个地方兼容。
    env = 'production'
    connect_url = 'mongo://xxx'  # mongo连接


# noinspection PyProtectedMember,PyUnusedLocal,PyIncorrectDocstring
def very_nb_print(*args, sep=' ', end='\n', file=None):
    """
    超流弊的print补丁,
    :param x:
    :return:
    """
    # 获取被调用函数在被调用时所处代码行数
    line = sys._getframe().f_back.f_lineno
    # 获取被调用函数所在模块文件名
    file_name = sys._getframe(1).f_code.co_filename
    # sys.stdout.write(f'"{__file__}:{sys._getframe().f_lineno}"    {x}\n')
    args = (str(arg) for arg in args)  # REMIND 防止是数字或其他类型对象不能被join
    sys.stdout.write(
        f'\033[0;34m{time.strftime("%H:%M:%S")}\033[0m  "{file_name}:{line}"   \033[0;30;44m{"".join(args)}\033[0m\n')


# print = very_nb_print # 更精确的print的猴子补丁有另一个模块monkey_print2中独立提供，不再在日志中默认就打真正的全局print猴子补丁。
# 修改python最核心的内置函数的猴子补丁与常规猴子补丁不一样，具体看monkey_print2.py文件。

very_nb_print(
    """
    1)使用pycharm时候，建议重新自定义设置pycharm的console里面的主题颜色，以适应当前的自动彩色打印方案。
    设置方式为 打开pycharm的 File -> settings -> Editor -> Color Scheme -> Console Colors 选择monokai，
    并重新修改自定义6个颜色，设置Blue为1585FF，Cyan为06B8B8，Green 为 07E85E，Magenta为 ff1cd5,red为FF0207，yellow为FFB009。
    
    2)使用xshell或finashell工具连接linux也可以自定义主题颜色，默认使用shell连接工具的颜色也可以。
    
    颜色效果如连接 https://i.niupic.com/images/2020/03/24/76zi.png
    """)


def revision_call_handlers(self, record):  # 对logging标准模块打猴子补丁。主要是使父命名空间的handler不重复记录当前命名空间日志已有种类的handler。
    """
    重要。这可以使同名logger或父logger随意添加同种类型的handler，确保不会重复打印。

    :param self:
    :param record:
    :return:
    """

    """
    Pass a record to all relevant handlers.

    Loop through all handlers for this logger and its parents in the
    logger hierarchy. If no handler was found, output a one-off error
    message to sys.stderr. Stop searching up the hierarchy whenever a
    logger with the "propagate" attribute set to zero is found - that
    will be the last logger whose handlers are called.
    """
    c = self
    found = 0
    hdlr_type_set = set()

    while c:
        for hdlr in c.handlers:
            hdlr_type = type(hdlr)
            if hdlr_type == logging.StreamHandler:  # REMIND 因为很多handler都是继承自StreamHandler，包括filehandler，直接判断会逻辑出错。
                hdlr_type = ColorHandler
            found = found + 1
            if record.levelno >= hdlr.level:
                if hdlr_type not in hdlr_type_set:
                    hdlr.handle(record)
                hdlr_type_set.add(hdlr_type)
        if not c.propagate:
            c = None  # break out
        else:
            c = c.parent
    # noinspection PyRedundantParentheses
    if (found == 0):
        if logging.lastResort:
            if record.levelno >= logging.lastResort.level:
                logging.lastResort.handle(record)
        elif logging.raiseExceptions and not self.manager.emittedNoHandlerWarning:
            sys.stderr.write("No handlers could be found for logger"
                             " \"%s\"\n" % self.name)
            self.manager.emittedNoHandlerWarning = True


# noinspection PyProtectedMember
def revision_add_handler(self, hdlr):  # 从添加源头阻止同一个logger添加同类型的handler。
    """
    Add the specified handler to this logger.
    """
    logging._acquireLock()

    try:
        """ 官方的
        if not (hdlr in self.handlers):
            self.handlers.append(hdlr)
        """
        hdlrx_type_set = set()
        for hdlrx in self.handlers:
            hdlrx_type = type(hdlrx)
            if hdlrx_type == logging.StreamHandler:  # REMIND 因为很多handler都是继承自StreamHandler，包括filehandler，直接判断会逻辑出错。
                hdlrx_type = ColorHandler
            hdlrx_type_set.add(hdlrx_type)

        hdlr_type = type(hdlr)
        if hdlr_type == logging.StreamHandler:
            hdlr_type = ColorHandler
        if hdlr_type not in hdlrx_type_set:
            self.handlers.append(hdlr)
    finally:
        logging._releaseLock()


logging.Logger.callHandlers = revision_call_handlers  # 打猴子补丁。
logging.Logger.addHandler = revision_add_handler  # 打猴子补丁。

# noinspection PyShadowingBuiltins
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


class KafkaHandler(logging.Handler):
    """
    日志批量写入kafka中。
    """
    ES_INTERVAL_SECONDS = 0.5

    host_name = socket.gethostname()
    host_process = f'{host_name} -- {os.getpid()}'

    script_name = sys.argv[0].split('/')[-1]

    task_queue = Queue()
    last_es_op_time = time.time()
    has_start_do_bulk_op = False
    has_start_check_size_and_clear = False

    kafka_producer = None
    es_index_prefix = 'pylog-'

    def __init__(self, bootstrap_servers, **configs):
        """
        :param elastic_hosts:  es的ip地址，数组类型
        :param elastic_port：  es端口
        :param index_prefix: index名字前缀。
        """
        logging.Handler.__init__(self)
        if not self.__class__.kafka_producer:
            very_nb_print('实例化kafka producer')
            self.__class__.kafka_producer = KafkaProducer(bootstrap_servers=bootstrap_servers, **configs)

        t = Thread(target=self._do_bulk_op)
        t.setDaemon(True)
        t.start()

    @classmethod
    def __add_task_to_bulk(cls, task):
        cls.task_queue.put(task)

    # noinspection PyUnresolvedReferences
    @classmethod
    def __clear_bulk_task(cls):
        cls.task_queue.queue.clear()

    @classmethod
    def _check_size_and_clear(cls):
        """
        如果是外网传输日志到测试环境风险很大，测试环境网络经常打满，传输不了会造成日志队列堆积，会造成内存泄漏，所以需要清理。
        :return:
        """
        if cls.has_start_check_size_and_clear:
            return
        cls.has_start_check_size_and_clear = True

        def __check_size_and_clear():
            while 1:
                size = cls.task_queue.qsize()
                if size > 1000:
                    very_nb_print(f'kafka防止意外日志积累太多了,达到 {size} 个，为防止内存泄漏，清除队列')
                    cls.__clear_bulk_task()
                time.sleep(0.1)

        t = Thread(target=__check_size_and_clear)
        t.setDaemon(True)
        t.start()

    @classmethod
    def _do_bulk_op(cls):
        if cls.has_start_do_bulk_op:
            return

        cls.has_start_do_bulk_op = True
        # very_nb_print(cls.kafka_producer)
        while 1:
            try:
                # noinspection PyUnresolvedReferences
                tasks = list(cls.task_queue.queue)
                cls.__clear_bulk_task()
                for task in tasks:
                    topic = (cls.es_index_prefix + task['name']).replace('.', '').replace('_', '').replace('-', '')
                    # very_nb_print(topic)
                    cls.kafka_producer.send(topic, json.dumps(task).encode())
                cls.last_es_op_time = time.time()
            except Exception as e:
                very_nb_print(e)
            finally:
                time.sleep(cls.ES_INTERVAL_SECONDS)

    def emit(self, record):
        # noinspection PyBroadException, PyPep8
        try:
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
            log_info_dict['@timestamp'] = datetime.datetime.utcfromtimestamp(record.created).isoformat()
            log_info_dict['time'] = time.strftime('%Y-%m-%d %H:%M:%S')
            log_info_dict['name'] = record.name
            log_info_dict['host'] = self.host_name
            log_info_dict['host_process'] = self.host_process
            # log_info_dict['file_path'] = record.pathname
            log_info_dict['file_name'] = record.filename
            log_info_dict['func_name'] = record.funcName
            # log_info_dict['line_no'] = record.lineno
            log_info_dict['log_place'] = f'{record.pathname}:{record.lineno}'
            log_info_dict['log_level'] = level_str
            log_info_dict['msg'] = str(record.msg)
            log_info_dict['script'] = self.script_name
            log_info_dict['es_index'] = f'{self.es_index_prefix}{record.name.lower()}'
            self.__add_task_to_bulk(log_info_dict)

        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception:
            self.handleError(record)


class ElasticHandler000(logging.Handler):
    """
    日志批量写入es中。
    """
    ES_INTERVAL_SECONDS = 2
    host_name = socket.gethostname()

    def __init__(self, elastic_hosts: list, elastic_port, index_prefix='pylog-'):
        """
        :param elastic_hosts:  es的ip地址，数组类型
        :param elastic_port：  es端口
        :param index_prefix: index名字前缀。
        """
        logging.Handler.__init__(self)
        self._es_client = Elasticsearch(elastic_hosts, port=elastic_port)
        self._index_prefix = index_prefix
        self._task_list = []
        self._task_queue = Queue()
        self._last_es_op_time = time.time()
        t = Thread(target=self._do_bulk_op)
        t.setDaemon(True)
        t.start()

    def __add_task_to_bulk(self, task):
        self._task_queue.put(task)

    def __clear_bulk_task(self):
        # noinspection PyUnresolvedReferences
        self._task_queue.queue.clear()

    def _do_bulk_op(self):
        while 1:
            try:
                if self._task_queue.qsize() > 10000:
                    very_nb_print('防止意外日志积累太多了，不插入es了。')
                    self.__clear_bulk_task()
                    return
                # noinspection PyUnresolvedReferences
                tasks = list(self._task_queue.queue)
                self.__clear_bulk_task()
                helpers.bulk(self._es_client, tasks)

                self._last_es_op_time = time.time()
            except Exception as e:
                very_nb_print(e)
            finally:
                time.sleep(1)

    def emit(self, record):
        # noinspection PyBroadException, PyPep8
        try:
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
            log_info_dict['@timestamp'] = datetime.datetime.utcfromtimestamp(record.created).isoformat()
            log_info_dict['time'] = time.strftime('%Y-%m-%d %H:%M:%S')
            log_info_dict['name'] = record.name
            log_info_dict['host'] = self.host_name
            log_info_dict['file_path'] = record.pathname
            log_info_dict['file_name'] = record.filename
            log_info_dict['func_name'] = record.funcName
            log_info_dict['line_no'] = record.lineno
            log_info_dict['log_level'] = level_str
            log_info_dict['msg'] = str(record.msg)
            self.__add_task_to_bulk({
                "_index": f'{self._index_prefix}{record.name.lower()}',
                "_type": f'{self._index_prefix}{record.name.lower()}',
                "_source": log_info_dict
            })

        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception:
            self.handleError(record)


# noinspection PyUnresolvedReferences
class ElasticHandler(logging.Handler):
    """
    日志批量写入es中。
    """
    ES_INTERVAL_SECONDS = 0.5

    host_name = socket.gethostname()
    host_process = f'{host_name} -- {os.getpid()}'

    script_name = sys.argv[0]

    task_queue = Queue()
    last_es_op_time = time.time()
    has_start_do_bulk_op = False

    def __init__(self, elastic_hosts: list, elastic_port, index_prefix='pylog-'):
        """
        :param elastic_hosts:  es的ip地址，数组类型
        :param elastic_port：  es端口
        :param index_prefix: index名字前缀。
        """
        logging.Handler.__init__(self)
        self._es_client = Elasticsearch(elastic_hosts, port=elastic_port)
        self._index_prefix = index_prefix
        t = Thread(target=self._do_bulk_op)
        t.setDaemon(True)
        t.start()

    @classmethod
    def __add_task_to_bulk(cls, task):
        cls.task_queue.put(task)

    # noinspection PyUnresolvedReferences
    @classmethod
    def __clear_bulk_task(cls):
        cls.task_queue.queue.clear()

    def _do_bulk_op(self):
        if self.__class__.has_start_do_bulk_op:
            return
        self.__class__.has_start_do_bulk_op = True
        while 1:
            try:
                if self.__class__.task_queue.qsize() > 10000:
                    very_nb_print('防止意外日志积累太多了，不插入es了。')
                    self.__clear_bulk_task()
                    return
                tasks = list(self.__class__.task_queue.queue)
                self.__clear_bulk_task()
                helpers.bulk(self._es_client, tasks)
                self.__class__.last_es_op_time = time.time()
            except Exception as e:
                very_nb_print(e)
            finally:
                time.sleep(self.ES_INTERVAL_SECONDS)

    def emit(self, record):
        # noinspection PyBroadException, PyPep8
        try:
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
            log_info_dict['@timestamp'] = datetime.datetime.utcfromtimestamp(record.created).isoformat()
            log_info_dict['time'] = time.strftime('%Y-%m-%d %H:%M:%S')
            log_info_dict['name'] = record.name
            log_info_dict['host'] = self.host_name
            log_info_dict['host_process'] = self.host_process
            log_info_dict['file_path'] = record.pathname
            log_info_dict['file_name'] = record.filename
            log_info_dict['func_name'] = record.funcName
            log_info_dict['line_no'] = record.lineno
            log_info_dict['log_level'] = level_str
            log_info_dict['msg'] = str(record.msg)
            log_info_dict['script'] = self.script_name
            self.__add_task_to_bulk({
                "_index": f'{self._index_prefix}{record.name.lower()}',
                "_type": f'{self._index_prefix}{record.name.lower()}',
                "_source": log_info_dict
            })

        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception:
            self.handleError(record)


class ColorHandler000(logging.Handler):
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
        self._word_color = 30 if os_name == 'posix' else 30

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
                msg_color = ('\033[%s;%sm%s\033[0m' % (
                    self._display_method, 34 if self._is_pycharm_2019 else 32, msg))  # 绿色
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
            # very_nb_print(record)
            msg = self.format(record)
            stream = self.stream
            msg1, msg2 = self.__spilt_msg(record.levelno, msg)
            if record.levelno == 10:
                # msg_color = ('\033[0;32m%s\033[0m' % msg)  # 绿色
                # print(msg1)
                msg_color = f'\033[0;32m{msg1}\033[0m \033[0;{self._word_color};42m{msg2}\033[0m'  # 绿色
            elif record.levelno == 20:
                # msg_color = ('\033[%s;%sm%s\033[0m' % (self._display_method, self.bule, msg))  # 青蓝色 36    96
                msg_color = f'\033[0;36m{msg1}\033[0m \033[0;{self._word_color};46m{msg2}\033[0m'
            elif record.levelno == 30:
                # msg_color = ('\033[%s;%sm%s\033[0m' % (self._display_method, self.yellow, msg))
                msg_color = f'\033[0;33m{msg1}\033[0m \033[0;{self._word_color};43m{msg2}\033[0m'
            elif record.levelno == 40:
                # msg_color = ('\033[%s;35m%s\033[0m' % (self._display_method, msg))  # 紫红色
                msg_color = f'\033[0;35m{msg1}\033[0m \033[0;{self._word_color};45m{msg2}\033[0m'
            elif record.levelno == 50:
                # msg_color = ('\033[%s;31m%s\033[0m' % (self._display_method, msg))  # 血红色
                msg_color = f'\033[0;31m{msg1}\033[0m \033[0;{self._word_color};41m{msg2}\033[0m'
            else:
                msg_color = msg
            # print(msg_color,'***************')
            stream.write(msg_color)
            stream.write(self.terminator)
            self.flush()
        except Exception as e:
            very_nb_print(e)
            very_nb_print(traceback.format_exc())
            # self.handleError(record)

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


class ConcurrentRotatingFileHandlerWithBufferPassivity(ConcurrentRotatingFileHandler):
    """
    ConcurrentRotatingFileHandler 解决了多进程下文件切片问题，但频繁操作文件锁，带来程序性能巨大下降。
    反复测试极限日志写入频次，在windows上比不切片的写入性能降低100倍。在linux上比不切片性能降低10倍。多进程切片文件锁在windows使用pywin32，在linux上还是要fcntl实现。
    所以此类使用缓存1秒钟内的日志为一个长字符串再插入，大幅度地降低了文件加锁和解锁的次数，速度和不做多进程安全切片的文件写入速度几乎一样。
    被动触发方式，最后一条记录有可能要过很久才会记录到文件中。
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._buffer_msgs = ''
        self._last_write_time = time.time()
        atexit.register(self.__when_exit)  # 如果程序属于立马就能结束的，需要在程序结束前执行这个钩子，防止不到最后一秒的日志没记录到。

    def __when_exit(self):
        try:
            self._do_lock()
            self.do_write(self._buffer_msgs)
        finally:
            self._do_unlock()

    def emit(self, record):
        """
        emit已经在logger的handle方法中加了锁，所以这里的重置上次写入时间和清除buffer_msgs不需要加锁了。
        :param record:
        :return:
        """
        # noinspection PyBroadException
        try:
            msg = self.format(record)
            self._buffer_msgs += msg + '\n'
            if time.time() - self._last_write_time > 1:
                try:
                    self._do_lock()
                    try:
                        if self.shouldRollover(record):
                            self.doRollover()
                    except Exception as e:
                        self._console_log("Unable to do rollover: %s" % (e,), stack=True)
                        # Continue on anyway
                    self.do_write(self._buffer_msgs)
                finally:
                    self._do_unlock()
                    self._buffer_msgs = ''
                    self._last_write_time = time.time()

        except Exception:
            self.handleError(record)


class ConcurrentRotatingFileHandlerWithBufferInitiativeWindwos(ConcurrentRotatingFileHandler):
    """
    ConcurrentRotatingFileHandler 解决了多进程下文件切片问题，但频繁操作文件锁，带来程序性能巨大下降。
    反复测试极限日志写入频次，在windows上比不切片的写入性能降低100倍。在linux上比不切片性能降低10倍。多进程切片文件锁在windows使用pywin32，在linux上还是要fcntl实现。
    所以此类使用缓存1秒钟内的日志为一个长字符串再插入，大幅度地降低了文件加锁和解锁的次数，速度和不做多进程安全切片的文件写入速度几乎一样。
    主动触发写入文件。
    """
    file_handler_list = []
    has_start_emit_all_file_handler = False  # 只能在windwos运行正常，windwos是多进程每个进程的变量has_start_emit_all_file_handler是独立的。linux是共享的。

    @classmethod
    def _emit_all_file_handler(cls):
        while True:
            for hr in cls.file_handler_list:
                # very_nb_print(hr.buffer_msgs_queue.qsize())
                hr.rollover_and_do_write()
            time.sleep(1)

    @classmethod
    def start_emit_all_file_handler(cls):
        pass
        Thread(target=cls._emit_all_file_handler, daemon=True).start()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.buffer_msgs_queue = Queue()
        atexit.register(self._when_exit)  # 如果程序属于立马就能结束的，需要在程序结束前执行这个钩子，防止不到最后一秒的日志没记录到。
        self.file_handler_list.append(self)
        if not self.has_start_emit_all_file_handler:
            self.start_emit_all_file_handler()
            self.__class__.has_start_emit_all_file_handler = True

    def _when_exit(self):
        pass
        self.rollover_and_do_write()

    def emit(self, record):
        """
        emit已经在logger的handle方法中加了锁，所以这里的重置上次写入时间和清除buffer_msgs不需要加锁了。
        :param record:
        :return:
        """
        # noinspection PyBroadException
        try:
            msg = self.format(record)
            self.buffer_msgs_queue.put(msg)
        except Exception:
            self.handleError(record)

    def rollover_and_do_write(self, ):
        # very_nb_print(self.buffer_msgs_queue.qsize())
        self._rollover_and_do_write()

    def _rollover_and_do_write(self):
        buffer_msgs = ''
        while True:
            try:
                msg = self.buffer_msgs_queue.get(block=False)
                buffer_msgs += msg + '\n'
            except Empty:
                break
        if buffer_msgs:
            try:
                self._do_lock()
                try:
                    if self.shouldRollover(None):
                        self.doRollover()
                except Exception as e:
                    self._console_log("Unable to do rollover: %s" % (e,), stack=True)
                # very_nb_print(len(self._buffer_msgs))
                self.do_write(buffer_msgs)
            finally:
                self._do_unlock()


class ConcurrentRotatingFileHandlerWithBufferInitiativeLinux(ConcurrentRotatingFileHandlerWithBufferInitiativeWindwos):
    """
    ConcurrentRotatingFileHandler 解决了多进程下文件切片问题，但频繁操作文件锁，带来程序性能巨大下降。
    反复测试极限日志写入频次，在windows上比不切片的写入性能降低100倍。在linux上比不切片性能降低10倍。多进程切片文件锁在windows使用pywin32，在linux上还是要fcntl实现。
    所以此类使用缓存1秒钟内的日志为一个长字符串再插入，大幅度地降低了文件加锁和解锁的次数，速度和不做多进程安全切片的文件写入速度几乎一样。
    主动触发写入文件。
    """
    file_handler_list = []
    has_start_emit_all_file_handler_process_id_set = set()  # 这个linux和windwos都兼容，windwos是多进程每个进程的变量has_start_emit_all_file_handler是独立的。linux是共享的。
    __lock_for_rotate = Lock()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.buffer_msgs_queue = Queue()
        atexit.register(self._when_exit)  # 如果程序属于立马就能结束的，需要在程序结束前执行这个钩子，防止不到最后一秒的日志没记录到。
        self.file_handler_list.append(self)
        if os.getpid() not in self.has_start_emit_all_file_handler_process_id_set:
            self.start_emit_all_file_handler()
            self.__class__.has_start_emit_all_file_handler_process_id_set.add(os.getpid())

    def rollover_and_do_write(self, ):
        # very_nb_print(self.buffer_msgs_queue.qsize())
        with self.__lock_for_rotate:
            self._rollover_and_do_write()


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
                                         log_file_size=100, mongo_url=None, is_add_elastic_handler=False,
                                         is_add_kafka_handler=False,
                                         ding_talk_token=DING_TALK_TOKEN, ding_talk_time_interval=60,
                                         formatter_template=5, mailhost: tuple = EMAIL_HOST,
                                         fromaddr: str = EMAIL_FROMADDR,
                                         toaddrs: tuple = EMAIL_TOADDRS,
                                         subject: str = '马踏飞燕日志报警测试',
                                         credentials: tuple = EMAIL_CREDENTIALS,
                                         secure=None, timeout=5.0, is_use_ssl=True, mail_time_interval=60):

        if log_filename is None:
            log_filename = f'{logger_name}.log'
        logger = cls(logger_name).get_logger_and_add_handlers(log_level_int=log_level_int,
                                                              is_add_stream_handler=is_add_stream_handler,
                                                              do_not_use_color_handler=do_not_use_color_handler,
                                                              log_path=log_path, log_filename=log_filename,
                                                              log_file_size=log_file_size, mongo_url=mongo_url,
                                                              is_add_elastic_handler=is_add_elastic_handler,
                                                              is_add_kafka_handler=is_add_kafka_handler,
                                                              ding_talk_token=ding_talk_token,
                                                              ding_talk_time_interval=ding_talk_time_interval,
                                                              formatter_template=formatter_template, )
        if cls._judge_logger_has_handler_type(logger, CompatibleSMTPSSLHandler):
            return logger
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
        logger.addHandler(smtp_handler)
        return logger

    # 加*是为了强制在调用此方法时候使用关键字传参，如果以位置传参强制报错，因为此方法后面的参数中间可能以后随时会增加更多参数，造成之前的使用位置传参的代码参数意义不匹配。
    # noinspection PyAttributeOutsideInit
    def get_logger_and_add_handlers(self, log_level_int: int = 10, *, is_add_stream_handler=True,
                                    do_not_use_color_handler=False, log_path=get_logs_dir_by_disk_root(),
                                    log_filename=None, log_file_size=100,
                                    mongo_url=None, is_add_elastic_handler=False, is_add_kafka_handler=False,
                                    ding_talk_token=None, ding_talk_time_interval=60, formatter_template=5):
        """
       :param log_level_int: 日志输出级别，设置为 1 2 3 4 5，分别对应原生logging.DEBUG(10)，logging.INFO(20)，logging.WARNING(30)，logging.ERROR(40),logging.CRITICAL(50)级别，现在可以直接用10 20 30 40 50了，兼容了。
       :param is_add_stream_handler: 是否打印日志到控制台
       :param do_not_use_color_handler :是否禁止使用color彩色日志
       :param log_path: 设置存放日志的文件夹路径
       :param log_filename: 日志的名字，仅当log_path和log_filename都不为None时候才写入到日志文件。
       :param log_file_size :日志大小，单位M，默认10M
       :param mongo_url : mongodb的连接，为None时候不添加mongohandler
       :param is_add_elastic_handler: 是否记录到es中。
       :param is_add_kafka_handler: 日志是否发布到kafka。
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
        self._is_add_elastic_handler = is_add_elastic_handler
        self._is_add_kafka_handler = is_add_kafka_handler
        self._ding_talk_token = ding_talk_token
        self._ding_talk_time_interval = ding_talk_time_interval
        self._formatter = formatter_dict[formatter_template]
        self.logger.setLevel(self._logger_level)
        self.__add_handlers()
        # self.logger_name_list.append(self._logger_name)
        # self.logger_list.append(self.logger)
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
        if handler_class not in (
                logging.StreamHandler, ColorHandler, MongoHandler, ConcurrentRotatingFileHandler, MongoHandler,
                CompatibleSMTPSSLHandler, ElasticHandler, DingTalkHandler, KafkaHandler):
            raise TypeError('设置的handler类型不正确')
        for handler in self.logger.handlers:
            if isinstance(handler, handler_class):
                self.logger.removeHandler(handler)

    def __add_a_hanlder(self, handlerx: logging.Handler):
        handlerx.setLevel(10)
        handlerx.setFormatter(self._formatter)
        self.logger.addHandler(handlerx)

    @staticmethod
    def _judge_logger_has_handler_type(logger, handler_type: type):
        for hr in logger.handlers:
            if isinstance(hr, handler_type):
                return True

    def __add_handlers(self):
        pass

        # REMIND 添加控制台日志
        if not (self._judge_logger_has_handler_type(self.logger, ColorHandler) or self._judge_logger_has_handler_type(
                self.logger, logging.StreamHandler)) and self._is_add_stream_handler:
            handler = ColorHandler(
                is_pycharm_2019=self._is_pycharm_2019) if not self._do_not_use_color_handler else logging.StreamHandler()  # 不使用streamhandler，使用自定义的彩色日志
            # handler = logging.StreamHandler()
            self.__add_a_hanlder(handler)

        # REMIND 添加多进程安全切片的文件日志
        if not self._judge_logger_has_handler_type(self.logger, ConcurrentRotatingFileHandler) and all(
                [self._log_path, self._log_filename]):
            if not os.path.exists(self._log_path):
                os.makedirs(self._log_path)
            log_file = os.path.join(self._log_path, self._log_filename)
            rotate_file_handler = None
            if os_name == 'nt':
                # 在win下使用这个ConcurrentRotatingFileHandler可以解决多进程安全切片，但性能损失惨重。
                # 10进程各自写入10万条记录到同一个文件消耗15分钟。比不切片写入速度降低100倍。
                rotate_file_handler = ConcurrentRotatingFileHandlerWithBufferInitiativeWindwos(log_file,
                                                                                               maxBytes=self._log_file_size * 1024 * 1024,
                                                                                               backupCount=3,
                                                                                               encoding="utf-8")

                # windows下用这个，多进程安全，但不能切片，自己手动删除，要确保每天剩余磁盘空间很大。
                # rotate_file_handler = logging.FileHandler(log_file,encoding="utf-8")

                # windows下用这个，多进程不安全，多进程写入同一个文件切片瞬间时候100%会出错，导致程序出错。
                # rotate_file_handler = logging.handlers.RotatingFileHandler(log_file, maxBytes=self._log_file_size * 1024 * 1024,
                #                                                            backupCount=3,
                #                                                            encoding="utf-8")

            elif os_name == 'posix':
                # linux下可以使用ConcurrentRotatingFileHandler，进程安全的日志方式。
                # 10进程各自写入10万条记录到同一个文件消耗100秒，还是比不切片写入速度降低10倍。因为每次检查切片大小和文件锁的原因。
                rotate_file_handler = ConcurrentRotatingFileHandlerWithBufferInitiativeLinux(log_file,
                                                                                             maxBytes=self._log_file_size * 1024 * 1024,
                                                                                             backupCount=3,
                                                                                             encoding="utf-8")
            self.__add_a_hanlder(rotate_file_handler)

        # REMIND 添加mongo日志。
        if not self._judge_logger_has_handler_type(self.logger, MongoHandler) and self._mongo_url:
            self.__add_a_hanlder(MongoHandler(self._mongo_url))

        # REMIND 添加es日志。
        # if app_config.env == 'test' and self._is_add_elastic_handler:
        if not self._judge_logger_has_handler_type(self.logger,
                                                   ElasticHandler) and app_config.env == 'testxxxxxx':  # 使用kafka。不直接es。
            """
            生产环境使用阿里云 oss日志，不使用这个。
            """
            self.__add_a_hanlder(ElasticHandler([ELASTIC_HOST], ELASTIC_PORT))

        # REMIND 添加kafka日志。
        # if self._is_add_kafka_handler:
        if not self._judge_logger_has_handler_type(self.logger,
                                                   KafkaHandler) and app_config.env == 'test' and ALWAYS_ADD_KAFKA_HANDLER_IN_TEST_ENVIRONENT:
            self.__add_a_hanlder(KafkaHandler(KAFKA_BOOTSTRAP_SERVERS, ))

        # REMIND 添加钉钉日志。
        if not self._judge_logger_has_handler_type(self.logger, DingTalkHandler) and self._ding_talk_token:
            self.__add_a_hanlder(DingTalkHandler(self._ding_talk_token, self._ding_talk_time_interval))


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
            logger_var = LogManager(self.logger_full_name).get_logger_and_add_handlers(
                log_filename=self.logger_full_name + '.log', log_file_size=50)
            self.subclass_logger_dict[logger_name_key] = logger_var
            return logger_var
        else:
            return self.subclass_logger_dict[logger_name_key]

    @property
    def logger_with_file_mongo(self):
        logger_name_key = self.logger_full_name + '3'
        if logger_name_key not in self.subclass_logger_dict:
            logger_var = LogManager(self.logger_full_name).get_logger_and_add_handlers(
                log_filename=self.logger_full_name + '.log', log_file_size=50, mongo_url=app_config.connect_url)
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
            logger_var = LogManager(self.logger_full_name).get_logger_and_add_handlers(
                log_filename=self.logger_full_name + '.log', log_file_size=50)
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
        logger = LogManager('testdinding').get_logger_and_add_handlers(ding_talk_token=DING_TALK_TOKEN,
                                                                       ding_talk_time_interval=10)
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

    @unittest.skip
    def test_color_and_mongo_hanlder(self):
        """测试彩色日志和日志写入mongodb"""
        very_nb_print('测试颜色和mongo')

        # logger = LogManager('helloMongo', is_pycharm_2019=False).get_logger_and_add_handlers(mongo_url=app_config.connect_url, formatter_template=5)
        logging.error('xxxx')
        logger = LogManager('helloMongo', is_pycharm_2019=False).get_logger_and_add_handlers(formatter_template=5)
        logger.addHandler(ColorHandler())  # 由于打了强大的猴子补丁，无惧反复添加同种handler。
        logger.addHandler(ColorHandler())
        logger.addHandler(ColorHandler())
        for i in range(1000000):
            time.sleep(0.1)
            logger.debug('一个debug级别的日志。' * 5)
            logger.info('一个info级别的日志。' * 5)
            logger.warning('一个warning级别的日志。' * 5)
            logger.error('一个error级别的日志。' * 5)
            logger.critical('一个critical级别的日志。' * 5)


def test_multiprocess_file_handler():
    logger = LogManager('abcd').get_logger_and_add_handlers(is_add_stream_handler=False,
                                                            log_filename='amulti_test91.log', log_file_size=100)
    t1 = time.time()
    for i in range(100000, 200000):
        time.sleep(0.000001)
        logger.debug(f'{i}a')
        if i % 10000 == 0:
            very_nb_print(i)
    very_nb_print(time.time() - t1)
    time.sleep(10)


if __name__ == "__main__":
    unittest.main()
    # from multiprocessing import Process
    #
    # [Process(target=test_multiprocess_file_handler, ).start() for _ in range(10)]
