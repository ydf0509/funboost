# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2019/8/8 0008 13:32
import json

# noinspection PyPackageRequirements
from kafka import KafkaConsumer as OfficialKafkaConsumer, KafkaProducer

from function_scheduling_distributed_framework.consumers.base_consumer import AbstractConsumer
from function_scheduling_distributed_framework import frame_config
from nb_log import LogManager

LogManager('kafka').get_logger_and_add_handlers(20)


class KafkaConsumer(AbstractConsumer):
    """
    kafla作为中间件实现的。
    """
    BROKER_KIND = 8

    def _shedual_task(self):
        self._producer = KafkaProducer(bootstrap_servers=frame_config.KAFKA_BOOTSTRAP_SERVERS)
        consumer = OfficialKafkaConsumer(self._queue_name, bootstrap_servers=frame_config.KAFKA_BOOTSTRAP_SERVERS,
                                         group_id=f'frame_group66-{self._queue_name}', enable_auto_commit=True,
                                         auto_offset_reset='earliest')

        #  auto_offset_reset (str): A policy for resetting offsets on
        #             OffsetOutOfRange errors: 'earliest' will move to the oldest
        #             available message, 'latest' will move to the most recent. Any
        #             other value will raise the exception. Default: 'latest'.       默认是latest

        # kafka 的 group_id


        # REMIND 由于是很高数量的并发消费，线程很多，分区很少，这里设置成自动确认消费了，否则多线程提交同一个分区的偏移量导致超前错乱，就没有意义了。
        # REMIND 要保证很高的可靠性和一致性，请用rabbitmq。
        # REMIND 好处是并发高。topic像翻书一样，随时可以设置偏移量重新消费。多个分组消费同一个主题，每个分组对相同主题的偏移量互不干扰。

        for message in consumer:
            # 注意: message ,value都是原始的字节数据，需要decode
            self.logger.debug(
                f'从kafka的 [{message.topic}] 主题,分区 {message.partition} 中 取出的消息是：  {message.value.decode()}')
            kw = {'consumer': consumer, 'message': message, 'body': json.loads(message.value)}
            self._submit_task(kw)

    def _confirm_consume(self, kw):
        pass  # 使用kafka的自动commit模式。

    def _requeue(self, kw):
        self._producer.send(self._queue_name, json.dumps(kw['body']).encode())

