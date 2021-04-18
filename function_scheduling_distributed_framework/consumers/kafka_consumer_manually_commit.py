# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2019/8/8 0008 13:32
import json
from collections import defaultdict, OrderedDict
# noinspection PyPackageRequirements
import time

from confluent_kafka.cimpl import TopicPartition
from kafka import KafkaConsumer as OfficialKafkaConsumer, KafkaProducer
from confluent_kafka import Consumer as ConfluentConsumer

from function_scheduling_distributed_framework.consumers.base_consumer import AbstractConsumer
from function_scheduling_distributed_framework import frame_config
from nb_log import LogManager

LogManager('kafka').get_logger_and_add_handlers(20)


class KafkaConsumerManuallyCommit(AbstractConsumer):
    """
    kafla作为中间件实现的。
    """
    BROKER_KIND = 8

    def _shedual_task(self):
        self._producer = KafkaProducer(bootstrap_servers=frame_config.KAFKA_BOOTSTRAP_SERVERS)
        # consumer 配置 https://github.com/edenhill/librdkafka/blob/master/CONFIGURATION.md
        self._confluent_consumer = ConfluentConsumer({
            'bootstrap.servers': ','.join(frame_config.KAFKA_BOOTSTRAP_SERVERS),
            'group.id': 'mygroup',
            'auto.offset.reset': 'earliest',
            'enable.auto.commit': False
        })
        self._confluent_consumer.subscribe([self._queue_name])

        self._recent_commit_time = time.time()
        self._partion__offset_consume_status_map = defaultdict(OrderedDict)
        while 1:
            msg = self._confluent_consumer.poll()
            self._manually_commit()
            if msg is None:
                continue
            if msg.error():
                print("Consumer error: {}".format(msg.error()))
                continue
            # msg的类型  https://docs.confluent.io/platform/current/clients/confluent-kafka-python/html/index.html#message
            # value()  offset() partition()
            # print('Received message: {}'.format(msg.value().decode('utf-8'))) # noqa
            self._partion__offset_consume_status_map[msg.partition()][msg.offset()] = 0
            kw = {'partition': msg.partition(), 'offset': msg.offset(), 'body': json.loads(msg.value())}  # noqa
            self._submit_task(kw)

            # self.logger.debug(
            #     f'从kafka的 [{message.topic}] 主题,分区 {message.partition} 中 取出的消息是：  {message.value.decode()}')
            # kw = {'consumer': consumer, 'message': message, 'body': json.loads(message.value)}
            # self._submit_task(kw)

    def _manually_commit(self):
        if time.time() - self._recent_commit_time > 2:
            partion_max_consumed_offset_map = dict()
            to_be_remove_from_partion_max_consumed_offset_map = defaultdict(list)
            for partion, offset_consume_status in self._partion__offset_consume_status_map.items():
                max_consumed_offset = 0
                for offset, consume_status in offset_consume_status.items():
                    # print(offset,consume_status)
                    if consume_status == 1:
                        max_consumed_offset = offset
                        to_be_remove_from_partion_max_consumed_offset_map[partion].append(offset)
                    else:
                        break
                if max_consumed_offset:
                    partion_max_consumed_offset_map[partion] = max_consumed_offset
            self.logger.debug(partion_max_consumed_offset_map)
            # TopicPartition
            offsets = list()
            for partion, max_consumed_offset in partion_max_consumed_offset_map.items():
                offsets.append(TopicPartition(topic=self._queue_name, partition=partion, offset=max_consumed_offset + 1))
            self._confluent_consumer.commit(offsets=offsets, asynchronous=False)
            self._recent_commit_time = time.time()
            for partion, offset_list in to_be_remove_from_partion_max_consumed_offset_map.items():
                for offset in offset_list:
                    del self._partion__offset_consume_status_map[partion][offset]

    def _confirm_consume(self, kw):
        self._partion__offset_consume_status_map[kw['partition']][kw['offset']] = 1
        # print(self._partion__offset_consume_status_map)

    def _requeue(self, kw):
        self._producer.send(self._queue_name, json.dumps(kw['body']).encode())
