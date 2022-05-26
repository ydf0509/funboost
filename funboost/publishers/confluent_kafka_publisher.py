# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2019/8/20 0008 12:12

import os

if os.name == 'nt':
    """
    为了保险起见，这样做一下,设置一下path，否则anaconda安装的python可能出现 ImportError: DLL load failed while importing cimpl: 找不到指定的模块。
    多设置没事，少设置了才麻烦。
    """
    from pathlib import Path
    import sys

    # print(sys.executable)  #F:\minicondadir\Miniconda2\envs\py38\python.exe
    # print(os.getenv('path'))
    python_install_path = Path(sys.executable).parent.absolute()
    kafka_libs_path = python_install_path / Path(r'.\Lib\site-packages\confluent_kafka.libs')
    dlls_path = python_install_path / Path(r'.\DLLs')
    library_bin_path = python_install_path / Path(r'.\Library\bin')
    # print(library_bin_path)
    path_env = os.getenv('path')
    os.environ['path'] = f'''{path_env};{kafka_libs_path};{dlls_path};{library_bin_path};'''

import atexit
import time
# noinspection PyPackageRequirements
from kafka import KafkaProducer, KafkaAdminClient
# noinspection PyPackageRequirements
from kafka.admin import NewTopic
# noinspection PyPackageRequirements
from kafka.errors import TopicAlreadyExistsError

from funboost import funboost_config_deafult
from funboost.publishers.base_publisher import AbstractPublisher


class ConfluentKafkaPublisher(AbstractPublisher, ):
    """
    使用kafka作为中间件，这个confluent_kafka包的性能远强于 kafka-pyhton
    """

    # noinspection PyAttributeOutsideInit
    def custom_init(self):
        from confluent_kafka import Producer as ConfluentProducer  # 这个包不好安装，用户用这个中间件的时候自己再想办法安装。win用户需要安装c++ 14.0以上环境。
        # self._producer = KafkaProducer(bootstrap_servers=funboost_config_deafult.KAFKA_BOOTSTRAP_SERVERS)
        try:
            admin_client = KafkaAdminClient(bootstrap_servers=funboost_config_deafult.KAFKA_BOOTSTRAP_SERVERS)
            admin_client.create_topics([NewTopic(self._queue_name, 10, 1)])
            # admin_client.create_partitions({self._queue_name: NewPartitions(total_count=16)})
        except TopicAlreadyExistsError:
            pass
        except Exception as e:
            self.logger.exception(e)
        atexit.register(self.close)  # 程序退出前不主动关闭，会报错。
        self._confluent_producer = ConfluentProducer({'bootstrap.servers': ','.join(funboost_config_deafult.KAFKA_BOOTSTRAP_SERVERS)})
        self._recent_produce_time = time.time()

    # noinspection PyAttributeOutsideInit
    def concrete_realization_of_publish(self, msg):
        # noinspection PyTypeChecker
        # self.logger.debug(msg)
        self._confluent_producer.produce(self._queue_name, msg.encode(), )
        if time.time() - self._recent_produce_time > 1:
            self._confluent_producer.flush()
            self._recent_produce_time = time.time()

    def clear(self):
        self.logger.warning('还没开始实现 kafka 清空 消息')
        # self._consumer.seek_to_end()
        # self.logger.warning(f'将kafka offset 重置到最后位置')

    def get_message_count(self):
        return -1  # 还没找到获取所有分区未消费数量的方法。

    def close(self):
        pass
        # self._confluent_producer.

    def _at_exit(self):
        # self._producer.flush()
        self._confluent_producer.flush()
        super()._at_exit()
