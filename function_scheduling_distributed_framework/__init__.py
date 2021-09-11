import re
import sys
import threading
import time
from functools import update_wrapper, wraps, partial
from multiprocessing import Process
from typing import List
import copy
# noinspection PyUnresolvedReferences
import nb_log
from fabric2 import Connection
from function_scheduling_distributed_framework.utils.paramiko_util import ParamikoFolderUploader

from function_scheduling_distributed_framework.set_frame_config import patch_frame_config, show_frame_config
# import frame_config
from function_scheduling_distributed_framework.consumers.base_consumer import ExceptionForRequeue, ExceptionForRetry, \
    AbstractConsumer, ConsumersManager, FunctionResultStatusPersistanceConfig
from function_scheduling_distributed_framework.publishers.base_publisher import PriorityConsumingControlConfig, AbstractPublisher
from function_scheduling_distributed_framework.factories.publisher_factotry import get_publisher
from function_scheduling_distributed_framework.factories.consumer_factory import get_consumer

# noinspection PyUnresolvedReferences
from function_scheduling_distributed_framework.utils import nb_print, patch_print, LogManager, get_logger, LoggerMixin
from function_scheduling_distributed_framework.timing_job import fsdf_background_scheduler, timing_publish_deco
from function_scheduling_distributed_framework.constant import BrokerEnum, ConcurrentModeEnum

# 有的包默认没加handlers，原始的日志不漂亮且不可跳转不知道哪里发生的。这里把warnning级别以上的日志默认加上handlers。
nb_log.get_logger(name=None, log_level_int=30, log_filename='pywarning.log')

logger = nb_log.get_logger('function_scheduling_distributed_framework')


class IdeAutoCompleteHelper(LoggerMixin):
    """
    为了被装饰的消费函数的敲代码时候的被pycharm自动补全而写的类。
    """

    def __init__(self, consuming_func_decorated: callable):
        """
        :param consuming_func_decorated:   传入被task_deco装饰的函数

        此框架非常非常注重，公有函数、方法、类 的名字和入参在ide开发环境下面的自动提示补全效果，如果不是为了这一点，框架能减少很多重复地方。
        此类是防止用户调用打错字母或者不知道怎么敲代码不知道有哪些入参。所以才有这个类。

        这个类是个补全类，能够使pycharm自动补全方法名字和入参。可以用，可以不用，用了后在pycharm里面补全效果会起作用。


       from function_scheduling_distributed_framework import task_deco, IdeAutoCompleteHelper

       @task_deco('queue_test_f01', qps=2, broker_kind=3)
       def f(a, b):
           print(f'{a} + {b} = {a + b}')


       if __name__ == '__main__':
           f(1000, 2000)
           IdeAutoCompleteHelper(f).clear()  # f.clear()
           for i in range(100, 200):
               f.pub(dict(a=i, b=i * 2))  # f.sub方法是强行用元编程加到f上去的，是运行时状态，pycharm只能补全非运行时态的静态东西。
               IdeAutoCompleteHelper(f).pub({'a': i * 3, 'b': i * 4})  # 和上面的发布等效，但可以自动补全方法名字和入参。
               f.push(a=i, b=i * 2)
               IdeAutoCompleteHelper(f).delay(i * 3,  i * 4)

           IdeAutoCompleteHelper(f).start_consuming_message()  # 和 f.consume()等效

        """
        self.is_decorated_as_consume_function = consuming_func_decorated.is_decorated_as_consume_function
        self.consuming_func_decorated = consuming_func_decorated

        self.consumer = consuming_func_decorated.consumer  # type: AbstractConsumer

        self.publisher = consuming_func_decorated.publisher  # type: AbstractPublisher
        self.publish = self.pub = self.apply_async = self.publisher.publish  # type: AbstractPublisher.publish
        self.push = self.delay = self.publisher.push  # type: AbstractPublisher.push
        self.clear = self.clear_queue = self.publisher.clear  # type: AbstractPublisher.clear

        self.start_consuming_message = self.consume = self.start = self.consumer.start_consuming_message

        self.clear_filter_tasks = self.consumer.clear_filter_tasks

        self.wait_for_possible_has_finish_all_tasks = self.consumer.wait_for_possible_has_finish_all_tasks

    def multi_process_consume(self, process_num=1):
        run_consumer_with_multi_process(self.consuming_func_decorated, process_num)

    # noinspection PyDefaultArgument
    def fabric_deploy(self, host, port, user, password,
                      path_pattern_exluded_tuple=('/.git/', '/.idea/', '/dist/', '/build/'),
                      file_suffix_tuple_exluded=('.pyc', '.log', '.gz'),
                      only_upload_within_the_last_modify_time=3650 * 24 * 60 * 60,
                      file_volume_limit=1000 * 1000, extra_shell_str='',
                      invoke_runner_kwargs={'hide': None, 'pty': True, 'warn': False},
                      process_num=1):
        """
        入参见 fabric_deploy 函数。这里重复入参是为了代码在pycharm补全提示。
        """
        in_kwargs = locals()
        in_kwargs.pop('self')
        fabric_deploy(self.consuming_func_decorated, **in_kwargs)

    multi_process_start = multi_process_consume

    def __call__(self, *args, **kwargs):
        return self.consuming_func_decorated(*args, **kwargs)


def task_deco(queue_name, *, function_timeout=0,
              concurrent_num=50, specify_concurrent_pool=None, specify_async_loop=None, concurrent_mode=1,
              max_retry_times=3, log_level=10, is_print_detail_exception=True, is_show_message_get_from_broker=False,
              qps: float = 0, is_using_distributed_frequency_control=False, msg_expire_senconds=0,
              is_send_consumer_hearbeat_to_redis=False,
              logger_prefix='', create_logger_file=True, do_task_filtering=False, task_filtering_expire_seconds=0,
              is_do_not_run_by_specify_time_effect=False, do_not_run_by_specify_time=('10:00:00', '22:00:00'),
              schedule_tasks_on_main_thread=False,
              function_result_status_persistance_conf=FunctionResultStatusPersistanceConfig(False, False, 7 * 24 * 3600),
              is_using_rpc_mode=False,
              broker_kind: int = None):
    """
    # 为了代码提示好，这里重复一次入参意义。被此装饰器装饰的函数f，函数f对象本身自动加了一些方法，例如f.push 、 f.consume等。
    :param queue_name: 队列名字。
    :param function_timeout : 超时秒数，函数运行超过这个时间，则自动杀死函数。为0是不限制。
    # 如果设置了qps，并且cocurrent_num是默认的50，会自动开了500并发，由于是采用的智能线程池任务少时候不会真开那么多线程而且会自动缩小线程数量。具体看ThreadPoolExecutorShrinkAble的说明
    # 由于有很好用的qps控制运行频率和智能扩大缩小的线程池，此框架建议不需要理会和设置并发数量只需要关心qps就行了，框架的并发是自适应并发数量，这一点很强很好用。
    :param concurrent_num:并发数量
    :param specify_concurrent_pool:使用指定的线程池（协程池），可以多个消费者共使用一个线程池，不为None时候。threads_num失效
    :param specify_async_loop:指定的async的loop循环，设置并发模式为async才能起作用。
    :param concurrent_mode:并发模式，1线程 2gevent 3eventlet 4 asyncio
    :param max_retry_times: 最大自动重试次数，当函数发生错误，立即自动重试运行n次，对一些特殊不稳定情况会有效果。
           可以在函数中主动抛出重试的异常ExceptionForRetry，框架也会立即自动重试。
           主动抛出ExceptionForRequeue异常，则当前消息会重返中间件。
    :param log_level:框架的日志级别。logging.DEBUG(10)  logging.DEBUG(10) logging.INFO(20) logging.WARNING(30) logging.ERROR(40) logging.CRITICAL(50)
    :param is_print_detail_exception:是否打印详细的堆栈错误。为0则打印简略的错误占用控制台屏幕行数少。
    :param is_show_message_get_from_broker: 从中间件取出消息时候时候打印显示出来
    :param qps:指定1秒内的函数执行次数，qps会覆盖msg_schedule_time_intercal，以后废弃msg_schedule_time_intercal这个参数。
    :param msg_expire_senconds:消息过期时间，为0永不过期，为10则代表，10秒之前发布的任务如果现在才轮到消费则丢弃任务。
    :param is_using_distributed_frequency_control: 是否使用分布式空频（依赖redis计数），默认只对当前实例化的消费者空频有效。假如实例化了2个qps为10的使用同一队列名的消费者，
               并且都启动，则每秒运行次数会达到20。如果使用分布式空频则所有消费者加起来的总运行次数是10。
    :param is_send_consumer_hearbeat_to_redis   时候将发布者的心跳发送到redis，有些功能的实现需要统计活跃消费者。因为有的中间件不是真mq。
    :param logger_prefix: 日志前缀，可使不同的消费者生成不同的日志
    :param create_logger_file : 是否创建文件日志
    :param do_task_filtering :是否执行基于函数参数的任务过滤
    :param task_filtering_expire_seconds:任务过滤的失效期，为0则永久性过滤任务。例如设置过滤过期时间是1800秒 ，
           30分钟前发布过1 + 2 的任务，现在仍然执行，
           如果是30分钟以内发布过这个任务，则不执行1 + 2，现在把这个逻辑集成到框架，一般用于接口价格缓存。
    :param is_do_not_run_by_specify_time_effect :是否使不运行的时间段生效
    :param do_not_run_by_specify_time   :不运行的时间段
    :param schedule_tasks_on_main_thread :直接在主线程调度任务，意味着不能直接在当前主线程同时开启两个消费者。
    :param function_result_status_persistance_conf   :配置。是否保存函数的入参，运行结果和运行状态到mongodb。
           这一步用于后续的参数追溯，任务统计和web展示，需要安装mongo。
    :param is_using_rpc_mode 是否使用rpc模式，可以在发布端获取消费端的结果回调，但消耗一定性能，使用async_result.result时候会等待阻塞住当前线程。。
    :param broker_kind:中间件种类,。 0 使用pika链接rabbitmqmq，1使用rabbitpy包实现的操作rabbitmnq，2使用redis，
           3使用python内置Queue,4使用amqpstorm包实现的操作rabbitmq，5使用mongo，6使用本机磁盘持久化。
           7使用nsq，8使用kafka，9也是使用redis但支持消费确认。10为sqlachemy，支持mysql sqlite postgre oracel sqlserver
           11使用rocketmq. 12 使用 redis 的 stream 数据结构，这个也能支持消费确认。
    """

    """
    这是此框架最重要的一个函数，必须看懂里面的入参有哪些。
    此函数的入参意义请查看 get_consumer的入参注释。

    本来是这样定义的，def task_deco(queue_name, **consumer_init_kwargs):
    为了更好的ide智能补全，重复写全函数入参。

    装饰器方式注册消费任务，如果有人过于喜欢装饰器方式，例如celery 装饰器方式的任务注册，觉得黑科技，那就可以使用这个装饰器。
    此种方式不利于ide代码自动补全,被装饰的函数自身自动添加了几个方法,但不能被ide补全。所以请牢记以下几个方法名，
    假如你的函数名是f,那么可以调用f.publish或f.pub来发布任务。调用f.start_consuming_message 或 f.consume 或 f.start消费任务。
    必要时候调用f.publisher.funcxx   和 f.conusmer.funcyy。


    装饰器版，使用方式例如：
    '''
    @task_deco('queue_test_f01', qps=0.2, broker_kind=2)
    def f(a, b):
        print(a + b)

    for i in range(10, 20):
        f.pub(dict(a=i, b=i * 2))
        f.push(i, i * 2)
    f.consume()
    # f.multi_process_conusme(8)             # # 这个是新加的方法，细粒度 线程 协程并发 同时叠加8个进程，速度炸裂。主要是无需导入run_consumer_with_multi_process函数。
    # run_consumer_with_multi_process(f,8)   # 这个是细粒度 线程 协程并发 同时叠加8个进程，速度炸裂。
    '''

    常规方式，使用方式如下
    '''
    def f(a, b):
        print(a + b)

    consumer = get_consumer('queue_test_f01', consuming_function=f,qps=0.2, broker_kind=2)
    # 需要手动指定consuming_function入参的值。
    for i in range(10, 20):
        consumer.publisher_of_same_queue.publish(dict(a=i, b=i * 2))
    consumer.start_consuming_message()
    #run_consumer_with_multi_process(consumer,4) # 一次性启动4个进程。
    '''

    装饰器版本的 task_deco 入参 和 get_consumer 入参99%一致，唯一不同的是 装饰器版本加在了函数上自动知道消费函数了，
    所以不需要传consuming_function参数。
    """
    # 装饰器版本能够自动知道消费函数，防止task_deco按照get_consumer的入参重复传参了consuming_function。
    consumer_init_params = copy.copy(locals())

    def _deco(func) -> IdeAutoCompleteHelper:  # 加这个-> 可以实现pycahrm动态补全

        func.init_params = consumer_init_params
        consumer = get_consumer(consuming_function=func, **consumer_init_params)
        func.is_decorated_as_consume_function = True
        func.consumer = consumer
        # 下面这些连等主要是由于元编程造成的不能再ide下智能补全，参数太长很难手动拼写出来

        func.publisher = consumer.publisher_of_same_queue
        func.publish = func.pub = func.apply_async = consumer.publisher_of_same_queue.publish
        func.push = func.delay = consumer.publisher_of_same_queue.push
        func.clear = func.clear_queue = consumer.publisher_of_same_queue.clear

        func.start_consuming_message = func.consume = func.start = consumer.start_consuming_message
        func.multi_process_start = func.multi_process_consume = partial(run_consumer_with_multi_process, func)
        func.fabric_deploy = partial(fabric_deploy, func)

        func.clear_filter_tasks = consumer.clear_filter_tasks

        func.wait_for_possible_has_finish_all_tasks = consumer.wait_for_possible_has_finish_all_tasks

        # @wraps(func)
        # def __deco(*args, **kwargs):  # 这样函数的id变化了，导致win在装饰器内部开多进程不方便。
        #     return func(*args, **kwargs)
        return func
        # return __deco  # noqa # 两种方式都可以
        # return update_wrapper(__deco, func)

    return _deco  # noqa


def _run_many_consumer_by_init_params(consumer_init_params_list: List[dict]):
    for consumer_init_params in consumer_init_params_list:
        get_consumer(**consumer_init_params).start_consuming_message()
    ConsumersManager.join_all_consumer_shedual_task_thread()


def run_consumer_with_multi_process(task_fun, process_num=1):
    """
    :param task_fun:被 task_deco 装饰器装饰的消费函数
    :param process_num:开启多个进程。  主要是 多进程并发  + 4种细粒度并发(threading gevent eventlet asyncio)。叠加并发。
    这种是多进程方式，一次编写能够兼容win和linux的运行。一次性启动6个进程 叠加 多线程 并发。
    """
    '''
       from function_scheduling_distributed_framework import task_deco, BrokerEnum, ConcurrentModeEnum, run_consumer_with_multi_process
       import os

       @task_deco('test_multi_process_queue',broker_kind=BrokerEnum.REDIS_ACK_ABLE,concurrent_mode=ConcurrentModeEnum.THREADING,)
       def fff(x):
           print(x * 10,os.getpid())

       if __name__ == '__main__':
           # fff.consume()
           run_consumer_with_multi_process(fff,6) # 一次性启动6个进程 叠加 多线程 并发。
    '''
    if not getattr(task_fun, 'is_decorated_as_consume_function'):
        raise ValueError(f'{task_fun} 参数必须是一个被 task_deco 装饰的函数')
    if process_num == 1:
        task_fun.consume()
    else:
        [Process(target=_run_many_consumer_by_init_params,
                 args=([{**{'consuming_function': task_fun}, **task_fun.init_params}],)).start() for _ in range(process_num)]


# noinspection PyDefaultArgument
def fabric_deploy(task_fun, host, port, user, password,
                  path_pattern_exluded_tuple=('/.git/', '/.idea/', '/dist/', '/build/'),
                  file_suffix_tuple_exluded=('.pyc', '.log', '.gz'),
                  only_upload_within_the_last_modify_time=3650 * 24 * 60 * 60,
                  file_volume_limit=1000 * 1000, extra_shell_str='',
                  invoke_runner_kwargs={'hide': None, 'pty': True, 'warn': False},
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


    :param task_fun:被@task_deco 装饰的函数
    :param host: 需要部署的远程linux机器的 ip
    :param port:需要部署的远程linux机器的 port
    :param user: 需要部署的远程linux机器的用户名
    :param password:需要部署的远程linux机器的密码
    :param path_pattern_exluded_tuple:排除的文件夹或文件路径
    :param file_suffix_tuple_exluded:排除的后缀
    :param only_upload_within_the_last_modify_time:只上传多少秒以内的文件，如果完整运行上传过一次后，之后可以把值改小，避免每次全量上传。
    :param file_volume_limit:大于这个体积的不上传，因为python代码文件很少超过1M
    :param extra_shell_str :自动部署前额外执行的命令，例如可以设置环境变量什么的
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
                                          only_upload_within_the_last_modify_time, file_volume_limit)
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

        python_exec_str = f'''export is_fsdf_remote_run=1;export PYTHONPATH={remote_dir}:$PYTHONPATH ;python3 -c "from {relative_module} import {func_name};{func_name}.multi_process_consume({process_num})"  -fsdfmark {process_mark} '''
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
