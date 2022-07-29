import sys
import re
from multiprocessing import Process
import threading
import time
from typing import List
from concurrent.futures import ProcessPoolExecutor

from nb_log import LoggerMixin

import nb_log
from fabric2 import Connection

from funboost.utils.paramiko_util import ParamikoFolderUploader

logger = nb_log.get_logger('funboost')


def _run_many_consumer_by_init_params(consumer_init_params_list: List[dict]):
    from funboost import get_consumer, ConsumersManager
    for consumer_init_params in consumer_init_params_list:
        get_consumer(**consumer_init_params).start_consuming_message()
    ConsumersManager.join_all_consumer_shedual_task_thread()


def run_consumer_with_multi_process(task_fun, process_num=1):
    """
    :param task_fun:被 boost 装饰器装饰的消费函数
    :param process_num:开启多个进程。  主要是 多进程并发  + 4种细粒度并发(threading gevent eventlet asyncio)。叠加并发。
    这种是多进程方式，一次编写能够兼容win和linux的运行。一次性启动6个进程 叠加 多线程 并发。
    """
    '''
       from funboost import boost, BrokerEnum, ConcurrentModeEnum, run_consumer_with_multi_process
       import os

       @boost('test_multi_process_queue',broker_kind=BrokerEnum.REDIS_ACK_ABLE,concurrent_mode=ConcurrentModeEnum.THREADING,)
       def fff(x):
           print(x * 10,os.getpid())

       if __name__ == '__main__':
           # fff.consume()
           run_consumer_with_multi_process(fff,6) # 一次性启动6个进程 叠加 多线程 并发。
           fff.multi_process_conusme(6)    # 这也是一次性启动6个进程 叠加 多线程 并发。
    '''
    if not getattr(task_fun, 'is_decorated_as_consume_function'):
        raise ValueError(f'{task_fun} 参数必须是一个被 boost 装饰的函数')
    if process_num == 1 :
        task_fun.consume()
    else:
        for i in range(process_num):
            # print(i)
            Process(target=_run_many_consumer_by_init_params,
                     args=([{**{'consuming_function': task_fun}, **task_fun.init_params}],)).start()


def _multi_process_pub_params_list_by_consumer_init_params(consumer_init_params: dict, msgs: List[dict]):
    from funboost import get_consumer
    consumer = get_consumer(**consumer_init_params)
    publisher = consumer.publisher_of_same_queue
    publisher.set_log_level(20)  # 超高速发布，如果打印详细debug日志会卡死屏幕和严重降低代码速度。
    for msg in msgs:
        publisher.publish(msg)


def multi_process_pub_params_list(task_fun, params_list, process_num=16):
    """超高速多进程发布任务，充分利用多核"""
    if not getattr(task_fun, 'is_decorated_as_consume_function'):
        raise ValueError(f'{task_fun} 参数必须是一个被 boost 装饰的函数')
    params_list_len = len(params_list)
    if params_list_len < 1000 * 100:
        raise ValueError(f'要要发布的任务数量是 {params_list_len} 个,要求必须至少发布10万任务才使用此方法')
    ava_len = params_list_len // process_num + 1
    with ProcessPoolExecutor(process_num) as pool:
        t0 = time.time()
        for i in range(process_num):
            msgs = params_list[i * ava_len: (i + 1) * ava_len]
            # print(msgs)
            pool.submit(_multi_process_pub_params_list_by_consumer_init_params,
                        {**{'consuming_function': task_fun}, **task_fun.init_params}, msgs)
    logger.info(f'\n 通过 multi_process_pub_params_list 多进程子进程的发布方式，发布了 {params_list_len} 个任务。耗时 {time.time() - t0} 秒')


# noinspection PyDefaultArgument
def fabric_deploy(task_fun, host, port, user, password,
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
    python3 -c "from test_frame.test_fabric_deploy.test_deploy1 import f2;f2.multi_process_consume(2)"  -fsdfmark fsdf_fabric_mark_queue_test30

    这个是可以直接在远程机器上运行函数任务。无需用户亲自部署代码和启动代码。自动上传代码，自动设置环境变量，自动导入函数，自动运行。
    这个原理是使用python -c 实现的精确到函数级别的部署，不是python脚本级别的部署。
    可以很灵活的指定在哪台机器运行什么函数，开几个进程。这个比celery更为强大，celery需要登录到每台机器，手动下载代码并部署在多台机器，celery不支持代码自动运行在别的机器上


    :param task_fun:被@boost 装饰的函数
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
    python_proj_dir = sys.path[1].replace('\\', '/') + '/'
    python_proj_dir_short = python_proj_dir.split('/')[-2]
    # 获取被调用函数所在模块文件名
    file_name = sys._getframe(1).f_code.co_filename.replace('\\', '/')  # noqa\
    relative_file_name = re.sub(f'^{python_proj_dir}', '', file_name)
    relative_module = relative_file_name.replace('/', '.')[:-3]  # -3是去掉.py
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

        func_name = task_fun.__name__
        queue_name = task_fun.consumer.queue_name

        process_mark = f'fsdf_fabric_mark__{queue_name}__{func_name}'
        conn = Connection(host, port=port, user=user, connect_kwargs={"password": password}, )
        kill_shell = f'''ps -aux|grep {process_mark}|grep -v grep|awk '{{print $2}}' |xargs kill -9'''
        logger.warning(f'{kill_shell} 命令杀死 {process_mark} 标识的进程')
        uploader.ssh.exec_command(kill_shell)
        # conn.run(kill_shell, encoding='utf-8',warn=True)  # 不想提示，免得烦扰用户以为有什么异常了。所以用上面的paramiko包的ssh.exec_command

        python_exec_str = f'''export is_fsdf_remote_run=1;export PYTHONPATH={remote_dir}:$PYTHONPATH ;{python_interpreter} -c "from {relative_module} import {func_name};{func_name}.multi_process_consume({process_num})"  -fsdfmark {process_mark} '''
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
    fsdf_fabric_mark_all = 'fsdf_fabric_mark__'
    kill_shell = f'''ps -aux|grep {fsdf_fabric_mark_all}|grep -v grep|awk '{{print $2}}' |xargs kill -9'''
    logger.warning(f'{kill_shell} 命令杀死 {fsdf_fabric_mark_all} 标识的进程')
    uploader.ssh.exec_command(kill_shell)
    logger.warning(f'杀死 {host}  机器所有的 {fsdf_fabric_mark_all} 标识的进程')


class FunctionResultStatusPersistanceConfig(LoggerMixin):
    def __init__(self, is_save_status: bool, is_save_result: bool, expire_seconds: int = 7 * 24 * 3600, is_use_bulk_insert=False):
        """
        :param is_save_status:
        :param is_save_result:
        :param expire_seconds: 设置统计的过期时间，在mongo里面自动会移除这些过期的执行记录。
        :param is_use_bulk_insert : 是否使用批量插入来保存结果，批量插入是每隔0.5秒钟保存一次最近0.5秒内的所有的函数消费状态结果，始终会出现最后0.5秒内的执行结果没及时插入mongo。为False则，每完成一次函数就实时写入一次到mongo。
        """

        if not is_save_status and is_save_result:
            raise ValueError(f'你设置的是不保存函数运行状态但保存函数运行结果。不允许你这么设置')
        self.is_save_status = is_save_status
        self.is_save_result = is_save_result
        if expire_seconds > 10 * 24 * 3600:
            self.logger.warning(f'你设置的过期时间为 {expire_seconds} ,设置的时间过长。 ')
        self.expire_seconds = expire_seconds
        self.is_use_bulk_insert = is_use_bulk_insert

    def to_dict(self):
        return {"is_save_status": self.is_save_status,
                'is_save_result': self.is_save_result, 'expire_seconds': self.expire_seconds}

    def __str__(self):
        return f'<FunctionResultStatusPersistanceConfig> {id(self)} {self.to_dict()}'
