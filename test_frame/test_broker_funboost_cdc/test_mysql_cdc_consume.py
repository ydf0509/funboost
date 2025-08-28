# coding=utf-8
from typing import Dict, Any
import dataset

from funboost import boost, BrokerEnum, ConcurrentModeEnum, BoosterParams,BoostersManager,PublisherParams
from pymysqlreplication.row_event import (DeleteRowsEvent, UpdateRowsEvent, WriteRowsEvent, )

from funboost.contrib.cdc.mysql2mysql import MySql2Mysql # 从 funboost的额外贡献文件夹中导入 MySql2Mysql 类.

bin_log_stream_reader_config = dict(
    # BinLogStreamReaderConfig 的所有入参都是 pymysqlreplication.BinLogStreamReader 的 原生入参
    connection_settings={"host": "127.0.0.1", "port": 3306, "user": "root", "passwd": "123456"},
    server_id=104,
    only_events=[DeleteRowsEvent, UpdateRowsEvent, WriteRowsEvent, ],
    blocking=True,  # 1. 设置为阻塞模式，使其持续等待新事件
    resume_stream=True,  # 2. (推荐) 允许在断线后自动从上次的位置恢复}},
    only_schemas=['testdb6'],  # 3. 仅监听 testdb6 数据库
    only_tables=['users'],  # 4. 仅监听 users 表
)

sink_db = dataset.connect('mysql+pymysql://root:123456@127.0.0.1:3306/testdb7')  # 使用cdc技术 ,把 testdb6.users 表数据同步到另外一个库testdb7中的user表



@boost(BoosterParams(
    queue_name='test_queue_no_use_for_mysql_cdc',
    broker_exclusive_config={'BinLogStreamReaderConfig': bin_log_stream_reader_config},
    broker_kind=BrokerEnum.MYSQL_CDC, ))
def consume_binlog(event_type: str,
                   schema: str,
                   table: str,
                   timestamp: int,
                   **row_data: Any):
    full_cdc_msg = locals()
    print(full_cdc_msg)
    # update 事件打印如下
    """
    {
    "event_type": "UPDATE",
    "row_data": {
        "after_none_sources": {},
        "after_values": {
            "email": "wangshier@example.com",
            "id": 10,
            "name": "王八蛋2b16"
        },
        "before_none_sources": {},
        "before_values": {
            "email": "wangshier@example.com",
            "id": 10,
            "name": "王八蛋2b15"
        }
    },
    "schema": "testdb6",
    "table": "users",
    "timestamp": 1756207785
}
    """
    # 演示 轻松搞定mysql2mysql 表同步,你也可以清洗数据再插入mysql,这里是演示整表原封不动同步, 可以不用搭建flinkcdc大数据集群,就能5行代码以内搞定 mysql2mysql
    m2m = MySql2Mysql(primary_key='id',target_table_name='users', target_sink_db=sink_db, )
    m2m.sync_data(event_type, schema, table, timestamp,row_data) # 只需要一行代码就能把cdc数据同步到另外一个数据库实例的表中.


    # 你还可以吧消息发到 rabbitmq  kafka redis 随你喜欢,可以使用 funboost的 publisher.send_msg 来发布原始内容,不会添加extra taskid等额外key.,
    # 不需要亲自封装各种消息发布工具,利用funboost的万能特性,发布到所有各种消息队列只需要一行代码.

    # 演示把消息发到redis
    pb_redis = BoostersManager.get_cross_project_publisher(PublisherParams(queue_name='test_queue_mysql_cdc_dest1',broker_kind=BrokerEnum.REDIS))
    pb_redis.send_msg(full_cdc_msg)

    # 演示把消息发到kafka
    pb_kafka = BoostersManager.get_cross_project_publisher(PublisherParams(queue_name='test_queue_mysql_cdc_dest2', broker_kind=BrokerEnum.KAFKA,
                                                                           broker_exclusive_config={'num_partitions':10,'replication_factor':1}))
    pb_kafka.send_msg(full_cdc_msg)


if __name__ == '__main__':
    # MYSQL_CDC 作为funboost的broker时候, 所以禁止了 push 来人工发布消息, 自动监听binlog作为消息来源,所以不需要人工发消息.
    # 任何对数据库的 insert delete update 都会触发binlog,间接的作为了 funboost 消费者的消息来源.
    consume_binlog.consume()
