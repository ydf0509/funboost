# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2021/04/18 0008 13:32
# import time
import os

import traceback
from pathlib import Path
from kombu.entity import Exchange, Queue
from kombu.connection import Connection
from kombu.transport.virtual.base import Channel
from kombu.transport.virtual.base import Message
from kombu.transport import redis
from kombu.transport.redis import Empty

from nb_log import get_logger

from funboost import funboost_config_deafult
from funboost.consumers.base_consumer import AbstractConsumer


def patch_kombu_redis000():
    # 这个也可以，代码长了一点。
    """
    给kombu的redis 模式打猴子补丁
    kombu有bug，redis中间件 unnacked 中的任务即使客户端掉线了或者突然关闭脚本中正在运行的任务，也永远不会被重新消费。
    这个很容易验证那个测试，把消费函数写成sleep 100秒，启动20秒后把脚本关掉，取出来的任务在 unacked 队列中那个永远不会被确认消费，也不会被重新消费。
    """

    # noinspection PyUnusedLocal
    def monkey_get(self, callback, timeout=None):
        self._in_protected_read = True
        try:
            for channel in self._channels:
                if channel.active_queues:  # BRPOP mode?
                    if channel.qos.can_consume():
                        self._register_BRPOP(channel)
                if channel.active_fanout_queues:  # LISTEN mode?
                    self._register_LISTEN(channel)

            events = self.poller.poll(timeout)
            if events:
                for fileno, event in events:
                    ret = None
                    # noinspection PyBroadException,PyUnusedLocal
                    try:
                        ret = self.handle_event(fileno, event)  # 主要是这行改了加了try，不然会raise empty 导致self.maybe_restore_messages()没执行
                    except BaseException as e:
                        pass
                        # print(traceback.format_exc())
                        # print(e)
                    if ret:
                        return
            # - no new data, so try to restore messages.
            # - reset active redis commands.
            self.maybe_restore_messages()
            raise Empty()
            # raise Exception('kombu.five.Empty')
        finally:
            self._in_protected_read = False
            # print(self.after_read)
            while self.after_read:
                try:
                    fun = self.after_read.pop()
                except KeyError:
                    break
                else:
                    fun()

    redis.MultiChannelPoller.get = monkey_get


def patch_kombu_redis():
    """
    给kombu的redis 模式打猴子补丁
    kombu有bug，redis中间件 unnacked 中的任务即使客户端掉线了或者突然关闭脚本中正在运行的任务，也永远不会被重新消费。
    这个很容易验证那个测试，把消费函数写成sleep 100秒，启动20秒后把脚本关掉，取出来的任务在 unacked 队列中那个永远不会被确认消费，也不会被重新消费。
    """

    redis_multichannelpoller_get_raw = redis.MultiChannelPoller.get

    # noinspection PyUnusedLocal
    def monkey_get(self, callback, timeout=None):
        try:
            redis_multichannelpoller_get_raw(self, callback, timeout)
        except Empty:
            self.maybe_restore_messages()
            raise Empty()

    redis.MultiChannelPoller.get = monkey_get


patch_kombu_redis()

''' kombu 能支持的消息队列中间件有如下，可以查看 D:\ProgramData\Miniconda3\Lib\site-packages\kombu\transport\__init__.py 文件。

TRANSPORT_ALIASES = {
    'amqp': 'kombu.transport.pyamqp:Transport',
    'amqps': 'kombu.transport.pyamqp:SSLTransport',
    'pyamqp': 'kombu.transport.pyamqp:Transport',
    'librabbitmq': 'kombu.transport.librabbitmq:Transport',
    'memory': 'kombu.transport.memory:Transport',
    'redis': 'kombu.transport.redis:Transport',
    'rediss': 'kombu.transport.redis:Transport',
    'SQS': 'kombu.transport.SQS:Transport',
    'sqs': 'kombu.transport.SQS:Transport',
    'mongodb': 'kombu.transport.mongodb:Transport',
    'zookeeper': 'kombu.transport.zookeeper:Transport',
    'sqlalchemy': 'kombu.transport.sqlalchemy:Transport',
    'sqla': 'kombu.transport.sqlalchemy:Transport',
    'SLMQ': 'kombu.transport.SLMQ.Transport',
    'slmq': 'kombu.transport.SLMQ.Transport',
    'filesystem': 'kombu.transport.filesystem:Transport',
    'qpid': 'kombu.transport.qpid:Transport',
    'sentinel': 'kombu.transport.redis:SentinelTransport',
    'consul': 'kombu.transport.consul:Transport',
    'etcd': 'kombu.transport.etcd:Transport',
    'azurestoragequeues': 'kombu.transport.azurestoragequeues:Transport',
    'azureservicebus': 'kombu.transport.azureservicebus:Transport',
    'pyro': 'kombu.transport.pyro:Transport'
}

'''


# noinspection PyAttributeOutsideInit
class KombuConsumer(AbstractConsumer, ):
    """
    使用kombu作为中间件,这个能直接一次性支持很多种小众中间件，但性能很差，除非是分布式函数调度框架没实现的中间件种类用户才可以用这种，用户也可以自己对比性能。
    """

    BROKER_KIND = 15
    BROKER_EXCLUSIVE_CONFIG_DEFAULT = {'kombu_url': None,  # 如果这里也配置了kombu_url,则优先使用跟着你的kombu_url，否则使用funboost_config. KOMBU_URL
                                       'transport_options': {},  # transport_options是kombu的transport_options 。
                                       'prefetch_count': 500
                                       }
    # prefetch_count 是预获取消息数量
    ''' transport_options是kombu的transport_options 。 
       例如使用kombu使用redis作为中间件时候，可以设置 visibility_timeout 来决定消息取出多久没有ack，就自动重回队列。
       kombu的每个中间件能设置什么 transport_options 可以看 kombu的源码中的 transport_options 参数说明。

例如kombu redis的Transport Options 说明
D:\ProgramData\Miniconda3\envs\py311\Lib\site-packages\kombu\transport\redis.py

Transport Options
=================
* ``sep``
* ``ack_emulation``: (bool) If set to True transport will
  simulate Acknowledge of AMQP protocol.
* ``unacked_key``
* ``unacked_index_key``
* ``unacked_mutex_key``
* ``unacked_mutex_expire``
* ``visibility_timeout``
* ``unacked_restore_limit``
* ``fanout_prefix``
* ``fanout_patterns``
* ``global_keyprefix``: (str) The global key prefix to be prepended to all keys
  used by Kombu
* ``socket_timeout``
* ``socket_connect_timeout``
* ``socket_keepalive``
* ``socket_keepalive_options``
* ``queue_order_strategy``
* ``max_connections``
* ``health_check_interval``
* ``retry_on_timeout``
* ``priority_steps``


      '''

    def custom_init(self):
        self.kombu_url = self.broker_exclusive_config['kombu_url'] or funboost_config_deafult.KOMBU_URL
        self._middware_name = self.kombu_url.split(":")[0]
        logger_name = f'{self._logger_prefix}{self.__class__.__name__}--{self._middware_name}--{self._queue_name}'
        self.logger = get_logger(logger_name, log_level_int=self._log_level,
                                 log_filename=f'{logger_name}.log' if self._create_logger_file else None,
                                 formatter_template=funboost_config_deafult.NB_LOG_FORMATER_INDEX_FOR_CONSUMER_AND_PUBLISHER,
                                 )  #
        if self.kombu_url.startswith('filesystem://'):
            self._create_msg_file_dir()

    def _create_msg_file_dir(self):
        os.makedirs(self.broker_exclusive_config['transport_options']['data_folder_in'], exist_ok=True)
        os.makedirs(self.broker_exclusive_config['transport_options']['data_folder_out'], exist_ok=True)
        processed_folder = self.broker_exclusive_config['transport_options'].get('processed_folder', None)
        if processed_folder:
            os.makedirs(processed_folder, exist_ok=True)

    # noinspection DuplicatedCode
    def _shedual_task(self):  # 这个倍while 1 启动的，会自动重连。
        def callback(body: dict, message: Message):
            # print(type(body),body,type(message),message)
            self._print_message_get_from_broker('kombu', body)
            # self.logger.debug(f""" 从 kombu {self._middware_name} 中取出的消息是 {body}""")
            kw = {'body': body, 'message': message, }
            self._submit_task(kw)

        self.exchange = Exchange('funboost_exchange', 'direct', durable=True)
        self.queue = Queue(self._queue_name, exchange=self.exchange, routing_key=self._queue_name, auto_delete=False, no_ack=False)
        # https://docs.celeryq.dev/projects/kombu/en/stable/reference/kombu.html?highlight=visibility_timeout#kombu.Connection 每种中间件的transport_options不一样。
        self.conn = Connection(self.kombu_url, transport_options=self.broker_exclusive_config['transport_options'])
        self.queue(self.conn).declare()
        with self.conn.Consumer(self.queue, callbacks=[callback], no_ack=False, prefetch_count=self.broker_exclusive_config['prefetch_count']) as consumer:
            # Process messages and handle events on all channels
            channel = consumer.channel  # type:Channel
            channel.body_encoding = 'no_encode'  # 这里改了编码，存到中间件的参数默认把消息base64了，我觉得没必要不方便查看消息明文。
            while True:
                self.conn.drain_events()

    def _confirm_consume(self, kw):
        pass  # redis没有确认消费的功能。
        kw['message'].ack()

    def _requeue(self, kw):
        kw['message'].requeue()
