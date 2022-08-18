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

try:
    import sqlalchemy
    from sqlalchemy import Column, func, or_, and_, Table, MetaData
    from sqlalchemy import Integer
    from sqlalchemy import String, DateTime
    from sqlalchemy import create_engine
    from sqlalchemy.ext.automap import automap_base
    from sqlalchemy.ext.declarative import declarative_base
    from sqlalchemy.orm import sessionmaker, scoped_session
    from sqlalchemy.pool import StaticPool
    from sqlalchemy_utils import database_exists, create_database
except ImportError as e:
    print(f'{e}  不使用sqlalchemy操作数据库模拟消息队列，就可以无视这')
from funboost.utils import LoggerMixin, decorators, LoggerLevelSetterMixin


class TaskStatus:
    TO_BE_CONSUMED = 'to_be_consumed'
    PENGDING = 'pengding'
    FAILED = 'failed'
    SUCCESS = 'success'
    REQUEUE = 'requeue'


"""
class SqlaBase(Base):
    __abstract__ = True
    job_id = Column(Integer, primary_key=True, autoincrement=True)
    body = Column(String(10240))
    publish_timestamp = Column(DateTime, default=datetime.datetime.now, comment='发布时间')
    status = Column(String(20), index=True, nullable=True)
    consume_start_timestamp = Column(DateTime, default=None, comment='消费时间', index=True)

    def __init__(self, job_id=None, body=None, publish_timestamp=None, status=None, consume_start_timestamp=None):
        self.job_id = job_id
        self.body = body
        self.publish_timestamp = publish_timestamp
        self.status = status
        self.consume_start_timestamp = consume_start_timestamp

    def __str__(self):
        return f'{self.__class__} {self.__dict__}'

    def to_dict(self):
        # return {'job_id':self.job_id,'body':self.body,'publish_timestamp':self.publish_timestamp,'status':self.status}
        # noinspection PyUnresolvedReferences
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
"""





class SessionContext:
    def __init__(self, session: sqlalchemy.orm.session.Session):
        self.ss = session

    def __enter__(self):
        return self.ss

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.ss.commit()
        self.ss.close()


@decorators.flyweight
class SqlaQueue(LoggerMixin, LoggerLevelSetterMixin):
    # noinspection PyPep8Naming
    @decorators.where_is_it_called
    def __init__(self, queue_name: str, sqla_conn_url: str):
        class SqlaBaseMixin:
            # __abstract__ = True
            job_id = Column(Integer, primary_key=True, autoincrement=True)
            body = Column(String(10240))
            publish_timestamp = Column(DateTime, default=datetime.datetime.now, comment='发布时间')
            status = Column(String(20), index=False, nullable=True)
            consume_start_timestamp = Column(DateTime, default=None, comment='消费时间', index=False)

            def __init__(self, job_id=None, body=None, publish_timestamp=None, status=None, consume_start_timestamp=None):
                self.job_id = job_id
                self.body = body
                self.publish_timestamp = publish_timestamp
                self.status = status
                self.consume_start_timestamp = consume_start_timestamp

            def __str__(self):
                return f'{self.__class__} {self.to_dict()}'

            def to_dict(self):
                # return {'job_id':self.job_id,'body':self.body,'publish_timestamp':self.publish_timestamp,'status':self.status}
                # noinspection PyUnresolvedReferences
                return {c.name: getattr(self, c.name) for c in self.__table__.columns}

        self.logger.setLevel(20)
        self.queue_name = queue_name
        self._sqla_conn_url = sqla_conn_url
        self.__auto_create_database()

        if sqla_conn_url.startswith('sqlite'):
            engine = create_engine(sqla_conn_url,
                                   connect_args={'check_same_thread': False},
                                   # poolclass=StaticPool
                                   )
        else:
            engine = create_engine(sqla_conn_url, echo=False,
                                   max_overflow=30,  # 超过连接池大小外最多创建的连接
                                   pool_size=20,  # 连接池大小
                                   pool_timeout=300,  # 池中没有线程最多等待的时间，否则报错
                                   pool_recycle=-1  # 多久之后对线程池中的线程进行一次连接的回收（重置）
                                   )

        try:
            Base = declarative_base()  # type: sqlalchemy.ext.declarative.api.Base

            class SqlaQueueModel(SqlaBaseMixin, Base, ):
                __tablename__ = self.queue_name
                # __table_args__ = {'extend_existing': True， "mysql_engine": "MyISAM",
                #                     "mysql_charset": "utf8"}  # "useexisting": True

            SqlaQueueModel.metadata.create_all(engine, )
            self.Session = sessionmaker(bind=engine, expire_on_commit=False)
            self.SqlaQueueModel = SqlaQueueModel
        except Exception as e:
            self.logger.warning(e)
            Base = automap_base()

            class SqlaQueueModel(SqlaBaseMixin, Base, ):
                __tablename__ = self.queue_name
                # __table_args__ = {'extend_existing': True}  # "useexisting": True

            Base.prepare(engine, reflect=True)
            self.Session = sessionmaker(bind=engine, expire_on_commit=False)
            self.SqlaQueueModel = SqlaQueueModel

        self._to_be_publish_task_list = []

    def __auto_create_database(self):
        # 'sqlite:////sqlachemy_queues/queues.db'
        if self._sqla_conn_url.startswith('sqlite:'):
            if not Path('/sqlachemy_queues').exists():
                Path('/sqlachemy_queues').mkdir()
        else:
            if not database_exists(self._sqla_conn_url):
                create_database(self._sqla_conn_url)

    def push(self, sqla_task_dict):
        with SessionContext(self.Session()) as ss:
            # sqla_task = ss.merge(sqla_task)
            self.logger.debug(sqla_task_dict)
            ss.add(self.SqlaQueueModel(**sqla_task_dict))

    def bulk_push(self, sqla_task_dict_list: list):
        """
        queue = SqlaQueue('queue37', 'sqlite:////sqlachemy_queues/queues.db')
        queue.bulk_push([queue.SqlaQueueModel(body=json.dumps({'a': i, 'b': 2 * i}), status=TaskStatus.TO_BE_CONSUMED) for i in range(10000)])
        :param sqla_task_dict_list:
        :return:
        """
        with SessionContext(self.Session()) as ss:
            self.logger.debug(sqla_task_dict_list)
            sqla_task_list = [self.SqlaQueueModel(**sqla_task_dict) for sqla_task_dict in sqla_task_dict_list]
            ss.add_all(sqla_task_list)

    def get(self):
        # print(ss)
        while True:
            with SessionContext(self.Session()) as ss:
                ten_minitues_ago_datetime = datetime.datetime.now() + datetime.timedelta(minutes=-10)
                # task = ss.query(self.SqlaQueueModel).filter_by(status=TaskStatus.TO_BE_CONSUMED).first()
                # query = ss.query(self.SqlaQueueModel).filter(self.SqlaQueueModel.status.in_([TaskStatus.TO_BE_CONSUMED, TaskStatus.REQUEUE]))
                # noinspection PyUnresolvedReferences
                query = ss.query(self.SqlaQueueModel).filter(or_(self.SqlaQueueModel.status.in_([TaskStatus.TO_BE_CONSUMED, TaskStatus.REQUEUE]),
                                                                 and_(self.SqlaQueueModel.status == TaskStatus.PENGDING,
                                                                      self.SqlaQueueModel.consume_start_timestamp < ten_minitues_ago_datetime)))
                # print(str(query))  # 打印原始语句。
                task = query.first()
                if task:
                    task.status = task.status = TaskStatus.PENGDING
                    task.consume_start_timestamp = datetime.datetime.now()
                    return task.to_dict()
                else:
                    time.sleep(0.2)

    def set_success(self, sqla_task_dict, is_delete_the_task=True):
        with SessionContext(self.Session()) as ss:
            # sqla_task = ss.merge(sqla_task)
            # print(sqla_task_dict)
            if is_delete_the_task:
                sqla_task = ss.query(self.SqlaQueueModel).filter_by(job_id=sqla_task_dict['job_id']).first()
                # print(sqla_task)
                if sqla_task:  # REMIND 如果中途把表清空了，则不会查找到。
                    ss.delete(sqla_task)
            else:
                sqla_task = ss.query(self.SqlaQueueModel).filter(self.SqlaQueueModel.job_id == sqla_task_dict['job_id']).first()
                if sqla_task:
                    sqla_task.status = TaskStatus.SUCCESS

    def set_failed(self, sqla_task_dict):
        with SessionContext(self.Session()) as ss:
            # sqla_task = ss.merge(sqla_task)
            task = ss.query(self.SqlaQueueModel).filter_by(job_id=sqla_task_dict['job_id']).first()
            task.status = TaskStatus.FAILED

    def set_task_status(self, sqla_task_dict, status: str):
        with SessionContext(self.Session()) as ss:
            # sqla_task = ss.merge(sqla_task)
            task = ss.query(self.SqlaQueueModel).filter(self.SqlaQueueModel.job_id == sqla_task_dict['job_id']).first()
            task.status = status

    def requeue_task(self, sqla_task_dict):
        self.set_task_status(sqla_task_dict, TaskStatus.REQUEUE)

    def clear_queue(self):
        with SessionContext(self.Session()) as ss:
            ss.query(self.SqlaQueueModel).delete(synchronize_session=False)

    def get_count_by_status(self, status):
        with SessionContext(self.Session()) as ss:
            return ss.query(func.count(self.SqlaQueueModel.job_id)).filter(self.SqlaQueueModel.status == status).scalar()

    @property
    def total_count(self):
        with SessionContext(self.Session()) as ss:
            return ss.query(func.count(self.SqlaQueueModel.job_id)).scalar()

    @property
    def to_be_consumed_count(self):
        return self.get_count_by_status(TaskStatus.TO_BE_CONSUMED)


if __name__ == '__main__':
    queue = SqlaQueue('queue37', 'sqlite:////sqlachemy_queues/queues.db').set_log_level(10)
    print()
    queue.bulk_push([dict(body=json.dumps({'a': i, 'b': 2 * i}), status=TaskStatus.TO_BE_CONSUMED) for i in range(10000)])
    print()
    for i in range(1000):
        queue.push(dict(body=json.dumps({'a': i, 'b': 2 * i}), status=TaskStatus.TO_BE_CONSUMED))
    task_dictx = queue.get()
    print(task_dictx)
