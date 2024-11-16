# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2021/4/18 0008 13:32


import json
import threading
from collections import defaultdict, OrderedDict
# noinspection PyPackageRequirements
import time

# noinspection PyPackageRequirements
# pip install kafka-python==2.0.2

from funboost.consumers.base_consumer import AbstractConsumer
from funboost.core.lazy_impoter import KafkaPythonImporter
from funboost.funboost_config_deafult import BrokerConnConfig
from confluent_kafka.cimpl import TopicPartition
from confluent_kafka import Consumer as ConfluentConsumer  # 这个包在win下不好安装，用户用这个中间件的时候自己再想办法安装。win用户需要安装c++ 14.0以上环境。


class KafkaConsumerManuallyCommit(AbstractConsumer):
    """
    confluent_kafla作为中间件实现的。操作kafka中间件的速度比kafka-python快10倍。
    这个是自动间隔2秒的手动确认，由于是异步在并发池中并发消费，可以防止强制关闭程序造成正在运行的任务丢失，比自动commit好。
    如果使用kafka，推荐这个。

    可以让消费函数内部 sleep 60秒，突然停止消费代码，使用 kafka-consumer-groups.sh --bootstrap-server 127.0.0.1:9092 --describe --group frame_group 来证实自动确认消费和手动确认消费的区别。
    """

    BROKER_EXCLUSIVE_CONFIG_DEFAULT = {'group_id': 'funboost_confluent_kafka', 'auto_offset_reset': 'earliest'}

    def custom_init(self):
        self._lock_for_operate_offset_dict = threading.Lock()

    def _shedual_task(self):

        try:
            admin_client = KafkaPythonImporter().KafkaAdminClient(bootstrap_servers=BrokerConnConfig.KAFKA_BOOTSTRAP_SERVERS)
            admin_client.create_topics([KafkaPythonImporter().NewTopic(self._queue_name, 10, 1)])
            # admin_client.create_partitions({self._queue_name: NewPartitions(total_count=16)})
        except KafkaPythonImporter().TopicAlreadyExistsError:
            pass

        self._producer = KafkaPythonImporter().KafkaProducer(bootstrap_servers=BrokerConnConfig.KAFKA_BOOTSTRAP_SERVERS)
        # consumer 配置 https://github.com/edenhill/librdkafka/blob/master/CONFIGURATION.md
        self._confluent_consumer = ConfluentConsumer({
            'bootstrap.servers': ','.join(BrokerConnConfig.KAFKA_BOOTSTRAP_SERVERS),
            'group.id': self.consumer_params.broker_exclusive_config["group_id"],
            'auto.offset.reset': self.consumer_params.broker_exclusive_config["auto_offset_reset"],
            'enable.auto.commit': False
        })
        self._confluent_consumer.subscribe([self._queue_name])

        self._recent_commit_time = time.time()
        self._partion__offset_consume_status_map = defaultdict(OrderedDict)
        while 1:
            msg = self._confluent_consumer.poll(timeout=10)
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
            kw = {'partition': msg.partition(), 'offset': msg.offset(), 'body': msg.value()}  # noqa
            if self.consumer_params.is_show_message_get_from_broker:
                self.logger.debug(
                    f'从kafka的 [{self._queue_name}] 主题,分区 {msg.partition()} 中 的 offset {msg.offset()} 取出的消息是：  {msg.value()}')  # noqa
            self._submit_task(kw)

            # kw = {'consumer': consumer, 'message': message, 'body': json.loads(message.value)}
            # self._submit_task(kw)

    def _manually_commit(self):
        """
        kafka要求消费线程数量和分区数量是一对一或一对多，不能多对一，消息并发处理收到分区数量的限制，这种是支持超高线程数量消费，所以commit非常复杂。
        因为这种是可以支持单分区200线程消费，消费本身和拉取kafka任务不在同一个线程，而且可能offset较大的比offset较小的任务先完成，
        每隔2秒对1组offset，对连续消费状态是1的最大offset进行commit
        :return:
        """
        with self._lock_for_operate_offset_dict:
            if time.time() - self._recent_commit_time > 2:
                partion_max_consumed_offset_map = dict()
                to_be_remove_from_partion_max_consumed_offset_map = defaultdict(list)
                for partion, offset_consume_status in self._partion__offset_consume_status_map.items():
                    sorted_keys = sorted(offset_consume_status.keys())
                    offset_consume_status_ordered = {key: offset_consume_status[key] for key in sorted_keys}
                    max_consumed_offset = None

                    for offset, consume_status in offset_consume_status_ordered.items():
                        # print(offset,consume_status)
                        if consume_status == 1:
                            max_consumed_offset = offset
                            to_be_remove_from_partion_max_consumed_offset_map[partion].append(offset)
                        else:
                            break
                    if max_consumed_offset is not None:
                        partion_max_consumed_offset_map[partion] = max_consumed_offset
                # self.logger.info(partion_max_consumed_offset_map)
                # TopicPartition
                offsets = list()
                for partion, max_consumed_offset in partion_max_consumed_offset_map.items():
                    # print(partion,max_consumed_offset)
                    offsets.append(TopicPartition(topic=self._queue_name, partition=partion, offset=max_consumed_offset + 1))
                if len(offsets):
                    self._confluent_consumer.commit(offsets=offsets, asynchronous=False)
                self._recent_commit_time = time.time()
                for partion, offset_list in to_be_remove_from_partion_max_consumed_offset_map.items():
                    for offset in offset_list:
                        del self._partion__offset_consume_status_map[partion][offset]

    def _confirm_consume(self, kw):
        with self._lock_for_operate_offset_dict:
            self._partion__offset_consume_status_map[kw['partition']][kw['offset']] = 1
            # print(self._partion__offset_consume_status_map)

    def _requeue(self, kw):
        self._producer.send(self._queue_name, json.dumps(kw['body']).encode())


class SaslPlainKafkaConsumer(KafkaConsumerManuallyCommit):

    def _shedual_task(self):

        try:
            admin_client = KafkaPythonImporter().KafkaAdminClient(
                **BrokerConnConfig.KFFKA_SASL_CONFIG)
            admin_client.create_topics([KafkaPythonImporter().NewTopic(self._queue_name, 10, 1)])
            # admin_client.create_partitions({self._queue_name: NewPartitions(total_count=16)})
        except KafkaPythonImporter().TopicAlreadyExistsError:
            pass

        self._producer = KafkaPythonImporter().KafkaProducer(
            **BrokerConnConfig.KFFKA_SASL_CONFIG)
        # consumer 配置 https://github.com/edenhill/librdkafka/blob/master/CONFIGURATION.md
        self._confluent_consumer = ConfluentConsumer({
            'bootstrap.servers': ','.join(BrokerConnConfig.KAFKA_BOOTSTRAP_SERVERS),
            'security.protocol': BrokerConnConfig.KFFKA_SASL_CONFIG['security_protocol'],
            'sasl.mechanisms': BrokerConnConfig.KFFKA_SASL_CONFIG['sasl_mechanism'],
            'sasl.username': BrokerConnConfig.KFFKA_SASL_CONFIG['sasl_plain_username'],
            'sasl.password': BrokerConnConfig.KFFKA_SASL_CONFIG['sasl_plain_password'],
            'group.id': self.consumer_params.broker_exclusive_config["group_id"],
            'auto.offset.reset': self.consumer_params.broker_exclusive_config["auto_offset_reset"],
            'enable.auto.commit': False,
            "enable.auto.offset.store": False,
        })
        self._confluent_consumer.subscribe([self._queue_name])

        self._recent_commit_time = time.time()
        self._partion__offset_consume_status_map = defaultdict(OrderedDict)

        while 1:
            msg = self._confluent_consumer.poll(timeout=10)
            self._manually_commit()
            if msg is None:
                continue
            if msg.error():
                print("Consumer error: {}".format(msg.error()))
                continue
            # msg的类型  https://docs.confluent.io/platform/current/clients/confluent-kafka-python/html/index.html#message
            # value()  offset() partition()
            # print('Received message: {}'.format(msg.value().decode('utf-8'))) # noqa
            self._partion__offset_consume_status_map[msg.partition(
            )][msg.offset()] = 0
            kw = {'partition': msg.partition(), 'offset': msg.offset(), 'body': msg.value()}  # noqa
            if self.consumer_params.is_show_message_get_from_broker:
                self.logger.debug(
                    f'从kafka的 [{self._queue_name}] 主题,分区 {msg.partition()} 中 的 offset {msg.offset()} 取出的消息是：  {msg.value()}')  # noqa
            self._submit_task(kw)

    def __exit__(self):
        self._confluent_consumer.close()
