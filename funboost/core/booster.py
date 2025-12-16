from __future__ import annotations
import copy
import inspect
from multiprocessing import Process
import os
import sys
import types
import typing

from funboost.concurrent_pool import FlexibleThreadPool
from funboost.concurrent_pool.async_helper import simple_run_in_executor
from funboost.constant import FunctionKind
from funboost.utils.class_utils import ClsHelper

from funboost.utils.ctrl_c_end import ctrl_c_recv
from funboost.core.loggers import flogger, develop_logger, logger_prompt

from functools import wraps

from funboost.core.exceptions import BoostDecoParamsIsOldVersion
from funboost.core.func_params_model import BoosterParams, FunctionResultStatusPersistanceConfig, PriorityConsumingControlConfig, PublisherParams

from funboost.factories.consumer_factory import get_consumer
from funboost.factories.publisher_factotry import get_publisher
from funboost.publishers.base_publisher import AbstractPublisher


from funboost.core.msg_result_getter import AsyncResult, AioAsyncResult


class Booster:
    """
    funboost极其重视代码能在pycharm下自动补全。元编程经常造成在pycharm下代码无法自动补全提示，主要是实现代码补全难。
    这种__call__写法在pycahrm下 不仅能补全消费函数的 push consume等方法，也能补全函数本身的入参，一举两得。代码能自动补全很重要。
    一个函数fun被 boost装饰器装饰后， isinstance(fun,Booster) 为True.

    pydatinc pycharm编程代码补全,请安装 pydantic插件, 在pycharm的  file -> settings -> Plugins -> 输入 pydantic 搜索,点击安装 pydantic 插件.

    Booster 是把Consumer 和 Publisher的方法集为一体。
    """

    def __init__(self, queue_name: typing.Union[BoosterParams, str] = None, *, boost_params: BoosterParams = None, **kwargs):
        """
        @boost 这是funboost框架最重要的一个函数，必须看懂BoosterParams里面的入参有哪些。
        建议永远使用 @boost(BoosterParams(queue_name='queue_test_f01', qps=0.2, )) 这种传参方式。


        pydatinc pycharm编程代码补全,请安装 pydantic插件, 在pycharm的  file -> settings -> Plugins -> 输入 pydantic 搜索,点击安装 pydantic 插件.
        (高版本的pycharm pydantic是内置支持代码补全的,由此可见,pydantic太好了,pycharm官方都来支持)

        强烈建议所有入参放在 BoosterParams() 中,不要直接在BoosterParams之外传参.现在是兼容老的直接在@boost中传参方式.
        建议不要给第一个入参queue_name传递字符串，而是永远传递BoosterParams类型， 例如 @boost(BoosterParams(queue_name='queue_test_f01', qps=0.2, ))


        ```python
        # @boost('queue_test_f01', qps=0.2, ) # 老的入参方式
        @boost(BoosterParams(queue_name='queue_test_f01', qps=0.2, )) # 新的入参方式,所有入参放在 最流行的三方包 pydantic model BoosterParams 里面.
        def f(a, b):
            print(a + b)

        for i in range(10, 20):
            f.pub(dict(a=i, b=i * 2))
            f.push(i, i * 2)
        f.consume()
        # f.multi_process_conusme(8)             # # 这个是新加的方法，细粒度 线程 协程并发 同时叠加8个进程，速度炸裂。
        ```
        
        
        @boost('queue_test_f01', qps=0.2, ) 
        @boost(BoosterParams(queue_name='queue_test_f01', qps=0.2, ))
        @Booster(BoosterParams(queue_name='queue_test_f01', qps=0.2, ))
        @BoosterParams(queue_name='queue_test_f01', qps=0.2, )
        以上4种写法等效。 
        """

        # 以下代码很复杂，主要是兼容老的在@boost直接传参的方式,强烈建议使用新的入参方式,所有入参放在一个 BoosterParams 中，那就不需要理会下面这段逻辑.
        if isinstance(queue_name, str):
            if boost_params is None:
                boost_params = BoosterParams(queue_name=queue_name)
        elif queue_name is None and boost_params is None:
            raise ValueError('boost 入参错误')
        elif isinstance(queue_name, BoosterParams):
            boost_params = queue_name
        if isinstance(queue_name, str) or kwargs:
            flogger.warning(f'''你的 {queue_name} 队列， funboost 40.0版本以后： {BoostDecoParamsIsOldVersion.default_message}''')
        boost_params_merge = boost_params.copy()
        boost_params_merge.update_from_dict(kwargs)
        self.boost_params: BoosterParams = boost_params_merge
        self.queue_name = boost_params_merge.queue_name

    def __str__(self):
        return f'{type(self)}  队列为 {self.queue_name} 函数为 {self.consuming_function} 的 booster'

    def __get__(self, instance, cls):
        """https://python3-cookbook.readthedocs.io/zh_CN/latest/c09/p09_define_decorators_as_classes.html"""
        if instance is None:
            return self
        else:
            return types.MethodType(self, instance)

    def __call__(self, *args, **kwargs) -> Booster:
        """
        # 第一次调用__call__，是装饰函数,返回了Booster对象,从此之后,被消费函数就变成了Booster类型对象.
        # Booster类型对象,怎么支持函数原来本身的直接运行功能? 那就是要让他走到 else 分支,直接用 self.consuming_function 函数本身去运行入参
        # 这里非常巧妙
        # 如果用户之后不打算使用funboost 的分布式函数调度功能,那么直接运行函数和原来一模一样,用户不需要删除 @boost装饰器 也能直接运行函数本身
        """
        if len(kwargs) == 0 and len(args) == 1 and isinstance(args[0], typing.Callable) and not isinstance(args[0], Booster):
            consuming_function = args[0]
            self.boost_params.consuming_function = consuming_function
            self.boost_params.consuming_function_raw = consuming_function
            self.boost_params.consuming_function_name = consuming_function.__name__
            # print(consuming_function)
            # print(ClsHelper.get_method_kind(consuming_function))
            # print(inspect.getsourcelines(consuming_function))
            if self.boost_params.consuming_function_kind is None:
                self.boost_params.consuming_function_kind = ClsHelper.get_method_kind(consuming_function)
            # if self.boost_params.consuming_function_kind in [FunctionKind.CLASS_METHOD,FunctionKind.INSTANCE_METHOD]:
            #     if self.boost_params.consuming_function_class_module is None:
            #         self.boost_params.consuming_function_class_module = consuming_function.__module__
            #     if self.boost_params.consuming_function_class_name is None:
            #         self.boost_params.consuming_function_class_name = consuming_function.__qualname__.split('.')[0]
            logger_prompt.debug(f''' {self.boost_params.queue_name} booster 配置是 {self.boost_params.json_str_value()}''')
            self.consuming_function = consuming_function
            self.is_decorated_as_consume_function = True

            consumer = get_consumer(self.boost_params)
            self.consumer = consumer

            self.publisher = consumer.publisher_of_same_queue
            # self.publish = self.pub = self.apply_async = consumer.publisher_of_same_queue.publish
            # self.push = self.delay = consumer.publisher_of_same_queue.push
            self.publish = self.pub = self.apply_async = self._safe_publish
            self.push = self.delay = self._safe_push

            self.clear = self.clear_queue = consumer.publisher_of_same_queue.clear
            self.get_message_count = consumer.publisher_of_same_queue.get_message_count

            self.start_consuming_message = self.consume = self.start = consumer.start_consuming_message
            self.clear_filter_tasks = consumer.clear_filter_tasks
            self.wait_for_possible_has_finish_all_tasks = consumer.wait_for_possible_has_finish_all_tasks

            self.pause = self.pause_consume = consumer.pause_consume
            self.continue_consume = consumer.continue_consume

            wraps(consuming_function)(self)
            BoostersManager.regist_booster(self.queue_name, self)  # 这一句是登记
            return self
        else:
            return self.consuming_function(*args, **kwargs)

    def _safe_push(self, *func_args, **func_kwargs) -> AsyncResult:
        """ 多进程安全的,在fork多进程(非spawn多进程)情况下,有的包多进程不能共用一个连接,例如kafka"""
        # print( self.__dict__)
        consumer = BoostersManager.get_or_create_booster_by_queue_name(self.queue_name).consumer
        return consumer.publisher_of_same_queue.push(*func_args, **func_kwargs)

    def _safe_publish(self, msg: typing.Union[str, dict], task_id=None,
                      priority_control_config: PriorityConsumingControlConfig = None) -> AsyncResult:
        """ 多进程安全的,在fork多进程(非spawn多进程)情况下,很多包跨线程/进程不能共享中间件连接,"""
        consumer = BoostersManager.get_or_create_booster_by_queue_name(self.queue_name).consumer
        return consumer.publisher_of_same_queue.publish(msg=msg, task_id=task_id, priority_control_config=priority_control_config)

    async def aio_push(self, *func_args, **func_kwargs) -> AioAsyncResult:
        """asyncio 生态下发布消息,因为同步push只需要消耗不到1毫秒,所以基本上大概可以直接在asyncio异步生态中直接调用同步的push方法,
        但为了更好的防止网络波动(例如发布消息到外网的消息队列耗时达到10毫秒),可以使用aio_push"""
        async_result = await simple_run_in_executor(self.push, *func_args, **func_kwargs)
        return AioAsyncResult(async_result.task_id,timeout=async_result.timeout )

    async def aio_publish(self, msg: typing.Union[str, dict], task_id=None,
                          priority_control_config: PriorityConsumingControlConfig = None) -> AioAsyncResult:
        """asyncio 生态下发布消息,因为同步push只需要消耗不到1毫秒,所以基本上大概可以直接在asyncio异步生态中直接调用同步的push方法,
        但为了更好的防止网络波动(例如发布消息到外网的消息队列耗时达到10毫秒),可以使用aio_push"""
        async_result = await simple_run_in_executor(self.publish, msg, task_id, priority_control_config)
        return AioAsyncResult(async_result.task_id, timeout=async_result.timeout)

    # noinspection PyMethodMayBeStatic
    def multi_process_consume(self, process_num=1):
        """超高速多进程消费"""
        from funboost.core.muliti_process_enhance import run_consumer_with_multi_process
        run_consumer_with_multi_process(self, process_num)

    multi_process_start = multi_process_consume
    mp_consume = multi_process_consume

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
                      process_num=1,
                      pkey_file_path=None,
                      ):
        """
        入参见 fabric_deploy 函数。这里重复入参是为了代码在pycharm补全提示。
        """
        params = copy.copy(locals())
        params.pop('self')
        from funboost.core.fabric_deploy_helper import fabric_deploy
        fabric_deploy(self, **params)

    def __getstate__(self):
        state = {}
        state['queue_name'] = self.boost_params.queue_name
        return state

    def __setstate__(self, state):
        """非常高级的骚操作,支持booster对象pickle序列化和反序列化,设计非常巧妙，堪称神来之笔
        这样当使用redis作为apscheduler的 jobstores时候,aps_obj.add_job(booster.push,...) 可以正常工作,
        使不报错 booster对象无法pickle序列化.

        这个反序列化,没有执着于对 socket threding.Lock 怎么反序列化,而是偷换概念，绕过难题,基于标识的代理反序列化
        """
        _booster = BoostersManager.get_or_create_booster_by_queue_name(state['queue_name'])
        self.__dict__.update(_booster.__dict__)




boost = Booster  # @boost 后消费函数.  不能自动补全方法就用 Booster就可以。 2024版本的 pycharm抽风了，@boost的消费函数不能自动补全提示 .consume  .push 这些方法。
task_deco = boost  # 两个装饰器名字都可以。task_deco是原来名字，兼容一下。


class BoostersManager:
    """
    这个BoostersManager类是后来加的不是一开始就规划了的.

    消费函数生成Booster对象时候,会自动调用BoostersManager.regist_booster方法,把队列名和入参信息保存到pid_queue_name__booster_map字典中.
    使用这个类,可以创建booster对象,达到无需使用装饰器的目的.

    如果你想一次性启动所有函数消费,不想 f1.consume()  f2.consume() f3.consume() 一个个的启动.
    可以  BoostersManager.consume_all_queues()
    """

    # pid_queue_name__booster_map字典存放 {(进程id,queue_name):Booster对象}
    pid_queue_name__booster_map :typing.Dict[typing.Tuple[int,str],Booster]= {}

    # queue_name__boost_params_consuming_function_map 字典存放  {queue_name,(@boost的入参字典,@boost装饰的消费函数)}
    queue_name__boost_params_map :typing.Dict[str,BoosterParams]= {}  

    pid_queue_name__has_start_consume_set = set()

    @classmethod
    def regist_booster(cls, queue_name: str, booster: Booster):
        """这个是框架在@boost时候自动调用的,无需用户亲自调用"""
        if booster.boost_params.is_fake_booster is True:
            return
        cls.pid_queue_name__booster_map[(os.getpid(), queue_name)] = booster
        cls.queue_name__boost_params_map[queue_name] = booster.boost_params

    @classmethod
    def show_all_boosters(cls):
        queues = []
        for pid_queue_name, booster in cls.pid_queue_name__booster_map.items():
            queues.append(pid_queue_name[1])
            flogger.debug(f'booster: {pid_queue_name[1]}  {booster}')

    @classmethod
    def get_all_queues(cls) ->list:
        return list(cls.queue_name__boost_params_map.keys())

    @classmethod
    def get_all_queue_name__boost_params_unstrict_dict(cls):
        """
        主要用来给前端或可视化观看的。

        返回一个字典,键是队列名,值是@boost的 BoosterParams 入参字典,
        因为 BoosterParams 有的入参是复杂对象类型,不能json序列化
        """
        return {k:v.get_str_dict() for k,v in cls.queue_name__boost_params_map.items()}

    @classmethod
    def get_booster(cls, queue_name: str) -> Booster:
        """
        当前进程获得booster对象。注意和下面的get_or_create_booster_by_queue_name方法的区别,主要是开了多进程时候有区别.
        :param queue_name:
        :return:
        """
        pid = os.getpid()
        key = (pid, queue_name)
        if key in cls.pid_queue_name__booster_map:
            return cls.pid_queue_name__booster_map[key]
        else:
            err_msg = f'进程 {pid} ，没有 {queue_name} 对应的 booster   , pid_queue_name__booster_map: {cls.pid_queue_name__booster_map}'
            raise ValueError(err_msg)

    @classmethod
    def get_or_create_booster_by_queue_name(cls, queue_name, ) -> Booster:
        """
        当前进程获得booster对象，如果是多进程,会在新的进程内部创建一个新的booster对象,因为多进程操作有些中间件的同一个conn不行.
        :param queue_name: 就是 @boost的入参。
        :return:
        """
        pid = os.getpid()
        key = (pid, queue_name)
        if key in cls.pid_queue_name__booster_map:
            return cls.pid_queue_name__booster_map[key]
        else:
            boost_params = cls.get_boost_params(queue_name)
            return Booster(boost_params)(boost_params.consuming_function)

    @classmethod
    def get_boost_params(cls, queue_name: str) -> (dict, typing.Callable):
        """
        这个函数是为了在别的进程实例化 booster，consumer和publisher,获取queue_name队列对应的booster的当时的入参。
        有些中间件python包的对中间件连接对象不是多进程安全的，不要在进程2中去操作进程1中生成的booster consumer publisher等对象。
        """
        return cls.queue_name__boost_params_map[queue_name]

    @classmethod
    def build_booster(cls, boost_params: BoosterParams) -> Booster:
        """
        当前进程获得或者创建booster对象。方便有的人需要在函数内部临时动态根据队列名创建booster,不会无数次临时生成消费者、生产者、创建消息队列连接。
        :param boost_params: 就是 @boost的入参。
        :param consuming_function: 消费函数
        :return:
        """
        pid = os.getpid()
        key = (pid, boost_params.queue_name)
        if key in cls.pid_queue_name__booster_map:
            booster = cls.pid_queue_name__booster_map[key]
        else:
            if boost_params.consuming_function is None:
                raise ValueError(f' build_booster 方法的 consuming_function 字段不能为None,必须指定一个函数')
            flogger.info(f'创建booster {boost_params} {boost_params.consuming_function}')
            booster = Booster(boost_params)(boost_params.consuming_function)
        return booster

    queue_name__cross_project_publisher_map = {}

    @classmethod
    def get_cross_project_publisher(cls, publisher_params: PublisherParams) -> AbstractPublisher:
        """
        跨不同的项目，发布消息。例如proj1中定义有fun1消费函数，但proj2无法直接到日proj1的函数，无法直接 fun1.push 来发布消息
        可以使用这个方法，获取一个publisher。

        publisher = BoostersManager.get_cross_project_publisher(PublisherParams(queue_name='proj1_queue', broker_kind=publisher_params.broker_kind))
        publisher.publish({'x': aaa})
        """
        pid = os.getpid()
        key = (pid,publisher_params.broker_kind, publisher_params.queue_name)
        if key not in cls.queue_name__cross_project_publisher_map:
            publisher = get_publisher(publisher_params)
            publisher.push = lambda *args, **kwargs: print('跨项目虚拟publisher不支持push方法，请使用publish来发布消息')
            cls.queue_name__cross_project_publisher_map[key] = publisher
        return cls.queue_name__cross_project_publisher_map[key]

    @classmethod
    def push(cls, queue_name, *args, **kwargs):
        """push发布消息到消息队列 ;
        """
        cls.get_or_create_booster_by_queue_name(queue_name).push(*args, **kwargs)

    @classmethod
    def publish(cls, queue_name, msg):
        """publish发布消息到消息队列;
        """
        cls.get_or_create_booster_by_queue_name(queue_name).publish(msg)

    @classmethod
    def consume_queues(cls, *queue_names):
        """
        启动多个消息队列名的消费,多个函数队列在当前同一个进程内启动消费.
        这种方式节约总的内存,但无法利用多核cpu
        """
        for queue_name in queue_names:
            cls.get_booster(queue_name).consume()
        ctrl_c_recv()

    consume = consume_queues

    @classmethod
    def consume_all_queues(cls, block=True):
        """
        启动所有消息队列名的消费,无需一个一个函数亲自 funxx.consume()来启动,多个函数队列在当前同一个进程内启动消费.
        这种方式节约总的内存,但无法利用多核cpu
        """
        for queue_name in cls.get_all_queues():
            cls.get_booster(queue_name).consume()
        if block:
            ctrl_c_recv()

    consume_all = consume_all_queues

    @classmethod
    def multi_process_consume_queues(cls, **queue_name__process_num):
        """
        启动多个消息队列名的消费,传递队列名和进程数,每个队列启动n个单独的消费进程;
        这种方式总的内存使用高,但充分利用多核cpu
        例如 multi_process_consume_queues(queue1=2,queue2=3) 表示启动2个进程消费queue1,启动3个进程消费queue2
        """
        for queue_name, process_num in queue_name__process_num.items():
            cls.get_booster(queue_name).multi_process_consume(process_num)
        ctrl_c_recv()

    mp_consume = multi_process_consume_queues

    @classmethod
    def consume_group(cls, booster_group:str,block=False):
        """
        根据@boost装饰器的 booster_group消费分组名字,启动多个消费函数;
        """
        if booster_group is None:
            raise ValueError('booster_group 不能为None')
        need_consume_queue_names = []
        for queue_name in cls.get_all_queues():
            booster= cls.get_or_create_booster_by_queue_name(queue_name)
            if booster.boost_params.booster_group == booster_group:
                need_consume_queue_names.append(queue_name)
        flogger.info(f'according to booster_group:{booster_group} ,start consume queues: {need_consume_queue_names}')
        for queue_name in need_consume_queue_names:
            cls.get_or_create_booster_by_queue_name(queue_name).consume()
        if block:
            ctrl_c_recv()

    @classmethod
    def multi_process_consume_group(cls, booster_group:str, process_num=1):
        """
        根据@boost装饰器的 booster_group消费分组名字,启动多个消费函数;
        """
        for _ in range(process_num):
            Process(target=cls.consume_group,args=(booster_group,True)).start()
    
    mp_consume_group = multi_process_consume_group
            
    @classmethod
    def multi_process_consume_all_queues(cls, process_num=1):
        """
        启动所有消息队列名的消费,无需指定队列名,每个队列启动n个单独的消费进程;
        这种方式总的内存使用高,但充分利用多核cpu
        """
        for queue_name in cls.get_all_queues():
            cls.get_booster(queue_name).multi_process_consume(process_num)
        ctrl_c_recv()

    mp_consume_all = multi_process_consume_all_queues
    