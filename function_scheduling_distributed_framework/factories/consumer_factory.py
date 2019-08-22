# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2019/8/8 0008 13:19
import copy
from collections import Callable

from function_scheduling_distributed_framework.consumers.kafka_consumer import KafkaConsumer
from function_scheduling_distributed_framework.consumers.local_python_queue_consumer import LocalPythonQueueConsumer
from function_scheduling_distributed_framework.consumers.mongomq_consumer import MongoMqConsumer
from function_scheduling_distributed_framework.consumers.nsq_consumer import NsqConsumer
from function_scheduling_distributed_framework.consumers.persist_queue_consumer import PersistQueueConsumer
from function_scheduling_distributed_framework.consumers.rabbitmq_amqpstorm_consumer import RabbitmqConsumerAmqpStorm
from function_scheduling_distributed_framework.consumers.rabbitmq_pika_consumer import RabbitmqConsumer
from function_scheduling_distributed_framework.consumers.rabbitmq_rabbitpy_consumer import RabbitmqConsumerRabbitpy
from function_scheduling_distributed_framework.consumers.redis_consumer import RedisConsumer


def get_consumer(queue_name, *, consuming_function: Callable = None, function_timeout=0, threads_num=50, specify_threadpool=None, concurrent_mode=1,
                 max_retry_times=3, log_level=10, is_print_detail_exception=True, msg_schedule_time_intercal=0.0, msg_expire_senconds=0,
                 logger_prefix='', create_logger_file=True, do_task_filtering=False, is_consuming_function_use_multi_params=True,
                 is_do_not_run_by_specify_time_effect=False, do_not_run_by_specify_time=('10:00:00', '22:00:00'),
                 schedule_tasks_on_main_thread=False, broker_kind=0):
    """
    使用工厂模式再包一层，通过设置数字来生成基于不同中间件或包的consumer。
    :param queue_name:
    :param consuming_function: 处理消息的函数。
    :param function_timeout : 超时秒数，函数运行超过这个时间，则自动杀死函数。为0是不限制。
    :param threads_num:并发数量，协程或线程。由concurrent_mode决定并发种类。
    :param specify_threadpool:使用指定的线程池（协程池），可以多个消费者共使用一个线程池，不为None时候。threads_num失效
    :param concurrent_mode:并发模式，1线程 2gevent 3eventlet
    :param max_retry_times: 最大自动重试次数，当函数发生错误，立即自动重试运行n次，对一些特殊不稳定情况会有效果。
    可以在函数中主动抛出重试的异常ExceptionForRetry，框架也会立即自动重试。 主动抛出ExceptionForRequeue异常，则当前消息会重返中间件。
    :param log_level:框架的日志级别。
    :param is_print_detail_exception:是否打印详细的堆栈错误。为0则打印简略的错误占用控制台屏幕行数少。
    :param msg_schedule_time_intercal:消息调度的时间间隔，用于控频的关键。
    :param msg_expire_senconds:消息过期时间，为0永不过期，为10则代表，10秒之前发布的任务如果现在才轮到消费则丢弃任务。
    :param logger_prefix: 日志前缀，可使不同的消费者生成不同的日志
    :param create_logger_file : 是否创建文件日志
    :param do_task_filtering :是否执行基于函数参数的任务过滤
    :param is_consuming_function_use_multi_params  函数的参数是否是传统的多参数，不为单个body字典表示多个参数。
    :param is_do_not_run_by_specify_time_effect :是否使不运行的时间段生效
    :param do_not_run_by_specify_time   :不运行的时间段
    :param schedule_tasks_on_main_thread :直接在主线程调度任务，意味着不能直接在当前主线程同时开启两个消费者。
    :param broker_kind:中间件种类,。 0 使用pika链接mq，2使用redis，3使用python内置Queue,5使用mongo，6使用sqlite。7使用nsq，8使用kafka。
    :return
    """
    all_kwargs = copy.copy(locals())
    all_kwargs.pop('broker_kind')
    if broker_kind == 0:
        return RabbitmqConsumer(**all_kwargs)
    elif broker_kind == 1:
        return RabbitmqConsumerRabbitpy(**all_kwargs)
    elif broker_kind == 2:
        return RedisConsumer(**all_kwargs)
    elif broker_kind == 3:
        return LocalPythonQueueConsumer(**all_kwargs)
    elif broker_kind == 4:
        return RabbitmqConsumerAmqpStorm(**all_kwargs)
    elif broker_kind == 5:
        return MongoMqConsumer(**all_kwargs)
    elif broker_kind == 6:
        return PersistQueueConsumer(**all_kwargs)
    elif broker_kind == 7:
        return NsqConsumer(**all_kwargs)
    elif broker_kind == 8:
        return KafkaConsumer(**all_kwargs)
    else:
        raise ValueError('设置的中间件种类数字不正确')
