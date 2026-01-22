# -*- coding: utf-8 -*-
# @Author  : AI Assistant
# @Time    : 2026/1/16
"""
原生 PostgreSQL 消息队列实现
充分利用 PostgreSQL 相比 MySQL 的独特优势：
1. FOR UPDATE SKIP LOCKED - 高并发无锁抢任务，多消费者不阻塞
2. LISTEN/NOTIFY - 原生发布订阅机制，实时推送无需轮询
3. RETURNING - 插入/更新后直接返回数据，减少查询
4. 更强的事务隔离性和并发控制
"""
import json
import time


import psycopg2
from psycopg2 import sql
from psycopg2.extras import RealDictCursor
from psycopg2.pool import ThreadedConnectionPool

from funboost.core.loggers import FunboostFileLoggerMixin, LoggerLevelSetterMixin
from funboost.utils import decorators


class TaskStatus:
    TO_BE_CONSUMED = 'to_be_consumed'
    PENDING = 'pending'
    FAILED = 'failed'
    SUCCESS = 'success'
    REQUEUE = 'requeue'


@decorators.flyweight
class PostgresQueue(FunboostFileLoggerMixin, LoggerLevelSetterMixin):
    """
    原生 PostgreSQL 队列实现，利用 PostgreSQL 独有特性：
    - FOR UPDATE SKIP LOCKED: 高并发下多消费者无锁竞争
    - LISTEN/NOTIFY: 实时消息通知，避免轮询
    - RETURNING: 减少额外查询
    """

    def __init__(self, queue_name: str, dsn: str, min_conn: int = 2, max_conn: int = 20):
        """
        :param queue_name: 队列名称（作为表名）
        :param dsn: PostgreSQL 连接字符串，如 "host=localhost dbname=funboost user=postgres password=xxx"
        :param min_conn: 连接池最小连接数
        :param max_conn: 连接池最大连接数
        """
        self.queue_name = queue_name
        self._dsn = dsn
        self._table_name = f"funboost_queue_{queue_name}"
        self._notify_channel = f"funboost_notify_{queue_name}"

        # 创建线程安全连接池
        self._pool = ThreadedConnectionPool(min_conn, max_conn, dsn)
        self._create_table()
        self._listen_conn = None
        self._is_listening = False

        self.logger.info(f"PostgreSQL 队列 [{queue_name}] 初始化完成，使用 SKIP LOCKED + LISTEN/NOTIFY")

    def _get_conn(self):
        return self._pool.getconn()

    def _put_conn(self, conn):
        self._pool.putconn(conn)

    def _create_table(self):
        """创建队列表，包含必要的索引"""
        conn = self._get_conn()
        try:
            with conn.cursor() as cur:
                # 创建表
                cur.execute(sql.SQL("""
                    CREATE TABLE IF NOT EXISTS {} (
                        job_id BIGSERIAL PRIMARY KEY,
                        body TEXT NOT NULL,
                        status VARCHAR(20) DEFAULT 'to_be_consumed',
                        priority INTEGER DEFAULT 0,
                        publish_time TIMESTAMP DEFAULT NOW(),
                        consume_start_time TIMESTAMP,
                        created_at TIMESTAMP DEFAULT NOW()
                    )
                """).format(sql.Identifier(self._table_name)))

                # 创建索引：状态 + 优先级 + 发布时间（用于高效获取任务）
                cur.execute(sql.SQL("""
                    CREATE INDEX IF NOT EXISTS {} ON {} (status, priority DESC, publish_time ASC)
                    WHERE status IN ('to_be_consumed', 'requeue')
                """).format(
                    sql.Identifier(f"idx_{self._table_name}_status_priority"),
                    sql.Identifier(self._table_name)
                ))

                conn.commit()
        finally:
            self._put_conn(conn)

    def push(self, body: str, priority: int = 0) -> int:
        """
        发布消息到队列
        利用 RETURNING 直接返回 job_id，无需额外查询
        """
        conn = self._get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    sql.SQL("""
                        INSERT INTO {} (body, status, priority)
                        VALUES (%s, %s, %s)
                        RETURNING job_id
                    """).format(sql.Identifier(self._table_name)),
                    (body, TaskStatus.TO_BE_CONSUMED, priority)
                )
                job_id = cur.fetchone()[0]
                conn.commit()

                # 发送 NOTIFY 通知消费者有新消息
                cur.execute(sql.SQL("NOTIFY {}, %s").format(sql.Identifier(self._notify_channel)), (str(job_id),))
                conn.commit()

                return job_id
        finally:
            self._put_conn(conn)

    def bulk_push(self, items: list) -> list:
        """
        批量发布消息
        :param items: [{'body': str, 'priority': int}, ...]
        :return: job_id 列表
        """
        conn = self._get_conn()
        try:
            with conn.cursor() as cur:
                job_ids = []
                for item in items:
                    body = item.get('body') if isinstance(item, dict) else item
                    priority = item.get('priority', 0) if isinstance(item, dict) else 0
                    cur.execute(
                        sql.SQL("""
                            INSERT INTO {} (body, status, priority)
                            VALUES (%s, %s, %s)
                            RETURNING job_id
                        """).format(sql.Identifier(self._table_name)),
                        (body, TaskStatus.TO_BE_CONSUMED, priority)
                    )
                    job_ids.append(cur.fetchone()[0])
                conn.commit()

                # 批量通知
                cur.execute(sql.SQL("NOTIFY {}, %s").format(sql.Identifier(self._notify_channel)), ('bulk',))
                conn.commit()

                return job_ids
        finally:
            self._put_conn(conn)

    def get(self, timeout: float = None) -> dict:
        """
        获取一条消息（核心方法）
        
        利用 PostgreSQL 的 FOR UPDATE SKIP LOCKED：
        - 多个消费者并发获取时，不会阻塞等待
        - 已被其他消费者锁定的行会被跳过
        - 大幅提升高并发场景下的吞吐量
        """
        conn = self._get_conn()
        try:
            start_time = time.time()
            while True:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    # 使用 FOR UPDATE SKIP LOCKED 无锁获取任务
                    # 按优先级降序、发布时间升序获取
                    cur.execute(
                        sql.SQL("""
                            UPDATE {} SET
                                status = %s,
                                consume_start_time = NOW()
                            WHERE job_id = (
                                SELECT job_id FROM {}
                                WHERE status IN ('to_be_consumed', 'requeue')
                                ORDER BY priority DESC, publish_time ASC
                                FOR UPDATE SKIP LOCKED
                                LIMIT 1
                            )
                            RETURNING job_id, body, status, priority, publish_time, consume_start_time
                        """).format(
                            sql.Identifier(self._table_name),
                            sql.Identifier(self._table_name)
                        ),
                        (TaskStatus.PENDING,)
                    )
                    row = cur.fetchone()
                    conn.commit()

                    if row:
                        return dict(row)

                # 没有消息，短暂等待后重试
                if timeout and (time.time() - start_time) >= timeout:
                    return None

                time.sleep(0.1)  # 轮询间隔
        finally:
            self._put_conn(conn)

    def get_with_listen(self, timeout: float = 30) -> dict:
        """
        使用 LISTEN/NOTIFY 机制获取消息（推荐）
        
        PostgreSQL 独有特性：
        - 生产者 push 时发送 NOTIFY
        - 消费者 LISTEN 等待通知
        - 比轮询更高效，实时性更好
        """
        # 先尝试直接获取
        task = self.get(timeout=0.01)
        if task:
            return task

        # 没有消息，使用 LISTEN 等待通知
        if not self._listen_conn:
            self._listen_conn = psycopg2.connect(self._dsn)
            self._listen_conn.autocommit = True
            with self._listen_conn.cursor() as cur:
                cur.execute(sql.SQL("LISTEN {}").format(sql.Identifier(self._notify_channel)))

        import select
        start_time = time.time()
        while True:
            # 等待通知
            if select.select([self._listen_conn], [], [], min(1.0, timeout)) == ([], [], []):
                # 超时，再尝试一次获取
                if (time.time() - start_time) >= timeout:
                    return self.get(timeout=0.01)
                continue

            # 收到通知，消费通知并获取任务
            self._listen_conn.poll()
            while self._listen_conn.notifies:
                self._listen_conn.notifies.pop()

            task = self.get(timeout=0.01)
            if task:
                return task

            if (time.time() - start_time) >= timeout:
                return None

    def ack(self, job_id: int, delete: bool = True):
        """确认消费成功"""
        conn = self._get_conn()
        try:
            with conn.cursor() as cur:
                if delete:
                    cur.execute(
                        sql.SQL("DELETE FROM {} WHERE job_id = %s").format(sql.Identifier(self._table_name)),
                        (job_id,)
                    )
                else:
                    cur.execute(
                        sql.SQL("UPDATE {} SET status = %s WHERE job_id = %s").format(sql.Identifier(self._table_name)),
                        (TaskStatus.SUCCESS, job_id)
                    )
                conn.commit()
        finally:
            self._put_conn(conn)

    def requeue(self, job_id: int):
        """消息重新入队"""
        conn = self._get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    sql.SQL("""
                        UPDATE {} SET status = %s, consume_start_time = NULL
                        WHERE job_id = %s
                    """).format(sql.Identifier(self._table_name)),
                    (TaskStatus.REQUEUE, job_id)
                )
                conn.commit()
                # 通知其他消费者
                cur.execute(sql.SQL("NOTIFY {}, %s").format(sql.Identifier(self._notify_channel)), (str(job_id),))
                conn.commit()
        finally:
            self._put_conn(conn)

    def clear(self):
        """清空队列"""
        conn = self._get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute(sql.SQL("TRUNCATE TABLE {}").format(sql.Identifier(self._table_name)))
                conn.commit()
        finally:
            self._put_conn(conn)

    def get_message_count(self) -> int:
        """获取待消费消息数量"""
        conn = self._get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    sql.SQL("""
                        SELECT COUNT(*) FROM {}
                        WHERE status IN ('to_be_consumed', 'requeue')
                    """).format(sql.Identifier(self._table_name))
                )
                return cur.fetchone()[0]
        finally:
            self._put_conn(conn)

    def recover_timeout_tasks(self, timeout_minutes: int = 10):
        """
        恢复超时未确认的任务
        将超过 timeout_minutes 的 PENDING 任务重置为 TO_BE_CONSUMED
        """
        conn = self._get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    sql.SQL("""
                        UPDATE {} SET status = %s, consume_start_time = NULL
                        WHERE status = %s
                        AND consume_start_time < NOW() - INTERVAL '%s minutes'
                        RETURNING job_id
                    """).format(sql.Identifier(self._table_name)),
                    (TaskStatus.TO_BE_CONSUMED, TaskStatus.PENDING, timeout_minutes)
                )
                recovered = cur.fetchall()
                conn.commit()
                if recovered:
                    self.logger.info(f"恢复了 {len(recovered)} 个超时任务")
                    cur.execute(sql.SQL("NOTIFY {}, %s").format(sql.Identifier(self._notify_channel)), ('recover',))
                    conn.commit()
                return len(recovered)
        finally:
            self._put_conn(conn)

    def close(self):
        """关闭连接池"""
        if self._listen_conn:
            self._listen_conn.close()
        self._pool.closeall()


if __name__ == '__main__':
    # 测试代码
    dsn = "host=localhost dbname=funboost user=postgres password=123456"
    queue = PostgresQueue('test_queue', dsn)

    # 发布消息
    for i in range(10):
        job_id = queue.push(json.dumps({'x': i, 'y': i * 2}), priority=i % 3)
        print(f"Published job_id: {job_id}")

    # 消费消息
    while True:
        task = queue.get(timeout=5)
        if not task:
            break
        print(f"Got task: {task}")
        queue.ack(task['job_id'])

    queue.close()
    