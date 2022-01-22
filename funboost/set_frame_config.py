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
import json
from pathlib import Path
from shutil import copyfile
from nb_log import nb_print, stderr_write, stdout_write
from nb_log.monkey_print import is_main_process, only_print_on_main_process
from funboost import funboost_config_deafult


def dict2json(dictx: dict, indent=4):
    dict_new = {}
    for k, v in dictx.items():
        # only_print_on_main_process(f'{k} :  {v}')
        if isinstance(v, (bool, tuple, dict, float, int)):
            dict_new[k] = v
        else:
            dict_new[k] = str(v)
    return json.dumps(dict_new, ensure_ascii=False, indent=indent)


# noinspection PyPep8Naming
# 这是手动调用函数设置配置，框架会自动调用use_config_form_funboost_config_module读当前取项目根目录下的funboost_config.py，不需要嗲用这里
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

                       SQLACHEMY_ENGINE_URL='sqlite:////sqlachemy_queues/queues.db',

                       **other_configs,  # 其他入参可以是其他中间件的配置名字，例如 MQTT_HOST

                       ):
    """
    对框架的配置使用猴子补丁的方式进行更改。利用了模块天然是单利的特性。格式参考frame_config.py
    :return:
    """
    kw = copy.copy(locals())
    kw.update(kw['other_configs'])
    kw.pop('other_configs')
    for var_name, var_value in kw.items():
        if var_value is not None:
            setattr(funboost_config_deafult, var_name, var_value)
    nb_print('使用patch_frame_config 函数设置框架配置了。')
    show_frame_config()


def show_frame_config():
    only_print_on_main_process('显示当前的项目中间件配置参数')
    for var_name in dir(funboost_config_deafult):
        if var_name.isupper():
            var_value = getattr(funboost_config_deafult, var_name)
            if var_name == 'MONGO_CONNECT_URL':
                if re.match('mongodb://.*?:.*?@.*?/.*', var_value):
                    mongo_pass = re.search('mongodb://.*?:(.*?)@', var_value).group(1)
                    mongo_pass_encryption = f'{"*" * (len(mongo_pass) - 2)}{mongo_pass[-1]}' if len(
                        mongo_pass) > 3 else mongo_pass
                    var_value_encryption = re.sub(r':(\w+)@', f':{mongo_pass_encryption}@', var_value)
                    only_print_on_main_process(f'{var_name}:             {var_value_encryption}')
                    continue
            if 'PASS' in var_name and var_value is not None and len(var_value) > 3:  # 对密码打*
                only_print_on_main_process(f'{var_name}:                {var_value[0]}{"*" * (len(var_value) - 2)}{var_value[-1]}')
            else:
                only_print_on_main_process(f'{var_name}:                {var_value}')

    only_print_on_main_process(f'读取的 BoostDecoratorDefaultParams 默认 @boost 装饰器入参的默认全局配置是： \n  '
                               f'{dict2json(funboost_config_deafult.BoostDecoratorDefaultParams().get_dict())}')


def use_config_form_funboost_config_module():
    """
    自动读取配置。会优先读取启动脚本的目录的funboost_config.py文件。没有则读取项目根目录下的funboost_config.py
    :return:
    """
    current_script_path = sys.path[0].replace('\\', '/')
    project_root_path = sys.path[1].replace('\\', '/')
    inspect_msg = f"""
    分布式函数调度框架会自动导入funboost_config模块
    当第一次运行脚本时候，函数调度框架会在你的python当前项目的根目录下 {project_root_path} 下，创建一个名为 funboost_config.py 的文件。
    自动读取配置，会优先读取启动脚本的所在目录 {current_script_path} 的funboost_config.py文件，
    如果没有 {current_script_path}/funboost_config.py 文件，则读取项目根目录 {project_root_path} 下的funboost_config.py做配置。
    在 "{project_root_path}/funboost_config.py:1" 文件中，需要按需重新设置要使用到的中间件的键和值，例如没有使用rabbitmq而是使用redis做中间件，则不需要配置rabbitmq。
    """
    # sys.stdout.write(f'\033[0;33m{time.strftime("%H:%M:%S")}\033[0m  "{__file__}:{sys._getframe().f_lineno}"   \033[0;30;43m{inspect_msg}\033[0m\n')
    # noinspection PyProtectedMember
    if is_main_process():
        stdout_write(f'\033[0;93m{time.strftime("%H:%M:%S")}\033[0m  "{__file__}:{sys._getframe().f_lineno}"   \033[0;93;100m{inspect_msg}\033[0m\n')
    try:
        # noinspection PyUnresolvedReferences
        # import funboost_config
        m = importlib.import_module('funboost_config')
        importlib.reload(m)  # 这行是防止用户在导入框架之前，写了 from funboost_config import REDIS_HOST 这种，导致 m.__dict__.items() 不包括所有配置变量了。
        # print(dir(m))
        # nb_print(m.__dict__.items())
        only_print_on_main_process(f'分布式函数调度框架 读取到\n "{m.__file__}:1" 文件里面的变量作为优先配置了\n')
        for var_namex, var_valuex in m.__dict__.items():
            # print(m, var_namex, var_valuex)
            if var_namex.isupper():
                setattr(funboost_config_deafult, var_namex, var_valuex)  # 用用户自定义的配置覆盖框架的默认配置。
            if var_namex == 'BoostDecoratorDefaultParams':
                for k, v in var_valuex().get_dict().items():
                    setattr(funboost_config_deafult.BoostDecoratorDefaultParams, k, v)

    except ModuleNotFoundError:
        nb_print(
            f'''分布式函数调度框架检测到 你的项目根目录 {project_root_path} 和当前文件夹 {current_script_path}  下没有 funboost_config.py 文件，\n''')
        auto_creat_config_file_to_project_root_path()
    else:
        show_frame_config()
        # print(getattr(m,'BoostDecoratorDefaultParams')().get_dict())


def auto_creat_config_file_to_project_root_path():
    """
    在没有使用pycahrm运行代码时候，如果实在cmd 或者 linux 运行， python xx.py，
    请在临时会话窗口设置linux export PYTHONPATH=你的项目根目录 ，winwdos set PYTHONPATH=你的项目根目录
    :return:
    """
    # print(Path(sys.path[1]).as_posix())
    # print((Path(__file__).parent.parent).absolute().as_posix())
    # if Path(sys.path[1]).as_posix() in Path(__file__).parent.parent.absolute().as_posix():
    #     nb_print('不希望在本项目里面创建')
    #     return
    if '/lib/python' in sys.path[1] or r'\lib\python' in sys.path[1] or '.zip' in sys.path[1]:
        raise EnvironmentError(f'''如果是cmd 或者shell启动而不是pycharm 这种ide启动脚本，请先在会话窗口设置临时PYTHONPATH为你的项目路径，
                               windwos 使用 set PYTHONNPATH=你的当前python项目根目录,
                               linux 使用 export PYTHONPATH=你的当前你python项目根目录,
                               PYTHONPATH 作用是python的基本常识，请百度一下。
                               需要在会话窗口命令行设置临时的环境变量，而不是修改linux配置文件的方式设置永久环境变量，每个python项目的PYTHONPATH都要不一样，不要在配置文件写死
                               
                               懂PYTHONPATH 的重要性和妙用见： https://github.com/ydf0509/pythonpathdemo
                               ''')
        return  # 当没设置pythonpath时候，也不要在 /lib/python36.zip这样的地方创建配置文件。

    file_name = Path(sys.path[1]) / Path('funboost_config.py')
    copyfile(Path(__file__).absolute().parent / Path('funboost_config_deafult.py'), file_name)
    nb_print(f'在  {Path(sys.path[1])} 目录下自动生成了一个文件， 请查看或修改 \n "{file_name}:1" 文件')
    # with (file_name).open(mode='w', encoding='utf8') as f:
    #     nb_print(f'在 {file_name} 目录下自动生成了一个文件， 请查看或修改 \n "{file_name}:1" 文件')
    #     f.write(config_file_content)


use_config_form_funboost_config_module()
