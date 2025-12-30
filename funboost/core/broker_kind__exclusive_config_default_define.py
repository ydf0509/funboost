
"""
这个文件决定了，每种broker对应的能额外传递哪些独特特殊的中间件配置，
从BoosterParams 的 broker_exclusive_config 入参中传递一个字典
"""

from logging import Logger
from funboost.constant import BrokerEnum


broker_kind__exclusive_config_default_map: dict = {}


def register_broker_exclusive_config_default(
    broker_kind: str, broker_exclusive_config_default: dict
):
    broker_kind__exclusive_config_default_map[broker_kind] = broker_exclusive_config_default



def generate_broker_exclusive_config(
    broker_kind: str,
    user_broker_exclusive_config: dict,
    logger: Logger,
):
    broker_exclusive_config_default = broker_kind__exclusive_config_default_map.get(
        broker_kind, {}
    )
    broker_exclusive_config_keys = broker_exclusive_config_default.keys()
    if user_broker_exclusive_config:
        if set(user_broker_exclusive_config).issubset(broker_exclusive_config_keys):
            logger.info(
                f"当前消息队列中间件能支持特殊独有配置 {broker_exclusive_config_default.keys()}"
            )
        else:
            logger.warning(f"""当前消息队列中间件含有不支持的特殊配置 {user_broker_exclusive_config.keys()} ,
            能支持的特殊独有配置包括 {broker_exclusive_config_keys}""")
    broker_exclusive_config_merge = dict()
    broker_exclusive_config_merge.update(broker_exclusive_config_default)
    broker_exclusive_config_merge.update(user_broker_exclusive_config)
    return broker_exclusive_config_merge


# celery的可以配置项大全  https://docs.celeryq.dev/en/stable/userguide/configuration.html#new-lowercase-settings
# celery @app.task() 所有可以配置项可以看  D:\ProgramData\Miniconda3\Lib\site-packages\celery\app\task.py
register_broker_exclusive_config_default(BrokerEnum.CELERY, {"celery_task_config": {}})


# dramatiq_actor_options 的值可以是：
# {'max_age', 'throws', 'pipe_target', 'pipe_ignore', 'on_success', 'retry_when', 'time_limit', 'min_backoff', 'max_retries', 'max_backoff', 'notify_shutdown', 'on_failure'}
register_broker_exclusive_config_default(
    BrokerEnum.DRAMATIQ, {"dramatiq_actor_options": {}}
)


register_broker_exclusive_config_default(
    BrokerEnum.GRPC,
    {
        "host": "127.0.0.1",
        "port": None,
    },
)

register_broker_exclusive_config_default(
    BrokerEnum.HTTP,
    {
        "host": "127.0.0.1",
        "port": None,
    },
)


"""
retries=0, retry_delay=0, priority=None, context=False,
name=None, expires=None, **kwargs
"""
register_broker_exclusive_config_default(BrokerEnum.HUEY, {"huey_task_kwargs": {}})


"""
auto_offset_reset 介绍

auto_offset_reset (str): A policy for resetting offsets on
OffsetOutOfRange errors: 'earliest' will move to the oldest
available message, 'latest' will move to the most recent. Any
other value will raise the exception. Default: 'latest'.
"""
register_broker_exclusive_config_default(
    BrokerEnum.KAFKA,
    {
        "group_id": "funboost_kafka",
        "auto_offset_reset": "earliest",
        "num_partitions": 10,
        "replication_factor": 1,
    },
)


register_broker_exclusive_config_default(
    BrokerEnum.KAFKA_CONFLUENT,
    {
        "group_id": "funboost_kafka",
        "auto_offset_reset": "earliest",
        "num_partitions": 10,
        "replication_factor": 1,
    },
)


""" 
# prefetch_count 是预获取消息数量
transport_options是kombu的transport_options 。 
例如使用kombu使用redis作为中间件时候，可以设置 visibility_timeout 来决定消息取出多久没有ack，就自动重回队列。
kombu的每个中间件能设置什么 transport_options 可以看 kombu的源码中的 transport_options 参数说明。
"""
register_broker_exclusive_config_default(
    BrokerEnum.KOMBU,
    {
        "kombu_url": None,  # 如果这里也配置了kombu_url,则优先使用跟着你的kombu_url，否则使用funboost_config. KOMBU_URL
        "transport_options": {},  # transport_options是kombu的transport_options 。
        "prefetch_count": 500,
    },
)


register_broker_exclusive_config_default(
    BrokerEnum.MYSQL_CDC, {"BinLogStreamReaderConfig": {}}
)  # 入参是 BinLogStreamReader 的入参BinLogStreamReader


"""
consumer_type Members:
Exclusive  Shared Failover KeyShared
"""
register_broker_exclusive_config_default(
    BrokerEnum.PULSAR,
    {
        "subscription_name": "funboost_group",
        "replicate_subscription_state_enabled": True,
        "consumer_type": "Shared",
    },
)


register_broker_exclusive_config_default(
    BrokerEnum.RABBITMQ_AMQPSTORM,
    {
        "queue_durable": True,
        "x-max-priority": None,  # x-max-priority 是 rabbitmq的优先级队列配置，必须为整数，强烈建议要小于5。为None就代表队列不支持优先级。
        "no_ack": False,
    },
)


register_broker_exclusive_config_default(
    BrokerEnum.RABBITMQ_COMPLEX_ROUTING,
    {
        "queue_durable": True,
        "x-max-priority": None,  # x-max-priority 是 rabbitmq的优先级队列配置，必须为整数，强烈建议要小于5。为None就代表队列不支持优先级。
        "no_ack": False,
        "exchange_name": "",
        "exchange_type": "direct",
        "routing_key_for_bind": None,  # 绑定交换机和队列时使用的key。None表示使用queue_name作为绑定键；""(空字符串)也表示使用queue_name。对于fanout和headers交换机，此值会被忽略。对于topic交换机，可以使用通配符*和#。
        "routing_key_for_publish": None,
        # for headers exchange
        "headers_for_bind": {},
        "x_match_for_bind": "all",  # all or any
        "exchange_declare_durable": True,
    },
)


register_broker_exclusive_config_default(
    BrokerEnum.REDIS,
    {
        "redis_bulk_push": 1,
        "pull_msg_batch_size": 100,
    },
)  # redis_bulk_push 是否redis批量推送


register_broker_exclusive_config_default(
    BrokerEnum.REDIS_ACK_ABLE, {"pull_msg_batch_size": 100}
)

# RedisConsumerAckUsingTimeout的ack timeot 是代表消息取出后过了多少秒还未ack，就自动重回队列。这个配置一定要大于函数消耗时间，否则不停的重回队列。
"""
用法，如何设置ack_timeout，是使用 broker_exclusive_config 中传递，就能覆盖这里的3600，用户不用改BROKER_EXCLUSIVE_CONFIG_DEFAULT的源码。
@boost(BoosterParams(queue_name='test_redis_ack__use_timeout', broker_kind=BrokerEnum.REIDS_ACK_USING_TIMEOUT,
                        concurrent_num=5, log_level=20, broker_exclusive_config={'ack_timeout': 30}))
"""
register_broker_exclusive_config_default(
    BrokerEnum.REIDS_ACK_USING_TIMEOUT, {"ack_timeout": 3600}
)


register_broker_exclusive_config_default(
    BrokerEnum.REDIS_PRIORITY, {"x-max-priority": None}
)  # x-max-priority 是 rabbitmq的优先级队列配置，必须为整数，强烈建议要小于5。为None就代表队列不支持优先级。


register_broker_exclusive_config_default(
    BrokerEnum.REDIS_STREAM,
    {
        "group": "funboost_group",
        "pull_msg_batch_size": 100,
    },
)


register_broker_exclusive_config_default(
    BrokerEnum.TCP,
    {
        "host": "127.0.0.1",
        "port": None,
        "bufsize": 10240,
    },
)


register_broker_exclusive_config_default(
    BrokerEnum.UDP,
    {
        "host": "127.0.0.1",
        "port": None,
        "bufsize": 10240,
    },
)

register_broker_exclusive_config_default(BrokerEnum.ZEROMQ, {"port": None})
