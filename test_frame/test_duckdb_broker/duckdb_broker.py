# -*- coding: utf-8 -*-
# @Author  : AI Assistant
# @Time    : 2026/1/2
"""
此文件最重要的目的是演示 register_custom_broker 来如何扩展一个全新的broker中间件。

DuckDB 消息队列中间件实现

DuckDB 特点：
1. 嵌入式数据库，无需额外部署服务，开箱即用
2. 列式存储，高性能 OLAP 查询
3. 支持标准 SQL，易于使用
4. 单机场景非常适合，性能优异
5. 文件存储或内存模式灵活选择

使用场景：
- 单机开发测试
- 轻量级任务队列
- 不想部署 Redis/RabbitMQ 等外部服务的场景
- 需要持久化但不想使用重量级数据库的场景

使用方式：
    from funboost.contrib.register_custom_broker_contrib.duckdb_broker import BROKER_KIND_DUCKDB
    
    @boost(BoosterParams(queue_name='my_queue', broker_kind=BROKER_KIND_DUCKDB))
    def my_func(x):
        print(x)
"""

import json
import threading
import time
from pathlib import Path
from typing import Optional

try:
    import duckdb
except ImportError:
    raise ImportError("请安装 duckdb: pip install duckdb")

from funboost import register_custom_broker, AbstractConsumer, AbstractPublisher
from funboost.core.loggers import FunboostFileLoggerMixin, LoggerLevelSetterMixin
from funboost.utils import decorators


class TaskStatus:
    """任务状态常量"""
    TO_BE_CONSUMED = 'to_be_consumed'  # 待消费
    PENDING = 'pending'                 # 消费中
    SUCCESS = 'success'                 # 消费成功
    REQUEUE = 'requeue'                 # 重新入队


# 全局锁，保证 DuckDB 单文件并发安全
_duckdb_locks = {}
_lock_for_locks = threading.Lock()


def _get_lock(db_path: str) -> threading.Lock:
    """获取指定数据库文件的锁"""
    with _lock_for_locks:
        if db_path not in _duckdb_locks:
            _duckdb_locks[db_path] = threading.Lock()
        return _duckdb_locks[db_path]


@decorators.flyweight
class DuckDBQueue(FunboostFileLoggerMixin, LoggerLevelSetterMixin):
    """
    DuckDB 队列实现
    
    特点：
    1. 使用文件存储，消息持久化
    2. 支持内存模式，性能更高
    3. 线程安全，使用锁保护并发操作
    4. 支持优先级队列
    5. 支持消息确认和重入队
    """

    def __init__(self, queue_name: str, db_path: str = ':memory:', 
                 wal_autocheckpoint: int = 1000):
        """
        :param queue_name: 队列名称
        :param db_path: 数据库文件路径，':memory:' 表示内存模式
        :param wal_autocheckpoint: WAL 自动检查点阈值（已废弃，DuckDB 不使用此参数）
        """
        self.queue_name = queue_name
        self._db_path = db_path
        self._table_name = f"funboost_queue_{queue_name.replace('-', '_').replace('.', '_')}"
        self._lock = _get_lock(db_path)
        
        # 创建连接
        self._conn = duckdb.connect(db_path)
        
        # 创建表
        self._create_table()
        self.logger.info(f"DuckDB 队列 [{queue_name}] 初始化完成，数据库: {db_path}")

    def _create_table(self):
        """创建队列表"""
        with self._lock:
            self._conn.execute(f"""
                CREATE TABLE IF NOT EXISTS {self._table_name} (
                    job_id BIGINT PRIMARY KEY,
                    body VARCHAR NOT NULL,
                    status VARCHAR DEFAULT 'to_be_consumed',
                    priority INTEGER DEFAULT 0,
                    publish_time TIMESTAMP DEFAULT current_timestamp,
                    consume_start_time TIMESTAMP
                )
            """)
            # 创建序列（如果不存在）
            try:
                self._conn.execute(f"CREATE SEQUENCE IF NOT EXISTS seq_{self._table_name}")
            except Exception:
                pass  # DuckDB 可能不支持 IF NOT EXISTS 对于 SEQUENCE
            
            # 创建索引
            try:
                self._conn.execute(f"""
                    CREATE INDEX IF NOT EXISTS idx_{self._table_name}_status 
                    ON {self._table_name} (status, priority DESC, publish_time ASC)
                """)
            except Exception:
                pass  # 索引可能已存在

    def _next_job_id(self) -> int:
        """生成下一个 job_id"""
        try:
            result = self._conn.execute(f"SELECT nextval('seq_{self._table_name}')").fetchone()
            return result[0]
        except Exception:
            # 如果序列不存在，使用时间戳 + 随机数
            import random
            return int(time.time() * 1000000) + random.randint(0, 999999)

    def push(self, body: str, priority: int = 0) -> int:
        """
        发布消息到队列
        :param body: 消息体（JSON 字符串）
        :param priority: 优先级（越大越优先）
        :return: job_id
        """
        with self._lock:
            job_id = self._next_job_id()
            self._conn.execute(f"""
                INSERT INTO {self._table_name} (job_id, body, status, priority, publish_time)
                VALUES (?, ?, ?, ?, current_timestamp)
            """, [job_id, body, TaskStatus.TO_BE_CONSUMED, priority])
            return job_id

    def bulk_push(self, items: list) -> list:
        """
        批量发布消息
        :param items: [{'body': str, 'priority': int}, ...] 或 [str, ...]
        :return: job_id 列表
        """
        job_ids = []
        with self._lock:
            for item in items:
                if isinstance(item, dict):
                    body = item.get('body', item)
                    priority = item.get('priority', 0)
                else:
                    body = item
                    priority = 0
                
                job_id = self._next_job_id()
                self._conn.execute(f"""
                    INSERT INTO {self._table_name} (job_id, body, status, priority, publish_time)
                    VALUES (?, ?, ?, ?, current_timestamp)
                """, [job_id, body, TaskStatus.TO_BE_CONSUMED, priority])
                job_ids.append(job_id)
        return job_ids

    def get(self, timeout: float = None) -> Optional[dict]:
        """
        获取一条待消费的消息
        :param timeout: 超时时间（秒），None 表示一直等待
        :return: {'job_id': int, 'body': str, 'priority': int} 或 None
        """
        start_time = time.time()
        while True:
            with self._lock:
                # 查找待消费的消息（按优先级降序、发布时间升序）
                result = self._conn.execute(f"""
                    SELECT job_id, body, priority, publish_time
                    FROM {self._table_name}
                    WHERE status IN ('{TaskStatus.TO_BE_CONSUMED}', '{TaskStatus.REQUEUE}')
                    ORDER BY priority DESC, publish_time ASC
                    LIMIT 1
                """).fetchone()
                
                if result:
                    job_id, body, priority, publish_time = result
                    # 更新状态为处理中
                    self._conn.execute(f"""
                        UPDATE {self._table_name}
                        SET status = ?, consume_start_time = current_timestamp
                        WHERE job_id = ?
                    """, [TaskStatus.PENDING, job_id])
                    return {
                        'job_id': job_id,
                        'body': body,
                        'priority': priority,
                        'publish_time': publish_time,
                    }
            
            # 没有消息，检查超时
            if timeout is not None and (time.time() - start_time) >= timeout:
                return None
            
            # 短暂等待后重试
            time.sleep(0.05)

    def ack(self, job_id: int, delete: bool = True):
        """
        确认消费成功
        :param job_id: 任务 ID
        :param delete: 是否删除消息（True 删除，False 更新状态为成功）
        """
        with self._lock:
            if delete:
                self._conn.execute(f"DELETE FROM {self._table_name} WHERE job_id = ?", [job_id])
            else:
                self._conn.execute(f"""
                    UPDATE {self._table_name} SET status = ? WHERE job_id = ?
                """, [TaskStatus.SUCCESS, job_id])

    def requeue(self, job_id: int):
        """消息重新入队"""
        with self._lock:
            self._conn.execute(f"""
                UPDATE {self._table_name}
                SET status = ?, consume_start_time = NULL
                WHERE job_id = ?
            """, [TaskStatus.REQUEUE, job_id])

    def clear(self):
        """清空队列"""
        with self._lock:
            self._conn.execute(f"DELETE FROM {self._table_name}")

    def get_message_count(self) -> int:
        """获取待消费消息数量"""
        with self._lock:
            result = self._conn.execute(f"""
                SELECT COUNT(*) FROM {self._table_name}
                WHERE status IN ('{TaskStatus.TO_BE_CONSUMED}', '{TaskStatus.REQUEUE}')
            """).fetchone()
            return result[0] if result else 0

    def recover_timeout_tasks(self, timeout_minutes: int = 10) -> int:
        """
        恢复超时未确认的任务
        :param timeout_minutes: 超时阈值（分钟）
        :return: 恢复的任务数量
        """
        with self._lock:
            # DuckDB 的时间计算语法
            self._conn.execute(f"""
                UPDATE {self._table_name}
                SET status = ?, consume_start_time = NULL
                WHERE status = ?
                AND consume_start_time < current_timestamp - INTERVAL '{timeout_minutes} minutes'
            """, [TaskStatus.TO_BE_CONSUMED, TaskStatus.PENDING])
            
            # 由于 DuckDB 不直接返回更新行数，这里查询一下
            result = self._conn.execute(f"""
                SELECT COUNT(*) FROM {self._table_name}
                WHERE status = '{TaskStatus.TO_BE_CONSUMED}'
            """).fetchone()
            return result[0] if result else 0

    def close(self):
        """关闭连接"""
        if self._conn:
            self._conn.close()
            self._conn = None


# ============================================================================
# Publisher 和 Consumer 实现
# ============================================================================

class DuckDBPublisher(AbstractPublisher):
    """DuckDB 消息发布者"""
    
    def custom_init(self):
        # 从 broker_exclusive_config 获取配置
        db_path = self.publisher_params.broker_exclusive_config['db_path']
        priority = self.publisher_params.broker_exclusive_config['priority']
        
        self._priority = priority
        self._queue = DuckDBQueue(
            queue_name=self._queue_name,
            db_path=db_path,
        )
        self.logger.info(f"DuckDB Publisher 初始化完成，队列: {self._queue_name}, 数据库: {db_path}")

    def _publish_impl(self, msg: str):
        """发布消息"""
        priority = self._priority
        # 尝试从消息中获取优先级
        try:
            msg_dict = json.loads(msg)
            if 'extra' in msg_dict:
                extra = msg_dict.get('extra', {})
                if isinstance(extra, dict):
                    other_extra = extra.get('other_extra_params', {})
                    if isinstance(other_extra, dict) and 'priority' in other_extra:
                        priority = other_extra['priority']
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


class DuckDBConsumer(AbstractConsumer):
    """DuckDB 消息消费者"""
    
    BROKER_KIND = None  # 会被框架自动设置

    def custom_init(self):
        # 从 broker_exclusive_config 获取配置
        db_path = self.consumer_params.broker_exclusive_config['db_path']
        self._poll_interval = self.consumer_params.broker_exclusive_config['poll_interval']
        self._timeout_minutes = self.consumer_params.broker_exclusive_config['timeout_minutes']
        self._delete_after_ack = self.consumer_params.broker_exclusive_config['delete_after_ack']
        
        self._queue = DuckDBQueue(
            queue_name=self._queue_name,
            db_path=db_path,
        )
        self.logger.info(
            f"DuckDB Consumer 初始化完成，队列: {self._queue_name}, "
            f"数据库: {db_path}, 轮询间隔: {self._poll_interval}s, 确认后删除: {self._delete_after_ack}"
        )

    def _dispatch_task(self):
        """
        核心调度方法
        循环从 DuckDB 获取消息并提交执行
        """
        # 启动超时任务恢复线程
        self._start_timeout_recovery()
        
        while True:
            try:
                task = self._queue.get(timeout=self._poll_interval)
                if task:
                    self._print_message_get_from_broker('DuckDB', task)
                    kw = {
                        'body': task['body'],
                        'job_id': task['job_id'],
                        'priority': task.get('priority', 0),
                    }
                    self._submit_task(kw)
            except Exception as e:
                self.logger.error(f"获取消息异常: {e}", exc_info=True)
                time.sleep(1)

    def _start_timeout_recovery(self):
        """启动超时任务恢复后台线程"""
        def recovery_loop():
            while True:
                try:
                    recovered = self._queue.recover_timeout_tasks(self._timeout_minutes)
                    if recovered:
                        self.logger.info(f"恢复了 {recovered} 个超时任务")
                except Exception as e:
                    self.logger.error(f"恢复超时任务异常: {e}")
                time.sleep(60)  # 每分钟检查一次

        t = threading.Thread(
            target=recovery_loop, 
            daemon=True, 
            name=f"duckdb_recovery_{self._queue_name}"
        )
        t.start()

    def _confirm_consume(self, kw):
        """确认消费成功，根据配置决定删除消息还是更新状态"""
        self._queue.ack(kw['job_id'], delete=self._delete_after_ack)

    def _requeue(self, kw):
        """消息重新入队"""
        self._queue.requeue(kw['job_id'])


# ============================================================================
# 注册 Broker
# ============================================================================

# 定义 broker kind（使用字符串，更易识别）
BROKER_KIND_DUCKDB = 'duckdb'

# 注册默认配置
from funboost.core.broker_kind__exclusive_config_default_define import register_broker_exclusive_config_default

register_broker_exclusive_config_default(
    BROKER_KIND_DUCKDB,
    {
        'db_path': 'funboost_duckdb.db',  # 数据库文件路径，':memory:' 为内存模式
        'poll_interval': 1.0,              # 轮询间隔（秒）
        'timeout_minutes': 10,             # 超时恢复阈值（分钟）
        'priority': 0,                     # 默认消息优先级
        'delete_after_ack': True,          # 确认消费后是否删除消息，False 则更新状态为 success
    }
)

# 注册到 funboost
register_custom_broker(BROKER_KIND_DUCKDB, DuckDBPublisher, DuckDBConsumer)


# ============================================================================
# 测试代码
# ============================================================================

if __name__ == '__main__':
    from funboost import boost, BoosterParams
    
    @boost(BoosterParams(
        queue_name='test_duckdb_queue',
        broker_kind=BROKER_KIND_DUCKDB,
        qps=5,
        concurrent_num=3,
        broker_exclusive_config={
            'db_path': Path(__file__).parent / 'test_funboost_duckdb.db',  # 使用文件存储
            # 'db_path': ':memory:',        # 或使用内存模式
        }
    ))
    def test_func(x, y):
        print(f"计算: {x} + {y} = {x + y}")
        time.sleep(0.5)
        return x + y
    
    # 发布消息
    for i in range(20):
        test_func.push(i, y=i * 2)
    
    print(f"队列消息数量: {test_func.publisher.get_message_count()}")
    
    # 启动消费
    test_func.consume()
