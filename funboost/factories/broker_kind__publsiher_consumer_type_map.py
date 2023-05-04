from funboost.constant import BrokerEnum

from funboost.publishers.confluent_kafka_publisher import ConfluentKafkaPublisher
from funboost.publishers.http_publisher import HTTPPublisher
from funboost.publishers.kombu_publisher import KombuPublisher
from funboost.publishers.nats_publisher import NatsPublisher
from funboost.publishers.peewee_publisher import PeeweePublisher
# from funboost.publishers.pulsar_publisher import PulsarPublisher
from funboost.publishers.redis_publisher_lpush import RedisPublisherLpush
from funboost.publishers.redis_pubsub_publisher import RedisPubSubPublisher
from funboost.publishers.tcp_publisher import TCPPublisher
from funboost.publishers.txt_file_publisher import TxtFilePublisher
from funboost.publishers.udp_publisher import UDPPublisher
from funboost.publishers.zeromq_publisher import ZeroMqPublisher
from funboost.publishers.kafka_publisher import KafkaPublisher
from funboost.publishers.local_python_queue_publisher import LocalPythonQueuePublisher
from funboost.publishers.mongomq_publisher import MongoMqPublisher
from funboost.publishers.nsq_publisher import NsqPublisher
from funboost.publishers.persist_queue_publisher import PersistQueuePublisher
from funboost.publishers.rabbitmq_amqpstorm_publisher import RabbitmqPublisherUsingAmqpStorm
from funboost.publishers.rabbitmq_pika_publisher import RabbitmqPublisher
from funboost.publishers.rabbitmq_rabbitpy_publisher import RabbitmqPublisherUsingRabbitpy
from funboost.publishers.redis_publisher import RedisPublisher
from funboost.publishers.rocketmq_publisher import RocketmqPublisher
from funboost.publishers.sqla_queue_publisher import SqlachemyQueuePublisher
from funboost.publishers.redis_stream_publisher import RedisStreamPublisher
from funboost.publishers.mqtt_publisher import MqttPublisher
from funboost.publishers.httpsqs_publisher import HttpsqsPublisher

from funboost.consumers.redis_pubsub_consumer import RedisPbSubConsumer
from funboost.consumers.http_consumer import HTTPConsumer
from funboost.consumers.kafka_consumer import KafkaConsumer
from funboost.consumers.kafka_consumer_manually_commit import KafkaConsumerManuallyCommit
from funboost.consumers.kombu_consumer import KombuConsumer
from funboost.consumers.local_python_queue_consumer import LocalPythonQueueConsumer
from funboost.consumers.mongomq_consumer import MongoMqConsumer
from funboost.consumers.nats_consumer import NatsConsumer
from funboost.consumers.nsq_consumer import NsqConsumer
from funboost.consumers.peewee_conusmer import PeeweeConsumer
from funboost.consumers.persist_queue_consumer import PersistQueueConsumer
from funboost.consumers.rabbitmq_amqpstorm_consumer import RabbitmqConsumerAmqpStorm
from funboost.consumers.rabbitmq_pika_consumer import RabbitmqConsumer
from funboost.consumers.rabbitmq_rabbitpy_consumer import RabbitmqConsumerRabbitpy
from funboost.consumers.redis_brpoplpush_consumer import RedisBrpopLpushConsumer
from funboost.consumers.redis_consumer import RedisConsumer
from funboost.consumers.redis_consumer_ack_able import RedisConsumerAckAble
from funboost.consumers.rocketmq_consumer import RocketmqConsumer
from funboost.consumers.sqlachemy_consumer import SqlachemyConsumer
from funboost.consumers.redis_stream_consumer import RedisStreamConsumer
from funboost.consumers.tcp_consumer import TCPConsumer
from funboost.consumers.txt_file_consumer import TxtFileConsumer
from funboost.consumers.udp_consumer import UDPConsumer
from funboost.consumers.zeromq_consumer import ZeroMqConsumer
from funboost.consumers.mqtt_consumer import MqttConsumer
from funboost.consumers.httpsqs_consumer import HttpsqsConsumer

broker_kind__publsiher_consumer_type_map = {
    BrokerEnum.RABBITMQ_AMQPSTORM: (RabbitmqPublisherUsingAmqpStorm, RabbitmqConsumerAmqpStorm),
    BrokerEnum.RABBITMQ_RABBITPY: (RabbitmqPublisherUsingRabbitpy, RabbitmqConsumerRabbitpy),
    BrokerEnum.REDIS: (RedisPublisher, RedisConsumer),
    BrokerEnum.MEMORY_QUEUE: (LocalPythonQueuePublisher, LocalPythonQueueConsumer),
    BrokerEnum.RABBITMQ_PIKA: (RabbitmqPublisher, RabbitmqConsumer),
    BrokerEnum.MONGOMQ: (MongoMqPublisher, MongoMqConsumer),
    BrokerEnum.PERSISTQUEUE: (PersistQueuePublisher, PersistQueueConsumer),
    BrokerEnum.NSQ: (NsqPublisher, NsqConsumer),
    BrokerEnum.KAFKA: (KafkaPublisher, KafkaConsumer),
    BrokerEnum.REDIS_ACK_ABLE: (RedisPublisher, RedisConsumerAckAble),
    BrokerEnum.SQLACHEMY: (SqlachemyQueuePublisher, SqlachemyConsumer),
    BrokerEnum.ROCKETMQ: (RocketmqPublisher, RocketmqConsumer),
    BrokerEnum.REDIS_STREAM: (RedisStreamPublisher, RedisStreamConsumer),
    BrokerEnum.ZEROMQ: (ZeroMqPublisher, ZeroMqConsumer),
    BrokerEnum.RedisBrpopLpush: (RedisPublisherLpush, RedisBrpopLpushConsumer),
    BrokerEnum.KOMBU: (KombuPublisher, KombuConsumer),
    BrokerEnum.KAFKA_CONFLUENT: (ConfluentKafkaPublisher, KafkaConsumerManuallyCommit),
    BrokerEnum.MQTT: (MqttPublisher, MqttConsumer),
    BrokerEnum.HTTPSQS: (HttpsqsPublisher, HttpsqsConsumer),
    BrokerEnum.UDP: (UDPPublisher, UDPConsumer),
    BrokerEnum.TCP: (TCPPublisher, TCPConsumer),
    BrokerEnum.HTTP: (HTTPPublisher, HTTPConsumer),
    BrokerEnum.NATS: (NatsPublisher, NatsConsumer),
    BrokerEnum.TXT_FILE: (TxtFilePublisher, TxtFileConsumer),
    BrokerEnum.PEEWEE: (PeeweePublisher, PeeweeConsumer),
    BrokerEnum.REDIS_PUBSUB: (RedisPubSubPublisher, RedisPbSubConsumer),

}

for broker_kindx, cls_tuple in broker_kind__publsiher_consumer_type_map.items():
    cls_tuple[1].BROKER_KIND = broker_kindx
