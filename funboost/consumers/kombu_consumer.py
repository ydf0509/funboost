# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2021/04/18 0008 13:32
# import time
import kombu
from kombu import Connection, Exchange, Queue
from kombu.transport.virtual.base import Channel
from nb_log import LogManager

from funboost import funboost_config_deafult
from funboost.consumers.base_consumer import AbstractConsumer


def patch_kombu_redis():
    """
    给kombu的redis 模式打猴子补丁
    kombu有bug，redis中间件 unnacked 中的任务即使客户端掉线了后者突然关闭脚本中正在运行的任务，也永远不会被重新消费。
    这个很容易验证那个测试，把消费函数写成sleep 100秒，启动20秒后把脚本关掉，取出来的任务在 unacked 队列中那个永远不会被确认消费，也不会被重新消费。
    """
    from kombu.transport import redis
    # from kombu.five import Empty  #

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
                        ret = self.handle_event(fileno, event)
                    except Exception as e:
                        pass
                    if ret:
                        return
            # - no new data, so try to restore messages.
            # - reset active redis commands.
            self.maybe_restore_messages()
            # raise Empty()
            # raise Exception('kombu.five.Empty')
        finally:
            self._in_protected_read = False
            while self.after_read:
                try:
                    fun = self.after_read.pop()
                except KeyError:
                    break
                else:
                    fun()

    redis.MultiChannelPoller.get = monkey_get


# noinspection PyAttributeOutsideInit
class KombuConsumer(AbstractConsumer, ):
    """
    使用kombu作为中间件,这个能直接一次性支持很多种小众中间件，但性能很差，除非是分布式函数调度框架没实现的中间件种类用户才可以用这种，用户也可以自己对比性能。
    """

    BROKER_KIND = 15

    def custom_init(self):
        self._middware_name = funboost_config_deafult.KOMBU_URL.split(":")[0]
        logger_name = f'{self._logger_prefix}{self.__class__.__name__}--{self._middware_name}--{self._queue_name}'
        self.logger = LogManager(logger_name).get_logger_and_add_handlers(self._log_level,
                                                                          log_filename=f'{logger_name}.log' if self._create_logger_file else None,
                                                                          formatter_template=funboost_config_deafult.NB_LOG_FORMATER_INDEX_FOR_CONSUMER_AND_PUBLISHER,
                                                                          )  #
        patch_kombu_redis()

    # noinspection DuplicatedCode
    def _shedual_task(self):  # 这个倍while 1 启动的，会自动重连。
        def callback(body: dict, message: kombu.transport.virtual.base.Message):
            # print(type(body),body,type(message),message)
            self._print_message_get_from_broker('kombu', body)
            # self.logger.debug(f""" 从 kombu {self._middware_name} 中取出的消息是 {body}""")
            kw = {'body': body, 'message': message, }
            self._submit_task(kw)

        self.exchange = Exchange('funboost_exchange', 'direct', durable=True)
        self.queue = Queue(self._queue_name, exchange=self.exchange, routing_key=self._queue_name, auto_delete=False)
        self.conn = Connection(funboost_config_deafult.KOMBU_URL, transport_options={"visibility_timeout": 600})  # 默认3600秒unacked重回队列
        self.queue(self.conn).declare()
        with self.conn.Consumer(self.queue, callbacks=[callback], no_ack=False, prefetch_count=100) as consumer:
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
