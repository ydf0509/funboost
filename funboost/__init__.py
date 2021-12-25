from functools import update_wrapper, wraps, partial
import copy
# noinspection PyUnresolvedReferences
import nb_log
from funboost.set_frame_config import patch_frame_config, show_frame_config
from funboost.helpers import (fabric_deploy, kill_all_remote_tasks,
                              multi_process_pub_params_list,
                              run_consumer_with_multi_process)
from funboost.utils.paramiko_util import ParamikoFolderUploader
from funboost.consumers.base_consumer import (ExceptionForRequeue, ExceptionForRetry,
                                              AbstractConsumer, ConsumersManager,
                                              FunctionResultStatusPersistanceConfig,
                                              wait_for_possible_has_finish_all_tasks_by_conusmer_list)
from funboost.publishers.base_publisher import (PriorityConsumingControlConfig,
                                                AbstractPublisher, AsyncResult, HasNotAsyncResult)
from funboost.factories.publisher_factotry import get_publisher
from funboost.factories.consumer_factory import get_consumer

# noinspection PyUnresolvedReferences
from funboost.utils import nb_print, patch_print, LogManager, get_logger, LoggerMixin
from funboost.timing_job import fsdf_background_scheduler, timing_publish_deco
from funboost.constant import BrokerEnum, ConcurrentModeEnum

# 有的包默认没加handlers，原始的日志不漂亮且不可跳转不知道哪里发生的。这里把warnning级别以上的日志默认加上handlers。
nb_log.get_logger(name=None, log_level_int=30, log_filename='pywarning.log')

logger = nb_log.get_logger('funboost')

logger.debug(f'\n 分布式函数调度框架文档地址：  https://function-scheduling-distributed-framework.readthedocs.io/zh_CN/latest/')

class IdeAutoCompleteHelper(LoggerMixin):
    """
    为了被装饰的消费函数的敲代码时候的被pycharm自动补全而写的类。
    """

    def __init__(self, consuming_func_decorated: callable):
        """
        :param consuming_func_decorated:   传入被boost装饰的函数

        此框架非常非常注重，公有函数、方法、类 的名字和入参在ide开发环境下面的自动提示补全效果，如果不是为了这一点，框架能减少很多重复地方。
        此类是防止用户调用打错字母或者不知道怎么敲代码不知道有哪些入参。所以才有这个类。

        这个类是个补全类，能够使pycharm自动补全方法名字和入参。可以用，可以不用，用了后在pycharm里面补全效果会起作用。


       from funboost import boost, IdeAutoCompleteHelper

       @boost('queue_test_f01', qps=2, broker_kind=3)
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
        """超高速多进程消费"""
        run_consumer_with_multi_process(self.consuming_func_decorated, process_num)

    def multi_process_pub_params_list(self, params_list, process_num=16):
        """超高速多进程发布，例如先快速发布1000万个任务到中间件，以后慢慢消费"""
        """
        用法例如，快速20进程发布1000万任务，充分利用多核加大cpu使用率。
        @boost('test_queue66c', qps=1/30,broker_kind=BrokerEnum.KAFKA_CONFLUENT)
        def f(x, y):
            print(f'函数开始执行时间 {time.strftime("%H:%M:%S")}')
        if __name__ == '__main__':
            f.multi_process_pub_params_list([{'x':i,'y':i*3}  for i in range(10000000)],process_num=20)
            f.consume()
        """
        multi_process_pub_params_list(self.consuming_func_decorated, params_list=params_list, process_num=process_num)

    # noinspection PyDefaultArgument
    def fabric_deploy(self, host, port, user, password,
                      path_pattern_exluded_tuple=('/.git/', '/.idea/', '/dist/', '/build/'),
                      file_suffix_tuple_exluded=('.pyc', '.log', '.gz'),
                      only_upload_within_the_last_modify_time=3650 * 24 * 60 * 60,
                      file_volume_limit=1000 * 1000, sftp_log_level=20, extra_shell_str='',
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



def boost(queue_name, *, function_timeout=0,
          concurrent_num=50, specify_concurrent_pool=None, specify_async_loop=None, concurrent_mode=ConcurrentModeEnum.THREADING,
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
    :param concurrent_mode:并发模式，1线程(ConcurrentModeEnum.THREADING) 2gevent(ConcurrentModeEnum.GEVENT)
                              3eventlet(ConcurrentModeEnum.EVENTLET) 4 asyncio(ConcurrentModeEnum.ASYNC) 5单线程(ConcurrentModeEnum.SINGLE_THREAD)
    :param max_retry_times: 最大自动重试次数，当函数发生错误，立即自动重试运行n次，对一些特殊不稳定情况会有效果。
           可以在函数中主动抛出重试的异常ExceptionForRetry，框架也会立即自动重试。
           主动抛出ExceptionForRequeue异常，则当前 消息会重返中间件。
    :param log_level:框架的日志级别。logging.DEBUG(10)  logging.DEBUG(10) logging.INFO(20) logging.WARNING(30) logging.ERROR(40) logging.CRITICAL(50)
    :param is_print_detail_exception:是否打印详细的堆栈错误。为0则打印简略的错误占用控制台屏幕行数少。
    :param is_show_message_get_from_broker: 从中间件取出消息时候时候打印显示出来
    :param qps:指定1秒内的函数执行次数，例如可以是小数0.01代表每100秒执行一次，也可以是50代表1秒执行50次.为0则不控频。
    :param msg_expire_senconds:消息过期时间，为0永不过期，为10则代表，10秒之前发布的任务如果现在才轮到消费则丢弃任务。
    :param is_using_distributed_frequency_control: 是否使用分布式空频（依赖redis统计消费者数量，然后频率平分），默认只对当前实例化的消费者空频有效。
            假如实例化了2个qps为10的使用同一队列名的消费者，并且都启动，则每秒运行次数会达到20。如果使用分布式空频则所有消费者加起来的总运行次数是10。
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
    :param broker_kind:中间件种类，支持30种消息队列。 入参见 BrokerEnum枚举类的属性。
    """

    """
    这是此框架最重要的一个函数，必须看懂里面的入参有哪些。
    此函数的入参意义请查看 get_consumer的入参注释。

    本来是这样定义的，def boost(queue_name, **consumer_init_kwargs):
    为了更好的ide智能补全，重复写全函数入参。

    装饰器方式注册消费任务，如果有人过于喜欢装饰器方式，例如celery 装饰器方式的任务注册，觉得黑科技，那就可以使用这个装饰器。
    此种方式不利于ide代码自动补全,被装饰的函数自身自动添加了几个方法,但不能被ide补全。所以请牢记以下几个方法名，
    假如你的函数名是f,那么可以调用f.publish或f.pub来发布任务。调用f.start_consuming_message 或 f.consume 或 f.start消费任务。
    必要时候调用f.publisher.funcxx   和 f.conusmer.funcyy。


    装饰器版，使用方式例如：
    '''
    @boost('queue_test_f01', qps=0.2, broker_kind=2)
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

    装饰器版本的 boost 入参 和 get_consumer 入参99%一致，唯一不同的是 装饰器版本加在了函数上自动知道消费函数了，
    所以不需要传consuming_function参数。
    """
    # 装饰器版本能够自动知道消费函数，防止boost按照get_consumer的入参重复传参了consuming_function。
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
        func.multi_process_pub_params_list = partial(multi_process_pub_params_list, func)
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


task_deco =  boost  # 两个装饰器名字都可以。task_deco是原来名字，兼容一下。