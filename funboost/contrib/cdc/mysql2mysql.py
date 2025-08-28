import dataset
from typing import Dict

class MySql2Mysql:
    """
    使用dataset封装的mysql binlog消息数据,保存到目标库中
    有了这个贡献类, 用户只需要一行代码就能通过cdc 实现 mysql2mysql,非常方便把数据库实例1的源表a,自动实时同步到数据库实例2的目标表a

    这个只是贡献类,用户想怎么插入表,想怎么清洗都可以,可以参考这个例子,dataset把一个字典保存到mysql的一行,真的很方便.
    用户还可以自定义批量插入目标表,都可以. 这个类不是必须使用,是做个示范.
    """
    def __init__(self, primary_key: str,
                 target_table_name: str,
                 target_sink_db: dataset.Database, ):
        self.primary_key = primary_key
        self.target_table_name = target_table_name
        self.target_sink_db = target_sink_db

    def sync_data(self, event_type: str,
                  schema: str,
                  table: str,
                  timestamp: int,
                  row_data: Dict, ):
        # 例如把这个表里面的数据原封不动 插入到 testdb7.users 表里面
        target_table: dataset.Table = self.target_sink_db[self.target_table_name]  # dataset会根据表名自动获取或创建表
        print(f"接收到事件: {event_type} on schema: {schema},  table: {table}, timestamp: {timestamp}")

        if event_type == 'INSERT':
            # `row_data` 中包含 'values' 字典
            data_to_insert = row_data['values']
            target_table.upsert(data_to_insert, [self.primary_key])
            print(f"  [INSERT] 成功同步数据: {data_to_insert}")

        elif event_type == 'UPDATE':
            # `row_data` 中包含 'before_values' 和 'after_values'
            data_to_update = row_data['after_values']
            target_table.upsert(data_to_update, [self.primary_key])
            print(f"  [UPDATE] 成功同步数据: {data_to_update}")

        elif event_type == 'DELETE':
            # `row_data` 中包含 'values' 字典，即被删除的行的数据
            data_to_delete = row_data['values']
            target_table.delete(**{self.primary_key: data_to_delete[self.primary_key]})
            print(f"  [DELETE] 成功同步数据: {data_to_delete}")