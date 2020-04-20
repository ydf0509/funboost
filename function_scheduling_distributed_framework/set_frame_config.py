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
from function_scheduling_distributed_framework import frame_config


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
    sys.stdout.write(
        f'\033[0;34m{time.strftime("%H:%M:%S")}\033[0m  "{file_name}:{line}"   \033[0;30;44m{"".join(args)}\033[0m\n')  # 36  93 96 94


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
# REDIS_PASSWORD = 'redis_password' 
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
'''


def use_config_form_distributed_frame_config_module():
    """
    自动读取配置。会优先读取启动脚本的目录的distributed_frame_config.py文件。没有则读取项目根目录下的distributed_frame_config.py
    :return:
    """
    current_script_path = sys.path[0].replace('\\', '/')
    project_root_path = sys.path[1].replace('\\', '/')
    inspect_msg = f"""
    分布式函数调度框架，设置配置有两种方式。两种方式的目的相同，就是使用猴子补丁的方式修改此框架的frame_config模中块的变量。
    
    1)第一种方式，自动读取配置文件方式
    分布式函数调度框架会尝试自动导入distributed_frame_config模块
    请在你的python当前项目的根目录下 {project_root_path} 或 当前文件夹 {current_script_path} 文件夹下，创建一个名为 distributed_frame_config.py 的文件，并在文件中定义例子里面的python常量。
    自动读取配置，会优先读取启动脚本的所在目录 {current_script_path} 的distributed_frame_config.py文件，
    如果没有 {current_script_path}/distributed_frame_config.py 文件，则读取项目根目录 {project_root_path} 下的distributed_frame_config.py做配置。
    内容例子如下，distributed_frame_config模块需要按需必须包含以下变量，需要按需重新设置要使用到的中间件的键和值，例如没有使用rabbitmq而是使用redis做中间件，则不需要配置rabbitmq。
    
    
    \033[0;97;40m
    MONGO_CONNECT_URL = f'mongodb://yourname:yourpassword@127.0.01:27017/admin'
    
    RABBITMQ_USER = 'rabbitmq_user'
    RABBITMQ_PASS = 'rabbitmq_pass'
    RABBITMQ_HOST = '127.0.0.1'
    RABBITMQ_PORT = 5672
    RABBITMQ_VIRTUAL_HOST = 'rabbitmq_virtual_host'
    
    REDIS_HOST = '127.0.0.1'
    REDIS_PASSWORD = 'redis_password' 
    REDIS_PORT = 6379
    REDIS_DB = 7
    
    NSQD_TCP_ADDRESSES = ['127.0.0.1:4150']
    NSQD_HTTP_CLIENT_HOST = '127.0.0.1'
    NSQD_HTTP_CLIENT_PORT = 4151
    
    KAFKA_BOOTSTRAP_SERVERS = ['127.0.0.1:9092']
    
    SQLACHEMY_ENGINE_URL ='sqlite:////sqlachemy_queues/queues.db'
    
    \033[0m
    
    \033[0;93;100m
    2)第二种方式,手动调用猴子补丁函数的方式
    如果你没有在python当前项目的根目录下 {project_root_path} 或 当前文件夹 {current_script_path} 文件夹下建立 distributed_frame_config.py 这个文件，
    也可以使用第二种配置方式，调用 patch_frame_config 函数进行框架配置设置
    \033[0m
    
    \033[0;97;40m
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

    show_frame_config()
    \033[0m
    
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
            f'''分布式函数调度框架检测到 你的项目根目录 {project_root_path} 和当前文件夹 {current_script_path}  下没有 distributed_frame_config.py 文件，
                 无法使用第一种方式做配置。
                 请你务必使用第二种方式，调用 patch_frame_config 函数打猴子补丁进行框架的配置进行设置，
                 patch_frame_config 函数要放在生成消费者 发布者之前运行\n\n''')
        auto_creat_config_file_to_project_root_path()
        nb_print(f'在 {project_root_path} 目录下自动生成了一个文件， 请查看或修改 \n "{project_root_path}/distributed_frame_config.py:1" 文件')

    show_frame_config()


def auto_creat_config_file_to_project_root_path():
    # print(Path(sys.path[1]).as_posix())
    # print((Path(__file__).parent.parent).absolute().as_posix())
    if Path(sys.path[1]).as_posix() in Path(__file__).parent.parent.absolute().as_posix():
        nb_print('不希望在本项目里面创建')
        return
    with (Path(sys.path[1]) / Path('distributed_frame_config.py')).open(mode='w', encoding='utf8') as f:
        f.write(config_file_content)


use_config_form_distributed_frame_config_module()
