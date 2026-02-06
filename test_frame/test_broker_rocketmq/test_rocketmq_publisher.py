# -*- coding: utf-8 -*-
"""
RocketMQ 5.x 发布者测试

使用方法:
1. 首先确保 RocketMQ 5.x 服务器已启动
   默认 gRPC 端点地址为 127.0.0.1:8081

2. 运行此脚本发布消息:
   python test_rocketmq_publisher.py

安装依赖:
    pip install rocketmq-python-client

特性:
    - 基于 gRPC 协议，纯 Python 实现
    - 支持 Windows / Linux / macOS
"""

# 导入消费者中定义的函数
from test_rocketmq_consumer import test_rocketmq_task


if __name__ == '__main__':
    print('开始发布消息到 RocketMQ 5.x...')
    
    # 发布 20 条测试消息
    for i in range(20):
        # 使用 push 方法发布消息（简写方式）
        test_rocketmq_task.push(i, i * 2)
        print(f'已发布消息: x={i}, y={i * 2}')
    
    print('消息发布完成!')
    print('现在可以运行 test_rocketmq_consumer.py 来消费消息')
