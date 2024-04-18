# noinspection PyDefaultArgument
import re
import sys
import threading
import time
import os
import typing
from pathlib import Path
from fabric2 import Connection
from nb_libs.path_helper import PathHelper
# from funboost.core.booster import Booster
from funboost.utils.paramiko_util import ParamikoFolderUploader

# import nb_log
from funboost.core.loggers import get_funboost_file_logger
from funboost.core.booster import Booster

logger = get_funboost_file_logger(__name__)


# noinspection PyDefaultArgument



def fabric_deploy(booster: Booster, host, port, user, password,
                  path_pattern_exluded_tuple=('/.git/', '/.idea/', '/dist/', '/build/'),
                  file_suffix_tuple_exluded=('.pyc', '.log', '.gz'),
                  only_upload_within_the_last_modify_time=3650 * 24 * 60 * 60,
                  file_volume_limit=1000 * 1000, sftp_log_level=20, extra_shell_str='',
                  invoke_runner_kwargs={'hide': None, 'pty': True, 'warn': False},
                  python_interpreter='python3',
                  process_num=1):
    """
    不依赖阿里云codepipeline 和任何运维发布管理工具，只需要在python代码层面就能实现多机器远程部署。
    这实现了函数级别的精确部署，而非是部署一个 .py的代码，远程部署一个函数实现难度比远程部署一个脚本更高一点，部署更灵活。

    之前有人问怎么方便的部署在多台机器，一般用阿里云codepipeline  k8s自动部署。被部署的远程机器必须是linux，不能是windwos。
    但是有的人是直接操作多台物理机，有些不方便，现在直接加一个利用python代码本身实现的跨机器自动部署并运行函数任务。

    自动根据任务函数所在文件，转化成python模块路径，实现函数级别的精确部署，比脚本级别的部署更精确到函数。
    例如 test_frame/test_fabric_deploy/test_deploy1.py的fun2函数 自动转化成 from test_frame.test_fabric_deploy.test_deploy1 import f2
    从而自动生成部署语句
    export PYTHONPATH=/home/ydf/codes/distributed_framework:$PYTHONPATH ;cd /home/ydf/codes/distributed_framework;
    python3 -c "from test_frame.test_fabric_deploy.test_deploy1 import f2;f2.multi_process_consume(2)"  -funboostmark funboost_fabric_mark_queue_test30

    这个是可以直接在远程机器上运行函数任务。无需用户亲自部署代码和启动代码。自动上传代码，自动设置环境变量，自动导入函数，自动运行。
    这个原理是使用python -c 实现的精确到函数级别的部署，不是python脚本级别的部署。
    可以很灵活的指定在哪台机器运行什么函数，开几个进程。这个比celery更为强大，celery需要登录到每台机器，手动下载代码并部署在多台机器，celery不支持代码自动运行在别的机器上


    :param booster:被@boost 装饰的函数
    :param host: 需要部署的远程linux机器的 ip
    :param port:需要部署的远程linux机器的 port
    :param user: 需要部署的远程linux机器的用户名
    :param password:需要部署的远程linux机器的密码
    :param path_pattern_exluded_tuple:排除的文件夹或文件路径
    :param file_suffix_tuple_exluded:排除的后缀
    :param only_upload_within_the_last_modify_time:只上传多少秒以内的文件，如果完整运行上传过一次后，之后可以把值改小，避免每次全量上传。
    :param file_volume_limit:大于这个体积的不上传，因为python代码文件很少超过1M
    :param sftp_log_level: 文件上传日志级别  10为logging.DEBUG 20为logging.INFO  30 为logging.WARNING
    :param extra_shell_str :自动部署前额外执行的命令，例如可以设置环境变量什么的
    :param python_interpreter: python解释器路径，如果linux安装了多个python环境可以指定绝对路径。
    :param invoke_runner_kwargs : invoke包的runner.py 模块的 run()方法的所有一切入参,例子只写了几个入参，实际可以传入十几个入参，大家可以自己琢磨fabric包的run方法，按需传入。
                                 hide 是否隐藏远程机器的输出，值可以为 False不隐藏远程主机的输出  “out”为只隐藏远程机器的正常输出，“err”为只隐藏远程机器的错误输出，True，隐藏远程主机的一切输出
                                 pty 的意思是，远程机器的部署的代码进程是否随着当前脚本的结束而结束。如果为True，本机代码结束远程进程就会结束。如果为False，即使本机代码被关闭结束，远程机器还在运行代码。
                                 warn 的意思是如果远程机器控制台返回了异常码本机代码是否立即退出。warn为True这只是警告一下，warn为False,远程机器返回异常code码则本机代码直接终止退出。
    :param process_num:启动几个进程，要达到最大cpu性能就开启cpu核数个进程就可以了。每个进程内部都有任务函数本身指定的并发方式和并发数量，所以是多进程+线程/协程。
    :return:


    task_fun.fabric_deploy('192.168.6.133', 22, 'ydf', '123456', process_num=2) 只需要这样就可以自动部署在远程机器运行，无需任何额外操作。
    """
    # print(locals())
    python_proj_dir = Path(sys.path[1]).resolve().as_posix() + '/'
    python_proj_dir_short = python_proj_dir.split('/')[-2]
    # 获取被调用函数所在模块文件名
    file_name = Path(sys._getframe(2).f_code.co_filename).resolve().as_posix() # noqa
    relative_file_name = Path(file_name).relative_to(Path(python_proj_dir)).as_posix()
    relative_module = relative_file_name.replace('/', '.')[:-3]  # -3是去掉.py
    func_name = booster.consuming_function.__name__

    """以下这种是为了兼容 函数没有@boost,而是使用 boosterxx = BoostersManager.build_booster() 来创建的booster. 下面的 python_exec_str 中需要用到 func_name 
    也可以远程时候使用 BoostersManager.get_booster(queue_name),然后启动消费.  因为import模块后,就能启动了.
    """
    module_obj = PathHelper(sys._getframe(2).f_code.co_filename).import_as_module()  # noqa
    for var_name,var_value in module_obj.__dict__.items():
        if isinstance(var_value,Booster) and var_value.queue_name == booster.queue_name:
            func_name = var_name

    logger.debug([file_name, python_proj_dir, python_proj_dir_short,relative_module, func_name])
    # print(relative_module)
    if user == 'root':  # 文件夹会被自动创建，无需用户创建。
        remote_dir = f'/codes/{python_proj_dir_short}'
    else:
        remote_dir = f'/home/{user}/codes/{python_proj_dir_short}'

    def _inner():
        logger.warning(f'将本地文件夹代码 {python_proj_dir}  上传到远程 {host} 的 {remote_dir} 文件夹。')
        t_start = time.perf_counter()
        uploader = ParamikoFolderUploader(host, port, user, password, python_proj_dir, remote_dir,
                                          path_pattern_exluded_tuple, file_suffix_tuple_exluded,
                                          only_upload_within_the_last_modify_time, file_volume_limit, sftp_log_level)
        uploader.upload()
        logger.info(f'上传 本地文件夹代码 {python_proj_dir}  上传到远程 {host} 的 {remote_dir} 文件夹耗时 {round(time.perf_counter() - t_start, 3)} 秒')
        # conn.run(f'''export PYTHONPATH={remote_dir}:$PYTHONPATH''')

        queue_name = booster.consumer.queue_name
        process_mark = f'funboost_fabric_mark__{queue_name}__{func_name}'
        conn = Connection(host, port=port, user=user, connect_kwargs={"password": password}, )
        kill_shell = f'''ps -aux|grep {process_mark}|grep -v grep|awk '{{print $2}}' |xargs kill -9'''
        logger.warning(f'{kill_shell} 命令杀死 {process_mark} 标识的进程')
        # uploader.ssh.exec_command(kill_shell)
        conn.run(kill_shell, encoding='utf-8', warn=True)  # 不想提示，免得烦扰用户以为有什么异常了。所以用上面的paramiko包的ssh.exec_command

        python_exec_str = f'''export is_funboost_remote_run=1;export PYTHONPATH={remote_dir}:$PYTHONPATH ;{python_interpreter} -c "from {relative_module} import {func_name};{func_name}.multi_process_consume({process_num})"  -funboostmark {process_mark} '''
        shell_str = f'''cd {remote_dir}; {python_exec_str}'''
        extra_shell_str2 = extra_shell_str  # 内部函数对外部变量不能直接改。
        if not extra_shell_str2.endswith(';') and extra_shell_str != '':
            extra_shell_str2 += ';'
        shell_str = extra_shell_str2 + shell_str
        logger.warning(f'使用语句 {shell_str} 在远程机器 {host} 上启动任务消费')
        conn.run(shell_str, encoding='utf-8', **invoke_runner_kwargs)
        # uploader.ssh.exec_command(shell_str)

    threading.Thread(target=_inner).start()


def kill_all_remote_tasks(host, port, user, password):
    """ 这个要小心用，杀死所有的远程部署的任务,一般不需要使用到"""
    uploader = ParamikoFolderUploader(host, port, user, password, '', '')
    funboost_fabric_mark_all = 'funboost_fabric_mark__'
    kill_shell = f'''ps -aux|grep {funboost_fabric_mark_all}|grep -v grep|awk '{{print $2}}' |xargs kill -9'''
    logger.warning(f'{kill_shell} 命令杀死 {funboost_fabric_mark_all} 标识的进程')
    uploader.ssh.exec_command(kill_shell)
    logger.warning(f'杀死 {host}  机器所有的 {funboost_fabric_mark_all} 标识的进程')
