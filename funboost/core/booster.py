from __future__ import annotations
import copy
import os
import types
import typing

import nb_log
from functools import wraps

from funboost.core.function_result_status_config import FunctionResultStatusPersistanceConfig

from funboost.funboost_config_deafult import BoostDecoratorDefaultParams

from funboost.factories.consumer_factory import get_consumer


class _Undefined:
    pass


class Booster:
    """
    funboost极其重视代码能在pycharm下自动补全。元编程经常造成在pycharm下代码无法自动补全提示，主要是实现代码补全难。
    这种__call__写法在pycahrm下 不仅能补全消费函数的 push consume等方法，也能补全函数本身的入参，一举两得。代码能自动补全很重要。
    一个函数fun被 boost装饰器装饰后， isinstance(fun,Booster) 为True.

    Booster 是把Consumer 和 Publisher的方法集为一体。
    """

    def __init__(self, queue_name,
                 *,
                 consumin_function_decorator: typing.Callable = _Undefined,
                 function_timeout: float = _Undefined,
                 concurrent_num: int = _Undefined,
                 specify_concurrent_pool=_Undefined,
                 specify_async_loop=_Undefined,
                 concurrent_mode: int = _Undefined,
                 qps: float = _Undefined,
                 is_using_distributed_frequency_control: bool = _Undefined,
                 max_retry_times: int = _Undefined,
                 is_push_to_dlx_queue_when_retry_max_times: bool = _Undefined,
                 log_level: int = _Undefined,
                 is_print_detail_exception: bool = _Undefined,
                 is_show_message_get_from_broker: bool = _Undefined,
                 msg_expire_senconds: float = _Undefined,
                 is_send_consumer_hearbeat_to_redis: bool = _Undefined,
                 logger_prefix: str = _Undefined,
                 create_logger_file: bool = _Undefined,
                 do_task_filtering: bool = _Undefined,
                 task_filtering_expire_seconds: float = _Undefined,
                 is_do_not_run_by_specify_time_effect: bool = _Undefined,
                 do_not_run_by_specify_time: bool = _Undefined,
                 schedule_tasks_on_main_thread: bool = _Undefined,
                 function_result_status_persistance_conf: FunctionResultStatusPersistanceConfig = _Undefined,
                 user_custom_record_process_info_func: typing.Union[typing.Callable, None] = _Undefined,
                 is_using_rpc_mode: bool = _Undefined,
                 is_support_remote_kill_task: bool = _Undefined,
                 broker_exclusive_config: dict = _Undefined,
                 broker_kind: int = _Undefined,
                 boost_decorator_default_params=BoostDecoratorDefaultParams()):
        """
           funboost.funboost_config_deafult.BoostDecoratorDefaultParams 的值会自动被你项目根目录下的funboost_config.BoostDecoratorDefaultParams的值覆盖，
           如果boost装饰器不传参，默认使用funboost_config.BoostDecoratorDefaultParams的配置

           入参也可以看文档 https://funboost.readthedocs.io/zh/latest/articles/c3.html   3.3章节。

           # 为了代码提示好，这里重复一次入参意义。被此装饰器装饰的函数f，函数f对象本身自动加了一些方法，例如f.push 、 f.consume等。
           :param queue_name: 队列名字。
           :param consumin_function_decorator : 函数的装饰器。因为此框架做参数自动转指点，需要获取精准的入参名称，不支持在消费函数上叠加 @ *args  **kwargs的装饰器，如果想用装饰器可以这里指定。
           :param function_timeout : 超时秒数，函数运行超过这个时间，则自动杀死函数。为0是不限制。设置后代码性能会变差，非必要不要轻易设置。
           # 如果设置了qps，并且cocurrent_num是默认的50，会自动开了500并发，由于是采用的智能线程池任务少时候不会真开那么多线程而且会自动缩小线程数量。具体看ThreadPoolExecutorShrinkAble的说明
           # 由于有很好用的qps控制运行频率和智能扩大缩小的线程池，此框架建议不需要理会和设置并发数量只需要关心qps就行了，框架的并发是自适应并发数量，这一点很强很好用。
           :param concurrent_num:并发数量
           :param specify_concurrent_pool:使用指定的线程池（协程池），可以多个消费者共使用一个线程池，不为None时候。threads_num失效
           :param specify_async_loop:指定的async的loop循环，设置并发模式为async才能起作用。
           :param concurrent_mode:并发模式，1线程(ConcurrentModeEnum.THREADING) 2gevent(ConcurrentModeEnum.GEVENT)
                                     3eventlet(ConcurrentModeEnum.EVENTLET) 4 asyncio(ConcurrentModeEnum.ASYNC) 5单线程(ConcurrentModeEnum.SINGLE_THREAD)
           :param max_retry_times: 最大自动重试次数，当函数发生错误，立即自动重试运行n次，对一些特殊不稳定情况会有效果。
                  可以在函数中主动抛出重试的异常ExceptionForRetry，框架也会立即自动重试。
                  主动抛出ExceptionForRequeue异常，则当前 消息会重返中间件，
                  主动抛出 ExceptionForPushToDlxqueue  异常，可以使消息发送到单独的死信队列中，死信队列的名字是 队列名字 + _dlx。
                  。
           :param is_push_to_dlx_queue_when_retry_max_times : 函数达到最大重试次数仍然没成功，是否发送到死信队列,死信队列的名字是 队列名字 + _dlx。
           :param log_level:框架的日志级别。logging.DEBUG(10)  logging.DEBUG(10) logging.INFO(20) logging.WARNING(30) logging.ERROR(40) logging.CRITICAL(50)
           :param is_print_detail_exception:是否打印详细的堆栈错误。为0则打印简略的错误占用控制台屏幕行数少。
           :param is_show_message_get_from_broker: 从中间件取出消息时候时候打印显示出来
           :param qps:指定1秒内的函数执行次数，例如可以是小数0.01代表每100秒执行一次，也可以是50代表1秒执行50次.为0则不控频。
           :param msg_expire_senconds:消息过期时间，为0永不过期，为10则代表，10秒之前发布的任务如果现在才轮到消费则丢弃任务。
           :param is_using_distributed_frequency_control: 是否使用分布式空频（依赖redis统计消费者数量，然后频率平分），默认只对当前实例化的消费者空频有效。
                   假如实例化了2个qps为10的使用同一队列名的消费者，并且都启动，则每秒运行次数会达到20。如果使用分布式空频则所有消费者加起来的总运行次数是10。
           :param is_send_consumer_hearbeat_to_redis   是否将发布者的心跳发送到redis，有些功能的实现需要统计活跃消费者。因为有的中间件不是真mq。
           :param logger_prefix: 日志前缀，可使不同的消费者生成不同的日志前缀
           :param create_logger_file : 是否创建文件日志
           :param do_task_filtering :是否执行基于函数参数的任务过滤
           :param task_filtering_expire_seconds:任务过滤的失效期，为0则永久性过滤任务。例如设置过滤过期时间是1800秒 ，
                  30分钟前发布过1 + 2 的任务，现在仍然执行，
                  如果是30分钟以内发布过这个任务，则不执行1 + 2，现在把这个逻辑集成到框架，一般用于接口价格缓存。
           :param is_do_not_run_by_specify_time_effect :是否使不运行的时间段生效
           :param do_not_run_by_specify_time   :不运行的时间段
           :param schedule_tasks_on_main_thread :直接在主线程调度任务，意味着不能直接在当前主线程同时开启两个消费者。fun.consume()就阻塞了，这之后的代码不会运行
           :param function_result_status_persistance_conf   :配置。是否保存函数的入参，运行结果和运行状态到mongodb。
                  这一步用于后续的参数追溯，任务统计和web展示，需要安装mongo。
           :param user_custom_record_process_info_func  提供一个用户自定义的保存消息处理记录到某个地方例如mysql数据库的函数，函数仅仅接受一个入参，入参类型是 FunctionResultStatus，用户可以打印参数
           :param is_using_rpc_mode 是否使用rpc模式，可以在发布端获取消费端的结果回调，但消耗一定性能，使用async_result.result时候会等待阻塞住当前线程。。
           :param is_support_remote_kill_task 是否支持远程任务杀死功能，如果任务数量少，单个任务耗时长，确实需要远程发送命令来杀死正在运行的函数，才设置为true，否则不建议开启此功能。
           :param broker_exclusive_config 加上一个不同种类中间件非通用的配置,不同中间件自身独有的配置，不是所有中间件都兼容的配置，因为框架支持30种消息队列，消息队列不仅仅是一般的先进先出queue这么简单的概念，
                   例如kafka支持消费者组，rabbitmq也支持各种独特概念例如各种ack机制 复杂路由机制，每一种消息队列都有独特的配置参数意义，可以通过这里传递。
           :param broker_kind:中间件种类，支持30种消息队列。 入参见 BrokerEnum枚举类的属性。
           :param boost_decorator_default_params: oostDecoratorDefaultParams是
                   @boost装饰器默认的全局入参。如果boost没有亲自指定某个入参，就自动使用funboost_config.py的BoostDecoratorDefaultParams中的配置。
                           如果你嫌弃每个 boost 装饰器相同入参太多重复了，可以在 funboost_config.py 文件中设置boost装饰器的全局默认值。
                   BoostDecoratorDefaultParams() 实例化时候也可以传递这个boost装饰器任何的入参，BoostDecoratorDefaultParams是个数据类，百度python3.7dataclass的概念，类似。

                   funboost.funboost_config_deafult.BoostDecoratorDefaultParams 的值会自动被你项目根目录下的funboost_config.BoostDecoratorDefaultParams的值覆盖

           """

        """
        这是此框架最重要的一个函数，必须看懂里面的入参有哪些。
        此函数的入参意义请查看 get_consumer的入参注释。

        '''
        @boost('queue_test_f01', qps=0.2, broker_kind=2)
        def f(a, b):
            print(a + b)

        for i in range(10, 20):
            f.pub(dict(a=i, b=i * 2))
            f.push(i, i * 2)
        f.consume()
        # f.multi_process_conusme(8)             # # 这个是新加的方法，细粒度 线程 协程并发 同时叠加8个进程，速度炸裂。主要是无需导入run_consumer_with_multi_process函数。
        '''
        """
        loc = locals()
        loc.pop('self')
        self.boost_params = self.__get_final_boost_params(boost_params_include_boost_decorator_default_params=loc)

    @staticmethod
    def __get_final_boost_params(boost_params_include_boost_decorator_default_params):
        # 下面这段代码 boost_params 是综合funboost_config.BoostDecoratorDefaultParams全局入参 和boost装饰器入参，最终得到的入参。
        # 如果@boost装饰器没有亲自执行boost的某个入参，则使用BoostDecoratorDefaultParams全局入参
        boost_params0 = copy.copy(boost_params_include_boost_decorator_default_params)
        boost_params0.pop('boost_decorator_default_params')
        boost_params = copy.copy(boost_params0)
        for k, v in boost_params0.items():
            if v == _Undefined:
                # print(k,v,boost_decorator_default_params[k])
                boost_params[k] = boost_params_include_boost_decorator_default_params['boost_decorator_default_params'][k]  # boost装饰器没有亲指定某个传参，就使用funboost_config.py的BoostDecoratorDefaultParams的全局配置。
        return boost_params

    def __str__(self):
        return f'{type(self)}  队列为 {self.queue_name} 函数为 {self.consuming_function} 的 booster'

    def __get__(self, instance, cls):
        """https://python3-cookbook.readthedocs.io/zh_CN/latest/c09/p09_define_decorators_as_classes.html"""
        if instance is None:
            return self
        else:
            return types.MethodType(self, instance)

    def __call__(self, *args, **kwargs) -> Booster:
        if len(kwargs) == 0 and len(args) == 1 and isinstance(args[0], typing.Callable):
            consuming_function = args[0]
            self.consuming_function = consuming_function
            self.boost_params = self.boost_params  # boost装饰器的入参
            self.queue_name = self.boost_params['queue_name']
            self.is_decorated_as_consume_function = True

            consumer = get_consumer(**self.boost_params, consuming_function=consuming_function)
            self.consumer = consumer
            self.publisher = consumer.publisher_of_same_queue
            self.publish = self.pub = self.apply_async = consumer.publisher_of_same_queue.publish
            self.push = self.delay = consumer.publisher_of_same_queue.push
            self.clear = self.clear_queue = consumer.publisher_of_same_queue.clear
            self.get_message_count = consumer.publisher_of_same_queue.get_message_count

            self.start_consuming_message = self.consume = self.start = consumer.start_consuming_message
            self.clear_filter_tasks = consumer.clear_filter_tasks
            self.wait_for_possible_has_finish_all_tasks = consumer.wait_for_possible_has_finish_all_tasks

            self.pause = self.pause_consume = consumer.pause_consume
            self.continue_consume = consumer.continue_consume

            wraps(consuming_function)(self)
            BoostersManager.regist_booster(self.queue_name, self)
            return self
        else:
            return self.consuming_function(*args, **kwargs)

    # noinspection PyMethodMayBeStatic
    def multi_process_consume(self, process_num=1):
        """超高速多进程消费"""
        from funboost.core.muliti_process_enhance import run_consumer_with_multi_process
        run_consumer_with_multi_process(self, process_num)

    multi_process_start = multi_process_consume

    # noinspection PyMethodMayBeStatic
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
        from funboost.core.muliti_process_enhance import multi_process_pub_params_list
        multi_process_pub_params_list(self, params_list, process_num)

    # noinspection PyDefaultArgument
    # noinspection PyMethodMayBeStatic
    def fabric_deploy(self, host, port, user, password,
                      path_pattern_exluded_tuple=('/.git/', '/.idea/', '/dist/', '/build/'),
                      file_suffix_tuple_exluded=('.pyc', '.log', '.gz'),
                      only_upload_within_the_last_modify_time=3650 * 24 * 60 * 60,
                      file_volume_limit=1000 * 1000, sftp_log_level=20, extra_shell_str='',
                      invoke_runner_kwargs={'hide': None, 'pty': True, 'warn': False},
                      python_interpreter='python3',
                      process_num=1):
        """
        入参见 fabric_deploy 函数。这里重复入参是为了代码在pycharm补全提示。
        """
        params = copy.copy(locals())
        params.pop('self')
        from funboost.core.fabric_deploy_helper import fabric_deploy
        fabric_deploy(self, **params)


boost = Booster
task_deco = boost  # 两个装饰器名字都可以。task_deco是原来名字，兼容一下。


class BoostersManager:
    logger = nb_log.get_logger('BoostersManager')

    # pid_queue_name__booster_map字典存放 {(进程id,queue_name):Booster对象}
    pid_queue_name__booster_map = {}  # type: typing.Dict[typing.Tuple[int,str],Booster]

    # queue_name__boost_params_consuming_function_map 字典存放  {queue_name,(@boost的入参字典,@boost装饰的函数)}
    queue_name__boost_params_consuming_function_map = {}  # type: typing.Dict[str,typing.Tuple[dict,typing.Callable]]

    @classmethod
    def regist_booster(cls, queue_name: str, booster: Booster):
        cls.pid_queue_name__booster_map[(os.getpid(), queue_name)] = booster
        cls.queue_name__boost_params_consuming_function_map[queue_name] = (booster.boost_params, booster.consuming_function)

    @classmethod
    def show_all_boosters(cls):
        queues = []
        for pid_queue_name, booster in cls.pid_queue_name__booster_map.items():
            queues.append(pid_queue_name[1])
            cls.logger.debug(f'booster: {pid_queue_name[1]}  {booster}')

    @classmethod
    def get_all_queues(cls):
        return cls.queue_name__boost_params_consuming_function_map.keys()

    @classmethod
    def get_booster(cls, queue_name: str) -> Booster:
        pid = os.getpid()
        key = (pid, queue_name)
        if key not in cls.pid_queue_name__booster_map:
            err_msg = f'进程 {pid} ，没有 {queue_name} 对应的 booster   , pid_queue_name__booster_map: {cls.pid_queue_name__booster_map}'
            raise ValueError(err_msg)
        return cls.pid_queue_name__booster_map[key]

    @classmethod
    def get_or_create_booster_by_queue_name(cls, queue_name, ) -> Booster:
        """
        当前进程获得booster对象。如果是多进程,在进程内部创建一个新的booster对象,因为多进程操作有些中间件的同一个conn不行.
        :param queue_name: 就是 @boost的入参。
        :return:
        """
        pid = os.getpid()
        key = (pid, queue_name)
        if key in cls.pid_queue_name__booster_map:
            return cls.pid_queue_name__booster_map[key]
        else:
            boost_params, consuming_function = cls.queue_name__boost_params_consuming_function_map[queue_name]
            return Booster(**boost_params)(consuming_function)

    @classmethod
    def get_boost_params_and_consuming_function(cls, queue_name: str) -> (dict, typing.Callable):
        """
        这个函数是为了在别的进程实例化 booster，consumer和publisher,获取queue_name队列对应的booster的当时的入参。
        有些中间件python包的对中间件连接对象不是多进程安全的，不要在进程2中去操作进程1中生成的booster consumer publisher等对象。
        """

        """
        boost_params,consuming_function = get_boost_params_and_consuming_function(queue_name)
        booster_current_pid = boost(**boost_params)(consuming_function)
        """
        return cls.queue_name__boost_params_consuming_function_map[queue_name]

    @classmethod
    def get_or_create_booster(cls, *, consuming_function=None, **boost_params, ) -> Booster:
        """
        当前进程获得或者创建booster对象。方便有的人需要在函数内部临时动态根据队列名创建booster,不会无数次临时生成消费者、生产者、创建消息队列连接。
        :param boost_params: 就是 @boost的入参。
        :param consuming_function: 消费函数
        :return:
        """
        pid = os.getpid()
        key = (pid, boost_params['queue_name'])
        if key in cls.pid_queue_name__booster_map:
            return cls.pid_queue_name__booster_map[key]
        else:
            cls.logger.info(f'创建booster {boost_params} {consuming_function}')
            return Booster(**boost_params)(consuming_function)
