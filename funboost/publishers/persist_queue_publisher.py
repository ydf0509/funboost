# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2019/8/8 0008 13:05
import json
import sqlite3

import persistqueue
from funboost import funboost_config_deafult
from funboost.publishers.base_publisher import AbstractPublisher
from funboost.utils import LogManager

LogManager('persistqueue').get_logger_and_add_handlers(10)


# noinspection PyProtectedMember
class PersistQueuePublisher(AbstractPublisher):
    """
    使用persistqueue实现的本地持久化队列。
    这个是本地持久化，支持本地多个启动的python脚本共享队列任务。与LocalPythonQueuePublisher相比，不会随着python解释器退出，导致任务丢失。
    """

    # noinspection PyAttributeOutsideInit
    def custom_init(self):
        # noinspection PyShadowingNames
        def _my_new_db_connection(self, path, multithreading, timeout):  # 主要是改了sqlite文件后缀，方便pycharm识别和打开。
            # noinspection PyUnusedLocal
            conn = None
            if path == self._MEMORY:
                conn = sqlite3.connect(path,
                                       check_same_thread=not multithreading)
            else:
                conn = sqlite3.connect('{}/data.sqlite'.format(path),
                                       timeout=timeout,
                                       check_same_thread=not multithreading)
            conn.execute('PRAGMA journal_mode=WAL;')
            return conn

        persistqueue.SQLiteAckQueue._new_db_connection = _my_new_db_connection  # 打猴子补丁。
        # REMIND 官方测试基于sqlite的本地持久化，比基于纯文件的持久化，使用相同固态硬盘和操作系统情况下，速度快3倍以上，所以这里选用sqlite方式。

        self.queue = persistqueue.SQLiteAckQueue(path=funboost_config_deafult.SQLLITE_QUEUES_PATH, name=self._queue_name, auto_commit=True, serializer=json, multithreading=True)

    def concrete_realization_of_publish(self, msg):
        # noinspection PyTypeChecker
        self.queue.put(msg)

    def clear(self):
        sql = f'{"DELETE"}  {"FROM"} ack_queue_{self._queue_name}'
        self.logger.info(sql)
        self.queue._getter.execute(sql)
        self.queue._getter.commit()
        self.logger.warning(f'清除 本地持久化队列 {self._queue_name} 中的消息成功')

    def get_message_count(self):
        return self.queue._count()
        # return self.queue.qsize()

    def close(self):
        pass
