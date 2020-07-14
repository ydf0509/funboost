from functools import update_wrapper
from multiprocessing import Process
from typing import List

# noinspection PyUnresolvedReferences
import apscheduler
from function_scheduling_distributed_framework.set_frame_config import patch_frame_config, show_frame_config

# import frame_config
from function_scheduling_distributed_framework.consumers.base_consumer import ExceptionForRequeue, ExceptionForRetry, \
    AbstractConsumer, ConsumersManager, FunctionResultStatusPersistanceConfig
from function_scheduling_distributed_framework.publishers.base_publisher import PriorityConsumingControlConfig
from function_scheduling_distributed_framework.factories.publisher_factotry import get_publisher
from function_scheduling_distributed_framework.factories.consumer_factory import get_consumer
# noinspection PyUnresolvedReferences
from function_scheduling_distributed_framework.utils import nb_print, patch_print, LogManager


def run_many_consumer_by_init_params(consumer_init_params_list: List[dict]):
    for consumer_init_params in consumer_init_params_list:
        get_consumer(**consumer_init_params).start_consuming_message()
    ConsumersManager.join_all_consumer_shedual_task_thread()


def run_many_consumer_with_multi_process(consumer_init_params_list: List[dict], process_num=1):
    """
    如果要开多进程，建议使用这个函数。不需要自己再调用Process，以免再linux上忘了加 ConsumersManager.join_all_consumer_shedual_task_thread()
     此处传init参数而不是conusmer对象本身，是由于一些属性的类型(例如threading.Lock类型)不可以被picke序列化，在windows中开多进程会出错。
     if __name__ == '__main__':
        run_many_consumer_with_multi_process([consumer1.init_params,consumer2.init_params],4)
    """
    [Process(target=run_many_consumer_by_init_params, args=(consumer_init_params_list,)).start() for _ in range(process_num)]


def task_deco(queue_name, **consumer_init_kwargs):
    """
    :param queue_name:
    :param consumer_init_kwargs:
    :return:

    装饰器方式注册消费任务，如果有人过于喜欢装饰器方式，例如celery 装饰器方式的任务注册，觉得黑科技，那就可以使用这个装饰器。
    此种方式不利于ide代码自动补全,被装饰的函数自身自动添加了几个方法,但不能被ide补全。所以请牢记几个方法名，
    假如你的函数名是f,那么可以调用f.publish或f.pub来发布任务。调用f.start_consuming_message 或 f.consume 或 f.start消费任务。


    装饰器版，使用方式例如：
    '''
    @task_deco('queue_test_f01', qps=0.2, broker_kind=2)
    def f(a, b):
        print(a + b)

    for i in range(10, 20):
        f.pub(dict(a=i, b=i * 2))
    f.consume()
    '''

    常规方式，使用方式如下
    '''
    def f(a, b):
        print(a + b)

    consumer = get_consumer('queue_test_f01', consuming_function=f,qps=0.2, broker_kind=2) # 需要手动指定consuming_function入参的值。
    for i in range(10, 20):
        consumer.publisher_of_same_queue.publish(dict(a=i, b=i * 2))
    consumer.start_consuming_message()
    '''

    装饰器版本的 task_deco 入参 和 get_consumer 入参99%一致，唯一不同的是 装饰器版本加在了函数上自动知道消费函数了，所以不需要传consuming_function参数。
    """
    # 装饰器版本能够自动知道消费函数，防止task_deco按照get_consumer的入参重复传参了consuming_function。
    if consumer_init_kwargs and 'consuming_function' in consumer_init_kwargs:
        consumer_init_kwargs.pop('consuming_function')

    def _deco(func):
        consumer = get_consumer(queue_name, consuming_function=func, **consumer_init_kwargs)
        func.consumer = consumer
        # 下面这些连等主要是由于元编程造成的不能再ide下智能补全，参数太长很难手动拼写出来
        func.start_consuming_message = func.consume = func.start = consumer.start_consuming_message
        func.publisher = consumer.publisher_of_same_queue
        func.publish = func.pub = consumer.publisher_of_same_queue.publish

        # @functools.wraps(func)
        def __deco(*args, **kwargs):
            return func(*args, **kwargs)

        # return __deco   # 两种方式都可以
        return update_wrapper(__deco, func)

    return _deco
