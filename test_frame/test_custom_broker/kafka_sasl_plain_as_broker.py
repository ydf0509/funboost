import atexit
import json
from collections import defaultdict, OrderedDict
# noinspection PyPackageRequirements
import time

# noinspection PyPackageRequirements
from kafka import KafkaProducer, KafkaAdminClient

# noinspection PyPackageRequirements
from kafka.admin import NewTopic
# noinspection PyPackageRequirements
from kafka.errors import TopicAlreadyExistsError

from funboost import register_custom_broker
from funboost.consumers.kafka_consumer_manually_commit import KafkaConsumerManuallyCommit
from funboost.publishers.confluent_kafka_publisher import ConfluentKafkaPublisher

from funboost.funboost_config_deafult import BrokerConnConfig

"""
funboost框架的kafka没有使用账号密码来连接，如果你的kafka有密码，那么扩展成支持有账号密码也是很简单的。
PLAIN 账号 密码方式的kafka服务端，funboost扩展例子，很简单 把KafkaConsumerManuallyCommit类复制粘贴， 然后只要把连接kafka的代码稍微修改下就可以了。
不需要继承 AbstractConsumer 重写全部对kafka的操作，继承子类就好了。

funboost_config.py 文件增加kafka配置如下，KFFKA_CONFIG 变量命名随意，例如可以叫 KFFKACONFAAA 也是可以，只要代码中应用这个变量就可以。

KFFKA_CONFIG = {
    "bootstrap_servers":KAFKA_BOOTSTRAP_SERVERS,
    'sasl_mechanism': "PLAIN",
    'security_protocol': "SASL_PLAINTEXT",
    'sasl_plain_username': "user",
    'sasl_plain_password': "password",
}
"""


class SaslPlainKafkaConsumer(KafkaConsumerManuallyCommit):


    def _shedual_task(self):

        # 这个包在win下不好安装，用户用这个中间件的时候自己再想办法安装。win用户需要安装c++ 14.0以上环境。
        from confluent_kafka import Consumer as ConfluentConsumer
        try:
            admin_client = KafkaAdminClient(
                **BrokerConnConfig.KFFKA_CONFIG)
            admin_client.create_topics([NewTopic(self._queue_name, 10, 1)])
            # admin_client.create_partitions({self._queue_name: NewPartitions(total_count=16)})
        except TopicAlreadyExistsError:
            pass

        self._producer = KafkaProducer(
            **BrokerConnConfig.KFFKA_CONFIG)
        # consumer 配置 https://github.com/edenhill/librdkafka/blob/master/CONFIGURATION.md
        self._confluent_consumer = ConfluentConsumer({
            'bootstrap.servers': ','.join(BrokerConnConfig.KAFKA_BOOTSTRAP_SERVERS),
            'security.protocol': BrokerConnConfig.KFFKA_CONFIG['security_protocol'],
            'sasl.mechanisms': BrokerConnConfig.KFFKA_CONFIG['sasl_mechanism'],
            'sasl.username': BrokerConnConfig.KFFKA_CONFIG['sasl_plain_username'],
            'sasl.password': BrokerConnConfig.KFFKA_CONFIG['sasl_plain_password'],
            'group.id': self.broker_exclusive_config["group_id"],
            'auto.offset.reset': self.broker_exclusive_config["auto_offset_reset"],
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
            self._partion__offset_consume_status_map[msg.partition(
            )][msg.offset()] = 0
            kw = {'partition': msg.partition(), 'offset': msg.offset(), 'body': json.loads(msg.value())}  # noqa
            if self._is_show_message_get_from_broker:
                self.logger.debug(
                    f'从kafka的 [{self._queue_name}] 主题,分区 {msg.partition()} 中 的 offset {msg.offset()} 取出的消息是：  {msg.value()}')  # noqa
            self._submit_task(kw)


class SaslPlainKafkaPublisher(ConfluentKafkaPublisher):
    """
    使用kafka作为中间件，这个confluent_kafka包的性能远强于 kafka-pyhton
    """

    # noinspection PyAttributeOutsideInit
    def custom_init(self):
        from confluent_kafka import Producer as ConfluentProducer  # 这个包不好安装，用户用这个中间件的时候自己再想办法安装。win用户需要安装c++ 14.0以上环境。
        # self._producer = KafkaProducer(bootstrap_servers=funboost_config_deafult.KAFKA_BOOTSTRAP_SERVERS)
        try:
            admin_client = KafkaAdminClient(**BrokerConnConfig.KFFKA_CONFIG)
            admin_client.create_topics([NewTopic(self._queue_name, 10, 1)])
            # admin_client.create_partitions({self._queue_name: NewPartitions(total_count=16)})
        except TopicAlreadyExistsError:
            pass
        except BaseException as e:
            self.logger.exception(e)
        atexit.register(self.close)  # 程序退出前不主动关闭，会报错。
        self._confluent_producer = ConfluentProducer({
            'bootstrap.servers': ','.join(BrokerConnConfig.KAFKA_BOOTSTRAP_SERVERS),
            'security.protocol': BrokerConnConfig.KFFKA_CONFIG['security_protocol'],
            'sasl.mechanisms': BrokerConnConfig.KFFKA_CONFIG['sasl_mechanism'],
            'sasl.username': BrokerConnConfig.KFFKA_CONFIG['sasl_plain_username'],
            'sasl.password': BrokerConnConfig.KFFKA_CONFIG['sasl_plain_password']
        })
        self._recent_produce_time = time.time()


BROKER_KIND_SASlPlAINKAFKA = 107
register_custom_broker(BROKER_KIND_SASlPlAINKAFKA, SaslPlainKafkaPublisher, SaslPlainKafkaConsumer)
