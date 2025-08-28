import time

from pymysqlreplication import BinLogStreamReader
from pymysqlreplication.row_event import (
    DeleteRowsEvent,
    UpdateRowsEvent,
    WriteRowsEvent,

)

MYSQL_SETTINGS = {"host": "127.0.0.1", "port": 3306, "user": "root", "passwd": "123456"}

stream = BinLogStreamReader(
        connection_settings=MYSQL_SETTINGS,
        server_id=103,
        only_events=[DeleteRowsEvent, UpdateRowsEvent, WriteRowsEvent,],

        # 添加这两个关键参数
        blocking=True,      # 1. 设置为阻塞模式，使其持续等待新事件
        resume_stream=True, # 2. (推荐) 允许在断线后自动从上次的位置恢复
    )

for binlogevent in stream:
    for row in binlogevent.rows:
        print(row)


