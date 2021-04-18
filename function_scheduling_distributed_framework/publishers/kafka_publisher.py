# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2019/8/20 0008 12:12

# noinspection PyPackageRequirements
import atexit

# noinspection PyPackageRequirements
from kafka import KafkaProducer, KafkaAdminClient
# noinspection PyPackageRequirements
from kafka.admin import NewTopic
# noinspection PyPackageRequirements
from kafka.errors import TopicAlreadyExistsError

from function_scheduling_distributed_framework import frame_config
from function_scheduling_distributed_framework.publishers.base_publisher import AbstractPublisher


class KafkaPublisher(AbstractPublisher, ):
    """
    使用kafka作为中间件
    """

    # noinspection PyAttributeOutsideInit
    def custom_init(self):

        self._producer = KafkaProducer(bootstrap_servers=frame_config.KAFKA_BOOTSTRAP_SERVERS)

        try:
            admin_client = KafkaAdminClient(bootstrap_servers=frame_config.KAFKA_BOOTSTRAP_SERVERS)
            admin_client.create_topics([NewTopic(self._queue_name, 10, 1)])
            # admin_client.create_partitions({self._queue_name: NewPartitions(total_count=16)})
        except TopicAlreadyExistsError:
            pass
        except Exception as e:
            self.logger.exception(e)
        atexit.register(self.close)  # 程序退出前不主动关闭，会报错。

    def concrete_realization_of_publish(self, msg):
        # noinspection PyTypeChecker
        # self.logger.debug(msg)
        self._producer.send(self._queue_name, msg.encode(), )

    def clear(self):
        self.logger.warning('还没开始实现 kafka 清空 消息')
        # self._consumer.seek_to_end()
        # self.logger.warning(f'将kafka offset 重置到最后位置')

    def get_message_count(self):
        return 0  # 还没找到获取所有分区未消费数量的方法。

    def close(self):
        self._producer.close()

    def _at_exit(self):
        self._producer.flush()
        self.close()
        super()._at_exit()
