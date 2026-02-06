# -*- coding: utf-8 -*-
"""
RocketMQ 5.x SimpleConsumer 消费者测试

使用方法:
1. 首先确保 RocketMQ 5.x 服务器已启动
   默认 gRPC 端点地址为 127.0.0.1:8081

2. 先运行发布者发布消息:
   python test_rocketmq_publisher.py

3. 然后运行消费者:
   python test_rocketmq_consumer.py

安装依赖:
    pip install rocketmq-python-client

特性:
    - SimpleConsumer 模式：支持单条消息乱序 ACK，不依赖 offset
    - 基于 gRPC 协议，纯 Python 实现
    - 支持 Windows / Linux / macOS
"""
from auto_run_on_remote import run_current_script_on_remote
run_current_script_on_remote()
import time
from funboost import boost, BoosterParams, BrokerEnum


@boost(BoosterParams(
    queue_name='test_rocketmq_5x_queue',
    broker_kind=BrokerEnum.ROCKETMQ,
    concurrent_num=5,
    log_level=10,  # DEBUG
    is_show_message_get_from_broker=True,
    # RocketMQ 5.x 专有配置
    broker_exclusive_config={
        'endpoints': '127.0.0.1:8081',  # RocketMQ 5.x gRPC 端点
        'consumer_group': 'funboost_test_group',
        # 'access_key': 'your_access_key',  # 阿里云等需要 AK/SK
        # 'secret_key': 'your_secret_key',
        # 'namespace': 'your_namespace',  # 可选
        'invisible_duration': 15,  # 消息不可见时间（秒）
        'max_message_num': 32,  # 每次拉取最大消息数
        'tag': '*',  # 消息过滤 tag，'*' 不过滤
    }
))
def test_rocketmq_task(x, y):
    """测试 RocketMQ 消费函数"""
    result = x + y
    print(f'计算结果: {x} + {y} = {result}')
    time.sleep(0.5)  # 模拟耗时操作
    return result


if __name__ == '__main__':
    # 启动消费者
    print('启动 RocketMQ 5.x SimpleConsumer...')
    print('特性: 支持单条消息乱序 ACK，不依赖 offset')
    print('按 Ctrl+C 停止')
    test_rocketmq_task.consume()
