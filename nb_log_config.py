# coding=utf8
"""
此文件nb_log_config.py是自动生成到python项目的根目录的。
在这里面写的变量会覆盖此文件nb_log_config_default中的值。对nb_log包进行默认的配置。
但最终配置方式是由get_logger_and_add_handlers方法的各种传参决定，如果方法相应的传参为None则使用这里面的配置。
"""
import json

"""
如果反对日志有各种彩色，可以设置 DEFAULUT_USE_COLOR_HANDLER = False
如果反对日志有块状背景彩色，可以设置 DISPLAY_BACKGROUD_COLOR_IN_CONSOLE = False
如果想屏蔽nb_log包对怎么设置pycahrm的颜色的提示，可以设置 WARNING_PYCHARM_COLOR_SETINGS = False
如果想改变日志模板，可以设置 FORMATTER_KIND 参数，只带了7种模板，可以自定义添加喜欢的模板
LOG_PATH 配置文件日志的保存路径的文件夹。
"""

# noinspection PyUnresolvedReferences
import logging
import os
# noinspection PyUnresolvedReferences
from pathlib import Path  # noqa
import socket
from pythonjsonlogger.jsonlogger import JsonFormatter


def get_host_ip():
    ip = ''
    host_name = ''
    # noinspection PyBroadException
    try:
        sc = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sc.connect(('8.8.8.8', 80))
        ip = sc.getsockname()[0]
        host_name = socket.gethostname()
        sc.close()
    except Exception:
        pass
    return ip, host_name


computer_ip, computer_name = get_host_ip()

def _json_translate(obj):
    print(obj)
    if isinstance(obj, dict):
        return obj

class JsonFormatterJumpAble(JsonFormatter):
    def add_fields000(self, log_record, record, message_dict):
        print(1,log_record,2,record,3,message_dict)
        # log_record['jump_click'] = f"{record.__dict__.get('pathname')}:{record.__dict__.get('lineno')}"
        log_record[f"{record.__dict__.get('pathname')}:{record.__dict__.get('lineno')}"] = ''  # 加个能点击跳转的字段。
        log_record['ip'] = computer_ip
        log_record['host_name'] = computer_name
        print(type(record.msg),repr(record.msg),type(record.message),record.message)
        # msg_dict = None
        # if record.msg.startswith('{'):
        #     try:
        #         msg_dict = json.loads(record.msg)
        #     except Exception:
        #         pass
        raw_no_color_msg = getattr(record,'raw_no_color_msg')
        print(raw_no_color_msg)
        if isinstance(raw_no_color_msg,dict):
            log_record['msg_dict'] = record.msg
        super().add_fields(log_record, record, message_dict)
        if 'for_segmentation_color' in log_record:
            del log_record['for_segmentation_color']

    def add_fields(self, log_record, record, message_dict):
        # log_record['jump_click']   = f"""File '{record.__dict__.get('pathname')}', line {record.__dict__.get('lineno')}"""
        log_record[f"{record.__dict__.get('pathname')}:{record.__dict__.get('lineno')}"] = ''  # 加个能点击跳转的字段。
        log_record['ip'] = computer_ip
        log_record['host_name'] = computer_name
        super().add_fields(log_record, record, message_dict)
        if 'for_segmentation_color' in log_record:
            del log_record['for_segmentation_color']


DING_TALK_TOKEN = '3dd0eexxxxxadab014bd604XXXXXXXXXXXX'  # 钉钉报警机器人

EMAIL_HOST = ('smtp.sohu.com', 465)
EMAIL_FROMADDR = 'aaa0509@sohu.com'  # 'matafyhotel-techl@matafy.com',
EMAIL_TOADDRS = ('cccc.cheng@silknets.com', 'yan@dingtalk.com',)
EMAIL_CREDENTIALS = ('aaa0509@sohu.com', 'abcdefg')

ELASTIC_HOST = '127.0.0.1'
ELASTIC_PORT = 9200

KAFKA_BOOTSTRAP_SERVERS = ['192.168.199.202:9092']
ALWAYS_ADD_KAFKA_HANDLER_IN_TEST_ENVIRONENT = False

MONGO_URL = 'mongodb://myUserAdmin:mimamiama@127.0.0.1:27016/admin'

USE_BULK_STDOUT_ON_WINDOWS = False # 在win上是否每隔0.1秒批量stdout,win的io太差了

DEFAULUT_USE_COLOR_HANDLER = True  # 是否默认使用有彩的日志。
DEFAULUT_IS_USE_LOGURU_STREAM_HANDLER = False # 是否默认使用 loguru的控制台日志，而非是nb_log的ColorHandler
DISPLAY_BACKGROUD_COLOR_IN_CONSOLE = True  # 在控制台是否显示彩色块状的日志。为False则不使用大块的背景颜色。
AUTO_PATCH_PRINT = True  # 是否自动打print的猴子补丁，如果打了猴子补丁，print自动变色和可点击跳转。
WHITE_COLOR_CODE = 97

DEFAULT_ADD_MULTIPROCESSING_SAFE_ROATING_FILE_HANDLER = False  # 是否默认同时将日志记录到记log文件记事本中。
AUTO_WRITE_ERROR_LEVEL_TO_SEPARATE_FILE = True # 自动把错误error级别以上日志写到单独的文件，根据log_filename名字自动生成错误文件日志名字。
LOG_FILE_SIZE = 100  # 单位是M,每个文件的切片大小，超过多少后就自动切割
LOG_FILE_BACKUP_COUNT = 3  # 对同一个日志文件，默认最多备份几个文件，超过就删除了。

LOG_PATH = '/pythonlogs'  # 默认的日志文件夹,如果不写明磁盘名，则是项目代码所在磁盘的根目录下的/pythonlogs
# LOG_PATH = Path(__file__).absolute().parent / Path("pythonlogs")   #这么配置就会自动在你项目的根目录下创建pythonlogs文件夹了并写入。
if os.name == 'posix':  # linux非root用户和mac用户无法操作 /pythonlogs 文件夹，没有权限，默认修改为   home/[username]  下面了。例如你的linux用户名是  xiaomin，那么默认会创建并在 /home/xiaomin/pythonlogs文件夹下写入日志文件。
    home_path = os.environ.get("HOME", '/')  # 这个是获取linux系统的当前用户的主目录，不需要亲自设置
    LOG_PATH = Path(home_path) / Path('pythonlogs')  # linux mac 权限很严格，非root权限不能在/pythonlogs写入，修改一下默认值。
# print(LOG_PATH)
LOG_FILE_HANDLER_TYPE = 6  # 1 2 3 4 5 6
"""
LOG_FILE_HANDLER_TYPE 这个值可以设置为 1 2 3 4 5 四种值，
1为使用多进程安全按日志文件大小切割的文件日志,这是本人实现的批量写入日志，减少操作文件锁次数，测试10进程快速写入文件，win上性能比第5种提高了100倍，linux提升5倍
2为多进程安全按天自动切割的文件日志，同一个文件，每天生成一个新的日志文件。日志文件名字后缀自动加上日期。
3为不自动切割的单个文件的日志(不切割文件就不会出现所谓进程安不安全的问题) 
4为 WatchedFileHandler，这个是需要在linux下才能使用，需要借助lograte外力进行日志文件的切割，多进程安全。
5 为第三方的concurrent_log_handler.ConcurrentRotatingFileHandler按日志文件大小切割的文件日志，
   这个是采用了文件锁，多进程安全切割，文件锁在linux上使用fcntl性能还行，win上使用win32con性能非常惨。按大小切割建议不要选第5个个filehandler而是选择第1个。
"""

LOG_LEVEL_FILTER = logging.DEBUG  # 默认日志级别，低于此级别的日志不记录了。例如设置为INFO，那么logger.debug的不会记录，只会记录logger.info以上级别的。
FILTER_WORDS_PRINT = ["测试过滤字符串的呀", "阿弥陀佛", "善哉善哉"]


RUN_ENV = 'test'

FORMATTER_DICT = {
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
    7: logging.Formatter('%(asctime)s - %(name)s - "%(filename)s:%(lineno)d" - %(levelname)s - %(message)s', "%Y-%m-%d %H:%M:%S"),  # 一个只显示简短文件名和所处行数的日志模板

    8: JsonFormatterJumpAble('%(asctime)s %(name)s  %(levelname)s %(message)s  %(pathname)s %(lineno)d %(funcName)s %(process)d %(thread)d', "%Y-%m-%d %H:%M:%S", json_ensure_ascii=False,json_default=_json_translate),  # 这个是json日志，方便分析.

    9: logging.Formatter(
        '[p%(process)d_t%(thread)d] %(asctime)s - %(name)s - "%(pathname)s:%(lineno)d" - %(funcName)s - %(levelname)s - %(message)s',
        "%Y-%m-%d %H:%M:%S"),  # 对5改进，带进程和线程显示的日志模板。
    10: logging.Formatter(
        '[p%(process)d_t%(thread)d] %(asctime)s - %(name)s - "%(filename)s:%(lineno)d" - %(levelname)s - %(message)s', "%Y-%m-%d %H:%M:%S"),  # 对7改进，带进程和线程显示的日志模板。
    11: logging.Formatter(
        f'({computer_ip},{computer_name})-[p%(process)d_t%(thread)d] %(asctime)s - %(name)s - "%(filename)s:%(lineno)d" - %(levelname)s - %(message)s', "%Y-%m-%d %H:%M:%S"),  # 对7改进，带进程和线程显示的日志模板以及ip和主机名。
}

FORMATTER_KIND = 5  # 如果get_logger不指定日志模板，则默认选择第几个模板









