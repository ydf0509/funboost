# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2020/1/10 0010 18:42
"""
使用sqlachemy来使5种关系型数据库模拟消息队列。
"""
import datetime
import json
import time
from pathlib import Path

import sqlalchemy
from sqlalchemy import Column, func
from sqlalchemy import Integer
from sqlalchemy import String, DateTime
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from function_scheduling_distributed_framework.utils import nb_print

Base = declarative_base()  # type: sqlalchemy.ext.declarative.api.Base
print(Base)
print(Base.metadata.__class__.__dict__)


class TaskStatus:
    TO_BE_CONSUMED = 'to_be_consumed'
    PENGDING = 'pengding'
    FAILED = 'failed'
    SUCCESS = 'success'
    REQUEUE = 'requeue'


class SqlaBase(Base):
    __abstract__ = True
    job_id = Column(Integer, primary_key=True, autoincrement=True)
    body = Column(String(10240))
    publish_timestamp = Column(DateTime, default=datetime.datetime.now, comment='发布时间')
    status = Column(String(20))

    def __init__(self, job_id=None, body=None, publish_timestamp=None, status=None):
        self.job_id = job_id
        self.body = body
        self.publish_timestamp = publish_timestamp
        self.status = status

    def __str__(self):
        return f'{self.__class__} {self.__dict__}'

    def to_dict(self):
        # return {'job_id':self.job_id,'body':self.body,'publish_timestamp':self.publish_timestamp,'status':self.status}
        # noinspection PyUnresolvedReferences
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class SessionContext:
    def __init__(self, session: sqlalchemy.orm.session.Session):
        self.ss = session

    def __enter__(self):
        return self.ss

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.ss.commit()
        self.ss.close()


class SqlaQueue:
    def __init__(self, queue_name: str, sqla_conn_url: str):
        self.queue_name = queue_name
        self.__create_sqlite_dir_if_using_sqlite(sqla_conn_url)

        class SqlaQueueTable(SqlaBase):
            __tablename__ = self.queue_name
            __table_args__ = {'extend_existing': True}  # "useexisting": True

        engine = create_engine(sqla_conn_url, echo=False,
                               # max_overflow=30,  # 超过连接池大小外最多创建的连接
                               # pool_size=20,  # 连接池大小
                               # pool_timeout=300,  # 池中没有线程最多等待的时间，否则报错
                               # pool_recycle=-1  # 多久之后对线程池中的线程进行一次连接的回收（重置）
                               )
        SqlaQueueTable.metadata.create_all(engine)
        self.Session = sessionmaker(bind=engine, expire_on_commit=False)
        self.SqlaQueueTable = SqlaQueueTable

    def __create_sqlite_dir_if_using_sqlite(self, sqla_conn_url: str):
        # 'sqlite:////sqlachemy_queues/queues.db'
        if sqla_conn_url.startswith('sqlite:'):
            if not Path('/sqlachemy_queues').exists():
                Path('/sqlachemy_queues').mkdir()

    def push(self, sqla_task: SqlaBase):
        with SessionContext(self.Session()) as ss:
            ss.add(sqla_task)

    def get(self) -> SqlaBase:
        with SessionContext(self.Session()) as ss:
            # print(ss)
            while True:
                # task = ss.query(self.SqlaQueueTable).filter_by(status=TaskStatus.TO_BE_CONSUMED).first()
                query = ss.query(self.SqlaQueueTable).filter(self.SqlaQueueTable.status.in_([TaskStatus.TO_BE_CONSUMED, TaskStatus.REQUEUE]))
                # print(str(query))  # 打印原始语句。
                task = query.first()
                if task:
                    task.status = task.status = TaskStatus.PENGDING
                    return task
                else:
                    time.sleep(0.2)

    def set_success(self, sqla_task: SqlaBase):
        with SessionContext(self.Session()) as ss:
            # sqla_task = ss.merge(sqla_task)
            task = ss.query(self.SqlaQueueTable).filter(self.SqlaQueueTable.job_id == sqla_task.job_id).first()
            task.status = TaskStatus.SUCCESS

    def set_failed(self, sqla_task: SqlaBase):
        with SessionContext(self.Session()) as ss:
            # sqla_task = ss.merge(sqla_task)
            task = ss.query(self.SqlaQueueTable).filter_by(job_id=sqla_task.job_id).first()
            task.status = TaskStatus.FAILED

    def set_task_status(self, sqla_task: SqlaBase, status: str):
        with SessionContext(self.Session()) as ss:
            task = ss.query(self.SqlaQueueTable).filter(self.SqlaQueueTable.job_id == sqla_task.job_id).first()
            task.status = status

    def requeue_task(self, sqla_task: SqlaBase):
        self.set_task_status(sqla_task, TaskStatus.REQUEUE)

    def clear_queue(self):
        with SessionContext(self.Session()) as ss:
            ss.query(self.SqlaQueueTable).delete(synchronize_session=False)

    def get_count_by_status(self, status):
        with SessionContext(self.Session()) as ss:
            return ss.query(func.count(self.SqlaQueueTable.job_id)).filter(self.SqlaQueueTable.status == status).scalar()

    @property
    def total_count(self):
        with SessionContext(self.Session()) as ss:
            return ss.query(func.count(self.SqlaQueueTable.job_id)).scalar()

    @property
    def to_be_consumed_count(self):
        return self.get_count_by_status(TaskStatus.TO_BE_CONSUMED)


if __name__ == '__main__':
    queue = SqlaQueue('queue7', 'sqlite:////sqlachemy_queues/queues.db')
    print()
    for i in range(20000):
        queue.push(queue.SqlaQueueTable(body=json.dumps({'a': i, 'b': 2 * i}), status=TaskStatus.TO_BE_CONSUMED))

    taskx = queue.get()
    print(taskx.to_dict())

    queue = SqlaQueue('queue8', 'sqlite:////sqla/test2.db')
    for i in range(20):
        queue.push(queue.SqlaQueueTable(None, json.dumps({'a': i, 'b': 2 * i}), None, TaskStatus.TO_BE_CONSUMED))
    taskx = queue.get()
    print(taskx.to_dict())
    queue.set_success(taskx)
    print(queue.total_count)
    # queue.clear_queue()
    nb_print(queue.to_be_consumed_count)
