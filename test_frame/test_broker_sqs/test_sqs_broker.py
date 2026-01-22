# -*- coding: utf-8 -*-
"""
AWS SQS 中间件测试示例

使用前请确保：
1. 安装 boto3: pip install boto3
2. 配置 AWS 凭证（通过环境变量、~/.aws/credentials 或在 funboost_config.py 中配置）

本地测试可以使用 LocalStack:
1. 安装 LocalStack: pip install localstack
2. 启动: localstack start
3. 在 funboost_config.py 中设置 SQS_ENDPOINT_URL = 'http://localhost:4566'
"""

import time
from funboost import boost, BrokerEnum, BoosterParams,ctrl_c_recv


@boost(BoosterParams(
    queue_name='test_sqs_queue',
    broker_kind=BrokerEnum.SQS,
    concurrent_num=5,
    log_level=10,
    is_show_message_get_from_broker=True,
    # SQS 专用配置
    broker_exclusive_config={
        'wait_time_seconds': 20,  # 长轮询等待时间（秒），最大20
        'max_number_of_messages': 10,  # 每次拉取的最大消息数，最大10
        'visibility_timeout': 300,  # 可见性超时（秒）
    }
))
def process_sqs_task(x, y):
    """处理 SQS 任务的函数"""
    print(f'开始处理任务: x={x}, y={y}')
    time.sleep(1)  # 模拟耗时操作
    result = x + y
    print(f'任务完成: {x} + {y} = {result}')
    return result


if __name__ == '__main__':
    # 发布任务
    print("发布 10 个任务到 SQS...")
    for i in range(10):
        process_sqs_task.push(x=i, y=i * 2)
    
    print(f"队列中消息数量: {process_sqs_task.get_message_count()}")
    
    # 启动消费
    print("开始消费任务...")
    process_sqs_task.consume()
    ctrl_c_recv()
