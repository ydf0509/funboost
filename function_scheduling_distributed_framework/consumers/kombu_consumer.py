# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2019/8/8 0008 13:32
import json
# import time
from kombu import Connection, Exchange, Queue, Consumer, Producer
from kombu.transport.virtual.base import Channel
import kombu
from nb_log import LogManager

from function_scheduling_distributed_framework.consumers.base_consumer import AbstractConsumer
from function_scheduling_distributed_framework import frame_config


class KombuConsumer(AbstractConsumer, ):
    """

    """
    BROKER_KIND = 15

    def custom_init(self):
        logger_name = f'{self._logger_prefix}{self.__class__.__name__}--{self._queue_name}--{frame_config.KOMBU_URL.split(":")[0]}'
        self.logger = LogManager(logger_name).get_logger_and_add_handlers(self._log_level,
                                                                          log_filename=f'{logger_name}.log' if self._create_logger_file else None,
                                                                          formatter_template=frame_config.NB_LOG_FORMATER_INDEX_FOR_CONSUMER_AND_PUBLISHER,
                                                                          )  #

    # noinspection DuplicatedCode
    def _shedual_task(self): # 这个倍while 1 启动的，会自动重连。
        def callback(body:dict, message:kombu.transport.virtual.base.Message):
            print(type(body),body,type(message),message)
            kw = {'body': body, 'message': message, }
            self._submit_task(kw)

        self.exchange = Exchange('distributed_framework_exchange', 'direct', durable=True)
        self.queue = Queue(self._queue_name, exchange=self.exchange, routing_key=self._queue_name)
        self.conn = Connection(frame_config.KOMBU_URL)
        self.queue(self.conn).declare()
        # self.producer = self.conn.Consumer(serializer='json')
        # self.channel = self.producer.channel  # type: Channel
        #
        # self.conn = Connection(frame_config.KOMBU_URL)
        # # self.queue(self.conn).declare()
        # self.channel = self.conn.channel()  # type: Channel
        # # self.channel.exchange_declare(exchange='distributed_framework_exchange', durable=True, type='direct')
        # self.queue = self.channel.queue_declare(queue=self._queue_name, durable=True)
        with  self.conn.Consumer(self.queue,callbacks=[callback],no_ack=False)  as consumer:
            # Process messages and handle events on all channels
            while True:
                self.conn.drain_events()



    def _confirm_consume(self, kw):
        pass  # redis没有确认消费的功能。
        kw['message'].ack()

    def _requeue(self, kw):
        kw['message'].requeue()
