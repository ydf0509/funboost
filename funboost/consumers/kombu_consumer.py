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


from funboost.consumers.base_consumer import AbstractConsumer
from funboost.funboost_config_deafult import BrokerConnConfig



has_patch_kombu_redis = False


def patch_kombu_redis():
    """
    给kombu的redis 模式打猴子补丁
    kombu有bug，redis中间件 unnacked 中的任务即使客户端掉线了或者突然关闭脚本中正在运行的任务，也永远不会被重新消费。
    这个很容易验证那个测试，把消费函数写成sleep 100秒，启动20秒后把脚本关掉，取出来的任务在 unacked 队列中那个永远不会被确认消费，也不会被重新消费。
    """
    global has_patch_kombu_redis
    if not has_patch_kombu_redis:
        redis_multichannelpoller_get_raw = redis.MultiChannelPoller.get

        # noinspection PyUnusedLocal
        def monkey_get(self, callback, timeout=None):
            try:
                redis_multichannelpoller_get_raw(self, callback, timeout)
            except Empty:
                self.maybe_restore_messages()
                raise Empty()

        redis.MultiChannelPoller.get = monkey_get
        has_patch_kombu_redis = True


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


    def custom_init(self):
        self.kombu_url = self.consumer_params.broker_exclusive_config['kombu_url'] or BrokerConnConfig.KOMBU_URL
        self._middware_name = self.kombu_url.split(":")[0]
        # logger_name = f'{self.consumer_params.logger_prefix}{self.__class__.__name__}--{self._middware_name}--{self._queue_name}'
        # self.logger = get_logger(logger_name, log_level_int=self.consumer_params.log_level,
        #                          _log_filename=f'{logger_name}.log' if self.consumer_params.create_logger_file else None,
        #                          formatter_template=FunboostCommonConfig.NB_LOG_FORMATER_INDEX_FOR_CONSUMER_AND_PUBLISHER,
        #                          )  #
        if self.kombu_url.startswith('filesystem://'):
            self._create_msg_file_dir()

    def _create_msg_file_dir(self):
        os.makedirs(self.consumer_params.broker_exclusive_config['transport_options']['data_folder_in'], exist_ok=True)
        os.makedirs(self.consumer_params.broker_exclusive_config['transport_options']['data_folder_out'], exist_ok=True)
        processed_folder = self.consumer_params.broker_exclusive_config['transport_options'].get('processed_folder', None)
        if processed_folder:
            os.makedirs(processed_folder, exist_ok=True)

    # noinspection DuplicatedCode
    def _shedual_task(self):  # 这个倍while 1 启动的，会自动重连。
        patch_kombu_redis()

        def callback(body: dict, message: Message):
            # print(type(body),body,type(message),message)
            # self.logger.debug(f""" 从 kombu {self._middware_name} 中取出的消息是 {body}""")
            kw = {'body': body, 'message': message, }
            self._submit_task(kw)

        self.exchange = Exchange('funboost_exchange', 'direct', durable=True)
        self.queue = Queue(self._queue_name, exchange=self.exchange, routing_key=self._queue_name, auto_delete=False, no_ack=False)
        # https://docs.celeryq.dev/projects/kombu/en/stable/reference/kombu.html?highlight=visibility_timeout#kombu.Connection 每种中间件的transport_options不一样。
        self.conn = Connection(self.kombu_url, transport_options=self.consumer_params.broker_exclusive_config['transport_options'])
        self.queue(self.conn).declare()
        with self.conn.Consumer(self.queue, callbacks=[callback], no_ack=False, prefetch_count=self.consumer_params.broker_exclusive_config['prefetch_count']) as consumer:
            # Process messages and handle events on all channels
            channel = consumer.channel  # type:Channel
            channel.body_encoding = 'no_encode'  # 这里改了编码，存到中间件的参数默认把消息base64了，我觉得没必要不方便查看消息明文。
            while True:
                self.conn.drain_events()

    def _confirm_consume(self, kw):
        kw['message'].ack()

    def _requeue(self, kw):
        kw['message'].requeue()
