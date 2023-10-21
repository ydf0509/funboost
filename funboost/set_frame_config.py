# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/4/11 0011 0:56
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
from nb_log import nb_print, stderr_write, stdout_write,get_logger
from nb_log.monkey_print import is_main_process, only_print_on_main_process
from funboost import funboost_config_deafult


def show_funboost_flag():

    logger = get_logger('funboost.show_funboost_flag')

    funboost_flag_str = '''


    FFFFFFFFFFFFFFFFFFFFFF     UUUUUUUU     UUUUUUUU     NNNNNNNN        NNNNNNNN     BBBBBBBBBBBBBBBBB             OOOOOOOOO               OOOOOOOOO             SSSSSSSSSSSSSSS      TTTTTTTTTTTTTTTTTTTTTTT
    F::::::::::::::::::::F     U::::::U     U::::::U     N:::::::N       N::::::N     B::::::::::::::::B          OO:::::::::OO           OO:::::::::OO         SS:::::::::::::::S     T:::::::::::::::::::::T
    F::::::::::::::::::::F     U::::::U     U::::::U     N::::::::N      N::::::N     B::::::BBBBBB:::::B       OO:::::::::::::OO       OO:::::::::::::OO      S:::::SSSSSS::::::S     T:::::::::::::::::::::T
    FF::::::FFFFFFFFF::::F     UU:::::U     U:::::UU     N:::::::::N     N::::::N     BB:::::B     B:::::B     O:::::::OOO:::::::O     O:::::::OOO:::::::O     S:::::S     SSSSSSS     T:::::TT:::::::TT:::::T
      F:::::F       FFFFFF      U:::::U     U:::::U      N::::::::::N    N::::::N       B::::B     B:::::B     O::::::O   O::::::O     O::::::O   O::::::O     S:::::S                 TTTTTT  T:::::T  TTTTTT
      F:::::F                   U:::::D     D:::::U      N:::::::::::N   N::::::N       B::::B     B:::::B     O:::::O     O:::::O     O:::::O     O:::::O     S:::::S                         T:::::T        
      F::::::FFFFFFFFFF         U:::::D     D:::::U      N:::::::N::::N  N::::::N       B::::BBBBBB:::::B      O:::::O     O:::::O     O:::::O     O:::::O      S::::SSSS                      T:::::T        
      F:::::::::::::::F         U:::::D     D:::::U      N::::::N N::::N N::::::N       B:::::::::::::BB       O:::::O     O:::::O     O:::::O     O:::::O       SS::::::SSSSS                 T:::::T        
      F:::::::::::::::F         U:::::D     D:::::U      N::::::N  N::::N:::::::N       B::::BBBBBB:::::B      O:::::O     O:::::O     O:::::O     O:::::O         SSS::::::::SS               T:::::T        
      F::::::FFFFFFFFFF         U:::::D     D:::::U      N::::::N   N:::::::::::N       B::::B     B:::::B     O:::::O     O:::::O     O:::::O     O:::::O            SSSSSS::::S              T:::::T        
      F:::::F                   U:::::D     D:::::U      N::::::N    N::::::::::N       B::::B     B:::::B     O:::::O     O:::::O     O:::::O     O:::::O                 S:::::S             T:::::T        
      F:::::F                   U::::::U   U::::::U      N::::::N     N:::::::::N       B::::B     B:::::B     O::::::O   O::::::O     O::::::O   O::::::O                 S:::::S             T:::::T        
    FF:::::::FF                 U:::::::UUU:::::::U      N::::::N      N::::::::N     BB:::::BBBBBB::::::B     O:::::::OOO:::::::O     O:::::::OOO:::::::O     SSSSSSS     S:::::S           TT:::::::TT      
    F::::::::FF                  UU:::::::::::::UU       N::::::N       N:::::::N     B:::::::::::::::::B       OO:::::::::::::OO       OO:::::::::::::OO      S::::::SSSSSS:::::S           T:::::::::T      
    F::::::::FF                    UU:::::::::UU         N::::::N        N::::::N     B::::::::::::::::B          OO:::::::::OO           OO:::::::::OO        S:::::::::::::::SS            T:::::::::T      
    FFFFFFFFFFF                      UUUUUUUUU           NNNNNNNN         NNNNNNN     BBBBBBBBBBBBBBBBB             OOOOOOOOO               OOOOOOOOO           SSSSSSSSSSSSSSS              TTTTTTTTTTT      


    '''

    funboost_flag_str2 = r'''

          ___                  ___                    ___                                           ___                    ___                    ___                          
         /  /\                /__/\                  /__/\                  _____                  /  /\                  /  /\                  /  /\                   ___   
        /  /:/_               \  \:\                 \  \:\                /  /::\                /  /::\                /  /::\                /  /:/_                 /  /\  
       /  /:/ /\               \  \:\                 \  \:\              /  /:/\:\              /  /:/\:\              /  /:/\:\              /  /:/ /\               /  /:/  
      /  /:/ /:/           ___  \  \:\            _____\__\:\            /  /:/~/::\            /  /:/  \:\            /  /:/  \:\            /  /:/ /::\             /  /:/   
     /__/:/ /:/           /__/\  \__\:\          /__/::::::::\          /__/:/ /:/\:|          /__/:/ \__\:\          /__/:/ \__\:\          /__/:/ /:/\:\           /  /::\   
     \  \:\/:/            \  \:\ /  /:/          \  \:\~~\~~\/          \  \:\/:/~/:/          \  \:\ /  /:/          \  \:\ /  /:/          \  \:\/:/~/:/          /__/:/\:\  
      \  \::/              \  \:\  /:/            \  \:\  ~~~            \  \::/ /:/            \  \:\  /:/            \  \:\  /:/            \  \::/ /:/           \__\/  \:\ 
       \  \:\               \  \:\/:/              \  \:\                 \  \:\/:/              \  \:\/:/              \  \:\/:/              \__\/ /:/                 \  \:\
        \  \:\               \  \::/                \  \:\                 \  \::/                \  \::/                \  \::/                 /__/:/                   \__\/
         \__\/                \__\/                  \__\/                  \__\/                  \__\/                  \__\/                  \__\/                         



    '''

    logger.debug('\033[0m' + funboost_flag_str2 + '\033[0m')

    logger.info(f'''分布式函数调度框架funboost文档地址：  \033[0m https://funboost.readthedocs.io/zh/latest/ \033[0m ''')

show_funboost_flag()

def dict2json(dictx: dict, indent=4):
    dict_new = {}
    for k, v in dictx.items():
        # only_print_on_main_process(f'{k} :  {v}')
        if isinstance(v, (bool, tuple, dict, float, int)):
            dict_new[k] = v
        else:
            dict_new[k] = str(v)
    return json.dumps(dict_new, ensure_ascii=False, indent=indent)


def show_frame_config():
    only_print_on_main_process('显示当前的项目中间件配置参数')
    # for var_name in dir(funboost_config_deafult):
    #     if var_name.isupper():
    #         var_value = getattr(funboost_config_deafult, var_name)
    #         if var_name == 'MONGO_CONNECT_URL':
    #             if re.match('mongodb://.*?:.*?@.*?/.*', var_value):
    #                 mongo_pass = re.search('mongodb://.*?:(.*?)@', var_value).group(1)
    #                 mongo_pass_encryption = f'{"*" * (len(mongo_pass) - 2)}{mongo_pass[-1]}' if len(
    #                     mongo_pass) > 3 else mongo_pass
    #                 var_value_encryption = re.sub(r':(\w+)@', f':{mongo_pass_encryption}@', var_value)
    #                 only_print_on_main_process(f'{var_name}:             {var_value_encryption}')
    #                 continue
    #         if 'PASS' in var_name and var_value is not None and len(var_value) > 3:  # 对密码打*
    #             only_print_on_main_process(f'{var_name}:                {var_value[0]}{"*" * (len(var_value) - 2)}{var_value[-1]}')
    #         else:
    #             only_print_on_main_process(f'{var_name}:                {var_value}')
    only_print_on_main_process(f'''读取的 BrokerConnConfig 配置是: 
    {funboost_config_deafult.BrokerConnConfig().get_json()}
    ''')

    only_print_on_main_process(f'''读取的 FunboostCommonConfig 配置是: 
        {funboost_config_deafult.FunboostCommonConfig().get_json()}
        ''')

    only_print_on_main_process(f'读取的 BoostDecoratorDefaultParams 默认 @boost 装饰器入参的默认全局配置是： \n  '
                               f'{funboost_config_deafult.BoostDecoratorDefaultParams().get_json()}')


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
        if not hasattr(m,'BrokerConnConfig'):
            raise EnvironmentError('funboost 30.0版本升级了配置文件，中间件配置写成了类，请删除原来老的配置文件')
        funboost_config_deafult.BrokerConnConfig.update_cls_attribute(**m.BrokerConnConfig().get_dict())
        funboost_config_deafult.FunboostCommonConfig.update_cls_attribute(**m.FunboostCommonConfig().get_dict())
        funboost_config_deafult.BoostDecoratorDefaultParams.update_cls_attribute(**m.BoostDecoratorDefaultParams().get_dict())


    except ModuleNotFoundError:
        nb_print(
            f'''分布式函数调度框架检测到 你的项目根目录 {project_root_path} 和当前文件夹 {current_script_path}  下没有 funboost_config.py 文件，\n''')
        _auto_creat_config_file_to_project_root_path()
    else:
        show_frame_config()
        # print(getattr(m,'BoostDecoratorDefaultParams')().get_dict())


def _auto_creat_config_file_to_project_root_path():
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
    nb_print(f'在  {Path(sys.path[1])} 目录下自动生成了一个文件， 请刷新文件夹查看或修改 \n "{file_name}:1" 文件')
    # with (file_name).open(mode='w', encoding='utf8') as f:
    #     nb_print(f'在 {file_name} 目录下自动生成了一个文件， 请查看或修改 \n "{file_name}:1" 文件')
    #     f.write(config_file_content)

    file_name = Path(sys.path[1]) / Path('funboost_cli_user.py')
    copyfile(Path(__file__).absolute().parent / Path('core/cli/funboost_cli_user_templ.py'), file_name)


use_config_form_funboost_config_module()
