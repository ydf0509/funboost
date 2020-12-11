# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2020/4/11 0011 0:56
"""

使用覆盖的方式，做配置。
"""
import copy
import sys
import time
import re
import importlib
from pathlib import Path
from nb_log import nb_print
from function_scheduling_distributed_framework import frame_config




# noinspection PyPep8Naming
def patch_frame_config(MONGO_CONNECT_URL: str = None,

                       RABBITMQ_USER: str = None,
                       RABBITMQ_PASS: str = None,
                       RABBITMQ_HOST: str = None,
                       RABBITMQ_PORT: int = None,
                       RABBITMQ_VIRTUAL_HOST: str = None,

                       REDIS_HOST: str = None,
                       REDIS_PASSWORD: str = None,
                       REDIS_PORT: int = None,
                       REDIS_DB: int = None,

                       NSQD_TCP_ADDRESSES: list = None,
                       NSQD_HTTP_CLIENT_HOST: str = None,
                       NSQD_HTTP_CLIENT_PORT: int = None,
                       KAFKA_BOOTSTRAP_SERVERS: list = None,

                       SQLACHEMY_ENGINE_URL='sqlite:////sqlachemy_queues/queues.db'

                       ):
    """
    对框架的配置使用猴子补丁的方式进行更改。利用了模块天然是单利的特性。格式参考frame_config.py
    :return:
    """
    kw = copy.copy(locals())
    for var_name, var_value in kw.items():
        if var_value is not None:
            setattr(frame_config, var_name, var_value)
    nb_print('使用patch_frame_config 函数设置框架配置了。')
    show_frame_config()


def show_frame_config():
    nb_print('显示当前的项目中间件配置参数')
    for var_name in dir(frame_config):
        if var_name.isupper():
            var_value = getattr(frame_config, var_name)
            if var_name == 'MONGO_CONNECT_URL':
                if re.match('mongodb://.*?:.*?@.*?/.*', var_value):
                    mongo_pass = re.search('mongodb://.*?:(.*?)@', var_value).group(1)
                    mongo_pass_encryption = f'{"*" * (len(mongo_pass) - 2)}{mongo_pass[-1]}' if len(
                        mongo_pass) > 3 else mongo_pass
                    var_value_encryption = re.sub(r':(\w+)@', f':{mongo_pass_encryption}@', var_value)
                    nb_print(f'{var_name}:             {var_value_encryption}')
                    continue
            if 'PASS' in var_name and var_value is not None and len(var_value) > 3:  # 对密码打*
                nb_print(f'{var_name}:                {var_value[0]}{"*" * (len(var_value) - 2)}{var_value[-1]}')
            else:
                nb_print(f'{var_name}:                {var_value}')
    print('\n')


config_file_content = '''# -*- coding: utf-8 -*-
"""
1.1） 此py配置文件的内容是可以不拘于形式的，例如在此文件里面可以根据环境写if else 判断，或者写其他python代码，里面写各种函数和变量都可以的。但模块必须按需包括以下名字的变量，
例如 如果不使用rabbitmq作为中间件，只使用redis做中间件，则此模块可以没有RABBITMQ_USER RABBITMQ_PASS MOOGO KAFKA sql数据库等这些变量，只需要redis相关的变量就可以。

1.2）如果你的py启动脚本是项目的深层目录下，你也可以在那个启动目录下，放入这个文件，
框架会优先读取启动脚本所在目录的distributed_frame_config.py作为配置，
如果启动脚本所在目录下无distributed_frame_config.py文件，则会使用项目根目录下的distributed_frame_config.py做配置。

2）也可以使用 patch_frame_config函数进行配置的覆盖和指定。
用法为：

from function_scheduling_distributed_framework import patch_frame_config, show_frame_config
# 初次接触使用，可以不安装任何中间件，使用本地持久化队列。正式墙裂推荐安装rabbitmq。
# 使用打猴子补丁的方式修改框架配置。这里为了演示，列举了所有中间件的参数，
# 实际是只需要对使用到的中间件的配置进行赋值即可。
patch_frame_config(MONGO_CONNECT_URL='mongodb://myUserAdminxx:xxxx@xx.90.89.xx:27016/admin',

                   RABBITMQ_USER='silxxxx',
                   RABBITMQ_PASS='Fr3Mxxxxx',
                   RABBITMQ_HOST='1xx.90.89.xx',
                   RABBITMQ_PORT=5672,
                   RABBITMQ_VIRTUAL_HOST='test_host',

                   REDIS_HOST='1xx.90.89.xx',
                   REDIS_PASSWORD='yxxxxxxR',
                   REDIS_PORT=6543,
                   REDIS_DB=7,

                   NSQD_TCP_ADDRESSES=['xx.112.34.56:4150'],
                   NSQD_HTTP_CLIENT_HOST='12.34.56.78',
                   NSQD_HTTP_CLIENT_PORT=4151,

                   KAFKA_BOOTSTRAP_SERVERS=['12.34.56.78:9092'],
                   
                   SQLACHEMY_ENGINE_URL = 'mysql+pymysql://root:123456@127.0.0.1:3306/sqlachemy_queues?charset=utf8',
                   )

"""



# 以下为配置，请您按需修改。

# MONGO_CONNECT_URL = f'mongodb://yourname:yourpassword@127.0.01:27017/admin'
# 
# RABBITMQ_USER = 'rabbitmq_user'
# RABBITMQ_PASS = 'rabbitmq_pass'
# RABBITMQ_HOST = '127.0.0.1'
# RABBITMQ_PORT = 5672
# RABBITMQ_VIRTUAL_HOST = 'rabbitmq_virtual_host'
# 
# REDIS_HOST = '127.0.0.1'
# REDIS_PASSWORD = '' 
# REDIS_PORT = 6379
# REDIS_DB = 7
# 
# NSQD_TCP_ADDRESSES = ['127.0.0.1:4150']
# NSQD_HTTP_CLIENT_HOST = '127.0.0.1'
# NSQD_HTTP_CLIENT_PORT = 4151
# 
# KAFKA_BOOTSTRAP_SERVERS = ['127.0.0.1:9092']
# 
# SQLACHEMY_ENGINE_URL ='sqlite:////sqlachemy_queues/queues.db'

# ROCKETMQ_NAMESRV_ADDR = '192.168.199.202:9876'

# nb_log包的第几个日志模板，内置了7个模板，可以在你当前项目根目录下的nb_log_config.py文件扩展模板。第5个模板可以点击跳转到框架内部，但有点占控制台面积，第7个模板简单不可点击跳转到框架内部。
# NB_LOG_FORMATER_INDEX_FOR_CONSUMER_AND_PUBLISHER = 7     
# FSDF_DEVELOP_LOG_LEVEL = 50   # 开发时候的日志，进攻自己用，所以日志级别跳到最高

# TIMEZONE = 'Asia/Shanghai'          
'''


def use_config_form_distributed_frame_config_module():
    """
    自动读取配置。会优先读取启动脚本的目录的distributed_frame_config.py文件。没有则读取项目根目录下的distributed_frame_config.py
    :return:
    """
    current_script_path = sys.path[0].replace('\\', '/')
    project_root_path = sys.path[1].replace('\\', '/')
    inspect_msg = f"""
    分布式函数调度框架会自动导入distributed_frame_config模块
    当第一次运行脚本时候，函数调度框架会在你的python当前项目的根目录下 {project_root_path} 下，创建一个名为 distributed_frame_config.py 的文件。
    自动读取配置，会优先读取启动脚本的所在目录 {current_script_path} 的distributed_frame_config.py文件，
    如果没有 {current_script_path}/distributed_frame_config.py 文件，则读取项目根目录 {project_root_path} 下的distributed_frame_config.py做配置。
    在 "{project_root_path}/distributed_frame_config.py:1" 文件中，需要按需重新设置要使用到的中间件的键和值，例如没有使用rabbitmq而是使用redis做中间件，则不需要配置rabbitmq。
    """
    # sys.stdout.write(f'\033[0;33m{time.strftime("%H:%M:%S")}\033[0m  "{__file__}:{sys._getframe().f_lineno}"   \033[0;30;43m{inspect_msg}\033[0m\n')
    # noinspection PyProtectedMember
    sys.stdout.write(
        f'\033[0;93m{time.strftime("%H:%M:%S")}\033[0m  "{__file__}:{sys._getframe().f_lineno}"   \033[0;93;100m{inspect_msg}\033[0m\n')

    try:
        # noinspection PyUnresolvedReferences
        # import distributed_frame_config
        m = importlib.import_module('distributed_frame_config')
        # nb_print(m.__dict__)
        nb_print(f'分布式函数调度框架 读取到\n "{m.__file__}:1" 文件里面的变量作为配置了\n')
        for var_namex, var_valuex in m.__dict__.items():
            if var_namex.isupper():
                setattr(frame_config, var_namex, var_valuex)
    except ModuleNotFoundError:
        nb_print(
            f'''分布式函数调度框架检测到 你的项目根目录 {project_root_path} 和当前文件夹 {current_script_path}  下没有 distributed_frame_config.py 文件，\n\n''')
        auto_creat_config_file_to_project_root_path()
        nb_print(f'在 {project_root_path} 目录下自动生成了一个文件， 请查看或修改 \n "{project_root_path}/distributed_frame_config.py:1" 文件')

    show_frame_config()


def auto_creat_config_file_to_project_root_path():
    # print(Path(sys.path[1]).as_posix())
    # print((Path(__file__).parent.parent).absolute().as_posix())
    if Path(sys.path[1]).as_posix() in Path(__file__).parent.parent.absolute().as_posix():
        nb_print('不希望在本项目里面创建')
        return
    if '/lib/python' in sys.path[1] or r'\lib\python' in sys.path[1] or '.zip' in sys.path[1]:
        return  # 当没设置pythonpath时候，也不要在 /lib/python36.zip这样的地方创建配置文件。
    with (Path(sys.path[1]) / Path('distributed_frame_config.py')).open(mode='w', encoding='utf8') as f:
        f.write(config_file_content)


use_config_form_distributed_frame_config_module()
