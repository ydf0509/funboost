# -*- coding: utf-8 -*-
# @Author  : AI Assistant
# @Time    : 2026/1/16
"""
PostgreSQL Consumer - 原生高性能实现
充分利用 PostgreSQL 独有特性：
1. FOR UPDATE SKIP LOCKED - 高并发无锁竞争
2. LISTEN/NOTIFY - 实时消息推送，避免无效轮询
"""
from funboost.consumers.base_consumer import AbstractConsumer
from funboost.funboost_config_deafult import BrokerConnConfig
from funboost.queues.postgres_queue import PostgresQueue


class PostgresConsumer(AbstractConsumer):
    """
    PostgreSQL 原生消费者
    
    相比 SQLAlchemy 通用实现的优势：
    1. FOR UPDATE SKIP LOCKED: 多消费者并发时无锁竞争，性能提升显著
    2. LISTEN/NOTIFY: 实时通知机制，比轮询更高效
    3. 使用原生 psycopg2 连接池
    """

    BROKER_KIND = None  # 会被框架自动设置

    def custom_init(self):
        self._use_listen_notify = self.consumer_params.broker_exclusive_config['use_listen_notify']
        self._poll_interval = self.consumer_params.broker_exclusive_config['poll_interval']
        self._timeout_minutes = self.consumer_params.broker_exclusive_config['timeout_minutes']
        
        self._queue = PostgresQueue(
            queue_name=self._queue_name,
            dsn=BrokerConnConfig.POSTGRES_DSN,
            min_conn=self.consumer_params.broker_exclusive_config['min_connections'],
            max_conn=self.consumer_params.broker_exclusive_config['max_connections'],
        )
        self.logger.info(
            f"PostgreSQL Consumer 初始化完成，队列: {self._queue_name}, "
            f"LISTEN/NOTIFY: {self._use_listen_notify}"
        )

    def _dispatch_task(self):
        """
        核心调度方法
        使用 FOR UPDATE SKIP LOCKED 获取任务，实现高并发无锁竞争
        可选启用 LISTEN/NOTIFY 实现实时推送
        """
        # 启动超时任务恢复线程
        self._start_timeout_recovery()

        while True:
            try:
                if self._use_listen_notify:
                    # 使用 LISTEN/NOTIFY 机制（推荐）
                    task = self._queue.get_with_listen(timeout=self._poll_interval)
                else:
                    # 使用轮询机制
                    task = self._queue.get(timeout=self._poll_interval)

                if task:
                    self._print_message_get_from_broker('PostgreSQL', task)
                    kw = {
                        'body': task['body'],
                        'job_id': task['job_id'],
                        'priority': task.get('priority', 0),
                    }
                    self._submit_task(kw)
            except Exception as e:
                self.logger.error(f"获取消息异常: {e}", exc_info=True)
                import time
                time.sleep(1)

    def _start_timeout_recovery(self):
        """启动超时任务恢复后台线程"""
        import threading

        def recovery_loop():
            import time
            while True:
                try:
                    recovered = self._queue.recover_timeout_tasks(self._timeout_minutes)
                    if recovered:
                        self.logger.info(f"恢复了 {recovered} 个超时任务")
                except Exception as e:
                    self.logger.error(f"恢复超时任务异常: {e}")
                time.sleep(60)  # 每分钟检查一次

        t = threading.Thread(target=recovery_loop, daemon=True, name=f"pg_recovery_{self._queue_name}")
        t.start()

    def _confirm_consume(self, kw):
        """确认消费成功，删除消息"""
        self._queue.ack(kw['job_id'], delete=True)

    def _requeue(self, kw):
        """消息重新入队"""
        self._queue.requeue(kw['job_id'])
