# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/8 0008 13:32
import json
# noinspection PyPackageRequirements

from funboost.constant import BrokerEnum
from funboost.consumers.base_consumer import AbstractConsumer
from funboost.core.lazy_impoter import KafkaPythonImporter
from funboost.funboost_config_deafult import BrokerConnConfig
# from nb_log import get_logger
from funboost.core.loggers import get_funboost_file_logger

# LogManager('kafka').get_logger_and_add_handlers(30)
get_funboost_file_logger('kafka', log_level_int=30)


class KafkaConsumer(AbstractConsumer):
    """
    kafka作为中间件实现的。自动确认消费，最多消费一次，随意重启会丢失正在大批正在运行的任务。推荐使用 confluent_kafka 中间件，kafka_consumer_manually_commit.py。

    可以让消费函数内部 sleep60秒，突然停止消费代码，使用 kafka-consumer-groups.sh --bootstrap-server 127.0.0.1:9092 --describe --group funboost 来证实自动确认消费和手动确认消费的区别。
    """

    """
    auto_offset_reset 介绍
      auto_offset_reset (str): A policy for resetting offsets on
            OffsetOutOfRange errors: 'earliest' will move to the oldest
            available message, 'latest' will move to the most recent. Any
            other value will raise the exception. Default: 'latest'.
    """

    def _dispatch_task(self):
        try:
            admin_client = KafkaPythonImporter().KafkaAdminClient(bootstrap_servers=BrokerConnConfig.KAFKA_BOOTSTRAP_SERVERS)
            admin_client.create_topics([KafkaPythonImporter().NewTopic(self._queue_name,
                                                                       self.consumer_params.broker_exclusive_config['num_partitions'],
                                                                       self.consumer_params.broker_exclusive_config['replication_factor'])])
            # admin_client.create_partitions({self._queue_name: NewPartitions(total_count=16)})
        except KafkaPythonImporter().TopicAlreadyExistsError:
            pass

        self._producer = KafkaPythonImporter().KafkaProducer(bootstrap_servers=BrokerConnConfig.KAFKA_BOOTSTRAP_SERVERS)
        consumer = KafkaPythonImporter().OfficialKafkaConsumer(self._queue_name, bootstrap_servers=BrokerConnConfig.KAFKA_BOOTSTRAP_SERVERS,
                                                               group_id=self.consumer_params.broker_exclusive_config["group_id"],
                                                               enable_auto_commit=True,
                                                               auto_offset_reset=self.consumer_params.broker_exclusive_config["auto_offset_reset"],
                                                               )
        #  auto_offset_reset (str): A policy for resetting offsets on
        #             OffsetOutOfRange errors: 'earliest' will move to the oldest
        #             available message, 'latest' will move to the most recent. Any
        #             other value will raise the exception. Default: 'latest'.       默认是latest

        # kafka 的 group_id

        # REMIND 由于是很高数量的并发消费，线程很多，分区很少，这里设置成自动确认消费了，否则多线程提交同一个分区的偏移量导致超前错乱，就没有意义了。
        # REMIND 要保证很高的可靠性和一致性，请用rabbitmq。
        # REMIND 好处是并发高。topic像翻书一样，随时可以设置偏移量重新消费。多个分组消费同一个主题，每个分组对相同主题的偏移量互不干扰 。
        for message in consumer:
            # 注意: message ,value都是原始的字节数据，需要decode
            kw = {'consumer': consumer, 'message': message, 'body': message.value.decode('utf-8')}
            self._submit_task(kw)

    def _confirm_consume(self, kw):
        pass  # 使用kafka的自动commit模式。

    def _requeue(self, kw):
        self._producer.send(self._queue_name, json.dumps(kw['body']).encode())
