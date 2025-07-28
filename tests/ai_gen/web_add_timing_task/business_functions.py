"""
定时任务业务函数模块
这里定义所有需要被定时调用的业务函数
"""
import time
from datetime import datetime
from funboost import boost, BrokerEnum


# 定义业务函数，使用funboost装饰器
@boost('task_queue', broker_kind=BrokerEnum.REDIS)
def send_email_task(to_email: str, subject: str, content: str):
    """发送邮件任务"""
    print(f"[{datetime.now()}] 开始发送邮件")
    print(f"收件人: {to_email}")
    print(f"主题: {subject}")
    print(f"内容: {content}")
    
    # 模拟发送邮件的耗时操作
    time.sleep(2)
    
    print(f"[{datetime.now()}] 邮件发送完成")
    return {"status": "success", "message": "邮件发送成功"}


@boost('data_sync_queue', broker_kind=BrokerEnum.REDIS)
def data_sync_task(source_db: str, target_db: str, table_name: str):
    """数据同步任务"""
    print(f"[{datetime.now()}] 开始数据同步")
    print(f"源数据库: {source_db}")
    print(f"目标数据库: {target_db}")
    print(f"表名: {table_name}")
    
    # 模拟数据同步操作
    time.sleep(3)
    
    print(f"[{datetime.now()}] 数据同步完成")
    return {"status": "success", "message": f"表 {table_name} 同步完成"}


@boost('report_queue', broker_kind=BrokerEnum.REDIS)
def generate_report_task(report_type: str, date_range: str):
    """生成报表任务"""
    print(f"[{datetime.now()}] 开始生成报表")
    print(f"报表类型: {report_type}")
    print(f"时间范围: {date_range}")
    
    # 模拟生成报表
    time.sleep(5)
    
    print(f"[{datetime.now()}] 报表生成完成")
    return {"status": "success", "message": f"{report_type}报表生成完成"}


@boost('cleanup_queue', broker_kind=BrokerEnum.REDIS)
def cleanup_temp_files_task(directory: str, days_old: int):
    """清理临时文件任务"""
    print(f"[{datetime.now()}] 开始清理临时文件")
    print(f"目录: {directory}")
    print(f"清理{days_old}天前的文件")
    
    # 模拟清理操作
    time.sleep(1)
    
    print(f"[{datetime.now()}] 临时文件清理完成")
    return {"status": "success", "message": f"清理了{directory}目录中{days_old}天前的文件"}


@boost('backup_queue', broker_kind=BrokerEnum.REDIS)
def database_backup_task(database_name: str, backup_path: str):
    """数据库备份任务"""
    print(f"[{datetime.now()}] 开始数据库备份")
    print(f"数据库: {database_name}")
    print(f"备份路径: {backup_path}")
    
    # 模拟备份操作
    time.sleep(4)
    
    print(f"[{datetime.now()}] 数据库备份完成")
    return {"status": "success", "message": f"数据库 {database_name} 备份完成"} 