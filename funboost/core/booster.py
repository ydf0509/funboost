from __future__ import annotations
import copy
import os
import types
import typing

from funboost.core.loggers import flogger, develop_logger

from functools import wraps

from funboost.core.exceptions import BoostDecoParamsIsOldVersion
from funboost.core.func_params_model import BoosterParams,FunctionResultStatusPersistanceConfig


from funboost.factories.consumer_factory import get_consumer


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
        pydatinc pycharm编程代码补全,请安装 pydantic插件, 在pycharm的  file -> settings -> Plugins -> 输入 pydantic 搜索,点击安装 pydantic 插件.

        强烈建议所有入参放在 BoosterParams() 中,不要直接在BoosterParams之外传参.现在是兼容老的直接在@boost中传参方式.
        """

        """
        '''
        # @boost('queue_test_f01', qps=0.2, broker_kind=2) # 老的入参方式
        @boost(BoosterParams(queue_name='queue_test_f01', qps=0.2, broker_kind=2)) # 新的入参方式,所有入参放在 最流行的三方包 pydantic model BoosterParams 里面.
        def f(a, b):
            print(a + b)

        for i in range(10, 20):
            f.pub(dict(a=i, b=i * 2))
            f.push(i, i * 2)
        f.consume()
        # f.multi_process_conusme(8)             # # 这个是新加的方法，细粒度 线程 协程并发 同时叠加8个进程，速度炸裂。
        '''
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
            flogger.warning(f'''你的 {queue_name} 队列， funboost 40.0版本以后： {BoostDecoParamsIsOldVersion.new_version_change_hint}''')
        boost_params_merge = boost_params.copy()
        boost_params_merge.update_from_dict(kwargs)
        self.boost_params = boost_params_merge
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
        if len(kwargs) == 0 and len(args) == 1 and isinstance(args[0], typing.Callable):
            consuming_function = args[0]
            self.boost_params.consuming_function = consuming_function
            flogger.info(f''' {self.boost_params.queue_name} booster 配置是 {self.boost_params.json_str_value()}''')
            self.consuming_function = consuming_function
            self.is_decorated_as_consume_function = True

            consumer = get_consumer(self.boost_params)
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
            BoostersManager.regist_booster(self.queue_name, self)  # 这一句是登记
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
    """
    消费函数生成Booster对象时候,会自动调用BoostersManager.regist_booster方法,把队列名和入参信息保存到pid_queue_name__booster_map字典中.
    使用这个类,可以创建booster对象,达到无需使用装饰器的目的.
    """

    # pid_queue_name__booster_map字典存放 {(进程id,queue_name):Booster对象}
    pid_queue_name__booster_map = {}  # type: typing.Dict[typing.Tuple[int,str],Booster]

    # queue_name__boost_params_consuming_function_map 字典存放  {queue_name,(@boost的入参字典,@boost装饰的消费函数)}
    queue_name__boost_params_map = {}  # type: typing.Dict[str,BoosterParams]

    @classmethod
    def regist_booster(cls, queue_name: str, booster: Booster):
        """这个是框架在@boost时候自动调用的,无需用户亲自调用"""
        cls.pid_queue_name__booster_map[(os.getpid(), queue_name)] = booster
        cls.queue_name__boost_params_map[queue_name] = booster.boost_params

    @classmethod
    def show_all_boosters(cls):
        queues = []
        for pid_queue_name, booster in cls.pid_queue_name__booster_map.items():
            queues.append(pid_queue_name[1])
            flogger.debug(f'booster: {pid_queue_name[1]}  {booster}')

    @classmethod
    def get_all_queues(cls):
        return cls.queue_name__boost_params_map.keys()

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
