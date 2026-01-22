# -*- coding: utf-8 -*-
# @Author  : AI Assistant
# @Time    : 2026/1/16
"""
PostgreSQL Publisher - 原生高性能实现
利用 PostgreSQL 的 RETURNING 和 NOTIFY 特性
"""
from funboost.publishers.base_publisher import AbstractPublisher
from funboost.funboost_config_deafult import BrokerConnConfig
from funboost.queues.postgres_queue import PostgresQueue


class PostgresPublisher(AbstractPublisher):
    """
    PostgreSQL 原生发布者
    
    相比 SQLAlchemy 通用实现的优势：
    1. 使用原生 psycopg2，性能更好
    2. 支持 NOTIFY 实时通知消费者
    3. 使用连接池，更高效的连接管理
    """

    def custom_init(self):
        self._priority = self.publisher_params.broker_exclusive_config['priority']
        self._queue = PostgresQueue(
            queue_name=self._queue_name,
            dsn=BrokerConnConfig.POSTGRES_DSN,
            min_conn=self.publisher_params.broker_exclusive_config['min_connections'],
            max_conn=self.publisher_params.broker_exclusive_config['max_connections'],
        )
        self.logger.info(f"PostgreSQL Publisher 初始化完成，队列: {self._queue_name}")

    def _publish_impl(self, msg: str):
        """发布消息，利用 RETURNING 返回 job_id"""
        # 尝试从消息中获取优先级
        priority = self._priority
        try:
            import json
            msg_dict = json.loads(msg)
            if 'extra' in msg_dict and 'priority' in msg_dict.get('extra', {}).get('other_extra_params', {}):
                priority = msg_dict['extra']['other_extra_params']['priority']
        except (json.JSONDecodeError, KeyError, TypeError):
            pass
        self._queue.push(msg, priority=priority)

    def clear(self):
        """清空队列"""
        self._queue.clear()

    def get_message_count(self):
        """获取待消费消息数量"""
        return self._queue.get_message_count()

    def close(self):
        """关闭连接"""
        self._queue.close()
